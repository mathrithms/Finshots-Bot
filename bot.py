#!/usr/bin/env python3
"""this is the file that will run 24*7 on the server"""

import datetime
import os
import random

import discord
import psycopg
from discord.ext import commands, tasks
from dotenv import load_dotenv

# loading environment variables
load_dotenv()
User = os.getenv('DB_USER')
Host = os.getenv('DB_HOST')
Password = os.getenv('DB_PASSWORD')
DBname = os.getenv('DB_NAME')

# making the connection to database
db = psycopg.connect(
    user=User,
    host=Host,
    password=Password,
    dbname=DBname,
    autocommit=True
)
cur = db.cursor()

# bot code
prefix = 'finshots '
client = commands.Bot(command_prefix=[
    f"{prefix}", "Finshots ", "FINSHOTS ", "finshot ", "Finshot ", "FINSHOT "
    ], case_insensitive=True
)


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
            "SELECT channel_id "
            "FROM channels "
            "WHERE EXTRACT(EPOCH FROM (CURRENT_TIME - time)) "
            "BETWEEN 0 AND 59;"
        )
        channelid = cur.fetchall()

        if len(channelid) == 0:
            return

        # extracting the articles that are updated in the database within
        # past 24 hours from now

        category = ['daily', 'brief', 'markets', 'infographics']
        articles = []
        for value in category:
            cur.execute(
                "SELECT links, title, category, link_date "
                "FROM articles "
                "WHERE category=%s "
                "AND EXTRACT (EPOCH FROM (CURRENT_TIMESTAMP - update_time)) "
                "/ 60 < 1440;",
                (value,)
            )
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
        cur.execute("SELECT channel_id FROM channels;")
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

@client.command()
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
        cur.execute("INSERT INTO channels VALUES(%s,%s);", (channel_id, time1))
        await ctx.send(
            f">>> Done! Finshots updates will be sent here everyday at"
            f"  **{time}**  `[UTC {sign}{timezone}]`")
    except (psycopg.errors.IntegrityError):
        await ctx.send(
            ">>> This channel/DM is already registered for Finshots updates!\n"
            "Use the update_time command to update the time for updates")


@client.command()
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
        "UPDATE channels SET time=%s WHERE channel_id=%s;",
        (time1, channel_id)
    )
    if cur.rowcount == 0:
        await ctx.send(
            ">>> This channel is not registered for finshots updates.\n"
            "Use the start command to start getting finshots updates here."
        )
    else:
        await ctx.send(
            f">>> Done! Finshots updates will now be sent here everyday at"
            f"  **{time}**  `[UTC {sign}{timezone}]`")


@client.command()
async def stop(ctx):
    """stop Finshots updates for the channel/DM
    syntax -> stop"""

    channel_id = ctx.channel.id
    cur.execute("DELETE FROM channels WHERE channel_id=%s;", (channel_id,))
    if cur.rowcount == 0:
        await ctx.send(
            ">>> This channel/DM is not registered for Finshots updates!")
    else:
        await ctx.send(
            ">>> Done! You won't recieve Finshots updates here from now")


@client.command(aliases=['random'])
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
        cur.execute('SELECT * FROM articles;')
    else:
        cur.execute("SELECT * FROM articles WHERE category=%s;", (category,))
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


@client.command()
async def latest(ctx, category=None):
    """sends the latest articles of the specified category stored in
    the bot database syntax -> latest <category name (default daily)>"""

    typos = {
        'briefs': 'brief',
        'market': 'markets',
        'infographic': 'infographics'
        }
    if category in typos.keys():
        category = typos[category]

    if category is None:
        cur.execute(
            "SELECT * FROM articles "
            "WHERE link_date = (SELECT MAX(link_date) FROM articles);"
            )
    else:
        cur.execute(
            "SELECT * FROM articles WHERE category=%s "
            "AND link_date = (SELECT MAX(link_date) FROM articles "
            "WHERE category=%s);",
            (category, category)
        )
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
    fetches latest 20 matching articles
    syntax -> search <search_term>"""

    if text is None:
        await ctx.send(
            "Please run the command again with a term/phrase to search for\n"
            "syntax -> search <search_term>")
        return

    cur.execute(
        "SELECT * FROM articles WHERE title ILIKE %s "
        "ORDER BY link_Date DESC LIMIT 20;", (f"%{text}%",)
    )
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
    fetches matching articles
    syntax -> date_search <date> (in YYYY-MM-DD format)"""

    if text is None:
        await ctx.send(
            "Please use the command again with a date to search for\n"
            "syntax -> date_search <date> (in YYY-MM-DD format)")
        return

    cur.execute(
        "SELECT * FROM articles WHERE link_date = %s "
        "ORDER BY link_date", (text,)
    )
    results = cur.fetchall()

    if len(results) == 0:
        await ctx.send('No articles/infographics found for this date. '
                       '\nMake sure your are using `YYYY-MM-DD` format')

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


@client.command(aliases=['sc'])
async def server_count(ctx):
    servers = len(client.guilds)
    await ctx.send(f"{client.user.mention} is playing on `{servers} servers`")


@client.command()
async def ping(ctx):
    """displays the network latency of the bot"""

    await ctx.send(f"Ping: {round(client.latency * 1000)} ms")


# Help commands

client.remove_command('help')


