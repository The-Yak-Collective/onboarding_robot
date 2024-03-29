##yak_scraper robot. current real functins are generating a list of yak members and indicating activities in the YC
##permissions needed are read/write channels, mainly, but also member intents. for now, we are not tracking presence.
##working on converting this to a modular design


import discord
import base64

import re

import sys

import tempfile
import subprocess
import pickle
import requests
import os.path
import os
from array import *

from datetime import datetime, timedelta
from pytz import timezone
import pytz
import time
from dotenv import load_dotenv

from datetime import datetime

##various "global" settings. will move to a configuration file at some point. 

HOMEDIR='/home/yak/'
LOCALDIR=HOMEDIR+'robot/onboarding_robot/'
TRUSTED_ROLE='yaktributor'

##discord specific settings. the discord key is that of the yak_scraper robot and is, for now, in the .env file

DISCORD_KEY='DISCORD_KEY'
INTRO_CHAN=692826420191297556 #channel id where new yaks are supposed to post an introduction about themselves
MAIERSNOWFLAKE=710573356759384075 #so maier can get dm
TWITTER_CHAN= 803272779558420551 #where we put tweets

load_dotenv(HOMEDIR+'.env')

intents = discord.Intents.default()
intents.members = True #if you want memebr data you need to say so in advance
intents.messages=True
intents.message_content=True #and now also to read messages...

client = discord.Client(intents=intents)

#dotenv_path = os.join(dirname(__file__), '.env')
#load_dotenv(dotenv_path)

CK = os.environ.get("CK")
CS = os.environ.get("CS")
ATK = os.environ.get("ATK")
ATS = os.environ.get("ATS")

#same for yakrover for testing
CK2 = os.environ.get("CK2")
CS2 = os.environ.get("CS2")
ATK2 = os.environ.get("ATK2")
ATS2 = os.environ.get("ATS2")

import twitter
twitterapi = twitter.Api(consumer_key=CK,
                  consumer_secret=CS,
                  access_token_key=ATK,
                  access_token_secret=ATS)
twitterapi2 = twitter.Api(consumer_key=CK2,
                  consumer_secret=CS2,
                  access_token_key=ATK2,
                  access_token_secret=ATS2)
                  

newones=[] #we keep track of recently added members. obsolete and should be removed
mem=[]

@client.event
async def on_ready(): 
#connecting to discord takes time and is asynchornous
    print(newlinetimestamp() + "We have logged in as {0.user}".format(client),  client.guilds)#, client.guilds[0].text_channels)
    g=client.guilds[0]
    #mem=await g.fetch_members().flatten() # no need to read until asked
    #for u in mem:
    #    pass #print(u,u.id)
        

@client.event
async def on_member_join(member):
#for now, we track when new members join. but this functionality shoudleb moved to shepherd
    print(newlinetimestamp() + "new member: "+str(member.name), flush=True)
    newones.append("new member"+str(member.name))
    me2 = client.get_user(MAIERSNOWFLAKE).dm_channel #for now send messages to me
    await me2.send("new member: "+str(member.name)+" id: "+str(member.id))
    

def getroles(y):
#helper function to provide array of roles of a member
    mid=client.guilds[0].get_member(y)
    try:
        return [x.name.replace('@','') for x in mid.roles]
    except:
        return []

@client.event
async def on_message(message):
#main workhorse - gets, parses and acts on discord messages meant for robot (must start with "$" or "/")
    if message.author == client.user:
        return
    r=getroles(message.author.id) #used to check permissions
    
    if message.content.startswith('$hello') or message.content.startswith('/hello'):
        await message.channel.send('Hello!')
        print(newlinetimestamp() + "hello mess from "+message.author.name,flush=True);
        
#obselete, will be removed
    if message.content.startswith('$whosenew') or message.content.startswith('/whosenew'):
        await message.channel.send(str(newones))
        
#somebody posted in #introductions
    if message.channel.id==INTRO_CHAN and not message.content[0] in ['$','/']: # a real message in intro
        whoposted=message.author.id
        if 'yak' in getroles(whoposted):
            return #only non yaks are responded to
        yakrole=discord.utils.get(client.guilds[0].roles, name="yak")
        await message.author.add_roles(yakrole)
        target=message.channel #and then we immediatly flip to personal DM - for testing
        target=await dmchan(message.author.id)
        await target.send("Welcome to the Yak Collective Discord server, "+message.author.name)
        with open(LOCALDIR+"/welcomemess") as f:
            themessage=f.read()
        await target.send(themessage)
        #maybe should have a file upload mechanism but see $uploadwelcome below
        return
