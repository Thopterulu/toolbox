import requests
import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo
import random
from dotenv import load_dotenv
import os
import logging

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

HEADERS = {
    "X-Api-Key": API_KEY,
    "Content-Type": "application/json",
}


def get_time_entries(start_date=None, end_date=None):
    """Get time entries within a date range. If no dates provided, gets all entries."""
    url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/user/{USER_ID}/time-entries"

    # Convert to UTC for Clockify API
    if start_date:
        start_utc = start_date.astimezone(datetime.timezone.utc)
        start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        start_str = None

    if end_date:
        end_utc = end_date.astimezone(datetime.timezone.utc)
        end_str = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        end_str = None

    # Clockify API expects dates in UTC format
    params = {
        "start": start_str,
        "end": end_str,
        "page-size": 5000,  # Get maximum entries per request
    }
    params = {k: v for k, v in params.items() if v is not None}

    logging.info(f"Fetching entries with params: {params}")
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()


def remove_night_entries():
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


def adjust_night_entry(entry):
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
    entries_to_create = []
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
                temp_entry = {
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


def split_time_entry(entry, create_entry=True, entries_to_create=None):
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
        new_entries = [
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
            new_entries.append(
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
            for new_entry in new_entries:
                create_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries"
                requests.post(create_url, headers=HEADERS, json=new_entry)
        else:
            # Add to the provided list
            entries_to_create.extend(new_entries)
    else:
        # If no split needed and we're not creating entries, add the original
        if not create_entry:
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


def get_default_project():
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


def create_time_entry(start_time, end_time, description):
    create_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries"
    project_id = "6571c5455e233f2fc06a3b24"  # get_default_project()

    payload = {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "description": description,
        "projectId": project_id,
        "tagIds": [],
    }
    response = requests.post(create_url, headers=HEADERS, json=payload)
    response.raise_for_status()


def add_morning_schedule():
    today = datetime.datetime.now(ZoneInfo(TIMEZONE)).date()

    # Random start between 9:15 and 9:28
    random_minutes = random.randint(15, 28)
    start_day = datetime.datetime.combine(
        today, datetime.time(9, random_minutes), tzinfo=ZoneInfo(TIMEZONE)
    )

    # Create morning meetings
    meetings = [
        {
            "start": datetime.datetime.combine(
                today, datetime.time(9, 30), tzinfo=ZoneInfo(TIMEZONE)
            ),
            "end": datetime.datetime.combine(
                today, datetime.time(9, 45), tzinfo=ZoneInfo(TIMEZONE)
            ),
            "description": "Morning Standup",
        },
        {
            "start": datetime.datetime.combine(
                today, datetime.time(9, 45), tzinfo=ZoneInfo(TIMEZONE)
            ),
            "end": datetime.datetime.combine(
                today, datetime.time(10, 0), tzinfo=ZoneInfo(TIMEZONE)
            ),
            "description": "Team Planning",
        },
    ]

    # Create start of day entry
    create_time_entry(start_day, meetings[0]["start"], "Start of Day")

    # Create meeting entries
    for meeting in meetings:
        create_time_entry(meeting["start"], meeting["end"], meeting["description"])


def add_hpfo_task():
    today = datetime.datetime.now(ZoneInfo(TIMEZONE)).date()

    # Random time between 2 PM and 4 PM
    random_hour = random.randint(14, 15)  # 14 = 2 PM, 15 = 3 PM
    random_minute = random.randint(0, 44)  # Ensures end time won't go past 4 PM

    start_time = datetime.datetime.combine(
        today, datetime.time(random_hour, random_minute), tzinfo=ZoneInfo(TIMEZONE)
    )
    end_time = start_time + datetime.timedelta(minutes=15)

    create_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries"
    payload = {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "description": "HPFO",
        "projectId": "60c9a33e33cb7c4047062b35",
        "tagIds": [],
    }
    response = requests.post(create_url, headers=HEADERS, json=payload)
    response.raise_for_status()


def main():
    # Choose function to run based on environment or argument
    action = os.getenv("CLOCKIFY_ACTION", "daily")

    if action == "remove_nights":
        remove_night_entries()
    else:
        # Regular daily schedule
        today = datetime.datetime.now(ZoneInfo(TIMEZONE)).date().isoformat()
        add_morning_schedule()
        add_hpfo_task()
        entries = get_time_entries(today)

        for entry in entries:
            split_time_entry(entry)


if __name__ == "__main__":
    main()
