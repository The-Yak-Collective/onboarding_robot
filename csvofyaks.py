##yak_scraper robot. current real functins are generating a list of yak members, indicating activities in the YC and reporting on upcoming events
##permissions needed are read/write channels, mainly, but also member intents. for now, we are not tracking presence.
##working on converting this to a modular design


import discord
import base64

import re

import sys

import pickle
import requests
import os.path
import os
from array import *

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

from datetime import datetime

##various "global" settings. will move to a configuration file at some point. 

HOMEDIR='/home/yak/'
LOCALDIR=HOMEDIR+'robot/onboarding_robot/'
CALID='o995m43173bpslmhh49nmrp5i4@group.calendar.google.com' #yakcollective google calender id

##discord specific settings. the discord key is that of the yak_scraper robot and is, for now, in the .env file

DISCORD_KEY='DISCORD_KEY'
INTRO_CHAN=692826420191297556 #channel id where new yaks are supposed to post an introduction about themselves
MAIERSNOWFLAKE=710573356759384075 #so maier can get dm

load_dotenv(HOMEDIR+'.env')

intents = discord.Intents.default()
intents.members = True #if you want memebr data you need to say so in advance


client = discord.Client(intents=intents)


newones=[] #we keep track of recently added members. obsolete and should be removed
mem=[]

@client.event
async def on_ready(): 
#connecting to discord takes time and is asynchornous
    print('We have logged in as {0.user}'.format(client),  client.guilds)#, client.guilds[0].text_channels)
    g=client.guilds[0]
    #mem=await g.fetch_members().flatten() # no need to read until asked
    #for u in mem:
    #    pass #print(u,u.id)
        

@client.event
async def on_member_join(member):
#for now, we track when new members join. but this functionality shoudleb moved to shepherd
    print("new member: "+str(member.name), flush=True)
    newones.append("new member"+str(member.name))
    me2 = client.get_user(MAIERSNOWFLAKE).dm_channel #for now send messages to me
    await me2.send("new member: "+str(member.name)+" id: "+str(member.id))
    

def getroles(y):
#helper function to provide array of roles of a member
    mid=client.guilds[0].get_member(y)
    return [x.name for x in mid.roles]

@client.event
async def on_message(message):
#main workhorse - gets, parses and acts on discord messages meant for robot (must start with "$")
    if message.author == client.user:
        return
    r=getroles(message.author.id) #used to check permissions
    
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
        print("hello mess from "+message.author.name,flush=True);
        
#obselete, will be removed
    if message.content.startswith('$whosenew'):
        await message.channel.send(str(newones))
        
#generates a CSV of all the discord users
    if message.content.startswith('$givemecsv'):
        if 'yakshaver' not in r and 'yakherder' not in r:
            await message.channel.send('You must be either a yakshaver or yakherder to use this command. Your current roles are: {}'.format(r))
            return
        print("working on memberlist")
        await message.channel.trigger_typing() #show that robot is busy
        await makecsvfile()
        await message.channel.send("a csv file of all yaks")
        await message.channel.send("actual file:", file=discord.File("memberlist.csv"))
        
    if message.content.startswith('$test'):
        await message.channel.trigger_typing()
        await message.channel.send("this is a test...")#: "+str([(x.name,x.created_at) for x in message.author.roles]))
#only maier can kill robot from discord, for now
    if (message.content.startswith('$die!') and message.author.id==MAIERSNOWFLAKE):
        exit(0)

#test tool to have robot send a dm to a user. can be deleted
    if message.content.startswith('$dm'):
        print("dm",flush=True);
        t=int(message.content[3:])
        target=await dmchan(t)
        print("target is:",target,flush=True)    
        await target.send('Hello! i was told by '+message.author.name+' to contact you')
        
#generate a list of upcming events in next week
    if message.content.startswith('$upcoming'):
        await message.channel.trigger_typing() #show that robot is busy
