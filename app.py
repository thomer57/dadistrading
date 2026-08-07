import streamlit as st
import pandas as pd

from market import load_etfs, load_prices
from momentum import Momentum
from ranking import ranking
from portfolio import load_portfolio, compute_portfolio_targets

st.set_page_config(layout="wide")
st.title("📈 Dadistrading")


def compute_market_index(prices_df, date, window=200):
    history = prices_df.loc[:date].copy()

    if history.empty:
        return None, 0, 0

    latest_prices = history.iloc[-1]
    sma200 = history.rolling(window=window, min_periods=window).mean().iloc[-1]

    valid = latest_prices.notna() & sma200.notna()
    bullish = (latest_prices > sma200) & valid

    total_valid = valid.sum()
    bullish_count = bullish.sum()

    if total_valid == 0:
        return None, 0, 0

    market_index = bullish_count / total_valid
    return market_index, bullish_count, total_valid


# ====================== CHARGEMENT ======================
etfs = load_etfs()
prices_df = load_prices(etfs)
portfolio_df = load_portfolio()



# ====================== SIDEBAR ======================
min_date = prices_df.index[0].date()
max_date = prices_df.index[-1].date()

selected_date = st.sidebar.date_input(
    "Date",
    value=pd.to_datetime("2026-07-27").date(),
    min_value=min_date,
    max_value=max_date
)

date = pd.Timestamp(selected_date)

n = st.sidebar.slider("Top n Champions / Boulets", 1, 8, 3)

c = st.sidebar.slider(
    "Coefficient de surpondération",
    min_value=1.0,
    max_value=2.0,
    value=1.5,
    step=0.1
)

min_trade = st.sidebar.slider(
    "Seuil minimum",
    min_value=0,
    max_value=2000,
    value=300,
    step=50
)

momentum_version = st.sidebar.radio(
    "Version du Momentum",
    ["M (brute)", "Mbis (normalisée)"],
    index=0,
    horizontal=True
)

show_details = st.sidebar.checkbox("👁 Afficher les colonnes avancées", value=False)

# ====================== CALCUL MOMENTUM ======================
calc = Momentum()
scores = calc.compute(prices_df, date)

final_column = "Momentum" if momentum_version == "M (brute)" else "Mbis"

# ====================== RANKING ======================
table = ranking(scores, n=n, final_column=final_column)

# ====================== ENRICHISSEMENT ETF ======================
table = table.merge(
    etfs[["code", "nom", "zone", "risque"]],
    on="code",
    how="left"
)

# ====================== CALCUL PORTEFEUILLE ======================
start_date = pd.Timestamp("2026-07-11")

table, total_portfolio, pim = compute_portfolio_targets(
    ranking_table=table,
    prices_df=prices_df,
    portfolio_df=portfolio_df,
    start_date=start_date,
    current_date=date,
    c=c,
    min_trade=min_trade
)

# ====================== INDICE DE MARCHÉ ======================
market_index, bullish_count, total_valid_etfs = compute_market_index(prices_df, date)

# ====================== METRICS ======================
col1, col2 = st.columns(2)

with col1:
    st.metric("Valeur totale portefeuille", f"{total_portfolio:,.0f} €".replace(",", " "))

with col2:
    if market_index is not None:
        st.metric(
            "Indice de marché",
            f"{market_index * 100:.0f} %",
            help=f"{bullish_count} ETF sur {total_valid_etfs} sont au-dessus de leur moyenne mobile 200 jours."
        )
    else:
        st.metric(
            "Indice de marché",
            "N/A",
            help="Pas assez d'historique pour calculer la moyenne mobile 200 jours."
        )

# ====================== COLONNES À MASQUER PAR DÉFAUT ======================
hidden_by_default = [
    "date_calcul",
    "nom",
    "zone",
    "risque",
    "montant_07_11",
    "1W", "1M", "3M", "6M", "1Y",
    "1WN", "1MN", "3MN", "6MN", "1YN",
    "MCT", "MMT", "MCTbis", "MMTbis",
]

if show_details:
    display_table = table.copy()
else:
    display_table = table.drop(
        columns=[col for col in hidden_by_default if col in table.columns],
        errors="ignore"
    ).copy()

display_table = display_table.rename(columns={
    "PII": "Cible",
    "Ecart PII": "Ecart cible",
    "montant_07_11": "Valeur 11_07"
})

# ====================== ORDRE DES COLONNES ======================
preferred_order = [
    "Rang",
    "code",
    "Type",
    "Momentum",
    "Mbis",
    "Valeur actuelle",
    "Cible",
    "Ecart cible",
    "Pourquoi",
    "Recommandation",
    "risque",
    "Valeur 11_07",
]

ordered_cols = [col for col in preferred_order if col in display_table.columns]
remaining_cols = [col for col in display_table.columns if col not in ordered_cols]
display_table = display_table[ordered_cols + remaining_cols]

# ====================== FORMATAGE ======================
def format_pct(val):
    if pd.isna(val):
        return "–"
    return f"{val * 100:.2f}%"

def format_eur(val):
    if pd.isna(val):
        return "–"
    return f"{val:,.0f} €".replace(",", " ")

pct_columns = [
    "1W", "1M", "3M", "6M", "1Y",
    "MCT", "MMT", "Momentum",
    "1WN", "1MN", "3MN", "6MN", "1YN",
    "MCTbis", "MMTbis", "Mbis"
]

eur_columns = [
    "Valeur 11_07",
    "Valeur actuelle",
    "Cible",
    "Ecart cible"
]

for col in pct_columns:
    if col in display_table.columns:
        display_table[col] = display_table[col].apply(format_pct)

for col in eur_columns:
    if col in display_table.columns:
        display_table[col] = display_table[col].apply(format_eur)

if "date_calcul" in display_table.columns:
    display_table["date_calcul"] = pd.to_datetime(display_table["date_calcul"]).dt.strftime("%Y-%m-%d")

# ====================== COULEURS ======================
def color_type(val):
    if val == "Champion":
        return "color: #00C853; font-weight: bold"
    elif val == "Ventre mou":
        return "color: #FF9800; font-weight: bold"
    elif val == "Boulet":
        return "color: #F44336; font-weight: bold"
    return ""

def color_reco(val):
    if val == "Renforcer":
        return "color: #00C853; font-weight: bold"
    elif val == "Alléger":
        return "color: #F44336; font-weight: bold"
    elif val == "Conserver":
        return "color: #B0BEC5; font-weight: bold"
    return ""

styled_table = (
    display_table.style
    .map(color_type, subset=["Type"])
    .map(color_reco, subset=["Recommandation"])
)

# ====================== AFFICHAGE TABLEAU ======================
st.dataframe(
    styled_table,
    use_container_width=True,
    height=700,
    hide_index=True
)