#upload further message. lets start with plain text
    if message.content.startswith('$uploadwelcome') or message.content.startswith('/uploadwelcome'):
        themessage= message.content.split(maxsplit=1)[1]
        if len(themessage)>0:
            with open(LOCALDIR+"/welcomemess",'w') as f:
                f.write(themessage)
            await message.channel.send('''this is what it will look like''')
            await message.channel.send(themessage)
        else:
            await message.channel.send('''
            please provide a welcome message to upload. plain text, use markdown, etc.''')
        return



#unfurl

    if message.content.startswith('$unfurl') or message.content.startswith('/unfurl'):
        url=message.content.split() #maxsplit=1
        #print("1",url)
        temp_l=len(url)
        print(temp_l,url)
        if temp_l<2:
            await message.channel.send("usage /unfurl discord_URL discord_URL/end")
        else:
            if(temp_l==2):
                try:
                    #print(temp_l,url[1],':',durl2m(url[1]))
                    m,chan,c=await durl2m(url[1])
                    #print("afterdurl")
                    txt=m.content
                    strig="<@"+str(m.author.id)+"> in <#"+chan+">:\n"+txt
                    #print(strig)
                    #await message.channel.send(strig) needs split as message could be long (2k chars. maybe better solution is simply to send two messages? tried it and it does not work. strange)
                    await splitsend(message.channel,strig,False)
                except:
                    await message.channel.send("some bug. are you sure that is a link to a discord message?")
            elif (temp_l==3 and url[2]=="end"):
                try:
                    m,chan,c=await durl2m(url[1])
                    txt=m.content
                    #await message.channel.send("<@"+str(m.author.id)+"> in <#"+chan+">:\n"+txt)
                    strig="<@"+str(m.author.id)+"> in <#"+chan+">:\n"+txt
                    await splitsend(message.channel,strig,False)
                    async for mess in c.history(after=m):
                        txt=mess.content
                        #await message.channel.send("<@"+str(mess.author.id)+"> in <#"+chan+">:\n") #moved txt to next message INSTEAD of using splitsend
                        #await message.channel.send(txt)
                        strig="<@"+str(mess.author.id)+"> in <#"+chan+">:\n"+txt
                        await splitsend(message.channel,strig,False)
                except:
                    await message.channel.send("some bug. are you sure that is a link to a discord message followed by the word 'end'?")
            else:
                try:
                    m1,chan,c=await durl2m(url[1])
                    m2,chan,c=await durl2m(url[2])
                    txt=m1.content
                    #await message.channel.send("<@"+str(m1.author.id)+"> in <#"+chan+">:\n"+txt)
                    strig="<@"+str(m1.author.id)+"> in <#"+chan+">:\n"+txt
                    await splitsend(message.channel,strig,False)
                    async for mess in c.history(after=m1,before=m2):
                        txt=mess.content
                        #await message.channel.send("<@"+str(mess.author.id)+"> in <#"+chan+">:\n"+txt)
                        strig="<@"+str(mess.author.id)+"> in <#"+chan+">:\n"+txt
                        await splitsend(message.channel,strig,False)

                    txt=m2.content
                    #await message.channel.send("<@"+str(m2.author.id)+"> in <#"+chan+">:\n"+txt)
                    strig="<@"+str(m2.author.id)+"> in <#"+chan+">:\n"+txt
                    await splitsend(message.channel,strig,False)
                except:
                    await message.channel.send("some bug. are you sure you gave two discord message urls?")
        return

        
#generates a CSV of all the discord users
    if message.content.startswith('$givemecsv') or message.content.startswith('/givemecsv'):
        if 'yakshaver' not in r and 'yakherder' not in r:
            await message.channel.send('You must be either a yakshaver or yakherder to use this command. Your current roles are: {}'.format(r))
            return
        print(newlinetimestamp() + "working on memberlist")
        await message.channel.trigger_typing() #show that robot is busy
        await makecsvfile()
        await message.channel.send("a csv file of all yaks")
        await message.channel.send("actual file:", file=discord.File("memberlist.csv"))
        
    if message.content.startswith('$test') or message.content.startswith('/test'):
        await message.channel.trigger_typing()
        await message.channel.send("this is a test...")#: "+str([(x.name,x.created_at) for x in message.author.roles]))
#only maier can kill robot from discord, for now
    if ((message.content.startswith('$die!') or message.content.startswith('/die!')) and message.author.id==MAIERSNOWFLAKE):
        exit(0)

