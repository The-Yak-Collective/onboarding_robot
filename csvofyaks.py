import discord
import base64


import pickle
import requests
import os.path
import os

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dateutil.parser import parse

from datetime import datetime, timedelta
from pytz import timezone
import pytz
import time
from dotenv import load_dotenv

from datetime import datetime

load_dotenv('/home/yak/.env')

intents = discord.Intents.default()
intents.members = True


client = discord.Client(intents=intents)


newones=[]
mem=[]
@client.event
async def on_ready(): 

    print('We have logged in as {0.user}'.format(client),  client.guilds)#, client.guilds[0].text_channels)
    g=client.guilds[0]
    #mem=await g.fetch_members().flatten() # no need to read until asked
    #for u in mem:
    #    pass #print(u,u.id)
        

@client.event
async def on_member_join(member):
    print("new member: "+str(member.name), flush=True)
    newones.append("new member"+str(member.name))
    me2 = client.get_user(710573356759384075).dm_channel #for now send messages to me
    await me2.send("new member: "+str(member.name)+"id: "+str(member.id))
    


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
        print("hello mess from "+message.author.name,flush=True);
    if message.content.startswith('$whosenew'):
        await message.channel.send(str(newones))
    if message.content.startswith('$givemecsv'):
        print("working on memberlist")
        await makecsvfile()
        await message.channel.send("a csv file of all yaks")
        await message.channel.send("actual file:", file=discord.File("memberlist.csv"))
    if message.content.startswith('$test'):
        await message.channel.send("this is a test")#: "+str([(x.name,x.created_at) for x in message.author.roles]))
    if (message.content.startswith('$die!') and message.author.id==710573356759384075):
        exit(0)
    if message.content.startswith('$dm'):
        print("dm",flush=True);
        t=int(message.content[3:])
        target=client.get_user(t).dm_channel
        if (not target): 
            print("need to create dm channel",flush=True)
            target=await client.get_user(t).create_dm()
        print("target is:",target,flush=True)    
        await target.send('Hello! i was told by '+message.author.name+' to contact you')
    if message.content.startswith('$upcoming'):
        creds = None
        if os.path.exists('/home/yak/token.pickle'):
            with open('/home/yak/token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('yc-credentials.json', SCOPES)
                creds = flow.run_local_server(port=9000)
            with open('/home/yak/token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        cal = build('calendar', 'v3', credentials=creds)

        now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        events_result = cal.events().list(calendarId='o995m43173bpslmhh49nmrp5i4@group.calendar.google.com', timeMin=now,timeMax=(datetime.utcnow()+timedelta(days=7)).isoformat()+ 'Z',
                                            singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])
        print('events len:', len(events))
        s="Upcoming in next week (beta version):\n"
        if not events:
            s=s+'No upcoming events found.'
        

        for event in events:
            start = parse(event['start'].get('dateTime', event['start'].get('date')))
            #print(start, datetime.utcnow(),datetime.now().astimezone())
            seconds2go=(start-datetime.utcnow().astimezone()).total_seconds()
            days, hours, minutes = seconds2go //(3600*24), seconds2go // 3600, seconds2go // 60 % 60

            ts=str(days) + ' days '
            ts=ts+ ' and '+ str(hours)+ ' hours' +' and '+str(minutes)+ ' minutes'
            s=s+event.summary+ ' **Starts in:** '+ ts+'\n'
        print('s:',s)
        await message.channel.send(s)


async def makecsvfile(): 
    g=client.guilds[0]
    mem=await g.fetch_members().flatten()
    with open("memberlist.csv",'w') as f:
        for u in mem:
            f.write('"{0}", "{1}", "{2}", "{3}", "{4}"\n'.format(u.display_name,u.id, u.joined_at, ";".join([x.name for x in u.roles]),u.name))

discord_token=os.getenv('DISCORD_KEY')
client.run(discord_token)
