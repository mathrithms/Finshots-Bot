"""his script when run will extract image links from the Finshots/inforgraphics
page and update the infographics table in database"""

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
url = "https://finshots.in/infographic/"
r = requests.get(url).content

soup = BeautifulSoup(r, 'html.parser')
div = soup.find('div', class_='post-feed')
articles = div.find_all('article')

# updating news links in the database
for item in articles:

    article = {
        'img': item.find('img')['src'],
        'discription': item.find('img')['alt'],
        'link_date': item.find('time')['datetime']
    }

    now = datetime.datetime.now().strftime(r"%Y:%m:%d %H:%M:%S")

    try:
        cur.execute(
            f"insert into infographics values('{article['img']}',"
            f" '{article['discription']}', '{article['link_date']}',"
            f"'{now}'); ")
        db.commit()

    except (mc.errors.IntegrityError, mc.errors.ProgrammingError):
        pass


# deleting articles older than 7 days from the database
cur.execute(
    "delete from infographics where link_date not in"
    "(select link_date from(select link_date from infographics"
    "order by link_date desc limit 10)foo);"
)
db.commit()

# closing connection to the database
cur.close()
db.close()
