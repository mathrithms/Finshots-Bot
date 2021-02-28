# this is the file that will run 24*7 on the server

import discord
from discord.ext import commands, tasks
from discord.utils import find

import mysql.connector as mc
from dotenv import load_dotenv
import os
import datetime
import random
import asyncio

load_dotenv()

# making the connection to database
User = os.getenv('USER')
Host = os.getenv('HOST')
Password = os.getenv('PASSWORD')
Database = os.getenv('DATABASE')

db = mc.connect(user = User, host = Host, password = Password, database = Database)
cur = db.cursor()

# bot code
prefix = 'finshots '
client = commands.Bot(command_prefix = [f"{prefix}", "Finshots ", "FINSHOTS ", "finshot ", "Finshot ","FINSHOT "], case_insensitive = True)


@client.event
async def on_ready():
    '''this code runs when the bot comes online'''
    print('Bot is online!')

    # this task (piece of code) keep running in loop every 1 minute
    # this will check every minute if the bot needs to send new articles to a channel or user, and if so send it
    @tasks.loop(minutes=1)
    async def link_poster():

        # extracting channel ids to send the articles at this time (minute)
        cur = db.cursor()
        cur.execute("select channel_id from channels where time_to_sec(timediff(curtime(),time)) between 0 and 59")
        channelid = cur.fetchall()
        
        # extracting the articles that are updated in the database withing past 24 hours from now
        now = datetime.datetime.now().strftime(r"%Y:%m:%d %H:%M:%S")
        cur.execute(f"select links, title, link_date from articles where timestampdiff(minute,'{now}',update_time) < 1440 ;")
        articles = cur.fetchall()

        # sending the articles in the required channels
        for ch_id in channelid:
            channel = client.get_channel(int(ch_id[0]))
            for article in articles:
                await channel.send(f'>>> **{article[1]}   |   {article[2]}**\n{article[0]}')
    
    link_poster.start()  #starts the above task

    # changes the activity/status of the bot on discord    
    names = {'playing' : f"on {len(client.guilds)} servers", 'listening' : f"{prefix}help"}
    types = {'playing' : discord.ActivityType.playing, 'listening' : discord.ActivityType.listening}
    while not client.is_closed():
        activity = random.choice(['playing', 'listening']) 
        await client.change_presence(activity=discord.Activity(type = types[activity], name = names[activity]))
        await asyncio.sleep(10)


# BOT COMMANDS

@client.command()
async def start(ctx, time=None):

    '''start  Finshots updates in the channel/DM at a specified time
    syntax -> start HH:MM'''

    channel_id = ctx.channel.id 
    cur.execute(f"select * from channels where channel_id = '{channel_id}';")
    if cur.fetchall() != []:
        await ctx.send("This channel/DM is already registered for Finshots updates! Use the update_time command to update the time for updates")
    else:
        if time == None:
            await ctx.send("Specify the time in HH:MM format")
            msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            time = msg.content
        cur.execute(f"insert into channels values('{channel_id}','{time+':00'}');")
        db.commit()
        await ctx.send(f"Done! Finshots updates will be received @here everyday at {time}")



@client.command()
async def update_time(ctx, time=None):
    
    '''update time of the channel/DM for the Finshots updates
    syntax -> update_time HH:MM'''

    channel_id = ctx.channel.id
    cur.execute(f"select * from channels where channel_id = '{channel_id}';")
    if cur.fetchall() == []:
        await ctx.send("This channel/DM is not registered for Finshots updates! Use the start command to register the channel")
    else:
        if time == None:
            await ctx.send("Specify the time in HH:MM format")
            msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            time = msg.content
        cur.execute(f"update channels set time='{time}' where channel_id='{channel_id}';")
        db.commit()
        await ctx.send(f"Done! Finshots updates will now be received @here everyday at {time}")

    

@client.command()
async def stop(ctx):

    '''stop Finshots updates for the channel/DM 
    syntax -> stop'''

    channel_id = ctx.channel.id
    cur.execute(f"delete from channels  where channel_id='{channel_id}';")
    db.commit()
    if cur.rowcount==0:
        await ctx.send("This channel/DM was never registered for Finshots updates!")
    else:
        await ctx.send(f"Done! You won't recieve Finshots updates @here from now")


@client.command()
async def latest(ctx):

    '''sends the latest articles stored in the bot database
    syntax -> latest'''

    cur.execute('select * from articles where link_date = (select max(link_date) from articles);')
    articles = cur.fetchall()

    for article in articles:
        await ctx.send(f'>>> **{article[1]}   |   {article[2]}**\n{article[0]}')
    

# Help commands

client.remove_command('help')

@client.group(invoke_without_command = True)
async def help(ctx):

    colours = [discord.Colour.red(),discord.Colour.blue(),discord.Colour.green(),discord.Colour.teal(),discord.Colour.orange()]   
    em = discord.Embed(description = "**FINSHOSTS HELP**\n\n", colour = random.choice(colours))
    em.add_field(name="**Who am I ???**", value="```I am a simple bot that can send updates (new articles) from FINSHOTS website to a specific channel in a server or to individual users on their DM eveyday at the time specified by user.```\n" , inline=False)
    em.add_field(name="**BOT COMMANDS:**  _(can be run in a channel or in DM to the bot)_", value="```prefix : finshots```", inline=False)
    em.add_field(name = "start", value = "```start  Finshots updates in the channel/DM at a specified time\nsyntax :  start HH:MM```", inline=False)
    em.add_field(name = "update_time", value = "```update time of the channel/DM for the Finshots updates\nsyntax :  update_time HH:MM```",  inline=False)
    em.add_field(name = "stop", value = "```stop Finshots updates for the channel/DM\nsyntax :  stop```",  inline=False)
    em.add_field(name = "latest", value = "```sends the articles of the latest date\nsyntax :  latest```",  inline=False)
    await ctx.send(embed = em)


@client.command(aliases=['hi'])
async def hello(ctx):
    
    '''bot replies with a hello to hello/hi'''

    await ctx.send(f'Hello {ctx.author.mention}, FINSHOTS_SCOUT here at your service')


@client.event
async def on_guild_join(guild):

    '''bot will send a welcome message when it joins a server'''

    general = find(lambda x: x.name == 'general',  guild.text_channels)
    if general:
        title = "Greetings"
        description = f"```Hello {guild.name}! I am a simple bot that can send updates (new articles) from FINSHOTS website to a specified channel in a server or to individual users on their DM at a specified time everyday.```"
        
        em = discord.Embed(title = title, description = description, colour = discord.Colour.blue())
        em.add_field(name = "Help Command", value = f"```{prefix} help```", inline = False)
    
        await general.send(embed=em)

#launching the bot
bot_token = os.getenv('DISCORD_TOKEN')
client.run(bot_token)

