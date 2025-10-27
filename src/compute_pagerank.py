import networkx as nx
import pandas as pd
from build_graph import build_graph
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data"

if __name__ == "__main__":
    graph_data = build_graph()
    G = graph_data["graph"]
    print(f" Graphe chargé : {graph_data['nodes']} équipes, {graph_data['edges']} matchs\n")

    print(" Calcul du PageRank en cours...")
    pagerank_scores = nx.pagerank(G, alpha=0.85)
    df = pd.DataFrame(pagerank_scores.items(), columns=["team", "pagerank"])
    df = df.sort_values("pagerank", ascending=False)

    out_path = OUT / "team_pagerank.csv"
    df.to_csv(out_path, index=False)

    print(f" Résultats sauvegardés → {out_path}")
    print("\n🏆 Top 10 équipes selon le PageRank :\n")
    print(df.head(10).to_string(index=False))