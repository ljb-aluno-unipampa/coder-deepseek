#!/bin/bash
echo "==> Cliente iniciado. Solicitando IP via DHCP..."
# Remove o endereço inicial injetado pelo Docker para validar o DHCP do laboratório.
dhclient -r eth0 2>/dev/null || true
ip addr flush dev eth0
ip link set eth0 up
dhclient -v eth0

echo "==> Configuração obtida:"
ip addr show eth0
ip route show

tail -f /dev/null
