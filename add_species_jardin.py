import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "jardin.db"

species_data = [
    # 1) Poirier 1 – Marguerite Marillat
    ("Poirier", "Marguerite Marillat",
     "Pyrus communis L.", "Rosaceae", "Pyrus", "arbre",
     "fruitier,pepins",
     "Cultivar ancien 'Marguerite Marillat'. Porte-greffe à préciser (franc, BA29…)."),

    # 2) Poirier 2 – cultivar à préciser
    ("Poirier", None,
     "Pyrus communis L.", "Rosaceae", "Pyrus", "arbre",
     "fruitier,pepins",
     "Poirier de table, cultivar à préciser. Porte-greffe à préciser (franc, BA29…)."),

    # 3) Amandier
    ("Amandier", None,
     "Prunus dulcis (Mill.) D.A.Webb", "Rosaceae", "Prunus", "arbre",
     "fruitier,noyau",
     "Amandier, cultivar à préciser. Porte-greffe possible GF677, franc, etc."),

    # 4) Pommier 'Reine des Reinettes'
    ("Pommier", "Reine des Reinettes",
     "Malus domestica Borkh.", "Rosaceae", "Malus", "arbre",
     "fruitier,pepins,ancien",
     "Cultivar 'Reine des Reinettes'. Porte-greffe à préciser (M106, M111…)."),

    # 5) Pommier 'Nationale'
    ("Pommier", "Nationale",
     "Malus domestica Borkh.", "Rosaceae", "Malus", "arbre",
     "fruitier,pepins",
     "Cultivar 'Nationale'. Porte-greffe à préciser (M106, M111…)."),

    # 6) Cognassier
    ("Cognassier", None,
     "Cydonia oblonga Mill.", "Rosaceae", "Cydonia", "arbre",
     "fruitier,pepins",
     "Cognassier, cultivar à préciser. Porte-greffe franc à préciser."),

    # 7) Châtaignier
    ("Châtaignier", None,
     "Castanea sativa Mill.", "Fagaceae", "Castanea", "arbre",
     "fruitier,canopée",
     "Châtaignier, cultivar à préciser (variété locale). Porte-greffe franc."),

    # 8) Noyer
    ("Noyer commun", None,
     "Juglans regia L.", "Juglandaceae", "Juglans", "arbre",
     "fruitier,canopée",
     "Noyer commun, cultivar à préciser. Porte-greffe possible franc ou hybrides J. nigra × J. regia."),

    # 9) Cerisier
    ("Cerisier", None,
     "Prunus avium (L.) L.", "Rosaceae", "Prunus", "arbre",
     "fruitier,noyau",
     "Cerisier doux, cultivar à préciser. Porte-greffe possible Colt, Sainte-Lucie, etc."),

    # 10) Abricotier 'Luizet'
    ("Abricotier", "Luizet",
     "Prunus armeniaca L.", "Rosaceae", "Prunus", "arbre",
     "fruitier,noyau",
     "Cultivar 'Luizet'. Porte-greffe à préciser (franc, Myrobolan…)."),

    # 11) Abricotier 'Polonais'
    ("Abricotier", "Polonais",
     "Prunus armeniaca L.", "Rosaceae", "Prunus", "arbre",
     "fruitier,noyau",
     "Cultivar 'Polonais'. Porte-greffe à préciser (franc, Myrobolan…)."),

    # 12) Néflier d’Allemagne
    ("Néflier d'Allemagne", None,
     "Mespilus germanica L.", "Rosaceae", "Mespilus", "arbre",
     "fruitier",
     "Néflier d’Allemagne, cultivar à préciser. Porte-greffe franc ou cognassier."),

    # 13) Prunier d’Ente
    ("Prunier d'Ente", "d'Ente",
     "Prunus domestica L.", "Rosaceae", "Prunus", "arbre",
     "fruitier,noyau",
     "Prunier d’Ente (pruneau d’Agen). Porte-greffe à préciser (Myrobolan, Saint-Julien A…)."),

    # 14) Mirabellier
    ("Mirabellier", None,
     "Prunus domestica subsp. syriaca", "Rosaceae", "Prunus", "arbre",
     "fruitier,noyau",
     "Mirabellier, cultivar à préciser. Porte-greffe à préciser (Myrobolan, Saint-Julien A…)."),

    # 15) Nashi
    ("Poirier asiatique (Nashi)", None,
     "Pyrus pyrifolia (Burm.f.) Nakai", "Rosaceae", "Pyrus", "arbre",
     "fruitier,pepins",
     "Nashi, cultivar à préciser. Porte-greffe possible franc ou cognassier compatible."),

    # 16–17) Amélanchier du Canada
    ("Amélanchier du Canada", None,
     "Amelanchier canadensis (L.) Medik.", "Rosaceae", "Amelanchier", "arbuste",
     "petits-fruits,mellifere",
     "Amélanchier du Canada. Deux plants prévus, cultivar à préciser."),

    # 18–19) Aronie noire
    ("Aronie noire", None,
     "Aronia melanocarpa (Michx.) Elliott", "Rosaceae", "Aronia", "arbuste",
     "petits-fruits",
     "Aronie noire (baies riches en anthocyanes). Deux plants, cultivar à préciser."),

    # 20–21) Argousier
    ("Argousier", None,
     "Hippophae rhamnoides L.", "Elaeagnaceae", "Hippophae", "arbuste",
     "petits-fruits,fixateur-azote,mellifere",
     "Argousier (baies très vitaminées, fixateur d’azote). Deux plants, cultivar/sexes à préciser."),

    # 22–24) Cassis
    ("Cassis", None,
     "Ribes nigrum L.", "Grossulariaceae", "Ribes", "arbuste",
     "petits-fruits",
     "Cassis, cultivars à préciser (3 pieds)."),

    # 25–27) Groseillier rouge
    ("Groseillier rouge", None,
     "Ribes rubrum L.", "Grossulariaceae", "Ribes", "arbuste",
     "petits-fruits",
     "Groseillier rouge, cultivars à préciser (3 pieds)."),

    # 28–30) Framboisier
    ("Framboisier", None,
     "Rubus idaeus L.", "Rosaceae", "Rubus", "arbuste",
     "petits-fruits",
     "Framboisier, variétés à préciser (3 rangs / pieds)."),

    # 31) Tilleul
    ("Tilleul", None,
     "Tilia sp.", "Malvaceae", "Tilia", "arbre",
     "mellifere,arbre",
     "Tilleul, espèce/variété à préciser (cordata, platyphyllos, etc.).")
]


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"Base {DB_PATH} introuvable. Lance d'abord init_db.py pour la créer.")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Optionnel : décommenter si tu veux d’abord virer les espèces de test
    # cur.execute("DELETE FROM species")
    # conn.commit()

    cur.executemany(
        """
        INSERT INTO species
          (common_name, variety_name, latin_name, family, genus, strata, tags, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        species_data,
    )

    conn.commit()
    conn.close()
    print(f"{len(species_data)} espèces ajoutées.")


if __name__ == "__main__":
    main()