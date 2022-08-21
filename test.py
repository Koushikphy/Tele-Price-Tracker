import requests # used to fetch websites
from bs4 import BeautifulSoup #used to parse websites
headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36' }

URLs=[
    "https://www.flipkart.com/allen-solly-color-block-men-polo-neck-grey-t-shirt/p/itm42c82b45d0082?pid=TSHGDHWEYED7FWGQ&otracker=wishlist&lid=LSTTSHGDHWEYED7FWGQ3OMIVE&fm=organic&iid=00ce9a87-d51e-4190-befd-58bad6901bc3.TSHGDHWEYED7FWGQ.PRODUCTSUMMARY&ppt=hp&ppn=homepage&ssid=sfqaa4srfk0000001661087789527",
    "https://www.flipkart.com/eyebogler-striped-men-polo-neck-black-t-shirt/p/itmca7bb58390b95?pid=TSHG99FKSYJBQ7PS&otracker=wishlist&lid=LSTTSHG99FKSYJBQ7PSEFNYZM&fm=organic&iid=8768f785-896c-4b94-941b-7326f417e20c.TSHG99FKSYJBQ7PS.PRODUCTSUMMARY&ppt=hp&ppn=homepage&ssid=sfqaa4srfk0000001661087789527",
    "https://www.flipkart.com/allen-solly-solid-men-polo-neck-multicolor-t-shirt/p/itm05d8a277e8502?pid=TSHGDHW8AGZFAHZU&otracker=wishlist&lid=LSTTSHGDHW8AGZFAHZUWNQTXB&fm=organic&iid=c47898a6-1145-488b-934e-efe35e1cff3a.TSHGDHW8AGZFAHZU.PRODUCTSUMMARY&ppt=hp&ppn=homepage&ssid=sfqaa4srfk0000001661087789527",
    "https://www.flipkart.com/yha-men-checkered-casual-dark-green-shirt/p/itm7bfddbb7c0ec0?pid=SHTG2DEFV3J4YMGZ&otracker=wishlist&lid=LSTSHTG2DEFV3J4YMGZPEAGV5&fm=organic&iid=b87ad5c6-8486-4da0-857c-4bb37010fbea.SHTG2DEFV3J4YMGZ.PRODUCTSUMMARY&ppt=hp&ppn=homepage&ssid=sfqaa4srfk0000001661087789527",
    "https://www.flipkart.com/zexer-solid-men-black-tights/p/itm54e3e559c22a1?pid=TGTFP3RNHK5KJ9P7&otracker=wishlist&lid=LSTTGTFP3RNHK5KJ9P7KWLSZN&fm=organic&iid=de3d2143-36e0-4629-808c-f3167213d9ea.TGTFP3RNHK5KJ9P7.PRODUCTSUMMARY&ppt=hp&ppn=homepage&ssid=sfqaa4srfk0000001661087789527",
    "https://www.flipkart.com/never-lose-solid-men-black-tights/p/itmfgg7cj4ydpmhx?pid=TGTFGHVFJTW5J8VY&otracker=wishlist&lid=LSTTGTFGHVFJTW5J8VYSBM2FF&fm=organic&iid=cf76f12e-b268-492f-a7f3-aa4e8190f075.TGTFGHVFJTW5J8VY.PRODUCTSUMMARY&ppt=hp&ppn=homepage&ssid=sfqaa4srfk0000001661087789527",
    "https://www.flipkart.com/lycot-solid-men-black-tights/p/itmca6b38634c26f?pid=TGTFXBA53ZTSX6KC&otracker=wishlist&lid=LSTTGTFXBA53ZTSX6KCFE8SUP&fm=organic&iid=b1196522-3d3a-489b-9047-d39f58b1afb9.TGTFXBA53ZTSX6KC.PRODUCTSUMMARY&ppt=hp&ppn=homepage&ssid=sfqaa4srfk0000001661087789527",
    "https://www.flipkart.com/sansar-nursery-two-layer-bamboo-plant/p/itmfdgfjx9tkm7ry?pid=PSGFDFWYY4GZQZHP&otracker=wishlist&lid=LSTPSGFDFWYY4GZQZHPYAHKKH&fm=organic&iid=e307d06e-b783-4eff-862b-365c8ecf37cd.PSGFDFWYY4GZQZHP.PRODUCTSUMMARY&ppt=hp&ppn=homepage&ssid=sfqaa4srfk0000001661087789527",
    "https://www.flipkart.com/roadster-color-block-men-polo-neck-grey-t-shirt/p/itmae1fecbe549e8?pid=TSHFBQJSB7WEPCYG&otracker=wishlist&lid=LSTTSHFBQJSB7WEPCYGCJJZAD&fm=organic&iid=0ff0590e-41b0-4555-9b86-655b82404836.TSHFBQJSB7WEPCYG.PRODUCTSUMMARY&ppt=hp&ppn=homepage&ssid=sfqaa4srfk0000001661087789527",
]


def check_price_flipkart(url):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    title = soup.find("span", {"class": "B_NuCI"}).get_text()
    price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text()[1:].replace(',','')
    print(price,title) #prints the price
for u in URLs:
    check_price_flipkart(u)
# check_price_flipkart()

# def check_price_amazon():
#     page = requests.get(URL, headers=headers)
#     soup = BeautifulSoup(page.content, 'html.parser')
#     title = soup.find("span", {"id": "productTitle"}).get_text()
#     price = soup.find("span", {"class": "a-offscreen"}).get_text()[1:].replace(',','')
#     print(price,title) #prints the price

# check_price_amazon()


