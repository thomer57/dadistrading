import numpy as np
import pandas as pd


class Momentum:
    def _get_reference_price(self, series, target_date):
        """
        Retourne le dernier prix disponible à target_date ou avant.
        """
        history = series.loc[:target_date].dropna()

        if history.empty:
            return np.nan

        return history.iloc[-1]

    def compute(self, prices, date):
        """
        Calcule les performances calendaires :
        - 1W = date - 7 jours
        - 1M = date - 1 mois
        - 3M = date - 3 mois
        - 6M = date - 6 mois
        - 1Y = date - 1 an

        En prenant à chaque fois la dernière clôture disponible
        à la date cible ou avant.
        """

        history = prices.loc[:date].copy()

        if history.empty:
            raise ValueError("Aucune donnée disponible jusqu'à cette date.")

        effective_date = history.index[-1]

        horizons = {
            "1W": effective_date - pd.Timedelta(days=7),
            "1M": effective_date - pd.DateOffset(months=1),
            "3M": effective_date - pd.DateOffset(months=3),
            "6M": effective_date - pd.DateOffset(months=6),
            "1Y": effective_date - pd.DateOffset(years=1),
        }

        df = pd.DataFrame(index=prices.columns)

        last_prices = history.iloc[-1]

        for code in prices.columns:
            series = prices[code].dropna()

            current_price = self._get_reference_price(series, effective_date)

            for label, ref_date in horizons.items():
                reference_price = self._get_reference_price(series, ref_date)

                if pd.isna(current_price) or pd.isna(reference_price) or reference_price == 0:
                    df.loc[code, label] = np.nan
                else:
                    df.loc[code, label] = current_price / reference_price - 1

        # ---------- M ----------
        df["MCT"] = (
            0.40 * df["1W"]
            + 0.35 * df["1M"]
            + 0.25 * df["3M"]
        )

        df["MMT"] = (
            0.20 * df["1M"]
            + 0.40 * df["3M"]
            + 0.40 * df["6M"]
        )

        df["Momentum"] = (df["MCT"] + df["MMT"]) / 2

        # ---------- Mbis ----------
        df["1WN"] = (1 + df["1W"]) ** 52 - 1
        df["1MN"] = (1 + df["1M"]) ** 12 - 1
        df["3MN"] = (1 + df["3M"]) ** 4 - 1
        df["6MN"] = (1 + df["6M"]) ** 2 - 1
        df["1YN"] = df["1Y"]

        df["MCTbis"] = (
            0.40 * df["1WN"]
            + 0.35 * df["1MN"]
            + 0.25 * df["3MN"]
        )

        df["MMTbis"] = (
            0.20 * df["1MN"]
            + 0.40 * df["3MN"]
            + 0.40 * df["6MN"]
        )

        df["Mbis"] = (df["MCTbis"] + df["MMTbis"]) / 2

        df["date_calcul"] = effective_date

        return df