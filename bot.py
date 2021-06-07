#!/usr/bin/env python3
"""this is the file that will run 24*7 on the server"""

import datetime
import os
import random

import discord
import mysql.connector as mc
from discord.ext import commands, tasks
from discord.utils import find
from dotenv import load_dotenv

load_dotenv()

# making the connection to database
User = os.getenv('DB_USER')
Host = os.getenv('DB_HOST')
Password = os.getenv('DB_PASSWORD')
Database = os.getenv('DB_DATABASE')

db = mc.connect(
    user=User,
    host=Host,
    password=Password,
    database=Database,
    autocommit=True
)
cur = db.cursor()

# bot code
prefix = 'test '
client = commands.Bot(
    command_prefix=[f"{prefix}", "Finshots ", "FINSHOTS ", "finshot ",
                    "Finshot ", "FINSHOT "], case_insensitive=True)


@client.event
async def on_ready():
    """this code runs when the bot comes online"""
    print('Bot is online!')

    # this task (piece of code) keep running in loop every 1 minute this
    # will check every minute if the bot needs to send new articles to a
    # channel or user, and if so send it
    @tasks.loop(minutes=1)
    async def link_poster():
        """checks every minute where to send links and sends it"""

        # extracting channel ids to send the articles at this time (minute)
        cur.execute(
            "select channel_id from channels where time_to_sec(timediff("
            "curtime(),time)) between 0 and 59")
        channelid = cur.fetchall()

        if len(channelid) == 0:
            return

        # extracting the articles that are updated in the database withing
        # past 24 hours from now
        now = datetime.datetime.now().strftime(r"%Y:%m:%d %H:%M:%S")

        category = ['daily', 'brief', 'markets', 'infographics']
        articles = []
        for value in category:
            cur.execute(
                "select links, title, category, link_date from articles "
                f"where category='{value}' and "
                f"timestampdiff(minute, update_time, '{now}') < 1440;")
            articles += cur.fetchall()

        # sending the articles in the required channels
        for ch_id in channelid:
            channel = client.get_channel(int(ch_id[0]))

            for article in articles:
                if article[2] == 'infographics':
                    await channel.send(
                        f'> **FINSHOTS {(article[2]).upper()}**\n'
                        f'> {article[1]}   **|**   '
                        f'`{article[3]}`')
                    await channel.send(article[0])
                else:
                    await channel.send(
                        f'>>> **FINSHOTS {(article[2]).upper()}**\n'
                        f'{article[1]}   **|**   '
                        f'`{article[3]}`\n{article[0]}')

    link_poster.start()  # starts the above task

    @tasks.loop(hours=240)
    async def repo():
        """Sends the repository link with a probability of 1/200 each day"""

        # extracting all channel ids
        cur.execute("select channel_id from channels")
        channelid = cur.fetchall()

        # sending the repo link randomly with low probability
        for ch_id in channelid:
            channel = client.get_channel(int(ch_id[0]))
            p = random.randint(1, 20)
            if p == 3:
                await channel.send(
                    ">>> Check out our Github Repository :"
                    "\nhttps://github.com/mathrithms/Finshots-Bot")

    repo.start()  # starts the above task

    # set the activity/status of the bot on discord
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{prefix}help"
        )
    )


# BOT COMMANDS

@ client.command()
async def start(ctx, time=None, *, timezone='[+5:30]'):
    """start  Finshots updates in the channel/DM at a specified time
    syntax -> start HH:MM (24 hr. clock) timezone [+/-HH:MM] (w.r.t UTC)
    note -> timezone parameter is optional, default is IST [+5:30]"""

    channel_id = ctx.channel.id

    if time is None:
        await ctx.send(
            ">>> Please use the command again with a time mentioned\nsyntax ->"
            " start HH:MM (24 hr. clock) timezone [+/-HH:MM] (w.r.t UTC)\n"
            "note -> timezone parameter is optional, default is IST [+5:30]")
        return

    timezone = timezone[timezone.index('[')+1:timezone.index(']')]
    sign = '-' if '-' in timezone else '+'
    if '+' in timezone or '-' in timezone:
        timezone = timezone[1:]

    ti = datetime.datetime.strptime(time, "%H:%M")
    timez = list(map(int, timezone.split(":")))
    tz = datetime.timedelta(hours=timez[0], minutes=timez[1])

    if sign == '-':
        ti += tz
    else:
        ti -= tz

    time1 = f"{str(ti.hour)}:{str(ti.minute)}:{ti.second}"

    try:
        cur.execute(f"insert into channels values('{channel_id}','{time1}');")
        db.commit()
        await ctx.send(
            f">>> Done! Finshots updates will be sent here everyday at"
            f"  **{time}**  `[UTC {sign}{timezone}]`")
    except (mc.errors.IntegrityError):
        await ctx.send(
            ">>> This channel/DM is already registered for Finshots updates!\n"
            "Use the update_time command to update the time for updates")


