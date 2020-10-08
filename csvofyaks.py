import discord
import base64
import os

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
        print(u,u.id)
        
@client.event
async def on_member_join(member):
    print("new member"+str(member.name), flush=True)
    newones.append("new member"+str(member.name))
    me = await client.get_user(747357865513189436)
    await client.send_message(me, "new member"+str(member.name))
    me2 = await client.get_user(710573356759384075)
    await client.send_message(me2, "new member"+str(member.name))
    


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
discord_token=os.getenv('DISCORD_KEY')
client.run(discord_token)
