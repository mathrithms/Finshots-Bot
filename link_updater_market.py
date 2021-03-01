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
url = "https://finshots.in/markets/"
r = requests.get(url).content

soup = BeautifulSoup(r, 'html.parser')
div = soup.find('div', class_='post-feed')
markets = div.find_all('article')

# updating new finshot market links in the database
for item in markets:
    market = {
        'link_m': "https://finshots.in" + item.find('a')['href'],
        'title_m': item.find('img')['alt'],
        'link_date_m': item.find('time')['datetime']}
    now = datetime.datetime.now().strftime(r"%Y:%m:%d %H:%M:%S")

    try:
        cur.execute(
            f"insert into market values('{market['link_m']}',"
            f"'{market['title_m']}','{market['link_date_m']}','{now}');")
        db.commit()
    except (mc.errors.IntegrityError, mc.errors.ProgrammingError):
        pass

print('database updated with fresh new market articles!')

# # deleting articles older than 7 days from the database
# cur.execute(
#     'delete from articles where timestampdiff(day, link_date, curdate())>2 ;')
# db.commit()

# closing connection to the database
cur.close()
db.close()
