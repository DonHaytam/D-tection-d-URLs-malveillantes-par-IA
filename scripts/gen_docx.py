"""Generate the professional article-style DOCX report for Phishing AI Master 2."""
import os
import tempfile

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional dependency
    Image = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "reports", "RAPPORT_FINAL_MASTER_IA.docx")

# ----------------------------- Theme -----------------------------
# Black-and-white academic article design: only black, white and greys.
BLACK = RGBColor(0, 0, 0)
DARK = RGBColor(35, 35, 35)
GRAY = RGBColor(90, 90, 90)
WHITE = RGBColor(255, 255, 255)

NAVY = BLACK
TEAL = DARK
RED = DARK
AMBER = DARK
GREEN = DARK

NAVY_HEX = "D9D9D9"
TEAL_HEX = "BFBFBF"
LIGHT_HEX = "F2F2F2"
ALT_HEX = "F7F7F7"
AMBER_HEX = "F2F2F2"
RED_HEX = "F2F2F2"
GREEN_HEX = "F2F2F2"

doc = Document()

# ----------------------------- Page setup -----------------------------
for section in doc.sections:
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)
    section.header_distance = Inches(0.35)
    section.footer_distance = Inches(0.35)

# ----------------------------- Styles -----------------------------
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)
normal.font.color.rgb = DARK
normal.paragraph_format.line_spacing = 1.16
normal.paragraph_format.space_after = Pt(6)

for name, size, color, before, after in [
    ("Heading 1", 16, NAVY, 14, 6),
    ("Heading 2", 12.5, TEAL, 10, 4),
    ("Heading 3", 11, NAVY, 8, 3),
    ("Heading 4", 10.5, DARK, 6, 2),
]:
    style = doc.styles[name]
    style.font.name = "Calibri"
    style.font.size = Pt(size)
    style.font.bold = True
    style.font.color.rgb = color
    style.paragraph_format.space_before = Pt(before)
    style.paragraph_format.space_after = Pt(after)
    style.paragraph_format.keep_with_next = True

# ----------------------------- Helpers -----------------------------
def shade_element(element, fill):
    pr = element.get_or_add_pPr() if hasattr(element, "get_or_add_pPr") else element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pr.append(shd)


def shade_paragraph(paragraph, fill):
    shade_element(paragraph._p, fill)


def shade_cell(cell, fill):
    shade_element(cell._tc, fill)


def set_run(run, size=10.5, bold=False, italic=False, color=None, font="Calibri"):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    return run


def para(text="", size=10.5, bold=False, italic=False, color=None,
         align=None, space_after=6, fill=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    if text:
        set_run(p.add_run(text), size=size, bold=bold, italic=italic, color=color)
    if fill:
        shade_paragraph(p, fill)
    return p


def bullet(text, level=0, size=10.5):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Inches(0.22 + 0.22 * level)
    p.paragraph_format.space_after = Pt(3)
    set_run(p.add_run(text), size=size)
    return p


def add_table(headers, rows, widths=None, font=9, header_fill=NAVY_HEX):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = ""
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.space_before = Pt(1)
        set_run(p.add_run(str(header)), size=font, bold=True, color=DARK)
        shade_cell(cell, header_fill)

    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for col_index, value in enumerate(row):
            if col_index >= len(cells):
                continue
            cell = cells[col_index]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.space_before = Pt(1)
            set_run(p.add_run("" if value is None else str(value)), size=font)
            if row_index % 2 == 1:
                shade_cell(cell, ALT_HEX)

    if widths:
        for col_index, width in enumerate(widths):
            for row in table.rows:
                row.cells[col_index].width = Inches(width)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def callout(title, text, tone="info"):
    fill = {"info": LIGHT_HEX, "warn": AMBER_HEX, "blocked": RED_HEX, "ok": GREEN_HEX}[tone]
    color = {"info": NAVY, "warn": AMBER, "blocked": RED, "ok": GREEN}[tone]
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(8)
    set_run(p.add_run(title + " — "), size=10, bold=True, color=color)
    set_run(p.add_run(text), size=10)
    shade_paragraph(p, fill)
    return p


def add_figure(path, caption, number):
    if os.path.exists(path):
        insert_path = path
        temp_path = None
        if Image is not None:
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    temp_path = tmp.name
                Image.open(path).convert("L").save(temp_path)
                insert_path = temp_path
            except Exception:
                insert_path = path
        doc.add_picture(insert_path, width=Inches(5.9))
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run(p.add_run(f"Figure {number} — {caption}"), size=9, italic=True, color=GRAY)
        p.paragraph_format.space_after = Pt(10)
    else:
        para(f"[Figure {number} — {caption} : fichier non trouvé]", size=9, italic=True, color=GRAY)


def add_toc_entry(text, level=0):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.18 * level)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.6), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    set_run(p.add_run(text), size=10 if level == 0 else 9.5,
            bold=(level == 0), color=NAVY if level == 0 else GRAY)
    p.add_run("\t").font.size = Pt(9.5)
    set_run(p.add_run(""), size=9.5)
    return p


def add_page_number(paragraph):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, separate, text, end):
        run._r.append(element)
    return run


for section in doc.sections:
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run(header.add_run("Phishing AI Master 2 — Rapport final"), size=8.5, color=GRAY)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(footer.add_run("Master 2 IA & Cybersécurité  |  "), size=8.5, color=GRAY)
    add_page_number(footer)

# ============================================================
# PAGE DE GARDE
# ============================================================
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(24)
set_run(p.add_run("MASTER 2 — INTELLIGENCE ARTIFICIELLE ET CYBERSÉCURITÉ"),
        size=9.5, bold=True, color=GRAY)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(24)
p.paragraph_format.space_after = Pt(8)
set_run(p.add_run("Détection intelligente des URL de phishing"), size=22, bold=True, color=NAVY)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(p.add_run("et malveillantes par Intelligence Artificielle"), size=22, bold=True, color=NAVY)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(20)
set_run(p.add_run("Rapport final d'articlisation, d'audit et de validation du projet"),
        size=13, color=TEAL)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(18)
set_run(p.add_run("OUTIL EXPÉRIMENTAL  •  34 TESTS RÉUSSIS  •  DÉPLOIEMENT MANUEL"),
        size=9, bold=True, color=GRAY)

