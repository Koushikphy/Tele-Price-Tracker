<p align="center">
  <h2 align="center">Tele Price Tracker Bot</h2>
  <h3 align="center">A Telegram bot that keeps track of prices for your products.</h3>
</p>

<p align="center">
  <a href="https://t.me/telepricetrackerbot" alt="Version"><img src="https://img.shields.io/badge/Telegram-TelePriceTracker-blue.svg?style=flat&logo=telegram" /></a>  <a href="https://t.me/Koushikphy" alt="Version"><img src="https://img.shields.io/badge/Telegram-Koushik_Naskar-blue.svg?style=flat&logo=telegram" /></a> 
</p>

---
### Usage:
Send a link to the [Tele Price Tracker Bot](https://t.me/telepricetrackerbot) and this bot will keep track the price for you and notify you when the price drops. Currently, it works only on Flipkart products.

### Setting up your own bot:
1. Create a `.env` file and put the following environment variables:
    1. `TOKEN` - Telegram bot token
    2. `ADMIN` - Admin's telegram user id
    3. `DATABASE_URL` - Database URL, just file name if using sqlite
1. Setup the environment using the `Pipfile`
1. Start the bot with `pipenv run bot`
