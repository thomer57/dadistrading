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

    # Fallback : si un ticker est vide dans le batch, on le recharge seul
    for ticker in tickers:
        if ticker not in prices.columns or prices[ticker].dropna().empty:
            single = yf.download(
                ticker,
                period="6y",
                auto_adjust=True,
                progress=False,
                threads=False
            )

            if not single.empty and "Close" in single.columns:
                prices[ticker] = single["Close"]

    mapping = dict(zip(etfs["yahoo"], etfs["code"]))
    prices = prices.rename(columns=mapping)

    return prices