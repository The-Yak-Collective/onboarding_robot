from discord.ext import tasks, commands
import discord
import asyncio
import os
from dotenv import load_dotenv
import sqlite3  #consider , "check_same_thread = False" on sqlite.connect()
from statemachine import * # this includes "machines", a list of machine dicts

class MyCog(commands.Cog):
    def __init__(self):
        self.index = 0
        self.on_tick.start()

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=3600.0)
    async def on_tick():
        #check that db loaded... if not it means bot is not ready yet
        print("check if any on_ticks need to be run, check first run_params for tick count to decide IF to run")


load_dotenv('.env')

intents = discord.Intents.default()
intents.members = True


client = discord.Client(intents=intents)

@client.event
async def on_ready(): 

    print('We have logged in as {0.user}'.format(client),  client.guilds)
    await update_database()
    setup_sm(machines)
        

@client.event
async def on_member_join(member):
    update_db_new_member(member)
    


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    #here add a test facility as well as other stuff
    #most important - add ignore me function in db, so we skip eveything if person asked to be ignored/frozen
    #also parse "$help"


async def update_database(): 
    g=client.guilds[0]
    mem=await g.fetch_members().flatten()

def setup_sm():
    pass

discord_token=os.getenv('SHEPHERD_DISCORD_KEY')
client.run(discord_token)
loop = asyncio.get_event_loop() #need to make sure this doe snot clash with discord
loop.run_until_complete(on_tick())
loop.close()