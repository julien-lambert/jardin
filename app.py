from flask import Flask, g, render_template, request, redirect, url_for, flash
import sqlite3 
from pathlib import Path
import os


BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "jardin.db"

app = Flask(__name__)


# ---------- Connexion SQLite ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # accès par nom de colonne
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        db.close()


import re

def make_species_code(common_name):
    """Code espèce : 3 lettres en majuscules, sans accents/espaces."""
    if not common_name:
        return "XXX"
    base = common_name.strip().upper()
    base = re.sub(r"[^A-Z]", "", base)
    return (base + "XXX")[:3]


def make_variety_code(variety_name):
    """Code variété : 3 lettres, ou TYP si pas de cultivar."""
    if not variety_name:
        return "TYP"
    base = variety_name.strip().upper()
    base = re.sub(r"[^A-Z0-9]", "", base)
    return (base + "XXX")[:3]


def generate_label(db, species_id):
    """
    Génère un label du type XXX-YYY-NNN en se basant sur
    species.common_name et species.variety_name.
    """
    row = db.execute(
        """
        SELECT common_name, variety_name
        FROM species
        WHERE id = ?
        """,
        (species_id,)
    ).fetchone()

    if row is None:
        code_species = "XXX"
        code_variety = "TYP"
    else:
        code_species = make_species_code(row["common_name"])
        code_variety = make_variety_code(row["variety_name"])

    prefix = "{}-{}-".format(code_species, code_variety)

    last = db.execute(
        """
        SELECT label
        FROM plants
        WHERE label LIKE ?
        ORDER BY label DESC
        LIMIT 1
        """,
        (prefix + "%",)
    ).fetchone()

    if last:
        try:
            n_str = last["label"].split("-")[-1]
            n = int(n_str)
        except Exception:
            n = 0
    else:
        n = 0

    n += 1
    num = "{:03d}".format(n)

    return prefix + num
    
# ---------- Routes ----------

@app.route("/")
def home():
    """Page d’accueil avec quelques stats."""
    db = get_db()
    stats = {
        "species_count": db.execute("SELECT COUNT(*) FROM species").fetchone()[0],
        "plant_count": db.execute("SELECT COUNT(*) FROM plants").fetchone()[0],
        "zone_count": db.execute(
            "SELECT COUNT(DISTINCT zone) FROM plants WHERE zone IS NOT NULL"
        ).fetchone()[0],
    }
    return render_template("home.html", stats=stats)


@app.route("/plants")
def plants():
    db = get_db()

    search = request.args.get("q", "").strip()
    zone_filter = request.args.get("zone", "").strip()

    where = []
    params = []

    if search:
        where.append("""
            (plants.label LIKE ?
             OR species.common_name LIKE ?
             OR species.variety_name LIKE ?
             OR species.latin_name LIKE ?)
        """)
        like = f"%{search}%"
        params.extend([like, like, like, like])

    if zone_filter:
        where.append("plants.zone = ?")
        params.append(zone_filter)

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    plants = db.execute(f"""
        SELECT
          plants.*,
          species.common_name,
          species.variety_name,
          species.latin_name,
          species.family        AS species_family,
          species.genus         AS species_genus,
          species.strata        AS species_strata,
          species.image_url     AS species_image_url
        FROM plants
        JOIN species ON plants.species_id = species.id
        {where_sql}
        ORDER BY
          CASE species.strata
            WHEN 'canopée'     THEN 1
            WHEN 'sous-étage'  THEN 2
            WHEN 'arbuste'     THEN 3
            WHEN 'liane'       THEN 4
            WHEN 'couvre-sol'  THEN 5
            WHEN 'autre'       THEN 6
            ELSE 7
          END,
          species.family,
          species.genus,
          species.latin_name,
          plants.label
    """, params).fetchall()

    zones_rows = db.execute("""
        SELECT DISTINCT zone
        FROM plants
        WHERE zone IS NOT NULL AND zone <> ''
        ORDER BY zone
    """).fetchall()
    zones = [r["zone"] for r in zones_rows]

    return render_template(
        "plants.html",
        plants=plants,
        zones=zones,
        search=search,
        zone_filter=zone_filter,
    )


