import os
import openai
import discord
from discord.ext import commands
import logging
import textwrap
from io import StringIO
from dotenv import load_dotenv, find_dotenv

load_dotenv()
#https://discord.com/oauth2/authorize?client_id=1055708615761199185&permissions=0&scope=bot%20applications.commands

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
description = '''An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.'''

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.Model.list()

def word_count(str):
    counts = dict()
    words = str.split()

    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1

    return counts

def getGPTComplete(input):
    logging.info(f"Sending query for gpt3 with message {input}")
    response = openai.Completion.create(
    engine="text-davinci-003",
    prompt=input,
    temperature=0.7,
    max_tokens=2000,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0
    )
    text = response['choices'][0]['text'] 
    logging.info(f"Got response from gpt3 back with length {len(text.split())}")
    return text

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)
@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})\n--------')

@bot.command()
async def getgpt(ctx, *,query : str):
    resp = getGPTComplete(query)
    messages = textwrap.wrap(resp,1900)
    messageswithdot = []
    if len(messages) > 1:
        for x in messages[:-1]:
            messageswithdot.append(x + "...")
        messageswithdot.append(messages[-1])
        messages = messageswithdot

    for message in messages:
        await ctx.send(message)

bot.run(os.getenv("DISCORD_KEY"))