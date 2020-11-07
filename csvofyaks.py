import discord
import base64
import os
from dotenv import load_dotenv
from icalevents.icalevents import events
from datetime import datetime

load_dotenv('.env')

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
        icalurl='https://calendar.google.com/calendar/ical/o995m43173bpslmhh49nmrp5i4%40group.calendar.google.com/public/basic.ics'
        es=events(icalurl)
        s="Upcoming in next week:\n"
        for y in es:
            tl=y.time_left()
            days, hours, minutes = tl.days, tl.seconds // 3600, tl.seconds // 60 % 60
            ts=str(tl.days) + ' days '
            ts=ts+ ' and '+ str(hours)+ ' hours' +' and '+str(minutes)+ ' minutes'
            s=s+y.summary+ ' starts in: '+ ts+'\n'
        await message.channel.send(s)


async def makecsvfile(): 
    g=client.guilds[0]
    mem=await g.fetch_members().flatten()
    with open("memberlist.csv",'w') as f:
        for u in mem:
            f.write('"{0}", "{1}", "{2}", "{3}", "{4}"\n'.format(u.display_name,u.id, u.joined_at, ";".join([x.name for x in u.roles]),u.name))

discord_token=os.getenv('DISCORD_KEY')
client.run(discord_token)
