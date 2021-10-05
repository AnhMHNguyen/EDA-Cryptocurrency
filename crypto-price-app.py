import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from bs4 import BeautifulSoup
import json
import requests
from PIL import Image
import base64

st.set_page_config(layout="wide")

image = Image.open("logo.jpg")
st.image(image, width=500)
st.title("Crypto Price App")
st.markdown("""
This app retrieves cryptocurrency prices for top 100 cryptocurrency from CoinMarketCap
* **Python libraries:** base64, pandas, streamlit, numpy, matplotlib, seaborn, BeautifulSoup, requests, json, time
* **Data source:** [CoinMarketCap](http://coinmarketcap.com).
* **Credit:** Web scraper adapted from the Medium article *[Web Scraping Crypto Prices With Python](https://towardsdatascience.com/web-scraping-crypto-prices-with-python-41072ea5b5bf)* written by [Bryan Feng](https://medium.com/@bryanf).
""")
st.write("""
***
""")
col2, col3 = st.beta_columns((2,1))

@st.cache
def load_data(currency):
    url = "https://coinmarketcap.com/"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    data = soup.find('script', id='__NEXT_DATA__', type='application/json')
    data = json.loads(data.contents[0])
    listings = data['props']['initialState']['cryptocurrency']['listingLatest']['data']
    # coins = {}
    # for i in listings:
    #     coins[str(i['id'])] = i['slug']
    coin_name = []
    coin_symbol = []
    market_cap = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    price = []
    volume_24h = []
    if currency == "USD":
        pos = 2
    elif currency == "BTC":
        pos = 0
    else:
        pos = 1
    for i in listings:
        coin_name.append(i["name"])
        coin_symbol.append(i["symbol"])
        market_cap.append(i["quotes"][pos]["marketCap"])
        percent_change_1h.append(i["quotes"][pos]["percentChange1h"])
        percent_change_7d.append(i["quotes"][pos]["percentChange7d"])
        percent_change_24h.append(i["quotes"][pos]["percentChange24h"])
        price.append(i["quotes"][pos]["price"])
        volume_24h.append(i["quotes"][pos]["volume24h"])

    df = pd.DataFrame(columns=['Name', 'Symbol', 'Market Cap', '1h %', '24h %', '7d %', 'Price', 'Volume (24h)'])
    df['Name'] = coin_name
    df['Symbol'] = coin_symbol
    df['Market Cap'] = market_cap
    df['1h %'] = percent_change_1h
    df['24h %'] = percent_change_24h
    df['7d %'] = percent_change_7d
    df['Price'] = price
    df['Volume (24h)'] = volume_24h
    return df

selected_currency = st.sidebar.selectbox("Select currency for price", options=["USD", "BTC", "ETH"])
df = load_data(selected_currency)

sort_coin = sorted(df["Symbol"])
selected_symbol = st.sidebar.multiselect("Cryptocurrency", options=sort_coin, default=sort_coin)
df_selected_crypto = df[df["Symbol"].isin(selected_symbol)]

num_coin = st.sidebar.slider('Display Top N Coins', 1, 100, 100)
df_coins = df_selected_crypto[:num_coin]

col2.subheader("Price Data of Selected Cryptocurrency")
col2.write("Data Dimension: "+str(len(df_coins))+" rows and "+str(len(df_coins.columns))+" columns.")
col2.dataframe(df_coins)

def download_file(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f"<a href='data:file/csv;base64,{b64}' download='crypto.csv'>Download CSV</a>"
    return href
col2.markdown(download_file(df_selected_crypto), unsafe_allow_html=True)

col2.subheader("Table of % Price Change")
df_percent_change = df_coins.drop(["Name", "Market Cap", "Price", "Volume (24h)"], axis=1)
df_percent_change.set_index("Symbol", inplace=True)
df_percent_change["positive_percent_change_1h"] = df_percent_change["1h %"] > 0
df_percent_change["positive_percent_change_24h"] = df_percent_change["24h %"] > 0
df_percent_change["positive_percent_change_7d"] = df_percent_change["7d %"] > 0

col2.dataframe(df_percent_change)

selected_time_frame = st.sidebar.selectbox("Percent change time frame", options=["1h", "24h", "7d"])

def show_plot(symbol, percent_change, positive_percent_change):
    fig, ax = plt.subplots(figsize=(5,20))
    ax.barh(list(symbol),
            list(percent_change),
            color=positive_percent_change.map({True:'green', False:'red'}))
    # ax.set_ylim(int(symbol[0]), int(symbol[-1]), auto=True)
    fig.subplots_adjust(top=1, bottom=0)
    return fig
col3.subheader('Bar plot of % Price Change')
if selected_time_frame == "1h":
    col3.write('*1 hour period*')
    df_percent_change = df_percent_change.sort_values(by=["1h %"])
    col3.pyplot(show_plot(df_percent_change.index, df_percent_change["1h %"], df_percent_change["positive_percent_change_1h"]))
elif selected_time_frame == "24h":
    col3.write('*24 hours period*')
    df_percent_change = df_percent_change.sort_values(by=["24h %"])
    col3.pyplot(show_plot(df_percent_change.index, df_percent_change["24h %"], df_percent_change["positive_percent_change_24h"]))
else:
    col3.write('*7 days period*')
    df_percent_change = df_percent_change.sort_values(by=["7d %"])
    col3.pyplot(show_plot(df_percent_change.index, df_percent_change["7d %"], df_percent_change["positive_percent_change_7d"]))
