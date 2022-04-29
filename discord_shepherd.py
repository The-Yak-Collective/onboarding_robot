import discord

intents = discord.Intents.default()
intents.members = True
intents.messages=True
intents.message_content=True
INTRODUCTIONCHANNELID=692826420191297556

client = discord.Client(intents=intents)
