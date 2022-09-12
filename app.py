from flask import Flask, render_template, request
from flask_cors import CORS,cross_origin
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.common import exceptions
import time
import pymysql
import pytube
import pymongo
from functions_file import AWS_Cred, to_db_home, to_db_stats

client = pymongo.MongoClient("mongodb+srv://muzammil:123456Ab@cluster0.wyo7z.mongodb.net/?retryWrites=true&w=majority")
db = client.test
db = client["You_tube_Comments"]
coll = db['Comments']

app = Flask(__name__)


@app.route("/", methods=['GET'])
@cross_origin()
def home():
    return render_template("index.html")

# route to show the You_tube information on the web UI
@app.route('/review',methods=['POST','GET'])
@cross_origin()
def index():

    if request.method == "POST":
        try:
            driver = webdriver.Chrome()
            searchString = request.form['content']
            time.sleep(4)
            driver.get(searchString)
            content = driver.page_source.encode("utf-8").strip()
            soup = bs(content, 'html.parser')
            channel = driver.find_element('xpath', '//*[@id="text-container"]/yt-formatted-string').text
            titles = soup.findAll('a', id='video-title')
            views = soup.findAll('span', class_="style-scope ytd-grid-video-renderer")
            video_urls = soup.findAll('a', id='video-title')
            thumbNail = driver.find_elements('xpath',
                                            '// *[ @ id = "items"]/ytd-grid-video-renderer/div/ytd-thumbnail/a/yt-img-shadow/img')


            i = 0  # views and time
            j = 0  # urls
            channel_data = []

            for title in titles[:10]:
                title = title.text
                thumbNail_1 = thumbNail[j].get_attribute("src")
                views_1 = views[i].text
                len1 = views[i + 1].text
                url_0 = video_urls[j].get("href")
                url_1 = "https://www.youtube.com{}".format(url_0)
                mydict = {"Channel": channel, "Title": title, "ThumbNail": thumbNail_1, "Views": views_1,
                          "Length": len1, "Video_Url": url_1}
                i = i + 2
                j = j + 1

                channel_data.append(mydict)

            cursor = AWS_Cred()
            to_db_home(cursor, channel_data)

            return render_template('results.html', channel_data=channel_data[0:(len(channel_data)-1)])

        except Exception as e:
            print('The Exception message is: ', e)
            return 'something is wrong'

    else:
        return render_template('index.html')


@app.route('/baseinfo', methods=['POST','GET'])
@cross_origin()
def scrape():
    """
    Extracts the channel statics from the Youtube video given by the URL.

    Args:
        url (str): The URL to the Youtube video

    Raises:
        selenium.common.exceptions.NoSuchElementException:
        When certain elements to look for cannot be found
    """

    if request.method == "POST":
        try:

            driver = webdriver.Chrome()
            url = request.form['baseinfo']
            driver.get(url)
            driver.maximize_window()
            time.sleep(7)
            stats = []
            try:

                title = driver.find_element('xpath', '//*[@id="container"]/h1/yt-formatted-string').text
                views = driver.find_element('xpath', '//*[@id = "count"]/ytd-video-view-count-renderer/span[1]').text
                date = driver.find_element('xpath', '//*[@id="info-strings"]/yt-formatted-string').text
                channel = driver.find_element('xpath', '//*[@id="text"]/a').text
                subscribers = driver.find_element('xpath', '//*[@id="owner-sub-count"]').text
                description = driver.find_element('xpath', '//*[@id="description"]/yt-formatted-string').text
                likes = driver.find_element('xpath',
                                            '//*[@id="top-level-buttons-computed"]/ytd-toggle-button-renderer/a/yt-formatted-string').text

                mydict = {"Title": title, "Views": views, "Date": date, "Channel": channel,
                          "Subscribers": subscribers, "Description": description, "Likes": likes}
                stats.append(mydict)

            except exceptions.NoSuchElementException:
                print("Encontered processing Issue please try again")

            cursor = AWS_Cred()
            to_db_stats(cursor, stats)

            return render_template('basicinfo.html', stats1=mydict)

        except Exception as e:
            print('The Exception message is: ', e)
            return 'something is wrong'

    else:
        return render_template('index.html')


@app.route('/comments', methods=['POST', 'GET'])
@cross_origin()
def comments():
    """
    Extracts the comments from the Youtube video given by the URL.

    Args:
        url (str): The URL to the Youtube video

    Raises:
        selenium.common.exceptions.NoSuchElementException:
        When certain elements to look for cannot be found
    """

    if request.method == "POST":
        try:

            driver = webdriver.Chrome()
            url = request.form['comments']
            driver.get(url)
            driver.maximize_window()
            time.sleep(7)
            # driver.close()

            ## Scraping of Comments:

            comment_section = driver.find_element('xpath', '//*[@id="comments"]')
            driver.execute_script('arguments[0].scrollIntoView();', comment_section)
            time.sleep(7)

            last_height = driver.execute_script('return document.documentElement.scrollHeight')

            while True:

                driver.execute_script("window.scrollTo(0,'document.documentElement.scrollHeight');")
                time.sleep(2)

                new_height = driver.execute_script('return document.documentElement.scrollHeight')

                if new_height == last_height:
                    break

                last_height = new_height

            driver.execute_script("window.scrollTo(0,'document.documentElement.scrollHeight');")

            # Extract the elements storing the usernames and comments.
            username_elems = driver.find_elements('xpath', '//*[@id="author-text"]')
            comment_elems = driver.find_elements('xpath', '//*[@id="content-text"]')

            rev1 = []

            for user_name, comments in zip(username_elems, comment_elems):
                mydict2 = {"User_name": user_name.text, "Comments": comments.text}

                rev1.append(mydict2)
            coll.insert_many(rev1)

            # named as "Table"
            return render_template('comments.html',rev1=rev1[0:(len(rev1)-1)])


        except Exception as e:
            print('The Exception message is: ', e)
            return 'something is wrong'


    else:
        return render_template('index.html')


if __name__ == "__main__":
    #app.run(host='127.0.0.1', port=8001, debug=True)
	app.run(debug=True)