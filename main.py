import os
import openai
import discord
from discord.ext import commands
import logging
import logging.handlers
import textwrap
from io import StringIO
from dotenv import load_dotenv, find_dotenv

load_dotenv()


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    logger.info(f"Sending query for gpt3 with message \"{input}\"")
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
    logger.info(f"Got response from gpt3 back with length {len(text.split())} from input \"{input}\"")
    return text

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)
@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})\n--------')

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