import requests # used to fetch websites
from time import time
import aiohttp
import asyncio
from bs4 import BeautifulSoup #used to parse websites
headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36' }


s = time()

def check_price_flipkart(url):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    title = soup.find("span", {"class": "B_NuCI"}).get_text()
    price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text()[1:].replace(',','')
    print(price,title) #prints the price
for u in URLs:
    check_price_flipkart(u)
print(time()-s)


async def main():
    async with aiohttp.ClientSession() as session:
        for u in URLs:
            async with session.get(u) as resp:
                page = await resp.read()
                # print(page)
                soup = BeautifulSoup(page, 'html.parser')
                title = soup.find("span", {"class": "B_NuCI"}).get_text()
                price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text()[1:].replace(',','')
                print(price,title) #prints the price

s= time()
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
# print("--- %s seconds ---" % (time.time() - start_time))

print(time()-s)
