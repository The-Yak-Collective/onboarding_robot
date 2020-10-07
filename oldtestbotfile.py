#this file has several places where we use the raw filed number of knack. shoudl be fixed to none raw, probbaly, using a translation table  

try:
    print("this is a python file", flush=True)

    import discord
    import traceback
    import knackpy
    import json
    import ast
    import sys
    import os

    client = discord.Client()
    dl=[]
    tupd=[]

    def make_and_write_members_file():
        print("started make", flush=True)
        with open('members.json', 'w') as fp: #need to make sure this happens after discord bot...
            json.dump(l, fp)

        #now upload the list so we use knack as a file server
        herebefiles=knack_app.get('object_28')
        print("for the record:",dict(herebefiles[0])) #indeed. application is listed as *** rather than "5f286f84d61121001594a056"
        file_id=dict(herebefiles[0])['id']

        res = knack_app.upload(
             container="object_28",  # must be an object key or name
             field="field_595",
             path="members.json",
             asset_type="file",  # must be 'file' or 'image', depending on field type
             record_id=file_id
        )
        print("res is:",res)
        loc=res['field_595_raw']['url']
        if res['field_595_raw']['application_id']=='***':
            loc=loc.replace("***",app_id)
        with open('linktomembers', 'w') as fp:#this will be pushed to github. we hope, due to .git setup in bash file. mayeb it needs some finetuning. shoudl eb excluding members.json
            fp.write(loc)

    @client.event
    async def on_ready():
        global dl,l
        print('We have logged in as {0.user}'.format(client),  client.guilds, flush=True) #, client.guilds[0].text_channels, flush=True)
        dl=[]
        tupd=[]
        toadd=[]
        todelete=[]
        print("now show member count",len(client.guilds[0].members),client.guilds[0].members[1],flush=True)
        uu=[u for u in client.guilds[0].members] #maybe will be faster?
        for u in uu:
          if('madeyak' in [x.name for x in u.roles]): # for now, read only made yaks
            r=[x.name for x in u.roles if x.name not in ['@everyone','yak']]
            dl.append((str(u),r,str(u.id),u))
            print(u.name, u.id, u, r, flush=True)
        print("l,dl is:", len(l),len(dl),flush=True)
        def nn(x):
            if x:
                return x
            return []
 
        for i in l:
            found=False
            for j in dl:
                #if i["discordID"]==j[0]: #then change to discord_user_id and add code to check if user name changed and if yes, update field 586. intersting - when copying to knack there was a rounding of teh last 3 digits!?
                if i['discord_user_id']==j[2]:
                    found=True
                    if [l for l in nn(i["discord roles"])+nn(j[1]) if (l in nn(i["discord roles"])) ^ (l in nn(j[1]))]:
                        tupd.append({"id":i["id"],"field_591":j[1]}) #we assume that discord rules over knack and we simply overwrite
                        i['discord roles']=j[1] #also update l, as it is what we will be using
                    if i['discordID']!=j[0]: #means name was updated, as user_id wins
                        print ("seems like we have a name update here:",i,j)
                        tupd.append({"id":i["id"],"field_586":j[0]}) #we assume that discord rules over knack and we simply overwrite
                        i['discordID']=j[0]
                    break
            if found==False:
                print("consider deleting member not on discord (but remember anne) :",i["id"],i["title"])
                todelete.append(i)
        #just once, copy over the discord_user_id and then comment away. and then again due to a rounding error of some sort
        #for i in l:
        #    nm=i["discordID"]
        #    for j in dl:
        #        if j[0]==nm:
        #            print("am updating",i['discord_user_id'],'to',j[2],str(j[2]),j[3].id)
        #            tupd.append({"id":i["id"],"field_596":str(j[2])})
        #            i['discord_user_id']=j[2]
        #            break
        print("list of roles that need to be updated in knack:",tupd,flush=True)
        for x in tupd:
            res = knack_app.record(method="update", data=x, obj="object_27")
            print(res,flush=True)
        print("updated",flush=True)
        existing=[i["discord_user_id"] for i in l] #by now we HAVE discord_user_id
        got=[i[2] for i in dl] #user_id more reliable than username
        toadd=[x for x in got if x not in existing]
        print("consider adding these new madeyaks to members",toadd, flush=True) #IRL there should probbaly be a form to fill sent to knack via some other way. maybe manual entry

        make_and_write_members_file()
        exit(0) #do not want program actually running 

    @client.event 
    async def on_message(message): #should never run
        if message.author == client.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')
        if message.content.startswith('$die'):
            exit(0)

    app_id=sys.argv[2]        
    knack_app = knackpy.App(app_id=app_id,  api_key=sys.argv[3])
    github_token=sys.argv[4]
    github_repository_base=sys.argv[5]
    print(knack_app.info(), flush=True)
    records=knack_app.get('object_27')
    print("the records from knack are many. now show just one")
    #print([(x,vars(x)) for x in records])
    #print(json.dumps(records,indent=2))#record is not serializable
    record=records[4]
    print("now single record - 1nd one for a change")
    data=dict(record)
    #od=dict(record)
    print([x for x in data])
    print("direct")
    print(data)
    #links_number="field_594" #will change if/when we upload again arguably we should FIRST format, so we get field name and not number
    #j=ast.literal_eval(data[links_number])
    #print("links field:", data[links_number], j)
    #data[links_number]=j
    #print("now unfolded the links:",data)
    #to update a record, send only the id and the data to be changed in payload:     record4 = knack_app.record(method="update", data={'id':data['id'],'field_10':{'first':data["field_10"]["first"]+'x','last':'y'}}, obj="object_2")
    #when updating a record, maybe we should do it BEFORE we modify the links? wonder how it will work otherwise
    l=[]
    for r in records: #this should create a propert dict and also save it to file for use as an artifact
        rr=r.format()
        data=dict(rr)
        #print(data)
        #print("links=", data["links"])
        if data["links"]:
           data["links"]=ast.literal_eval(data["links"])
        if data["password"]:
           data["password"]="itisasecret"
        l.append(data)

    print("hum", flush=True)
    #print(os.listdir(github_repository_base))
    client.run(sys.argv[1])
except Exception as e:
    print(e)
    traceback.print_exc()
