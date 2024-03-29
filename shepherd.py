from discord.ext import tasks, commands
import discord
import asyncio
import os
import time
import datetime
from dotenv import load_dotenv
import sqlite3  #consider , "check_same_thread = False" on sqlite.connect()
from statemachine import * # this includes "machines", a list of machine dicts
from discord_shepherd import *

conn=sqlite3.connect('statedatabase.db') #the connection should be global. 
db_c = conn.cursor()
tick=0


@tasks.loop(seconds=60.0) #change to 3600 as soon as we see this works. right now at 60, just so we see it happens multipel times
async def test_tick():
    global tick
    tick=tick+1
    #print("does this tick work?",time.time(), tick)
    for m in machines:
        for item in m['lut']['on_tick']:
            state=item[0]
            print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nstate in tick:",state, item)
            yaks_it=db_c.execute('select * from yakstates where state=(?) and machine=(?)',(state,m['name']))
            yak_list=[r2yak(x) for x in yaks_it]
            for theyak in yak_list:
                if theyak['ignoreme']!=0:
                    continue;
                print(theyak)
                for trans in m['states'][state]['transitions']:
                    print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\ntrans:",trans)
                    if "on_tick" in trans:
                        print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nfound on_tick")
                        if (trans['on_tick']['run_params'][0]==0) or (tick % trans['on_tick']['run_params'][0]==0):#really, should not be zero...
                            val=await trans['on_tick']['run'](theyak,tick,trans['on_tick']['run_params'][1:])
                            await transition_on(theyak, val, trans['on_tick']['goto'],m)




load_dotenv('/home/yak/.env')


@client.event
async def on_ready(): 

    print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nWe have logged in as {0.user}".format(client),  client.guilds)
    setup_sm() # needs to be first, (or maybe not) as update_database calls on_enter
    await update_database()
    test_tick.start() #makes sure we have DB


@client.event
async def on_member_join(member):
    print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\ni think somebody joined:",member.id)
    await update_db_new_member(member)
    #and now also apply state machine on him? or wait for events? after all, he did just join a state
    


@client.event
async def on_message(message): # a logical problem since the freeze cannot know which machine to freeze. nevermind. maybe will do seperate commands for each. maybe each machine sends a first introductory message with a unique freeze command (one for each machine). later...
    if message.author == client.user:
        return
    print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\ni would have checked this message:",message.content, message.channel, message.author.id)
    if message.content.startswith("$maierme") or message.content.startswith("/maierme"):
        x=client.guilds[0].get_member(765463520389103638)
        await update_db_new_member(x)
    if message.content.startswith("$help") or message.content.startswith("/help"):
        await send_dm({'discordid':message.author.id},0,"help is near. or not, as help feature not implemented yet")
        return
    if message.content.startswith("$freezeme") or message.content.startswith("/freezeme"):
        await send_dm({'discordid':message.author.id},0,"no more messages from this bot for you. dm $unfreezeme to restart")
        db_c.execute('update yakstates set ignoreme=1 where discordid=(?)',(message.author.id,))
        conn.commit()
        return
    if message.content.startswith("$unfreezeme") or message.content.startswith("/unfreezeme"):
        await send_dm({'discordid':message.author.id},0,"know more messages from this bot for you. dm $freezeme to freeze again")
        db_c.execute('update yakstates set ignoreme=0 where discordid=(?)',(message.author.id,))
        conn.commit()
        return

    for m in machines:
        theyak=get_yak_mac(message.author.id,m) #for now we only look at who sent, not who got. 
        if  not theyak:
            print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nmessage from somebody not in db:",message.author.id)
            return 
        if theyak['ignoreme']!=0:
            continue;
        print(theyak, m['lut']['on_message'])
        if theyak['state'] in m['lut']['on_message']:
            for trans in m['states']['transitions']:
                if "on_message" in trans:
                    val=await trans['on_message']['run'](theyak,message,trans['on_message']['run_params'])
                    await transition_on(theyak, val, trans['on_message']['goto'],m)
    
async def transition_on(yak,val,where,m):
    print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\ntransition of {} who is at {} using vector {} with val {} to {}".format(yak['discordid'],yak['state'],where,val, where[val]))
    newstate=where[val]
    if newstate=='':
        return
    db_c.execute('update yakstates set state=(?), startedat=(?) where discordid=(?) and machine=(?)',(newstate,int(time.time()),yak['discordid'],yak['machine']))
    conn.commit()
    await do_on_enter(m,yak,newstate)



