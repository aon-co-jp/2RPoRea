cd /mnt/f/2RPoRea/.tmp-v
export PYTHONPATH=/mnt/f/2RPoRea/src
python3 -m torporea convert src -o out --rpoem-path /mnt/f/RPoem 2>&1 | tail -8
find out -maxdepth 3 -name Cargo.toml
