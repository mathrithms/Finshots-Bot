from dotenv import load_dotenv
import os

load_dotenv()
Host='localhost'#os.getenv('Host')
User='root'#os.getenv('User')
Passwd='1234'#os.getenv('Password')
Database='Finshots'#os.getenv('Database')
Table1='time_table'#os.getenv('Table1')

import mysql.connector as sqltor
mycon= sqltor.connect(host=Host,user=User,password=Passwd,database=Database)
cursor=mycon.cursor()

if mycon.is_connected():
    print('connection established')
else:
    print('error connecting to database, please check code')
    sys.exit()
        
def set_time(channel_id,time):
    print(channel_id,time)
    query ='update '+Table1+' set time=%s where channel_id=%s'
    cursor.execute(query,(channel_id,time))
    mycon.commit()
    return 


def add_member(channel_id, time):
    query='insert into '+Table1+'(channel_id,time) values(%s,%s);'
    cursor.execute(query,(channel_id,time))
    mycon.commit()
    return

