#!/usr/bin/python3
import tempfile
import pickle
import requests
import os.path
import os
#google specific stuff for calendar
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dateutil.parser import parse

from datetime import datetime, timedelta
from pytz import timezone
import pytz
import time
from dotenv import load_dotenv

HOMEDIR='/home/yak/'
CALID='o995m43173bpslmhh49nmrp5i4@group.calendar.google.com' #yakcollective google calender id

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

load_dotenv(HOMEDIR+'.env')

creds = None
if os.path.exists(HOMEDIR+'token.pickle'):
    with open(HOMEDIR+'token.pickle', 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(HOMEDIR+'yc-credentials.json', SCOPES)
        creds = flow.run_local_server(port=9000)
    with open(HOMEDIR+'token.pickle', 'wb') as token:
        pickle.dump(creds, token)
#ask fro next 7 days of events
cal = build('calendar', 'v3', credentials=creds)

now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
events_result = cal.events().list(calendarId=CALID, timeMin=now,timeMax=(datetime.utcnow()+timedelta(days=7)).isoformat()+ 'Z',
                                    singleEvents=True,
                                    orderBy='startTime').execute()
events = events_result.get('items', [])
#print("events len:", len(events))

#generate a message string

#print("yes nice")
s="Upcoming in next week:\n"
if not events:
    s=s+'No upcoming events found.'
tod=""
tom=""
too=""

for event in events:
    if (event['status']=="canceled" or event['summary'].startswith("Canceled:")):
        continue
#for each event figure out how long until it starts and generate a nice format of it, base don nathan ack's suggestion
    start = parse(event['start'].get('dateTime', event['start'].get('date')))
    seconds2go=(start-datetime.utcnow().astimezone()).total_seconds()
    days, hours, minutes = int(seconds2go //(3600*24)), int((seconds2go // 3600) % 24), int(seconds2go // 60 % 60)
    el=event.get('location','')
    if el!='':
        if el.startswith("http"):
            el="<"+el+">"
        el='\n> '+el
    if (days==0):
        ts=str(hours)+ ' hours' +' and '+str(minutes)+ ' minutes '
        if(tod!=""):
            tod=tod+"\n"
        tod=tod+"> **"+event['summary'].replace("and Yak Collective","")+ '**'+el+'\n> Starts in '+ ts+'\n'
    if (days==1):
        if(tom!=""):
            tom=tom+"\n"
        ts=str(days) + ' day and '+str(hours)+ ' hours' +' and '+str(minutes)+ ' minutes '
        tom=tom+"> **"+event['summary'].replace("and Yak Collective","")+ '**'+el+'\n> Starts in '+ ts+'\n'
    if(days>1):
        if(too!=""):
            too=too+"\n"
        ts=str(days) + ' days and '+str(hours)+ ' hours' +' and '+str(minutes)+ ' minutes '
        too=too+"> **"+event['summary'].replace("and Yak Collective","")+ '**'+el+'\n> Starts in '+ ts+'\n'
if (tod==""):
    tod="No upcoming events in next 24 hours\n"
if (tom==""):
    tom="No upcoming events tomorrow\n"
if (too==""):
    too="No other upcoming events"
s=s+"\n__**Today**__ (next 24 hours)\n"+tod+"\n__**Tomorrow**__\n"+tom+"\n__**Later this week**__ \n"+too

print(s)
