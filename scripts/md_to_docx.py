"""Convert RAPPORT_FINAL_MASTER_IA.md to DOCX."""
import sys, os, re
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
md_path = os.path.join(ROOT, "reports", "RAPPORT_FINAL_MASTER_IA.md")
docx_path = os.path.join(ROOT, "reports", "RAPPORT_FINAL_MASTER_IA.docx")

doc = Document()
# base style
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

with open(md_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

i = 0
while i < len(lines):
    line = lines[i].rstrip("\n")
    # heading
    m = re.match(r"^(#{1,6})\s+(.*)$", line)
    if m:
        level = len(m.group(1))
        text = m.group(2)
        h = doc.add_heading(text, level=min(level, 4))
        i += 1
        continue
    # table
    if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-\s|]+\|$", lines[i+1].strip()):
        # parse table
        header = [c.strip() for c in line.strip().strip("|").split("|")]
        i += 2  # skip header + separator
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
            i += 1
        t = doc.add_table(rows=1, cols=len(header))
        t.style = "Table Grid"
        for j, h in enumerate(header):
            t.rows[0].cells[j].text = h
        for r in rows:
            cells = t.add_row().cells
            for j, val in enumerate(r):
                if j < len(cells):
                    cells[j].text = val
        continue
    # bullet
    if line.strip().startswith("- ") or line.strip().startswith("* "):
        text = line.strip()[2:]
        doc.add_paragraph(text, style="List Bullet")
        i += 1
        continue
    # empty line
    if line.strip() == "":
        i += 1
        continue
    # normal paragraph
    doc.add_paragraph(line)
    i += 1

doc.save(docx_path)
print("Saved", docx_path)
