import urllib.request, re
url = 'https://web.cs.hacettepe.edu.tr/~selman/grambeddings-dataset/'
with urllib.request.urlopen(url, timeout=30) as r:
    html = r.read().decode('utf-8')
links = re.findall(r'href="([^"]*)"', html)
for l in links:
    if 'download' in l.lower() or 'drive' in l.lower() or 'forms' in l.lower() or '.zip' in l.lower() or '.csv' in l.lower() or 'http' in l.lower():
        print(l)
