import os
import openai
import discord
from discord.ext import commands
from discord.ext.commands import Greedy, Context # or a subclass of yours
from typing import Literal, Optional
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

@bot.hybrid_command(name="getgpt")
async def getgpt(ctx, *,query : str):
    await ctx.defer(ephemeral=True)
    resp = getGPTComplete(query)
    messages = textwrap.wrap(resp,1900)
    messageswithdot = []
    if len(messages) > 1:
        for x in messages[:-1]:
            messageswithdot.append(x + "...")
        messageswithdot.append(messages[-1])
        messages = messageswithdot
    messages[0] = f"Prompt: {query}\nResponse:" + messages[0]
    for message in messages:
        await ctx.send(message)
    
@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
  ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}{synced}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")
   
    

bot.run(os.getenv("DISCORD_KEY"))