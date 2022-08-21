from time import time
import aiohttp
import asyncio
from bs4 import BeautifulSoup #used to parse websites
headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36' }

with open('./items.txt') as f:
    URLs = f.read().strip().split('\n')


s = time()

async def check_price(session, url):
    async with session.get(url) as resp:
        page = await resp.read()
        soup = BeautifulSoup(page, 'html.parser')
        # for flipkart
        title = soup.find("span", {"class": "B_NuCI"}).get_text()
        price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text()[1:].replace(',','')
        # for amazon
        # title = soup.find("span", {"id": "productTitle"}).get_text()
        # price = soup.find("span", {"class": "a-offscreen"}).get_text()[1:].replace(',','')
        print(price,title) #prints the price


async def main():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in URLs:
            tasks.append(asyncio.ensure_future(check_price(session, url)))
        await asyncio.gather(*tasks)


s= time()
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
# print("--- %s seconds ---" % (time.time() - start_time))

print(time()-s)
