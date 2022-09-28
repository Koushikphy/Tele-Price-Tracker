import os
import re
import telebot
import asyncio
import traceback
from time import sleep
from threading import Timer
from bs4 import BeautifulSoup 
from flask import Flask, request
from aiohttp import ClientSession
from psycopg2 import connect, InterfaceError
from aiohttp.client_exceptions import InvalidURL
import requests 


headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36' }

TOKEN = os.getenv("TOKEN")
ADMIN = os.getenv('ADMIN')
dbURL = os.getenv('DATABASE_URL')
ADMIN_NAME = "Koushik Naskar"
server = Flask(__name__)


bot= telebot.TeleBot(TOKEN, parse_mode='HTML')


class DataBase:
    def __init__(self):
        self.dbFile = dbURL
        self.con = connect(self.dbFile)
        with self.con:
            with self.con.cursor() as cur:
                # create database tables and insert admin details
                cur.execute( "CREATE TABLE IF NOT EXISTS ITEMS("
                "itemID SERIAL PRIMARY KEY,"
                "userId INTEGER NOT NULL,"
                "link TEXT NOT NULL UNIQUE,"
                "name TEXT NOT NULL,"
                "addedPrice INTEGER NOT NULL,"
                "price INTEGER NOT NULL);"
                )
    

    def connectToDb(self):
        # flyio postgresql disconnects after 30 minutes of inactivity
        if self.con.closed !=0:
            sendToAdmin(f'Current value of connection {self.con.closed}')
            self.con = connect(self.dbFile)
            sleep(1)
        else:
            try:
                with self.con:
                    with self.con.cursor() as cur:
                        cur.execute("SELECT count(*) from ITEMS;")
            except InterfaceError:
                # con.closed is 0 but still unable to connect to database
                # sendToAdmin("con.closed fails to check properly")
                self.con = connect(self.dbFile)



    def addItem(self,user,_link):
        try:
            self.connectToDb()
            # if 'amazon' in _link or 'amzn' in _link:
            if 'flipkart' not in _link and "myntra" not in _link:
                bot.send_message(user,"Currently, this bot does not support link from this website.")
                return

            message = bot.send_message(user, "Searching for the product🧐. Please wait.")
            links = re.findall("(?P<url>https?://[^\s]+)",_link)
            if len(links) ==0:
                bot.send_message(user,"No links found.")
                return
            elif len(links)>1:
                bot.send_message(user,"Only one link is supported at a time.")
                return

            link = links[0]

            with self.con:
                with self.con.cursor() as cur:
                    cur.execute("SELECT count(*) from ITEMS where link=%s",(link,))
                    v = cur.fetchone()

                    if v[0]==0:
                        
                        newValues = queryPrice([link])
                        if newValues:
                            n,p = newValues[0]
                            cur.execute(
                                'INSERT into ITEMS (userId, link, name,addedPrice, price) values (%s,%s,%s,%s,%s)',
                                (user,link,n,p,p))

                            bot.send_message(user,
                              f'The following product(s) are added for tracking.\n\n<i>{n}</i> \nCurrent Price: <b>{p}</b>')
                        else:
                            bot.send_message(user,'Unable to find the product.')

                    else:
                        bot.send_message(user,'Link is already in database')
        except InvalidURL:
            bot.send_message(user,'Unable to find the product. Check if the link is ok.')
        except:
            print(traceback.format_exc())
            sendToAdmin("exception occurred in adding new item")
            bot.send_message(user,'Unable to find the product.')
        finally:
            bot.delete_message(message.chat.id, message.message_id)



    def update(self,user):
        # list the items from the database and also query the site for latest price
        try:
            self.connectToDb()
            message = bot.send_message(user, "Checking prices🧐. Please wait.")
            with self.con:
                with self.con.cursor() as cur:
                    cur.execute('SELECT link from ITEMS where userId=%s',(user,))
                    links = [i for (i,) in cur.fetchall()]
                    if len(links)==0:
                        bot.send_message(user,'No items found on list')
                        return
                    newValues = queryPrice(links)
                    if newValues:

                        for l,(_,p) in zip(links,newValues):
                            cur.execute("UPDATE ITEMS SET price=%s where link=%s",(p,l))
                        cur.execute('SELECT name, price, addedPrice,link from ITEMS where userId=%s ORDER BY itemID',(user,))
                        txt = f"Here is your current product list.\n<b>{'-'*50}</b>\n\n" + self.buildList(cur.fetchall())
                        bot.send_message(user,txt,disable_web_page_preview=True)
                    else:
                        bot.send_message(user,'Unable to get update for some product')
        except:
            print(traceback.format_exc())
            sendToAdmin("exception occurred during update")
        finally:
            bot.delete_message(message.chat.id, message.message_id)



    def scheduleUpdate(self):
        toUpdate = []
        try:
            self.connectToDb()
            with self.con:
                with self.con.cursor() as cur:
                    cur.execute("SELECT userid from ITEMS group by userid")
                    userids = cur.fetchall()
                    for u in userids:
                        cur.execute("SELECT link,price from ITEMS where userid=%s",u)
                        infos = cur.fetchall()
                        links, oPrice = zip(*infos)
                        newValues = queryPrice(links)
                        update = [[p,l] for l,(_,p) in zip(links,newValues) if p ]
                        # print(update)
                        noUpdate = [l for l,(_,p) in zip(links,newValues) if not p ]
                        if len(noUpdate):
                            sendToAdmin("Cound not update these links\n" +"\n".join(noUpdate))
                        cur.executemany("UPDATE ITEMS SET price=%s where link=%s",update)
                        
                        # check if price of any product is dropped
                        for oP,(_,nP) in zip(oPrice,newValues):
                            if int(nP)<oP:
                                # note whom to send the notification
                                toUpdate.append(u)
                                break
                
            with self.con:
                with self.con.cursor() as cur:
                    for u in toUpdate:
                        print(f"Price dropped for items for user {u[0]}")
                        cur.execute('SELECT name, price, addedPrice, link from ITEMS where userId=%s ORDER BY itemID',u)
                        txt = f"<b>Price dropped for some items in your list.</b>\n<b>{'-'*50}</b>\n\n" + self.buildList(cur.fetchall())
                        bot.send_message(u[0],txt,disable_web_page_preview=True)
            # sendToAdmin('Scheduled update done.')
        except:
            print(traceback.format_exc())
            sendToAdmin("exception occurred in schedule update")




    def buildList(self,info):
        # info is a list fo title, price and added price
        txt = ""
        for i,(title,price,addedPrice,link) in enumerate(info):
            txt += f"{i+1}. <a href='{link}'><i>{title}</i></a>\nPrice: <b>{price}</b>"
            if price-addedPrice>0:
                txt += f" [&#x25B2;{addedPrice}]"
            elif price-addedPrice<0:
                txt += f" [&#x25BC;{addedPrice}]"
            txt += "\n\n"
        return txt


    def untrack(self,user,_prompt):
        try:
            self.connectToDb()
            prompt = _prompt.strip('/untrack').strip()
            if len(prompt)==0: # send the list
                with self.con:
                    with self.con.cursor() as cur:
                        cur.execute('SELECT itemID,name from ITEMS where userId=%s ORDER BY itemID',(user,))
                        values = cur.fetchall()
                        if len(values) == 0:
                            bot.send_message(user,'No items found on list')
                            return
                        txt = "Choose the link beside the product to untrack.\n"
                        txt += f"<b>{'-'*50}</b>\n\n"
                        for i,(iID,name) in enumerate(values):
                            txt += f"{i+1}. {name}\n/untrack{iID} \n"
                        bot.send_message(user,txt)
            else: # untrack item
                with self.con:
                    with self.con.cursor() as cur:
                        cur.execute("DELETE from items where itemID=%s RETURNING name",(prompt,))
                        name = cur.fetchone()[0]
                        bot.send_message(user, f"Your product <i>{name}</i> is removed from list.")
        except:
            print(traceback.format_exc())
            sendToAdmin("exception occurred during untrack")

    def listAll(self):
        try:
            self.connectToDb()
            with self.con:
                with self.con.cursor() as cur:
                    cur.execute("Select userId, count(*) from items group by userId;")
                    txt = '\n'.join([f"{i} - {j}" for i,j in cur.fetchall()])
                    bot.send_message(ADMIN,txt)
        except:
            print(traceback.format_exc())
            sendToAdmin("exception occurred in status")
        



