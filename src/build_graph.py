"""
====================================================
 Module : build_graph.py
 Auteur : Mevlut Cakin
 Description : Construction d'un graphe orienté de football à partir des résultats.
 Chaque nœud représente une équipe, chaque arête une confrontation pondérée.
====================================================
"""
import pandas as pd
import networkx as nx
from pathlib import Path

# === Configuration du chemin vers les données ===
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

def build_graph():
    """
    Construit un graphe orienté à partir des résultats de matchs de football.
    Chaque équipe est un nœud, et chaque match une arête pondérée selon le résultat :
      - 1 point pour une victoire
      - 0.5 point pour un match nul
    """
    csv_path = DATA_DIR / "matches.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f" Fichier introuvable : {csv_path}")
    df = pd.read_csv(csv_path)

    G = nx.DiGraph()

    for _, row in df.iterrows():
        home = row["home_team"]
        away = row["away_team"]
        home_goals = row["home_team_goal"]
        away_goals = row["away_team_goal"]

        # On ignore les lignes invalides
        if pd.isna(home) or pd.isna(away):
            continue

        # Victoire / défaite / match nul
        if home_goals > away_goals:
            G.add_edge(home, away, weight=1)
        elif away_goals > home_goals:
            G.add_edge(away, home, weight=1)
        else:
            G.add_edge(home, away, weight=0.5)
            G.add_edge(away, home, weight=0.5)

    print(" Graphe de football construit avec succès !")
    print(f"  {G.number_of_nodes()} équipes")
    print(f"  {G.number_of_edges()} confrontations enregistrées\n")

    return {
        "graph": G,
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges()
    }

if __name__ == "__main__":
    build_graph()