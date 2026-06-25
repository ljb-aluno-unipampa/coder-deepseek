# Laboratorio de Gateway Dockerizado

Artefato reprodutivel para simular uma rede local isolada com um gateway Linux
dockerizado. O gateway executa DHCPv4 com Kea, NAT/firewall stateful com
nftables e uma API administrativa em Flask para observacao e alteracao
temporaria de regras.

Artigo associado: o titulo formal e o resumo do artigo nao estao incluidos no
repositorio. Para fins de avaliacao do artefato, este README documenta a
reivindicacao tecnica implementada: e possivel reproduzir, em uma unica maquina
com Docker, uma topologia LAN/WAN na qual clientes recebem endereco via DHCP,
saem para a Internet apenas pelo gateway e podem ser observados por uma API web.

## Estrutura do README.md

Este documento esta organizado da seguinte forma:

- `Informacoes basicas`: ambiente necessario para executar e replicar os testes.
- `Dependencias`: softwares, imagens, pacotes e recursos externos utilizados.
- `Preocupacoes com seguranca`: riscos e cuidados recomendados.
- `Instalacao`: passos para obter, configurar e iniciar o artefato.
- `Teste minimo`: validacao rapida de funcionamento.
- `Experimentos`: passos para reproduzir as principais reivindicacoes.
- `LICENSE`: licenca do projeto.

## Estrutura do repositorio

```text
coder-deepseek/
├── api/
│   ├── app.py                      # API Flask e painel web
│   ├── static/css/style.css
│   └── templates/index.html
├── docker/
│   ├── client/
│   │   ├── Dockerfile              # Imagem dos clientes LAN
│   │   └── entrypoint.sh           # Solicita IP via DHCP e mantem o container vivo
│   └── gateway/
│       ├── Dockerfile              # Imagem do gateway
│       ├── entrypoint.sh           # Inicializa rede, nftables, Kea e API
│       └── requirements.txt
├── docs/arquitetura.md             # Nota de arquitetura
├── kea/
│   ├── kea-dhcp4.conf              # Exemplo de configuracao gerada
│   └── kea-dhcp4.conf.template     # Template usado no startup
├── nftables/ruleset.nft            # Regras base de NAT/firewall
├── scripts/test_connectivity.sh    # Reservado para testes auxiliares
├── docker-compose.yml              # Topologia experimental
├── env.example                     # Variaveis de ambiente opcionais
├── LICENSE
└── README.md
```

## Informacoes basicas

O ambiente cria tres containers:

- `gateway`: conectado a rede `wan` (`eth0`) e a rede `lan` (`eth1`). Usa o IP
  `192.168.100.1/24` na LAN, habilita encaminhamento IPv4, aplica NAT/firewall,
  executa Kea DHCPv4 e expoe a API administrativa na porta `8080`.
- `client1` e `client2`: conectados apenas a rede `lan`. O endereco inicial
  atribuido pelo Docker e removido no startup, e o endereco operacional e obtido
  via DHCP do gateway.

Topologia:

```text
Internet / host Docker
        |
      wan
        |
  eth0 gateway eth1 (192.168.100.1)
        |
      lan internal
        |
   client1, client2
```

Requisitos de software no host:

- Linux Ubuntu 24.04 ou superior, ou distribuicao Linux equivalente com suporte
  a Docker Engine e redes bridge.
- Docker Engine 20.10 ou superior.
- Docker Compose v2 ou superior (`docker compose ...`).
- Git para obter o repositorio.
- Acesso a Internet durante o build para baixar a imagem `ubuntu:24.04` e
  pacotes dos repositorios Ubuntu.
- `curl` e `jq` no host sao recomendados para executar os comandos de validacao
  do README; nao sao necessarios para iniciar os containers.

Requisitos de hardware estimados:

- CPU: 2 vCPUs ou mais. A validacao local foi feita em CPU AMD Ryzen 5600X.
- Memoria: 1 GB livre para execucao; 2 GB recomendados durante o build. O host
  de desenvolvimento usado como referencia possui 8 GB de RAM.
- Disco: 2 GB livres para imagens, camadas e cache; SSD recomendado para build
  e recriacao mais rapidos.
- Rede: acesso externo para baixar dependencias e testar NAT.

Nao e necessario instalar Kea, nftables, Flask, Python ou pacotes pip
diretamente no host. Esses componentes sao instalados dentro das imagens Docker
pelos respectivos `Dockerfile`.

## Dependencias

O artefato nao depende de benchmark externo. A validacao e feita por comandos de
rede executados nos containers.

Dependencias principais:

- Imagem base: `ubuntu:24.04`.
- Gateway:
  - `kea-dhcp4-server` para DHCPv4.
  - `nftables` para NAT e firewall.
  - `python3-flask` para API e interface web.
  - `iproute2`, `curl`, `jq`, `dnsutils`, `gettext-base`.
- Clientes:
  - `isc-dhcp-client` para solicitar lease DHCP.
  - `iproute2` para inspecao/configuracao de rede.
  - `iputils-ping`, `curl`, `jq`, `dnsutils` para testes.

Dependencias Python:

- A API usa Flask instalado pelo pacote Ubuntu `python3-flask`.
- O arquivo `docker/gateway/requirements.txt` existe no repositorio, mas o
  build atual nao executa `pip install` a partir dele. Portanto, nao ha
  requisito de `pip` no host para a execucao via Docker Compose.

As versoes exatas dos pacotes sao resolvidas pelos repositorios do Ubuntu 24.04
no momento do build. Em uma execucao validada, o Kea reportou versao `2.4.1`.

Variaveis configuraveis em `.env`:

```text
LAN_SUBNET=192.168.100.0/24
LAN_DOCKER_GATEWAY=192.168.100.254
GATEWAY_LAN_IP=192.168.100.1
DHCP_POOL_START=192.168.100.100
DHCP_POOL_END=192.168.100.200
DHCP_DNS_SERVERS=8.8.8.8, 1.1.1.1
ADMIN_API_PORT=8080
ADMIN_USER=admin
ADMIN_PASSWORD=lab123
LOG_LEVEL=DEBUG
```

## Preocupacoes com seguranca

Este artefato deve ser executado em ambiente de laboratorio, preferencialmente
em uma VM ou maquina descartavel.

Riscos e mitigacoes:

- O container `gateway` usa `privileged: true` para manipular interfaces,
  encaminhamento IPv4 e nftables. Nao execute em hosts de producao.
- A regra `flush ruleset` existe dentro do arquivo nftables aplicado no
  namespace de rede do container. Ainda assim, por usar modo privilegiado,
  recomenda-se isolar a avaliacao em uma maquina sem regras criticas no host.
- A API expoe a porta `8080` no host. Endpoints de leitura sao publicos; apenas
  escrita exige HTTP Basic.
- As credenciais padrao (`admin`/`lab123`) sao fracas e trafegam por HTTP sem
  TLS. Altere `ADMIN_USER` e `ADMIN_PASSWORD` em `.env` se a porta ficar
  acessivel a terceiros.
- As regras adicionadas pela API sao temporarias e desaparecem ao recriar o
  container.

Para encerrar e remover os recursos criados:

```bash
docker compose down --remove-orphans
```

## Instalacao

1. Clone o repositorio e entre no diretorio:

   ```bash
   git clone <url-do-repositorio> coder-deepseek
   cd coder-deepseek
   ```

2. Crie o arquivo `.env` a partir do exemplo:

   ```bash
   cp env.example .env
   ```

3. Opcionalmente edite `.env` para alterar sub-rede, pool DHCP, porta da API ou
   credenciais administrativas.

4. Construa e inicie o ambiente:

   ```bash
   docker compose up --build -d
   ```

5. Verifique se os containers estao ativos:

   ```bash
   docker compose ps
   ```

Ao final da instalacao, a interface web/API deve estar disponivel em
`http://localhost:8080`.

## Teste minimo

O teste minimo valida se a aplicacao subiu, se o DHCP funcionou e se um cliente
consegue sair para a Internet via gateway. Tempo esperado: menos de 2 minutos
apos o build inicial.

1. Verifique o estado dos containers:

   ```bash
   docker compose ps
   ```

   Resultado esperado: `gateway`, `client1` e `client2` com status `Up`.

2. Consulte a API:

   ```bash
   curl -fsS http://localhost:8080/api/status | jq -r '.status'
   ```

   Resultado esperado:

   ```text
   running
   ```

3. Verifique o endereco DHCP do `client1`:

   ```bash
   docker exec client1 ip -4 addr show eth0
   docker exec client1 ip route show
   ```

   Resultado esperado: endereco dinamico na faixa `192.168.100.100-200` e rota
   padrao `default via 192.168.100.1`.

4. Teste conectividade externa:

   ```bash
   docker exec client1 ping -c 2 8.8.8.8
   docker exec client1 curl -fsS --max-time 10 http://example.com | head -n 1
   ```

   Resultado esperado: `0% packet loss` no ping e retorno HTML do
   `example.com`.

## Experimentos

Os experimentos abaixo reproduzem as principais reivindicacoes tecnicas do
artefato. Cada experimento pressupoe que a instalacao ja foi concluida.

### Reivindicacao #1: clientes LAN recebem configuracao via DHCP

