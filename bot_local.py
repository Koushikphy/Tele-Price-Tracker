import os
from sqlite3 import connect
import asyncio
from bs4 import BeautifulSoup
import telebot
from aiohttp import ClientSession
from aiohttp.client_exceptions import InvalidURL
import requests
import traceback
import logging
from threading import Timer


headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36' }

TOKEN = os.getenv("TOKEN")
ADMIN = os.getenv('ADMIN')
dbURL = os.getenv('DATABASE_URL')
ADMIN_NAME = "Koushik Naskar"


bot= telebot.TeleBot(TOKEN, parse_mode='HTML')


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def make_logger():
    #Create the logger
    logger = logging.getLogger('Tel')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("tel.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("[%(asctime)s] - %(message)s","%d-%m-%Y %I:%M:%S %p"))
    logger.addHandler(fh)
    return logger

logger = make_logger()




class DataBase:
    def __init__(self,dbFile):
        self.dbFile = dbFile
        self.con = connect(dbFile, check_same_thread=False)
        with connect(self.dbFile) as con:
            cur = con.cursor()
            # create database tables and insert admin details
            cur.execute( "CREATE TABLE IF NOT EXISTS ITEMS("
            "itemID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
            "userId INTEGER NOT NULL,"
            "link TEXT NOT NULL UNIQUE,"
            "name TEXT NOT NULL,"
            "addedPrice INTEGER NOT NULL,"
            "price INTEGER NOT NULL);"
            )


    def addItem(self,user,link):
        try:
            logger.info(f"New link request from {user}: {link}")
            message = bot.send_message(user, "Searching for the product🧐. Please wait.")
            with connect(self.dbFile) as con:
                cur = con.cursor()
                cur.execute("SELECT count(*) from ITEMS where link=?",(link,))
                v = cur.fetchone()

                if v[0]==0:
                    name,price = queryPrice([link])[0]
                    logger.info(f"New product added to list {name} [{price}]")
                    cur.execute(
                        'INSERT into ITEMS (userId, link, name,addedPrice, price) values (?,?,?,?,?)',
                        (user,link,name,price,price))
                    bot.send_message(user,f'The following product is added for tracking.\n<i>{name}</i> \nCurrent Price: <b>{price}</b>')
                else:
                    bot.send_message(user,'Link is already in database')
                    logger.info("Link is already in database")
        except InvalidURL:
            bot.send_message(user,'Unable to find the product. Check if the link is ok.')
            logger.info(f"Unable to product the link {link}")
        except:
            print(traceback.format_exc())
        finally:
            bot.delete_message(message.chat.id, message.message_id)




    def update(self,user):
        # list the items from the database and also query the site for latest price
        try:
            logger.info(f"Update triggered for user {user}")
            message = bot.send_message(user, "Checking prices🧐. Please wait.")
            with connect(self.dbFile) as con:
                cur = con.cursor()
                cur.execute('SELECT link from ITEMS where userId=?',(user,))
                links = [i for (i,) in cur.fetchall()]
                if len(links)==0:
                    bot.send_message(user,'No items found on list')
                    return
                newValues = queryPrice(links)

                for l,(_,p) in zip(links,newValues):
                    cur.execute("UPDATE ITEMS SET price=? where link=?",(p,l))
                cur.execute('SELECT name, price, addedPrice,link from ITEMS where userId=?',(user,))
                txt = f"Here is your current product list.\n<b>{'-'*50}</b>\n\n" + self.buildList(cur.fetchall())
                bot.send_message(user,txt,disable_web_page_preview=True)
        except:
            print(traceback.format_exc())
        finally:
            bot.delete_message(message.chat.id, message.message_id)



    def scheduleUpdate(self):
        toUpdate = []
        logger.info("Schedule update trigger.")
        with connect(self.dbFile) as con:
            cur = con.cursor()
            cur.execute("SELECT userid from ITEMS group by userid")
            userids = cur.fetchall()
            for u in userids:
                cur.execute("SELECT link,price from ITEMS where userid=?",u)
                infos = cur.fetchall()
                links, oPrice = zip(*infos)
                newValues = queryPrice(links)
                update = [[p,l] for l,(_,p) in zip(links,newValues)]
                print(update)
                cur.executemany("UPDATE ITEMS SET price=? where link=?",update)
                
                # check if price of any product is dropped
                for oP,(_,nP) in zip(oPrice,newValues):
                    if int(nP)<oP:
                        # note whom to send the notification
                        toUpdate.append(u)
                        break
        
        with connect(self.dbFile) as con:
            cur = con.cursor()
            for u in toUpdate:
                logger.info(f"Price dropped for items for user {u[0]}")
                cur.execute('SELECT name, price, addedPrice, link from ITEMS where userId=?',u)
                txt = f"<b>Price dropped for some items in your list.</b>\n<b>{'-'*50}</b>\n\n" + self.buildList(cur.fetchall())
                bot.send_message(u[0],txt,disable_web_page_preview=True)





    def buildList(self,info):
        # info is a list fo title, price and addedprice, link
        # print(info)
        def sourceType(link):
            if 'flipkart' in link: # if flipkart
                return "Flipkart"
            elif 'amazon' in link or 'amzn' in link:# for amazon
                return 'Amazon'

        txt = ''
        for i,(title,price,addedPrice,link) in enumerate(info):

            txt += f"{i+1}. <i>{title}</i> (<a href='{link}'>Open in {sourceType(link)}</a>) \nPrice: <b>{price}</b>"
            if price-addedPrice>0:
                txt += f" [&#x25B2;{addedPrice}]"
            elif price-addedPrice<0:
                txt += f" [&#x25BC;{addedPrice}]"
            txt += "\n\n"
        return txt


    def untrack(self,user,_prompt):
        try:
            logger.info(f"Untrack requested for user {user}")
            prompt = _prompt.strip('/untrack').strip()
            if len(prompt)==0: # send the list
                with connect(self.dbFile) as con:
                    cur = con.cursor()
                    cur.execute('SELECT itemID,name from ITEMS where userId=?',(user,))
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
                with connect(self.dbFile) as con:
                    cur = con.cursor()
                    cur.execute("SELECT name from items where itemID=?",(prompt,))
                    name = cur.fetchone()[0]
                    logger.info(f"Removing item {name} from list of {user}")
                    cur.execute("DELETE from items where itemID=?",(prompt,))
                    bot.send_message(user, f"Your product <i>{name}</i> is removed from list.")
        except:
            print(traceback.format_exc())


    def listAll(self):
        try:
            with connect(self.dbFile) as con:
                cur = con.cursor()
                cur.execute("Select userId, count(*) from items group by userId;")
                txt = '\n'.join([f"{i} - {j}" for i,j in cur.fetchall()])
                bot.send_message(ADMIN,txt)
        except:
            print(traceback.format_exc())
        


db = DataBase(dbURL)



async def check_price(session:ClientSession, url:str):
    async with session.get(url) as resp:
        # print("checking price for ",url)
        page = await resp.read()

        soup = BeautifulSoup(page, 'html.parser')
        print(soup)
        if 'flipkart' in url: # if flipkart
            title = soup.find("span", {"class": "B_NuCI"}).get_text().strip()
            price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text()[1:].replace(',','')
        
        elif 'amazon' in url or 'amzn' in url:# for amazon
            title = soup.find("span", {"id": "productTitle"}).get_text().strip()
            price = soup.find("span", {"class": "a-offscreen"}).get_text()[1:].replace(',','')
        print('checking price',title,price)
        price = int(float(price))
        return title,price #prints the price


async def auxqueryPrice(URLs):
    async with ClientSession(trust_env = True) as session:
        tasks = [asyncio.ensure_future(check_price(session, u)) for u in URLs]
        return await asyncio.gather(*tasks)


def queryPrice(URLs):
    return asyncio.run(auxqueryPrice(URLs))



def helpMessage(user):
    bot.send_message(user,(
        'Send a product link and this bot will track the price for you.\n'
        'Send /check to check prices for all the products in the list.\n'
        'Send /untrack to untrack products.\n'
        'Currently only supports link for flipkart and amazon.'
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
    elif link.lower()=='list' and int(user) == int(ADMIN):
        db.listAll()
    else:
        print('link received')

        db.addItem(user,link)

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# bot.remove_webhook()
bot.send_message(ADMIN, "Starting bot")
# db.scheduleUpdate()
# RepeatTimer(10, db.scheduleUpdate).start()
bot.infinity_polling()