@app.route("/plant/<int:plant_id>")
def plant_detail(plant_id):
    """Fiche détaillée d’un plant (individu), avec toutes les infos taxonomiques et horticoles."""
    db = get_db()
    plant = db.execute(
        """
        SELECT
            -- champs individu
            plants.id,
            plants.species_id,
            plants.label,
            plants.zone,
            plants.planted_at,
            plants.lat,
            plants.lon,
            plants.altitude,
            plants.notes,
            plants.image_local,
            plants.tags,
            plants.micro_site,
            plants.exposure_local,
            plants.soil_local,
            plants.height_current,
            plants.acquisition_type,
            plants.acquisition_source,
            plants.plantnet_obs_id,
            plants.status,
            plants.care_notes,
            plants.rootstock,          -- <<< AJOUT ESSENTIEL !!!

            -- champs espèce (base taxonomique)
            species.common_name,
            species.variety_name,
            species.latin_name      AS species_latin_name,
            species.family          AS species_family,
            species.genus           AS species_genus,
            species.strata          AS species_strata,
            species.tags            AS species_tags,
            species.notes           AS species_notes,
            species.image_url       AS species_image_url,
            species.origin          AS species_origin,
            species.plant_type      AS species_plant_type,
            species.morphology      AS species_morphology,
            species.culture         AS species_culture,
            species.uses            AS species_uses,
            species.melliferous_level     AS species_melliferous_level,
            species.ornamental_interest   AS species_ornamental_interest,
            species.lifespan_min          AS species_lifespan_min,
            species.lifespan_max          AS species_lifespan_max,
            species.height_min            AS species_height_min,
            species.height_max            AS species_height_max
        FROM plants
        JOIN species ON plants.species_id = species.id
        WHERE plants.id = ?
        """,
        (plant_id,),
    ).fetchone()

    if plant is None:
        return "Plant introuvable", 404

    return render_template("plant_detail.html", plant=plant)

@app.route("/plants/<int:plant_id>/edit", methods=["GET", "POST"])
def plant_edit(plant_id):
    db = get_db()

    # Récupérer l'individu + un minimum de contexte espèce
    plant = db.execute(
        """
        SELECT
            plants.*,
            species.common_name,
            species.variety_name,
            species.latin_name
        FROM plants
        JOIN species ON plants.species_id = species.id
        WHERE plants.id = ?
        """,
        (plant_id,),
    ).fetchone()

    if plant is None:
        return "Individu introuvable", 404

    if request.method == "POST":
        label   = request.form.get("label") or None
        zone    = request.form.get("zone") or None
        notes   = request.form.get("notes") or None

        lat_raw = (request.form.get("lat") or "").strip()
        lon_raw = (request.form.get("lon") or "").strip()
        alt_raw = (request.form.get("altitude") or "").strip()

        tags    = request.form.get("tags") or None
        micro   = request.form.get("micro_site") or None
        expo    = request.form.get("exposure_local") or None
        soil    = request.form.get("soil_local") or None
        h_raw   = (request.form.get("height_current") or "").strip()

        acq_type   = request.form.get("acquisition_type") or None
        acq_source = request.form.get("acquisition_source") or None
        plantnet   = request.form.get("plantnet_obs_id") or None
        status     = request.form.get("status") or None
        care_notes = request.form.get("care_notes") or None

        image_local = request.form.get("image_local") or None

        def to_float(x):
            try:
                return float(x) if x else None
            except ValueError:
                return None

        lat = to_float(lat_raw)
        lon = to_float(lon_raw)
        alt = to_float(alt_raw)
        height_current = to_float(h_raw)

        db.execute(
            """
            UPDATE plants
            SET
              label = ?,
              zone = ?,
              lat = ?,
              lon = ?,
              altitude = ?,
              notes = ?,
              tags = ?,
              micro_site = ?,
              exposure_local = ?,
              soil_local = ?,
              height_current = ?,
              acquisition_type = ?,
              acquisition_source = ?,
              plantnet_obs_id = ?,
              status = ?,
              care_notes = ?,
              image_local = ?
            WHERE id = ?
            """,
            (
                label,
                zone,
                lat,
                lon,
                alt,
                notes,
                tags,
                micro,
                expo,
                soil,
                height_current,
                acq_type,
                acq_source,
                plantnet,
                status,
                care_notes,
                image_local,
                plant_id,
            ),
        )
        db.commit()

        return redirect(url_for("plant_detail", plant_id=plant_id))

    # GET : afficher le formulaire pré-rempli
    return render_template("plant_form.html", plant=plant)

