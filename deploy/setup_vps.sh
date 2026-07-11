#!/usr/bin/env bash
# Setup "chiavi in mano" del paper trading su VPS (Ubuntu/Debian, es. Hetzner).
# Installa: dipendenze, IB Gateway (headless via Xvfb), IBC (login automatico),
# l'ambiente Python del progetto e i servizi systemd (Gateway 24/7 + bot giornaliero).
#
# NON contiene credenziali. Le metti TU nel file deploy/ibc/config.ini sul VPS,
# che resta solo sul server (è git-ignored).
#
# Uso (come root o con sudo), dopo aver clonato la repo:
#   cd ~/Trading && sudo bash deploy/setup_vps.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IBC_VERSION="3.20.0"                       # verifica l'ultima su github.com/IbcAlpha/IBC/releases
GW_INSTALLER="ibgateway-stable-standalone-linux-x64.sh"
GW_URL="https://download2.interactivebrokers.com/installers/ibgateway/stable-standalone/${GW_INSTALLER}"
IBC_URL="https://github.com/IbcAlpha/IBC/releases/download/${IBC_VERSION}/IBCLinux-${IBC_VERSION}.zip"
INSTALL_USER="${SUDO_USER:-$USER}"

echo "== 1/6 pacchetti di sistema =="
apt-get update -y
apt-get install -y openjdk-17-jre-headless xvfb unzip curl git python3-venv python3-pip

echo "== 2/6 IB Gateway =="
if [ ! -d "$HOME/Jts/ibgateway" ] && [ ! -d "/root/Jts" ]; then
  curl -fsSL "$GW_URL" -o "/tmp/${GW_INSTALLER}"
  chmod +x "/tmp/${GW_INSTALLER}"
  # installazione non interattiva nella home di default (~/Jts)
  yes "" | "/tmp/${GW_INSTALLER}" -q -dir "$HOME/ibgateway" || "/tmp/${GW_INSTALLER}"
fi

echo "== 3/6 IBC (login automatico) =="
if [ ! -d "/opt/ibc" ]; then
  curl -fsSL "$IBC_URL" -o /tmp/IBC.zip
  mkdir -p /opt/ibc && unzip -o /tmp/IBC.zip -d /opt/ibc
  chmod +x /opt/ibc/*.sh /opt/ibc/scripts/*.sh || true
fi
# copia la TUA config (da compilare, vedi deploy/ibc/config.ini)
mkdir -p /opt/ibc/config
if [ -f "$REPO_DIR/deploy/ibc/config.ini" ]; then
  cp "$REPO_DIR/deploy/ibc/config.ini" /opt/ibc/config/config.ini
  echo "  -> /opt/ibc/config/config.ini (RICORDA di inserirci utente/password paper)"
fi

echo "== 4/6 ambiente Python del progetto =="
cd "$REPO_DIR"
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

echo "== 5/6 servizi systemd =="
sed "s#__REPO__#$REPO_DIR#g; s#__USER__#$INSTALL_USER#g" \
    "$REPO_DIR/deploy/systemd/ib-gateway.service" > /etc/systemd/system/ib-gateway.service
sed "s#__REPO__#$REPO_DIR#g; s#__USER__#$INSTALL_USER#g" \
    "$REPO_DIR/deploy/systemd/paper-bot.service" > /etc/systemd/system/paper-bot.service
cp "$REPO_DIR/deploy/systemd/paper-bot.timer" /etc/systemd/system/paper-bot.timer
systemctl daemon-reload

echo "== 6/6 fatto =="
cat <<'EOF'

PROSSIMI PASSI (a mano, una volta sola):
  1. Compila le credenziali paper in:  /opt/ibc/config/config.ini
     (IbLoginId=IL_TUO_UTENTE_PAPER, IbPassword=LA_TUA_PASSWORD, TradingMode=paper)
  2. Compila la repo:  cp .env.example .env  e metti IBKR_ACCOUNT_ID=DU...  (porta 4002)
  3. Avvia il Gateway:   systemctl enable --now ib-gateway
     Controlla:          journalctl -u ib-gateway -f
  4. Prova il bot a secco: ./.venv/bin/python -m src.live.paper_bot --dry-run
  5. Attiva il bot giornaliero: systemctl enable --now paper-bot.timer

Il bot gira ogni giorno alle 22:30 (Europe/Berlin) sul conto PAPER.
EOF
