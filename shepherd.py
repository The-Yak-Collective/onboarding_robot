from discord.ext import tasks, commands
import discord
import asyncio
import os
import time
import datetime
from dotenv import load_dotenv
import sqlite3  #consider , "check_same_thread = False" on sqlite.connect()
from statemachine import * # this includes "machines", a list of machine dicts

conn=sqlite3.connect('statedatabase.db') #the connection should be global. 
db_c = conn.cursor()


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
    #and now also apply state machine on him? or wait for events? after all, he did just join a state
    


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
#    db_c = conn.cursor()
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
            for y in mem:
                do_on_enter(m,y)
        db_c.execute('''UPDATE lastread
             set timestamp=(?)''',(lastread,))
    else:
        db_c.execute('''select * from lastread''')
        prevread=db_c.fetchone()[0]
        mem=await g.fetch_members(after=datetime.datetime.fromtimestamp(prevread)).flatten() # reads only ones added since prevread
        print("fetched only:",len(mem))
        print("prevread=",prevread)
        for m in machines:
            db_c.execute('''UPDATE lastread
             set timestamp=(?)''',(lastread,))
            #mem1=[x for x in mem if datetime.datetime.timestamp(x.joined_at)>prevread]
            print("adding {} members to machine {}".format(len(mem), m[1]))
            db_c.executemany('''insert into yakstates values
             (?, ?, ?, ?, ?)''',[(x.id,m[1],m[2],lastread,0) for x in mem])
            for y in mem:
                do_on_enter(m,y,m[2])
    conn.commit()

def update_db_new_member(member):
    x=member
#    db_c=conn.cursor()
    db_c.execute('select * from yakstates where discordid=(?)',(str(x.id),))
    if not db_c.fetchone(): # is not in db yet
        print(member.id, " not in db yet")
        lastread=int(time.time()) #could not be exectly correct. so one solution is to run fetchall again. another is to check. which we did
        for m in machines:
            db_c.execute('''insert into yakstates values
             (?, ?, ?, ?, ?)''',(x.id,m[1],m[2],lastread, 0))# new yaks get benifit of doubt... as if they joined just now
        db_c.execute('''UPDATE lastread
             set timestamp=(?)''',(lastread,))
        conn.commit()
        for m in machines:
            do_on_enter(m,x,m[2])
    print('add new member to db, if not already in it', member.name, member.id)

def do_on_enter(m,x,state): # run when entering any new state, especially first one...
    print("here we run the on_enter function")
    print(m[1], state, m[0][state].onenter.__name__, m[0][state].onenter_params)


    #read database

def setup_sm(x):
    pass

discord_token=os.getenv('SHEPHERD_DISCORD_KEY')
client.run(discord_token)
#loop = asyncio.get_event_loop() #need to make sure this doe snot clash with discord
#loop.run_until_complete(on_tick())
#loop.close()
print("should i get here")