@echo off
set PYTHONPATH=D:\business\account-creation\common\src;D:\business\account-creation\registrar\src
cd /d D:\business\account-creation\registrar
python -m uvicorn src.api.app:app --port 8709 --host 0.0.0.0