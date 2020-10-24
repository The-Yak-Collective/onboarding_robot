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


@tasks.loop(seconds=60.0) #change to 3600 as soon as we see this works. right now at 60, just so we see it happens multipel times
async def test_tick():
    print("does this tick work?",time.time())



load_dotenv('.env')

intents = discord.Intents.default()
intents.members = True


client = discord.Client(intents=intents)

@client.event
async def on_ready(): 

    print('We have logged in as {0.user}'.format(client),  client.guilds)
    await update_database()
    setup_sm(machines)
    test_tick.start() #makes sure we have DB


@client.event
async def on_member_join(member):
    update_db_new_member(member)
    


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    print("i would have checked this message:",message.content, message.channel, message.author.id)
    print(db_c.execute('select * from yakstates where discordid=(?)',(str(message.author.id),)))
    #here add a test facility as well as other stuff
    #most important - add ignore me function in db, so we skip eveything if person asked to be ignored/frozen
    #also parse "$help"


async def update_database(): 
    mem=[]
    g=client.guilds[0]
    lastread=int(time.time())
    conn=sqlite3.connect('statedatabase.db')
    db_c = conn.cursor()
    db_c.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='yakstates' ''')
    if db_c.fetchone()[0]!=1:
        db_c.execute('''CREATE TABLE yakstates
             (discordid text, machine text, state text, startedat int, ignoreme int)''')
        db_c.execute('''CREATE TABLE lastread
             (timestamp int)''')
        mem=await g.fetch_members().flatten()
        for m in machines:
            db_c.executemany('''insert into yakstates values
             (?, ?, ?, ?, ?)''',[(x.id,m[1],m[2],lastread, 0) for x in mem])# new yaks get benifit of doubt... as if they joined just now
        db_c.execute('''UPDATE lastread
             set timestamp=(?)''',(lastread,))
    else:
        db_c.execute('''select * from lastread''')
        prevread=db_c.fetchone()[0]
        mem=await g.fetch_members(after=datetime.datetime.fromtimestamp(prevread-10000)).flatten()
        print("fetched only:",len(mem))
        print("prevread=",prevread)
        for m in machines:
            db_c.execute('''UPDATE lastread
             set timestamp=(?)''',(lastread,))
            mem1=[x for x in mem if datetime.datetime.timestamp(x.joined_at)>prevread]
            print("adding {} members to machine {}".format(len(mem1), m[1]))
            db_c.executemany('''insert into yakstates values
             (?, ?, ?, ?, ?)''',[(x.id,m[1],m[2],lastread,0) for x in mem1])
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