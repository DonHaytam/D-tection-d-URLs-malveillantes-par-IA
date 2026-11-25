import urllib.request, re
url = 'https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2024.1308634/full'
try:
    with urllib.request.urlopen(url, timeout=30) as r:
        html = r.read().decode('utf-8', 'replace')
    links = re.findall(r'href="([^"]*\.csv[^"]*)"', html)
    print('CSV links:', links[:5])
    links2 = re.findall(r'href="([^"]*zip[^"]*)"', html)
    print('Zip links:', links2[:5])
    links3 = re.findall(r'href="([^"]*dataset[^"]*)"', html)
    print('Dataset links:', links3[:10])
except Exception as e:
    print('FAIL:', repr(e))