@client.group(invoke_without_command=True)
async def help(ctx, category='main'):
    """displays the help for the bot in an embed"""

    colours = [discord.Colour.red(), discord.Colour.blue(),
               discord.Colour.green(), discord.Colour.teal(),
               discord.Colour.orange()]
    main = discord.Embed(
        title="**FINSHOTS HELP**\n\n",
        description="```I am a simple bot that can send updates (new "
        "articles) from FINSHOTS website to a specific "
        "channel in a server or to individual users on their "
        "DM everyday at the time specified by user. And I have some more "
        "interesting features revolving the Finshots website.```\n",
        colour=random.choice(colours)
    )
    main.add_field(
        name="BOT COMMANDS:",
        value="```PREFIX : finshots \n"
        "use this prefix before every command!\n"
        "NOTE : commands can be run in a both channels or in DM to the bot```"
        "\nCOMMANDS CATEGORY WISE :",
        inline=False
    )
    main.add_field(
        name="**updates**",
        value="```\nstart\nupdate_time\nstop```",
        inline=True
    )
    main.add_field(
        name="**fetching**",
        value="```\nlatest\nrandom```",
        inline=True
    )
    main.add_field(
        name="**searching**",
        value="```\nsearch\ndate_search```",
        inline=True
    )
    main.add_field(
        name="**Ping**",
        value="```Use 'finshots ping' to check the latency of the bot```",
        inline=False
    )
    main.add_field(
        name="FURTHER HELP",
        value="```use : help <category/command>"
        "\nto see the command details```",
        inline=False
    )

    updates = discord.Embed(
        title="**UPDATES COMMANDS HELP**\n\n",
        colour=random.choice(colours)
    )
    updates.add_field(
        name="start",
        value="```start Finshots updates in the channel/DM at a "
        "specified time\nSYNTAX :  start HH:MM (24 hr. clock) "
        "timezone [+/-HH:MM] (w.r.t UTC)\nNOTE : timezone parameter "
        "is optional, default is IST [+5:30]```",
        inline=False
    )
    updates.add_field(
        name="update_time",
        value="```update time of the channel/DM for the Finshots "
        "updates\nSYNTAX :  update_time HH:MM (24 hr. clock) "
        "timezone [+/-HH:MM] (w.r.t UTC)\nNOTE : timezone parameter "
        "is optional, default is IST [+5:30]```",
        inline=False
    )
    updates.add_field(
        name="stop",
        value="```stop Finshots updates for the channel/DM\nSYNTAX "
        ":  stop```",
        inline=False
    )

    fetching = discord.Embed(
        title="**FETCHING COMMANDS HELP**\n\n",
        colour=random.choice(colours)
    )
    fetching.add_field(
        name="latest",
        value="```sends the latest articles of the specified category stored"
        " in the bot database"
        "\nSYNTAX :  latest <category name>"
        "\nNOTE : <category name> is optional"
        "\nCATEGORY NAMES :  daily, markets, brief, infographics```",
        inline=False
    )
    fetching.add_field(
        name="random / feeling_lucky",
        value="```sends a random article of the specified category stored"
        " in the bot database"
        "\nSYNTAX :  random/feeling_lucky <category name>"
        "\nNOTE : <category name> is optional"
        "\nCATEGORY NAMES :  daily, markets, brief, infographics```",
        inline=False
    )

    searching = discord.Embed(
        title="**SEARCHING COMMANDS HELP**\n\n",
        colour=random.choice(colours)
    )
    searching.add_field(
        name="search",
        value="```Search the finshots database for any article/infographic "
        "based on keyword/phrase in article title, result will have latest"
        " 1o matching results\nSYNTAX :  search <search term/phrase>```",
        inline=False
    )
    searching.add_field(
        name="date_search",
        value="```Search the finshots database for any article/infographic "
        "based on publish date, result will have latest 10 matching "
        "results\nSYNTAX :  date_search <date> (in YYY-MM-DD format)```",
        inline=False
    )

    if category in ['start', 'update_time', 'stop']:
        category = 'updates'
    elif category in ['latest', 'random', 'feeling_lucky']:
        category = 'fetching'
    elif category in ['search', 'date_search']:
        category = 'searching'

    embeds = {
        'main': main,
        'updates': updates,
        'fetching': fetching,
        'searching': searching
    }
    await ctx.send(embed=embeds[category])


@client.event
async def on_guild_join(guild):
    """bot will send a welcome message when it joins a server"""

    system_channel = guild.system_channel
    if system_channel:
        em = discord.Embed(
            title="**GREETINGS**",
            description=f"```Hello {guild.name}! I am a simple bot that can "
            "send updates (new articles) from FINSHOTS website to "
            "a specific channel in a server or to individual "
            "users on their DM eveyday at the time specified by "
            "user. And I have some more interesting features "
            "revolving the Finshots website.``` ",
            colour=discord.Colour.blue()
        )
        em.add_field(
            name="HOW TO USE?",
            value=f"```{prefix}help```", inline=False
        )
        em.add_field(
            name="NOTE:",
            value="```This bot and all its commands work in server "
            "channels for server use as well as in DM for "
            "personal use. Feel free to right click the bot "
            "and click on message to DM the bot```",
            inline=False
        )
        await system_channel.send(embed=em)


# launching the bot
bot_token = os.getenv('DISCORD_TOKEN')
client.run(bot_token)
