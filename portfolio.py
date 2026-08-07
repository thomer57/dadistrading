import numpy as np
import pandas as pd

from momentum import Momentum
from ranking import ranking


def load_portfolio():
    return pd.read_csv("data/portfolio.csv", sep=";")


def get_reference_price(series, target_date):
    history = series.loc[:target_date].dropna()

    if history.empty:
        return np.nan

    return history.iloc[-1]


def compute_portfolio_targets(
    ranking_table,
    prices_df,
    portfolio_df,
    start_date,
    current_date,
    c=1.5,
    min_trade=300
):
    df = ranking_table.copy()

    portfolio_map = portfolio_df.set_index("code")["montant_07_11"].to_dict()
    df["montant_07_11"] = df["code"].map(portfolio_map)

    current_values = []

    for code in df["code"]:
        if code not in prices_df.columns:
            current_values.append(np.nan)
            continue

        series = prices_df[code].dropna()

        p0 = get_reference_price(series, start_date)
        pt = get_reference_price(series, current_date)

        initial_amount = portfolio_map.get(code, np.nan)

        if pd.isna(initial_amount) or pd.isna(p0) or pd.isna(pt) or p0 == 0:
            current_values.append(np.nan)
        else:
            current_values.append(initial_amount * pt / p0)

    df["Valeur actuelle"] = current_values

    total_portfolio = df["Valeur actuelle"].sum()
    nb_supports = df["code"].nunique()
    pim = total_portfolio / nb_supports if nb_supports > 0 else np.nan

    def target_value(row):
        if row["Type"] == "Champion":
            return pim * c
        elif row["Type"] == "Boulet":
            return pim / c
        return pim

    df["PII"] = df.apply(target_value, axis=1)
    df["Ecart PII"] = df["PII"] - df["Valeur actuelle"]

    def build_recommendation(row):
        ecart = row["Ecart PII"]
        support_type = row["Type"]

        if pd.isna(ecart):
            return "Donnée manquante", "Impossible de calculer la cible"

        # ===== CHAMPION =====
        if support_type == "Champion":
            if ecart > min_trade:
                return "Renforcer", f"Champion sous la cible de {ecart:,.0f} €".replace(",", " ")
            else:
                if ecart < 0:
                    return "Conserver", f"Champion déjà au-dessus de sa cible ({abs(ecart):,.0f} €)".replace(",", " ")
                else:
                    return "Conserver", f"Écart limité avec la cible ({ecart:,.0f} €)".replace(",", " ")

        # ===== VENTRE MOU =====
        if support_type == "Ventre mou":
            if ecart > min_trade:
                return "Renforcer", f"Position sous la cible de {ecart:,.0f} €".replace(",", " ")
            elif ecart < -min_trade:
                return "Alléger", f"Position au-dessus de la cible de {abs(ecart):,.0f} €".replace(",", " ")
            else:
                return "Conserver", f"Écart limité avec la cible ({ecart:,.0f} €)".replace(",", " ")

        # ===== BOULET =====
        if support_type == "Boulet":
            if ecart < -min_trade:
                return "Alléger", f"Boulet au-dessus de la cible de {abs(ecart):,.0f} €".replace(",", " ")
            elif ecart > 0:
                return "Conserver", f"On ne renforce pas un boulet (manque {ecart:,.0f} € vs cible)".replace(",", " ")
            else:
                return "Conserver", f"Écart limité avec la cible ({ecart:,.0f} €)".replace(",", " ")

        return "Conserver", "Aucune action"

    recommendations = df.apply(build_recommendation, axis=1)
    df["Recommandation"] = recommendations.apply(lambda x: x[0])
    df["Pourquoi"] = recommendations.apply(lambda x: x[1])

    return df, total_portfolio, pim


