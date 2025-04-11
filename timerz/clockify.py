import requests
import datetime
from zoneinfo import ZoneInfo
import random
from dotenv import load_dotenv
import os

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


def get_time_entries(date):
    url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/user/{USER_ID}/time-entries"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def split_time_entry(entry):
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

    split_start = datetime.datetime.combine(
        start_time.date(), datetime.time(12, 0), tzinfo=ZoneInfo(TIMEZONE)
    )
    split_end = datetime.datetime.combine(
        start_time.date(), datetime.time(12, 30), tzinfo=ZoneInfo(TIMEZONE)
    )

    if start_time < split_end and end_time > split_start:
        # Split into two entries
        first_end = min(end_time, split_start)
        second_start = max(start_time, split_end)

        entries_to_create = [
            {
                "start": start_time.isoformat(),
                "end": first_end.isoformat(),
                "description": entry["description"],
            },
            {
                "start": second_start.isoformat(),
                "end": end_time.isoformat(),
                "description": entry["description"],
            },
        ]

        # Delete the original entry
        delete_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries/{entry['id']}"
        requests.delete(delete_url, headers=HEADERS)

        # Create the new entries
        for new_entry in entries_to_create:
            create_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries"
            payload = {
                "start": new_entry["start"],
                "end": new_entry["end"],
                "description": new_entry["description"],
                "projectId": entry["projectId"],
                "tagIds": entry.get("tagIds", []),
            }
            requests.post(create_url, headers=HEADERS, json=payload)


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
    today = datetime.datetime.now(ZoneInfo(TIMEZONE)).date().isoformat()
    add_morning_schedule()
    add_hpfo_task()
    entries = get_time_entries(today)

    for entry in entries:
        split_time_entry(entry)


if __name__ == "__main__":
    main()
