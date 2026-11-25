import urllib.request, re
url = 'https://research.aalto.fi/en/datasets/phishstorm-phishing-legitimate-url-dataset/'
try:
    with urllib.request.urlopen(url, timeout=30) as r:
        html = r.read().decode('utf-8', 'replace')
    links = re.findall(r'href="([^"]*\.csv[^"]*)"', html)
    print('CSV links:', links[:10])
    links2 = re.findall(r'href="([^"]*download[^"]*)"', html)
    print('Download links:', links2[:10])
    # print any URL with zip or data
    links3 = re.findall(r'href="([^"]*(?:zip|data|file)[^"]*)"', html)
    print('Data links:', links3[:10])
except Exception as e:
    print('FAIL:', repr(e))
