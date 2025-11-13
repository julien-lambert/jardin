import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "jardin.db"

SCHEMA = """
DROP TABLE IF EXISTS plants;
DROP TABLE IF EXISTS species;

CREATE TABLE species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    common_name TEXT NOT NULL,
    variety_name TEXT,
    latin_name TEXT,
    family TEXT,
    genus TEXT,
    strata TEXT,
    tags TEXT,
    notes TEXT,
    image_url TEXT
);

CREATE TABLE plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL,
    label TEXT,
    lat REAL,
    lon REAL,
    zone TEXT,
    planted_at DATE,
    notes TEXT,
    image_local TEXT,   -- <== NOUVELLE COLONNE POUR L’IMAGE LOCALE DE L’INDIVIDU
    FOREIGN KEY (species_id) REFERENCES species(id)
);
"""

# quelques données minimales pour tester
SEED_SPECIES = [
    ("Pommier", "Reine des Reinettes", "Malus domestica", "Rosaceae", "Malus", "arbre", "fruitier,pepins,ancien", "Variété ancienne"),
    ("Poirier", "Conférence", "Pyrus communis", "Rosaceae", "Pyrus", "arbre", "fruitier,pepins", "Variété classique")
]

SEED_PLANTS = [
    (1, "POM-001", 45.00010, 4.00010, "Îlot nord", "2025-11-01", "Planté sur butte."),
    (2, "POI-001", 45.00020, 4.00020, "Îlot nord", "2025-11-02", "Exposition est.")
]


def main():
    if DB_PATH.exists():
        print(f"Suppression de l'ancienne base {DB_PATH}")
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Création du schéma…")
    cur.executescript(SCHEMA)

    print("Insertion des données de test…")
    cur.executemany(
        """
        INSERT INTO species (common_name, variety_name, latin_name, family, genus, strata, tags, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        SEED_SPECIES
    )

    cur.executemany(
        """
        INSERT INTO plants (species_id, label, lat, lon, zone, planted_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        SEED_PLANTS
    )

    conn.commit()
    conn.close()
    print("Base initialisée.")


if __name__ == "__main__":
    main()