import requests # used to fetch websites
from bs4 import BeautifulSoup #used to parse websites
headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36' }



def check_price_flipkart(url):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    title = soup.find("span", {"class": "B_NuCI"}).get_text()
    price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text()[1:].replace(',','')
    print(price,title) #prints the price

# check_price_flipkart()

# def check_price_amazon():
#     page = requests.get(URL, headers=headers)
#     soup = BeautifulSoup(page.content, 'html.parser')
#     title = soup.find("span", {"id": "productTitle"}).get_text()
#     price = soup.find("span", {"class": "a-offscreen"}).get_text()[1:].replace(',','')
#     print(price,title) #prints the price

# check_price_amazon()



