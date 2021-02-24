from dotenv import load_dotenv
from datetime import date
import requests
import sys
import os
from bs4 import BeautifulSoup

load_dotenv()
Host=os.getenv('Host')
User=os.getenv('User')
Passwd=os.getenv('Password')
Database=os.getenv('Database')
Table2=os.getenv('Table2')

import mysql.connector as sqltor
mycon= sqltor.connect(host=Host,user=User,password=Passwd,database=Database)
cursor=mycon.cursor()

if mycon.is_connected():
    print('connection established')
else:
    print('error connecting to database, please check code')
    sys.exit()

class data():
    def __init__(self, link, discription, date, sent=False):
        self.link=link
        self.discription=discription
        self.sent=sent
        self.date=date
        
    def getData(self):
         return (self.link,self.discription, self.date, self.sent)
        
cursor.execute("select * from %s"%(Table2))
link,discription,date,sent=cursor.fetchone()
last_feed= data(link,discription,date,sent)

url= "https://finshots.in/archive"
r=requests.get(url).content

soup=BeautifulSoup(r, 'html.parser')
div=soup.find('div',class_='post-feed')
article=div.find_all('article')

for item in article:
    try :
        Data=data("https:/finshots.in"+item.find('a')['href'],item.find('img')['alt'],item.find('time')['datetime'])
        if Data.link==last_feed.link:
            break
        else:
            print(Data.getData())
            query="insert into "+Table2+"(links,discription,date,sent) values(%s,%s,%s,%s);"
            cursor.execute(query,Data.getData())
            mycon.commit()
    except:
        print('error occured please check')
mycon.close()