add_table(
    ["Champ", "Valeur"],
    [
        ["Auteur", "Projet Master 2 IA"],
        ["Date", "26 novembre 2026"],
        ["Modèle retenu", "M1_LR_HARDNEG"],
        ["Environnement", "Windows, Python 3.10, CPU uniquement"],
        ["Interface active", "HTML/CSS/JS statique via python -m http.server, port 8501"],
        ["Statut du modèle", "production_gate = BLOCKED (metadata.json)"],
    ],
    widths=[1.7, 4.8], font=10,
)

callout("Note de périmètre",
        "Ce document décrit le projet, ses conditions, ses résultats et l'ensemble des travaux réalisés. "
        "Aucune opération de publication distante n'est décrite.", "info")

doc.add_page_break()

# ============================================================
# SOMMAIRE
# ============================================================
doc.add_heading("Sommaire", level=1)
toc = [
    ("0. Résumé", 0),
    ("1. Synthèse exécutive", 0),
    ("2. Conditions et contraintes du projet", 0),
    ("3. Présentation détaillée du projet", 0),
    ("   3.1 Contexte et problématique", 1),
    ("   3.2 Objectifs et périmètre", 1),
    ("   3.3 Architecture générale", 1),
    ("   3.4 Pile technologique", 1),
    ("4. État de l'art et choix méthodologiques", 0),
    ("5. Collecte et préparation des données", 0),
    ("6. Méthodologie de modélisation", 0),
    ("7. Résultats expérimentaux", 0),
    ("8. Application, API et interface", 0),
    ("9. Audit, corrections et travaux réalisés", 0),
    ("   9.1 Sécurisation de la couche de production", 1),
    ("   9.2 Durcissement du Laboratoire", 1),
    ("   9.3 Pipeline de feedback et apprentissage", 1),
    ("   9.4 Dérive de domaines et PSI", 1),
    ("   9.5 Tests A/B", 1),
    ("   9.6 Active Learning", 1),
    ("   9.7 Réentraînement", 1),
    ("   9.8 Monitoring et distribution des scores", 1),
    ("   9.9 Correctifs d'exécution frontend et API", 1),
    ("10. Sécurité et conformité", 0),
    ("11. Validation, tests et reproductibilité", 0),
    ("12. Limites factuelles observées", 0),
    ("13. Conclusion", 0),
    ("14. Bibliographie", 0),
    ("15. Annexes", 0),
]
for text, level in toc:
    add_toc_entry(text, level)

doc.add_page_break()

# ============================================================
# 0. RESUME
# ============================================================
doc.add_heading("0. Résumé", level=1)
para("Ce rapport présente le projet Phishing AI Master 2 sous forme d'article technique complet : contexte, "
     "conditions de réalisation, données, méthodes, résultats, application opérationnelle, audit de qualité "
     "et travaux correctifs. Le système détecte les URL de phishing par analyse passive de la chaîne de "
     "caractères, sans visiter les sites, sans résolution DNS et sans requête HTTP vers les URL soumises.")
para("Six familles de modèles ont été entraînées et comparées sur un corpus nettoyé de 159 568 URL. Le modèle "
     "retenu est M1_LR_HARDNEG : régression logistique sur des n-grammes de caractères TF-IDF (3–5), améliorée "
     "par hard-negative mining. Sur le jeu de validation DEV, il obtient un rappel de 0.8422, un FPR de 0.0381 "
     "et une ROC-AUC de 0.9610. Les cibles initiales — rappel ≥ 0.85 et FPR ≤ 0.01 — ne sont donc pas "
     "simultanément atteintes ; le statut reste BLOCKED pour un usage de production autonome.")
para("La partie application a ensuite été modifiée : API FastAPI, interface web, base SQLite, authentification, "
     "contrôle des origines, pipeline de feedback, monitoring, A/B testing, Active Learning et réentraînement "
     "supervisé. Les défauts d'exécution identifiés — signatures de fonctions désalignées, initialisation de "
     "base manquante, erreur JavaScript refreshLab is not defined, erreur bins.map is not a function, dérive "
     "de domaines mal interprétée, gagnant A/B déclaré trop tôt — ont été corrigés et couverts par des tests. "
     "La suite complète comporte 34 tests réussis, et l'artefact du modèle conserve son empreinte inchangée.")
para("Mots-clés : phishing, détection d'URL, machine learning, TF-IDF, n-grammes de caractères, régression "
     "logistique, hard-negative mining, calibration, monitoring, dérive de domaines, PSI, feedback, A/B testing, "
     "Active Learning.", italic=True, color=GRAY)

callout("Abstract",
        "This report documents the complete Phishing AI Master 2 project: assumptions, dataset, methodology, "
        "experimental comparison, operational application, security constraints, audit findings and corrective "
        "work. The selected model is M1_LR_HARDNEG. All 34 regression tests pass and the model checksum is unchanged.",
        "info")

# ============================================================
# 1. SYNTHESE
# ============================================================
doc.add_heading("1. Synthèse exécutive", level=1)
para("Le projet comporte quatre couches : données, modélisation, inférence et exploitation.")
add_table(
    ["Dimension", "Résultat vérifié", "Lecture"],
    [
        ["Corpus nettoyé", "159 568 URL", "Jeu équilibré après déduplication"],
        ["Domaines registrables", "96 155", "Split domain-disjoint"],
        ["Meilleur modèle", "M1_LR_HARDNEG", "FPR le plus faible et AUC élevée"],
        ["Rappel DEV", "0.8422", "Inférieur à la cible 0.85"],
        ["FPR DEV", "0.0381", "Supérieur à la cible 0.01"],
        ["ROC-AUC DEV", "0.9610", "Valeur mesurée sur le jeu DEV"],
        ["Seuils opérationnels", "0.25 / 0.75", "Inchangés"],
        ["Tests", "34 / 34 réussis", "Suite de régression verte"],
        ["Empreinte modèle", "388d774e…a2e99202", "Inchangée"],
        ["Déploiement", "MANUAL APPROVAL", "Aucun remplacement automatique"],
    ],
    widths=[1.5, 1.8, 3.2], font=9,
)
callout("Constat vérifié",
        "Le modèle sélectionné ne satisfait pas les deux objectifs de production en même temps. Le champ "
        "production_gate du fichier models/versions/metadata.json vaut BLOCKED.", "warn")

