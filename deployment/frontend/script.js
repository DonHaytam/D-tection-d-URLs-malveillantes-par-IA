// Phishing AI Master 2 - Frontend JavaScript
// Passive URL analysis only: no URL is ever visited by this interface.
window.onerror = function (msg, src, line, col, err) {
    try { alert("Erreur JS: " + msg + "\\n" + (err && err.stack ? err.stack : src + ":" + line)); } catch (e) {}
    return false;
};
const API_URL = "http://127.0.0.1:8000";
const CLIENT_KEY = "phishing_ai_client_id";

let lastResult = null;
let pendingIncorrect = false;

function clientId() {
    let id = localStorage.getItem(CLIENT_KEY);
    if (!id) {
        id = "web-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
        localStorage.setItem(CLIENT_KEY, id);
    }
    return id;
}

async function api(path, options = {}) {
    const res = await fetch(API_URL + path, options);
    let data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (!res.ok) {
        const detail = (data && (data.detail || data.error)) || ("HTTP " + res.status);
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return data;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
}

function pct(score) { return (Number(score) * 100).toFixed(2) + "%"; }

function verdictClass(v) {
    if (v === "PHISHING") return "verdict-phishing";
    if (v === "LEGITIMATE") return "verdict-legitimate";
    return "verdict-review";
}

function verdictColor(v) {
    if (v === "PHISHING") return "#ef4444";
    if (v === "LEGITIMATE") return "#22c55e";
    return "#f59e0b";
}

function verdictIcon(v) {
    if (v === "PHISHING") return "fa-triangle-exclamation";
    if (v === "LEGITIMATE") return "fa-circle-check";
    return "fa-circle-question";
}

function fmtDate(value) {
    if (!value) return "-";
    const d = new Date(value);
    return isNaN(d.getTime()) ? String(value) : d.toLocaleString("fr-FR");
}

// ---------------- Navigation ----------------
document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
        e.preventDefault();
        document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
        item.classList.add("active");
        const page = item.dataset.page;
        document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
        const section = document.getElementById("page-" + page);
        if (section) section.classList.add("active");
        if (page === "historique") loadHistory();
        if (page === "statistiques") loadStats();
        if (page === "collecte") loadCollecte();
        if (page === "laboratoire") loadLab();
        if (page === "idees") loadIdeas();
    });
});

// ---------------- Analyse ----------------
document.getElementById("analyzeBtn").addEventListener("click", analyzeUrl);
document.getElementById("urlInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") analyzeUrl();
});

async function analyzeUrl() {
    const input = document.getElementById("urlInput");
    const url = input.value.trim();
    if (!url) return;
    const btn = document.getElementById("analyzeBtn");
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyse...';
    try {
        const result = await api("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url, client_id: clientId() })
        });
        lastResult = result;
        showResult(result);
    } catch (err) {
        alert("Erreur : " + err.message + "\nVerifiez que l'API est demarree (uvicorn).");
    } finally {
        btn.disabled = false;
        btn.innerHTML = original;
    }
}

