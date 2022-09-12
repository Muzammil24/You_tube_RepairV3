from flask import Flask, render_template, request
from flask_cors import CORS,cross_origin
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.common import exceptions
import time
import pymysql
# importing the module
from pytube import YouTube
import pandas as pd
import csv


def AWS_Cred():
    """
    This Function Is Used to Authenticate to DB on AWS, which Uses AWS RDB Service
    :return:
    """
    mydb = pymysql.connect(host='youtube-db.canomptavg82.ap-south-1.rds.amazonaws.com', user='admin',
                           password='admin123', database="youtube1")
    cursor = mydb.cursor()
    cursor.execute("select version()")
    cursor.fetchone()

    return cursor

def create_DB(cursor,DB):
    """
    This Function is Used to Create DB"
    :param cursor:
    :return:
    """

    sql = "create database {}".format(DB)
    cursor.execute(sql)
    cursor.connection.commit()

    sql = "use {}".format(DB)
    cursor.execute(sql)
    cursor.connection.commit()



def to_db_home(cursor,lst_P):
    sql = 'INSERT INTO youtab (`Title`,`Views`, `Length`, `Video_url`) VALUES (%s,%s,%s,%s)'
    for i in lst_P:
        cursor.execute(sql, (i["Title"], i["Views"], i["Length"], i["Video_Url"]))
    cursor.connection.commit()

def to_db_stats(cursor,lst_P):
    sql = 'INSERT INTO youtab_stat (`Title`,`Views`, `Date`, `Channel`,`Subscribers`,`Description`,`Likes`) VALUES (%s,%s,%s,%s,%s,%s,%s)'
    for i in lst_P:
        cursor.execute(sql, (
        i["Title"], i["Views"], i["Date"], i["Channel"], i["Subscribers"], i["Description"], i["Likes"]))
    cursor.connection.commit()


def index(url):
    """
    Scrapes You_Tube Data
    :param url:
    :return:
    """
    try:
        driver = webdriver.Chrome()
        searchString = (url)
        driver.get(searchString)
        content = driver.page_source.encode("utf-8").strip()
        soup = bs(content, 'lxml')
        titles = soup.findAll('a', id='video-title')
        views = soup.findAll('span', class_="style-scope ytd-grid-video-renderer")
        video_urls = soup.findAll('a', id='video-title')

        i = 0  # views and time
        j = 0  # urls
        channel_data = []

        for title in titles[:50]:
            title = title.text
            views_1 = views[i].text
            len1 = views[i + 1].text
            url_0 =  video_urls[j].get("href")
            url_1 = "https://www.youtube.com{}".format(url_0)

            mydict = {"Title": title, "Views": views_1, "Length": len1, "Video_Url": url_1}
            i = i + 2
            j = j + 1

            channel_data.append(mydict)
        cursor = AWS_Cred()
        to_db_home(cursor,channel_data)

    except Exception as e:
        print('The Exception message is: ', e)
        return 'something is wrong'

    return channel_data

cursor = AWS_Cred()

def value_check(tableName,cursor):
    """
    This Function shows the data in side the table it takes two parameters
    :param tableName: Shoulb be closed in double Quotes
    :param cursor:
    :return:
    """
    sql = "select * from " + tableName
    cursor.execute(sql)
    res = cursor.fetchall()
    return res

url = "https://www.youtube.com/c/TheLiveTvnews/videos"



def to_download_videos():

    # where to save
    SAVE_PATH = "https://drive.google.com/drive/u/0/my-drive"  # to_do

    # link of the video to be downloaded
    link = "https://www.youtube.com/watch?v=xWOoBJUqlbI"

    try:
        # object creation using YouTube
        # which was imported in the beginning
        yt = YouTube(link)
    except:
        print("Connection Error")  # to handle exception

    # filters out all the files with "mp4" extension
    mp4files = yt.filter('mp4')

    # to set the name of the file
    yt.set_filename('GeeksforGeeks Video')

    # get the video with the extension and
    # resolution passed in the get() function
    d_video = yt.get(mp4files[-1].extension, mp4files[-1].resolution)
    try:
        # downloading the video
        d_video.download(SAVE_PATH)
    except:
        print("Some Error!")
    print('Task Completed!')


if __name__ == "__main__":

    stats = value_check("youtab_stat", cursor)


    lst_stat = []
    for data in stats:
        lst_stat.append(data)

    df = pd.DataFrame(lst_stat, columns=["Title", "Views", "Date", "Channel", "Subscribers","Description","Likes"])
    df.to_csv("YouTab_stat.csv")

    comments = value_check("youtab", cursor)

    lst = []
    for data in comments:
        lst.append(data)

    df = pd.DataFrame(lst, columns=["Channel Name", "Video Title", "Number of Views", "Posted on", "Url"])
    df.to_csv("YouTab.csv")