doc.add_heading("1.1 État opérationnel observé", level=2)
para("Les valeurs ci-dessous constituent un instantané de la base locale au 26 novembre 2026. Elles évoluent "
     "avec l'usage de l'application.")
add_table(
    ["Indicateur", "Valeur observée", "Interprétation"],
    [
        ["Prédictions enregistrées", "115", "Volume de test local"],
        ["Prédictions avec feedback", "6", "Retours vérifiés disponibles"],
        ["Retours corrects / incorrects", "5 / 1", "Taux d'erreur : 16,67 % sur 6 retours"],
        ["Fenêtre monitoring", "7 jours", "115 prédictions courantes, 0 précédente"],
        ["PSI", "indisponible", "Pas de distribution de référence valide"],
        ["Dérive de domaines", "insufficient_data", "Aucune baseline historique"],
        ["File Active Learning", "0 élément", "Aucun score dans [0.4 ; 0.6] sans feedback"],
        ["Gagnant A/B", "insufficient_data", "6 retours pour M1, 0 pour Ensemble ; seuil = 20"],
        ["Seuil d'alerte incorrect", "5 %", "Avec minimum 20 retours"],
    ],
    widths=[1.8, 1.6, 3.1], font=9,
)

# ============================================================
# 2. CONDITIONS
# ============================================================
doc.add_heading("2. Conditions et contraintes du projet", level=1)
para("Le travail a été réalisé sous un jeu de conditions strictes. Aucune n'a été assouplie pour obtenir un "
     "résultat plus favorable.")
add_table(
    ["#", "Condition imposée", "État", "Détail de conformité"],
    [
        ["1", "Conserver M1_LR_HARDNEG", "Respectée", "Modèle chargé et artefact non modifiés"],
        ["2", "Conserver la régression logistique", "Respectée", "LogisticRegression conservée"],
        ["3", "Conserver TF-IDF caractères 3–5", "Respectée", "min_df=3, max_features=20000"],
        ["4", "Conserver les seuils 0.25 et 0.75", "Respectée", "<0.25 LEGITIMATE ; 0.25–<0.75 NEEDS_REVIEW ; ≥0.75 PHISHING"],
        ["5", "Conserver les labels 0 et 1", "Respectée", "0 = legitimate, 1 = phishing"],
        ["6", "Conserver l'empreinte du modèle", "Respectée", "388d774e…a2e99202"],
        ["7", "Préserver TRAIN / DEV / LOCKED_TEST / INDEPENDENT", "Respectée", "Découpage par domaine registrable conservé"],
        ["8", "Ne jamais entraîner sur les jeux verrouillés", "Respectée", "Jeux exclus de l'entraînement et du réglage"],
        ["9", "Aucune visite d'URL, DNS ou HTTP vers l'URL", "Respectée", "Analyse textuelle passive uniquement"],
        ["10", "Aucun déploiement automatique", "Respectée", "Validation manuelle obligatoire"],
        ["11", "Aucune donnée fabriquée", "Respectée", "Statuts insufficient_data explicites"],
        ["12", "Aucun secret ni base privée exposée", "Respectée", "Configuration sensible hors livrable"],
        ["13", "Ne pas modifier l'artefact du modèle", "Respectée", "Checksum vérifié avant et après"],
        ["14", "Ne pas confondre score moyen et exactitude", "Respectée", "Distribution présentée sans prétention accuracy"],
        ["15", "Ne pas déclarer 100 % de dérive sans baseline", "Respectée", "insufficient_data si historique vide"],
        ["16", "Ne pas déclarer un gagnant A/B sur un retour", "Respectée", "Minimum 20 retours vérifiés"],
        ["17", "Suite de tests verte avant livraison", "Respectée", "34 tests réussis"],
    ],
    widths=[0.3, 1.9, 0.9, 3.4], font=8.2,
)
callout("Cahier des charges",
        "Ces conditions expliquent plusieurs décisions volontairement conservatrices : mains sur le modèle, "
        "seuils non réécrits, statuts d'insuffisance plutôt que valeurs artificielles, et blocage du "
        "déploiement automatique.", "info")

# ============================================================
# 3. PROJET
# ============================================================
doc.add_heading("3. Présentation détaillée du projet", level=1)

doc.add_heading("3.1 Contexte et problématique", level=2)
para("Le phishing est une forme d'ingénierie sociale qui exploite la confiance de l'utilisateur. Une URL "
     "trompeuse peut imiter une banque, une messagerie ou un service de paiement afin de collecter des "
     "identifiants. La détection automatique doit fonctionner sans accès réseau à l'URL soumise. La "
     "généralisation à des domaines jamais vus est évaluée par le découpage domain-disjoint.")
para("La problématique centrale est la suivante : comment construire un détecteur d'URL malveillantes qui "
     "atteigne un rappel élevé sans produire un nombre inacceptable de faux positifs, tout en généralisant "
     "à des domaines inconnus ?")
bullet("Tension rappel / faux positifs : augmenter la sensibilité augmente souvent les fausses alertes.")
bullet("Tension signal lexical / généralisation : les tokens de marque peuvent devenir des raccourcis fragiles.")

doc.add_heading("3.2 Objectifs et périmètre", level=2)
for item in [
    "Construire un pipeline de données reproductible.",
    "Entraîner et comparer six modèles.",
    "Sélectionner le meilleur candidat sur des critères mesurés.",
    "Développer une application fonctionnelle autour du modèle.",
    "Documenter honnêtement les limites.",
    "Durcir l'exploitation : feedback, monitoring, A/B, Active Learning, réentraînement contrôlé.",
]:
    bullet(item)
para("Le périmètre fonctionnel final couvre la prédiction unitaire et par lot, l'affichage du verdict et du "
     "score, l'historique, le feedback avec règle « dernier retour gagnant », le monitoring de dérive, "
     "l'A/B testing, la file d'Active Learning et le réentraînement contrôlé.")