function showResult(result) {
    const card = document.getElementById("resultCard");
    card.style.display = "block";

    const verdict = result.verdict;
    const score = Number(result.score || 0);
    const display = document.getElementById("verdictDisplay");
    if (display) {
        display.className = "verdict-display " + verdictClass(verdict);
        display.innerHTML = '<i class="fa-solid ' + verdictIcon(verdict) + '"></i> ' + escapeHtml(verdict);
    }

    const scoreText = document.getElementById("scoreText");
    if (scoreText) scoreText.innerHTML =
        '<i class="fa-solid fa-gauge-high"></i> Score de risque : ' + pct(score);
    const fill = document.getElementById("scoreFill");
    if (fill) {
        fill.style.width = Math.max(0, Math.min(100, score * 100)) + "%";
        fill.style.background = score >= 0.75 ? "#ef4444" : score >= 0.5 ? "#f59e0b" : "#22c55e";
    }

    const mv = document.getElementById("modelVersion");
    if (mv) mv.textContent = result.model_version || "-";
    const th = result.thresholds || {};
    const thr = document.getElementById("thresholds");
    if (thr) thr.textContent = (th.low != null ? th.low : "-") + " / " + (th.high != null ? th.high : "-");
    const pt = document.getElementById("procTime");
    if (pt) pt.textContent = result.processing_time_ms != null ? result.processing_time_ms : "-";
    const vd = document.getElementById("variantDisplay");
    if (vd) vd.textContent = result.variant || (result.model_version || "-");

    const hint = document.getElementById("activeLearningHint");
    if (hint) hint.style.display = result.active_learning ? "flex" : "none";

    // Explainability disabled (noisy char n-gram fragments). Section hidden.

    // Reset feedback UI for this prediction
    pendingIncorrect = false;
    document.getElementById("feedbackDetails").style.display = "none";
    document.getElementById("feedbackButtons").style.display = "flex";
    document.getElementById("feedbackMsg").textContent = "";
    document.getElementById("feedbackPrompt").textContent = result.active_learning
        ? "Cette prediction est incertaine : confirmez-vous le resultat ?"
        : "Cette prediction est-elle correcte ?";

    card.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderExplanation(exp) {
    const section = document.getElementById("explainSection");
    if (!section) return;
    if (!exp || exp.error) {
        section.style.display = "none";
        return;
    }
    section.style.display = "block";
    const summary = document.getElementById("explainSummary");
    if (summary) summary.textContent =
        exp.summary || "Contributions des n-grammes de caracteres (coefficients de regression logistique).";

    const annot = document.getElementById("urlAnnotation");
    if (annot && Array.isArray(exp.annotated_url) && exp.annotated_url.length) {
        annot.innerHTML = exp.annotated_url.map(seg => {
            const text = escapeHtml(seg.text);
            if (seg.signal === "phishing") return '<mark class="mark-phishing">' + text + "</mark>";
            if (seg.signal === "legitimate") return '<mark class="mark-legitimate">' + text + "</mark>";
            return "<span>" + text + "</span>";
        }).join("");
    } else {
        annot.textContent = "";
    }

    renderChips("phishingSignals", exp.phishing_signals, "danger");
    renderChips("legitSignals", exp.legitimate_signals, "success");

    const numericWrap = document.getElementById("numericSignalsWrap");
    if (Array.isArray(exp.numeric_signals) && exp.numeric_signals.length) {
        numericWrap.style.display = "block";
        renderChips("numericSignals", exp.numeric_signals, "neutral");
    } else {
        numericWrap.style.display = "none";
    }
}

function renderChips(elementId, items, tone) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (!Array.isArray(items) || !items.length) {
        el.innerHTML = '<span class="chip-empty">Aucun signal dominant.</span>';
        return;
    }
    el.innerHTML = items.map(item => {
        const term = Array.isArray(item) ? item[0] : item;
        const value = Array.isArray(item) ? item[1] : "";
        return '<span class="chip chip-' + tone + '">' + escapeHtml(term) +
            (value !== "" ? ' <em>' + escapeHtml(value) + "</em>" : "") + "</span>";
    }).join("");
}

// ---------------- Feedback ----------------
function sendFeedback(feedback) {
    if (!lastResult || !lastResult.prediction_id) {
        setFeedbackMessage("Analysez d'abord une URL.", "warning");
        return;
    }
    if (feedback === "incorrect") {
        pendingIncorrect = true;
        document.getElementById("feedbackButtons").style.display = "none";
        document.getElementById("feedbackDetails").style.display = "block";
        return;
    }
    postFeedback({ feedback });
}

function submitIncorrectFeedback() {
    const label = document.getElementById("correctedLabel").value;
    const comment = document.getElementById("feedbackComment").value.trim();
    postFeedback({ feedback: "incorrect", corrected_label: label, comment: comment || null });
}

function hideFeedbackDetails() {
    pendingIncorrect = false;
    document.getElementById("feedbackDetails").style.display = "none";
    document.getElementById("feedbackButtons").style.display = "flex";
}

