import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "database.sqlite"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "matches_with_league.csv"

def extract_matches():
    if not DB_PATH.exists():
        raise FileNotFoundError(f" Base introuvable : {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            m.season,
            l.name AS league_name,
            c.name AS country_name,
            th.team_long_name AS home_team,
            ta.team_long_name AS away_team,
            m.home_team_goal AS home_score,
            m.away_team_goal AS away_score
        FROM Match AS m
        LEFT JOIN League AS l ON m.league_id = l.id
        LEFT JOIN Country AS c ON l.country_id = c.id
        LEFT JOIN Team AS th ON m.home_team_api_id = th.team_api_id
        LEFT JOIN Team AS ta ON m.away_team_api_id = ta.team_api_id
        WHERE m.season IS NOT NULL;
    """
    df = pd.read_sql_query(query, conn)
    # Basic cleanup: drop rows with missing team names
    original_len = len(df)
    df = df.dropna(subset=["home_team", "away_team"]).reset_index(drop=True)
    print(f"ℹ️  Lignes sans nom d'équipe ignorées : {original_len - len(df)}")
    conn.close()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ {len(df)} matchs exportés vers {OUTPUT_PATH}")

if __name__ == "__main__":
    extract_matches()