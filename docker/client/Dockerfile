FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    isc-dhcp-client \
    iproute2 \
    curl \
    jq \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Copia o script de entrada (manterá o container vivo)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
