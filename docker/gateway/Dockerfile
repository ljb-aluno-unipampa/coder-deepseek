FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    kea-dhcp4-server \
    nftables \
    python3-flask \
    python3-pip \
    iproute2 \
    curl \
    jq \
    dnsutils \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /api /etc/kea /etc/nftables

# Copia template do Kea (contexto = raiz do projeto)
COPY kea/kea-dhcp4.conf.template /kea-dhcp4.conf.template
COPY docker/gateway/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]