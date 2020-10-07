import discord
import base64
import os
client = discord.Client()
l=[]

@client.event
async def on_ready(): #note l is used differently in github
    global l
    #print('We have logged in as {0.user}'.format(client),  client.guilds)#, client.guilds[0].text_channels)
    l=[]
    for u in client.guilds[0].members:
      #if('madeyak' in [x.name for x in u.roles]):
        r=[x.name for x in u.roles if x.name !='@everyone']
        l.append((str(u),r))
        listofr=str(r).replace("'"," ").replace(",",";")
        try:
            thename=u.name.encode('utf-8').decode('utf-8','replace').replace(",",";")
        except:
            thename="could not parse"
        try:
            print( thename, ",", u.id, "," ,listofr)
        except:
            print("couldnotprintthisname",",", u.id)

    exit(0)

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
