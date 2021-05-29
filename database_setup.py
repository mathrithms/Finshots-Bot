"""This file will delete existing database if any with the provided name in
env file And create a fresh database with the required structure for the
finshots_scout code to function """

import datetime
import os

import mysql.connector as mc
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

print('creating mysql database...')

# making the connection to database

load_dotenv()
User = os.getenv('DB_USER')
Host = os.getenv('DB_HOST')
Password = os.getenv('DB_PASSWORD')
Database = os.getenv('DB_DATABASE')

db = mc.connect(
    user=User,
    host=Host,
    password=Password,
    autocommit=True
)
cur = db.cursor()

# creating database
cur.execute(f'drop database if exists {Database};')
cur.execute(f'create database {Database};')
cur.execute(f'use {Database};')
cur.execute("set names 'utf8';")
cur.execute("set character set utf8;")
# creating table for channel ids and time
cur.execute(
    'create table channels (channel_id varchar(25) primary key, '
    'time time);')

# creating table for storing the links
cur.execute(
    "create table articles (links varchar(200) primary key, title "
    "varchar(200), category varchar(20), link_date date, "
    "update_time datetime);")

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
                article['link'] = ("https://finshots.in"
                                   + item.find('a')['href'])

            now = datetime.datetime.now().strftime(r"%Y:%m:%d %H:%M:%S")

            # updating links into articles table
            sql = ("insert into articles values(%s,%s,%s, %s, %s);")
            val = (article['link'], article['title'],
                   category[url], article['link_date'], now)
            cur.execute(sql, val)
            db.commit()

# setting older articles update_time to 3 days back to avoid spam
cur.execute(
    "update articles set update_time = date_sub(curdate(), interval 3 day)"
    " where link_date != curdate();")

# closing the database connection
cur.close()
db.close()

print('success! database updated with all articles!')
