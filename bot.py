# this is the file that will run 24*7 on the server

import discord
from discord.ext import commands, tasks

import mysql.connector as mc
from dotenv import load_dotenv
import os
import datetime

load_dotenv()

# making the connection to database
User = os.getenv('USER')
Host = os.getenv('HOST')
Password = os.getenv('PASSWORD')
Database = os.getenv('DATABASE')

db = mc.connect(user = User, host = Host, password = Password, database = Database)
cur = db.cursor()

# bot code
prefix = os.getenv('PREFIX')
client = commands.Bot(command_prefix = f"{prefix}")


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

        # extracting user ids to send the articles at this time (minute)
        cur = db.cursor()
        cur.execute("select member_id from members where time_to_sec(timediff(curtime(),time)) between 0 and 59")
        userid = cur.fetchall()
        
        # extracting the articles that are updated in the database withing past 24 hours from now
        now = datetime.datetime.now().strftime(r"%Y:%m:%d %H:%M:%S")
        cur.execute(f"select links, title, link_date from articles where timestampdiff(minute,'{now}',update_time) < 1440 ;")
        articles = cur.fetchall()

        # sending the articles in the required channels
        for ch_id in channelid:
            channel = client.get_channel(int(ch_id[0]))
            for article in articles:
                await channel.send(f'New Article on Finshots - {article[1]}')
                await channel.send(f'Posted on - {article[2]}')
                await channel.send(f'Read here - {article[0]}')

        # sending the articles in the required dms
        for ch_id in userid:
            user = client.get_user(int(ch_id[0]))
            for article in articles:
                await user.send(f'New Article - {article[1]}')
                await user.send(f'Posted on - {article[2]}')
                await user.send(f'Link - {article[0]}')
        
    link_poster.start()  #starts this tasks


# BOT COMMANDS

# commands for updates on server channels

@client.command(aliases=['reg'])
async def register(ctx, channel:discord.TextChannel, time=None):

    '''register a channel for Finshots updates on a server
    syntax -> register #channel_mention HH:MM
    alias  -> reg'''

    if time == None:
        await ctx.send("Specify the time in HH:MM format")
        msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        time = msg.content
    channel_id = channel.id   

    try:
        cur.execute(f"insert into channels values('{channel_id}','{time+':00'}');")
        db.commit()
        await ctx.send(f"Registered! Finshots updates will be received in {channel.mention} everyday at {time}")
    except mc.errors.IntegrityError:
        await ctx.send(f'{channel.mention} channel is already registered for updates!')
    except:
        await ctx.send("Some error ocuured! Try checking your command format")


@client.command()
async def set_time(ctx, channel:discord.TextChannel, time=None):
    
    '''update time of a channel for Finshots updates
    syntax -> set_time #channel_mention HH:MM'''

    channel_id = channel.id
    cur.execute(f"select * from channels where channel_id = '{channel_id}';")
    if cur.fetchall() == []:
        await ctx.send(f"{channel.mention} channel is not registered! Use the register command to register the channel")
    else:
        if time == None:
            await ctx.send("Specify the time in HH:MM format")
            msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            time = msg.content
        cur.execute(f"update channels set time='{time}' where channel_id='{channel_id}';")
        db.commit()
        await ctx.send(f"Your time has been updated! {channel.mention} will now receive updates at {time}")

    
@client.command(aliases=['dereg'])
async def deregister(ctx, channel:discord.TextChannel):

    '''deregister a channel for Finshots updates
    syntax -> deregister #channel_mention
    alias  -> dereg'''

    channel_id = channel.id
    cur.execute(f"delete from channels  where channel_id='{channel_id}';")
    db.commit()
    if cur.rowcount==0:
        await ctx.send(f"{channel.mention} was never registered for updates!")
    else:
        await ctx.send(f"Deregistered! {channel.mention} channel wont recieve updates from now !")


# commands for updates on dm

@client.command(aliases=['reg_me'])
async def register_me(ctx, time=None):

    '''register yourself for Finshots updates on DM
    syntax -> register_me HH:MM
    alias  -> reg_me'''

    if time == None:
        await ctx.send("Specify the time in HH:MM format")
        msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        time = msg.content

    user_id = ctx.author.id   
    try:
        cur.execute(f"insert into members values('{user_id}','{time+':00'}');")
        db.commit()
        await ctx.send(f"Registered! You will now receive Finshot Updatws in your DM everyday at {time}")
    except mc.errors.IntegrityError:
        await ctx.author.send('You are already registered for updates in DM!')
    except:
        await ctx.author.send("Some error ocuured! Try checking your command format")


@client.command()
async def set_my_time(ctx, time=None):

    '''update time of yoour Finshots updates on DM
    syntax -> set_my_time HH:MM'''

    user_id = ctx.author.id
    cur.execute(f"select * from members where member_id = '{user_id}';")
    if cur.fetchall() == []:
        await ctx.send(f"You are not registered for Finshots Updates! Use the register_me command to register!")
    else:
        if time == None:
            await ctx.send("Specify the time in HH:MM format")
            msg = await client.wait_for('message', check=lambda message: message.author == message.author)
            time = msg.content
        cur.execute(f"update members set time='{time}' where member_id='{user_id}';")
        db.commit()
        await ctx.send(f"Your time has been updated! You will now receive updates at {time}")


@client.command(aliases=['dereg_me'])
async def deregister_me(ctx):

    '''deregister yourself for Finshots updates on DM
    syntax -> deregister_me
    alias  -> dereg_me'''

    user_id = ctx.author.id
    cur.execute(f"delete from members where member_id='{user_id}';")
    db.commit()
    if cur.rowcount==0:
        await ctx.send("You were never registered for DM updates!")
    else:
        await ctx.send("Deregistered! You wont recieve updates in DM from now !")



@client.command(aliases=['hi'])
async def hello(ctx):
    
    '''bot replies with a hello to hello/hi'''

    await ctx.send(f'Hello {ctx.author.mention}, FINSHOTS_SCOUT here at your service')



#launching the bot
bot_token = os.getenv('DISCORD_TOKEN')
client.run(bot_token)