async def update_database(): 

    db_c.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='yakstates' ''')
    if db_c.fetchone()[0]!=1:
        db_c.execute('''CREATE TABLE yakstates (discordid text, machine text, state text, startedat int, ignoreme int, roles text)''')
        db_c.execute('''CREATE TABLE lastread (timestamp int)''')
        db_c.execute('''insert into lastread values (?)''',(0,))#(1572048000,)) # last year - before yc and after discord
    await read_and_add()

async def read_and_add():
    lastread=int(time.time())
    mem=[]
    g=client.guilds[0]
    db_c.execute('''select * from lastread''')
    prevread=int(db_c.fetchone()[0])
    print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nprevread=",prevread,datetime.datetime.fromtimestamp(prevread))
#    mem=await g.fetch_members(after=datetime.datetime.fromtimestamp(prevread)).flatten() # reads only ones added since prevread
#    print("fetched only:",len(mem))
#seems datetime might not work, but can try snowflake - timestamp from 1995 epoch <<22. see https://discord.com/developers/docs/reference
    #mem1=await g.fetch_members(limit=10).flatten() # reads only ones added since prevread. for now, limiting to just 10 (to reduce size of potential catastrophe)
    mem1=g.members #fails on api call will try on list. this may fail above 1000 members, and we are getting close
    mem=[x for x in mem1 if x.joined_at.timestamp()>prevread]
    print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nfetched:",len(mem1), "filtered to:",len(mem))

    db_c.execute('''UPDATE lastread
    set timestamp=(?)''',(lastread,)) 
    for m in machines:
        #mem1=[x for x in mem if datetime.datetime.timestamp(x.joined_at)>prevread]
        print(m)
        print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nadding {} members to machine {}".format(len(mem), m['name']))
        db_c.executemany('''insert into yakstates values
         (?, ?, ?, ?, ?, ?)''',[(x.id,m['name'],m['startat'],lastread,0, roles(x)) for x in mem])
        for y in mem:
            yak=get_yak_mac(y.id,m)
            await do_on_enter(m,yak,m['startat']) #maybe move out of loop into its own "do enter", but actually thsi is teh only thing done when entering a state
    conn.commit()
    
async def do_on_enter(mac,yak,state):
    await mac['states'][state]['onenter'](yak,0,mac['states'][state]['onenter_params']) #for now, we ignore any return value here. note the '0', as we have nothing special to say, but want compatibility with on_message (send message) and on_tick (sends the tick parameter

async def update_db_new_member(member):
    x=member
    db_c.execute('select * from yakstates where discordid=(?)',(str(x.id),))
    if not db_c.fetchone(): # is not in db yet
        print(member.id, " not in db yet")
        lastread=int(time.time()) #could not be exectly correct. so one solution is to run fetchall again. another is to check. which we did
        for m in machines:
            print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nbefore insert")
            db_c.execute('''insert into yakstates values
             (?, ?, ?, ?, ?, ?)''',(x.id,m['name'],m['startat'],lastread, 0, roles(x)))# new yaks get benifit of doubt... as if they joined just now

            print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nafter insert")
        db_c.execute('''UPDATE lastread set timestamp=(?)''',(lastread,))
        print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nafter update timestamp")
        conn.commit()
        for m in machines:
            yak=get_yak_mac(x.id,m)
            await do_on_enter(m,yak,m['startat'])
    print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nadd new member to db, if not already in it", member.name, member.id)


def roles(x):
    return ",".join([y.name for y in x.roles])

def get_yak(id):
    r=db_c.execute('select * from yakstates where discordid=(?)',(str(id),)).fetchone()
    return r2yak(r)

def get_yak_mac(id,mac):
    r=db_c.execute('select * from yakstates where discordid=(?) and machine=(?)',(str(id),mac['name'])).fetchone()
    return r2yak(r)
    
def r2yak(r):
    if not r:
        return r
    return {'discordid':int(r[0]), 'machine':r[1],'state':r[2], 'startedat':int(r[3]),'ignoreme':int(r[4]),'roles':r[5].split(',')} 

def setup_sm():
    for m in machines: #make sit easier if machines are a global
        for state in m['states']:
            print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nstate:",state,m['states'][state]['transitions'])
            for trans in m['states'][state]['transitions']:
                print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nand trans:",trans)
                for t in trans:
                    print("---\n[" + datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() + "]\nand t is:",t)
                    m['lut'][t].append((state,trans[t]['run'],trans[t]['run_params'])) #not clear why we need all three


discord_token=os.getenv('SHEPHERD_DISCORD_KEY')
client.run(discord_token) #last command run, apparently execution continues only after async loop is broken
