"""This file will delete existing database if any with the provided name in
env file And create a fresh database with the required structure for the
finshots_scout code to function """

import os

import mysql.connector as mc
from dotenv import load_dotenv

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

# creating table for channel ids and time
cur.execute(
    'create table channels (channel_id varchar(25) primary key, '
    'time time);')

# creating table for storing the links
cur.execute(
    "create table articles (links varchar(200) primary key, title "
    "varchar(200), category varchar(20), link_date date, "
    "update_time datetime);")

print('Database created succesfully')

# feeding in articles to the database
os.system('database_updater.py')

# setting older articles update_time to 3 days back to avoid spam
cur.execute(
    "update articles set update_time = date_sub(curdate(), interval 3 day)"
    " where link_date != curdate();")

# closing the database connection
cur.close()
db.close()