doc.add_heading("3.3 Architecture générale", level=2)
add_table(
    ["Couche", "Rôle principal"],
    [
        ["src/data/", "Ingestion, validation, déduplication, splitting, provenance"],
        ["src/features/", "Parsing URL, features lexicales, structurelles et TF-IDF"],
        ["src/models/", "Modèles M1–M6 et registre"],
        ["src/evaluation/", "Métriques, calibration, seuils"],
        ["src/inference/", "Chargeur de modèle et prédicteur"],
        ["src/policy/", "Politique de décision à trois états"],
        ["src/storage/", "Base SQLite, feedback, monitoring, drift, A/B, Active Learning"],
        ["src/retraining/", "Éligibilité, exclusions, garde-fous"],
        ["deployment/api/", "API FastAPI"],
        ["deployment/frontend/", "Interface web"],
        ["database/", "Base locale SQLite"],
        ["reports/", "Rapports techniques, figures et tables"],
    ],
    widths=[1.7, 4.8], font=9,
)

doc.add_heading("3.4 Pile technologique", level=2)
add_table(
    ["Composant", "Version / choix"],
    [["Python", "3.10"], ["scikit-learn", "1.7.2"], ["pandas", "2.3.3"], ["numpy", "2.2.6"],
     ["FastAPI", "0.142.2"],
     ["Interface active", "HTML/CSS/JS statique via python -m http.server (port 8501)"],
     ["XGBoost", "3.2.0"],
     ["LightGBM", "4.7.0 (vendorisé)"], ["Base", "SQLite locale"], ["Exécution", "CPU uniquement"]],
    widths=[2.1, 4.4], font=9,
)

# ============================================================
# 4. ETAT DE L'ART
# ============================================================
doc.add_heading("4. État de l'art et choix méthodologiques", level=1)
para("La détection d'URL malveillantes peut s'appuyer sur des signaux lexicaux (longueur, ponctuation, entropie), "
     "structurels (schéma, profondeur, paramètres), textuels (n-grammes de caractères) ou de réputation. "
     "Le projet exploite les trois premiers et écarte volontairement la réputation en ligne pour respecter "
     "la contrainte d'analyse passive.")
para("Le choix retenu combine TF-IDF de caractères et régression logistique. Le modèle est linéaire, "
     "interprétable et peu coûteux à exécuter. Les résultats comparatifs du chapitre 7 ne montrent pas "
     "d'amélioration simultanée du rappel et du FPR pour les autres modèles.")

# ============================================================
# 5. DONNEES
# ============================================================
doc.add_heading("5. Collecte et préparation des données", level=1)
doc.add_heading("5.1 Sources", level=2)
add_table(
    ["Source", "Type", "Taille", "Licence / restriction"],
    [["HuggingFace ealvaradob/phishing-dataset", "Mixte", "835 697 URL", "Licence à vérifier"],
     ["Tranco", "Légitime", "1 000 000 domaines", "CC BY 3.0 / 4.0"],
     ["PhishTank via Zenodo", "Phishing", "149 188 URL", "Conditions PhishTank"]],
    widths=[2.2, 1.1, 1.4, 1.8], font=9,
)
doc.add_heading("5.2 Nettoyage et composition", level=2)
for item in [
    "Déduplication exacte : 276 URL supprimées.",
    "Déduplication normalisée : 0 URL supplémentaire.",
    "Validation syntaxique : 156 URL invalides supprimées.",
    "Domaines avec labels contradictoires : 591 exclus de l'entraînement.",
    "Total après nettoyage : 159 568 URL, dont 79 842 légitimes et 79 726 phishing.",
]:
    bullet(item)
doc.add_heading("5.3 Séparation des jeux", level=2)
add_table(
    ["Split", "Taille", "Légitimes", "Phishing", "Usage autorisé"],
    [["TRAIN", "114 873", "58 221", "56 652", "Entraînement"],
     ["DEV", "22 586", "10 885", "11 701", "Réglage et comparaison"],
     ["LOCKED_TEST", "22 109", "10 736", "11 373", "Évaluation verrouillée"],
     ["INDEPENDENT_FINAL_TEST", "réservé", "—", "—", "Test final indépendant"]],
    widths=[1.5, 1.0, 1.0, 1.0, 2.0], font=8.8,
)
para("Le découpage est domain-disjoint : aucun domaine registrable ne traverse deux ensembles. Cette mesure "
     "réduit le risque de fuite et force le modèle à généraliser à des domaines inconnus.", italic=True)
doc.add_heading("5.4 Analyse exploratoire", level=2)
for item in [
    "URLs uniques observées avant nettoyage : 821 402.",
    "Hôtes uniques : 448 803.",
    "Longueur moyenne : 47,48 caractères.",
    "607 141 URL sans schéma, normalisées en https.",
    "TLD dominant : .com (486 714 occurrences).",
]:
    bullet(item)
add_figure(os.path.join(ROOT, "reports/figures/eda/fig01_class_distribution.png"),
           "Distribution des classes", 1)
add_figure(os.path.join(ROOT, "reports/figures/eda/fig02_url_length.png"),
           "Distribution de la longueur des URL", 2)
add_figure(os.path.join(ROOT, "reports/figures/eda/fig03_tld_distribution.png"),
           "Top 15 TLD", 3)
add_figure(os.path.join(ROOT, "reports/figures/eda/fig04_scheme_distribution.png"),
           "Distribution des schémas", 4)

# ============================================================
# 6. METHODOLOGIE
# ============================================================
doc.add_heading("6. Méthodologie de modélisation", level=1)
doc.add_heading("6.1 Représentation", level=2)
para("La représentation finale est un pipeline TF-IDF sur n-grammes de caractères de taille 3 à 5, avec "
     "min_df=3 et max_features=20000. Les n-grammes captent des motifs même lorsque l'URL est légèrement "
     "modifiée, contrairement à une tokenisation par mots trop sensible aux séparateurs.")
doc.add_heading("6.2 Modèles comparés", level=2)
add_table(
    ["Code", "Modèle", "Principe"],
    [["M1", "Régression logistique", "Baseline linéaire interprétable"],
     ["M2", "SVM linéaire", "Haute dimension, calibration nécessaire"],
     ["M3", "Random Forest", "Ensemble d'arbres"],
     ["M4", "Gradient Boosting", "Boosting séquentiel"],
     ["M5", "XGBoost", "Boosting régularisé"],
     ["M6", "Hybride", "TF-IDF + features numériques"],
     ["M1_HARDNEG", "M1 + hard-negative mining", "Candidat retenu"]],
    widths=[1.0, 2.0, 3.5], font=9,
)
doc.add_heading("6.3 Hard-negative mining, calibration et seuils", level=2)
para("Les faux positifs de DEV ont été réinjectés comme exemples difficiles pendant l'entraînement : le FPR "
     "est passé de 0.0548 à 0.0381. La calibration isotonique donne un Brier de 0.0761 et un ECE de 0.0000. "
     "Une expérience de seuil à 0.4774 atteint un rappel de 0.8500 mais avec un FPR de 0.0469 ; elle n'a pas "
     "été adoptée car elle ne respecte pas la cible FPR et modifierait la politique validée.")
