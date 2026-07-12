#!/usr/bin/env bash
# Avvia IB Gateway headless (Xvfb) con login automatico via IBC, in modalità paper.
# Chiamato dal servizio systemd ib-gateway. Rileva versione e path del Gateway.
set -euo pipefail

export DISPLAY=:1
# display virtuale (Gateway è una GUI Java)
pgrep -f "Xvfb :1" >/dev/null || (Xvfb :1 -screen 0 1024x768x24 >/tmp/xvfb.log 2>&1 &)
sleep 3

# IBC (gateway) si aspetta il layout:  <tws-path>/ibgateway/<versione>/jars
# Cerchiamo la base che contiene ibgateway/<num>/jars e ne ricaviamo la versione.
GW_DIR=""; TWS_VERSION=""
for base in "$HOME/Jts" "/root/Jts" "$HOME/ibgateway" "/opt/ibgateway"; do
  [ -d "$base/ibgateway" ] || continue
  v="$(ls "$base/ibgateway" 2>/dev/null | grep -oE '^[0-9]+$' | sort -rn | head -1 || true)"
  if [ -n "$v" ] && [ -d "$base/ibgateway/$v/jars" ]; then
    GW_DIR="$base"; TWS_VERSION="$v"; break
  fi
done
[ -z "$GW_DIR" ] && { echo "IB Gateway non trovato (cerco <base>/ibgateway/<versione>/jars in ~/Jts, /root/Jts, ~/ibgateway, /opt/ibgateway)"; exit 1; }

echo "Gateway dir=$GW_DIR versione=$TWS_VERSION → avvio IBC (paper)"
exec /opt/ibc/scripts/ibcstart.sh "$TWS_VERSION" --gateway \
    --tws-path="$GW_DIR" \
    --ibc-path=/opt/ibc \
    --ibc-ini=/opt/ibc/config/config.ini \
    --mode=paper
