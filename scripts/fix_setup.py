p = 'D:/openhands/projects/v2/phishing_ai_master/setup.bat'
with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

old = 'set "PYTHONPATH=%VENDOR_DIR%;%PROJECT_DIR%"\necho [OK] PYTHONPATH set to %PYTHONPATH%'
new = ('set "PYTHONPATH=%VENDOR_DIR%;%PROJECT_DIR%"\n'
       'set "MODEL_PATH=%PROJECT_DIR%\\models\\versions\\M1_LR_HARDNEG.joblib"\n'
       'set "META_PATH=%PROJECT_DIR%\\models\\versions\\metadata.json"\n'
       'echo [OK] PYTHONPATH set to %PYTHONPATH%\n'
       'echo [OK] MODEL_PATH set to %MODEL_PATH%')
assert old in content, 'old1 not found'
content = content.replace(old, new)

old2 = 'set PYTHONPATH=%VENDOR_DIR%;%PROJECT_DIR% && python -m uvicorn'
new2 = 'set PYTHONPATH=%VENDOR_DIR%;%PROJECT_DIR% && set MODEL_PATH=%PROJECT_DIR%\\models\\versions\\M1_LR_HARDNEG.joblib && set META_PATH=%PROJECT_DIR%\\models\\versions\\metadata.json && python -m uvicorn'
assert old2 in content, 'old2 not found'
content = content.replace(old2, new2)

with open(p, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
