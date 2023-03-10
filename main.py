import os
import openai
import discord
from discord.ext import commands
from discord.ext.commands import Greedy, Context  # or a subclass of yours
from typing import Literal, Optional
import logging
import logging.handlers
import textwrap
from io import StringIO
from io import BytesIO
from dotenv import load_dotenv, find_dotenv
import sqlite3
import time
import requests
import uuid
import json
from datetime import datetime

load_dotenv()


logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler(
    filename="discord.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
consolehandler = logging.StreamHandler()
consolehandler.setFormatter(formatter)
consolehandler.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(consolehandler)

description = """Bot for ai things like gpt and dalle"""

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.Model.list()


def add_data(time, query, reply):
    # Connect to the database
    conn = sqlite3.connect("database.db")

    # Create a cursor
    cursor = conn.cursor()
    # Insert a row into the table
    cursor.execute(
        "INSERT INTO queries (time, input, output) VALUES (?, ?, ?)",
        (time, query, reply),
    )

    # Commit the changes
    conn.commit()

    # Close the connection
    conn.close()


async def getGPTComplete(input):
    logger.info(f'Sending query for gpt3 with message "{input}"')
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=input,
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    finish_reason = response["choices"][0]["finish_reason"]
    text = response["choices"][0]["text"]
    logger.info(
        f'Got response from gpt3 back with length {len(text.split())} from input "{input}"'
    )
    return finish_reason, text

async def getCodexComplete(input):
    logger.info(f'Sending query for gpt3 with message "{input}"')
    response = openai.Completion.create(
        engine="code-davinci-002",
        prompt=input,
        temperature=0.7,
        max_tokens=3000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    finish_reason = response["choices"][0]["finish_reason"]
    text = response["choices"][0]["text"]
    logger.info(
        f'Got response from gpt3 back with length {len(text.split())} from input "{input}"'
    )
    return finish_reason, text

async def getDALLE(input):
    logger.info(f'Sending query for dalle with message "{input}"')
    try:
        response = openai.Image.create(prompt=input, n=1, size="512x512")
        image_url = response["data"][0]["url"]
        logger.info(f'Got response from dalle back {image_url} from input "{input}"')
        r = requests.get(image_url)
        buffer = BytesIO(r.content)
    except openai.error.OpenAIError as e:
        logger.error(f"Error creating dalle image {e.http_status} {e.error}")
        image_url = "Error"
        buffer = None
    return image_url, buffer


intents = discord.Intents().all()

bot = commands.Bot(command_prefix="?", description=description, intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})\n--------")

    if os.path.exists('user_status.json'):
        with open('user_status.json', 'r') as log_file:
            user_data = json.load(log_file)
    else:
        log_file = open('user_status.json', 'w')
        user_data = {}
        json.dump(user_data, log_file)
        log_file.flush()

    logging.info(bot.guilds)
    lookedatusers = []
    # checking all online users to make sure they are logged if online
    # and to make sure they are added to the list to avoid keyerrors
    # from missing users
    for guild in bot.guilds:
        logger.info(guild)
        for member in guild.members:
            logger.info(member.name + " is " + str(member.status))
            if member.name not in lookedatusers and (member.status == discord.Status.online):
                # add users who are not currently on the list if they are online
                if member.name not in user_data:
                    # adding new user to log list
                    user_data[member.name] = {'online_times': []}
                    onlinetime = {'start': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'end': None}
                    if onlinetime not in user_data[member.name]['online_times']:
                        user_data[member.name]['online_times'].append(onlinetime)


                if user_data[member.name]["online_times"][-1]["end"] != None:
                    # check if final online time has a end time, if not and they are online
                    # their login was missed and should be logged now
                    logger.info(member.name + " is not logged as currently online")
                    onlinetime = {'start': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'end': None}
                    if onlinetime not in user_data[member.name]['online_times']:
                        user_data[member.name]['online_times'].append(onlinetime)
            if member.status == discord.Status.idle or member.status == discord.Status.dnd:
                if member.name not in user_data:
                    # adding new user to log list but since idle/do not disturb do not add start
                    # or end time
                    user_data[member.name] = {'online_times': []}
                    
            if member.name not in lookedatusers:
                lookedatusers.append(member.name)

    out_file = open("user_status.json", "w")
    json.dump(user_data, out_file)

                
                    
                

@bot.event
async def on_presence_update(before, after):
    if before.status != after.status:         
        logger.info(f'{after} is now {after.status}')  
        if os.path.exists('user_status.json'):
            with open('user_status.json', 'r') as log_file:
                user_data = json.load(log_file)
        else:
            log_file = open('user_status.json', 'w')
            user_data = {}
            json.dump(user_data, log_file)
            log_file.flush()
        if before.status != discord.Status.online and after.status == discord.Status.online:
            logger.info(f'{after.name} is now online at {datetime.now()}')

            if after.name not in user_data:
                user_data[after.name] = {'online_times': []}

            if user_data[after.name]["online_times"][-1]["end"] == None:
                # user was already considered online and nothing should be logged
                logger.info(f'{after.name} changed status to {after.status} but was already logged as online at {datetime.now()}')
                return

            onlinetime = {'start': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'end': None}
            if onlinetime not in user_data[after.name]['online_times']:
                user_data[after.name]['online_times'].append(onlinetime)
        elif before.status == discord.Status.online and after.status != discord.Status.online:
            logger.info(f'{after.name} is now not online at {datetime.now()}')
            for i in range(len(user_data[after.name]['online_times'])):
                if user_data[after.name]['online_times'][i]['end'] is None:
                    user_data[after.name]['online_times'][i]['end'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    break
        out_file = open("user_status.json", "w")
        json.dump(user_data, out_file)
      

@bot.hybrid_command(name="getgpt")
async def getgpt(ctx, *, query: str):
    user = ctx.message.author
    if not ctx.interaction:
        sent = await ctx.message.reply("Processing!")
    await ctx.defer(ephemeral=True)
    start_time = time.time()
    finish_reason, resp = await getGPTComplete(query)
    total_time = time.time() - start_time
    total_time = round(total_time, 2)
    logger.info(f'GPT query for input "{query}" took {total_time}s')
    messages = textwrap.wrap(resp, 1900)
    messageswithdot = []
    if len(messages) > 1:
        for x in messages[:-1]:
            messageswithdot.append(x + "...")
        messageswithdot.append(messages[-1])
        messages = messageswithdot
    if len(messages) > 0:
        messages[0] = f'Prompt: "{query}"\nResponse:' + messages[0]
        add_data(total_time, query, resp)
    else:
        messages = [
            f'Prompt: "{query}"\nResponse: No response\nReason: {finish_reason}'
        ]
        add_data(total_time, query, f"Failed due to reason: {finish_reason}")

    if not ctx.interaction:
        await sent.delete()
    for message in messages:
        await ctx.send(message)

@bot.hybrid_command(name="getcodex")
async def getcodex(ctx, *, query: str):
    user = ctx.message.author
    if not ctx.interaction:
        sent = await ctx.message.reply("Processing!")
    await ctx.defer(ephemeral=True)
    start_time = time.time()
    finish_reason, resp = await getCodexComplete(query)
    total_time = time.time() - start_time
    total_time = round(total_time, 2)
    logger.info(f'GPT query for input "{query}" took {total_time}s')
    messages = textwrap.wrap(resp, 1900)
    messageswithdot = []
    if len(messages) > 1:
        for x in messages[:-1]:
            messageswithdot.append(x + "...")
        messageswithdot.append(messages[-1])
        messages = messageswithdot
    if len(messages) > 0:
        messages[0] = f'Prompt: "{query}"\nResponse:' + messages[0]
        add_data(total_time, query, resp)
    else:
        messages = [
            f'Prompt: "{query}"\nResponse: No response\nReason: {finish_reason}'
        ]
        add_data(total_time, query, f"Failed due to reason: {finish_reason}")

    if not ctx.interaction:
        await sent.delete()
    for message in messages:
        await ctx.send(message)


@bot.hybrid_command(name="getdalle")
async def getdalle(ctx, *, query: str):
    if not ctx.interaction:
        sent = await ctx.message.reply("Processing!")
    await ctx.defer(ephemeral=True)
    start_time = time.time()
    image, buffer = await getDALLE(query)
    total_time = time.time() - start_time
    total_time = round(total_time, 2)
    logger.info(f'DALLE query for input "{query}" took {total_time}s')

    if not ctx.interaction:
        await sent.delete()
    if image != "Error" and not ctx.interaction:
        add_data(total_time, query, image)
        uuidyeah = uuid.uuid1()
        image_file = discord.File(buffer, filename=f"images/{uuidyeah}.png")
        await ctx.message.reply(file=image_file)

        # await ctx.message.reply(file=discord.File("image.png"))
    elif image != "Error" and ctx.interaction:
        uuidyeah = uuid.uuid1()
        image_file = discord.File(buffer, filename=f"images/{uuidyeah}.png")
        await ctx.send(file=image_file)
    elif not ctx.interaction:
        await ctx.message.reply(
            "Error, try a different prompt, might not have liked wording"
        )
    else:
        await ctx.send("Error, try a different prompt, might not have liked wording")


@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
    ctx: Context,
    guilds: Greedy[discord.Object],
    spec: Optional[Literal["~", "*", "^"]] = None,
) -> None:
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


def create_db():
    # Connect to the database
    conn = sqlite3.connect("database.db")

    # Create a cursor
    cursor = conn.cursor()

    # Check if the table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='queries'"
    )

    # If the table does not exist, create it
    if not cursor.fetchone():
        cursor.execute("CREATE TABLE queries (time REAL, input TEXT, output TEXT)")

    # Commit the changes
    conn.commit()

    # Close the connection
    conn.close()


create_db()


bot.run(os.getenv("DISCORD_KEY"), log_handler=None)