#test tool to have robot send a dm to a user. can be deleted
    if message.content.startswith('$dm') or message.content.startswith('/dm'):
        print(newlinetimestamp() + "dm",flush=True);
        t=int(message.content[3:])
        target=await dmchan(t)
        print(newlinetimestamp() + "target is:",target,flush=True)    
        await target.send('Hello! i was told by '+message.author.name+' to contact you')
        
#show activity in channels
    if message.content.startswith('$activity') or message.content.startswith('/activity'):
        await do_activity(message,r)
        return
#show activity of yaks
    if message.content.startswith('$noise') or message.content.startswith('/noise') or message.content.startswith('$signal') or message.content.startswith('/signal'):
        await do_noise(message,r)
        return
#get links per phil's request
    if message.content.startswith('$links') or message.content.startswith('/links'):
        await do_links(message,r,'csv')
        return
    if message.content.startswith('$lunks') or message.content.startswith('/lunks') or message.content.startswith('$mlinks') or message.content.startswith('/mlinks'):
        await do_links(message,r,'markdown')
        return
    if message.content.startswith('$hlinks') or message.content.startswith('/hlinks'):
        await do_links(message,r,'html')
        return
#send tweet 
    if message.content.startswith('$yaktweet') or message.content.startswith('/yaktweet'):
        dm_chan=await dmchan(message.author.id) #report by DM
        print(newlinetimestamp() + "tweet "+message.content)
        if TRUSTED_ROLE in r:
            print(newlinetimestamp() + TRUSTED_ROLE)
            #send tweet
            conts=message.content.split(maxsplit=1)[1]
            txt=(conts+' #yakbot')[:280]
            ##check if ONE attachment. if yes, save it and then post it
            if (len(message.attachments)>0):
                print(newlinetimestamp() + "has attachment")
                fp=tempfile.NamedTemporaryFile()
                print(newlinetimestamp() + "opened file {}".format(fp.name))
                await message.attachments[0].save(fp.file)
                fp.flush() #does this help? some images workand some not without command
                status = twitterapi.PostUpdate(txt,media=fp.name)
                fp.close()
            else:
            ###here we tweet just text
                status = twitterapi.PostUpdate(txt)
            print(status.text)
            #post the tweet and sender in tweeter channel
            ch=client.get_channel(TWITTER_CHAN)
            await ch.send('<@{0}> sent a tweet: {1}'.format(message.author.id, txt))
            await dm_chan.send('tweet tweeted:'+txt)
            
        else:
            await dm_chan.send('sorry, you need to be a "madeyak" to tweet.')
            print(str(message.author.id)+' is not a madeyak:',r)
        return
#from here tweet TEST using iamz1 info
    if message.content.startswith('$yaktwit') or message.content.startswith('/yaktwit'):
        dm_chan=await dmchan(message.author.id) #report by DM
        print(newlinetimestamp() + "tweet "+message.content)
        if 'madeyak' in r:
            print(newlinetimestamp() + "madeyak")
            #send tweet
            conts=message.content.split(maxsplit=1)[1]
            txt=(conts+' #yakbot')[:280]
            ##check if ONE attachment. if yes, save it and then post it
            if (len(message.attachments)>0):
                print(newlinetimestamp() + "has attachment")
                fp=tempfile.NamedTemporaryFile(delete=False)
                print(newlinetimestamp() + "opened file {}".format(fp.name))
                n=fp.name
                await message.attachments[0].save(fp.file)
                fp.close()
                status = twitterapi2.PostUpdate(txt,media=n)
                #fp.close()
            else:
            ###here we tweet just text
                status = twitterapi2.PostUpdate(txt)
                pass
            print(status.text)
            #post the tweet and sender in tweeter channel
            try:
                ch=client.get_channel(TWITTER_CHAN)
                await ch.send('<@{0}> sent a twit: {1}'.format(message.author.id, txt))
            except:
                pass
            await dm_chan.send('twit tweeted:'+txt)
            
        else:
            await dm_chan.send('sorry, you need to be a "madeyak" to tweet.')
            print(str(message.author.id)+' is not a madeyak:',r)
        return
#beta feature - help yaks learn about other yaks. for now show info in introduction chan.  and only of last message. later show data from knack and of all people in last message. consider deleting the message itself OR working on message ID in a private channel, so yak can be circumspect
    if message.content.startswith('$intro') or message.content.startswith('/intro'):#of course intros should be in a local db...
        await message.channel.trigger_typing() #say you are busy
        last_mess=await message.channel.history(limit=1).flatten() #get last message
        last_mess=last_mess[0]
        target=await dmchan(message.author.id) #answer by DM
