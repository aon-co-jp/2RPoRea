. ~/2fa-venv/bin/activate 2>/dev/null
cd /mnt/f/2RPoRea
python3 -m pytest -q -p no:cacheprovider tests 2>&1 | tail -15