async function postFeedback(payload) {
    if (!lastResult || !lastResult.prediction_id) return;
    payload.prediction_id = lastResult.prediction_id;
    try {
        await api("/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const labels = {
            correct: "Merci, prediction confirmee.",
            incorrect: "Merci, correction enregistree : elle alimentera le reentrainement.",
            unknown: "Feedback enregistre (incertain)."
        };
        setFeedbackMessage(labels[payload.feedback] || "Feedback enregistre.", "success");
        document.getElementById("feedbackButtons").style.display = "flex";
        document.getElementById("feedbackDetails").style.display = "none";
        loadIdeas();
    } catch (err) {
        setFeedbackMessage("Erreur feedback : " + err.message, "error");
    }
}

function setFeedbackMessage(text, tone) {
    const msg = document.getElementById("feedbackMsg");
    msg.textContent = text;
    msg.style.color = tone === "error" ? "#ef4444" : tone === "warning" ? "#f59e0b" : "#22c55e";
}

// ---------------- Batch ----------------
document.getElementById("batchBtn").addEventListener("click", async () => {
    const text = document.getElementById("batchUrls").value.trim();
    if (!text) return;
    const urls = text.split("\n").map(u => u.trim()).filter(Boolean);
    const container = document.getElementById("batchResults");
    container.innerHTML = '<p class="caption">Analyse en cours...</p>';
    try {
        const data = await api("/predict_batch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ urls, client_id: clientId() })
        });
        let html = '<table class="data-table"><thead><tr><th>URL</th><th>Verdict</th><th>Score</th><th>Variante</th><th>Temps (ms)</th></tr></thead><tbody>';
        data.results.forEach(r => {
            html += "<tr><td class=\"cell-url\">" + escapeHtml(r.url) + "</td><td style=\"color:" +
                verdictColor(r.verdict) + ";font-weight:600;\">" + escapeHtml(r.verdict) +
                "</td><td>" + pct(r.score || 0) + "</td><td>" + escapeHtml(r.variant || "-") +
                "</td><td>" + (r.processing_time_ms != null ? r.processing_time_ms : "-") + "</td></tr>";
        });
        html += "</tbody></table>";
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = '<p style="color:#ef4444;">Erreur : ' + escapeHtml(err.message) + "</p>";
    }
});

// ---------------- Historique ----------------
async function loadHistory() {
    const tbody = document.querySelector("#historyTable tbody");
    const empty = document.getElementById("historyEmpty");
    try {
        const data = await api("/history?limit=200");
        const items = data.items || [];
        if (!items.length) {
            tbody.innerHTML = "";
            empty.style.display = "block";
            return;
        }
        empty.style.display = "none";
        tbody.innerHTML = items.map(h => {
            const fb = h.user_feedback
                ? '<span class="feedback-tag ' + (h.user_feedback === "incorrect" ? "tag-warning" : "tag-success") + '">' +
                  escapeHtml(h.user_feedback) + "</span>"
                : '<span class="muted">-</span>';
            return "<tr><td>" + h.id + '</td><td class="cell-url">' + escapeHtml(h.url) +
                '</td><td style="color:' + verdictColor(h.verdict) + ';font-weight:600;">' +
                escapeHtml(h.verdict || "-") + "</td><td>" + pct(h.score || 0) + "</td><td>" +
                escapeHtml(h.model_version || "-") + "</td><td>" + escapeHtml(h.variant || "-") +
                "</td><td>" + fmtDate(h.timestamp) + "</td><td>" + fb + "</td></tr>";
        }).join("");
    } catch (err) {
        tbody.innerHTML = "";
        empty.style.display = "block";
        empty.textContent = "Impossible de charger l'historique : " + err.message;
    }
}

