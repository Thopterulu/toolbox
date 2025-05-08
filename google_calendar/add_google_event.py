import datetime
import os.path
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import requests

# Scope requis pour lire/écrire dans l'agenda
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
SECRETS_FILE = Path("google_calendar", "client_secret_.json")
SAMPLE_EVENTS_FILE = Path("google_calendar", "sample_events.json")


def get_calendar_service():
    creds = None
    token_file = "token.json"
    # token.json stocke le token d'accès utilisateur
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    # Authentification si pas encore connectés
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Sauvegarder les identifiants
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def add_event(summary, start_time_str, duration_minutes, description="", location=""):
    service = get_calendar_service()
    start_time = datetime.datetime.fromisoformat(start_time_str)
    end_time = start_time + datetime.timedelta(minutes=duration_minutes)

    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "Europe/Paris",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "Europe/Paris",
        },
    }

    event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"✅ Événement créé : {event.get('htmlLink')}")


def recurring_event(
    summary,
    start_time_str,
    duration_minutes,
    recurrence="WEEKLY",
    description="",
    location="",
    count=None,
    until=None,
):
    """
    Add a recurring event to Google Calendar

    Args:
        summary: Title of the event
        start_time_str: Start time in ISO 8601 format (e.g. "2025-05-09T14:00:00")
        duration_minutes: Duration of the event in minutes
        recurrence: Frequency of recurrence (default: "WEEKLY")
                   Can also include BYDAY parameter (e.g. "WEEKLY;BYDAY=MO,TU,WE,TH,FR")
        description: Event description
        location: Event location
        count: Number of occurrences (optional)
        until: End date of recurrence in ISO 8601 format (optional)
    """
    service = get_calendar_service()
    start_time = datetime.datetime.fromisoformat(start_time_str)
    end_time = start_time + datetime.timedelta(minutes=duration_minutes)

    # Handle recurrence with or without BYDAY parameter
    if "BYDAY" in recurrence:
        recurrence_rule = f"RRULE:FREQ={recurrence}"
    else:
        recurrence_rule = f"RRULE:FREQ={recurrence}"
        if count:
            recurrence_rule += f";COUNT={count}"
        if until:
            # Format until date as YYYYMMDD for RRULE
            until_formatted = until.replace("-", "").split("T")[0]
            recurrence_rule += f";UNTIL={until_formatted}"

    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "Europe/Paris",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "Europe/Paris",
        },
        "recurrence": [recurrence_rule],
        "visibility": "private",  # Make events private
    }

    event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"✅ Événement récurrent créé : {event.get('htmlLink')}")


def load_sample_events():
    """Load sample events from the JSON file and add them as recurring weekly events"""
    try:
        with open(SAMPLE_EVENTS_FILE, "r", encoding="utf-8") as file:
            events = json.load(file)

        print(
            f"Chargement de {len(events)} événements récurrents depuis {SAMPLE_EVENTS_FILE}"
        )
        for event in events:
            recurring_event(
                summary=event["summary"],
                start_time_str=event["start_time_str"],
                duration_minutes=event["duration_minutes"],
                recurrence=event.get("recurrence", "WEEKLY"),
                description=event.get("description", ""),
                location=event.get("location", ""),
            )
        print("✅ Tous les événements récurrents ont été ajoutés avec succès!")
    except Exception as e:
        print(f"❌ Erreur lors du chargement des événements: {e}")


if __name__ == "__main__":
    # Chargement des événements depuis le fichier JSON en tant qu'événements récurrents
    load_sample_events()
