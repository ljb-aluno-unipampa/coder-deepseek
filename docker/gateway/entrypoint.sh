#!/bin/bash
set -e

echo "==> Configurando interface LAN (eth1)"
ip link set eth1 up
if ! ip addr show eth1 | grep -q "${GATEWAY_LAN_IP:-192.168.100.1}"; then
    ip addr add ${GATEWAY_LAN_IP:-192.168.100.1}/24 dev eth1
    echo "IP ${GATEWAY_LAN_IP:-192.168.100.1}/24 adicionado à eth1"
else
    echo "IP já configurado em eth1"
fi

echo "==> Habilitando IP forwarding"
sysctl -w net.ipv4.ip_forward=1

echo "==> Aplicando regras nftables (NAT + Firewall)"
nft -f /etc/nftables/ruleset.nft

echo "==> Gerando configuração do Kea a partir do template"
envsubst < /kea-dhcp4.conf.template > /etc/kea/kea-dhcp4.conf

echo "==> Iniciando Kea DHCP Server em background"
kea-dhcp4 -c /etc/kea/kea-dhcp4.conf &

echo "==> Iniciando API Administrativa em background"
python3 /api/app.py &

echo "==> Gateway pronto. NAT, firewall, DHCP e API ativos."
tail -f /dev/null