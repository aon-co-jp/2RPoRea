export PATH="$HOME/.cargo/bin:$PATH"
cd /mnt/f/2RPoRea/.tmp-v/out/backend-php
CARGO_TARGET_DIR=/tmp/php2r cargo build 2>&1 | tail -5
ls /tmp/php2r/debug | head
PORT=18777 /tmp/php2r/debug/php-ported >/tmp/php2r.log 2>&1 &
sleep 2
curl -s -w ' %{http_code}\n' http://127.0.0.1:18777/hello/admin
curl -s -w ' %{http_code}\n' http://127.0.0.1:18777/hello/Taro
kill %1