@ client.command()
async def update_time(ctx, time=None, *, timezone='[+5:30]'):
    """update time and timezone of the channel/DM for the Finshots updates
    syntax -> update_time HH:MM (24 hr. clock) timezone [+/-HH:MM] (w.r.t UTC)
    note -> timezone parameter is optional, default is IST [UTC +5:30]"""

    channel_id = ctx.channel.id

    if time is None:
        await ctx.send(
            ">>> Please use the command again with a time mentioned\nsyntax ->"
            " start HH:MM (24 hr. clock) timezone [+/-HH:MM] (w.r.t UTC)\nnote"
            " -> timezone parameter is optional, default is IST [UTC +5:30]")
        return

    timezone = timezone[timezone.index('[')+1:timezone.index(']')]
    sign = '-' if '-' in timezone else '+'
    if '+' in timezone or '-' in timezone:
        timezone = timezone[1:]

    ti = datetime.datetime.strptime(time, "%H:%M")
    timez = list(map(int, timezone.split(":")))
    tz = datetime.timedelta(hours=timez[0], minutes=timez[1])

    if sign == '-':
        ti += tz
    else:
        ti -= tz

    time1 = f"{str(ti.hour)}:{str(ti.minute)}:{ti.second}"

    cur.execute(
        f"update channels set time='{time1}' where"
        f" channel_id='{channel_id}';")
    db.commit()
    if cur.rowcount == 0:
        await ctx.send(
            ">>> This channel is not registered for finshots updates.\n"
            "Use the start command to start getting finshots updates here."
        )
    else:
        await ctx.send(
            f">>> Done! Finshots updates will now be sent here everyday at"
            f"  **{time}**  `[UTC {sign}{timezone}]`")


@ client.command()
async def stop(ctx):
    """stop Finshots updates for the channel/DM
    syntax -> stop"""

    channel_id = ctx.channel.id
    cur.execute(f"delete from channels  where channel_id='{channel_id}';")
    db.commit()
    if cur.rowcount == 0:
        await ctx.send(
            ">>> This channel/DM is not registered for Finshots updates!")
    else:
        await ctx.send(
            ">>> Done! You won't recieve Finshots updates here from now")


@ client.command(aliases=['random'])
async def feeling_lucky(ctx, category=None):
    """send a random article from the bot database
    optional argument for random article from specific category
    syntax -> feeling_lucky <category>"""

    typos = {
        'briefs': 'brief',
        'market': 'markets',
        'infographic': 'infographics'
        }
    if category in typos.keys():
        category = typos[category]

    # extracting all articles
    if category is None:
        cur.execute('select * from articles;')
    else:
        cur.execute(f"select * from articles where category='{category}'")
    articles = cur.fetchall()

    # posting a random one
    article = random.choice(articles)

    if article[2] == 'infographics':
        await ctx.send(
            f'> **FINSHOTS {(article[2]).upper()}**\n'
            f'> {article[1]}   **|**   '
            f'`{article[3]}`')
        await ctx.send(article[0])
    else:
        await ctx.send(
            f'>>> **FINSHOTS {(article[2]).upper()}**\n'
            f'{article[1]}   **|**   '
            f'`{article[3]}`\n{article[0]}')


@ client.command()
async def latest(ctx, category='daily'):
    """sends the latest articles of the specified category stored in
    the bot database syntax -> latest <category name (default daily)>"""

    typos = {
        'briefs': 'brief',
        'market': 'markets',
        'infographic': 'infographics'
        }
    if category in typos.keys():
        category = typos[category]

    cur.execute(
        f"select * from articles where category='{category}' and link_date = "
        f"(select max(link_date) from articles where category='{category}');")
    articles = cur.fetchall()

    for article in articles:
        if article[2] == 'infographics':
            await ctx.send(
                f'> **FINSHOTS {(article[2]).upper()}**\n'
                f'> {article[1]}   **|**   '
                f'`{article[3]}`')
            await ctx.send(article[0])
        else:
            await ctx.send(
                f'>>> **FINSHOTS {(article[2]).upper()}**\n'
                f'{article[1]}   **|**   '
                f'`{article[3]}`\n{article[0]}')


@client.command()
async def search(ctx, *, text=None):
    """searches for an article/infographics with title in the bot database
    fetches latest 10 matching articles
    syntax -> search <search_term>"""

    if text is None:
        await ctx.send(
            "Please run the command again with a term/phrase to search for\n"
            "syntax -> search <search_term>")
        return

    cur.execute(
        f"select * from articles where title like '%{text}%'"
        " order by link_Date desc limit 10;")
    results = cur.fetchall()

    if len(results) == 0:
        await ctx.send('No such articles/infographics found')

    elif len(results) == 1:
        article = results[0]

        if article[2] == 'infographics':
            await ctx.send(
                f'> **FINSHOTS {(article[2]).upper()}**\n'
                f'> {article[1]}   **|**   '
                f'`{article[3]}`')
            await ctx.send(article[0])
        else:
            await ctx.send(
                f'>>> **FINSHOTS {(article[2]).upper()}**\n'
                f'{article[1]}   **|**   '
                f'`{article[3]}`\n{article[0]}')

    else:
        options = ''
        for y in range(1, len(results) + 1):
            option = (
                f"{y}) [{results[y-1][1]}]({results[y-1][0]})  **|**  "
                f"`{results[y-1][2]}`  **|**  "
                f"`{results[y-1][3]}`\n")
            if len(options) + len(option) >= 2047:
                em = discord.Embed(description=options)
                await ctx.send(embed=em)
                options = ''
            options += option
        else:
            em = discord.Embed(description=options)
            await ctx.send(embed=em)