// ---------------- Statistiques ----------------
async function loadStats() {
    try {
        const [stats, monitoring] = await Promise.all([
            api("/stats"),
            api("/monitoring?window_days=7").catch(() => null)
        ]);
        document.getElementById("statTotal").textContent = stats.n || 0;
        document.getElementById("statFeedback").textContent = stats.feedback || 0;
        document.getElementById("statCorrect").textContent = stats.correct || 0;
        document.getElementById("statIncorrect").textContent = stats.incorrect || 0;
        document.getElementById("statIncorrectRate").textContent = pct(stats.incorrect_rate || 0);
        document.getElementById("statActive").textContent = stats.active_learning_pending || 0;

        const dist = stats.verdicts || {};
        const distEl = document.getElementById("verdictDist");
        if (!Object.keys(dist).length) {
            distEl.innerHTML = '<p class="muted">Aucune prediction enregistree.</p>';
        } else {
            distEl.innerHTML = '<div class="dist-row">' + Object.entries(dist).map(([v, c]) =>
                '<div class="dist-box"><div class="dist-label" style="color:' + verdictColor(v) + '">' +
                escapeHtml(v) + '</div><div class="dist-value">' + c + "</div></div>"
            ).join("") + "</div>";
        }

        renderHistogram("scoreHistogram", stats.score_histogram || []);
        if (monitoring && monitoring.daily) {
            renderDaily("dailyChart", monitoring.daily);
        } else {
            document.getElementById("dailyChart").innerHTML = '<p class="muted">Pas assez de donnees.</p>';
        }
    } catch (err) {
        document.getElementById("verdictDist").innerHTML =
            '<p style="color:#ef4444;">Erreur : ' + escapeHtml(err.message) + "</p>";
    }
}

function renderHistogram(elementId, bins) {
    const el = document.getElementById(elementId);
    const max = Math.max(1, ...bins.map(b => b.count));
    el.innerHTML = bins.map(b =>
        '<div class="bar-row"><span class="bar-label">' + escapeHtml(b.bin) +
        '</span><div class="bar-track"><div class="bar-fill" style="width:' +
        (b.count / max * 100) + '%"></div></div><span class="bar-value">' + b.count + "</span></div>"
    ).join("");
}

function renderDaily(elementId, daily) {
    const el = document.getElementById(elementId);
    const max = Math.max(1, ...daily.map(d => d.n));
    el.innerHTML = daily.map(d =>
        '<div class="bar-row"><span class="bar-label">' + escapeHtml(d.date.slice(5)) +
        '</span><div class="bar-track"><div class="bar-fill" style="width:' +
        (d.n / max * 100) + '%"></div></div><span class="bar-value">' + d.n + "</span></div>"
    ).join("");
}

// ---------------- Collecte ----------------
async function loadCollecte() {
    try {
        const [al, history, retrain] = await Promise.all([
            api("/active-learning?limit=25"),
            api("/history?limit=200"),
            api("/retraining/status")
        ]);
        document.getElementById("activeLearningCount").textContent = al.count || 0;
        renderActiveLearningTable("activeLearningTable", al.items || []);
        renderFeedbackTable(history.items || []);
        renderRetrainStatus("retrainStatus", retrain);
        renderRetrainRuns("retrainRuns", retrain.runs || []);
    } catch (err) {
        document.getElementById("retrainStatus").innerHTML =
            '<p style="color:#ef4444;">Erreur : ' + escapeHtml(err.message) + "</p>";
    }
}

function renderActiveLearningTable(elementId, items) {
    const el = document.getElementById(elementId);
    if (!items.length) {
        el.innerHTML = '<p class="muted">Aucune URL dans la zone incertaine (0.4 - 0.6) pour le moment.</p>';
        return;
    }
    el.innerHTML = '<table class="data-table"><thead><tr><th>URL</th><th>Score</th><th>Verdict</th><th>Date</th><th>Etiqueter</th></tr></thead><tbody>' +
        items.map(item =>
            "<tr><td class=\"cell-url\">" + escapeHtml(item.url) + "</td><td>" + pct(item.score || 0) +
            "</td><td>" + escapeHtml(item.verdict || "-") + "</td><td>" + fmtDate(item.timestamp) +
            '</td><td class="actions-cell"><button class="mini-btn mini-danger" onclick="labelActive(' +
            item.id + ",'" + escapeHtml(item.verdict || "") + "','phishing')\">Phishing</button>" +
            '<button class="mini-btn mini-success" onclick="labelActive(' +
            item.id + ",'" + escapeHtml(item.verdict || "") + "','legitimate')\">Legitime</button></td></tr>"
        ).join("") + "</tbody></table>";
}

