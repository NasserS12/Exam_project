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
apt-get install -y lynis fail2ban libpam-tmpdir apt-listchanges debsums apt-show-versions

# Remove leftover config files of packages that were already removed
dpkg -l | awk '/^rc/ {print $2}' | xargs -r dpkg --purge

# Legal warning shown before login
cp "$SCRIPT_DIR/issue-banner.txt" /etc/issue
cp "$SCRIPT_DIR/issue-banner.txt" /etc/issue.net

# Block network protocols and USB storage this server never uses
cp "$SCRIPT_DIR/modprobe-hardening.conf" /etc/modprobe.d/hardening.conf

# Only root can run compilers (the app is built inside Docker, not on the host)
for compiler in as cc gcc g++; do
    path="$(command -v "$compiler" || true)"
    if [ -n "$path" ]; then
        chmod o-rx "$(readlink -f "$path")"
    fi
done

cp "$SCRIPT_DIR/sshd-hardening.conf" /etc/ssh/sshd_config.d/00-hardening.conf
sshd -t
systemctl restart ssh

cp "$SCRIPT_DIR/fail2ban-jail.local" /etc/fail2ban/jail.local
systemctl enable fail2ban
systemctl restart fail2ban

ufw default deny incoming
ufw default allow outgoing
ufw limit OpenSSH
ufw allow 80,443/tcp
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
