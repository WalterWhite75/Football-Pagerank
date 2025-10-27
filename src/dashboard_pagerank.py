
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from pathlib import Path
import dash_bootstrap_components as dbc
import webbrowser
import numpy as np
import logging
from datetime import datetime

import io
import os

# Optional PDF dependency 
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

#  Couleurs principales 
PRIMARY_COLOR = "#1A5276"
SECONDARY_COLOR = "#1ABC9C"
BACKGROUND_COLOR = "#F4F6F7"
CARD_BG = "#FFFFFF"
TEXT_COLOR = "#2C3E50"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

#  Chargement des données 
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "team_pagerank_with_league.csv"
YEARLY_PATH = Path(__file__).resolve().parents[1] / "data" / "team_pagerank_yearly.csv"
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"

if not DATA_PATH.exists():
    print("⚠️ Le fichier 'team_pagerank.csv' est introuvable dans /data/.")
    print("👉 Exécute d'abord 'compute_pagerank.py' pour le générer.")
    exit(1)

try:
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    df.rename(columns={
        " Team": "team", " team": "team",
        "Pagerank": "pagerank", " Pagerank": "pagerank"
    }, inplace=True)
    df["team"] = df["team"].astype(str)
    df["pagerank"] = pd.to_numeric(df["pagerank"], errors="coerce")
    # Remplissage des colonnes 'league' et 'country' si elles existent
    if 'league' in df.columns:
        df['league'] = df['league'].fillna('Inconnue')
    if 'country' in df.columns:
        df['country'] = df['country'].fillna('Inconnu')
    df.dropna(subset=["pagerank"], inplace=True)
    df.sort_values("pagerank", ascending=False, inplace=True)
    print(f" Données chargées : {len(df)} équipes importées depuis {DATA_PATH}.")
except Exception as e:
    print(f" Erreur lors du chargement du fichier CSV : {e}")
    df = pd.DataFrame(columns=["team", "pagerank"])

# Chargement du CSV annuel (optionnel)
if YEARLY_PATH.exists():
    try:
        df_yearly = pd.read_csv(YEARLY_PATH)
        df_yearly.columns = df_yearly.columns.str.strip()
        df_yearly.rename(columns={
            " Team": "team", " team": "team",
            "Pagerank": "pagerank", " Pagerank": "pagerank",
            "Saison": "season", " Saison": "season", "season": "season"
        }, inplace=True)
        df_yearly["team"] = df_yearly["team"].astype(str)
        df_yearly["pagerank"] = pd.to_numeric(df_yearly["pagerank"], errors="coerce")
        df_yearly["season"] = df_yearly["season"].astype(str)
        df_yearly.dropna(subset=["pagerank", "team", "season"], inplace=True)
        logging.info(f"➡️ Données annuelles chargées : {len(df_yearly)} lignes depuis {YEARLY_PATH}")
    except Exception as e:
        logging.warning(f"Impossible de lire {YEARLY_PATH}: {e}")
        df_yearly = pd.DataFrame(columns=["team", "season", "pagerank"])    
else:
    logging.info("(optionnel) Fichier annuel introuvable : section 'Évolution' masquée tant qu'il n'est pas généré.")
    df_yearly = pd.DataFrame(columns=["team", "season", "pagerank"])    

#  Application Dash 
app = dash.Dash(
    __name__,
    assets_folder=str(ASSETS_DIR),
    assets_url_path="/assets",
    external_stylesheets=[dbc.themes.MINTY, "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap"],
    suppress_callback_exceptions=True,
)
# (Backup toggle in case the runtime changes)
app.config.suppress_callback_exceptions = True
app.title = "Football PageRank"

#  KPIs dynamiques 
def get_kpis():
    total_teams = len(df)
    top_team = df.iloc[0]["team"] if not df.empty else "N/A"
    avg_rank = df["pagerank"].mean() if not df.empty else 0
    most_common_country = df['country'].mode()[0] if 'country' in df.columns and not df.empty else 'N/A'
    return total_teams, top_team, avg_rank, most_common_country

total_teams, top_team, avg_rank, most_common_country = get_kpis()

is_night = False
# Initialize switch default
app._force_default_theme_dark = False

# Composants KPI 
def kpi_card(title, value, color, icon):
    icon_span = html.Span(icon, className=f"text-{color}", style={"fontSize": "38px", "marginRight": "12px"}) if icon else None
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                icon_span,
                html.Span(title, className="card-title text-muted fw-bold")
            ], className="d-flex align-items-center justify-content-center"),
            html.H2(value, className=f"text-{color} mt-3", style={"fontWeight": "bold", "fontSize": "2.2rem"})
        ])
    ], className="glass-card text-center mb-4",
       style={
           "background": "linear-gradient(180deg, #FFFFFF 0%, #F8FBFC 100%)",
           "borderRadius": "10px",
           "boxShadow": "0 4px 15px rgba(0,0,0,0.08)",
           "border": f"1px solid {PRIMARY_COLOR}20"
       })

# Utilities: build a 1‑page project summary 