@app.route("/species")
def species_list():
    db = get_db()
    q = (request.args.get("q") or "").strip()

    base_sql = """
        SELECT
            s.family,
            s.genus,
            s.latin_name,
            s.common_name,
            s.image_url,
            COUNT(DISTINCT s.variety_name) AS variety_count,
            COUNT(DISTINCT p.id)          AS plant_count
        FROM species AS s
        LEFT JOIN plants AS p ON p.species_id = s.id
    """

    where = ""
    params = []

    if q:
        where = """
        WHERE
            s.family       LIKE ?
            OR s.genus     LIKE ?
            OR s.common_name  LIKE ?
            OR s.variety_name LIKE ?
            OR s.latin_name   LIKE ?
        """
        term = f"%{q}%"
        params = [term] * 5

    group_order = """
        GROUP BY
            s.family,
            s.genus,
            s.latin_name,
            s.common_name,
            s.image_url
        ORDER BY
            s.family,
            s.genus,
            s.latin_name
    """

    rows = db.execute(base_sql + where + group_order, params).fetchall()

    # Construction de la hiérarchie Famille → Genres → Espèces
    families = []
    current_family = None
    current_genus = None
    family_block = None
    genus_block = None

    for r in rows:
        fam_name = r["family"] or "Famille non renseignée"
        gen_name = r["genus"] or "Genre non renseigné"

        if family_block is None or fam_name != current_family:
            family_block = {
                "family": fam_name,
                "genera": []
            }
            families.append(family_block)
            current_family = fam_name
            current_genus = None
            genus_block = None

        if genus_block is None or gen_name != current_genus:
            genus_block = {
                "genus": gen_name,
                "items": []
            }
            family_block["genera"].append(genus_block)
            current_genus = gen_name

        # On pousse la ligne telle quelle dans items (image_url incluse)
        genus_block["items"].append(dict(r))

    return render_template("species_list.html", families=families, search=q)

@app.route("/species/<path:latin_name>")
def species_detail(latin_name):
    """
    Détail d'une espèce botanique :
    - fiche botanique (famille, genre, latin)
    - liste des cultivars (lignes de species)
    - liste des individus plantés (lignes de plants)
    """
    db = get_db()

    # Toutes les lignes de species correspondant à cette espèce
    variants = db.execute(
        """
        SELECT *
        FROM species
        WHERE latin_name = ?
        ORDER BY variety_name, common_name
        """,
        (latin_name,),
    ).fetchall()

    if not variants:
        return "Espèce introuvable", 404

    base = variants[0]  # fiche de référence

    # Tous les individus du jardin reliés à cette espèce
    plants = db.execute(
        """
        SELECT
            plants.*,
            species.common_name,
            species.variety_name
        FROM plants
        JOIN species ON plants.species_id = species.id
        WHERE species.latin_name = ?
        ORDER BY species.variety_name, plants.label
        """,
        (latin_name,),
    ).fetchall()

    return render_template(
        "species_detail.html",
        base=base,
        variants=variants,
        plants=plants,
    )

