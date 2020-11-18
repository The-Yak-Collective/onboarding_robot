import discord
import base64

import sys

import pickle
import requests
import os.path
import os
from array import *

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
        await message.channel.trigger_typing()
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
        await message.channel.trigger_typing()
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
            days, hours, minutes = int(seconds2go //(3600*24)), int((seconds2go // 3600) % 24), int(seconds2go // 60 % 60)

            ts=str(days) + ' days and '
            ts=ts+ str(hours)+ ' hours' +' and '+str(minutes)+ ' minutes '
            if days==0:
                ts=ts + '**Today**'
            s=s+event['summary']+ ' **Starts in:** '+ ts+'\n'
        print('s:',s)
        await message.channel.send(s)
    if message.content.startswith('$activity'):
        await message.channel.trigger_typing()
        cmd=message.content.split()
        howfarback=10
        if len(cmd)>1:
            howfarback=int(cmd[1])
        codeformat=False
        if len(cmd)>2 and cmd[2]=="code":
            codeformat=True
        cnt=[[(0,0) for i in range(howfarback//7+1)] for j in range(len(client.guilds[0].text_channels))]
        now=datetime.utcnow()
        wh=now-timedelta(days=howfarback)
        op="activity in the various channels in last {} days:\nshows total and per week reversed (messages, number of mentions) \n".format(howfarback)
        od=[]
        maxlen=len(max(client.guilds[0].text_channels,key=lambda x:len(x.name)).name)
        for idx,ch in enumerate(client.guilds[0].text_channels):
                #print(ch.name)
                try:
                    mess_data=await ch.history(after=wh, limit=None).flatten()
                    for m in mess_data:
                        theweek=(now-m.created_at).days // 7 #last week is always full. first week...
                        #print('the week: ',ch.name, theweek, m.created_at)
                        cnt[idx][theweek]=(cnt[idx][theweek][0]+1,cnt[idx][theweek][1]+len(m.mentions))
                    ws=""
                    for i in range(howfarback //7+1):
                        if codeformat:
                            ws=ws+'({},{}) '.format(str(cnt[idx][i][0]),str(cnt[idx][i][1]))
                        else:
                            ws=ws+'(**{}**,{}) '.format(str(cnt[idx][i][0]),str(cnt[idx][i][1]))
                except:
                    print(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
                    mess_data=''
                    ws='unavailable'
                    print('cannot access channel: ',ch.name)
                tot=len(mess_data)
                if not codeformat:
                    tmp=((ch.name+':').ljust(maxlen)+"   total messages: "+'**'+str(tot).ljust(5)+'**'+'    _weekly_: '+ws, tot)
                else:
                    tmp=((ch.name+':').ljust(maxlen+1)+"   total messages: "+''+str(tot).ljust(5)+''+'    weekly: '+ws, tot)
                od.append(tmp)
                #print(idx,ch.name, cnt[:10])
        od.sort(reverse=True,key=lambda x: x[1])
        
        op=op+"\n".join([x[0] for x in od])
        await splitsend(message.channel,op,codeformat)
    if message.content.startswith('$intro'):#of course intros should be in a local db...
        await message.channel.trigger_typing()
        last_mess=await message.channel.history(limit=1).flatten()
        last_mess=last_mess[0]
        target=message.author.dm_channel
        if (not target): 
            target=await client.get_user(message.author.id).create_dm()
        intro_chan=client.get_channel(692826420191297556)
        intros=await intro_chan.history(limit=None).flatten()
        intro_mess="no intro found"
        for i in intros:
            if i.author==last_mess.author:
                intro_mess=i.content
                break
        await target.send('here is the intro you wanted\n'+s)

async def splitsend(ch,st,codeformat):
    if len(st)<1900: #discord limit is 2k and we want some play)
        if codeformat:
            await ch.send('```'+st+'```')
        else:
            await ch.send(st)
    else:
        x=st.rfind('\n',0,2000)
        if codeformat:
            await ch.send('```'+st[0:x]+'```')
        else:
            await ch.send(st[0:x])
        await splitsend(ch,st[x+1:],codeformat)
    

async def makecsvfile(): 
    g=client.guilds[0]
    mem=await g.fetch_members().flatten()
    with open("memberlist.csv",'w') as f:
        for u in mem:
            f.write('"{0}", "{1}", "{2}", "{3}", "{4}"\n'.format(u.display_name,u.id, u.joined_at, ";".join([x.name for x in u.roles]),u.name))

discord_token=os.getenv('DISCORD_KEY')
client.run(discord_token)