def build_summary_pdf_bytes():
    """Return bytes for a 1‑page PDF summary of the project.
    Requires reportlab; if unavailable, raise RuntimeError to trigger fallback.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab not installed")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFillColor(colors.HexColor("#1A5276"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2*cm, height - 2.2*cm, "Football PageRank — Résumé projet")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 3.0*cm, f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Separator line
    c.setStrokeColor(colors.HexColor("#1ABC9C"))
    c.setLineWidth(2)
    c.line(2*cm, height - 3.3*cm, width - 2*cm, height - 3.3*cm)

    # Body
    text = c.beginText(2*cm, height - 4.2*cm)
    text.setFont("Helvetica", 11)
    lines = [
        "Objectif : appliquer PageRank au graphe des matchs européens (2008–2016)",
        "pour estimer l'influence structurelle des clubs (modèle perdant → gagnant).",
        "",
        f"Équipes totales : {len(df):,}",
        f"Meilleur club (PageRank max) : {df.iloc[0]['team'] if not df.empty else 'N/A'}",
        f"Score moyen de PageRank : {df['pagerank'].mean():.6f}",
        (f"Pays le plus représenté : {df['country'].mode()[0]}" if 'country' in df.columns and not df.empty else ""),
        "",
        "Méthodologie :",
        "  • Graphe dirigé; arête du perdant vers le gagnant (nuls bidirectionnels)",
        "  • Algorithmie : NetworkX PageRank (α = 0.85)",
        "  • Visualisation : Dash, Plotly, Bootstrap",
        "",
        "Interprétation : les scores reflètent la centralité/influence réseau,",
        "pas un classement sportif officiel.",
    ]
    for line in lines:
        text.textLine(line)
    c.drawText(text)

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.HexColor("#1A5276"))
    c.drawRightString(width - 2*cm, 1.8*cm, "© 2025 – Mevlut Cakin, M2 BIDABI")

    c.showPage()
    c.save()
    data = buffer.getvalue()
    buffer.close()
    return data


def build_summary_txt_bytes():
    """Fallback plain‑text summary when ReportLab is not installed."""
    content = (
        "Football PageRank — Résumé projet\n"
        f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        "Objectif : appliquer PageRank au graphe des matchs européens (2008–2016)\n"
        "pour estimer l'influence structurelle des clubs (modèle perdant → gagnant).\n\n"
        f"Équipes totales : {len(df):,}\n"
        f"Meilleur club (PageRank max) : {df.iloc[0]['team'] if not df.empty else 'N/A'}\n"
        f"Score moyen de PageRank : {df['pagerank'].mean():.6f}\n"
        + (f"Pays le plus représenté : {df['country'].mode()[0]}\n" if 'country' in df.columns and not df.empty else "") +
        "\nMéthodologie :\n"
        "  • Graphe dirigé; arête du perdant vers le gagnant (nuls bidirectionnels)\n"
        "  • Algorithmie : NetworkX PageRank (α = 0.85)\n"
        "  • Visualisation : Dash, Plotly, Bootstrap\n\n"
        "Interprétation : les scores reflètent la centralité/influence réseau,\n"
        "pas un classement sportif officiel.\n\n"
        "© 2025 – Mevlut Cakin, M2 BIDABI\n"
    )
    return content.encode("utf-8")

# Helper pour générer la figure comparative Ligue / Pays (simplifiée et corrigée) 
def build_compare_figures(dim="country", is_dark=False):
    import plotly.express as px

    # Nettoyage et uniformisation
    d = df.copy()
    d.columns = d.columns.str.strip().str.lower()
    for col in ["league", "country"]:
        if col in d.columns:
            d[col] = d[col].fillna("Inconnu").astype(str).str.strip()

    # Validation
    if dim not in d.columns:
        fig = px.bar(title=f"⚠️ Colonne '{dim}' absente.")
        # Force light theme
        fig.update_layout(template="plotly_white", plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", font=dict(color="#2C3E50"))
        return fig

    # Force theme to light mode and pastel colors
    template = "plotly_white"
    bg = "#FFFFFF"
    font_color = "#2C3E50"
    palette = px.colors.qualitative.Pastel2

    label = "Ligue" if dim == "league" else "Pays"

    # Agrégation : somme du PageRank + effectif, filtre par effectif minimal
    grp = (
        d.groupby(dim, as_index=False)
         .agg(pagerank=("pagerank", "sum"), n=("team", "count"))
    )
    min_count = 5 if dim == "country" else 8
    grp = grp[grp["n"] >= min_count]

    if grp.empty:
        fig = px.bar(title=f"Aucune donnée suffisante par {label} (n≥{min_count}).")
        fig.update_layout(template=template, plot_bgcolor=bg, paper_bgcolor=bg, font=dict(color=font_color))
        return fig

    # Mise à l'échelle pour rendre les différences visibles (ppm)
    grp = grp.sort_values("pagerank", ascending=False).head(15)
    grp["pagerank_ppm"] = grp["pagerank"] * 1_000_000  # parties par million
    # Format label: round to 0 decimals, thousands separator (space)
    grp["pagerank_ppm_label"] = grp["pagerank_ppm"].map(lambda x: f"{x:,.0f}".replace(",", " "))
    grp["pagerank_label"] = grp["pagerank"].map(lambda x: f"{x:.6f}")

    fig = px.bar(
        grp,
        x=dim,
        y="pagerank_ppm",
        color=dim,
        title=f"Influence totale (somme des scores PageRank) par {label} (Top 15)",
        labels={dim: label, "pagerank_ppm": "Somme du PageRank (ppm)"},
        text="pagerank_ppm_label",
        color_discrete_sequence=palette,
    )

    # Label propre : entier en ppm + hover détaillé
    fig.update_traces(
        texttemplate="%{text}",
        textposition="outside",
        marker_line_color="#E5E8E8",
        marker_line_width=1.2,
        hovertemplate=f"{label}: %{{x}}<br>PageRank moyen: %{{customdata[0]}}<br>Clubs pris en compte: %{{customdata[1]}}<extra></extra>",
        customdata=np.stack([grp["pagerank_label"], grp["n"]], axis=-1),
    )

    # Mise en forme esthétique
    ymax = float(grp["pagerank_ppm"].max()) * 1.10
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#2C3E50", size=15),
        title_x=0.5,
        height=550,
        margin=dict(l=60, r=40, t=80, b=120),
        xaxis_tickangle=-25,
        showlegend=False,
        yaxis=dict(range=[0, ymax]),
        hoverlabel=dict(bgcolor="#F9FAFB", font_size=13, font_color="#1A5276"),
    )
    fig.update_layout(title_font=dict(size=20, color="#1A5276", family="Lato, sans-serif"))

    return fig

# Figures initiales (pour éviter les graphes vides)
_initial_box = build_compare_figures(dim="country", is_dark=bool(app._force_default_theme_dark))

#  Layout principal 
app.layout = html.Div([
    dbc.Container([
        dcc.Tabs(
            id="tabs",
            value="main-tab",
            children=[
                dcc.Tab(
                    label="Accueil",
                    value="home-tab",
                    children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.Img(
                                            src=app.get_asset_url("photo_mevlut.png"),
                                            alt="Photo — Mevlut Cakin",
                                            style={
                                                "height": "85px",
                                                "width": "85px",
                                                "borderRadius": "50%",
                                                "objectFit": "cover",
                                                "marginRight": "18px",
                                                "boxShadow": "0 4px 10px rgba(0,0,0,0.25)",
                                                "transition": "transform 0.3s ease, box-shadow 0.3s ease"
                                            },
                                            id="photo-pro"
                                        ),
                                        html.Div([
                                            html.H2(
                                                "Football PageRank — Projet M2 BIDABI",
                                                style={
                                                    "color": "#1A5276",
                                                    "fontWeight": "700",
                                                    "marginBottom": "4px"
                                                }
                                            ),
                                            html.P(
                                                "Réalisé par Mevlut Cakin — Master 2 Big Data & Business Intelligence",
                                                style={
                                                    "color": "#2C3E50",
                                                    "fontSize": "15px",
                                                    "marginTop": "0px"
                                                }
                                            )
                                        ])
                                    ], style={"display": "flex", "alignItems": "center"})
                                ], md=12)
                            ], className="mb-4"),

                            dbc.Card([
                                dbc.CardBody([
                                    html.H4("Résumé du projet", className="mb-2", style={"color": "#1A5276"}),
                                    html.P(
                                        "Ce projet applique l’algorithme PageRank au graphe des matchs européens (2008–2016) pour évaluer l’influence structurelle des clubs. "
                                        "Il démontre une démarche de data science complète : extraction SQLite, modélisation réseau, calculs analytiques et dashboard professionnel.",
                                        className="text-body"
                                    ),
                                    html.Ul([
                                        html.Li("Dataset : European Soccer Database (Kaggle)"),
                                        html.Li("Modèle : graphe orienté perdant → gagnant, nuls bidirectionnels"),
                                        html.Li("Algorithme : PageRank (α = 0.85) via NetworkX"),
                                        html.Li("Livrable : tableau de bord interactif (Dash)"),
                                    ], className="mb-0")
                                ])
                            ], className="glass-card mb-4"),

                            dbc.Row([
                                dbc.Col(dbc.Card([
                                    dbc.CardBody([
                                        html.H5("Pourquoi c’est intéressant ?", style={"color": "#1A5276"}),
                                        html.P(
                                            "Le PageRank mesure l’influence par la connectivité : battre un club central compte davantage. "
                                            "On obtient une lecture structurelle complémentaire aux classements sportifs.",
                                            className="mb-0"
                                        )
                                    ])
                                ], className="glass-card h-100"), md=6),
                                dbc.Col(dbc.Card([
                                    dbc.CardBody([
                                        html.H5("À propos", style={"color": "#1A5276"}),
                                        html.P(
                                            "Projet réalisé par Mevlut Cakin — Master 2 Big Data & Business Intelligence, Université Sorbonne Paris‑Nord (2025).",
                                            className="mb-0"
                                        )
                                    ])
                                ], className="glass-card h-100"), md=6),
                            ], className="mb-4 g-3"),

                            dbc.Alert(
                                [
                                    html.Span("Téléchargez un résumé PDF d’une page pour votre rendu.", className="me-3"),
                                    dbc.Button("Télécharger le rapport PDF", id="btn-download-summary", color="secondary", n_clicks=0),
                                    dcc.Download(id="download-summary")
                                ],
                                color="info",
                                className="shadow-sm text-dark",
                                style={"backgroundColor": "#E8F6F3", "borderLeft": "6px solid #1ABC9C"}
                            ),
                        ], style={"maxWidth": "980px", "margin": "0 auto", "padding": "20px 10px"})
                    ]
                ),
                dcc.Tab(
                    label="Dashboard principal",
                    value="main-tab",
                    children=[
                        dbc.Navbar(
                            dbc.Container([
                                html.Div("Football PageRank Dashboard", className="navbar-brand fw-bold"),
                                dbc.Switch(id="theme-switch", label="Mode sombre", value=bool(app._force_default_theme_dark), className="text-light")
                            ]),
                            color="primary",
                            dark=True,
                            className="mb-4 shadow-sm",
                            style={"backgroundColor": "#1A5276", "borderRadius": "6px"},
                        ),

                        dcc.Store(id="theme-store", data="light"),

                        dbc.Alert(
                            [
                                html.H4("Analyse du réseau de football européen via l’algorithme PageRank", className="fw-bold text-center"),
                                html.P("Ce tableau de bord met en évidence les clubs les plus influents du football européen selon un modèle de graphes et d’analyse de connectivité.", className="text-center mb-0")
                            ],
                            color="info",
                            className="shadow-sm text-dark fade-in mb-4",
                            style={"backgroundColor": "#E8F6F3", "borderLeft": "6px solid #1ABC9C"}
                        ),

                        dbc.Row([
                            dbc.Col(kpi_card("Nombre total d’équipes", f"{total_teams:,}", "info", ""), md=3),
                            dbc.Col(kpi_card("Meilleur club (PageRank max)", top_team, "success", ""), md=3),
                            dbc.Col(kpi_card("Score moyen de PageRank", f"{avg_rank:.6f}", "warning", ""), md=3),
                            dbc.Col(kpi_card("Pays le plus représenté", most_common_country, "primary", ""), md=3),
                        ], className="text-center mt-2 mb-4 fade-in"),

                        html.Hr(style={"borderColor": "#4B8BBE"}),

                        # Ligne informations sélection + storytelling
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H5("Équipe sélectionnée", className="card-title text-muted"),
                                        html.Div(id="selection-info", className="text-body"),
                                    ])
                                ], className="glass-card")
                            ], md=6),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H5("Storytelling automatique", className="card-title text-muted"),
                                        html.Div(id="story-box", className="text-body")
                                    ])
                                ], className="glass-card")
                            ], md=6),
                        ], className="mb-3 fade-in"),

                        dbc.Row([
                            dbc.Col([
                                html.H4("Sélectionner le Top N à afficher", className="mb-3 text-primary fw-bold"),
                                dcc.Slider(
                                    id="top-n-slider",
                                    min=5, max=min(30, len(df)), step=1, value=min(15, len(df)),
                                    marks={i: f"Top {i}" for i in range(5, min(31, len(df)+1), 5)},
                                    tooltip={"placement": "bottom"}
                                ),
                                html.Div(
                                    [
                                        html.Span("Ordre de tri : ", className="text-body me-2 fw-bold"),
                                        dbc.RadioItems(
                                            id="sort-order",
                                            options=[
                                                {"label": "Descendant (Top en premier)", "value": "desc"},
                                                {"label": "Ascendant (Bas en premier)", "value": "asc"},
                                            ],
                                            value="desc",
                                            inline=True,
                                            className="ms-2"
                                        ),
                                    ], className="mb-3"
                                ),
                                dbc.Button("Télécharger le classement", id="download-btn", color="secondary", className="mb-3"),
                                dcc.Download(id="download-dataframe-csv"),
                                dcc.Loading(type="circle", children=dcc.Graph(id="pagerank-graph", style={"height": "650px"}, clear_on_unhover=True)),

                                html.Hr(style={"borderColor": "#4B8BBE"}),

                                dbc.Row([
                                    dbc.Col([
                                        html.H4("Répartition d’influence : Top 3 vs Reste", className="text-primary mt-2 mb-3"),
                                        dcc.Loading(type="circle", children=dcc.Graph(id="top3-pie", style={"height": "420px"}))
                                    ], md=6),
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.H5("Insights automatiques", className="card-title text-muted"),
                                                html.P(id="insights-text", className="text-body")
                                            ])
                                        ], className="glass-card")
                                    ], md=6)
                                ], className="mb-4"),

                                dbc.Row([
                                    dbc.Col([
                                        html.H4("Analyse de la distribution des scores PageRank", className="text-primary mt-4 mb-3"),
                                        dcc.Loading(type="circle", children=dcc.Graph(id="distribution-graph", style={"height": "450px"}))
                                    ], md=8),

                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.H5("Indice de compétitivité", className="card-title text-muted"),
                                                html.H2(id="competitivity-index", className="text-success", style={"fontWeight": "bold"}),
                                                html.Hr(),
                                                html.H5("Indice de diversité (Shannon)", className="card-title text-muted mt-2"),
                                                html.H2(id="shannon-index", className="text-info", style={"fontWeight": "bold"}),
                                                html.P(id="competitivity-comment", className="text-body mt-3")
                                            ])
                                        ], className="glass-card")
                                    ], md=4)
                                ], className="mb-4"),
                            ], width=12)
                        ], className="fade-in"),

                        # === Section évolution PageRank par club === (affichée uniquement si données annuelles disponibles)
                        (
                            html.Div([
                                html.Hr(),
                                html.H4("Évolution du PageRank d’un club par saison", className="text-primary mt-4 mb-3"),
                                dbc.Alert(
                                    [
                                        html.P(
                                            "Chaque saison, l’algorithme PageRank est recalculé sur un graphe où chaque match crée un lien du perdant vers le gagnant. "
                                            "Les clubs accumulent de l’influence selon la qualité de leurs adversaires et la densité de leurs connexions dans le réseau.",
                                            className="mb-0"
                                        )
                                    ],
                                    color="info",
                                    className="shadow-sm mb-3 text-dark",
                                    style={
                                        "backgroundColor": "#E8F8F5",
                                        "borderLeft": "6px solid #1ABC9C",
                                        "fontSize": "15px"
                                    }
                                ),
                                dbc.Row([
                                    dbc.Col([
                                        dcc.Dropdown(
                                            id="club-selector",
                                            options=[{"label": club, "value": club} for club in sorted(df_yearly["team"].unique())],
                                            value=sorted(df_yearly["team"].unique())[0] if not df_yearly.empty else None,
                                            placeholder="Sélectionner un club",
                                            clearable=False,
                                            className="mb-3"
                                        ),
                                    ], md=4),
                                    dbc.Col([
                                        dcc.Loading(
                                            type="circle",
                                            children=dcc.Graph(id="evolution-graph", style={"height": "400px"})
                                        )
                                    ], md=8)
                                ])
                            ], className="glass-card mb-4 fade-in")
                        if not df_yearly.empty else None
                        ),

                        html.Footer(
                            [
                                html.Hr(),
                                html.P("Projet universitaire - Master BIDABI | Visualisation et Analyse de Données Réelles", className="text-center text-muted mt-2"),
                                html.P("© 2025 - Tableau de bord Football PageRank | Réalisé par Mevlut Cakin",
                                       className="text-center text-body"),
                                html.P("Source : Données Kaggle - Football Graph Network", className="text-center text-muted mb-2"),
                            ],
                            style={"backgroundColor": "#F9FAFB", "padding": "10px", "borderRadius": "6px"}
                        )
                    ]
                ),
                dcc.Tab(
                    label="Comparaison Ligue/Pays",
                    value="compare-tab",
                    children=[
                        html.Div([
                            html.Hr(),
                            html.H4("Influence totale du PageRank par Pays (Top 15)", className="text-primary mt-4 mb-3"),
                            dcc.Loading(type="circle",
                                        children=dcc.Graph(id="compare-boxplot", figure=_initial_box, style={"height": "500px"})),
                        ], className="mb-5 fade-in", style={"backgroundColor": "#FAFAFA", "padding": "20px", "borderRadius": "10px"}),
                        html.Footer(
                            [
                                html.Hr(),
                                html.P("Projet universitaire - Master BIDABI | Visualisation et Analyse de Données Réelles", className="text-center text-muted mt-2"),
                                html.P("© 2025 - Tableau de bord Football PageRank | Réalisé par Mevlut Cakin",
                                       className="text-center text-body"),
                                html.P("Source : Données Kaggle - Football Graph Network", className="text-center text-muted mb-2"),
                            ],
                            style={"backgroundColor": "#F9FAFB", "padding": "10px", "borderRadius": "6px"}
                        )
                    ]
                ),
                dcc.Tab(
                    label="Contexte & Interprétation",
                    value="context-tab",
                    children=[
                        html.Div([
                            html.Div([
                                html.H2("Contexte & Interprétation", style={
                                    "color": "#1A5276",
                                    "fontWeight": "bold",
                                    "marginBottom": "18px",
                                    "marginTop": "10px",
                                    "fontSize": "2.1rem",
                                    "letterSpacing": "0.5px"
                                }),
                            ], style={"textAlign": "center", "marginBottom": "28px"}),
                            html.Div([
                                html.H4("Objectif du projet", style={
                                    "color": "#1A5276",
                                    "fontWeight": "bold",
                                    "marginBottom": "10px"
                                }),
                                html.P(
                                    "Ce projet applique l’algorithme PageRank au réseau du football européen afin d’identifier les clubs les plus influents dans un graphe de matchs. "
                                    "L’objectif est de démontrer comment une approche issue du web mining peut être utilisée dans un contexte sportif.",
                                    style={"color": "#222", "fontSize": "16px", "marginBottom": "22px", "marginTop": "2px", "lineHeight": "1.7"}
                                ),
                                html.H4("Principe du PageRank", style={
                                    "color": "#1A5276",
                                    "fontWeight": "bold",
                                    "marginTop": "20px",
                                    "marginBottom": "10px"
                                }),
                                html.P(
                                    "L’algorithme PageRank attribue à chaque club un score d’influence basé sur les victoires et la qualité des adversaires battus. "
                                    "Battre un club très influent augmente davantage le score qu’une victoire contre un club peu connecté.",
                                    style={"color": "#222", "fontSize": "16px", "marginBottom": "22px", "marginTop": "2px", "lineHeight": "1.7"}
                                ),
                                html.H4("Construction du graphe", style={
                                    "color": "#1A5276",
                                    "fontWeight": "bold",
                                    "marginTop": "20px",
                                    "marginBottom": "10px"
                                }),
                                html.P(
                                    "Chaque club est représenté par un nœud, et chaque match correspond à une arête orientée du perdant vers le gagnant. "
                                    "Les données proviennent du jeu de données European Soccer Database (Kaggle).",
                                    style={"color": "#222", "fontSize": "16px", "marginBottom": "22px", "marginTop": "2px", "lineHeight": "1.7"}
                                ),
                                html.H4("Interprétation des résultats", style={
                                    "color": "#1A5276",
                                    "fontWeight": "bold",
                                    "marginTop": "20px",
                                    "marginBottom": "10px"
                                }),
                                html.P(
                                    "Les scores PageRank ne représentent pas un classement sportif réel. Ils traduisent la position structurelle des clubs dans le graphe. "
                                    "Ainsi, certains clubs modestes peuvent apparaître en tête si leur réseau de matchs est plus dense ou mieux connecté.",
                                    style={"color": "#222", "fontSize": "16px", "marginBottom": "22px", "marginTop": "2px", "lineHeight": "1.7"}
                                ),
                                html.H4("Intérêt scientifique et pédagogique", style={
                                    "color": "#1A5276",
                                    "fontWeight": "bold",
                                    "marginTop": "20px",
                                    "marginBottom": "10px"
                                }),
                                html.P(
                                    "Le projet illustre la puissance des algorithmes de graphes pour modéliser la connectivité dans des systèmes complexes. "
                                    "Il montre comment des concepts de data science peuvent s’appliquer à des domaines variés comme le sport.",
                                    style={"color": "#222", "fontSize": "16px", "marginBottom": "22px", "marginTop": "2px", "lineHeight": "1.7"}
                                ),
                                html.H4("Perspectives d’amélioration", style={
                                    "color": "#1A5276",
                                    "fontWeight": "bold",
                                    "marginTop": "20px",
                                    "marginBottom": "10px"
                                }),
                                html.Ul([
                                    html.Li("Pondérer les matchs selon la différence de buts.", style={"color": "#222", "fontSize": "16px", "marginBottom": "7px"}),
                                    html.Li("Prendre en compte la saison ou la compétition.", style={"color": "#222", "fontSize": "16px", "marginBottom": "7px"}),
                                    html.Li("Ajouter un indicateur temporel d’évolution du PageRank.", style={"color": "#222", "fontSize": "16px", "marginBottom": "7px"}),
                                    html.Li("Enrichir le modèle avec d’autres ligues ou pays.", style={"color": "#222", "fontSize": "16px"}),
                                ], style={"marginLeft": "15px", "marginBottom": "22px", "marginTop": "2px", "lineHeight": "1.7"})
                            ], style={"maxWidth": "800px", "margin": "0 auto", "padding": "32px 28px 18px 28px", "background": "#FFFFFF", "borderRadius": "12px", "boxShadow": "0 4px 12px rgba(0,0,0,0.07)", "marginBottom": "28px"}),
                            html.Div([
                                html.H4("Synthèse finale", style={
                                    "color": "#1A5276",
                                    "fontWeight": "bold",
                                    "marginTop": "20px",
                                    "marginBottom": "10px",
                                    "borderBottom": "2px solid #D5DBDB",
                                    "paddingBottom": "4px"
                                }),
                                html.P(
                                    "Ce tableau de bord illustre comment un étudiant en data science peut allier "
                                    "rigueur analytique, storytelling visuel et compréhension métier. "
                                    "Le modèle PageRank, bien qu’abstrait, démontre la puissance de la théorie des graphes "
                                    "pour révéler des structures d’influence cachées dans les données sportives.",
                                    style={"color": "#222", "fontSize": "16px", "marginBottom": "16px", "marginTop": "2px", "lineHeight": "1.7"}
                                ),
                                html.P(
                                    "Projet réalisé par Mevlut Cakin — Master 2 Big Data & Business Intelligence "
                                    "à l’Université Sorbonne Paris-Nord (2025).",
                                    style={"fontStyle": "italic", "color": "#1A5276", "textAlign": "center", "marginTop": "15px"}
                                )
                            ], style={"maxWidth": "800px", "margin": "0 auto", "padding": "28px 28px 12px 28px", "background": "#FAFAFA", "borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)", "marginBottom": "28px"}),
                            html.Footer(
                                [
                                    html.Hr(),
                                    html.P("Projet universitaire - Master BIDABI | Visualisation et Analyse de Données Réelles", className="text-center text-muted mt-2"),
                                    html.P("© 2025 - Tableau de bord Football PageRank | Réalisé par Mevlut Cakin",
                                           className="text-center text-body"),
                                    html.P("Source : Données Kaggle - Football Graph Network", className="text-center text-muted mb-2"),
                                ],
                                style={"backgroundColor": "#F9FAFB", "padding": "10px", "borderRadius": "6px"}
                            )
                        ], style={"background": "linear-gradient(180deg, #F9F9F4 0%, #FFFFFF 100%)", "minHeight": "100vh"})
                    ]
                ),
            ]
        )
    ], fluid=True)
], id='app-body', className='theme-light')

#  Callback principal 
@app.callback(
    Output("pagerank-graph", "figure"),
    Output("distribution-graph", "figure"),
    Output("competitivity-index", "children"),
    Output("competitivity-comment", "children"),
    Output("top3-pie", "figure"),
    Output("insights-text", "children"),
    Output("shannon-index", "children"),
    Output("story-box", "children"),
    Output("selection-info", "children"),
    Input("top-n-slider", "value"),
    Input("theme-switch", "value"),
    Input("sort-order", "value"),
    Input("pagerank-graph", "clickData"),
)
def update_graph(top_n, is_dark, sort_order, click_data):
    if df.empty or top_n is None or top_n <= 0:
        empty_fig = px.bar(title="Aucune donnée à afficher.")
        return empty_fig, empty_fig, "N/A", "Pas de données à analyser.", empty_fig, "", "N/A", "", "Aucune sélection"

    if sort_order == "desc":
        subset = df.head(int(top_n))
        category_order = "total ascending"
    else:
        subset = df.tail(int(top_n)).sort_values("pagerank", ascending=True)
        category_order = "total descending"

    #  Récupération de l'équipe sélectionnée
    selected_team = None
    if click_data and "points" in click_data and click_data["points"]:
        selected_team = click_data["points"][0].get("y")

    selection_text = "Aucune sélection" if not selected_team else f"{selected_team} — score PageRank : {float(subset.loc[subset['team']==selected_team, 'pagerank'].values[0]):.6f}"

    #  Marges et plage pour éviter que les noms touchent les barres
    max_label_len = int(subset["team"].str.len().max()) if not subset.empty else 10
    left_margin = min(320, max(120, max_label_len * 7))  # largeur en px selon la longueur des noms
    xmax = float(subset["pagerank"].max()) * 1.12 if not subset.empty else 1.0

    # Theme settings
    template = "plotly_dark" if is_dark else "plotly_white"
    bg = "#0B1320" if is_dark else "#F9FAFB"
    font_color = "#ECF0F1" if is_dark else "#2C3E50"
    dist_color = ["#F4D03F"] if is_dark else ["#2ECC71"]
    bar_scale = px.colors.sequential.Magma if is_dark else px.colors.sequential.Tealgrn

    #  Graphique principal (barres horizontales)
    fig_main = px.bar(
        subset,
        y="team",
        x="pagerank",
        orientation="h",
        title=f"Top {top_n} clubs européens par PageRank (avec ligue et pays)",
        labels={"team": "Club", "pagerank": "Score PageRank"},
        text_auto=".4f",
        color_discrete_sequence=px.colors.qualitative.Pastel2
    )
    # Place les valeurs à l'extérieur des barres et évite les coupes
    fig_main.update_traces(
        textposition="outside", cliponaxis=False,
        marker_line_width=0,
        hoverlabel=dict(bgcolor="#F9FAFB", font_size=13)
    )
    # Laisse de l'espace à droite pour les étiquettes extérieures
    fig_main.update_xaxes(range=[0, xmax])
    # Décale les ticks du côté gauche et ajoute un padding
    fig_main.update_yaxes(automargin=True)
    fig_main.update_layout(
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#2C3E50"),
        transition={"duration": 700, "easing": "cubic-in-out"},
        title_x=0.5,
        title_font=dict(size=22, color="#1A5276", family="Lato, sans-serif"),
        height=650,
        margin=dict(l=left_margin, r=60, t=80, b=60),
        yaxis=dict(categoryorder=category_order),
        hoverlabel=dict(bgcolor="#F9FAFB", font_size=13),
        bargap=0.25,
    )
    fig_main.update_traces(
        marker_line_color="#FFFFFF",
        hovertemplate="<b>%{y}</b><br>Score: %{x:.4f}<extra></extra>"
    )

    #  Distribution des scores
    fig_dist = px.histogram(
        subset,
        x="pagerank",
        nbins=10,
        title="Distribution des scores PageRank",
        color_discrete_sequence=dist_color
    )
    fig_dist.update_layout(
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#2C3E50"),
        title_x=0.5,
        title_font=dict(size=22, color="#1A5276", family="Lato, sans-serif"),
        height=450,
        margin=dict(l=40, r=40, t=60, b=40),
        hoverlabel=dict(bgcolor="#F9FAFB", font_size=13),
    )
    fig_dist.update_traces(
        marker_line_width=0,
        hoverlabel=dict(bgcolor="#F9FAFB", font_size=13),
        hovertemplate="Score: %{x:.4f} | Fréquence: %{y}<extra></extra>"
    )

    #  Calculs analytiques
    std_dev = float(np.std(subset["pagerank"]))
    avg_val = float(np.mean(subset["pagerank"]))
    index_val = round(std_dev / avg_val * 100, 2) if avg_val != 0 else 0

    # Shannon diversity on normalized scores
    probs = (subset["pagerank"] / subset["pagerank"].sum()).clip(lower=1e-12)
    shannon = float(-(probs * np.log(probs)).sum())

    # Top 3 vs Reste
    top3_sum = float(subset.head(3)["pagerank"].sum())
    total_sum = float(subset["pagerank"].sum())
    rest_sum = max(total_sum - top3_sum, 0.0)
    pct_top3 = 100 * top3_sum / total_sum if total_sum else 0

    fig_pie = px.pie(
        names=["Top 3", "Reste"],
        values=[top3_sum, rest_sum],
        hole=0.55,
        color=["Top 3", "Reste"],
        color_discrete_map={
            "Top 3": ("#F39C12" if is_dark else "#1ABC9C"),
            "Reste": ("#5D6D7E" if is_dark else "#95A5A6")
        },
        title=f"Part d’influence du Top 3 : {pct_top3:.1f}%"
    )
    fig_pie.update_layout(
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#2C3E50"),
        title_x=0.5,
        title_font=dict(size=22, color="#1A5276", family="Lato, sans-serif"),
        height=420,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    fig_pie.update_traces(
        marker_line_width=0,
        hoverlabel=dict(bgcolor="#F9FAFB", font_size=13)
    )

    # Insights textuels
    if index_val < 5:
        compet = "homogènes"
    elif index_val < 15:
        compet = "équilibrés"
    else:
        compet = "très inégaux"

    if shannon < 2.0:
        shannon_comment = "diversité faible (domination de quelques clubs)"
    elif shannon < 3.0:
        shannon_comment = "diversité modérée"
    else:
        shannon_comment = "diversité élevée"

    insight = (
        f"Le Top 3 concentre {pct_top3:.1f}% du PageRank total. "
        f"Les scores sont {compet} (indice de compétitivité : {index_val}%). "
        f"Indice de Shannon : {shannon:.2f} ({shannon_comment})."
    )
    # Storytelling enrichi
    ranked = subset.sort_values('pagerank', ascending=False).reset_index(drop=True)
    leader = ranked.iloc[0]['team']
    leader_score = ranked.iloc[0]['pagerank']
    trailer = ranked.iloc[-1]['team']
    trailer_score = ranked.iloc[-1]['pagerank']
    story = (
        f"Top {top_n} — Leader : {leader} ({leader_score:.4f}). "
        f"Dernier de l’échantillon : {trailer} ({trailer_score:.4f}). "
        f"Part Top 3 : {pct_top3:.1f}%. {shannon_comment.capitalize()} (Shannon {shannon:.2f})."
    )
    fig_main.update_traces(textposition="outside", cliponaxis=False)
    fig_main.update_layout(margin=dict(l=left_margin, r=60, t=80, b=60))

    return (
        fig_main,
        fig_dist,
        f"{index_val} %",
        ("Les clubs sont très homogènes en termes d’influence." if index_val < 5 else ("La compétitivité est équilibrée entre les clubs." if index_val < 15 else "Forte inégalité : quelques clubs dominent nettement.")),
        fig_pie,
        insight,
        f"{shannon:.2f}",
        story,
        selection_text
    )


#  Téléchargement CSV du subset courant 
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("download-btn", "n_clicks"),
    Input("top-n-slider", "value"),
    Input("sort-order", "value"),
    prevent_initial_call=True
)
def download_csv(n_clicks, top_n, sort_order):
    if not n_clicks:
        return dash.no_update
    if sort_order == "desc":
        subset = df.head(int(top_n))
    else:
        subset = df.tail(int(top_n)).sort_values("pagerank", ascending=True)
    return dcc.send_data_frame(subset.to_csv, f"classement_pagerank_top{int(top_n)}_{sort_order}.csv", index=False)

# Download: one‑page PDF (or TXT fallback) 
@app.callback(
    Output('download-summary', 'data'),
    Input('btn-download-summary', 'n_clicks'),
    prevent_initial_call=True
)
def download_summary_cb(n_clicks):
    if not n_clicks:
        return dash.no_update
    try:
        data = build_summary_pdf_bytes()
        filename = 'resume_pagerank.pdf'
    except Exception:
        data = build_summary_txt_bytes()
        filename = 'resume_pagerank.txt'
    # Dash expects a writer function for send_bytes
    return dcc.send_bytes(lambda b: b.write(data), filename)

#  Persistance simple du thème 
@app.callback(Output("theme-store", "data"), Input("theme-switch", "value"))
def persist_theme(is_dark):
    return "dark" if is_dark else "light"


#  Callback évolution PageRank par club 
@app.callback(
    Output("evolution-graph", "figure"),
    Input("club-selector", "value"),
    Input("theme-switch", "value")
)
def update_evolution_graph(selected_club, is_dark):
    import plotly.express as px
    if not selected_club or df_yearly.empty:
        return px.line(title="Aucune donnée à afficher.")
    dff = df_yearly[df_yearly["team"] == selected_club].sort_values("season")
    if dff.empty:
        return px.line(title="Aucune donnée à afficher pour ce club.")
    # Determine theme
    template = "plotly_dark" if is_dark else "plotly_white"
    bg = "#0B1320" if is_dark else "#F9FAFB"
    font_color = "#ECF0F1" if is_dark else "#2C3E50"
    fig = px.line(
        dff,
        x="season",
        y="pagerank",
        markers=True,
        title=f"Évolution du PageRank pour {selected_club}",
        labels={"season": "Saison", "pagerank": "Score PageRank"}
    )
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
        marker_line_width=0,
        hoverlabel=dict(bgcolor="#F9FAFB", font_size=13),
        hovertemplate="Saison: %{x}<br>PageRank: %{y:.4f}<extra></extra>"
    )
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#2C3E50"),
        title_x=0.5,
        title_font=dict(size=22, color="#1A5276", family="Lato, sans-serif"),
        height=400,
        margin=dict(l=60, r=40, t=60, b=60)
    )
    return fig

# Lancement
if __name__ == "__main__":
    logging.info("Dashboard prêt. Ouverture du navigateur…")
    webbrowser.open_new("http://127.0.0.1:8060")
    app.run(debug=True, port=8060, use_reloader=False)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
    body, html {
        font-family: 'Lato', sans-serif;
        background: linear-gradient(180deg, #F9F9F4 0%, #FFFFFF 100%);
        color: #2C3E50;
        margin: 0;
        padding: 0;
        line-height: 1.6;
        letter-spacing: 0.2px;
        transition: background-color 0.5s, color 0.5s;
        min-height: 100vh;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1A5276;
        font-weight: 700;
    }
    /* Explications sobres : noir ou gris foncé uniquement */
    p, li, .text-body, .text-secondary, .text-muted, .lead,
    .card p, .alert p, footer p, .card-text, .form-text, label, small {
        color: #171717 !important;
        font-size: 16px;
        line-height: 1.7;
    }
    /* Neutralisation des textes rouges/roses */
    .text-danger, .text-warning, .text-rose, .text-pink, .text-error {
        color: #171717 !important;
    }
    .navbar {
        background-color: #1A5276 !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    }
    .glass-card {
        background: #FFFFFF;
        border-left: 6px solid #117A65;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-radius: 10px;
        transition: transform 0.3s, box-shadow 0.3s;
        padding: 10px 15px;
    }
    .glass-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
    }
    .alert-info, .card {
        background-color: #F4F9F8 !important;
        border-left: 5px solid #1ABC9C !important;
        color: #171717 !important;
    }
    footer {
        background-color: #F9FAFB;
        border-top: 2px solid #E5E8E8;
        padding: 10px;
        text-align: center;
        font-size: 14px;
        color: #5D6D7E;
    }
    a, .text-info, .btn-link {
        color: #117A65 !important;
        font-weight: 600;
        text-decoration: none;
    }
    a:hover {
        color: #0B5345 !important;
        text-decoration: underline;
    }
    .section-title {
        color: #1A5276;
        font-weight: 700;
        margin-top: 25px;
        border-bottom: 2px solid #D5DBDB;
        padding-bottom: 4px;
    }
    /* --- THEME LIGHT --- */
    .theme-light, body.theme-light {
        background-color: #F9F9F4 !important;
        color: #2C3E50 !important;
        transition: background-color 0.5s, color 0.5s;
    }
    .theme-light .navbar, body.theme-light .navbar {
        background-color: #1A5276 !important;
    }
    .theme-light .glass-card, body.theme-light .glass-card {
        background: #FFFFFF !important;
        border-left: 6px solid #117A65 !important;
        color: #222 !important;
    }
    .theme-light .alert-info, .theme-light .card, body.theme-light .alert-info, body.theme-light .card {
        background-color: #F4F9F8 !important;
        border-left: 5px solid #1ABC9C !important;
        color: #171717 !important;
    }
    .theme-light footer, body.theme-light footer {
        background-color: #F9FAFB !important;
        color: #5D6D7E !important;
    }
    .theme-light a, .theme-light .text-info, .theme-light .btn-link,
    body.theme-light a, body.theme-light .text-info, body.theme-light .btn-link {
        color: #117A65 !important;
    }
    /* --- THEME DARK --- */
    .theme-dark, body.theme-dark {
        background-color: #0E1117 !important;
        color: #ECF0F1 !important;
        transition: background-color 0.5s, color 0.5s;
    }
    .theme-dark .navbar, body.theme-dark .navbar {
        background-color: #121A24 !important;
    }
    .theme-dark .glass-card, body.theme-dark .glass-card {
        background: #1C2833 !important;
        border-left: 6px solid #1ABC9C !important;
        color: #ECF0F1 !important;
    }
    .theme-dark .alert-info, .theme-dark .card, body.theme-dark .alert-info, body.theme-dark .card {
        background-color: #1A1F25 !important;
        border-left: 5px solid #1ABC9C !important;
        color: #ECF0F1 !important;
    }
    .theme-dark footer, body.theme-dark footer {
        background-color: #121A24 !important;
        color: #BDC3C7 !important;
    }
    .theme-dark a, .theme-dark .text-info, .theme-dark .btn-link,
    body.theme-dark a, body.theme-dark .text-info, body.theme-dark .btn-link {
        color: #1ABC9C !important;
    }
    /* Adaptation des titres et paragraphes en mode sombre */
    .theme-dark h1, .theme-dark h2, .theme-dark h3, .theme-dark h4, .theme-dark h5, .theme-dark h6,
    body.theme-dark h1, body.theme-dark h2, body.theme-dark h3, body.theme-dark h4, body.theme-dark h5, body.theme-dark h6 {
        color: #1ABC9C !important;
    }
    .theme-dark p, .theme-dark li, .theme-dark .text-body, .theme-dark .text-secondary, .theme-dark .text-muted, .theme-dark .lead,
    .theme-dark .card p, .theme-dark .alert p, .theme-dark footer p, .theme-dark .card-text, .theme-dark .form-text, .theme-dark label, .theme-dark small,
    body.theme-dark p, body.theme-dark li, body.theme-dark .text-body, body.theme-dark .text-secondary, body.theme-dark .text-muted, body.theme-dark .lead,
    body.theme-dark .card p, body.theme-dark .alert p, body.theme-dark footer p, body.theme-dark .card-text, body.theme-dark .form-text, body.theme-dark label, body.theme-dark small {
        color: #ECF0F1 !important;
    }
    /* Remove any residual red in dark mode */
    .theme-dark .text-danger, .theme-dark .text-warning, .theme-dark .text-rose, .theme-dark .text-pink, .theme-dark .text-error,
    body.theme-dark .text-danger, body.theme-dark .text-warning, body.theme-dark .text-rose, body.theme-dark .text-pink, body.theme-dark .text-error {
        color: #ECF0F1 !important;
    }
    /* Paragraph/section spacing */
    .context-section {
        margin-bottom: 30px;
        padding-bottom: 12px;
    }
    .context-section h4 {
        margin-top: 18px;
        margin-bottom: 8px;
        color: #1A5276;
        font-weight: bold;
    }
    .theme-dark .context-section h4,
    body.theme-dark .context-section h4 {
        color: #1ABC9C !important;
    }
    /* Responsive */
    @media (max-width: 900px) {
        .glass-card, .context-section {
            padding: 12px 6px !important;
        }
    }
    </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''
# Callback Comparaison Ligue / Pays (MAJ: sans carte) 
@app.callback(
    Output("compare-boxplot", "figure"),
    Input("theme-switch", "value"),
)
def update_compare_section(is_dark):
    return build_compare_figures(dim="country", is_dark=is_dark)

#  Callback global pour appliquer la classe thème au body 
@app.callback(
    Output('app-body', 'className'),
    Input('theme-switch', 'value')
)
def update_theme(is_dark):
    return 'theme-dark' if is_dark else 'theme-light'