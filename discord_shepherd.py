import discord

intents = discord.Intents.default()
intents.members = True


client = discord.Client(intents=intents)