add_table(
    ["Score", "Verdict"],
    [["< 0.25", "LEGITIMATE"], ["0.25 – < 0.75", "NEEDS_REVIEW"], ["≥ 0.75", "PHISHING"]],
    widths=[2.0, 4.5], font=10,
)

# ============================================================
# 7. RESULTATS
# ============================================================
doc.add_heading("7. Résultats expérimentaux", level=1)
doc.add_heading("7.1 Comparaison sur DEV", level=2)
add_table(
    ["Modèle", "Acc", "Prec", "Recall", "FPR", "F1", "AUC", "PR-AUC", "Brier", "ECE"],
    [["M1 LR", "0.8947", "0.9432", "0.8478", "0.0548", "0.8930", "0.9593", "0.9676", "0.0784", "0.0304"],
     ["M2 SVM", "0.8980", "0.9389", "0.8590", "0.0601", "0.8972", "0.9583", "0.9669", "0.0818", "0.0560"],
     ["M3 RF", "0.8764", "0.9018", "0.8545", "0.1000", "0.8775", "0.9440", "0.9551", "0.0902", "0.0116"],
     ["M4 GB", "0.8662", "0.9051", "0.8286", "0.0934", "0.8652", "0.9394", "0.9496", "0.0964", "0.0210"],
     ["M5 XGBoost", "0.8801", "0.9148", "0.8474", "0.0848", "0.8798", "0.9484", "0.9576", "0.0870", "0.0067"],
     ["M6 Hybrid", "0.8080", "0.8871", "0.7212", "0.0987", "0.7956", "0.8896", "0.9070", "0.1331", "0.0325"],
     ["M1_HARDNEG", "0.8998", "0.9596", "0.8422", "0.0381", "0.8970", "0.9610", "0.9695", "0.0770", "0.0370"]],
    widths=[0.95, 0.55, 0.55, 0.55, 0.5, 0.5, 0.55, 0.6, 0.55, 0.5], font=8,
)
doc.add_heading("7.2 Interprétation", level=2)
for item in [
    "M1_HARDNEG possède le FPR le plus bas et la ROC-AUC la plus élevée.",
    "M2 SVM obtient un rappel plus élevé mais paie un FPR plus important.",
    "M6 Hybride sous-performe : les features numériques n'apportent pas de gain ici.",
    "Le modèle retenu limite les faux positifs, mais le rappel reste sous la cible.",
]:
    bullet(item)
doc.add_heading("7.3 Analyse des faux positifs", level=2)
for item in [
    "TLD sous-représentés : .cn et .ar.",
    "URL courtes avec tokens de marque : login, bank, amazon, paypal.",
    "Schéma http : 21,9 % des faux positifs contre 3,1 % des légitimes.",
    "Allow-list Tranco top 10k : FPR 0.0298 mais rappel 0.8209, donc trop agressive.",
]:
    bullet(item)

# ============================================================
# 8. APPLICATION
# ============================================================
doc.add_heading("8. Application, API et interface", level=1)
doc.add_heading("8.1 API FastAPI", level=2)
add_table(
    ["Endpoint", "Méthode", "Rôle"],
    [["/health", "GET", "État du modèle, environnement, authentification, base"],
     ["/predict", "POST", "Prédiction unitaire et enregistrement"],
     ["/predict_batch", "POST", "Prédiction par lot"],
     ["/feedback", "POST", "Feedback ; 404 si prédiction absente"],
     ["/history", "GET", "Historique paginé"],
     ["/stats", "GET", "Statistiques globales"],
     ["/active-learning", "GET", "File des cas incertains"],
     ["/monitoring", "GET", "Monitoring, dérive, PSI, distribution"],
     ["/ab-test", "GET", "Résultats A/B"],
     ["/feedback/export", "GET", "Export CSV du feedback"],
     ["/retraining/status", "GET", "Runs et planification"],
     ["/retraining/run", "POST", "Lancement contrôlé (admin)"],
     ["/retraining/approve", "POST", "Approbation manuelle (admin)"],
     ["/retraining/schedule", "GET / POST", "Calendrier (admin)"],
     ["/ensemble", "GET", "Informations sur la variante Ensemble"]],
    widths=[1.7, 0.9, 3.9], font=8.6,
)
doc.add_heading("8.2 Interface web", level=2)
for item in [
    "Statistiques : volumes, verdicts, distribution des scores.",
    "Collecte et Réentraînement : feedback, éligibilité, exclusions, runs.",
    "Laboratoire : monitoring, A/B, Active Learning, dérive.",
    "Monitoring : alertes, PSI, distribution temporelle.",
    "A/B Testing : comparaison M1 / Ensemble.",
    "Active Learning : file priorisée des URL incertaines.",
]:
    bullet(item)
para("Le bouton de rafraîchissement du Laboratoire appelle une fonction refreshLab() explicite, et le script "
     "est chargé avec un paramètre de version (script.js?v=3) afin d'éviter le service d'une copie obsolète.")
callout("Précision importante",
        "Le lancement actuel utilisé par setup.bat ne démarre pas Streamlit. Il sert index.html et script.js "
        "avec le serveur HTTP intégré de Python sur http://localhost:8501. Un fichier "
        "deployment/frontend/app.py propose une variante Streamlit, mais il n'est pas utilisé par le script "
        "de démarrage décrit dans ce rapport.", "info")
doc.add_heading("8.3 Base de données", level=2)
add_table(
    ["Table", "Contenu"],
    [["predictions", "URL, verdict, score, variante, version, feedback, domaine, labels corrigés"],
     ["feedback", "Retours horodatés, règle du dernier retour gagnant"],
     ["retraining_runs", "Runs, compteurs d'éligibilité, détails"],
     ["monitoring_events", "Alertes et événements de surveillance"]],
    widths=[1.7, 4.8], font=9,
)
para("La base est initialisée au démarrage par une étape dédiée du script de lancement, ce qui supprime les "
     "erreurs de colonne manquante lors d'un premier démarrage.")

