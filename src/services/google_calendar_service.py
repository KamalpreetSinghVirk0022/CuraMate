# services/google_calendar_service.py
import os
import datetime
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def get_calendar_service():
    """Authenticates the user and returns the Calendar API service."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                st.error("Missing 'credentials.json'. Please check the setup instructions.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # This will open a browser window for the user to login
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def add_medication_to_calendar(med_list):
    """Adds the medication schedule directly to the user's primary calendar."""
    service = get_calendar_service()
    if not service:
        return False

    added_count = 0
    
    for med in med_list:
        try:
            med_name = med.get("name", "Medication")
            dosage = med.get("dosage", "as prescribed")
            
            # 1. Calculate Recurrence Rule (RRULE)
            recurrence = ["RRULE:FREQ=DAILY"] # Default
            if med.get("end_date"):
                # Google requires YYYYMMDD format for UNTIL
                # We remove the hyphens from '2025-11-20' -> '20251120'
                end_date_str = med["end_date"].replace("-", "")
                recurrence = [f"RRULE:FREQ=DAILY;UNTIL={end_date_str}T235959Z"]

            # 2. Create an event for EACH time of day
            for alert_time_str in med.get("alert_times", []):
                
                # Create a start datetime for TODAY at that time
                # We use the user's local system time for simplicity
                now = datetime.datetime.now()
                alert_time = datetime.datetime.strptime(alert_time_str, "%H:%M").time()
                
                start_dt = datetime.datetime.combine(now.date(), alert_time)
                end_dt = start_dt + datetime.timedelta(minutes=15)

                event_body = {
                    'summary': f'💊 Take: {med_name}',
                    'description': f'Dosage: {dosage}\nAdded by CuraMate',
                    'start': {
                        'dateTime': start_dt.isoformat(),
                        'timeZone': 'Asia/Kolkata', # CHANGE THIS to your users' timezone if needed
                    },
                    'end': {
                        'dateTime': end_dt.isoformat(),
                        'timeZone': 'Asia/Kolkata',
                    },
                    'recurrence': recurrence,
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': 30}, # 30 min prior notification
                            {'method': 'popup', 'minutes': 5},  # 5 min prior notification
                        ],
                    },
                }

                service.events().insert(calendarId='primary', body=event_body).execute()
                added_count += 1
                
        except Exception as e:
            st.error(f"Error adding {med_name} to calendar: {e}")
            return False

    return added_count


# ... (keep existing imports and get_calendar_service function) ...

def add_appointment_to_calendar(doctor_name, hospital, date_str):
    """Adds a single appointment to the user's Google Calendar."""
    service = get_calendar_service()
    if not service:
        return False

    try:
        # 1. Set up the time (Defaulting to 9:00 AM on the booking date)
        appt_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        start_time = datetime.time(9, 0, 0) # 9:00 AM
        
        # Combine to get start/end datetime
        start_dt = datetime.datetime.combine(appt_date, start_time)
        end_dt = start_dt + datetime.timedelta(hours=1) # 1 hour duration

        event_body = {
            'summary': f'🩺 Appointment: {doctor_name}',
            'location': hospital,
            'description': 'Booked via CuraMate',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Asia/Kolkata', # Change this if your users are elsewhere
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 1440}, # 1 Day before (24 * 60)
                    {'method': 'popup', 'minutes': 60},   # 1 Hour before
                ],
            },
        }

        service.events().insert(calendarId='primary', body=event_body).execute()
        return True

    except Exception as e:
        st.error(f"Error adding appointment to calendar: {e}")
        return False