from discord.ext import tasks, commands
import discord
import asyncio
import os
import time
import datetime
from dotenv import load_dotenv
import sqlite3  #consider , "check_same_thread = False" on sqlite.connect()
from statemachine import * # this includes "machines", a list of machine dicts

conn=0 #the connection should be global. curso, etc, also, but not so much
db_c=0 #cursor

class MyCog(commands.Cog):
    def __init__(self):
        self.index = 0
        self.on_tick.start()

    def cog_unload(self):
        self.on_tick.cancel()

    @tasks.loop(seconds=30.0) #change to 3600 as soon as we see this works
    async def on_tick():
        #check that db loaded... if not it means bot is not ready yet
        print("check if any on_ticks need to be run, check first run_params for tick count to decide IF to run", index)

@tasks.loop(seconds=13.0) #change to 3600 as soon as we see this works
async def test_tick():
    print("does this tick work?",time.time())
test_tick.start()


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
    print("i would have checked this message:",message.content, message.channel)
    #here add a test facility as well as other stuff
    #most important - add ignore me function in db, so we skip eveything if person asked to be ignored/frozen
    #also parse "$help"


async def update_database(): 
    mem=[]
    g=client.guilds[0]
    lastread=int(time.time())
    mem=await g.fetch_members().flatten()
    conn=sqlite3.connect('statedatabase.db')
    db_c = conn.cursor()
    db_c.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='yakstates' ''')
    if db_c.fetchone()[0]!=1:
        db_c.execute('''CREATE TABLE yakstates
             (discordid text, machine text, state text, startedat int)''')
        db_c.execute('''CREATE TABLE lastread
             (timestamp int)''')
        for m in machines:
            db_c.executemany('''insert into yakstates values
             (?, ?, ?, ?)''',[(x.id,m[1],m[2],lastread) for x in mem])# new yaks get benifit of doubt... as if they joined just now
        db_c.execute('''UPDATE lastread
             set timestamp=(?)''',(lastread,))
    else:
        db_c.execute('''select * from lastread''')
        prevread=db_c.fetchone()[0]
        print("prevread=",prevread)
        for m in machines:
            db_c.execute('''UPDATE lastread
             set timestamp=(?)''',(lastread,))
            mem1=[x for x in mem if datetime.datetime.timestamp(x.joined_at)>prevread]
            print("adding {} members to machine {}".format(len(mem1), m[1]))
            db_c.executemany('''insert into yakstates values
             (?, ?, ?, ?)''',[(x.id,m[1],m[2],lastread) for x in mem1])
    conn.commit()

def update_db_new_member(member):
    print('add new member to db, if not already in it')

    #read database

def setup_sm(x):
    pass

discord_token=os.getenv('SHEPHERD_DISCORD_KEY')
client.run(discord_token)
#loop = asyncio.get_event_loop() #need to make sure this doe snot clash with discord
#loop.run_until_complete(on_tick())
#loop.close()
print("should i get here")