#this part copied form google quickstart. basically, use credentials and ask for new ones if they expired or are missing

        creds = None
        if os.path.exists(HOMEDIR+'token.pickle'):
            with open(HOMEDIR+'token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('yc-credentials.json', SCOPES)
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
        print('events len:', len(events))
        
#generate a message string
        s="Upcoming in next week (beta version):\n"
        if not events:
            s=s+'No upcoming events found.'
        

        for event in events:
#for each event figure out how long until it starts and generate a nice (?) format of it
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
        
#shwo activity in channels
    if message.content.startswith('$activity'):
        await do_activity(message,r)
        return
#show activity of yaks
    if message.content.startswith('$noise'):
        await do_noise(message,r)
        return

#beta feature - help yaks learn about other yaks. for now show info in introduction chan.  and only of last message. later show data from knack and of all people in last message. consider deleting the message itself OR working on message ID in a private channel, so yak can be circumspect
    if message.content.startswith('$intro'):#of course intros should be in a local db...
        await message.channel.trigger_typing() #say you are busy
        last_mess=await message.channel.history(limit=1).flatten() #get last message
        last_mess=last_mess[0]
        target=await dmchan(message.author.id) #answer by DM
#scan intro channel
        intro_chan=client.get_channel(INTRO_CHAN)
        intros=await intro_chan.history(limit=None).flatten()
        intro_mess="no intro found"
        for i in intros:
            if i.author==last_mess.author:
                intro_mess=i.content
                break
        s=intro_mess
        await target.send('here is the intro you wanted\n'+s)
        return
#show help message
    if message.content.startswith('$help') or message.content.startswith('$howto'):
        sp=message.content.split()
        if len(sp)==1:
            sp.append('')
        await servefiles(sp[0][1:]+'file',sp[0][1:]+'_files',sp[1],message,'.txt')
        return

#actually do the activity detection
async def do_activity(message,r):
    if 'yakshaver' not in r and 'yakherder' not in r: #can be replaced by a permission function as in gigayak
        await message.channel.send('You must be either a yakshaver or yakherder to use this command. Your current roles are: {}'.format(r))
        return
    await message.channel.trigger_typing()
#parse message + defaults. consider making this into a helper function
    cmd=message.content.split()
    howfarback=10
    if len(cmd)>1:
        howfarback=int(cmd[1])
    codeformat=False
    if len(cmd)>2 and cmd[2]=="code":
        codeformat=True
#initialize count array
    cnt=[[(0,0) for i in range(howfarback//7+1)] for j in range(len(client.guilds[0].text_channels))]
#read channels
    now=datetime.utcnow()
    wh=now-timedelta(days=howfarback)
    op="activity in the various channels in last {} days:\nshows total and per week reversed (messages, number of mentions) \n".format(howfarback)
    od=[] #array of collected channel data
    maxlen=len(max(client.guilds[0].text_channels,key=lambda x:len(x.name)).name) #read max channel name so we can print nicely
    for idx,ch in enumerate(client.guilds[0].text_channels):
            #print(ch.name)
            try: # some channels cannot be accessed
                mess_data=await ch.history(after=wh, limit=None).flatten()
                for m in mess_data:
                    theweek=(now-m.created_at).days // 7 #last week is always full. first week...
                    #print('the week: ',ch.name, theweek, m.created_at)
                    cnt[idx][theweek]=(cnt[idx][theweek][0]+1,cnt[idx][theweek][1]+len(m.mentions)) #update count with number of messages and with number of mentions in each message
                ws=""
                for i in range(howfarback //7+1):
                    if codeformat: #generate format string based on format option, per channel
                        ws=ws+'({},{}) '.format(str(cnt[idx][i][0]),str(cnt[idx][i][1]))
                    else:
                        ws=ws+'(**{}**,{}) '.format(str(cnt[idx][i][0]),str(cnt[idx][i][1]))
            except: #print error so we can trace channel problems
                print(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
                mess_data=''
                ws='unavailable'
                print('cannot access channel: ',ch.name)
            tot=len(mess_data)
            if not codeformat: # more format string
                tmp=((ch.name+':').ljust(maxlen)+"   total messages: "+'**'+str(tot).ljust(5)+'**'+'    _weekly_: '+ws, tot)
            else:
                tmp=((ch.name+':').ljust(maxlen+1)+"   total messages: "+''+str(tot).ljust(5)+''+'    weekly: '+ws, tot)
            od.append(tmp) #sort by number of messages
            #print(idx,ch.name, cnt[:10])
    od.sort(reverse=True,key=lambda x: x[1])
    
    op=op+"\n".join([x[0] for x in od])
    await splitsend(message.channel,op,codeformat) #is probbaly longer than 2k chars, so split

async def do_noise(message,r): 
#sort yaks by number of messages they send
    if 'yakshaver' not in r and 'yakherder' not in r:
        await message.channel.send('You must be either a yakshaver or yakherder to use this command. Your current roles are: {}'.format(r))
        return
    await message.channel.trigger_typing()

#parse command
    cmd=message.content.split()
    howfarback=10
    howmany= -20 #twenty least active (negaive number is from end, positive from start)
    codeformat=True #always code mode, so it looks nice

    if len(cmd)>1:
        howfarback=int(cmd[1])
    if len(cmd)>2:
        howmany= int(cmd[2])

    ml=client.guilds[0].members
    cnt={k.id:{'name':k.name, 'tot':0, 'weekly':[0 for i in range(howfarback//7+1)], 'roles': getroles(k.id)} for k in ml} #initialize dict, used for easy indexing by user id

    now=datetime.utcnow()
    wh=now-timedelta(days=howfarback)
    op="activity of members last {} days:\n shows total and per week reversed for {} \n".format(howfarback, str(abs(howmany)) + ' top' if howmany>0 else ' bottom')
    
    od=[] # here we will store yak results
    maxlen=len(max(client.guilds[0].members,key=lambda x:len(x.name)).name) # for nice formatting, need name length

#count messages each user sent
    for ch in client.guilds[0].text_channels:
        mess_data=await ch.history(after=wh, limit=None).flatten()
        for m in mess_data:
            idx=m.author.id
            theweek=(now-m.created_at).days // 7 
            try:
                cnt[idx]['weekly'][theweek]+=1
                cnt[idx]['tot']+=1
            except: #probbaly fail for users who left server
                print('failed for ',idx)
#format answer
    for k in cnt:
        ws=""
        for i in range(howfarback //7+1):
            ws=ws+'({}) '.format(str(cnt[k]['weekly'][i]))
        tmp=((cnt[k]['name']+':').ljust(maxlen+1)+"   tot: "+''+str(cnt[k]['tot']).ljust(5)+''+'    weekly: '+ws+ 'roles:'+str(cnt[k]['roles']), cnt[k]['tot'])
        od.append(tmp)
#sort yaks by activity
    od.sort(reverse=True,key=lambda x: x[1])
    od_filtered=(od[0:howmany] if howmany>0 else od[howmany:]) #head or tail
    op=op+"\n".join([x[0] for x in od_filtered])
    await splitsend(message.channel,op,codeformat)



async def dmchan(t):
#generate a dmc hannel to a yak, if needed
    target=client.get_user(t).dm_channel
    if (not target): 
        print("need to create dm channel",flush=True)
        target=await client.get_user(t).create_dm()
    return target


async def servefiles(hf,hd,ow,m, ext):
#show a textfile form server on discord, with some anti-injection defences
#hf=file, hd=directory, ow= toplevel or detailed level directory, m=message data, ext = what file extension to use
    target=await dmchan(m.author.id)
    if ow=='':
        with open(LOCALDIR+re.sub('^.*[^\w]', '', hf)+'ext') as f:
            s=f.read()
        await splitsend(target,s,False)
    else:
        fname=LOCALDIR+'/'+hd+'/'+re.sub('^.*[^\w]', '', ow)+ext
        if os.path.exists(fname):
            with open(fname) as f:
                s=f.read()
            await splitsend(target,s,False)
        else:
            s="Sorry, no help exists for that"
            await splitsend(target,s,False)

async def splitsend(ch,st,codeformat):
#send data in chunks smaller than 2k
    if len(st)<1900: #discord limit is 2k and we want some play)
        if codeformat:
            await ch.send('```'+st+'```')
        else:
            await ch.send(st)
    else:
        x=st.rfind('\n',0,1900)
        if codeformat:
            await ch.send('```'+st[0:x]+'```')
        else:
            await ch.send(st[0:x])
        await splitsend(ch,st[x+1:],codeformat)
    

async def makecsvfile(): 
#create csv file from discord member data
#u.name still breaks csv a bit
#date not in best of formats
    g=client.guilds[0]
    mem=await g.fetch_members().flatten()
    with open("memberlist.csv",'w') as f:
        for u in mem:
            f.write('"{0}", "{1}", "{2}", "{3}", "{4}"\n'.format(u.display_name,u.id, u.joined_at, ";".join([x.name for x in u.roles]),u.name))

discord_token=os.getenv(DISCORD_KEY)
client.run(discord_token) #discord loop