@app.route("/species/new", methods=["GET", "POST"])
def species_new():
    """
    Création d'une nouvelle espèce (avec éventuellement un premier cultivar).
    """
    db = get_db()
    error = None
    form_data = {}

    if request.method == "POST":
        common_name = (request.form.get("common_name") or "").strip() or None
        variety_name = (request.form.get("variety_name") or "").strip() or None
        latin_name = (request.form.get("latin_name") or "").strip() or None
        family = (request.form.get("family") or "").strip() or None
        genus = (request.form.get("genus") or "").strip() or None
        strata = (request.form.get("strata") or "").strip() or None
        tags = (request.form.get("tags") or "").strip() or None
        notes = (request.form.get("notes") or "").strip() or None
        image_url = (request.form.get("image_url") or "").strip() or None

        form_data = dict(
            common_name=common_name or "",
            variety_name=variety_name or "",
            latin_name=latin_name or "",
            family=family or "",
            genus=genus or "",
            strata=strata or "",
            tags=tags or "",
            notes=notes or "",
            image_url=image_url or "",
        )

        # validation : on exige un nom latin (clé taxonomique)
        if not latin_name:
            error = "Il faut renseigner un nom latin (clé taxonomique)."
        else:
            db.execute(
                """
                INSERT INTO species
                  (common_name, variety_name, latin_name,
                   family, genus, strata, tags, notes, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    common_name,
                    variety_name,
                    latin_name,
                    family,
                    genus,
                    strata,
                    tags,
                    notes,
                    image_url,
                ),
            )
            db.commit()

            return redirect(url_for("species_detail", latin_name=latin_name))

    return render_template("species_new.html", error=error, form=form_data)

@app.route("/species/<path:latin_name>/edit", methods=["GET", "POST"])
def species_edit(latin_name):
    """
    Page d'édition d'une espèce :
    - modification des champs communs (famille, genre, strate, tags, notes, image_url)
    - ajout d'un cultivar (nouvelle ligne dans species)
    - ajout d'un individu (nouvelle ligne dans plants, reliée à un cultivar existant)
    - suppression d'un cultivar (si aucun individu associé)
    - suppression de l'espèce entière (si aucun individu associé à aucun cultivar)
    """
    db = get_db()
    error = None

    # On récupère les cultivars avec le nombre d'individus associés pour chacun
    variants = db.execute(
        """
        SELECT
            s.*,
            COUNT(p.id) AS plant_count
        FROM species AS s
        LEFT JOIN plants AS p ON p.species_id = s.id
        WHERE s.latin_name = ?
        GROUP BY s.id
        ORDER BY s.variety_name, s.common_name
        """,
        (latin_name,),
    ).fetchall()

    if not variants:
        return "Espèce introuvable", 404

    base = variants[0]  # fiche de référence

    if request.method == "POST":
        action = request.form.get("action")

        # 1) Mise à jour des champs communs
        # 1) Mise à jour des champs communs
        if action == "update_base":
            family       = request.form.get("family") or None
            genus        = request.form.get("genus") or None
            strata       = request.form.get("strata") or None
            tags         = request.form.get("tags") or None
            notes        = request.form.get("notes") or None
            image_url    = request.form.get("image_url") or None

            origin       = request.form.get("origin") or None
            plant_type   = request.form.get("plant_type") or None
            morphology   = request.form.get("morphology") or None
            culture      = request.form.get("culture") or None
            uses         = request.form.get("uses") or None
            melliferous  = request.form.get("melliferous_level") or None
            ornamental   = request.form.get("ornamental_interest") or None

            lifespan_min = request.form.get("lifespan_min") or None
            lifespan_max = request.form.get("lifespan_max") or None
            height_min   = request.form.get("height_min") or None
            height_max   = request.form.get("height_max") or None

            # Cast simple pour les nombres
            def to_int(x):
                try:
                    return int(x) if x is not None and x != "" else None
                except ValueError:
                    return None

            def to_float(x):
                try:
                    return float(x) if x is not None and x != "" else None
                except ValueError:
                    return None

            lifespan_min = to_int(lifespan_min)
            lifespan_max = to_int(lifespan_max)
            height_min   = to_float(height_min)
            height_max   = to_float(height_max)

            db.execute(
                """
                UPDATE species
                SET
                  family = ?,
                  genus = ?,
                  strata = ?,
                  tags = ?,
                  notes = ?,
                  image_url = ?,
                  origin = ?,
                  plant_type = ?,
                  morphology = ?,
                  culture = ?,
                  uses = ?,
                  melliferous_level = ?,
                  ornamental_interest = ?,
                  lifespan_min = ?,
                  lifespan_max = ?,
                  height_min = ?,
                  height_max = ?
                WHERE latin_name = ?
                """,
                (
                    family,
                    genus,
                    strata,
                    tags,
                    notes,
                    image_url,
                    origin,
                    plant_type,
                    morphology,
                    culture,
                    uses,
                    melliferous,
                    ornamental,
                    lifespan_min,
                    lifespan_max,
                    height_min,
                    height_max,
                    latin_name,
                ),
            )
            db.commit()
            return redirect(url_for("species_edit", latin_name=latin_name))

        # 2) Ajout d'un cultivar
        elif action == "add_cultivar":
            common_name = request.form.get("common_name") or base["common_name"]
            variety_name = request.form.get("variety_name") or None
            c_tags = request.form.get("c_tags") or None
            c_notes = request.form.get("c_notes") or None

            db.execute(
                """
                INSERT INTO species
                  (common_name, variety_name, latin_name,
                   family, genus, strata, tags, notes, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    common_name,
                    variety_name,
                    latin_name,
                    base["family"],
                    base["genus"],
                    base["strata"],
                    c_tags,
                    c_notes,
                    base["image_url"],
                ),
            )
            db.commit()
            return redirect(url_for("species_edit", latin_name=latin_name))

                # 3) Ajout d'un individu (plant)
        elif action == "add_plant":
            species_id = request.form.get("species_id")
            label_user = (request.form.get("label") or "").strip()
            zone = request.form.get("zone") or None
            planted_at = request.form.get("planted_at") or None
            lat_str = (request.form.get("lat") or "").strip()
            lon_str = (request.form.get("lon") or "").strip()
            notes_p = request.form.get("notes_p") or None

            try:
                lat = float(lat_str) if lat_str else None
            except ValueError:
                lat = None
            try:
                lon = float(lon_str) if lon_str else None
            except ValueError:
                lon = None

            if species_id:
                species_id_int = int(species_id)

                # Si aucun label saisi → on génère XXX-YYY-NNN
                if label_user:
                    label = label_user
                else:
                    label = generate_label(db, species_id_int)

                db.execute(
                    """
                    INSERT INTO plants
                      (species_id, label, lat, lon, zone, planted_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (species_id_int, label, lat, lon, zone, planted_at, notes_p),
                )
                db.commit()

            return redirect(url_for("species_edit", latin_name=latin_name))

        # 4) Suppression d'un cultivar
        elif action == "delete_variant":
            variant_id = request.form.get("variant_id")
            if variant_id:
                # Sécurité côté serveur : on recompte les individus
                row = db.execute(
                    "SELECT COUNT(*) AS c FROM plants WHERE species_id = ?",
                    (variant_id,),
                ).fetchone()
                if row["c"] > 0:
                    error = f"Impossible de supprimer ce cultivar : il existe encore {row['c']} individu(s) planté(s) associé(s)."
                else:
                    db.execute("DELETE FROM species WHERE id = ?", (variant_id,))
                    db.commit()
                    return redirect(url_for("species_edit", latin_name=latin_name))

        # 5) Suppression de l'espèce entière
        elif action == "delete_species":
            ids_rows = db.execute(
                "SELECT id FROM species WHERE latin_name = ?",
                (latin_name,),
            ).fetchall()
            id_list = [r["id"] for r in ids_rows]
            if not id_list:
                return redirect(url_for("species_list"))

            placeholders = ",".join("?" * len(id_list))
            row = db.execute(
                f"SELECT COUNT(*) AS c FROM plants WHERE species_id IN ({placeholders})",
                id_list,
            ).fetchone()

            if row["c"] > 0:
                error = f"Impossible de supprimer cette espèce : il existe encore {row['c']} individu(s) planté(s) associé(s)."
            else:
                db.execute("DELETE FROM species WHERE latin_name = ?", (latin_name,))
                db.commit()
                return redirect(url_for("species_list"))

    # Recharger les variants et les individus après modifs
    variants = db.execute(
        """
        SELECT
            s.*,
            COUNT(p.id) AS plant_count
        FROM species AS s
        LEFT JOIN plants AS p ON p.species_id = s.id
        WHERE s.latin_name = ?
        GROUP BY s.id
        ORDER BY s.variety_name, s.common_name
        """,
        (latin_name,),
    ).fetchall()

    plants = db.execute(
        """
        SELECT
            plants.*,
            species.common_name,
            species.variety_name
        FROM plants
        JOIN species ON plants.species_id = species.id
        WHERE species.latin_name = ?
        ORDER BY species.variety_name, plants.label
        """,
        (latin_name,),
    ).fetchall()

    return render_template(
        "species_edit.html",
        base=base,
        variants=variants,
        plants=plants,
        error=error,
    )

@app.route("/map")
def garden_map():
    """Vue par zones (pseudo-carte + vraie carte Leaflet)."""
    db = get_db()
    rows = db.execute(
        """
        SELECT
            plants.id,
            plants.label,
            plants.zone,
            plants.lat,
            plants.lon,
            species.common_name,
            species.variety_name
        FROM plants
        JOIN species ON plants.species_id = species.id
        ORDER BY plants.zone, species.common_name
        """
    ).fetchall()

    # Conversion Row -> dict pour que tojson fonctionne
    plants = [dict(r) for r in rows]

    return render_template("map.html", plants=plants)


import os

if __name__ == "__main__":
# <<<<<<< HEAD
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)
# =======
    port = int(os.environ.get("PORT", 5001))  # 5001 en local, PORT imposé sur Render
    app.run(host="0.0.0.0", port=port, debug=True)
