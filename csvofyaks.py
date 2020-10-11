import discord
import base64
import os
from dotenv import load_dotenv

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
    mem=await g.fetch_members().flatten()
    for u in mem:
        pass #print(u,u.id)
        
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
    if message.content.startswith('$whosenew'):
        await message.channel.send(str(newones))
    if message.content.startswith('$die!'):
        exit(0)
    if message.content.startswith('$dm'):
        print("dm",flush=True);
        t=int(message.content[3:])
        target=client.get_user(t).dm_channel
        if (not target):
            print("need to create dm channel")
            target=await client.get_user(t).create_dm()
        print("target is:",target)    
        await target.send('Hello! i was told by '+message.author+' to contact you')

discord_token=os.getenv('DISCORD_KEY')
client.run(discord_token)
