#!/bin/bash
set -e

echo "==> Configurando interface LAN (eth1)"
ip link set eth1 up

# Atribui IP estático se ainda não configurado
if ! ip addr show eth1 | grep -q "${GATEWAY_LAN_IP:-192.168.100.1}"; then
    ip addr add ${GATEWAY_LAN_IP:-192.168.100.1}/24 dev eth1
    echo "IP ${GATEWAY_LAN_IP:-192.168.100.1}/24 adicionado à eth1"
else
    echo "IP já configurado em eth1"
fi

echo "==> Gerando configuração do Kea a partir do template"
envsubst < /kea-dhcp4.conf.template > /etc/kea/kea-dhcp4.conf

echo "==> Iniciando Kea DHCP Server em background"
kea-dhcp4 -c /etc/kea/kea-dhcp4.conf &

echo "==> Gateway pronto. DHCP ativo na LAN."
# Manter container vivo
tail -f /dev/null