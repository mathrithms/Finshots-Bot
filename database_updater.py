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
User = os.getenv('DB_USER')
Host = os.getenv('DB_HOST')
Password = os.getenv('DB_PASSWORD')
Database = os.getenv('DB_DATABASE')

db = mc.connect(user=User, host=Host, password=Password, database=Database)
cur = db.cursor()

# storing links to be scrapped
URL = {
    "https://finshots.in/archive": "daily",
    "https://finshots.in/brief/": "brief",
    "https://finshots.in/markets/": "markets",
    "https://finshots.in/infographic/": "infographics"
}

# inserting data for each category
for url in URL:

    # fetching source code of the link
    r = requests.get(url).content

    soup = BeautifulSoup(r, 'html.parser')
    div = soup.find('div', class_='post-feed')
    articles = div.find_all('article')

    for item in articles:
        # scrapping the data
        article = {
            'title': item.find('img')['alt'],
            'link_date': item.find('time')['datetime']
        }
        if URL[url] == 'infographics':
            article['link'] = item.find('img')['src']
        else:
            article['link'] = "https://finshots.in" + item.find('a')['href']

        now = datetime.datetime.now().strftime(r"%Y:%m:%d %H:%M:%S")

        # updating links into articles table
        try:
            sql = ("insert into articles values(%s,%s,%s, %s, %s);")
            val = (article['link'], article['title'],
                   URL[url], article['link_date'], now)
            cur.execute(sql, val)
            db.commit()

        except (mc.errors.IntegrityError, mc.errors.ProgrammingError):
            pass

    # deleting data that is not required
    if URL[url] == 'daily':
        # storing only the links that were updated in last 3 days for archives
        cur.execute(
            f"delete from articles where category='{URL[url]}' and"
            " timestampdiff(day, link_date, curdate())>2 ;"
        )
    else:
        # storing only last 2 links for all other links
        cur.execute(
            "delete from articles where link_date "
            "not in(select link_date from"
            "(select link_date from articles where category="
            f"'{URL[url]}' order by link_date desc limit 2)fo) "
            f" and category='{URL[url]}'"
        )

    db.commit()

print('database updated with latest articles!')

# closing connection to the database
cur.close()
db.close()