db = DataBase()


# NOTE:----------------------------------------------------------
# amazon does not allow the web scrapping from the cloud
# will solve this later


async def check_price(session:ClientSession, url:str):
    async with session.get(url) as resp:
        # print("checking price for ",url)
        page = await resp.read()
        soup = BeautifulSoup(page, 'html.parser')
        if 'flipkart' in url: # if flipkart
            title = soup.find("span", {"class": "B_NuCI"})
            if title :
                title = title.get_text().strip()
            else:
                return None,None
            company = soup.find("span", {"class": "G6XhRU"})
            company = company.get_text().strip() if company else ""
            price = soup.find("div", {"class": "_30jeq3 _16Jk6d"})
            if price:
                price = price.get_text()[1:].replace(',','')
            else:
                return None, None
            print('checking price',title,price)
            fullTitle = f"{company} {title}"
            return fullTitle,price #prints the price
        elif "myntra" in url:
            title = soup.find("h1", {"class": "pdp-name"})
            if title :
                title = title.get_text().strip()
            else:
                return None,None
            company = soup.find("h1", {"class": "pdp-title"})
            company = company.get_text().strip() if company else ""
            price = soup.find("div", {"class": "pdp-price"})
            if price:
                price = price.get_text()[1:].replace(',','')
            else:
                return None, None
            print('checking price',title,price)
            fullTitle = f"{company} {title}"
            return fullTitle,price #prints the price
        # else:
        #     return None,None
        # elif 'amazon' in url or 'amzn' in url:# for amazon
        #     title = soup.find("span", {"id": "productTitle"}).get_text()
        #     price = soup.find("span", {"class": "a-offscreen"}).get_text()[1:].replace(',','')


