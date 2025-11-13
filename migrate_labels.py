import sqlite3
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "jardin.db"


def make_species_code(common_name):
    """Code espèce : 3 lettres en majuscules, sans accents/espaces."""
    if not common_name:
        return "XXX"
    base = common_name.strip().upper()
    # on ne garde que les lettres A–Z
    base = re.sub(r"[^A-Z]", "", base)
    return (base + "XXX")[:3]


def make_variety_code(variety_name):
    """Code variété : 3 lettres, ou TYP si pas de cultivar."""
    if not variety_name:
        return "TYP"
    base = variety_name.strip().upper()
    # on garde lettres + chiffres, au cas où
    base = re.sub(r"[^A-Z0-9]", "", base)
    return (base + "XXX")[:3]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1) S'assurer qu'on a une colonne old_label pour garder la trace
    try:
        cur.execute("ALTER TABLE plants ADD COLUMN old_label TEXT")
    except sqlite3.OperationalError:
        # colonne déjà existante → on ignore
        pass

    # On ne touche pas aux anciens old_label existants, on ne remplit que si NULL / vide
    cur.execute(
        "UPDATE plants SET old_label = label "
        "WHERE old_label IS NULL OR old_label = ''"
    )

    # 2) Récupérer tous les individus avec leur espèce
    cur.execute(
        """
        SELECT
            plants.id,
            plants.species_id,
            plants.label,
            species.common_name,
            species.variety_name
        FROM plants
        JOIN species ON plants.species_id = species.id
        ORDER BY plants.species_id, plants.id
        """
    )
    rows = cur.fetchall()

    # 3) Générer les nouveaux labels de manière cohérente
    counters = {}  # (code_species, code_variety) -> dernier numéro utilisé
    updates = []

    for row in rows:
        code_species = make_species_code(row["common_name"])
        code_variety = make_variety_code(row["variety_name"])
        key = (code_species, code_variety)

        n = counters.get(key, 0) + 1
        counters[key] = n

        new_label = f"{code_species}-{code_variety}-{n:03d}"
        updates.append((new_label, row["id"]))

    # 4) Mise à jour en base
    cur.executemany("UPDATE plants SET label = ? WHERE id = ?", updates)
    conn.commit()
    conn.close()

    print("Migration terminée.")
    print("Nombre d'individus mis à jour :", len(updates))
    print("Exemple de codes générés :")
    for (new_label, plant_id) in updates[:10]:
        print(f"  id={plant_id} -> {new_label}")


if __name__ == "__main__":
    main()
