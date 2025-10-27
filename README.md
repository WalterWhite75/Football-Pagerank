# Football PageRank Dashboard

## Présentation du projet
Ce projet applique l’algorithme PageRank au réseau du football européen.  
Chaque club est modélisé comme un nœud, et chaque match crée une arête dirigée du perdant vers le gagnant.  
L’objectif est de mesurer l’influence structurelle des clubs dans un graphe de matchs réels (2008–2016).

Ce tableau de bord interactif développé avec Dash et Plotly offre une visualisation moderne et professionnelle des résultats, dans une démarche à la fois pédagogique et analytique.

---

## Objectifs du projet
- Illustrer l’application d’un algorithme de graphes à un domaine concret (le sport).  
- Développer un pipeline de données complet : extraction, traitement, modélisation, visualisation.  
- Créer une interface professionnelle en Python adaptée à un usage académique ou portfolio.  
- Démontrer les compétences d’un futur data professional à travers un cas d’usage original.

---

## Architecture du projet

football-pagerank/
│
├── .gitignore                # Fichiers et dossiers ignorés par Git (ex: .venv, data lourdes, etc.)
├── README.md                 # Documentation principale du projet
├── requirements.txt          # Liste des dépendances Python
├── assets/                   # Ressources statiques (images, CSS, logos…)
│   ├── photo_mevlut.png
│   └── custom.css            # (optionnel) Styles additionnels
│
├── data/                     # Données d’entrée et de sortie
│   ├── team_pagerank_with_league.csv
│   ├── team_pagerank_yearly.csv
│   └── database.sqlite       # (non versionné — exclu via .gitignore car >100Mo)
│
├── src/                      # Code source principal
│   ├── compute_pagerank.py   # Script de calcul de l’algorithme PageRank sur les matchs
│   └── dashboard_pagerank.py # Application Dash (visualisation interactive)
│
└── .venv/                    # Environnement virtuel local (non versionné)