async def auxqueryPrice(URLs):
    async with ClientSession() as session:
        tasks = [asyncio.ensure_future(check_price(session, u)) for u in URLs]
        return await asyncio.gather(*tasks)


def queryPrice(URLs):
    return asyncio.run(auxqueryPrice(URLs))




def check_price_flipkart(url:str):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    # print(soup)
    try:
        if 'flipkart' in url: # if flipkart
            print('checking for flipkart')
            title = soup.find("span", {"class": "B_NuCI"}).get_text()
            price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text()[1:].replace(',','')
        elif 'amazon' in url or 'amzn' in url:# for amazon
            print('checking for amazon')
            title = soup.find("span", {"id": "productTitle"}).get_text()
            price = soup.find("span", {"class": "a-offscreen"}).get_text()[1:].replace(',','')
            return title,price
        else:
            print('Unknown website')
    except:
        print(traceback.format_exc())
        sendToAdmin("exception occurred")



def helpMessage(user):
    bot.send_message(user,(
        'Send a product link and this bot will track the price for you.\n'
        'Send /check to check prices for all the products in the list.\n'
        'Send /untrack to untrack products.\n'
        'Currently only supports link for flipkart.'
        ))



@bot.message_handler(func=lambda _: True)
def newLink(message):
    link:str = message.text
    print("Text received",link)
    user = message.from_user.id
    if link == '/start':
        bot.send_message(user,"Welcome to the TelePriceTracker bot.")
        helpMessage(user)
    elif link == '/help':
        helpMessage(user)
    elif link == '/check':
        db.update(user)

    elif link.startswith('/untrack') : 
        # pass as /untrack 5,6 to untrack them
        db.untrack(user,link)
    elif link.lower()=='status' and int(user) == int(ADMIN):
        db.listAll()
    else:
        print('link received')

        db.addItem(user,link)




@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200



@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://telepricetracker.onrender.com/' + TOKEN)
    return '''<div style="text-align: center;">
    <h1>Tele Price Tracker</h1>
    <h3>Send a product link and this bot will track the price for you.</h3>
    <h2>Open <br><a href="https://t.me/telepricetrackerbot"> https://t.me/telepricetrackerbot</a> <br> to access the bot.</h2>
    </div>''', 200


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def sendToAdmin(msg:str):
    bot.send_message(ADMIN,msg)


if __name__ == "__main__":
    sendToAdmin("Bot started")
    t = RepeatTimer(3600, db.scheduleUpdate).start()
    from waitress import serve
    serve(server, host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
