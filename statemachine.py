#anyway, state table is a dict, where each item is a state, with id, function to run when entering  state , with array of parameters - useful, for example, for "add role" function.  most important is a list of state transitions, each one includes a type (like on_message) which is an actual function, a function that returns a number, an array of parameters to give that function (or teh parent "type" function) and an array of states you go to according to these values. 
#we also have ticks every hour, so we can set things to do when tick count is mod that number. tick count is per yak!

#for each type, we have an array for each state table. the array includes the states which care about that type. when running and the event occurs, if it is an on_tick event (not triggered by a user, i can imagine there are others) we see which states care about the event. then, for each state, we extract all the yaks in that state AND which do not say "exclude me". then, we call teh function, FOR THAT USER, with teh parameters and go to where result sends up.
#if it is an event triggered by a user (like a message), we can simply check in db that he is not 'frozen" and run the function in the state table, accorindg to his state (taken form db), if relevant

import discord



#here be functions used in the above state table. note they are called by predefined functions, like "on_message"
#all are async because some are async and no way of knowing which is which. but they can probbaly all run in parallel, any order
async def null_func(x,y,z): #always two parameters and then array. that is  my format
    return 0
    
async def reminder(yak,y,x):
    await send_dm(yak,y,["reminder: "+x[0]]) # 3rd parameter is always an array
    return 0

async def has_role(yak,y,x):
    #print("has role:",yak,x)
    if x[0] in yak['roles']:
        return 1
    return 0

async def kick_out(yak,y,x):
    print("kick out id with message (sent by dm):",yak.discordid,x[0])
    return 0

async def send_dm(yak,y,x):
    print("here i send a DM to the current yak we are looking at, with text:",yak['discordid'],x[0])
    target=client.get_user(yak['discordid']).dm_channel
    if (not target): 
        print("need to create dm channel",flush=True)
        target=await client.get_user(yak['discordid']).create_dm()
    print("target is:",target,flush=True)    
    #await target.send(x[0])# do not want to actually send yet
    return 0

async def posted_introduction(yak,m,x):
    print('check if this message is in introduction channel. if yes, return 1, otherwise 0')
    if m.channel.id==692826420191297556:
        return 1
    return 0


newyak={
'starthere': {
    'id':17, 
    'onenter': null_func, 
    'onenter_params': [],
    'transitions':[
        {"on_tick":{
            "run": has_role,
            'run_params':[1, 'yak'], 
            'goto': ['justjoined','yak'] 
            }},
        ]
    },
'justjoined': {
    'id':0, #is this needed?
    'onenter': send_dm, #NOT run on staying within same state due toa  failed transition
    'onenter_params': ['welcome to the yak collective.\n\nPlease post an introduction within 7 days.\n\nStart here (we use roam for data display): (some link to roam)'],#also send 0 as teh 2nd parameter
    'transitions':[
        {"on_message":{#notclear if we really look for other events...
            "run": posted_introduction,
            'run_params':[], #we always send theyak and teh message, followed by the list
            'goto': ['','yak'] #if 0 stay in state (not the same as going again to justjoin, as we do not zero anything, otherwise go up a level
            }},
        {"on_tick":{ #called every tick. the first param is checked before we actually run the function (special for on_tick function)
        #for on_tick we always send theyak and the tick number before the param
            "run": reminder,
            'run_params':[48,"please post an introduction in the introduction channel"],#every 48 ticks post this message. lets assume ticks are in hours
            'goto':['']
            }},
        {"on_tick":{ #called every tick
            "run": null_func,
            'run_params':[7*24],
            'goto':['out']
            }}
        ]
    },
'yak': {
    'id':1,
    'onenter': send_dm, 
    'onenter_params': ['thank you for posting an introduction. here are some more links to consider\n'],
    'transitions': [
        {"on_tick": { #called every tick
                "run": null_func,
                'run_params':[48],#every 48 ticks post this message. lets assume ticks are in hours
                'goto':['regular']
                }
        }]
    },
# we could have more link suggestion states; 'stage1links':

'regular':{ #not much happening here, but we could track what is going on
    'id':2,
    'onenter': send_dm, 
    'onenter_params': ['if you ever need help, pls send me a dm "$help"'],
    'transitions':[]
    },
'out':{ #not much happening here, but we coudl track what is going on
    'id':3,
    'onenter': kick_out, 
    'onenter_params': ['you did not post an introduction withon the required timelimit. try again later'],
    'transitions':[]
    }
}

machines=[
    {
        'states':newyak,
        'name':"newyak",
        'startat':"starthere", 
        'lut':{ #will add more when new functions are created
            "on_tick":[],
            "on_message":[]
        }
    }
] 
