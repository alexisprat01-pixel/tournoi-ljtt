# Tournoi LJTT — Gestion de tournois de tennis de table

Application desktop (Python + PyQt6) pour gérer les tournois du club LJTT.

## Types de tournois pris en charge

| Code     | Nom    | Description |
|----------|--------|-------------|
| `top12`  | Top 12 | 12 joueurs, 11 tours : 5 tours de poules (2×6) + 6 tours croisés (le tour 11 oppose les joueurs de même rang). |

D'autres formats viendront s'ajouter à mesure.

## Pré‑requis

- Python 3.10+ (Windows / macOS / Linux)

## Installation

```powershell
cd D:\appliTop12\top12
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancement

```powershell
python main.py
```

La base SQLite est créée dans `%USERPROFILE%\.tournoi-ljtt\tournoi-ljtt.db`. Si une ancienne base `~/.top12/top12.db` existe, elle est automatiquement recopiée au premier lancement.

## Utilisation (format Top 12)

1. **Création du tournoi** : nom + type (Top 12) + date + notes.
2. **Saisie des joueurs** : entre les 12 noms et leurs points.
3. **Tirage des poules** : seeding fixe 1‑4‑5‑8‑9‑12 (poule A) / 2‑3‑6‑7‑10‑11 (poule B). Génère les 5 tours de poules.
4. **Phase de poules (Session 1)** : saisis les scores en sets.
5. **Génération de la phase finale** : une fois la Session 1 jouée, génère les 6 tours croisés. Le tour 11 oppose les joueurs de même rang.
6. **Phase finale (Session 2)** : saisis les scores des tours 6 à 11.
7. **Classement final + statistiques** : automatiques.

### Système de points

| Résultat        | Points |
|-----------------|--------|
| Victoire        | 1      |
| Défaite         | 0      |
| Forfait / 0‑0   | 0      |

Départage :
1. Si 2 joueurs sont à égalité → vainqueur du face‑à‑face passe devant.
2. Si 3+ joueurs sont à égalité → différentiel de sets (sets gagnés − sets perdus).
3. Si après ce départage il reste 2 joueurs à égalité → on revient au face‑à‑face.

## Distribution — TournoiLJTT.exe autonome

Pour produire un **exécutable Windows unique** :

```powershell
cd D:\appliTop12\top12
.\build.ps1
```

Le script :
1. crée le venv s'il n'existe pas,
2. installe les dépendances (PyQt6, PyInstaller),
3. nettoie les anciens builds,
4. exécute PyInstaller via [tournoi_ljtt.spec](tournoi_ljtt.spec),
5. produit `dist\TournoiLJTT.exe` (~37 Mo).

Copie ce `.exe` sur n'importe quel PC Windows → double‑clic, ça tourne.

### Icône d'application

Si tu veux une vraie icône Windows : pose `icon.ico` dans `src/assets/` avant de lancer `build.ps1`.

## Logo du club

Pose ton logo en `src/assets/logo.png` (format carré conseillé). Il s'affiche dans la barre latérale.

## Couleurs

Thème **rouge & noir** du club, défini dans `src/ui/styles.py`.

## Structure du code

```
top12/
├── main.py                       # Point d'entrée
├── requirements.txt
├── tournoi_ljtt.spec             # PyInstaller spec
├── build.ps1                     # Build silencieux
├── README.md
└── src/
    ├── models.py                 # Tournament (avec type), Player, Match, PlayerStanding
    ├── tournament.py             # Algos: Berger (poules), croisé, classement, équité tables
    ├── stats.py                  # Récompenses (Marathonien, Showmen, etc.)
    ├── database.py               # SQLite + migrations
    ├── assets/                   # logo.png, icon.ico
    └── ui/
        ├── styles.py             # Thème V6 + GlowBackground
        ├── main_window.py        # Fenêtre + sidebar + navigation
        ├── home_page.py          # Liste des tournois
        ├── tournament_dialog.py  # Création / édition de tournoi (avec combo Type)
        ├── player_page.py        # Saisie des joueurs
        ├── rounds_page.py        # Sessions 1 et 2 (matchs + classements)
        ├── general_ranking_page.py
        ├── statistics_page.py
        ├── set_dialog.py         # Saisie des scores set par set
        ├── match_card.py
        ├── print_export.py       # Impression / export PDF
        └── dialogs.py
```
