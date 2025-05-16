import requests
import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo
import random
from dotenv import load_dotenv
import os
import logging
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
WORKSPACE_ID = os.getenv("WORKSPACE_ID")
USER_ID = os.getenv("USER_ID")
TIMEZONE = "Europe/Paris"

BASE_URL = "https://api.clockify.me/api/v1"

HEADERS: Dict[str, Optional[str]] = {
    "X-Api-Key": API_KEY,
    "Content-Type": "application/json",
}


def get_time_entries(
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
) -> List[Dict[str, Any]]:
    """Get time entries within a date range. If no dates provided, gets all entries."""
    url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/user/{USER_ID}/time-entries"

    # Convert to UTC for Clockify API
    start_str: Optional[str] = None
    if start_date:
        start_utc = start_date.astimezone(datetime.timezone.utc)
        start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    end_str: Optional[str] = None
    if end_date:
        end_utc = end_date.astimezone(datetime.timezone.utc)
        end_str = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Clockify API expects dates in UTC format
    params: Dict[str, Any] = {"page-size": 5000}  # Get maximum entries per request
    if start_str:
        params["start"] = start_str
    if end_str:
        params["end"] = end_str

    logging.info(f"Fetching entries with params: {params}")
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()


def remove_night_entries() -> None:
    """Remove time entries between 8 PM and 9 AM for the last 2 weeks"""
    today = datetime.datetime.now(ZoneInfo(TIMEZONE))
    two_weeks_ago = today - timedelta(days=14)
    logging.info("Starting to process time entries")
    logging.info(f"Date range: {two_weeks_ago.date()} to {today.date()}")

    # Get all entries from the last 2 weeks at once
    two_weeks_ago_start = datetime.datetime.combine(
        two_weeks_ago.date(), datetime.time(0, 0), tzinfo=ZoneInfo(TIMEZONE)
    )
    today_end = datetime.datetime.combine(
        today.date(), datetime.time(23, 59, 59), tzinfo=ZoneInfo(TIMEZONE)
    )

    entries = get_time_entries(start_date=two_weeks_ago_start, end_date=today_end)
    logging.info(f"Found {len(entries)} entries to process")

    entries_processed = 0
    for entry in entries:
        adjust_night_entry(entry)
        entries_processed += 1
        if entries_processed % 10 == 0:  # Log progress every 10 entries
            logging.info(f"Processed {entries_processed}/{len(entries)} entries")

    logging.info(f"Finished processing {entries_processed} entries")


