def ranking(scores, n=3, final_column="Momentum"):

    df = scores.copy()
    df = df.sort_values(final_column, ascending=False, na_position="last")

    df["Type"] = "Ventre mou"
    df.iloc[:n, df.columns.get_loc("Type")] = "Champion"
    df.iloc[-n:, df.columns.get_loc("Type")] = "Boulet"
    df["Rang"] = range(1, len(df) + 1)

    df = df.reset_index()

    # Renomme proprement la 1re colonne en "code"
    df = df.rename(columns={df.columns[0]: "code"})

    return df