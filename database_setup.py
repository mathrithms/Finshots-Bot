"""This file will delete existing database if any with the provided name in
env file And create a fresh database with the required structure for the
finshots_bot code to function """

import datetime
import os
import psycopg
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# loading environment variables
load_dotenv()
User = os.getenv('DB_USER')
Host = os.getenv('DB_HOST')
Password = os.getenv('DB_PASSWORD')
DBname = os.getenv('DB_NAME')


print('creating postgreSQL database...')

# connecting to postgreSQL main database
conn = psycopg.connect(
    dbname='postgres',
    user=User,
    host=Host,
    password=Password,
    autocommit=True
)
cur = conn.cursor()

# creating a new database
cur.execute(f"DROP DATABASE IF EXISTS {DBname};")
cur.execute(f"CREATE DATABASE {DBname} WITH ENCODING 'UTF8';")
cur.close()
conn.close()

# connecting to the created database
db = psycopg.connect(
    dbname=DBname,
    user=User,
    host=Host,
    password=Password,
    autocommit=True
)
cur = db.cursor()

# creating table for channel ids and time
cur.execute(
    "CREATE TABLE channels ("
    "channel_id BIGINT PRIMARY KEY, "
    "time TIME);"
)

# creating table for storing the links
cur.execute(
    "CREATE TABLE articles ("
    "links VARCHAR(200) PRIMARY KEY, "
    "title VARCHAR(200), "
    "category VARCHAR(20), "
    "link_date DATE, "
    "update_time TIMESTAMP);"
)

print('success! database created succesfully')
print('feeding in articles into the database...')

# feeding in data to the database
category = {
    "https://finshots.in/archive": "daily",
    "https://finshots.in/brief/": "brief",
    "https://finshots.in/markets/": "markets",
    "https://finshots.in/infographic/": "infographics"
}
for url in category:

    # fetching no. of pages the category has
    r1 = requests.get(url).content
    soup = BeautifulSoup(r1, 'html.parser')
    div = soup.find('div', class_='inner')
    page_string = div.find('nav').find('span').text
    pages = int(page_string.split()[-1])

    # scrapping from each page
    for i in range(1, pages+1):
        r = requests.get(f"{url}/page/{i}").content
        soup = BeautifulSoup(r, 'html.parser')
        div = soup.find('div', class_='post-feed')
        articles = div.find_all('article')

        for item in articles:
            # scrapping the data
            article = {
                'title': item.find('img')['alt'],
                'link_date': item.find('time')['datetime']
            }
            if category[url] == 'infographics':
                article['link'] = item.find('img')['src']
            else:
                article['link'] = (
                    "https://finshots.in" + item.find('a')['href']
                )

            now = datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")

            # updating links into articles table
            sql = ("INSERT INTO articles VALUES(%s,%s,%s,%s,%s);")
            val = (article['link'], article['title'],
                   category[url], article['link_date'], now)
            cur.execute(sql, val)
            db.commit()

# setting older articles update_time to 3 days back to avoid spam
cur.execute(
    "UPDATE articles "
    "SET update_time = CURRENT_DATE - INTERVAL '3 days' "
    "WHERE link_date != CURRENT_DATE;"
)

cur.close()
db.close()

print('success! database updated with all articles!')