# ============================================================
# 9. TRAVAUX
# ============================================================
doc.add_heading("9. Audit, corrections et travaux réalisés", level=1)
para("Cette section constitue le journal technique des travaux réalisés après la livraison initiale. Chaque "
     "problème est présenté avec sa cause réelle et la correction appliquée.")

doc.add_heading("9.1 Sécurisation de la couche de production", level=2)
add_table(
    ["Avant", "Cause", "Après"],
    [["Authentification non imposée", "Démarrage trop permissif", "Authentification obligatoire en production"],
     ["Droits fins non appliqués", "Constantes de rôles déclarées sans clés distinctes", "Contrôle effectif par clé admin X-Admin-API-Key"],
     ["CORS potentiellement bloquant", "Origines frontend non couvertes", "Localhost 8501 et 8000 autorisés"],
     ["Explications trompeuses", "Texte généré sans preuve", "Explication désactivée"]],
    widths=[1.8, 1.9, 2.8], font=8.8,
)

doc.add_heading("9.2 Durcissement du Laboratoire", level=2)
para("Le tableau de bord agrège monitoring, A/B, Active Learning et réentraînement. Les compteurs de feedback, "
     "l'affichage des tailles d'échantillon, la dérive de domaines et le PSI ont été corrigés. Le résultat est "
     "une interface qui affiche valeur + taille d'échantillon + fenêtre + interprétation + statut de suffisance.")

doc.add_heading("9.3 Pipeline de feedback et apprentissage", level=2)
para("La chaîne de feedback a été réécrite selon le flux : prédiction, feedback, dernier retour gagnant, label "
     "vérifié, déduplication, exclusions, candidat d'entraînement.")
for item in [
    "Validation des labels correct, incorrect, unknown.",
    "Erreur explicite si la prédiction ciblée n'existe pas.",
    "Règle du dernier retour gagnant appliquée.",
    "Inférence du label selon le verdict et la correction.",
    "Compteurs d'exclusion : URL invalide, label manquant ou invalide, doublon, conflit, domaine réservé.",
    "Un retour manquant n'est jamais compté comme un retour correct.",
]:
    bullet(item)

doc.add_heading("9.4 Dérive de domaines et PSI", level=2)
para("La nouveauté de domaines a été séparée de la dérive statistique. Sans domaine historique, le statut est "
     "insufficient_data ; sans domaine courant, il est stable ; sinon le ratio est calculé. Le PSI utilise 10 "
     "bins égaux dans [0, 1]. Si la distribution de référence est vide, le PSI vaut null et le statut est "
     "insufficient_data. Aucune valeur artificielle n'est substituée.")

doc.add_heading("9.5 Tests A/B", level=2)
para("L'assignation 50/50 par hash du client_id est conservée. Chaque retour est attribué à la variante ayant "
     "réellement généré la prédiction. Un gagnant exige au moins 20 retours vérifiés par variante ; sinon le "
     "statut reste insufficient_data. Les métriques hors ligne du jeu DEV (rappel 0.8595, FPR 0.0345, AUC "
     "0.9714) restent une référence, jamais un motif de promotion automatique.")

doc.add_heading("9.6 Active Learning", level=2)
for item in [
    "Score dans [0.4 ; 0.6].",
    "Exclusion des URL déjà pourvues d'un feedback.",
    "Tri par incertitude : ABS(score - 0.5) ASC, puis récence.",
    "Déduplication des URL et des domaines.",
    "Aucun retour non vérifié traité comme vérité terrain.",
]:
    bullet(item)

doc.add_heading("9.7 Réentraînement", level=2)
para("Le pipeline n'entraîne que sur des candidats vérifiés : inférence de label, exclusion des doublons et "
     "conflits, exclusion des domaines chevauchant LOCKED_TEST, exclusion de toute appartenance à LOCKED_TEST "
     "ou INDEPENDENT, compteurs visibles, statut insufficient_data sous le minimum requis et approbation "
     "manuelle avant tout remplacement du modèle.")

doc.add_heading("9.8 Monitoring et distribution des scores", level=2)
para("Le monitoring vérifie le filtrage temporel et UTC, des bins couvrant [0, 1] sans chevauchement, la somme "
     "des bins égale au nombre de prédictions de la fenêtre, et la séparation entre distribution des scores "
     "et exactitude réelle.")
add_table(
    ["Bin", "Effectif"],
    [["0.0–0.1", "22"], ["0.1–0.2", "38"], ["0.2–0.3", "18"], ["0.3–0.4", "19"],
     ["0.4–0.5", "0"], ["0.5–0.6", "0"], ["0.6–0.7", "0"], ["0.7–0.8", "0"],
     ["0.8–0.9", "0"], ["0.9–1.0", "18"], ["Total", "115"]],
    widths=[2.5, 4.0], font=9,
)

doc.add_heading("9.9 Correctifs d'exécution frontend et API", level=2)
add_table(
    ["Symptôme observé", "Cause réelle", "Correction"],
    [["get_history() unexpected keyword 'limit'", "Signature désalignée", "Paramètres alignés"],
     ["get_feedback_rows() unexpected keyword 'limit'", "Signature incomplète", "Paramètre limit ajouté"],
     ["create_retraining_run() unexpected keyword 'trigger'", "Paramètres non acceptés", "Signature étendue"],
     ["update_retraining_run() unexpected keyword 'status'", "Paramètres non acceptés", "Signature étendue"],
     ["no such column: created_at", "Colonne inexistante interrogée", "Requêtes alignées sur le schéma"],
     ["refreshLab is not defined", "Fonction absente", "Fonction refreshLab() définie"],
     ["bins.map is not a function", "Dict au lieu d'un tableau", "renderHistogram() normalise les deux formats"],
     ["Ancien JavaScript servi", "Cache navigateur", "script.js?v=3"],
     ["Base non initialisée", "Étape absente du lancement", "Initialisation au démarrage"],
     ["Erreur CORS depuis localhost:8501", "Origine non autorisée", "Liste d'origines vérifiée"]],
    widths=[2.2, 1.9, 2.4], font=8.3,
)
callout("Garde-fou",
        "Tous ces correctifs ont été apportés sans toucher au modèle, aux features, aux seuils ni aux jeux "
        "verrouillés. L'empreinte du modèle est restée identique après chaque étape.", "ok")

