import discord

intents = discord.Intents.default()
intents.members = True
INTRODUCTIONCHANNELID=692826420191297556

client = discord.Client(intents=intents)
