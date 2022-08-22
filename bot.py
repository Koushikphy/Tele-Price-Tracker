import os
from flask import Flask, request
from psycopg2 import connect
import aiohttp
import asyncio
from bs4 import BeautifulSoup #used to parse websites
import telebot


TOKEN = os.getenv("TOKEN")
ADMIN = os.getenv('ADMIN')
dbURL = os.getenv('DATABASE_URL')
ADMIN_NAME = "Koushik Naskar"
server = Flask(__name__)


bot= telebot.TeleBot(TOKEN, parse_mode='HTML')


# accepts links and add to database
# track price

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
                "link TEXT NOT NULL,"
                "name TEXT NOT NULL,"
                "price INTEGER NOT NULL);"
                )
    

    def addItem(self,user,link):
        # try:
        print('here')
        name, price = queryPrice([link])[0]
        print('--------',name,price)
        with self.con:
            with self.con.cursor() as cur:
                cur.execute('INSERT into ITEMS (userId, link, name,price) values (%s,%s,%s,%s) '
                    ' ON CONFLICT (userid) DO NOTHING',(user,link,name,price))
                print('here-------------------')
                bot.send_message(user,f'<i> {name} is added for tracking. Current price <b> {price} </b>')
        # except Exception as e:
        #     bot.send_message(user,"Failed to add the link. Check if its a proper link")
        #     print(e)

    def removeItem(self):
        pass


    def checkItems(self, user):
        with self.con:
            with self.con.cursor() as cur:
                cur.execute('SELECT link,name,price from ITEMS where userId=%s',(user.id,))
                values = cur.fetchall()
                links = [i[0] for i in values]
                newValues = queryPrice(links)
                txt = '\n\n'.join( f'{i}. <i>{t}</i> (<b>{p}</b>)' for i,(p,t) in enumerate(newValues,start=1)  )
                bot.send_message(user,txt)



db = DataBase()




async def check_price(session, url:str):
    async with session.get(url) as resp:
        page = await resp.read()
        soup = BeautifulSoup(page, 'html.parser')
        # print(url)
        if 'flipkart' in url: # if flipkart
            title = soup.find("span", {"class": "B_NuCI"}).get_text()
            price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text()[1:].replace(',','')
        
        elif 'amazon' in url:# for amazon
            title = soup.find("span", {"id": "productTitle"}).get_text()
            price = soup.find("span", {"class": "a-offscreen"}).get_text()[1:].replace(',','')
        # print(title,price)
        return price,title #prints the price


async def auxqueryPrice(URLs):
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.ensure_future(check_price(session, u)) for u in URLs]
        return await asyncio.gather(*tasks)


def queryPrice(URLs):
    return asyncio.run(auxqueryPrice(URLs))



@bot.message_handler(func=lambda _: True)
def newLink(message):
    # Only admin allowed functions
    link = message.text
    user = message.from_user.id
    print('link received')
    if 'flipkart' not in link and 'amazon' not in link:
        bot.send_message(user, 'This is not a valid link.')

    # try to get the product name and price
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
    <h1>Jobs Reminder</h1>
    <h3>A Telegram bot that notifies you about your computer jobs.</h3>
    <h2>Open <br><a href="https://t.me/JobReminderBot"> https://t.me/JobReminderBot</a> <br> to access the bot.</h2>
    </div>''', 200




if __name__ == "__main__":
    bot.send_message(ADMIN,'Bot Started')
    from waitress import serve
    serve(server, host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