doc.add_heading("9.10 Tableau récapitulatif des travaux", level=2)
add_table(
    ["Domaine", "Travail réalisé", "Résultat"],
    [["Sécurité", "Auth production, clé admin, CORS, lifecycle", "Contrôles configurés"],
     ["Feedback", "Dernier retour gagnant, validation, exclusions", "Pipeline traçable"],
     ["Dérive", "insufficient_data sans baseline", "Plus de fausse alerte 100 %"],
     ["PSI", "10 bins, comparaison référent/courant", "Calcul honnête ou null"],
     ["A/B", "Minimum 20 retours par variante", "Pas de gagnant sur bruit"],
     ["Active Learning", "Tri incertitude + récence", "File priorisée"],
     ["Réentraînement", "Filtres et approbation manuelle", "Aucun remplacement auto"],
     ["Monitoring", "UTC, bins, tailles d'échantillon", "Métriques interprétables"],
     ["Frontend", "refreshLab, renderHistogram, cache", "Erreurs JS supprimées"],
     ["API / base", "Signatures alignées, init DB", "Erreurs supprimées"],
     ["Tests", "34 tests de régression", "Suite verte"],
     ["Modèle", "Artefact non modifié", "Checksum conservé"]],
    widths=[1.4, 3.2, 1.9], font=8.6,
)

# ============================================================
# 10. SECURITE
# ============================================================
doc.add_heading("10. Sécurité et conformité", level=1)
add_table(
    ["Exigence", "Mise en œuvre"],
    [["Analyse passive", "Aucune visite, DNS ou HTTP GET/HEAD vers l'URL soumise"],
     ["Validation d'entrée", "Contrôle syntaxique avant prédiction"],
     ["Authentification", "Imposée en production"],
     ["Autorisation", "Constantes admin, analyst, viewer définies ; endpoints administratifs par clé admin"],
     ["CORS", "Origines locales explicitement autorisées"],
     ["Secrets", "Aucun secret inclus dans les livrables"],
     ["Base privée", "Non exposée dans les livrables"],
     ["Explicabilité", "Désactivée plutôt que simulée"],
     ["Réentraînement", "Approbation manuelle obligatoire"],
     ["Données", "Aucune valeur fabriquée"]],
    widths=[1.8, 4.7], font=9,
)
para("Cette posture est cohérente avec un usage académique et expérimental : le système peut être démontré et "
     "audité sans introduire de risque réseau lié aux URL analysées.")

# ============================================================
# 11. VALIDATION
# ============================================================
doc.add_heading("11. Validation, tests et reproductibilité", level=1)
doc.add_heading("11.1 Suite de tests", level=2)
para("Commande : python -m pytest tests/ -q. Résultat vérifié : 34 passed.")
for item in [
    "Authentification et autorisations.",
    "CORS, y compris la requête de prévol.",
    "Cycle de vie de l'application.",
    "Absence d'explications fabriquées.",
    "Cas limites predict, feedback, health.",
    "Dérive de domaines avec historique vide.",
    "Agrégation du feedback et attribution à la bonne variante.",
    "Assignation A/B stable et insuffisance d'échantillon.",
    "File Active Learning et doublons d'URL.",
    "Éligibilité du réentraînement et protection des jeux verrouillés.",
    "Bins de distribution et filtrage temporel.",
]:
    bullet(item)
doc.add_heading("11.2 Intégrité du modèle", level=2)
para("Empreinte SHA-256 vérifiée avant et après les travaux :")
p = doc.add_paragraph()
p.paragraph_format.left_indent = Inches(0.3)
set_run(p.add_run("388d774e9c98f74b2036f6d0ccf5dc634c61f38750c7ed6e3b24c196a2e99202"),
        size=9.5, bold=True, color=NAVY)
para("Le modèle, les features, les seuils et les splits n'ont pas été modifiés.")
doc.add_heading("11.3 Reproductibilité", level=2)
for item in [
    "Graine aléatoire : 42.",
    "Hashes des splits conservés dans data/splits/hashes/v1.json.",
    "Expériences consignées dans experiments/results/EXP001–EXP021.json.",
    "Versions logicielles documentées dans le présent rapport.",
]:
    bullet(item)

# ============================================================
# 12. LIMITES
# ============================================================
doc.add_heading("12. Limites factuelles observées", level=1)
for item in [
    "Cibles non atteintes : rappel 0.8422 < 0.85 et FPR 0.0381 > 0.01.",
    "Source datée : la source PhishTank référencée est celle de Zenodo, décembre 2015.",
    "Faux positifs relevés : le rapport d'analyse les concentre sur .cn, .ar, les tokens de marque et le schéma http.",
    "Signaux utilisés : le pipeline décrit n'utilise pas de signal de réputation de domaine.",
    "Feedback observé : 6 retours dans l'instantané, contre un minimum de 20 exigé pour une alerte ou un gagnant A/B.",
    "Monitoring observé : période précédente à 0 prédiction, PSI null, dérive de domaines insufficient_data.",
    "Périmètre de l'audit : aucun changement de modèle, de features, de seuils ni de splits n'a été appliqué.",
]:
    bullet(item)

# ============================================================
# 13. CONCLUSION
# ============================================================
doc.add_heading("13. Conclusion", level=1)
para("Le projet Phishing AI Master 2 comporte quatre couches : données, modélisation, inférence et exploitation. "
     "Le modèle conservé est M1_LR_HARDNEG ; ses métriques DEV sont rappel 0.8422, FPR 0.0381 et ROC-AUC 0.9610. "
     "Le champ production_gate du fichier models/versions/metadata.json vaut BLOCKED.")
para("Les travaux d'audit ont modifié la couche applicative : signatures des fonctions de base alignées, "
     "initialisation de base ajoutée au démarrage, fonction refreshLab() définie, fonction renderHistogram() "
     "adaptée au format de données renvoyé, cache-busting du script, pipeline de feedback et garde-fous de "
     "monitoring, A/B et réentraînement ajustés. Le modèle, les features, les seuils et les splits n'ont pas "
     "été modifiés.")
callout("Faits vérifiés",
        "34 tests réussis ; empreinte modèle inchangée ; interface statique active sur le port 8501 ; "
        "endpoints administratifs protégés par clé admin ; statut A/B insufficient_data.", "ok")

