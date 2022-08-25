import os
from flask import Flask, request
from psycopg2 import connect
import asyncio
from bs4 import BeautifulSoup #used to parse websites
import telebot
from aiohttp import ClientSession
from aiohttp.client_exceptions import InvalidURL
import requests # used to fetch websites
import traceback

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
        self.con = connect(dbURL)
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
    

    def addItem(self,user,link):
        try:
            message = bot.send_message(user, "Searching for the product🧐. Please wait.")
            with self.con:
                with self.con.cursor() as cur:
                    cur.execute("SELECT count(*) from ITEMS where link=%s",(link,))
                    v = cur.fetchone()

                    if v[0]==0:
                        name,price = queryPrice([link])[0]
                        cur.execute(
                            'INSERT into ITEMS (userId, link, name,addedPrice, price) values (%s,%s,%s,%s,%s)',
                            (user,link,name,price,price))
                        bot.send_message(user,f'The following product is added for tracking.\n<i> {name}</i> \nCurrent Price: <b> {price} </b>')
                    else:
                        bot.send_message(user,'Link is already in database')
        except InvalidURL:
            bot.send_message(user,'Unable to find the product. Check if the link is ok.')
        except:
            print(traceback.format_exc())
        finally:
            bot.delete_message(message.chat.id, message.message_id)




    def update(self,user):
        # list the items from the database and also query the site for latest price
        try:
            message = bot.send_message(user, "Checking prices🧐. Please wait.")
            with self.con:
                with self.con.cursor() as cur:
                    cur.execute('SELECT link from ITEMS where userId=%s',(user,))
                    links = [i for (i,) in cur.fetchall()]
                    if len(links)==0:
                        bot.send_message(user,'No items found on list')
                        return
                    newValues = queryPrice(links)

                    for l,(_,p) in zip(links,newValues):
                        cur.execute("UPDATE ITEMS SET price=%s where link=%s",(p,l))
                    cur.execute('SELECT name, price, addedPrice,link from ITEMS where userId=%s',(user,))
                    txt = self.buildList(cur.fetchall())
                    bot.send_message(user,txt,disable_web_page_preview=True)
        except:
            print(traceback.format_exc())
        finally:
            bot.delete_message(message.chat.id, message.message_id)





    def buildList(self,info):
        # info is a list fo title, price and added price
        txt = "Here is your current product list.\n"
        txt += f"<b>{'-'*50}</b>\n\n"
        for i,(title,price,addedPrice,link) in enumerate(info):
            txt += f"{i+1}. <a href='{link}'><i>{title}</i></a>\n Price: <b>{price}</b>"
            if price-addedPrice>0:
                txt += f" [&#x25B2;{addedPrice}]"
            elif price-addedPrice<0:
                txt += f" [&#x25BC;{addedPrice}]"
            txt += "\n\n"
        return txt


    def untrack(self,user,_prompt):
        try:
            prompt = _prompt.strip('/untrack').strip()
            if len(prompt)==0: # send the list
                with self.con:
                    with self.con.cursor() as cur:
                        cur.execute('SELECT itemID,name from ITEMS where userId=%s',(user,))
                        values = cur.fetchall()
                        if len(values) == 0:
                            bot.send_message(user,'No items found on list')
                            return
                        txt = "Choose the link beside the product to untrack.\n"
                        txt += f"<b>{'-'*50}</b>\n\n"
                        for i,(iID,name) in enumerate(values):
                            txt += f"{i+1}. {name} /untrack{iID} \n"
                        bot.send_message(user,txt)
            else: # untrack item
                with self.con:
                    with self.con.cursor() as cur:
                        cur.execute("DELETE from items where itemID=%s RETURNING name",(prompt,))
                        name = cur.fetchone()[0]
                        bot.send_message(user, f"Your product <i>{name}</i> is removed from list.")
        except:
            print(traceback.format_exc())

    def listAll(self):
        try:
            with self.con:
                with self.con.cursor() as cur:
                    cur.execute("Select userId, count(*) from items group by userId;")
                    txt = '\n'.join([f"{i} - {j}" for i,j in cur.fetchall()])
                    bot.send_message(ADMIN,txt)
        except:
            print(traceback.format_exc())
        



db = DataBase()


# NOTE:----------------------------------------------------------
# amazon does not allow the web scrapping from the cloud, it blocks the heroku ip address
# will solve this later


async def check_price(session:ClientSession, url:str):
    async with session.get(url) as resp:
        print("checking price for ",url)
        page = await resp.read()
        soup = BeautifulSoup(page, 'html.parser')
        if 'flipkart' in url: # if flipkart
            title = soup.find("span", {"class": "B_NuCI"}).get_text()
            price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text()[1:].replace(',','')
        
        # elif 'amazon' in url or 'amzn' in url:# for amazon
        #     title = soup.find("span", {"id": "productTitle"}).get_text()
        #     price = soup.find("span", {"class": "a-offscreen"}).get_text()[1:].replace(',','')
        print('checking price',title,price)
        return title,price #prints the price


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
    if 'flipkart' in url: # if flipkart
        print('checking for flipkart')
        title = soup.find("span", {"class": "B_NuCI"}).get_text()
        price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text()[1:].replace(',','')
        return title,price
    else:
        print('Unknown website')
    # elif 'amazon' in url or 'amzn' in url:# for amazon
    #     print('checking for amazon')
    #     title = soup.find("span", {"id": "productTitle"}).get_text()
    #     price = soup.find("span", {"class": "a-offscreen"}).get_text()[1:].replace(',','')


def helpMessage(user):
    bot.send_message(user,(
        'Send a product link and this bot track the price for you.\n'
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
    elif link.lower()=='list' and int(user) == int(ADMIN):
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
    bot.set_webhook(url='https://tele-price-tracker.herokuapp.com/' + TOKEN)
    return '''<div style="text-align: center;">
    <h1>Tele Price Tracker</h1>
    <h3>Send a product link and this bot track the price for you.</h3>
    <h2>Open <br><a href="https://t.me/telepricetrackerbot"> https://t.me/telepricetrackerbot</a> <br> to access the bot.</h2>
    </div>''', 200




if __name__ == "__main__":
    bot.send_message(ADMIN,'Bot Started.')
    from waitress import serve
    serve(server, host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
