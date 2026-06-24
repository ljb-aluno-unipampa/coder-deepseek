# Arquitetura do Laboratório de Gateway Dockerizado

## Visão geral

O objetivo é simular um pequeno escritório ou laboratório de redes onde uma máquina atua como **gateway** entre uma rede interna isolada (LAN) e a rede externa (WAN/Internet). Todos os componentes são empacotados em contêineres Docker para garantir reprodutibilidade.

## Diagrama de topologia

lab-gateway-docker/
├── .env.example
├── docker-compose.yml
├── docker/
│   ├── gateway/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── client/
│       ├── Dockerfile
│       └── entrypoint.sh
├── kea/
│   └── kea-dhcp4.conf.template
├── nftables/
│   └── ruleset.nft
├── api/
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── css/style.css
├── docs/
│   └── arquitetura.md
└── README.md
