#anyway, state table is a dict, where each item is a state, with id, function to run when entering  state , with array of parameters - useful, for example, for "add role" function.  most important is a list of state transitions, each one includes a type (like on_message) which is an actual function, a function that returns a number, an array of parameters to give that function (or teh parent "type" function) and an array of states you go to according to these values. 
#we also have ticks every hour, so we can set things to do when tick count is mod that number. tick count is per yak!

#for each type, we have an array for each state table. the array includes the states which care about that type. when running and the event occurs, if it is an on_tick event (not triggered by a user, i can imagine there are others) we see which states care about the event. then, for each state, we extract all the yaks in that state AND which do not say "exclude me". then, we call teh function, FOR THAT USER, with teh parameters and go to where result sends up.
#if it is an event triggered by a user (like a message), we can simply check in db that he is not 'frozen" and run the function in the state table, accorindg to his state (taken form db), if relevant





newyak={
'justjoined': {
    'id':0, #is this needed?
    'onenter': send_dm, #NOT run on staying within same state due toa  failed transition
    'onenter_params': ['welcome to the yak collective.\n\nPlease post an introduction within 7 days.\n\nStart here (we use roam for data display): (some link to roam)'],
    'transitions':[
        {"on_message":{#notclear if we really look for other events...
            "run": posted_introduction,
            'run_params':[],
            'goto': ['','yak'] #if 0 stay in state (not the same as going again to justjoin, as we do not zero anything, otherwise go up a level
            }},
        {"on_tick":{ #called every tick. the first param is checked before we actually run the function (special for on_tick function)
            "run": reminder,
            'run_params':[48,"please post an introduction in the introduction channel"],#every 48 ticks post this message. lets assume ticks are in hours
            'goto':['']
            }},
        {"on_tick":{ #called every tick
            "run": null_func,
            'run_params':[7*24]
            'goto':['out']
            }}
        ]
    },
'yak':{
    'id':1,
    'onenter': send_dm, 
    'onenter_params': ['thank you for posting an introduction. here are some more links to consider\n'],
    'transitions':[
        "on_tick":{ #called every tick
                "run": null_func,
                'run_params':[48],#every 48 ticks post this message. lets assume ticks are in hours
                'goto':['regular']
                }
        ]
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
#here be functions used in teh above state table. note they are called by predefined functions, like "on_message"
def null_func(id):
    return 0
    
def reminder(id,x):
    send_dm("reminder: "+x)

def send_dm(id,x):
    print("here i send a DM to the current yak we are looking at, with text:",x)

def posted_introduction(id):
    print('check if this message is in introduction. if yes, return 1, otherwise 0')
    
machines=[newyak]
