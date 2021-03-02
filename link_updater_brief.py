"""his script when run will extract article links from the Finshots website
 and update the links table in database"""

import datetime
import os

import mysql.connector as mc
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# making the connection to database
load_dotenv()
User = os.getenv('USER')
Host = os.getenv('HOST')
Password = os.getenv('PASSWORD')
Database = os.getenv('DATABASE')

db = mc.connect(user=User, host=Host, password=Password, database=Database)
cur = db.cursor()

# scrapping links form the finshots website
url = "https://finshots.in/brief/"
r = requests.get(url).content

soup = BeautifulSoup(r, 'html.parser')
div = soup.find('div', class_='post-feed')
briefs = div.find_all('article')

# updating new brief links in the database
for item in briefs:
    brief = {
        'link_b': "https://finshots.in" + item.find('a')['href'],
        'title_b': item.find('img')['alt'],
        'link_date_b': item.find('time')['datetime']}
    now = datetime.datetime.now().strftime(r"%Y:%m:%d %H:%M:%S")

    try:
        cur.execute(
            f"insert into brief values('{brief['link_b']}',"
            f"'{brief['title_b']}','{brief['link_date_b']}','{now}');")
        db.commit()
    except (mc.errors.IntegrityError, mc.errors.ProgrammingError):
        pass

print('database updated with fresh new briefs!')

# keeps only 10 latest articles
cur.execute(
    'delete from brief where link_date_b'
    ' not in(select link_date_b from'
    '(select link_date_b from brief order by link_date_b desc limit 10)fo);')
db.commit()

# closing connection to the database
cur.close()
db.close()
