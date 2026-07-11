#!/usr/bin/env bash
# Avvia IB Gateway headless (Xvfb) con login automatico via IBC, in modalità paper.
# Chiamato dal servizio systemd ib-gateway. Rileva versione e path del Gateway.
set -euo pipefail

export DISPLAY=:1
# display virtuale (Gateway è una GUI Java)
pgrep -f "Xvfb :1" >/dev/null || (Xvfb :1 -screen 0 1024x768x24 >/tmp/xvfb.log 2>&1 &)
sleep 3

# rileva la home del Gateway (l'installer usa ~/Jts o ~/ibgateway a seconda delle versioni)
GW_DIR=""
for d in "$HOME/Jts" "$HOME/ibgateway" "/root/Jts" "/opt/ibgateway"; do
  [ -d "$d" ] && GW_DIR="$d" && break
done
[ -z "$GW_DIR" ] && { echo "IB Gateway non trovato (cerco in ~/Jts, ~/ibgateway)"; exit 1; }

# versione = prima cartella numerica dentro la home del Gateway (es. 1030)
TWS_VERSION="$(ls "$GW_DIR" | grep -oE '^[0-9]+$' | sort -rn | head -1 || true)"
[ -z "$TWS_VERSION" ] && TWS_VERSION="1030"

echo "Gateway dir=$GW_DIR versione=$TWS_VERSION → avvio IBC (paper)"
exec /opt/ibc/scripts/ibcstart.sh "$TWS_VERSION" --gateway \
    --tws-path="$GW_DIR" \
    --ibc-path=/opt/ibc \
    --ibc-ini=/opt/ibc/config/config.ini \
    --mode=paper
