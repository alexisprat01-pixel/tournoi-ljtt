# Top12 — Gestion de tournoi de tennis de table

Application desktop (Python + PyQt6) pour gérer une compétition de tennis de table à **12 joueurs** sur **11 tours** :

- **Tours 1 à 5** : phase de poules (2 poules de 6, championnat aller).
- **Tours 6 à 11** : phase finale croisée. Le **tour 11** oppose les joueurs de **même rang** dans leur poule (1A‑1B, 2A‑2B, …).

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

La base SQLite est créée dans `%USERPROFILE%\.top12\top12.db` (persistée entre les lancements).

## Utilisation

1. **Saisie des joueurs** : entre les 12 noms (et club éventuel).
2. **Tirage des poules** : le bouton "Tirer les poules" répartit aléatoirement en 2 poules de 6 et génère automatiquement les **5 premiers tours**.
3. **Phase de poules** : pour chaque match, saisis le score en sets (`0` à `5`) puis "Valider".
4. **Génération de la phase finale** : une fois tous les matchs de poule joués, le bouton "Générer la phase finale" apparaît. Il crée les **6 tours croisés** en utilisant le classement des poules — le 11ᵉ tour est par construction la finale par rang.
5. **Phase finale** : saisis les scores des tours 6 à 11.
6. **Classement final** : il s'affiche automatiquement à la fin.

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

## Distribution — Top12.exe autonome

Pour produire un **exécutable Windows unique** que tu peux copier sur n'importe quel PC (sans Python installé) :

```powershell
cd D:\appliTop12\top12
.\build.ps1
```

Le script :
1. crée le venv s'il n'existe pas,
2. installe les dépendances (PyQt6, PyInstaller),
3. nettoie les anciens builds,
4. exécute PyInstaller via [top12.spec](top12.spec),
5. produit `dist\Top12.exe` (~40-60 Mo, ~10-15 s de démarrage la 1ʳᵉ fois).

Copie ce `.exe` sur n'importe quel PC Windows → double-clic, ça tourne. La base SQLite se crée dans `%USERPROFILE%\.top12\` du PC où l'app est lancée, donc les données restent locales à chaque poste.

### Icône d'application

Si tu veux une vraie icône Windows : pose `icon.ico` dans `src/assets/` avant de lancer `build.ps1`. Sans ça, l'icône par défaut Python est utilisée.

## Logo du club

Pose simplement ton logo en `src/assets/logo.png` (format carré conseillé). Il sera affiché dans la barre latérale au prochain lancement.

## Couleurs

Thème **rouge & noir** du club, défini dans `src/ui/styles.py` (constantes `RED`, `BLACK`, etc.) si tu veux ajuster les nuances.

## Réinitialiser

Le bouton "Réinitialiser" dans la barre latérale efface joueurs et matchs pour relancer un tournoi.

## Structure du code

```
top12/
├── main.py                    # Point d'entrée
├── requirements.txt
├── README.md
└── src/
    ├── models.py              # Player, Match, PlayerStanding
    ├── tournament.py          # Algos: Berger (poules), croisé, classement
    ├── database.py            # SQLite
    ├── assets/                # logo.png ici
    └── ui/
        ├── styles.py          # Thème QSS rouge/noir
        ├── main_window.py     # Fenêtre principale + navigation
        ├── player_page.py     # Saisie des 12 joueurs
        ├── rounds_page.py     # Tours, matchs, classements
        └── match_card.py      # Carte d'un match
```
