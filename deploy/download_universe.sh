#!/usr/bin/env bash
# Scarica i dati dell'universo da Dukascopy (gratis, cloud) nella cache locale.
# Da lanciare UNA VOLTA sul VPS (e all'occorrenza per aggiornare). Idempotente.
#
#   bash deploy/download_universe.sh          # daily (storia lunga) per tutti
#   bash deploy/download_universe.sh --m1     # aggiunge M1 (per lo sweep intraday)
#
# Nota: l'M1 di Dukascopy copre ~3 anni; il daily 15-23 anni. Il resampler deriva
# tutti gli altri timeframe (H1/H4/W) da questi due — non si scarica altro.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python

SYMBOLS=(US500 NAS100 US30 DAX UK100 \
         EUR_USD GBP_USD USD_JPY AUD_USD USD_CHF USD_CAD NZD_USD \
         XAU_USD XAG_USD WTI BRENT NATGAS COPPER)

echo "== Daily (storia lunga) =="
for s in "${SYMBOLS[@]}"; do
  echo "-- $s D"
  $PY -m src.backtest.data_fetcher --source dukascopy --instrument "$s" --tf D --years 25 || echo "   (saltato $s D)"
done

if [[ "${1:-}" == "--m1" ]]; then
  echo "== M1 (per lo sweep intraday, ~3 anni) =="
  for s in "${SYMBOLS[@]}"; do
    echo "-- $s M1"
    $PY -m src.backtest.data_fetcher --source dukascopy --instrument "$s" --tf M1 || echo "   (saltato $s M1)"
  done
fi
echo "Fatto. Dati in raw/cache/."
