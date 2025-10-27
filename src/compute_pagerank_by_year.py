import pandas as pd
import networkx as nx
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "matches_with_league.csv"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "team_pagerank_with_league.csv"

df = pd.read_csv(DATA_PATH)
print(f"{len(df)} matchs chargés depuis {DATA_PATH}")
print(f"Colonnes disponibles : {list(df.columns)}")
seasons = sorted(df["season"].unique())
results = []

for season in seasons:
    matches = df[df["season"] == season]
    G = nx.DiGraph()
    for _, row in matches.iterrows():
        if row["home_score"] > row["away_score"]:
            G.add_edge(row["home_team"], row["away_team"])
        elif row["home_score"] < row["away_score"]:
            G.add_edge(row["away_team"], row["home_team"])
    if len(G) == 0:
        continue
    pr = nx.pagerank(G, alpha=0.85)
    for team, score in pr.items():
        subset_home = matches[matches["home_team"] == team]
        subset_away = matches[matches["away_team"] == team]
        leagues = pd.concat([subset_home["league_name"], subset_away["league_name"]]).dropna().unique()
        countries = pd.concat([subset_home["country_name"], subset_away["country_name"]]).dropna().unique()
        league = leagues[0] if len(leagues) > 0 else None
        country = countries[0] if len(countries) > 0 else None
        results.append({
            "season": season,
            "team": team,
            "pagerank": score,
            "league": league,
            "country": country
        })

pd.DataFrame(results).to_csv(OUTPUT_PATH, index=False)
print(f"Fichier sauvegardé : {OUTPUT_PATH}")