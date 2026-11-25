"""Streamlit frontend - Phishing AI Master 2 (modern design)."""
import os, sys, sqlite3, json
from datetime import datetime
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import streamlit as st
import requests
import pandas as pd
import numpy as np

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
DB_PATH = os.environ.get("DB_PATH", "D:/openhands/projects/v2/phishing_ai_master/database/predictions.db")

st.set_page_config(page_title="Phishing AI Master 2", page_icon="shield", layout="wide")

# ---------- Custom CSS (modern dark-accent design) ----------
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0f172a; color: #e2e8f0; }
    .main-header { font-size: 2.2rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.3rem; }
    .sub-header { font-size: 1rem; color: #94a3b8; margin-bottom: 1.5rem; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
    .verdict-phishing { color: #ef4444; font-weight: 700; font-size: 1.6rem; }
    .verdict-legitimate { color: #22c55e; font-weight: 700; font-size: 1.6rem; }
    .verdict-review { color: #f59e0b; font-weight: 700; font-size: 1.6rem; }
    .score-bar { background: #334155; border-radius: 10px; height: 28px; overflow: hidden; margin: 0.5rem 0; }
    .score-fill { height: 100%; border-radius: 10px; transition: width 0.4s ease; }
    .score-text { font-size: 1.3rem; font-weight: 600; margin-top: 0.3rem; color: #f1f5f9; }
    .metric-box { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 1rem; text-align: center; }
    .metric-box .label { color: #94a3b8; font-size: 0.85rem; }
    .metric-box .value { color: #f1f5f9; font-size: 1.6rem; font-weight: 700; }
    .stButton > button { border-radius: 8px; font-weight: 500; }
    .stTextInput > div > div > input { background: #1e293b; color: #f1f5f9; border: 1px solid #334155; border-radius: 8px; }
    .stTextArea > div > div > textarea { background: #1e293b; color: #f1f5f9; border: 1px solid #334155; border-radius: 8px; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #f1f5f9; }
    section[data-testid="stSidebar"] { background: #1e293b; }
    section[data-testid="stSidebar"] .stRadio label { color: #e2e8f0; }
    .fa { margin-right: 8px; }
    hr { border-color: #334155; }
</style>
""", unsafe_allow_html=True)

# ---------- DB helpers ----------
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        verdict TEXT,
        score REAL,
        model_version TEXT,
        thresholds TEXT,
        processing_time_ms REAL,
        timestamp TEXT NOT NULL,
        user_feedback TEXT DEFAULT NULL,
        feedback_timestamp TEXT DEFAULT NULL
    )""")
    conn.commit()
    conn.close()

def save_prediction(url, result):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO predictions (url, verdict, score, model_version, thresholds, processing_time_ms, timestamp)
                 VALUES (?,?,?,?,?,?,?)""",
              (str(url), str(result.get("verdict")), float(result.get("score", 0)),
               str(result.get("model_version")), json.dumps(result.get("thresholds", {})),
               float(result.get("processing_time_ms", 0)), datetime.now().isoformat()))
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return rid

def update_feedback(row_id, feedback):
    if row_id is None:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE predictions SET user_feedback=?, feedback_timestamp=? WHERE id=?",
              (str(feedback), datetime.now().isoformat(), int(row_id)))
    conn.commit()
    conn.close()

def get_history(limit=100):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC LIMIT ?", conn, params=(int(limit),))
    conn.close()
    return df

def get_feedback_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    with_fb = c.execute("SELECT COUNT(*) FROM predictions WHERE user_feedback IS NOT NULL").fetchone()[0]
    correct = c.execute("SELECT COUNT(*) FROM predictions WHERE user_feedback='correct'").fetchone()[0]
    incorrect = c.execute("SELECT COUNT(*) FROM predictions WHERE user_feedback='incorrect'").fetchone()[0]
    conn.close()
    return int(total), int(with_fb), int(correct), int(incorrect)

init_db()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### Phishing AI Master 2")
    page = st.radio("Navigation", [
        "Analyse", "Historique", "Statistiques", "Collecte", "A propos"
    ])
    st.markdown("---")
    st.caption("Modele : M1_LR (Logistic Regression)")
    st.caption("Analyse passive - aucune visite d'URL")

# ---------- Page: Analyse ----------
if page == "Analyse":
    st.markdown('<p class="main-header"><i class="fa-solid fa-shield-halved"></i> Detection de phishing</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Analyse passive des chaines URL - aucune visite automatique.</p>', unsafe_allow_html=True)

    url = st.text_input("URL a analyser", placeholder="https://example.com/login")
    analyze = st.button("Analyser", type="primary")

    if analyze and url:
        try:
            r = requests.post(f"{API_URL}/predict", json={"url": url}, timeout=30)
            r.raise_for_status()
            result = r.json()
            row_id = save_prediction(url, result)

            verdict = result["verdict"]
            score = result["score"]
            pct = score * 100
            vclass = {"PHISHING": "verdict-phishing", "LEGITIMATE": "verdict-legitimate", "NEEDS_REVIEW": "verdict-review"}.get(verdict, "")
            vicon = {"PHISHING": "fa-triangle-exclamation", "LEGITIMATE": "fa-circle-check", "NEEDS_REVIEW": "fa-circle-question"}.get(verdict, "fa-circle")
            bar_color = "#ef4444" if pct >= 85 else ("#f59e0b" if pct >= 50 else "#22c55e")

            st.markdown(f'<p class="{vclass}"><i class="fa-solid {vicon}"></i>  {verdict}</p>', unsafe_allow_html=True)
            st.markdown(f'<div class="score-text"><i class="fa-solid fa-gauge-high"></i> Score de risque : {pct:.2f}%</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="score-bar"><div class="score-fill" style="width:{min(pct,100)}%; background:{bar_color};"></div></div>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'<div class="metric-box"><div class="label">Version modele</div><div class="value">{result["model_version"]}</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-box"><div class="label">Seuils</div><div class="value">{result["thresholds"]["low"]} / {result["thresholds"]["high"]}</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-box"><div class="label">Temps (ms)</div><div class="value">{result["processing_time_ms"]}</div></div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### Votre feedback")
            st.write("Cette prediction est-elle correcte ?")
            fb1, fb2, fb3 = st.columns(3)
            with fb1:
                if st.button("Correct", key="fb_ok", use_container_width=True):
                    update_feedback(row_id, "correct")
                    st.success("Merci pour votre feedback !")
            with fb2:
                if st.button("Incorrect", key="fb_bad", use_container_width=True):
                    update_feedback(row_id, "incorrect")
                    st.warning("Feedback enregistre. Ces donnees aideront a ameliorer le modele.")
            with fb3:
                if st.button("Je ne sais pas", key="fb_unk", use_container_width=True):
                    update_feedback(row_id, "unknown")
                    st.info("Feedback enregistre.")
        except Exception as e:
            st.error(f"Erreur : {e}")
            st.info("Verifiez que l'API est demarree (python -m uvicorn deployment.api.main:app)")

    st.markdown("---")
    st.markdown("#### Analyse par lot")
    batch_urls = st.text_area("Entrez plusieurs URL (une par ligne)", height=100)
    if st.button("Analyser le lot"):
        urls = [u.strip() for u in batch_urls.split("\n") if u.strip()]
        if urls:
            try:
                r = requests.post(f"{API_URL}/predict_batch", json={"urls": urls}, timeout=60)
                r.raise_for_status()
                results = r.json()["results"]
                for res in results:
                    save_prediction(res["url"], res)
                df = pd.DataFrame(results)
                df["score_pct"] = (df["score"] * 100).round(2).astype(str) + "%"
                st.dataframe(df[["url", "verdict", "score_pct", "processing_time_ms"]], use_container_width=True)
            except Exception as e:
                st.error(f"Erreur : {e}")

# ---------- Page: Historique ----------
elif page == "Historique":
    st.markdown('<p class="main-header"><i class="fa-solid fa-clock-rotate-left"></i> Historique</p>', unsafe_allow_html=True)
    df = get_history(100)
    if len(df) == 0:
        st.info("Aucune prediction pour le moment.")
    else:
        st.dataframe(df[["id", "url", "verdict", "score", "model_version", "timestamp", "user_feedback"]],
                     use_container_width=True)
        csv = df.to_csv(index=False)
        st.download_button("Exporter en CSV", csv, "predictions_history.csv", "text/csv")

# ---------- Page: Statistiques ----------
elif page == "Statistiques":
    st.markdown('<p class="main-header"><i class="fa-solid fa-chart-bar"></i> Statistiques</p>', unsafe_allow_html=True)
    total, with_fb, correct, incorrect = get_feedback_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-box"><div class="label">Total predictions</div><div class="value">{total}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div class="label">Avec feedback</div><div class="value">{with_fb}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div class="label">Correct</div><div class="value">{correct}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-box"><div class="label">Incorrect</div><div class="value">{incorrect}</div></div>', unsafe_allow_html=True)
    if with_fb > 0:
        accuracy = correct / with_fb * 100
        st.metric("Precision (feedback utilisateur)", f"{accuracy:.1f}%")

    df = get_history(1000)
    if len(df) > 0:
        st.markdown("#### Distribution des verdicts")
        st.bar_chart(df["verdict"].value_counts())
        st.markdown("#### Statistiques par verdict")
        for v in df["verdict"].unique():
            sub = df[df["verdict"] == v]
            st.write(f"**{v}** : n={len(sub)}, score moyen={sub['score'].mean()*100:.2f}%, min={sub['score'].min()*100:.2f}%, max={sub['score'].max()*100:.2f}%")

# ---------- Page: Collecte ----------
elif page == "Collecte":
    st.markdown('<p class="main-header"><i class="fa-solid fa-database"></i> Collecte et Reentrainement</p>', unsafe_allow_html=True)
    st.markdown("""
    ### Comment ca marche
    1. Les utilisateurs soumettent des URL et donnent leur feedback (correct/incorrect).
    2. Les donnees sont stockees dans la base SQLite (predictions.db).
    3. Un administrateur peut exporter les donnees avec feedback pour reentrainer le modele.
    4. Le modele reentraine est evalue sur le jeu DEV avant deploiement.
    """)

    total, with_fb, correct, incorrect = get_feedback_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Donnees avec feedback", with_fb)
    with col2:
        st.metric("Feedback 'incorrect' (erreurs du modele)", incorrect)

    df = get_history(10000)
    if len(df) > 0:
        fb_df = df[df["user_feedback"].notna()]
        if len(fb_df) > 0:
            st.markdown("#### Donnees avec feedback (pour reentrainement)")
            st.dataframe(fb_df[["url", "verdict", "score", "user_feedback"]], use_container_width=True)
            csv = fb_df.to_csv(index=False)
            st.download_button("Exporter les donnees avec feedback (CSV)", csv, "feedback_data.csv", "text/csv")
        else:
            st.info("Pas encore de feedback collecte.")

    st.markdown("---")
    st.markdown("#### Reentrainement (manuel)")
    st.code("""
# 1. Exporter les donnees avec feedback depuis cette page
# 2. Ajouter les URLs confirmees au dataset d'entrainement
# 3. Lancer le script d'entrainement :
python scripts/train_phase8.py
# 4. Evaluer sur DEV :
python scripts/gen_comparison.py
# 5. Mettre a jour le modele dans deployment/api/main.py
""", language="bash")

    st.markdown("#### Idees d'amelioration")
    st.markdown("""
    - **Active learning** : prioriser les URL avec score proche du seuil (0.4-0.6) pour le feedback.
    - **A/B testing** : comparer deux modeles en production.
    - **Monitoring** : alerter si le taux de feedback "incorrect" depasse un seuil.
    - **Reentrainement automatique** : scheduler un reentrainement hebdomadaire.
    - **Explainability** : afficher les tokens qui ont influence la decision (SHAP/LIME).
    - **Multi-modele** : voter entre plusieurs modeles pour reduire les faux positifs.
    """)

# ---------- Page: A propos ----------
elif page == "A propos":
    st.markdown('<p class="main-header"><i class="fa-solid fa-circle-info"></i> A propos</p>', unsafe_allow_html=True)
    st.markdown("""
    ### Phishing AI Master 2
    Detection intelligente des URL de phishing et malveillantes par IA et ML

    - **Modele** : M1_LR_HARDNEG (Logistic Regression, char TF-IDF 3-5)
    - **Recall** : 0.7383 | **FPR** : 0.0087 | **ROC-AUC** : 0.9610
    - **Seuils** : low=0.25 (legitime), high=0.75 (phishing)
    - **Analyse passive** : aucune visite automatique des URL

    ### Architecture
    - Backend : FastAPI (Python 3.10)
    - Frontend : Streamlit
    - Base de donnees : SQLite
    - Modele : scikit-learn (LogisticRegression)

    ### Securite
    - Pas de visite automatique des URL soumises
    - Pas de resolution DNS
    - Pas de requetes HTTP GET/HEAD
    - Analyse purement textuelle
    """)
    st.caption("Projet Master 2 Intelligence Artificielle - Cybersecurite")