async function labelActive(id, verdict, label) {
    let feedback = "incorrect";
    let corrected = label;
    if (verdict === "PHISHING" && label === "phishing") { feedback = "correct"; corrected = null; }
    if (verdict === "LEGITIMATE" && label === "legitimate") { feedback = "correct"; corrected = null; }
    try {
        await api("/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prediction_id: id,
                feedback,
                corrected_label: corrected,
                comment: "Active learning"
            })
        });
        loadCollecte();
    } catch (err) {
        alert("Erreur feedback : " + err.message);
    }
}

function renderFeedbackTable(items) {
    const el = document.getElementById("feedbackData");
    const rows = items.filter(h => h.user_feedback);
    if (!rows.length) {
        el.innerHTML = '<p class="muted">Pas encore de feedback collecte.</p>';
        return;
    }
    el.innerHTML = '<table class="data-table"><thead><tr><th>URL</th><th>Verdict</th><th>Score</th><th>Feedback</th><th>Correction</th><th>Date</th></tr></thead><tbody>' +
        rows.map(h =>
            '<tr><td class="cell-url">' + escapeHtml(h.url) + "</td><td>" + escapeHtml(h.verdict || "-") +
            "</td><td>" + pct(h.score || 0) + "</td><td>" + escapeHtml(h.user_feedback) +
            "</td><td>" + escapeHtml(h.corrected_label || "-") + "</td><td>" + fmtDate(h.feedback_timestamp) + "</td></tr>"
        ).join("") + "</tbody></table>";
}

function renderRetrainStatus(elementId, status) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const fb = status.feedback || {};
    const schedule = status.schedule || {};
    el.innerHTML = '<div class="info-line"><span>Feedback disponible</span><strong>' + (fb.with_feedback || 0) +
        "</strong></div>" +
        '<div class="info-line"><span>Taux incorrect</span><strong>' + pct(fb.incorrect_rate || 0) + "</strong></div>" +
        '<div class="info-line"><span>Planification</span><strong>' +
        (schedule.enabled ? "active" : "desactivee") + "</strong></div>" +
        '<div class="info-line"><span>Minimum de donnees</span><strong>' + (schedule.min_samples || 30) + "</strong></div>";
}

function renderRetrainRuns(elementId, runs) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (!runs.length) {
        el.innerHTML = '<p class="muted">Aucun reentrainement lance.</p>';
        return;
    }
    el.innerHTML = '<table class="data-table"><thead><tr><th>ID</th><th>Demande</th><th>Statut</th><th>Feedback</th><th>Donnees</th><th>Recall DEV</th><th>FPR DEV</th><th>Approuve</th></tr></thead><tbody>' +
        runs.map(run => {
            const metrics = run.metrics || {};
            return "<tr><td>" + run.id + "</td><td>" + fmtDate(run.created_at) + "</td><td>" +
                statusBadge(run.status) + "</td><td>" + (run.n_feedback || 0) + "</td><td>" +
                (run.n_train || 0) + "</td><td>" + (metrics.recall != null ? Number(metrics.recall).toFixed(4) : "-") +
                "</td><td>" + (metrics.fpr != null ? Number(metrics.fpr).toFixed(4) : "-") +
                "</td><td>" + (run.approved ? "oui" : "non") + "</td></tr>";
        }).join("") + "</tbody></table>";
}

function statusBadge(status) {
    const tone = status === "pending_approval" ? "warning"
        : status === "approved" ? "success"
        : status === "failed" || status === "rejected" ? "danger" : "neutral";
    return '<span class="badge badge-' + tone + '">' + escapeHtml(status || "-") + "</span>";
}