def adjust_night_entry(entry: Dict[str, Any]) -> None:
    """Split and adjust time entries to remove work during nights, weekends, and lunch"""
    logging.info(
        f"Processing entry: {entry.get('description', 'No description')} - ID: {entry.get('id', 'No ID')}"
    )
    if (
        not entry.get("timeInterval")
        or not entry["timeInterval"].get("start")
        or not entry["timeInterval"].get("end")
    ):
        return

    start_time = datetime.datetime.fromisoformat(
        entry["timeInterval"]["start"][:-1]
    ).replace(tzinfo=ZoneInfo(TIMEZONE))
    end_time = datetime.datetime.fromisoformat(
        entry["timeInterval"]["end"][:-1]
    ).replace(tzinfo=ZoneInfo(TIMEZONE))

    logging.info(f"Entry time range: {start_time} to {end_time}")

    # Skip weekend entries entirely
    if start_time.weekday() >= 5 or end_time.weekday() >= 5:
        logging.info("Skipping weekend entry")
        delete_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries/{entry['id']}"
        requests.delete(delete_url, headers=HEADERS)
        return

    # Generate all 8 PM and 9 AM cutoffs between start and end time
    current_date = start_time.date()
    entries_to_create: List[Dict[str, Any]] = []
    current_segment_start = start_time

    while current_date <= end_time.date():
        # Skip processing if it's a weekend
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        # Get cutoff times for current day
        pm_cutoff = datetime.datetime.combine(
            current_date, datetime.time(20, 0), tzinfo=ZoneInfo(TIMEZONE)
        )
        next_am_cutoff = datetime.datetime.combine(
            current_date + timedelta(days=1),
            datetime.time(9, 0),
            tzinfo=ZoneInfo(TIMEZONE),
        )

        # Handle segments before 8 PM
        if current_segment_start < pm_cutoff and current_segment_start < end_time:
            segment_end = min(pm_cutoff, end_time)
            if segment_end > current_segment_start:
                logging.info(
                    f"Creating daytime segment: {current_segment_start} to {segment_end}"
                )
                # Create a temporary entry for the segment
                # Ensure proper ISO format with timezone
                temp_entry: Dict[str, Any] = {
                    "timeInterval": {
                        "start": current_segment_start.astimezone(
                            datetime.timezone.utc
                        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "end": segment_end.astimezone(datetime.timezone.utc).strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),
                    },
                    "description": entry["description"],
                    "projectId": entry["projectId"],
                    "tagIds": entry.get("tagIds", []),
                }
                # Split this segment for lunch break
                split_time_entry(
                    temp_entry, create_entry=False, entries_to_create=entries_to_create
                )

        # Skip the night period (8 PM - 9 AM)
        if end_time > next_am_cutoff:
            # Start next segment at 9 AM if we're not at the end
            logging.info(f"Skipping night period: {pm_cutoff} to {next_am_cutoff}")
            current_segment_start = next_am_cutoff
        else:
            # If we've passed the end time, break
            logging.info(f"Reached end time {end_time}, stopping")
            break

        # Move to next day
        current_date += timedelta(days=1)

    # Delete the original entry
    delete_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries/{entry['id']}"
    logging.info(f"Deleting original entry: {entry['id']}")
    requests.delete(delete_url, headers=HEADERS)

    # Create the new entries
    logging.info(f"Creating {len(entries_to_create)} new segments")
    for new_entry in entries_to_create:
        create_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries"
        requests.post(create_url, headers=HEADERS, json=new_entry)


