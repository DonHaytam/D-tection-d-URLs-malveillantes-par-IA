p = 'D:/openhands/projects/v2/phishing_ai_master/deployment/frontend/script.js'
with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

old = "body: JSON.stringify({ url })"
new = "body: JSON.stringify({ url, explain: true })"
assert old in content, 'old1 not found'
content = content.replace(old, new)

old2 = "    document.getElementById('procTime').textContent = result.processing_time_ms;"
new2 = ("    document.getElementById('procTime').textContent = result.processing_time_ms;\n"
        "    if (result.explanation) {\n"
        "        const sec = document.getElementById('explainSection');\n"
        "        const cont = document.getElementById('explainContent');\n"
        "        sec.style.display = 'block';\n"
        "        let html = '';\n"
        "        if (result.explanation.phishing_signals) {\n"
        "            html += \"<p style='color:#ef4444;font-weight:600;margin-bottom:0.3rem;'><i class='fa-solid fa-triangle-exclamation'></i> Signaux phishing :</p><div style='display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:0.8rem;'>\";\n"
        "            result.explanation.phishing_signals.forEach(([feat, val]) => {\n"
        "                html += `<span style='background:rgba(239,68,68,0.15);color:#ef4444;padding:0.2rem 0.5rem;border-radius:4px;font-size:0.8rem;font-family:monospace;'>${feat} (${val})</span>`;\n"
        "            });\n"
        "            html += '</div>';\n"
        "        }\n"
        "        if (result.explanation.legitimate_signals) {\n"
        "            html += \"<p style='color:#22c55e;font-weight:600;margin-bottom:0.3rem;'><i class='fa-solid fa-shield-halved'></i> Signaux legitimes :</p><div style='display:flex;flex-wrap:wrap;gap:0.4rem;'>\";\n"
        "            result.explanation.legitimate_signals.forEach(([feat, val]) => {\n"
        "                html += `<span style='background:rgba(34,197,94,0.15);color:#22c55e;padding:0.2rem 0.5rem;border-radius:4px;font-size:0.8rem;font-family:monospace;'>${feat} (${val})</span>`;\n"
        "            });\n"
        "            html += '</div>';\n"
        "        }\n"
        "        cont.innerHTML = html;\n"
        "    }")
assert old2 in content, 'old2 not found'
content = content.replace(old2, new2)

with open(p, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
