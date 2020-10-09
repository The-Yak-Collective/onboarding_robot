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

        

    me = await client.get_user(747357865513189436)
    await client.send_message(me, "new member"+str(member.name))
    me2 = await client.get_user(710573356759384075)
    await client.send_message(me2, "new member"+str(member.name))
    


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$test'):
      me = await client.get_user(747357865513189436)
      await client.send_message(me, "a test message")
      me2 = await client.get_user(710573356759384075)
      await client.send_message(me2, "a test message")
    if message.content.startswith('$hello'):
        await message.channel.send('Hello too!')
    if message.content.startswith('$die!'):
        exit(0)
discord_token=os.getenv('DISCORD_KEY')
client.run(discord_token)