#scan intro channel
        intro_chan=client.get_channel(INTRO_CHAN)
        intros=await intro_chan.history(limit=None, oldest_first=True).flatten()
        intro_mess="no intro found"
        for i in intros:
            if i.author==last_mess.author:
                intro_mess=i.content
                break
        s=intro_mess
        await target.send('here is the intro you wanted\n'+s)
        return
#vinay idea - per user history
#beta feature - help yaks learn about other yaks. for now show message history of a single user.  and only of last message. later show data from knack and of all people in last message. consider deleting the message itself OR working on message ID in a private channel, so yak can be circumspect
    if message.content.startswith('$pintro') or message.content.startswith('/pintro'):
        cmd=message.content.split()
        howfarback=10
        if len(cmd)>1:
            howfarback=int(cmd[1])
        now=datetime.utcnow()
        wh=now-timedelta(days=howfarback)
        print(wh,howfarback)
        await message.channel.trigger_typing() #say you are busy
        last_mess=await message.channel.history(limit=2).flatten() #get last message author
        last_author=last_mess[1].author
        print(last_mess[1].content)
        target=await dmchan(message.author.id) #answer by DM
#scan author's history
        who=client.get_user(MAIERSNOWFLAKE)#last_author
        messes=await who.history(limit=None, after=wh).flatten()
        counts={}
        print(len(messes))
        for m in messes:
            print(m.channel)
            x=m.channel
            try:
                y=x.name
            except:
                y="unable"
            counts[y]=counts.get(y,0)+1
        s=""
        for x in counts:
            s=s+"channel {}: count:{}\n".format(x,counts[x])
        if len(s)==0:
            s="no activity found"
        await target.send('here is the activity of {}:\n'.format(last_author.name)+s)
        return
#try 2
    if message.content.startswith('$qintro') or message.content.startswith('/qintro'):
        cmd=message.content.split()
        howfarback=10
        howmany=5
        if len(cmd)>1:
            howfarback=int(cmd[1])
        if len(cmd)>2:
            howmany= int(cmd[2])
        now=datetime.utcnow()
        wh=now-timedelta(days=howfarback)
        print(wh,howfarback)
        await message.channel.trigger_typing() #say you are busy
        last_mess=await message.channel.history(limit=2).flatten() #get last message author
        last_author=last_mess[1].author
        print(last_mess[1].content,last_author,last_author.id)
        target=await dmchan(message.author.id) #answer by DM
#scan author's history
        counts={}
        for ch in client.guilds[0].text_channels:
            mess_data=await ch.history(after=wh, limit=None).flatten()
            #print(len(mess_data))
            for m in mess_data:
                #print(m,m.channel,m.author)
                #print(m.author.id,last_author.id)
                if m.author.id==last_author.id:
                    #print("made it in!")
                    x=m.channel
                    try:
                        y=x.name
                    except:
                        y="unable"
                    counts[y]=counts.get(y,0)+1
        s=""
        od=[]
        op=""
        for x in counts:
            tmp=("channel {}:        count:{} \n".format(x,counts[x]),counts[x])
            od.append(tmp)
        od.sort(reverse=True,key=lambda x: x[1])
        od_filtered=(od[0:howmany] if howmany>0 else od[howmany:]) #head or tail
        op=op+" \n".join([x[0] for x in od_filtered])
        await splitsend(target,op,True)

        return
#show help message
    if message.content.startswith('$help') or message.content.startswith('/help') or message.content.startswith('$howto') or message.content.startswith('/howto'):
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
                    #print("the week: "",ch.name, theweek, m.created_at)
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
                print(newlinetimestamp() + "cannot access channel: ",ch.name)
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

async def durl2m(u):
    print(u)
    url=u.split("/")
    url=list(reversed(url))
    print(url)
    c=client.guilds[0].get_channel(int(url[1]))
    m=await c.fetch_message(int(url[0]))
    return m,url[1],c


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
        try:
            mess_data=await ch.history(after=wh, limit=None).flatten()
        except:
            mess_data=[] #so will skip next for
            print ("unable to read hist of chan:",ch.id)
        for m in mess_data:
            idx=m.author.id
            theweek=(now-m.created_at).days // 7 
            try:
                cnt[idx]['weekly'][theweek]+=1
                cnt[idx]['tot']+=1
            except: #probbaly fail for users who left server
                print(newlinetimestamp() + "failed for ",idx)
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

