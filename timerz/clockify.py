import requests
import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
WORKSPACE_ID = os.getenv("WORKSPACE_ID")
USER_ID = os.getenv("USER_ID")


BASE_URL = "https://api.clockify.me/api/v1"

HEADERS = {
    "X-Api-Key": API_KEY,
    "Content-Type": "application/json",
}


def get_time_entries(date):
    url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/user/{USER_ID}/time-entries"
    params = {"start": f"{date}T07:00:00Z", "end": f"{date}T23:59:59Z"}
    response = requests.get(url, headers=HEADERS) #, params=params)
    response.raise_for_status()
    return response.json()


def split_time_entry(entry):
    start_time = datetime.datetime.fromisoformat(entry["timeInterval"]["start"][:-1])
    end_time = datetime.datetime.fromisoformat(entry["timeInterval"]["end"][:-1])

    split_start = datetime.datetime.combine(start_time.date(), datetime.time(12, 0))
    split_end = datetime.datetime.combine(start_time.date(), datetime.time(12, 30))

    if start_time < split_end and end_time > split_start:
        # Split into two entries
        first_end = min(end_time, split_start)
        second_start = max(start_time, split_end)

        entries_to_create = [
            {"start": start_time.isoformat(), "end": first_end.isoformat(), "description": entry["description"]},
            {"start": second_start.isoformat(), "end": end_time.isoformat(), "description": entry["description"]},
        ]

        # Delete the original entry
        delete_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries/{entry['id']}"
        requests.delete(delete_url, headers=HEADERS)

        # Create the new entries
        for new_entry in entries_to_create:
            create_url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries"
            payload = {
                "start": new_entry["start"] + "Z",
                "end": new_entry["end"] + "Z",
                "description": new_entry["description"],
                "projectId": entry["projectId"],
                "tagIds": entry.get("tagIds", []),
            }
            requests.post(create_url, headers=HEADERS, json=payload)


def main():
    today = datetime.date.today().isoformat()
    entries = get_time_entries(today)

    for entry in entries:
        if "timeInterval" in entry:
            split_time_entry(entry)


if __name__ == "__main__":
    main()
