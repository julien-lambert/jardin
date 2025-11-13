import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "jardin.db"


def get_species_id(cur, common_name, variety_name=None):
    """
    Retourne l'id de la ligne species correspondant au couple
    (common_name, variety_name). Lève une erreur si non trouvé.
    """
    if variety_name is None:
        cur.execute(
            """
            SELECT id FROM species
            WHERE common_name = ? AND variety_name IS NULL
            """,
            (common_name,),
        )
    else:
        cur.execute(
            """
            SELECT id FROM species
            WHERE common_name = ? AND variety_name = ?
            """,
            (common_name, variety_name),
        )

    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Espèce introuvable : {common_name!r}, {variety_name!r}")
    return row[0]


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"Base {DB_PATH} introuvable. Lance d'abord init_db.py + add_species_jardin.py")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # On efface les plants existants pour repartir propre
    # (si tu veux les garder, commente la ligne suivante)
    cur.execute("DELETE FROM plants")
    conn.commit()

    # Récupération des species_id à partir des noms
    species_ids = {}

    def sid(common, variety=None):
        key = (common, variety)
        if key not in species_ids:
            species_ids[key] = get_species_id(cur, common, variety)
        return species_ids[key]

    # Définition des 31 plants
    # zone = "À placer" pour le moment (tu ajusteras ensuite)
    # lat/lon = None (pas de coordonnées encore)
    # planted_at = None (date à compléter)
    plants = []

    # 1) Poirier 1 – Marguerite Marillat
    plants.append((
        sid("Poirier", "Marguerite Marillat"),
        "POI-MM-001", None, None, "À placer", None,
        "Poirier 'Marguerite Marillat'. Porte-greffe à préciser."
    ))

    # 2) Poirier 2 – cultivar à préciser
    plants.append((
        sid("Poirier", None),
        "POI-002-001", None, None, "À placer", None,
        "Poirier de table, cultivar à préciser. Porte-greffe à préciser."
    ))

    # 3) Amandier
    plants.append((
        sid("Amandier", None),
        "AMA-001", None, None, "À placer", None,
        "Amandier, cultivar et porte-greffe à préciser."
    ))

    # 4) Pommier ‘Reine des Reinettes’
    plants.append((
        sid("Pommier", "Reine des Reinettes"),
        "POM-RR-001", None, None, "À placer", None,
        "Pommier 'Reine des Reinettes'. Porte-greffe à préciser."
    ))

    # 5) Pommier ‘Nationale’
    plants.append((
        sid("Pommier", "Nationale"),
        "POM-NAT-001", None, None, "À placer", None,
        "Pommier 'Nationale'. Porte-greffe à préciser."
    ))

    # 6) Cognassier
    plants.append((
        sid("Cognassier", None),
        "COG-001", None, None, "À placer", None,
        "Cognassier, cultivar et porte-greffe à préciser."
    ))

    # 7) Châtaignier
    plants.append((
        sid("Châtaignier", None),
        "CHA-001", None, None, "À placer", None,
        "Châtaignier, cultivar à préciser."
    ))

    # 8) Noyer
    plants.append((
        sid("Noyer commun", None),
        "NOY-001", None, None, "À placer", None,
        "Noyer commun, cultivar et porte-greffe à préciser."
    ))

    # 9) Cerisier
    plants.append((
        sid("Cerisier", None),
        "CER-001", None, None, "À placer", None,
        "Cerisier doux, cultivar et porte-greffe à préciser."
    ))

    # 10) Abricotier ‘Luizet’
    plants.append((
        sid("Abricotier", "Luizet"),
        "ABR-LUI-001", None, None, "À placer", None,
        "Abricotier 'Luizet'. Porte-greffe à préciser."
    ))

    # 11) Abricotier ‘Polonais’
    plants.append((
        sid("Abricotier", "Polonais"),
        "ABR-POL-001", None, None, "À placer", None,
        "Abricotier 'Polonais'. Porte-greffe à préciser."
    ))

    # 12) Néflier
    plants.append((
        sid("Néflier d'Allemagne", None),
        "NEF-001", None, None, "À placer", None,
        "Néflier d’Allemagne, cultivar et porte-greffe à préciser."
    ))

    # 13) Prunier d’Ente
    plants.append((
        sid("Prunier d'Ente", "d'Ente"),
        "PRU-EN-001", None, None, "À placer", None,
        "Prunier d’Ente (pruneau d’Agen). Porte-greffe à préciser."
    ))

    # 14) Mirabellier
    plants.append((
        sid("Mirabellier", None),
        "MIR-001", None, None, "À placer", None,
        "Mirabellier, cultivar et porte-greffe à préciser."
    ))

    # 15) Nashi
    plants.append((
        sid("Poirier asiatique (Nashi)", None),
        "NAS-001", None, None, "À placer", None,
        "Nashi, cultivar et porte-greffe à préciser."
    ))

    # 16–17) Amélanchier du Canada (2 plants)
    for i in range(1, 3):
        plants.append((
            sid("Amélanchier du Canada", None),
            f"AME-{i:03d}", None, None, "À placer", None,
            "Amélanchier du Canada, cultivar à préciser."
        ))

    # 18–19) Aronie noire (2 plants)
    for i in range(1, 3):
        plants.append((
            sid("Aronie noire", None),
            f"ARO-{i:03d}", None, None, "À placer", None,
            "Aronie noire, cultivar à préciser."
        ))

    # 20–21) Argousier (2 plants)
    for i in range(1, 3):
        plants.append((
            sid("Argousier", None),
            f"ARG-{i:03d}", None, None, "À placer", None,
            "Argousier (baies vitaminées, fixateur d’azote). Sexe/cultivar à préciser."
        ))

    # 22–24) Cassis (3 plants)
    for i in range(1, 4):
        plants.append((
            sid("Cassis", None),
            f"CAS-{i:03d}", None, None, "À placer", None,
            "Cassis, cultivar à préciser."
        ))

    # 25–27) Groseillier rouge (3 plants)
    for i in range(1, 4):
        plants.append((
            sid("Groseillier rouge", None),
            f"GRO-{i:03d}", None, None, "À placer", None,
            "Groseillier rouge, cultivar à préciser."
        ))

    # 28–30) Framboisier (3 plants)
    for i in range(1, 4):
        plants.append((
            sid("Framboisier", None),
            f"FRA-{i:03d}", None, None, "À placer", None,
            "Framboisier, variété à préciser."
        ))

    # 31) Tilleul
    plants.append((
        sid("Tilleul", None),
        "TIL-001", None, None, "À placer", None,
        "Tilleul, espèce et variété à préciser."
    ))

    # Insertion dans la base
    cur.executemany(
        """
        INSERT INTO plants
          (species_id, label, lat, lon, zone, planted_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        plants,
    )

    conn.commit()
    conn.close()
    print(f"{len(plants)} plants insérés.")


if __name__ == "__main__":
    main()