import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data
def load_etfs():
    return pd.read_csv("data/etfs.csv", sep=";")


@st.cache_data(show_spinner="Téléchargement des données Yahoo...")
def load_prices(etfs):

    tickers = etfs["yahoo"].dropna().tolist()

    data = yf.download(
        tickers,
        period="6y",
        auto_adjust=True,
        progress=False,
        threads=False
    )

    prices = data["Close"]
    prices = prices.dropna(axis=0, how="all")

    # on remplace les tickers Yahoo par les codes du père
    mapping = dict(zip(etfs["yahoo"], etfs["code"]))

    prices = prices.rename(columns=mapping)

    return prices