#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this script with sudo." >&2
    exit 1
fi

if ! id ubuntu >/dev/null 2>&1; then
    echo "User 'ubuntu' not found. This script is meant for the AWS server only." >&2
    exit 1
fi

apt-get update && apt-get upgrade -y
ْapt-get install -y lynis fail2ban

cp "$SCRIPT_DIR/sshd-hardening.conf" /etc/ssh/sshd_config.d/00-hardening.conf
sshd -t
systemctl restart ssh

cp "$SCRIPT_DIR/fail2ban-jail.local" /etc/fail2ban/jail.local
systemctl enable fail2ban
systemctl restart fail2ban

ufw default deny incoming
ufw default allow outgoing
ufw limit OpenSSH
ufw --force enable

if [ ! -f /swapfile ]; then
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
fi

echo 'vm.swappiness=10' | tee /etc/sysctl.d/99-swappiness.conf
sysctl --system
