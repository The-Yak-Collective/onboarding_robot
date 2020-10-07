import discord
import base64
import os
client = discord.Client()

mem=[];
@client.event
async def on_ready(): 

    print('We have logged in as {0.user}'.format(client),  client.guilds)#, client.guilds[0].text_channels)
    g=client.guilds[0]
    mem=await g.fetch_members().flatten()
    for u in mem:
        print(u,u.id)
        


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
    if message.content.startswith('$die'):
        exit(0)
discord_token=os.getenv('DISCORD_KEY')
client.run(discord_token)
