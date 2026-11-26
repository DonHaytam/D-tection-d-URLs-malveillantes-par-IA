"""Produce the professional DOCX report.

The authoritative, fully styled generator is ``scripts/gen_docx.py``. This
compatibility entry point simply delegates to it so that running either script
always yields the same professional document instead of overwriting it with a
basic conversion.
"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
runpy.run_path(os.path.join(HERE, "gen_docx.py"))
