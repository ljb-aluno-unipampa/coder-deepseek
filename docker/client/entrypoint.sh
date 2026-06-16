#!/bin/bash
# Cliente aguardando configuração via DHCP
echo "Cliente iniciado. Obtendo configuração via DHCP..."
dhclient -v
# Manter container vivo
tail -f /dev/null