async def do_links(message,r,proc): 
#sort yaks by number of messages they send
    if False: #if 'yakshaver' not in r and 'yakherder' not in r:
        await message.channel.send('You must be either a yakshaver or yakherder to use this command. Your current roles are: {}'.format(r))
        return
    await message.channel.trigger_typing()
    if (proc == 'markdown') or (proc == 'html'):
        await message.channel.send('wait for two files to arrive. may be a brief while.')
    elif (proc == 'csv'):
        await message.channel.send('wait for one file to arrive. not too slow.')
#parse command
    cmd=message.content.split()
    howfarback=10
    codeformat=False
    
    if len(cmd)>1:
        howfarback=int(cmd[1])


    now=datetime.utcnow()
    wh=now-timedelta(days=howfarback)
    op="links in yak collective. last {} days:\n".format(howfarback)
    
    od=[] # here we will store link results
    regex=re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
#get and review messages
    for ch in client.guilds[0].text_channels:
        try:
            mess_data=await ch.history(after=wh, limit=None).flatten()
        except:
            mess_data=[] #so will skip next for
            print ("unable to read hist of chan:",ch.id)
        for m in mess_data:
            idx=m.author.id
            cont=m.content
            urls = regex.findall(cont)
            timestamp=m.created_at
            linkto=m.jump_url
            if urls:
                od.append((ch.name,timestamp,linkto,urls))
    with open(LOCALDIR+"links.csv",'w') as f:
        f.write(op)
        for u in od:
            f.write('"{0}","{1}","{2}","{3}"\n'.format(u[0],u[1], u[2], "; ".join([x for x in u[3]])))
    if (proc == 'csv'):
        await message.channel.send("a file of recent links:", file=discord.File(LOCALDIR+"links.csv"))
    elif (proc == 'markdown') or (proc == 'html'):
        thestringlist=['/bin/bash', 'tweetthelist.bash', "links.csv"] #using nathan's utility
        out = subprocess.Popen(thestringlist, 
           cwd=LOCALDIR,
           stdout=subprocess.PIPE, 
           stderr=subprocess.STDOUT)
        stdout,stderr = out.communicate() #waits for it to finish
        #print("stderr?:"+stderr)
        await message.channel.send("a file of extracted tweets from recent links:", file=discord.File(LOCALDIR+"tweets.csv"))
        print(newlinetimestamp() + "twits sent")
        if (proc == 'markdown'):
            thestringlist=['/bin/bash', 'markdownthelist.bash', "links.csv"] #using nathan's utility
            out = subprocess.Popen(thestringlist, 
               cwd=LOCALDIR,
               stdout=subprocess.PIPE, 
               stderr=subprocess.STDOUT)
            print(newlinetimestamp() + "asked for titles")
            stdout,stderr = out.communicate() #waits for it to finish
            #print("stderr?:"+stderr)
            await message.channel.send("a file of extracted titles from recent links (markdown):", file=discord.File(LOCALDIR+"links.md"))
            print(newlinetimestamp() + "titles sent")
        elif (proc == 'html'):
            thestringlist=['/bin/bash', 'htmlthelist.bash', "links.csv"] #using nathan's utility
            out = subprocess.Popen(thestringlist, 
               cwd=LOCALDIR,
               stdout=subprocess.PIPE, 
               stderr=subprocess.STDOUT)
            print(newlinetimestamp() + "asked for titles")
            stdout,stderr = out.communicate() #waits for it to finish
            #print("stderr?:"+stderr)
            await message.channel.send("a file of extracted titles from recent links (html):", file=discord.File(LOCALDIR+"links.html"))
            print(newlinetimestamp() + "titles sent")
    return



async def dmchan(t):
#generate a dmc hannel to a yak, if needed
    target=client.get_user(t).dm_channel
    if (not target): 
        print(newlinetimestamp() + "need to create dm channel",flush=True)
        target=await client.get_user(t).create_dm()
    return target


async def servefiles(hf,hd,ow,m, ext):
#show a textfile form server on discord, with some anti-injection defences
#hf=file, hd=directory, ow= toplevel or detailed level directory, m=message data, ext = what file extension to use
    target=await dmchan(m.author.id)
    if ow=='':
        with open(LOCALDIR+re.sub('^.*[^\w]', '', hf)+ext) as f:
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
#might it have a bug of dropping last space and last line?
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

def newlinetimestamp():
    return "---\n[" + kindatimestamp() +  "]\n"
    
def kindatimestamp():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()

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
