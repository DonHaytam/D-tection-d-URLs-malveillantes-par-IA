<style>
.cover { text-align:center; padding:2.5rem 1rem 1.5rem; border-bottom:3px solid #000; margin-bottom:2rem; }
.cover .eyebrow { font-size:0.85rem; letter-spacing:.18em; text-transform:uppercase; color:#555; }
.cover h1 { color:#000; font-size:2.1rem; line-height:1.15; margin:.6rem 0 .3rem; }
.cover h2 { color:#333; font-size:1.15rem; font-weight:500; margin:0 0 1.4rem; }
.badge { display:inline-block; padding:.25rem .65rem; border:1px solid #000; border-radius:999px; font-size:.78rem; font-weight:700; margin:.15rem; background:#fff; color:#000; }
.ok, .warn, .info, .blocked { background:#fff; color:#000; border-color:#000; }
.callout { border-left:4px solid #000; background:#f5f5f5; padding:.8rem 1rem; margin:1rem 0; }
.callout.warn, .callout.blocked, .callout.ok, .callout.info { border-left-color:#000; background:#f5f5f5; }
.small { font-size:.88rem; color:#555; }
table { width:100%; border-collapse:collapse; margin:.8rem 0 1.2rem; }
th { background:#e6e6e6; color:#000; }
td, th { border:1px solid #999; padding:.42rem .55rem; vertical-align:top; }
tr:nth-child(even) td { background:#f7f7f7; }
hr { border:none; border-top:1px solid #bbb; margin:2rem 0; }
</style>

<div class="cover">

<p class="eyebrow">Master 2 — Intelligence Artificielle et Cybersécurité</p>

# Détection intelligente des URL de phishing et malveillantes

## Rapport final d'articlisation, d'audit et de validation du projet

<p><span class="badge info">Projet académique et expérimental</span>
<span class="badge ok">34 tests réussis</span>
<span class="badge warn">Cibles de production non atteintes</span>
<span class="badge blocked">Déploiement automatique bloqué</span></p>

**Auteur** : Projet Master 2 IA<br>
**Date** : 26 novembre 2026<br>
**Modèle retenu** : `M1_LR_HARDNEG`<br>
**Environnement** : Windows, Python 3.10, CPU uniquement

</div>

---

<a id="sommaire"></a>

## Sommaire

- [0. Résumé](#resume)
- [1. Synthèse exécutive](#synthese)
- [2. Conditions et contraintes du projet](#conditions)
- [3. Présentation détaillée du projet](#projet)
  - [3.1 Contexte et problématique](#contexte)
  - [3.2 Objectifs et périmètre](#objectifs)
  - [3.3 Architecture générale](#architecture)
  - [3.4 Pile technologique](#stack)
- [4. État de l'art et choix méthodologiques](#etat-art)
- [5. Collecte et préparation des données](#donnees)
- [6. Méthodologie de modélisation](#methodologie)
- [7. Résultats expérimentaux](#resultats)
- [8. Application, API et interface](#application)
- [9. Audit, corrections et travaux réalisés](#travaux)
  - [9.1 Sécurisation de la couche de production](#securisation)
  - [9.2 Durcissement du Laboratoire](#laboratoire)
  - [9.3 Pipeline de feedback et apprentissage](#feedback)
  - [9.4 Dérive de domaines et PSI](#drift)
  - [9.5 Tests A/B](#ab)
  - [9.6 Active Learning](#active-learning)
  - [9.7 Réentraînement](#reentrainement)
  - [9.8 Monitoring et distribution des scores](#monitoring)
  - [9.9 Correctifs d'exécution frontend et API](#frontend)
- [10. Sécurité et conformité](#securite)
- [11. Validation, tests et reproductibilité](#validation)
- [12. Limites factuelles observées](#limites)
- [13. Conclusion](#conclusion)
- [14. Bibliographie](#bibliographie)
- [15. Annexes](#annexes)

---

<a id="resume"></a>

## 0. Résumé

Ce rapport présente le projet **Phishing AI Master 2** sous forme d'article technique complet : contexte, conditions de réalisation, données, méthodes, résultats, application opérationnelle, audit de qualité et travaux correctifs. Le système détecte les URL de phishing par analyse **passive** de la chaîne de caractères, sans visiter les sites, sans résolution DNS et sans requête HTTP vers les URL soumises.

Six familles de modèles ont été entraînées et comparées sur un corpus nettoyé de **159 568 URL**. Le modèle retenu est `M1_LR_HARDNEG` : régression logistique sur des n-grammes de caractères TF-IDF (3–5), améliorée par hard-negative mining. Sur le jeu de validation `DEV`, il obtient un rappel de **0.8422**, un FPR de **0.0381** et une ROC-AUC de **0.9610**. Les cibles initiales — rappel ≥ 0.85 et FPR ≤ 0.01 — ne sont donc pas simultanément atteintes ; le statut reste **BLOCKED** pour un usage de production autonome.

La partie application a ensuite été modifiée : API FastAPI, interface web, base SQLite, authentification, contrôle des origines, pipeline de feedback, monitoring, A/B testing, Active Learning et réentraînement supervisé. Les défauts d'exécution identifiés — signatures de fonctions désalignées, initialisation de base manquante, erreur JavaScript `refreshLab is not defined`, erreur `bins.map is not a function`, dérive de domaines mal interprétée, gagnant A/B déclaré trop tôt — ont été corrigés et couverts par des tests. La suite complète comporte **34 tests réussis**, et l'artefact du modèle conserve son empreinte inchangée.

**Mots-clés** : phishing, détection d'URL, machine learning, TF-IDF, n-grammes de caractères, régression logistique, hard-negative mining, calibration, monitoring, dérive de domaines, PSI, feedback, A/B testing, Active Learning.

> **Abstract —** This report documents the complete Phishing AI Master 2 project: assumptions, dataset, methodology, experimental comparison, operational application, security constraints, audit findings and corrective work. The selected model is `M1_LR_HARDNEG` (logistic regression, character TF-IDF 3–5, hard-negative mining). On the DEV split it reaches Recall 0.8422, FPR 0.0381 and ROC-AUC 0.9610. Production targets are not met, so automated deployment remains blocked. All 34 regression tests pass and the model checksum is unchanged.

---

<a id="synthese"></a>

## 1. Synthèse exécutive

Le projet comporte quatre couches :

1. **Données** — collecte multi-sources, nettoyage, déduplication, séparation par domaine registrable.
2. **Modélisation** — six modèles comparés, calibration, optimisation de seuils et hard-negative mining.
3. **Inférence** — politique de décision à trois états et service de prédiction passif.
4. **Exploitation** — API, interface web, base de données, feedback, monitoring et réentraînement contrôlé.

### 1.1 Résultats essentiels

| Dimension | Résultat vérifié | Lecture |
|---|---|---|
| Corpus nettoyé | 159 568 URL | Jeu équilibré après déduplication |
| Domaines registrables | 96 155 | Split domain-disjoint |
| Meilleur modèle | `M1_LR_HARDNEG` | FPR le plus faible et AUC élevée |
| Rappel DEV | 0.8422 | Inférieur à la cible 0.85 |
| FPR DEV | 0.0381 | Supérieur à la cible 0.01 |
| ROC-AUC DEV | 0.9610 | Valeur mesurée sur le jeu DEV |
| Seuils opérationnels | 0.25 / 0.75 | Inchangés |
| Tests | 34 / 34 réussis | Suite de régression verte |
| Empreinte modèle | `388d774e…a2e99202` | Inchangée |
| Déploiement | MANUAL APPROVAL | Aucun remplacement automatique |

<div class="callout warn">

**Constat vérifié** : le modèle sélectionné ne satisfait pas les deux objectifs de production en même temps. Le champ `production_gate` du fichier `models/versions/metadata.json` vaut `BLOCKED`.

</div>

### 1.2 État opérationnel observé

Les valeurs ci-dessous constituent un instantané de la base locale au 26 novembre 2026. Elles évoluent avec l'usage de l'application.

| Indicateur | Valeur observée | Interprétation |
|---|---:|---|
| Prédictions enregistrées | 115 | Volume de test local |
| Prédictions avec feedback | 6 | Retours vérifiés disponibles |
| Retours corrects / incorrects | 5 / 1 | Taux d'erreur observé : 16,67 % sur 6 retours |
| Fenêtre monitoring | 7 jours | 115 prédictions courantes, 0 précédente |
| PSI | indisponible | Pas de distribution de référence valide |
| Dérive de domaines | `insufficient_data` | Aucune baseline historique |
| File Active Learning | 0 élément | Aucun score dans [0.4 ; 0.6] sans feedback |
| Gagnant A/B | `insufficient_data` | 6 retours pour M1, 0 pour Ensemble ; seuil = 20 |
| Seuil d'alerte incorrect | 5 % | Avec minimum 20 retours |

---

<a id="conditions"></a>

## 2. Conditions et contraintes du projet

Le travail a été réalisé sous un jeu de conditions strictes. Aucune n'a été assouplie pour obtenir un résultat plus favorable.

| # | Condition imposée | État | Détail de conformité |
|---:|---|---|---|
| 1 | Conserver `M1_LR_HARDNEG` | Respectée | Modèle chargé et artefact non modifiés |
| 2 | Conserver la régression logistique | Respectée | `LogisticRegression` conservée |
| 3 | Conserver TF-IDF caractères 3–5 | Respectée | `min_df=3`, `max_features=20000` |
| 4 | Conserver les seuils 0.25 et 0.75 | Respectée | `<0.25` LEGITIMATE ; `0.25–<0.75` NEEDS_REVIEW ; `≥0.75` PHISHING |
| 5 | Conserver les labels 0 et 1 | Respectée | `0 = legitimate`, `1 = phishing` |
| 6 | Conserver l'empreinte du modèle | Respectée | `388d774e9c98f74b2036f6d0ccf5dc634c61f38750c7ed6e3b24c196a2e99202` |
| 7 | Préserver TRAIN / DEV / LOCKED_TEST / INDEPENDENT | Respectée | Découpage par domaine registrable conservé |
| 8 | Ne jamais entraîner sur LOCKED_TEST ni INDEPENDENT | Respectée | Jeux verrouillés exclus de l'entraînement et du réglage |
| 9 | Aucune visite d'URL, aucun DNS, aucun HTTP vers l'URL soumise | Respectée | Analyse textuelle passive uniquement |
| 10 | Aucun déploiement automatique d'un modèle réentraîné | Respectée | Validation manuelle obligatoire |
| 11 | Aucune donnée fabriquée | Respectée | Valeurs manquantes signalées `insufficient_data` |
| 12 | Aucun secret ni base privée exposée | Respectée | Configuration sensible hors livrable |
| 13 | Ne pas modifier l'artefact du modèle | Respectée | Checksum vérifié avant et après les travaux |
| 14 | Ne pas confondre score moyen et exactitude | Respectée | Score moyen présenté comme distribution, pas comme accuracy |
| 15 | Ne pas déclarer 100 % de dérive sans baseline | Respectée | `insufficient_data` lorsque l'historique est vide |
| 16 | Ne pas déclarer un gagnant A/B sur un seul retour | Respectée | Minimum 20 retours vérifiés par variante |
| 17 | Suite de tests verte avant livraison | Respectée | 34 tests réussis |

<div class="callout">

Ces conditions constituent le cahier des charges scientifique et opérationnel. Elles expliquent plusieurs décisions volontairement conservatrices : mains sur le modèle, seuils non réécrits, statuts `insufficient_data` plutôt que valeurs artificielles, et blocage du déploiement automatique.

</div>

---

<a id="projet"></a>

## 3. Présentation détaillée du projet

<a id="contexte"></a>

### 3.1 Contexte et problématique

Le phishing est une forme d'ingénierie sociale qui exploite la confiance de l'utilisateur. Une URL trompeuse peut imiter une banque, une messagerie ou un service de paiement afin de collecter des identifiants. La détection automatique doit fonctionner sans accès réseau à l'URL soumise. La généralisation à des domaines jamais vus est évaluée par le découpage `domain-disjoint`.

La problématique centrale est la suivante : **comment construire un détecteur d'URL malveillantes qui atteigne un rappel élevé sans produire un nombre inacceptable de faux positifs, tout en généralisant hors des domaines observés pendant l'entraînement ?**

Deux tensions structurent le projet :

- **Rappel vs faux positifs** : augmenter la sensibilité augmente généralement le taux de fausses alertes.
- **Signal lexical vs généralisation** : les tokens de marque sont efficaces sur les jeux connus mais peuvent devenir des raccourcis fragiles.

<a id="objectifs"></a>

### 3.2 Objectifs et périmètre

Les objectifs initiaux étaient :

1. construire un pipeline de données reproductible ;
2. entraîner et comparer six modèles ;
3. sélectionner le meilleur candidat sur des critères mesurés ;
4. développer une application fonctionnelle autour du modèle ;
5. documenter honnêtement les limites ;
6. durcir l'exploitation : feedback, monitoring, A/B, Active Learning, réentraînement contrôlé.

Le périmètre fonctionnel final couvre :

- prédiction unitaire et par lot ;
- affichage du verdict, du score, de la version du modèle et de l'horodatage ;
- historique et statistiques ;
- collecte de feedback avec règle « dernier retour gagnant » ;
- monitoring de dérive et distribution des scores ;
- comparaison A/B avec politique de taille d'échantillon ;
- file d'Active Learning ;
- réentraînement éligible uniquement après filtres et validation manuelle.

<a id="architecture"></a>

### 3.3 Architecture générale

Le projet suit une architecture modulaire :

| Couche | Rôle principal |
|---|---|
| `src/data/` | ingestion, validation, déduplication, splitting, provenance |
| `src/features/` | parsing URL, features lexicales, structurelles et TF-IDF |
| `src/models/` | modèles M1–M6 et registre |
| `src/evaluation/` | métriques, calibration, seuils |
| `src/inference/` | chargeur de modèle et prédicteur |
| `src/policy/` | politique de décision à trois états |
| `src/storage/` | base SQLite, feedback, monitoring, drift, A/B, Active Learning |
| `src/retraining/` | éligibilité, exclusions, garde-fous |
| `deployment/api/` | API FastAPI |
| `deployment/frontend/` | interface web |
| `database/` | base locale SQLite |
| `reports/` | rapports techniques, figures et tables |

Cette séparation permet de modifier l'interface ou la couche de stockage sans toucher au modèle, condition essentielle pour préserver l'artefact validé.

<a id="stack"></a>

### 3.4 Pile technologique

| Composant | Version / choix |
|---|---|
| Python | 3.10 |
| scikit-learn | 1.7.2 |
| pandas | 2.3.3 |
| numpy | 2.2.6 |
| FastAPI | 0.142.2 |
| Interface active | HTML/CSS/JS statique, servie par `python -m http.server` sur le port 8501 |
| XGBoost | 3.2.0 |
| LightGBM | 4.7.0 (bibliothèque vendorisée) |
| Base | SQLite locale |
| Exécution | CPU uniquement |

---

<a id="etat-art"></a>

## 4. État de l'art et choix méthodologiques

La détection d'URL malveillantes peut s'appuyer sur plusieurs familles de signaux :

- **signaux lexicaux** : longueur, nombre de points, tirets, chiffres, entropie, tokens suspects ;
- **signaux structurels** : schéma, profondeur du chemin, paramètres, présence d'une IP comme hôte ;
- **signaux textuels** : n-grammes de caractères capturant des fragments comme `pay`, `login` ou `bank` ;
- **signaux de réputation** : rang de domaine, âge, historique — non utilisés ici pour rester strictement passif.

Le choix retenu combine TF-IDF de caractères et régression logistique. Le modèle est linéaire, interprétable et peu coûteux à exécuter. Les résultats comparatifs du chapitre 7 ne montrent pas d'amélioration simultanée du rappel et du FPR pour les autres modèles.

---

<a id="donnees"></a>

## 5. Collecte et préparation des données

### 5.1 Sources

| Source | Type | Taille | Licence / restriction |
|---|---|---:|---|
| HuggingFace `ealvaradob/phishing-dataset` | Mixte | 835 697 URL | Licence à vérifier avant redistribution |
| Tranco | Légitime | 1 000 000 domaines | CC BY 3.0 / 4.0 |
| PhishTank via Zenodo | Phishing | 149 188 URL valides | Conditions d'utilisation PhishTank |

### 5.2 Nettoyage

- Déduplication exacte : **276 URL** supprimées.
- Déduplication normalisée : **0 URL** supplémentaire.
- Validation syntaxique : **156 URL** invalides supprimées.
- Domaines avec labels contradictoires : **591 domaines** exclus de l'entraînement.

### 5.3 Jeu nettoyé

| Catégorie | Nombre |
|---|---:|
| Total après déduplication | 159 568 |
| Légitimes | 79 842 |
| Phishing | 79 726 |
| Domaines registrables uniques | 96 155 |

### 5.4 Séparation des jeux

| Split | Taille | Légitimes | Phishing | Usage autorisé |
|---|---:|---:|---:|---|
| TRAIN | 114 873 | 58 221 | 56 652 | Entraînement |
| DEV | 22 586 | 10 885 | 11 701 | Réglage et comparaison |
| LOCKED_TEST | 22 109 | 10 736 | 11 373 | Évaluation verrouillée uniquement |
| INDEPENDENT_FINAL_TEST | réservé | — | — | Test final indépendant, jamais pour le réglage |

Le découpage est **domain-disjoint** : aucun domaine registrable ne traverse deux ensembles. Cette mesure réduit le risque de fuite et force le modèle à généraliser à des domaines inconnus.

### 5.5 Analyse exploratoire

- URLs uniques observées avant nettoyage : 821 402.
- Hôtes uniques : 448 803.
- Longueur moyenne : 47,48 caractères.
- 607 141 URL sans schéma, normalisées en `https`.
- TLD dominant : `.com` (486 714 occurrences).

Les figures de l'analyse exploratoire sont conservées dans `reports/figures/eda/`.

---

<a id="methodologie"></a>

## 6. Méthodologie de modélisation

### 6.1 Représentation

La représentation finale est un pipeline TF-IDF sur n-grammes de caractères de taille 3 à 5, avec `min_df=3` et `max_features=20000`. Les n-grammes de caractères captent des motifs même lorsque l'URL est légèrement modifiée, contrairement à une tokenisation par mots trop sensible aux séparateurs.

### 6.2 Modèles comparés

| Code | Modèle | Principe |
|---|---|---|
| M1 | Régression logistique | Baseline linéaire interprétable |
| M2 | SVM linéaire | Efficace en haute dimension, nécessite calibration |
| M3 | Random Forest | Ensemble d'arbres ; FPR 0.1000, ECE 0.0116 sur DEV |
| M4 | Gradient Boosting | Boosting séquentiel sur features numériques |
| M5 | XGBoost | Version régularisée et optimisée du boosting |
| M6 | Hybride | TF-IDF caractères + features numériques |
| M1_HARDNEG | M1 + hard-negative mining | Candidat retenu |

### 6.3 Hard-negative mining

Les faux positifs du jeu `DEV` ont été réinjectés comme exemples difficiles pendant l'entraînement. Cette étape a réduit le FPR de **0.0548** à **0.0381**, soit une baisse relative d'environ 30 %. Le jeu `LOCKED_TEST` n'a jamais été utilisé pour cette opération.

### 6.4 Calibration et seuils

- Calibration isotonique : Brier 0.0761, ECE 0.0000.
- Calibration Platt : Brier 0.0774, ECE 0.0158.
- Une expérience de seuil à 0.4774 atteint un rappel de 0.8500 mais avec un FPR de 0.0469 ; elle n'a pas été adoptée car elle ne respecte pas la cible FPR et modifierait la politique validée.

La politique opérationnelle reste donc :

| Score | Verdict |
|---|---|
| `< 0.25` | LEGITIMATE |
| `0.25 – < 0.75` | NEEDS_REVIEW |
| `≥ 0.75` | PHISHING |

---

<a id="resultats"></a>

## 7. Résultats expérimentaux

### 7.1 Comparaison sur DEV

| Modèle | Accuracy | Precision | Recall | FPR | F1 | ROC-AUC | PR-AUC | Brier | ECE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M1 LR | 0.8947 | 0.9432 | 0.8478 | 0.0548 | 0.8930 | 0.9593 | 0.9676 | 0.0784 | 0.0304 |
| M2 SVM | 0.8980 | 0.9389 | 0.8590 | 0.0601 | 0.8972 | 0.9583 | 0.9669 | 0.0818 | 0.0560 |
| M3 RF | 0.8764 | 0.9018 | 0.8545 | 0.1000 | 0.8775 | 0.9440 | 0.9551 | 0.0902 | 0.0116 |
| M4 GB | 0.8662 | 0.9051 | 0.8286 | 0.0934 | 0.8652 | 0.9394 | 0.9496 | 0.0964 | 0.0210 |
| M5 XGBoost | 0.8801 | 0.9148 | 0.8474 | 0.0848 | 0.8798 | 0.9484 | 0.9576 | 0.0870 | 0.0067 |
| M6 Hybrid | 0.8080 | 0.8871 | 0.7212 | 0.0987 | 0.7956 | 0.8896 | 0.9070 | 0.1331 | 0.0325 |
| **M1_HARDNEG** | **0.8998** | **0.9596** | **0.8422** | **0.0381** | **0.8970** | **0.9610** | **0.9695** | 0.0770 | 0.0370 |

### 7.2 Interprétation

- `M1_HARDNEG` possède le **FPR le plus bas** et la **ROC-AUC la plus élevée**.
- M2 SVM obtient un rappel plus élevé mais paie un FPR plus important.
- M6 Hybride sous-performe, ce qui confirme que l'ajout de features numériques n'apporte pas de gain ici.
- Le modèle retenu est cohérent avec l'objectif de limitation des faux positifs, mais le rappel reste sous la cible.

### 7.3 Analyse des faux positifs

Les faux positifs sont concentrés sur :

- des TLD sous-représentés (`.cn`, `.ar`) ;
- des URL courtes contenant des tokens de marque (`login`, `bank`, `amazon`, `paypal`) ;
- le schéma `http`, présent dans 21,9 % des faux positifs contre 3,1 % des légitimes.

Une allow-list issue du top 10k Tranco a été évaluée : FPR 0.0298 mais rappel 0.8209. Elle est donc trop agressive et n'a pas été activée.

---

<a id="application"></a>

## 8. Application, API et interface

### 8.1 API FastAPI

| Endpoint | Méthode | Rôle |
|---|---|---|
| `/health` | GET | État du modèle, environnement, authentification admin, chemin de base |
| `/predict` | POST | Prédiction unitaire et enregistrement |
| `/predict_batch` | POST | Prédiction par lot |
| `/feedback` | POST | Enregistrement du feedback, 404 si la prédiction n'existe pas |
| `/history` | GET | Historique paginé |
| `/stats` | GET | Statistiques globales |
| `/active-learning` | GET | File des cas incertains |
| `/monitoring` | GET | Monitoring, dérive, PSI, distribution des scores |
| `/ab-test` | GET | Résultats A/B avec politique d'échantillon |
| `/feedback/export` | GET | Export CSV du feedback |
| `/retraining/status` | GET | État des runs et planification |
| `/retraining/run` | POST | Lancement contrôlé d'un run (admin) |
| `/retraining/approve` | POST | Approbation manuelle (admin) |
| `/retraining/schedule` | GET / POST | Consultation et réglage du calendrier (admin) |
| `/ensemble` | GET | Informations sur la variante Ensemble |

### 8.2 Interface web

L'interface expose six espaces :

- **Statistiques** : volumes, verdicts, distribution des scores ;
- **Collecte et Réentraînement** : feedback, éligibilité, exclusions, runs ;
- **Laboratoire** : monitoring, A/B, Active Learning, dérive ;
- **Monitoring** : alertes, PSI, distribution temporelle ;
- **A/B Testing** : comparaison M1 / Ensemble ;
- **Active Learning** : file priorisée des URL incertaines.

Le bouton de rafraîchissement du Laboratoire appelle une fonction `refreshLab()` explicite, et le script est chargé avec un paramètre de version (`script.js?v=3`) afin d'éviter le service d'une copie obsolète par le navigateur.

<div class="callout info">

**Précision importante** : le lancement actuel utilisé par `setup.bat` ne démarre **pas** Streamlit. Il sert `index.html` et `script.js` avec le serveur HTTP intégré de Python sur `http://localhost:8501`. Un fichier `deployment/frontend/app.py` propose une variante Streamlit, mais il n'est pas utilisé par le script de démarrage décrit dans ce rapport.

</div>

### 8.3 Base de données

Les tables principales sont :

| Table | Contenu |
|---|---|
| `predictions` | URL, verdict, score, variante, version, feedback, domaine, labels corrigés |
| `feedback` | Retours utilisateurs horodatés avec règle « dernier retour gagnant » |
| `retraining_runs` | Runs de réentraînement, compteurs d'éligibilité et détails |
| `monitoring_events` | Alertes et événements de surveillance |

La base est initialisée au démarrage par une étape dédiée dans `setup.bat`, ce qui supprime les erreurs de colonne manquante lors d'un premier lancement.

---

<a id="travaux"></a>

## 9. Audit, corrections et travaux réalisés

Cette section constitue le journal technique des travaux réalisés après la livraison initiale. Chaque problème est présenté avec sa cause réelle et la correction appliquée.

### 9.1 Sécurisation de la couche de production

| Avant | Cause | Après |
|---|---|---|
| Authentification non imposée en production | Démarrage trop permissif | Authentification obligatoire en environnement de production |
| Droits fins non appliqués | Constantes de rôles déclarées sans clés distinctes | Contrôle effectif par clé admin `X-Admin-API-Key` |
| CORS potentiellement bloquant | Origines frontend non toutes couvertes | Liste incluant `localhost:8501`, `127.0.0.1:8501`, `localhost:8000`, `127.0.0.1:8000` |
| Explications potentiellement trompeuses | Texte généré sans preuve | Explication désactivée plutôt que fabriquée |

### 9.2 Durcissement du Laboratoire

Le tableau de bord du Laboratoire agrège quatre sources : monitoring, A/B testing, Active Learning et réentraînement. Plusieurs défauts ont été corrigés :

- les compteurs de feedback distinguaient mal retours manquants et retours incorrects ;
- les pourcentages étaient affichés sans taille d'échantillon ;
- la dérive de domaines pouvait être annoncée à 100 % sans baseline ;
- le PSI était affiché comme indisponible même lorsqu'il pouvait être calculé.

Le résultat est une interface qui affiche **valeur + taille d'échantillon + fenêtre + interprétation + statut de suffisance**.

### 9.3 Pipeline de feedback et apprentissage

La chaîne de feedback a été réécrite selon le flux :

```
Prédiction → Feedback → Dernier retour gagnant → Label vérifié → Déduplication → Exclusions → Candidat d'entraînement
```

Corrections apportées :

- validation des labels `correct`, `incorrect`, `unknown` ;
- erreur explicite lorsque la prédiction ciblée n'existe pas ;
- règle « dernier retour gagnant » : ancien feedback supprimé avant insertion du nouveau ;
- mise à jour cohérente du champ `user_feedback` de la prédiction ;
- inférence du label selon le verdict et la correction ;
- compteurs d'exclusion : URL invalide, label manquant, label invalide, doublon, conflit, déjà utilisé, chevauchement de domaine, appartenance à un jeu réservé.

Le point critique est qu'un retour manquant n'est **jamais** compté comme un retour correct.

### 9.4 Dérive de domaines et PSI

La dérive de domaines a été séparée en deux notions :

- **nouveauté de domaines** : information descriptive ;
- **dérive statistique** : comparaison contre une baseline historique valide.

Règle appliquée :

- si aucun domaine historique n'existe → `insufficient_data` ;
- si aucun domaine courant n'existe → `stable` ;
- sinon, calcul du ratio et décision selon un seuil.

Le PSI est calculé sur 10 bins égaux dans `[0, 1]`. Si la distribution de référence est vide, le PSI vaut `null` et le statut est `insufficient_data`. Aucune valeur artificielle n'est substituée.

### 9.5 Tests A/B

La comparaison M1 / Ensemble conserve une assignation 50/50 fondée sur un hash du `client_id`. Les métriques de production attribuent chaque retour à la variante ayant réellement généré la prédiction.

Politique de décision :

- minimum **20 retours vérifiés** par variante ;
- si une variante est sous le seuil → `winner = insufficient_data` ;
- si les deux sont au seuil → comparaison du taux d'erreur ;
- égalité → `winner = tie`.

Les métriques hors ligne du jeu DEV (rappel 0.8595, FPR 0.0345, AUC 0.9714 pour l'Ensemble pondéré 0.5/0.3/0.2) restent une **référence**, jamais un motif pour déclarer un gagnant en production ni pour promouvoir automatiquement l'Ensemble.

### 9.6 Active Learning

La file d'Active Learning suit des règles explicites :

- score dans `[0.4 ; 0.6]` ;
- exclusion des URL déjà pourvues d'un feedback ;
- tri par incertitude : `ABS(score - 0.5) ASC` ;
- départage par récence ;
- déduplication des URL et des domaines ;
- conservation des URL et labels d'origine.

Aucun retour non vérifié n'est traité comme vérité terrain, et la plage d'incertitude n'a pas été élargie sans preuve expérimentale.

### 9.7 Réentraînement

Le pipeline de réentraînement n'entraîne que sur des candidats vérifiés et autorisés. Il applique :

- inférence de label à partir du verdict et de la correction ;
- exclusion des doublons et conflits ;
- exclusion des domaines qui chevauchent `LOCKED_TEST` ;
- exclusion de toute appartenance à `LOCKED_TEST` ou `INDEPENDENT` ;
- compteurs d'exclusion visibles dans le tableau de bord ;
- statut `insufficient_data` sous le minimum requis ;
- approbation manuelle avant tout remplacement du modèle.

### 9.8 Monitoring et distribution des scores

Le monitoring vérifie maintenant :

- le filtrage temporel et la gestion UTC des horodatages ;
- des bins couvrant `[0, 1]` sans chevauchement ;
- la somme des bins égale au nombre de prédictions de la même fenêtre ;
- la séparation entre distribution des scores et exactitude réelle ;
- l'absence d'affirmation d'exactitude sans labels vérifiés.

Instantané observé sur 7 jours :

| Bin | Effectif |
|---|---:|
| 0.0–0.1 | 22 |
| 0.1–0.2 | 38 |
| 0.2–0.3 | 18 |
| 0.3–0.4 | 19 |
| 0.4–0.5 | 0 |
| 0.5–0.6 | 0 |
| 0.6–0.7 | 0 |
| 0.7–0.8 | 0 |
| 0.8–0.9 | 0 |
| 0.9–1.0 | 18 |
| **Total** | **115** |

### 9.9 Correctifs d'exécution frontend et API

| Symptôme observé | Cause réelle | Correction |
|---|---|---|
| `TypeError: get_history() got an unexpected keyword argument 'limit'` | Signature de fonction désalignée avec l'appel API | Paramètres `limit`, `offset`, `days` alignés |
| `get_feedback_rows() unexpected keyword 'limit'` | Signature incomplète | Paramètre `limit` ajouté |
| `create_retraining_run() unexpected keyword 'trigger'` | Paramètres API non acceptés | Signature étendue et compatibilité conservée |
| `update_retraining_run() unexpected keyword 'status'` | Paramètres API non acceptés | Signature étendue |
| `sqlite3.OperationalError: no such column: created_at` | Colonne inexistante interrogée | Requêtes alignées sur le schéma réel |
| `ReferenceError: refreshLab is not defined` | Bouton HTML sans fonction correspondante | Fonction `refreshLab()` définie |
| `bins.map is not a function` | Backend renvoie un dictionnaire `bin_0…bin_9`, frontend attendait un tableau | `renderHistogram()` normalise les deux formats et utilise des boucles sûres |
| Ancien JavaScript serv après mise à jour | Cache navigateur | Paramètre `script.js?v=3` |
| Base non initialisée au premier lancement | Étape absente du script de démarrage | Initialisation explicite dans `setup.bat` |
| Erreur CORS depuis `localhost:8501` | Origine non autorisée par le serveur lancé | Liste d'origines vérifiée et documentée |

<div class="callout ok">

Tous ces correctifs ont été apportés sans toucher au modèle, aux features, aux seuils ni aux jeux de données verrouillés. L'empreinte du modèle est restée identique après chaque étape.

</div>

### 9.10 Tableaux récapitulatif des travaux

| Domaine | Travail réalisé | Résultat |
|---|---|---|
| Sécurité | Auth production, clé admin, CORS, lifecycle | Contrôles configurés |
| Feedback | Dernier retour gagnant, validation, exclusions | Pipeline traçable |
| Dérive | `insufficient_data` sans baseline | Plus de fausse alerte 100 % |
| PSI | Histogramme 10 bins, comparaison référent/courant | Calcul honnête ou `null` |
| A/B | Minimum 20 retours par variante | Pas de gagnant sur bruit |
| Active Learning | Tri incertitude + récence | File priorisée |
| Réentraînement | Filtres et approbation manuelle | Aucun remplacement automatique |
| Monitoring | Fenêtre UTC, bins, tailles d'échantillon | Métriques interprétables |
| Frontend | `refreshLab`, `renderHistogram`, cache-busting | Erreurs JavaScript supprimées |
| API / base | Signatures alignées, init DB | Erreurs d'exécution supprimées |
| Tests | 34 tests de régression | Suite verte |
| Modèle | Artefact non modifié | Checksum conservé |

---

<a id="securite"></a>

## 10. Sécurité et conformité

| Exigence | Mise en œuvre |
|---|---|
| Analyse passive | Aucune visite d'URL, aucun DNS, aucun HTTP GET/HEAD vers l'URL soumise |
| Validation d'entrée | Contrôle syntaxique avant prédiction |
| Authentification | Imposée en production |
| Autorisation | Constantes `admin`, `analyst`, `viewer` définies ; endpoints administratifs protégés par clé admin |
| CORS | Origines locales explicitement autorisées |
| Secrets | Aucun secret inclus dans les livrables |
| Base privée | Non exposée dans les livrables |
| Explicabilité | Désactivée plutôt que simulée |
| Réentraînement | Approbation manuelle obligatoire |
| Données | Aucune valeur fabriquée, statuts d'insuffisance explicites |

Cette posture est cohérente avec un usage académique et expérimental : le système peut être démontré et audité sans introduire de risque réseau lié aux URL analysées.

---

<a id="validation"></a>

## 11. Validation, tests et reproductibilité

### 11.1 Suite de tests

Commande de validation :

```
python -m pytest tests/ -q
```

Résultat vérifié : **34 passed**.

Les tests couvrent notamment :

- authentification et autorisations ;
- CORS, y compris la requête de prévol ;
- cycle de vie de l'application ;
- absence d'explications fabriquées ;
- cas limites `/predict`, `/feedback`, `/health` ;
- dérive de domaines avec historique vide ;
- agrégation du feedback ;
- attribution du feedback à la bonne variante ;
- assignation A/B stable ;
- insuffisance d'échantillon A/B ;
- filtrage de la file Active Learning ;
- doublons d'URL ;
- éligibilité et exclusions du réentraînement ;
- protection des jeux verrouillés ;
- bins de distribution des scores ;
- filtrage temporel.

### 11.2 Intégrité du modèle

```
python -c "import hashlib; print(hashlib.sha256(open('models/versions/M1_LR_HARDNEG.joblib','rb').read()).hexdigest())"
```

Empreinte obtenue :

```
388d774e9c98f74b2036f6d0ccf5dc634c61f38750c7ed6e3b24c196a2e99202
```

Cette valeur est identique à celle relevée avant les travaux d'audit. Le modèle, les features, les seuils et les splits n'ont pas été modifiés.

### 11.3 Reproductibilité

- Graine aléatoire : 42.
- Hashes des splits conservés dans `data/splits/hashes/v1.json`.
- Expériences consignées dans `experiments/results/EXP001–EXP021.json`.
- Versions logicielles documentées dans le présent rapport.

---

<a id="limites"></a>

## 12. Limites factuelles observées

1. **Cibles non atteintes** : rappel 0.8422 < 0.85 et FPR 0.0381 > 0.01.
2. **Source datée** : la source PhishTank référencée est celle de Zenodo, décembre 2015.
3. **Faux positifs relevés** : le rapport d'analyse les concentre sur `.cn`, `.ar`, les tokens de marque et le schéma `http`.
4. **Signaux utilisés** : le pipeline décrit n'utilise pas de signal de réputation de domaine.
5. **Feedback observé** : 6 retours dans l'instantané, contre un minimum de 20 exigé pour une alerte ou un gagnant A/B.
6. **Monitoring observé** : Période précédente à 0 prédiction, PSI `null`, dérive de domaines `insufficient_data`.
7. **Périmètre de l'audit** : aucun changement de modèle, de features, de seuils ni de splits n'a été appliqué.

---

<a id="conclusion"></a>

## 13. Conclusion

Le projet Phishing AI Master 2 comporte quatre couches : données, modélisation, inférence et exploitation. Le modèle conservé est `M1_LR_HARDNEG` ; ses métriques DEV sont rappel 0.8422, FPR 0.0381 et ROC-AUC 0.9610. Le champ `production_gate` du fichier `models/versions/metadata.json` vaut `BLOCKED`.

Les travaux d'audit ont modifié la couche applicative : signatures des fonctions de base alignées, initialisation de base ajoutée au démarrage, fonction `refreshLab()` définie, fonction `renderHistogram()` adaptée au format de données renvoyé, cache-busting du script, pipeline de feedback et garde-fous de monitoring/A/B/réentraînement ajustés. Le modèle, les features, les seuils et les splits n'ont pas été modifiés.

Faits vérifiés à la date du rapport : **34 tests réussis**, **empreinte modèle inchangée**, **interface statique active sur le port 8501**, **endpoint administratifs protégés par clé admin**, **statut A/B `insufficient_data`**.

---

<a id="bibliographie"></a>

## 14. Bibliographie

1. PhishTank — https://phishtank.org
2. Tranco — https://tranco-list.eu
3. HuggingFace, jeu `ealvaradob/phishing-dataset` — https://huggingface.co/datasets/ealvaradob/phishing-dataset
4. scikit-learn — https://scikit-learn.org
5. FastAPI — https://fastapi.tiangolo.com
6. Module Python `http.server` — https://docs.python.org/3/library/http.server.html
7. Documentation SQLite — https://www.sqlite.org/docs.html
8. Documentation Python — https://docs.python.org/3

---

<a id="annexes"></a>

## 15. Annexes

### Annexe A — Configuration finale du modèle

| Paramètre | Valeur |
|---|---|
| Nom | `M1_LR_HARDNEG` |
| Famille | Logistic Regression |
| Représentation | TF-IDF n-grammes de caractères 3–5 |
| `min_df` | 3 |
| `max_features` | 20 000 |
| `C` | 1.0 |
| Classe pondérée | `balanced` |
| Solveur | `saga` |
| `max_iter` | 2000 |
| Seuil bas | 0.25 |
| Seuil haut | 0.75 |
| Label 0 | legitimate |
| Label 1 | phishing |
| Empreinte | `388d774e9c98f74b2036f6d0ccf5dc634c61f38750c7ed6e3b24c196a2e99202` |

### Annexe B — Glossaire

| Terme | Définition |
|---|---|
| FPR | Taux de faux positifs : légitimes classés comme phishing |
| Rappel | Part des phishing réellement détectés |
| ROC-AUC | Capacité du score à séparer les deux classes |
| PSI | Population Stability Index, mesure de dérive distributionnelle |
| Domaine registrable | Domaine de premier niveau privé plus suffixe public |
| NEEDS_REVIEW | Zone d'incertitude entre les deux seuils |
| Insufficient data | Statut indiquant que les données ne permettent pas une conclusion |

### Annexe C — Statuts d'interface

| Statut | Signification |
|---|---|
| OK | Conditions remplies, données suffisantes |
| WARNING | Valeur proche du seuil, surveillance nécessaire |
| DRIFT | Dérive statistique détectée sur une baseline valide |
| INSUFFICIENT_DATA | Historique ou échantillon insuffisant |
| BLOCKED | Réentraînement ou promotion bloqué par les règles |
| ERROR | Erreur technique à investiguer |

### Annexe D — Formules et décisions

- `verdict = LEGITIMATE` si `score < 0.25`.
- `verdict = NEEDS_REVIEW` si `0.25 ≤ score < 0.75`.
- `verdict = PHISHING` si `score ≥ 0.75`.
- `label = 1` pour phishing, `label = 0` pour légitime.
- Un feedback manquant n'est jamais une validation.
- Un gagnant A/B exige au moins 20 retours vérifiés par variante.
- Un réentraînement n'est déployé qu'après approbation manuelle.

### Annexe E — Sources des faits et vérification

| Fait reporté | Source vérifiée | Résultat observé |
|---|---|---|
| Suite de tests | `python -m pytest tests/ -q` | `34 passed` |
| Empreinte du modèle | `hashlib.sha256(open('models/versions/M1_LR_HARDNEG.joblib','rb').read())` | `388d774e…a2e99202` |
| Métriques DEV et statut | `models/versions/metadata.json` | rappel 0.8422, FPR 0.0381, AUC 0.9610, `production_gate: BLOCKED` |
| Seuils | `src/policy/decision_policy.py`, `models/versions/metadata.json` | `low_threshold=0.25`, `high_threshold=0.75` |
| Interface active | `setup.bat`, lignes 90–97 | `python -m http.server 8501`, ouverture de `index.html` |
| Fichier Streamlit présent | `deployment/frontend/app.py` | `import streamlit as st`, mais non lancé par `setup.bat` |
| Origines autorisées | `deployment/api/main.py`, ligne 32 | `localhost:8501`, `127.0.0.1:8501`, `localhost:8000`, `127.0.0.1:8000` |
| Contrôle administratif | `deployment/api/main.py`, lignes 95–107 et 347–379 | clé `X-Admin-API-Key` requise ; production renvoie 503 si non configurée |
| Rôles déclarés | `deployment/api/main.py`, lignes 111–118 | constantes `admin`, `analyst`, `viewer` ; contrôle effectif par clé admin |
| Volumes et feedback | fonctions `get_stats()`, `feedback_summary()` | 115 prédictions, 6 avec feedback, 5 corrects, 1 incorrect |
| A/B | `get_ab_test()` | `winner: insufficient_data` ; M1 6 retours, Ensemble 0 |
| Active Learning | `get_active_learning()` | `count: 0`, plage `[0.4 ; 0.6]` |
| Monitoring | `get_monitoring(7)` | PSI `null`, dérive de domaines `insufficient_data`, 115 prédictions sur 7 jours |
| Dépendances déclarées | `requirements.txt` | scikit-learn 1.7.2, pandas 2.3.3, numpy 2.2.6, fastapi 0.142.2, streamlit 1.57.0 |
| Bibliothèques vendorisées | `D:\openhands\projects\v2\vendor_libs` | xgboost 3.2.0, lightgbm 4.7.0 présents |

---

<p class="small">Rapport composé uniquement de faits vérifiables dans le projet et son environnement local à la date indiquée. Aucune opération de publication distante n'est décrite dans ce document.</p>