async function runRetraining() {
    const btn = document.getElementById("runRetrainBtn");
    if (btn) btn.disabled = true;
    const adminKey = (window.prompt("Cle admin (laisser vide en dev) :") || "").trim();
    const headers = { "Content-Type": "application/json" };
    if (adminKey) headers["X-Admin-API-Key"] = adminKey;
    try {
        const res = await api("/retraining/run", {
            method: "POST",
            headers,
            body: JSON.stringify({ trigger: "manual", min_samples: 30 })
        });
        setFeedbackMessage("");
        alert("Reentrainement lance (run #" + res.run_id + "). Suivez le statut ci-dessous.");
        setTimeout(loadCollecte, 1500);
        setTimeout(loadCollecte, 5000);
    } catch (err) {
        alert("Erreur : " + err.message);
    } finally {
        if (btn) btn.disabled = false;
    }
}

// ---------------- Laboratoire ----------------
async function loadLab() {
    document.getElementById("labRefreshTime").textContent = new Date().toLocaleTimeString("fr-FR");
    try {
        const [monitoring, ab, al, retrain] = await Promise.all([
            api("/monitoring?window_days=7"),
            api("/ab-test"),
            api("/active-learning?limit=15"),
            api("/retraining/status")
        ]);

        const cur = monitoring.current || {};
        document.getElementById("labIncorrectRate").textContent = pct(cur.incorrect_rate || 0);
        document.getElementById("labIncorrectSub").textContent =
            (cur.feedback || 0) + " retours / seuil " + pct(monitoring.alert_threshold || 0.05);
        document.getElementById("labActiveCount").textContent = al.count || 0;

        document.getElementById("labAbWinner").textContent = ab.winner || "-";
        document.getElementById("labDrift").textContent = monitoring.drift_status || "-";
        document.getElementById("labDriftSub").textContent =
            monitoring.psi != null ? "PSI = " + monitoring.psi : "PSI indisponible";

        const alertEl = document.getElementById("labAlert");
        if (monitoring.alerts && monitoring.alerts.length) {
            alertEl.style.display = "flex";
            alertEl.className = "alert-banner alert-" + (monitoring.alerts.some(a => a.severity === "high") ? "high" : "medium");
            alertEl.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i><div>' +
                monitoring.alerts.map(a => "<strong>" + escapeHtml(a.message) + "</strong>").join("<br>") + "</div>";
        } else {
            alertEl.style.display = "none";
        }

        renderAbCards(ab);
        renderAbTable(ab);
        renderMonitorAlerts(monitoring.alerts || []);
        renderHistogram("scoreDrift", (cur.hist || []));
        renderDomainDrift(monitoring.domain_drift || {});
        renderActiveLearningTable("labActiveTable", al.items || []);
        renderRetrainStatus("labRetrainStatus", retrain);
        renderRetrainRuns("labRetrainRuns", retrain.runs || []);
    } catch (err) {
        const alertEl = document.getElementById("labAlert");
        alertEl.style.display = "flex";
        alertEl.className = "alert-banner alert-high";
        alertEl.innerHTML = '<i class="fa-solid fa-plug-circle-xmark"></i><div>API indisponible : ' +
            escapeHtml(err.message) + "</div>";
    }
}