def split_time_entry(
    entry: Dict[str, Any],
    create_entry: bool = True,
    entries_to_create: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Split entry at lunch time (12:00-12:30)

    Args:
        entry: The time entry to split
        create_entry: If True, creates the new entries via API. If False, adds to entries_to_create
        entries_to_create: List to append entries to when create_entry is False
    """
    # Check if entry has complete timeInterval data
    if (
        not entry.get("timeInterval")
        or not entry["timeInterval"].get("start")
        or not entry["timeInterval"].get("end")
    ):
        return

    start_time = datetime.datetime.fromisoformat(
        entry["timeInterval"]["start"][:-1]
    ).replace(tzinfo=ZoneInfo(TIMEZONE))
    end_time = datetime.datetime.fromisoformat(
        entry["timeInterval"]["end"][:-1]
    ).replace(tzinfo=ZoneInfo(TIMEZONE))

    # Only split if the entry crosses lunch time
    split_start = datetime.datetime.combine(
        start_time.date(), datetime.time(12, 0), tzinfo=ZoneInfo(TIMEZONE)
    )
    split_end = datetime.datetime.combine(
        start_time.date(), datetime.time(12, 30), tzinfo=ZoneInfo(TIMEZONE)
    )

    if start_time < split_end and end_time > split_start:
        logging.info(f"Splitting entry at lunch time: {split_start} to {split_end}")

        # Split into two entries
        first_end = min(end_time, split_start)
        second_start = max(start_time, split_end)

        # Convert times to UTC and use proper ISO format
        new_entries_list: List[Dict[str, Any]] = [
            {
                "start": start_time.astimezone(datetime.timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "end": first_end.astimezone(datetime.timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "description": entry["description"],
                "projectId": entry.get("projectId"),
                "tagIds": entry.get("tagIds", []),
            }
        ]

        if end_time > split_end:
            new_entries_list.append(
                {
                    "start": second_start.astimezone(datetime.timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "end": end_time.astimezone(datetime.timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "description": entry["description"],
                    "projectId": entry.get("projectId"),
                    "tagIds": entry.get("tagIds", []),
                }
            )

        if create_entry:
            # Delete the original entry if it has an ID
            if entry.get("id"):
                delete_url = (
                    f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries/{entry['id']}"
                )
                requests.delete(delete_url, headers=HEADERS)

            # Create the new entries via API
            for new_entry_item in new_entries_list:
                create_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries"
                requests.post(create_url, headers=HEADERS, json=new_entry_item)
        else:
            # Add to the provided list
            if entries_to_create is not None:
                entries_to_create.extend(new_entries_list)
    else:
        # If no split needed and we're not creating entries, add the original
        if not create_entry and entries_to_create is not None:
            entries_to_create.append(
                {
                    "start": start_time.astimezone(datetime.timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "end": end_time.astimezone(datetime.timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "description": entry["description"],
                    "projectId": entry.get("projectId"),
                    "tagIds": entry.get("tagIds", []),
                }
            )


def get_default_project() -> Optional[str]:
    """fallback method :
    1. Via l'interface web (en inspectant lURL)

    Ouvrez votre espace de travail sur Clockify.

    Allez dans l'onglet « Projects ».

    Sélectionnez le projet dont vous souhaitez connaître l'ID.

    Dans la barre d'adresse du navigateur, l'URL contient souvent un segment du type .../projects/<ProjectID>.

        Par exemple : https://clockify.me/projects/621dc8af3e09a446a7ff...

        Le morceau après /projects/ (jusqu'au prochain /) correspond à l'ID de votre projet.
    """
    url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/projects"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    projects = response.json()
    return (
        projects[0]["id"] if projects else None
    )  # marche pas avec shiroo, certains id sont hidden


def create_time_entry(
    start_time: datetime.datetime, end_time: datetime.datetime, description: str
) -> None:
    create_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries"
    project_id = "6571c5455e233f2fc06a3b24"  # Consider making this configurable or using get_default_project()

    # Ensure times are in UTC and correct format for Clockify API
    start_utc_str = start_time.astimezone(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    end_utc_str = end_time.astimezone(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    payload = {
        "start": start_utc_str,
        "end": end_utc_str,
        "description": description,
        "projectId": project_id,
        "tagIds": [],
    }
    response = requests.post(create_url, headers=HEADERS, json=payload)
    response.raise_for_status()
    logging.info(
        f"Created entry: '{description}' from {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}"
    )


def add_morning_schedule(target_date_obj: datetime.date) -> None:
    """Adds standard morning meetings and start of day entry for the given date."""
    logging.info(f"Adding morning schedule for {target_date_obj.isoformat()}")

    # Random start between 9:15 and 9:28
    random_minutes = random.randint(15, 28)
    start_day = datetime.datetime.combine(
        target_date_obj, datetime.time(9, random_minutes), tzinfo=ZoneInfo(TIMEZONE)
    )

    # Create morning meetings
    meetings = [
        {
            "start": datetime.datetime.combine(
                target_date_obj, datetime.time(9, 30), tzinfo=ZoneInfo(TIMEZONE)
            ),
            "end": datetime.datetime.combine(
                target_date_obj, datetime.time(9, 45), tzinfo=ZoneInfo(TIMEZONE)
            ),
            "description": "Morning Standup",
        },
        {
            "start": datetime.datetime.combine(
                target_date_obj, datetime.time(9, 45), tzinfo=ZoneInfo(TIMEZONE)
            ),
            "end": datetime.datetime.combine(
                target_date_obj, datetime.time(10, 0), tzinfo=ZoneInfo(TIMEZONE)
            ),
            "description": "Team Planning",
        },
    ]

    # Create start of day entry
    if meetings:  # Ensure there's a meeting to mark the end of "Start of Day"
        create_time_entry(start_day, meetings[0]["start"], "Start of Day")

    # Create meeting entries
    for meeting in meetings:
        create_time_entry(meeting["start"], meeting["end"], meeting["description"])


def add_hpfo_task(target_date_obj: datetime.date) -> None:
    """Adds a 15-minute HPFO task at a random time between 2 PM and 4 PM for the given date."""
    logging.info(f"Adding HPFO task for {target_date_obj.isoformat()}")

    # Random time between 2 PM and 4 PM
    random_hour = random.randint(14, 15)  # 14 = 2 PM, 15 = 3 PM
    random_minute = random.randint(
        0, 44
    )  # Ensures end time (15 mins later) won't go past 4 PM if start is 3:44

    start_time = datetime.datetime.combine(
        target_date_obj,
        datetime.time(random_hour, random_minute),
        tzinfo=ZoneInfo(TIMEZONE),
    )
    end_time = start_time + timedelta(minutes=15)

    # Using the specific project ID for HPFO as in the original script
    hpfo_project_id = "60c9a33e33cb7c4047062b35"

    start_utc_str = start_time.astimezone(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    end_utc_str = end_time.astimezone(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    payload = {
        "start": start_utc_str,
        "end": end_utc_str,
        "description": "HPFO",
        "projectId": hpfo_project_id,
        "tagIds": [],
    }
    create_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries"
    response = requests.post(create_url, headers=HEADERS, json=payload)
    response.raise_for_status()
    logging.info(
        f"Created HPFO entry: {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}"
    )


def autofill_workday(target_date_obj: datetime.date) -> None:
    """Autofills a standard workday (9:00-12:00 and 12:30-17:00) for the given date."""
    logging.info(f"Autofilling standard workday for {target_date_obj.isoformat()}")

    work_start_morning = datetime.datetime.combine(
        target_date_obj, datetime.time(9, 0), tzinfo=ZoneInfo(TIMEZONE)
    )
    lunch_start = datetime.datetime.combine(
        target_date_obj, datetime.time(12, 0), tzinfo=ZoneInfo(TIMEZONE)
    )
    lunch_end = datetime.datetime.combine(
        target_date_obj, datetime.time(12, 30), tzinfo=ZoneInfo(TIMEZONE)
    )
    work_end_afternoon = datetime.datetime.combine(
        target_date_obj, datetime.time(17, 0), tzinfo=ZoneInfo(TIMEZONE)
    )

    create_time_entry(work_start_morning, lunch_start, "Work")
    create_time_entry(lunch_end, work_end_afternoon, "Work")
    logging.info(f"Completed autofill for {target_date_obj.isoformat()}")


def main() -> None:
    # Choose function to run based on environment or argument
    action = os.getenv("CLOCKIFY_ACTION", "daily")
    today_date_obj = datetime.datetime.now(ZoneInfo(TIMEZONE)).date()  # date object

    if action == "remove_nights":
        remove_night_entries()
    elif action == "autofill_specific_date":
        date_str = os.getenv("CLOCKIFY_DATE")
        if not date_str:
            logging.error(
                "CLOCKIFY_DATE environment variable not set for autofill_specific_date action."
            )
            return
        try:
            # Ensure we are working with a date object
            target_date_obj = datetime.datetime.fromisoformat(date_str).date()
        except ValueError:
            logging.error(
                f"Invalid date format for CLOCKIFY_DATE: {date_str}. Use YYYY-MM-DD."
            )
            return

        if target_date_obj.weekday() >= 5:  # Monday is 0 and Sunday is 6
            logging.info(
                f"Skipping autofill for weekend date: {target_date_obj.isoformat()}"
            )
            return

        autofill_workday(target_date_obj)
    else:  # Default "daily" action
        logging.info(f"Running daily schedule for {today_date_obj.isoformat()}")
        add_morning_schedule(today_date_obj)
        add_hpfo_task(today_date_obj)


if __name__ == "__main__":
    main()
