import os
import sys
import random
import discord
import aiocron
import asyncio
from dotenv import load_dotenv
from discord.utils import find
from discord.ext import commands

import channel_and_time_maintainer as cnt

load_dotenv()

prefix =os.getenv('PREFIX')
client =commands.Bot(command_prefix=prefix)

@client.event
async def on_ready():
    
    if(len(client.guilds)==1):
        await client.change_presence(status=discord.Status.online, activity=discord.Game(f"on {len(client.guilds)} server | {prefix}help"))
    else:
        await client.change_presence(status=discord.Status.online, activity=discord.Game(f"on {len(client.guilds)} servers | {prefix}help"))

    print("Bot is ready")
    
@client.event
async def on_guild_join(guild):
    general = find(lambda x: x.name == 'general',  guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        await general.send('Hello {}!'.format(guild.name))
        
@client.command()
async def hello(ctx):
    await ctx.send('henlo ^_^')

@client.command()
async def FinshotUpdate(ctx,*, given_name):
    if len(given_name.split())==2:
        Name,Time=given_name.split()
        channel = discord.utils.get(ctx.guild.channels, name=Name)
        channel_id = channel.id    
    else:
        channel = discord.utils.get(ctx.guild.channels, name=given_name)
        channel_id = channel.id
        await ctx.send("what time do you want the daily reminders?")

        msg=await client.wait_for("message")
        Time=msg.content
   
    try:
        cnt.add_member(channel_id, Time)
        await ctx.send('command set. You will not recieve daily updates of finshot site of channel %s at %s'%(channel.name,Time))
    except:
        await ctx.send('could not set updater! please look for error.')

@client.command()
async def ChangeTime(ctx,time):
    try:
        cnt.set_time(ctx.channel.id,time)
        await ctx.send('updates time changed')
    except:
        await ctx.send('some error occured :( ')
        
@client.command()
async def clear(ctx, amount =2):
    await ctx.channel.purge(limit=amount)
    
@client.command()
async def bye(ctx,*,text=''):
    r= ["Ok, byee byee time to go offline",
        "good bye, i am also going offline",
        "See you later, i'mm also gonna go offline now :) ",
        "Going offline, bye >_< ",
        "ta-ta, gona go offline ",
        "ME go'in offline, Sayonara" 
        ]
    
    await ctx.send(r[random.randint(0,5)])
    sys.exit()

@aiocron.crontab('* 6 * * *')
async def cornjob1():
    os.system('database_colector.py')

@aiocron.crontab('* * * * *')
async def cornjob1()
    pass

asyncio.get_event_loop().run_forever()
TOKEN =os.getenv('DISCORD_TOKEN')
client.run(TOKEN)