Objetivo: demonstrar que os clientes nao dependem de configuracao manual e
recebem IP, rota e DNS a partir do gateway Kea.

Arquivos relevantes:

- `kea/kea-dhcp4.conf.template`
- `docker/client/entrypoint.sh`
- `.env`

Comandos:

```bash
docker logs gateway | grep DHCP4_LEASE_ALLOC
docker exec client1 ip -4 addr show eth0
docker exec client2 ip -4 addr show eth0
docker exec client1 ip route show
```

Tempo esperado: menos de 30 segundos depois dos containers iniciarem.

Recursos esperados: menos de 1 GB de RAM e baixo uso de CPU.

Resultado esperado:

- Logs do gateway contendo eventos `DHCP4_LEASE_ALLOC`.
- `client1` e `client2` com enderecos dinamicos dentro do pool DHCP.
- Rota padrao dos clientes apontando para `192.168.100.1`.

Para alterar o experimento, edite `.env`:

```text
DHCP_POOL_START=192.168.100.120
DHCP_POOL_END=192.168.100.130
```

Depois recrie:

```bash
docker compose down --remove-orphans
docker compose up --build -d
```

### Reivindicacao #2: a LAN isolada acessa a Internet apenas via gateway

Objetivo: demonstrar que a rede `lan` e `internal: true`, e que a saida externa
dos clientes ocorre por encaminhamento IPv4 e NAT no gateway.

Arquivos relevantes:

- `docker-compose.yml`
- `nftables/ruleset.nft`
- `docker/gateway/entrypoint.sh`

Comandos:

```bash
docker exec gateway sysctl net.ipv4.ip_forward
docker exec gateway nft list ruleset
docker exec client1 ip route show
docker exec client1 ping -c 2 8.8.8.8
docker exec client1 curl -fsS --max-time 10 http://example.com | head -n 1
```

Tempo esperado: menos de 1 minuto.

Recursos esperados: menos de 1 GB de RAM; trafego de rede minimo.

Resultado esperado:

- `net.ipv4.ip_forward = 1`.
- Ruleset com `oifname "eth0" masquerade`.
- Rota padrao do cliente via `192.168.100.1`.
- Ping externo com `0% packet loss`.
- Requisicao HTTP externa bem-sucedida.

### Reivindicacao #3: o firewall stateful bloqueia encaminhamento nao permitido

Objetivo: demonstrar que o firewall aceita conexoes LAN -> WAN e respostas
estabelecidas, mas nao libera novos fluxos WAN -> LAN por padrao.

Arquivos relevantes:

- `nftables/ruleset.nft`
- `api/app.py`

Comandos:

```bash
docker exec gateway nft list chain inet filter forward
docker exec gateway nft list chain inet filter input
curl -fsS http://localhost:8080/api/firewall/rules | jq .
```

Tempo esperado: menos de 30 segundos.

Recursos esperados: uso irrelevante de CPU/RAM.

Resultado esperado:

- Cadeia `forward` com politica `drop`.
- Regra permitindo `ct state established,related`.
- Regra permitindo `iifname "eth1" oifname "eth0" accept`.
- Nenhuma regra padrao permitindo novas conexoes da WAN para a LAN.

### Reivindicacao #4: a API administrativa permite observacao do gateway

Objetivo: demonstrar que o artefato expoe estado operacional por HTTP e
consulta leases DHCP gravados pelo Kea.

Arquivos relevantes:

- `api/app.py`
- `api/templates/index.html`

Comandos:

```bash
curl -fsS http://localhost:8080/api/status | jq '.status, .uptime_seconds'
curl -fsS http://localhost:8080/api/leases | jq .
curl -fsS http://localhost:8080/api/firewall/rules | jq .
```

Tempo esperado: menos de 30 segundos.

Recursos esperados: uso irrelevante de CPU/RAM.

Resultado esperado:

- `/api/status` retorna `running`, uptime e interfaces.
- `/api/leases` retorna uma lista de leases, apos os clientes obterem DHCP.
- `/api/firewall/rules` retorna a representacao JSON das regras nftables.

Operacoes de escrita exigem autenticacao Basic. Exemplo de chamada autenticada:

```bash
curl -u admin:lab123 -X POST http://localhost:8080/api/firewall/rule \
  -H 'Content-Type: application/json' \
  -d '{"expression":"ip saddr 192.168.100.100 accept"}'
```

Observacao: regras adicionadas por esse endpoint sao temporarias e devem ser
removidas manualmente ou descartadas recriando o ambiente.

## LICENSE

Este projeto esta licenciado sob a licenca BSD 3-Clause. Consulte o arquivo
`LICENSE` para o texto completo.
