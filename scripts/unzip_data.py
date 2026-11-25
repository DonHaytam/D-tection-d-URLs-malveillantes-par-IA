import os
import zipfile

BASE = "D:/openhands/projects/SI project"
ZIP = os.path.join(BASE, "data", "raw", "phiusiil_phishing_url_dataset.zip")

with zipfile.ZipFile(ZIP, "r") as z:
    for n in z.namelist():
        print("ENTRY:", n)
    z.extractall(os.path.join(BASE, "data", "raw"))

print("DONE")
