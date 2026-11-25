import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master/scripts/data_expansion")

import pandas as pd
from src.data.provenance import registrable_domain
from src.data.validation import extract_components

SH = {'bit.ly', 't.co', 'goo.gl', 'tinyurl.com', 'is.gd', 'buff.ly', 'ow.ly', 'rb.gy',
      'cutt.ly', 'shorturl.at', 'rebrand.ly', 'tiny.cc', 'lnkd.in', 't.ly', 's.id',
      'v.gd', 'qr.ae', 'adf.ly', 'sh.st', 'clck.ru', 'shorturl.com', 'tiny.one',
      'urlz.fr', 'x.co', 'me2.do', 'j.mp', 'bit.do', 'soo.gd', 'trib.al', 'dlvr.it',
      'ift.tt', 'wp.me', 'flip.it', 'po.st', 'snip.ly', 'surl.li', 'shorte.st', 'tr.ee'}
FR = {'3utilities.com', 'ocry.com', 'mefound.com', '000webhostapp.com', 'weebly.com',
      'wixsite.com', 'blogspot.com', 'wordpress.com', 'github.io', 'gitlab.io',
      'netlify.app', 'vercel.app', 'herokuapp.com', 'glitch.me', 'repl.co',
      'firebaseapp.com', 'web.app', 'pages.dev', 'workers.dev', 'rf.gd', '42web.io',
      'infinityfree.net', 'epizy.com', 'byethost.com', 'freehostia.com', 'awardspace.com',
      '000space.com', 'x10.bz', 'in.net', 'pe.hu', 'esy.es', 'hol.es', '16mb.com',
      'my.id', 'web.id', 'site88.net', 'freewebhostingarea.com', 'atw.hu', 'thats.im',
      'youdontcare.com', 'babinet.cz', 'home.pl', 'pp.ua', 'pp.ru'}
DC = {'docs.google.com', 'drive.google.com', 'forms.gle', 'script.google.com',
      'sites.google.com', 'forms.office.com', 'outlook.office.com', 'onedrive.live.com',
      'sharepoint.com', 'notion.so', 'notion.site', 'airtable.com', 'typeform.com',
      'jotform.com', 'cognitoforms.com', 'paperform.co', 'forms.app', 'surveyheart.com',
      'sendgrid.net', 'mailchimp.com', 'list-manage.com'}
CL = {'amazonaws.com', 'cloudfront.net', 'azurewebsites.net', 'appspot.com',
      'googleusercontent.com', 'windows.net', 'digitaloceanspaces.com',
      'storage.googleapis.com', 'r2.dev', 'backblazeb2.com', 'linodeobjects.com'}


def p(u):
    try:
        h = extract_components(u)["host"].lower()
    except Exception:
        return "other"
    rd = registrable_domain(h)
    if any(h == x or h.endswith("." + x) for x in DC):
        return "doc"
    if rd in SH:
        return "shortener"
    if any(rd == x or rd.endswith("." + x) for x in FR):
        return "free"
    if any(rd == x or rd.endswith("." + x) for x in CL):
        return "cloud"
    return "other"


R = "D:/openhands/projects/v2/phishing_ai_master"
for name, path in [("DEV", "data/splits/DEV.csv"), ("EXT_DEV", "data/integrated/external_dev.csv")]:
    df = pd.read_csv(f"{R}/{path}", usecols=["url", "label"])
    df["platform"] = df["url"].map(p)
    print(name)
    print(pd.crosstab(df.platform, df.label).to_string())
