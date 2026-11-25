import urllib.request
url = 'https://raw.githubusercontent.com/almakhamreh/Multimodal-Phishing-Benchmarks/main/README.md'
with urllib.request.urlopen(url, timeout=30) as r:
    text = r.read().decode('utf-8')
    idx = text.find('Download Link')
with open('D:/openhands/projects/v2/phishing_ai_master/reports/technical/readme_dump.txt', 'w', encoding='utf-8') as f:
    f.write(text[idx:idx+3000])
print('saved')