function refreshLab() {
    // Rafraîchir les données du laboratoire
    loadLab();
}
function renderAbCards(ab) {
    const variants = ab.variants || {};
    [["abM1", "M1"], ["abEnsemble", "ENSEMBLE"]].forEach(([id, name]) => {
        const el = document.getElementById(id);
        const v = variants[name];
        const label = name === "M1" ? "M1 - Regression logistique" : "Ensemble - Soft voting 0.5/0.3/0.2";
        if (!v) {
            el.innerHTML = '<div class="ab-head">' + label + '</div><p class="muted">Aucune donnee pour cette variante.</p>';
            return;
        }
        el.innerHTML = '<div class="ab-head">' + label + "</div>" +
            '<div class="ab-metric"><span>Predictions</span><strong>' + v.n + "</strong></div>" +
            '<div class="ab-metric"><span>Feedback</span><strong>' + v.feedback + "</strong></div>" +
            '<div class="ab-metric"><span>Taux incorrect</span><strong style="color:' +
            (v.incorrect_rate > 0.05 ? "#ef4444" : "#22c55e") + '">' + pct(v.incorrect_rate) + "</strong></div>" +
            '<div class="ab-metric"><span>Score moyen</span><strong>' +
            (v.avg_score != null ? pct(v.avg_score) : "-") + "</strong></div>";
    });
}

function renderAbTable(ab) {
    const el = document.getElementById("abTable");
    const ref = ab.offline_reference || {};
    el.innerHTML = '<p class="caption">Reference hors ligne (DEV, ' + escapeHtml(ref.note || "") + ") : recall " +
        (ref.recall != null ? Number(ref.recall).toFixed(4) : "-") + ", FPR " +
        (ref.fpr != null ? Number(ref.fpr).toFixed(4) : "-") + ", ROC-AUC " +
        (ref.roc_auc != null ? Number(ref.roc_auc).toFixed(4) : "-") + ".</p>";
}

function renderMonitorAlerts(alerts) {
    const el = document.getElementById("monitorAlerts");
    if (!alerts.length) {
        el.innerHTML = '<p class="muted"><i class="fa-solid fa-circle-check"></i> Aucune alerte active.</p>';
        return;
    }
    el.innerHTML = alerts.map(a =>
        '<div class="monitor-alert monitor-' + escapeHtml(a.severity) + '"><strong>' +
        escapeHtml(a.type) + "</strong><span>" + escapeHtml(a.message) + "</span></div>"
    ).join("");
}

function renderDomainDrift(d) {
    const el = document.getElementById("domainDrift");
    el.innerHTML = '<div class="info-line"><span>Domaines recents</span><strong>' +
        (d.current_unique_domains != null ? d.current_unique_domains : "-") + "</strong></div>" +
        '<div class="info-line"><span>Domaines precedents</span><strong>' +
        (d.previous_unique_domains != null ? d.previous_unique_domains : "-") + "</strong></div>" +
        '<div class="info-line"><span>Nouveaux domaines</span><strong>' +
        (d.new_domains != null ? d.new_domains : "-") + "</strong></div>" +
        '<div class="info-line"><span>Ratio nouveau</span><strong>' +
        pct(d.new_domain_ratio || 0) + "</strong></div>" +
        '<div class="info-line"><span>Statut</span><strong>' + escapeHtml(d.status || "-") + "</strong></div>";
}

// ---------------- Idees ----------------
async function loadIdeas() {
    try {
        const [al, ab, monitoring, retrain] = await Promise.all([
            api("/active-learning?limit=1"),
            api("/ab-test"),
            api("/monitoring?window_days=7"),
            api("/retraining/status")
        ]);
        const el = document.getElementById("ideaActiveCount");
        if (el) el.textContent = al.count || 0;
        const winner = document.getElementById("ideaAbWinner");
        if (winner) winner.textContent = ab.winner || "-";
        const alertEl = document.getElementById("ideaAlert");
        if (alertEl) {
            alertEl.textContent = (monitoring.alerts && monitoring.alerts.length) ? "Alerte" : "OK";
            alertEl.style.color = (monitoring.alerts && monitoring.alerts.length) ? "#f59e0b" : "#22c55e";
        }
        const last = document.getElementById("ideaLastRetrain");
        if (last) {
            const runs = retrain.runs || [];
            last.textContent = runs.length ? ("#" + runs[0].id + " " + (runs[0].status || "")) : "aucun";
        }
    } catch (err) {
        // The ideas page must stay readable even if the API is down.
    }
}

// Initial load: reflect live counters on the ideas page and stats when opened.
loadIdeas();