@client.command()
async def date_search(ctx, text=None):
    """searches for an article/infographics with date in the bot database
    fetches latest 10 matching articles
    syntax -> date_search <date> (in YYY-MM-DD format)"""

    if text is None:
        await ctx.send(
            "Please use the command again with a date to search for\n"
            "syntax -> date_search <date> (in YYY-MM-DD format)")
        return

    cur.execute(
        f"select * from articles where link_date = '{text}'"
        " order by link_date limit 10;")
    results = cur.fetchall()

    if len(results) == 0:
        await ctx.send('No articles/infographics found for this date')

    elif len(results) == 1:
        article = results[0]

        if article[2] == 'infographics':
            await ctx.send(
                f'> **FINSHOTS {(article[2]).upper()}**\n'
                f'> {article[1]}   **|**   '
                f'`{article[3]}`')
            await ctx.send(article[0])
        else:
            await ctx.send(
                f'>>> **FINSHOTS {(article[2]).upper()}**\n'
                f'{article[1]}   **|**   '
                f'`{article[3]}`\n{article[0]}')

    else:
        options = ''
        for y in range(1, len(results) + 1):
            option = (
                f"{y}) [{results[y-1][1]}]({results[y-1][0]})  **|**  "
                f"`{results[y-1][2]}`  **|**  "
                f"`{results[y-1][3]}`\n")
            if len(options) + len(option) >= 2047:
                em = discord.Embed(description=options)
                await ctx.send(embed=em)
                options = ''
            options += option
        else:
            em = discord.Embed(description=options)
            await ctx.send(embed=em)


# Help commands

client.remove_command('help')


@ client.group(invoke_without_command=True)
async def help(ctx):
    """displays the help for the bot in an embed"""

    colours = [discord.Colour.red(), discord.Colour.blue(),
               discord.Colour.green(), discord.Colour.teal(),
               discord.Colour.orange()]
    em = discord.Embed(
        title="**FINSHOTS HELP**\n\n",
        description="```This is a simple bot that can send updates (new "
        "articles) from FINSHOTS website to a specific "
        "channel in a server or to individual users on their "
        "DM everyday at the time specified by user.```\n",
        colour=random.choice(colours)
    )
    em.add_field(
        name="**BOT COMMANDS:**  _(can be run in a both channels or "
        "in DM to the bot)_",
        value="```prefix : finshots```", inline=False)
    em.add_field(
        name="start",
        value="```start  Finshots updates in the channel/DM at a "
        "specified time\nsyntax :  start HH:MM (24 hr. clock "
        "format) (-)HH:MM (timezone relative to UTC)```",
        inline=False
    )
    em.add_field(
        name="update_time",
        value="```update time of the channel/DM for the Finshots "
        "updates\nsyntax :  update_time HH:MM (24 hr. clock "
        "format) (-)HH:MM (timezone relative to UTC)```",
        inline=False
    )
    em.add_field(
        name="stop",
        value="```stop Finshots updates for the channel/DM\nsyntax "
        ":  stop```",
        inline=False
    )
    em.add_field(
        name="latest",
        value="```sends the latest articles of the specified category stored"
        " in the bot database"
        "\nsyntax :  latest <category name> (optional argument)"
        "\ncategory names :  daily, markets, brief, infographics```",
        inline=False
    )
    em.add_field(
        name="feeling lucky",
        value="```sends a random article"
        "\nsyntax :  feeling lucky```",
        inline=False
    )
    await ctx.send(embed=em)


@ client.event
async def on_guild_join(guild):
    """bot will send a welcome message when it joins a server"""

    general = find(lambda x: x.name == 'general', guild.text_channels)
    if general:
        title = "Greetings"
        description = (
            f"```Hello {guild.name}! I am a simple bot that can "
            "send updates (new articles) from FINSHOTS website to "
            "a specific channel in a server or to individual "
            "users on their DM eveyday at the time specified by "
            "user.``` "
        )
        em = discord.Embed(title=title, description=description,
                           colour=discord.Colour.blue())
        em.add_field(name="Use Help Command to learn how to use",
                     value=f"```{prefix} help```", inline=False)
        em.add_field(
            name="NOTE:",
            value="```This bot and all its commands work in server "
            "channels for server use as well as in DM for "
            "personal use. Feel free to right click the bot "
            "and click on message to DM the bot```",
            inline=False)
        await general.send(embed=em)


# launching the bot
bot_token = os.getenv('DISCORD_TOKEN')
client.run(bot_token)
