FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Instalação dos pacotes essenciais
RUN apt-get update && apt-get install -y --no-install-recommends \
    kea-dhcp4-server \
    nftables \
    python3-flask \
    python3-pip \
    iproute2 \
    curl \
    jq \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Diretórios de trabalho
RUN mkdir -p /api /etc/kea /etc/nftables

# Copia o script de entrada (vazio por enquanto, você o preencherá depois)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Porta exposta pela API
EXPOSE 8080

# O entrypoint será responsável por iniciar todos os serviços
ENTRYPOINT ["/entrypoint.sh"]