#!/bin/bash
echo "==> Cliente iniciado. Solicitando IP via DHCP..."
# Libera lease anterior e obtém novo
dhclient -r eth0 2>/dev/null || true
dhclient -v eth0

echo "==> Configuração obtida:"
ip addr show eth0
ip route show

tail -f /dev/null