# ============================================================
# 14. BIBLIOGRAPHIE
# ============================================================
doc.add_heading("14. Bibliographie", level=1)
for ref in [
    "PhishTank — https://phishtank.org",
    "Tranco — https://tranco-list.eu",
    "HuggingFace, jeu ealvaradob/phishing-dataset — https://huggingface.co/datasets/ealvaradob/phishing-dataset",
    "scikit-learn — https://scikit-learn.org",
    "FastAPI — https://fastapi.tiangolo.com",
    "Module Python http.server — https://docs.python.org/3/library/http.server.html",
    "Documentation SQLite — https://www.sqlite.org/docs.html",
    "Documentation Python — https://docs.python.org/3",
]:
    bullet(ref)

# ============================================================
# 15. ANNEXES
# ============================================================
doc.add_heading("15. Annexes", level=1)
doc.add_heading("Annexe A — Configuration finale du modèle", level=2)
add_table(
    ["Paramètre", "Valeur"],
    [["Nom", "M1_LR_HARDNEG"], ["Famille", "Logistic Regression"],
     ["Représentation", "TF-IDF n-grammes de caractères 3–5"],
     ["min_df", "3"], ["max_features", "20 000"], ["C", "1.0"],
     ["Classe pondérée", "balanced"], ["Solveur", "saga"], ["max_iter", "2000"],
     ["Seuil bas", "0.25"], ["Seuil haut", "0.75"],
     ["Label 0", "legitimate"], ["Label 1", "phishing"],
     ["Empreinte", "388d774e9c98f74b2036f6d0ccf5dc634c61f38750c7ed6e3b24c196a2e99202"]],
    widths=[2.0, 4.5], font=9,
)
doc.add_heading("Annexe B — Glossaire", level=2)
add_table(
    ["Terme", "Définition"],
    [["FPR", "Taux de faux positifs : légitimes classés comme phishing"],
     ["Rappel", "Part des phishing réellement détectés"],
     ["ROC-AUC", "Capacité du score à séparer les deux classes"],
     ["PSI", "Population Stability Index, mesure de dérive distributionnelle"],
     ["Domaine registrable", "Domaine de premier niveau privé plus suffixe public"],
     ["NEEDS_REVIEW", "Zone d'incertitude entre les deux seuils"],
     ["Insufficient data", "Statut indiquant que les données ne permettent pas une conclusion"]],
    widths=[1.7, 4.8], font=9,
)
doc.add_heading("Annexe C — Statuts d'interface", level=2)
add_table(
    ["Statut", "Signification"],
    [["OK", "Conditions remplies, données suffisantes"],
     ["WARNING", "Valeur proche du seuil, surveillance nécessaire"],
     ["DRIFT", "Dérive statistique détectée sur une baseline valide"],
     ["INSUFFICIENT_DATA", "Historique ou échantillon insuffisant"],
     ["BLOCKED", "Réentraînement ou promotion bloqué par les règles"],
     ["ERROR", "Erreur technique à investiguer"]],
    widths=[1.9, 4.6], font=9,
)
doc.add_heading("Annexe D — Formules et décisions", level=2)
for item in [
    "verdict = LEGITIMATE si score < 0.25.",
    "verdict = NEEDS_REVIEW si 0.25 ≤ score < 0.75.",
    "verdict = PHISHING si score ≥ 0.75.",
    "label = 1 pour phishing, label = 0 pour légitime.",
    "Un feedback manquant n'est jamais une validation.",
    "Un gagnant A/B exige au moins 20 retours vérifiés par variante.",
    "Un réentraînement n'est déployé qu'après approbation manuelle.",
]:
    bullet(item)

doc.add_heading("Annexe E — Sources des faits et vérification", level=2)
add_table(
    ["Fait reporté", "Source vérifiée", "Résultat observé"],
    [["Suite de tests", "python -m pytest tests/ -q", "34 passed"],
     ["Empreinte du modèle", "hashlib.sha256(artefact joblib)", "388d774e…a2e99202"],
     ["Métriques DEV et statut", "models/versions/metadata.json", "rappel 0.8422, FPR 0.0381, AUC 0.9610, production_gate BLOCKED"],
     ["Seuils", "decision_policy.py, metadata.json", "low 0.25, high 0.75"],
     ["Interface active", "setup.bat lignes 90–97", "python -m http.server 8501, index.html"],
     ["Fichier Streamlit présent", "deployment/frontend/app.py", "import streamlit as st, non lancé par setup.bat"],
     ["Origines autorisées", "deployment/api/main.py ligne 32", "localhost et 127.0.0.1, ports 8501 et 8000"],
     ["Contrôle administratif", "deployment/api/main.py lignes 95–107, 347–379", "clé X-Admin-API-Key ; 503 en production si absente"],
     ["Rôles déclarés", "deployment/api/main.py lignes 111–118", "constantes admin, analyst, viewer ; contrôle par clé admin"],
     ["Volumes et feedback", "get_stats(), feedback_summary()", "115 prédictions, 6 avec feedback, 5 corrects, 1 incorrect"],
     ["A/B", "get_ab_test()", "winner insufficient_data ; M1 6 retours, Ensemble 0"],
     ["Active Learning", "get_active_learning()", "count 0, plage [0.4 ; 0.6]"],
     ["Monitoring", "get_monitoring(7)", "PSI null, dérive insufficient_data, 115 prédictions"],
     ["Dépendances", "requirements.txt", "scikit-learn 1.7.2, pandas 2.3.3, numpy 2.2.6, fastapi 0.142.2, streamlit 1.57.0"],
     ["Vendor libs", "D:\\openhands\\projects\\v2\\vendor_libs", "xgboost 3.2.0, lightgbm 4.7.0"]],
    widths=[1.5, 2.2, 2.8], font=8.2,
)

para("Rapport composé uniquement de faits vérifiables dans le projet et son environnement local à la date "
     "indiquée. Aucune opération de publication distante n'est décrite dans ce document.",
     size=9, italic=True, color=GRAY)

try:
    doc.save(OUT)
    print("Saved", OUT)
except PermissionError:
    fallback = OUT.replace(".docx", "_NOUVEAU.docx")
    doc.save(fallback)
    print("Saved", fallback, "(original file is open in another application)")
