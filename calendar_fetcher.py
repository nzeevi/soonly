import os
import json
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dateutil import parser

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CONFIG_FILE = 'config.json'


# Load / Save calendar IDs
def load_calendar_ids():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('calendar_ids', [])
    return []

def save_calendar_ids(calendar_ids):
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            pass  # במידה והקובץ פגום – מתחילים מחדש
    config['calendar_ids'] = calendar_ids
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# Load keywords to exclude from events
def load_excluded_keywords():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("exclude_keywords", [])
        except:
            pass
    return []

def should_exclude_event(summary):
    if not summary:
        return True
    excluded = load_excluded_keywords()
    return summary in excluded



# Authenticate with Google account
def get_credentials():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


# Fetch list of available calendars
def get_calendar_list():
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    calendars_result = service.calendarList().list().execute()
    calendars = calendars_result.get('items', [])

    calendar_choices = {}
    for cal in calendars:
        name = cal.get('summary', '(ללא שם)')
        cal_id = cal.get('id')
        calendar_choices[name] = cal_id

    return calendar_choices


# Interactive calendar selection
import tkinter as tk
from tkinter import messagebox

def choose_calendars():
    calendars = get_calendar_list()

    calendar_ids = list(calendars.values())
    calendar_names = list(calendars.keys())

    def confirm_selection():
        selected = [calendar_ids[i] for i in listbox.curselection()]
        if not selected:
            messagebox.showwarning("Empty selection", "Please select at least one calendar.")
            return
        # Save immediately on confirmation
        save_calendar_ids(selected)
        window.destroy()

    window = tk.Tk()
    window.title("Select Calendars")
    window.geometry("300x400")

    label = tk.Label(window, text="Select the calendars you wish to display:")
    label.pack(pady=10)

    listbox = tk.Listbox(window, selectmode=tk.MULTIPLE)
    for name in calendar_names:
        listbox.insert(tk.END, name)
    listbox.pack(expand=True, fill="both", padx=10, pady=5)

    button = tk.Button(window, text="Confirm", command=confirm_selection)
    button.pack(pady=10)

    window.mainloop()

    # After closing – verify selection was saved
    ids = load_calendar_ids()
    if ids:
        return ids
    else:
        messagebox.showerror("Error", "No calendars were selected. Please restart the application.")
        exit(1)

def get_upcoming_events(count=10):
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    calendar_ids = load_calendar_ids()
    if not calendar_ids:
        calendar_ids = choose_calendars()

    now = datetime.now(timezone.utc)
    now_str = now.isoformat()
    all_events = []

    for calendar_id in calendar_ids:
        try:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=now_str,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            for event in events:
                summary = event.get('summary', '')
                if should_exclude_event(summary):
                    continue

                start_str = event['start'].get('dateTime', event['start'].get('date'))
                end_str = event['end'].get('dateTime', event['end'].get('date'))

                try:
                    end_dt = parser.parse(end_str)
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    continue

                if end_dt > now:
                    all_events.append({
                        'summary': summary if summary else '(\u05dc\u05dc\u05d0 \u05e9\u05dd)',
                        'start': start_str,
                        'end': end_str
                    })

        except Exception as e:
            print(f"Error in calendar {calendar_id}: {e}")

    if not all_events:
        return []

    all_events.sort(key=lambda e: parser.parse(e['start']).astimezone(timezone.utc))

    return all_events[:count]
