p = 'D:/openhands/projects/v2/phishing_ai_master/deployment/frontend/index.html'
with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                </div>

                <div class="feedback-section">"""
new = """                </div>

                <div id="explainSection" style="display:none; margin-top:1rem;">
                    <h3><i class="fa-solid fa-magnifying-glass-chart"></i> Explicabilite</h3>
                    <div id="explainContent"></div>
                </div>

                <div class="feedback-section">"""
assert old in content, 'old not found'
content = content.replace(old, new, 1)

old2 = "body: JSON.stringify({ url })"
new2 = "body: JSON.stringify({ url, explain: true })"
assert old2 in content, 'old2 not found'
content = content.replace(old2, new2)

with open(p, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
