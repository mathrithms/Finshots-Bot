# This file will delete existing database if any with the provided name in env file
# And create a fresh database with the required structure for the finshots_scout code to function

import mysql.connector as mc
from dotenv import load_dotenv
import os

# making the connection to database
try:
    load_dotenv()
    User = os.getenv('USER')
    Host = os.getenv('HOST')
    Password = os.getenv('PASSWORD')
    Database = os.getenv('DATABASE')

    db = mc.connect(user = User, host = Host, password = Password)
    if db.is_connected():
        print('MySQL connection successful !')
    else:
        print('Some error occured while connecting to the MySQL server !')
except:
    print('Some error occured while connecting to the MySQL server !')

try:
    cur = db.cursor()

    # creating database
    cur.execute(f'drop database if exists {Database};')
    cur.execute(f'create database {Database};')
    cur.execute(f'use {Database};')

    # creating table for channel ids and time
    cur.execute('create table channels (channel_id varchar(25) primary key, time time);')
    
    # creating table for storing the links
    cur.execute('create table articles (links varchar(200) primary key, title varchar(200), link_date date, update_time datetime);')

    print('Database created succesfully')
except:
    print('Some error occured while creating the database !')

# feeding in articles
os.system('link_updater.py')

# closing the database connection
cur.close()
db.close()