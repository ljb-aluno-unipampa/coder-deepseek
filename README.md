# Laboratório de Gateway Dockerizado

Laboratório reprodutível para disciplina de mestrado que simula um ambiente de rede com um **gateway** contendo:

- Servidor DHCPv4 (**Kea**)
- NAT / Firewall stateful (**nftables**)
- API administrativa e interface web (**Python/Flask**)

Todo o sistema é executado em contêineres **Docker** com **Ubuntu 24.04**, proporcionando isolamento real entre a rede LAN (totalmente interna) e a rede WAN (externa).

## 🧱 Arquitetura

Consulte o [documento detalhado de arquitetura](docs/arquitetura.md).

**Resumo:**
- Rede `wan` (bridge, com acesso à Internet)
- Rede `lan` (bridge, `internal: true` – completamente isolada)
- Contêiner `gateway` com duas interfaces:  
  `eth0` na WAN, `eth1` na LAN (IP fixo `192.168.100.1`).
- Contêineres `client1` e `client2` conectados apenas à LAN, obtendo IP via DHCP do gateway.
- O gateway aplica NAT (masquerade) para que os clientes acessem a Internet, e firewall stateful que protege a LAN e expõe apenas a API (porta 8080).

## ⚙️ Pré‑requisitos

- Docker (versão 20.10 ou superior)
- Docker Compose (versão 2.x ou superior)
- Git (para clonar o repositório)

## 🚀 Como usar

1. Clone o repositório e acesse o diretório:

   ```bash
   git clone <url-do-repo> lab-gateway-docker
   cd lab-gateway-docker
   ```
2. Copie o arquivo de variáveis de ambiente e ajuste se desejar:
   `cp .env.example .env`

3. Construa e suba os contêineres:
    `docker-compose up -d`

4. Verifique os logs do gateway:
    `docker logs gateway`

5. Acesse a interface web administrativa:
    Abra http://localhost:8080 no navegador.

6. Teste a conectividade a partir de um cliente LAN:
    ```bash
    docker exec client1 ping -c 3 8.8.8.8
    docker exec client1 curl -s ifconfig.me
    ```

## 🔧 Configuração
As principais variáveis estão em .env (veja .env.example):

Variável	Descrição	Padrão
LAN_SUBNET	Sub-rede da LAN	192.168.100.0/24
GATEWAY_LAN_IP	IP do gateway na LAN	192.168.100.1
DHCP_POOL_START	Início do pool DHCP	192.168.100.100
DHCP_POOL_END	Fim do pool DHCP	192.168.100.200
DHCP_DNS_SERVERS	Servidores DNS (separados por vírgula)	8.8.8.8, 1.1.1.1
ADMIN_API_PORT	Porta exposta da API (host)	8080
ADMIN_USER	Usuário para a API	admin
ADMIN_PASSWORD	Senha para a API	lab123
LOG_LEVEL	Nível de log (não implementado)	DEBUG

## 🧪 Testes manuais
DHCP: os clientes devem obter IP automaticamente na faixa definida.

NAT: clientes alcançam a Internet (ping, curl). O IP público visto será o do gateway (ou da rede Docker).

Firewall: a partir do host, tente acessar um IP da LAN (ex.: 192.168.100.100) – deve falhar.

API: endpoints públicos (/api/status, /api/leases, /api/firewall/rules) não exigem autenticação. Endpoints de escrita (POST, DELETE) requerem autenticação HTTP Basic (usuário/senha definidos).

## 📂 Estrutura do projeto

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

## ⚠️ Riscos de segurança

Este é um ambiente de laboratório; em produção, considere:

Privilégios: O gateway roda em modo privileged por conveniência. Em um cenário real, utilize capabilities estritas (NET_ADMIN, NET_RAW).

Autenticação: As credenciais da API são passadas via variáveis de ambiente e transmitidas em texto plano (HTTP Basic). Use HTTPS e mecanismos de sessão robustos em produção.

Exposição: Apenas a porta 8080 é exposta no host. O firewall interno restringe acessos à LAN.

Persistência: As regras de firewall adicionadas via API são voláteis (somem ao reiniciar). Para persistência, seria necessário modificar o ruleset base.

Arquitetura do Laboratório de Gateway Dockerizado
Visão geral
O objetivo é simular um pequeno escritório ou laboratório de redes onde uma máquina atua como gateway entre uma rede interna isolada (LAN) e a rede externa (WAN/Internet). Todos os componentes são empacotados em contêineres Docker para garantir reprodutibilidade.

Diagrama de topologia
```text
                  Internet / Rede do Host
                         │
                  ┌──────▼───────┐
                  │   gateway    │
                  │ eth0 (WAN)   │  ← IP dinâmico (rede wan)
                  │              │
                  │ eth1 (LAN)   │  ← 192.168.100.1/24
                  │              │
                  │ - Kea DHCP   │
                  │ - nftables   │
                  │ - Flask API  │
                  └──────┬───────┘
                         │ (rede lan, internal)
        ┌────────────────┼────────────────┐
   ┌────▼────┐      ┌────▼────┐
   │ cliente1│      │ cliente2│
   │ IP DHCP │      │ IP DHCP │
   └─────────┘      └─────────┘
```

Rede WAN (wan): bridge Docker normal, com acesso externo. O gateway obtém um endereço nessa rede (via DHCP do Docker).

Rede LAN (lan): bridge Docker com internal: true. Nenhum tráfego externo pode entrar ou sair dessa rede sem passar pelo gateway.

Gateway: contêiner com duas interfaces virtuais (eth0 e eth1). Executa os serviços críticos: servidor DHCP, NAT/firewall e API administrativa.

Clientes: contêineres Ubuntu 24.04 conectados exclusivamente à LAN. Não possuem nenhuma configuração de rede manual; dependem do DHCP para obter IP, rota padrão e servidores DNS.


## Componentes internos do gateway
### 1. Kea DHCPv4
Arquivo de configuração gerado a partir do template kea-dhcp4.conf.template usando envsubst.

Atende apenas na interface eth1.

Distribui endereços do pool definido (DHCP_POOL_START a DHCP_POOL_END), além de informar roteador padrão (192.168.100.1) e servidores DNS.

As concessões são armazenadas no arquivo CSV /var/lib/kea/kea-leases4.csv.

### 2. nftables (NAT + Firewall)
O arquivo nftables/ruleset.nft contém duas tabelas:

Tabela inet nat: cadeia postrouting com regra de masquerade para todo tráfego saindo pela eth0. Isso permite que os clientes da LAN acessem a Internet com o IP do gateway.

Tabela inet filter:

Cadeia input (proteção local): política drop. Aceita tráfego de loopback, conexões já estabelecidas, todo tráfego vindo da eth1 (LAN) e apenas a porta 8080 (API) na interface eth0 (WAN).

Cadeia forward (roteamento): política drop. Aceita pacotes de retorno de conexões estabelecidas e novas conexões iniciadas da LAN (eth1) para a WAN (eth0). Nenhuma conexão iniciada da WAN para a LAN é permitida, a menos que regras adicionais sejam inseridas via API.

O encaminhamento IP é ativado com sysctl net.ipv4.ip_forward=1 no script de inicialização.

### 3. API Administrativa (Flask)
Aplicação Python servida pelo Flask na porta 8080. Fornece endpoints para monitoramento e controle:

GET /api/status – uptime e informações das interfaces de rede.

GET /api/leases – lista de concessões DHCP ativas (leitura do CSV do Kea).

GET /api/firewall/rules – regras atuais da cadeia forward (tabela filter).

POST /api/firewall/rule – adiciona uma regra temporária na cadeia forward (requer autenticação Basic).

DELETE /api/firewall/rule/<handle> – remove uma regra pelo seu identificador (handle).

/ – painel web que consome os endpoints acima e oferece formulários para administração.

A autenticação é feita por HTTP Basic, com credenciais definidas pelas variáveis ADMIN_USER e ADMIN_PASSWORD.

### 4. Interface Web
O painel (/) é uma página HTML com Bootstrap 5 e JavaScript puro. Ele:

Exibe o status do gateway (uptime, IPs das interfaces).

Lista as concessões DHCP ativas.

Mostra as regras do firewall e permite adicionar/remover regras mediante autenticação.

#### Fluxo de inicialização
O script entrypoint.sh do gateway segue a seguinte ordem:

Configura a interface eth1 com o IP estático 192.168.100.1/24.

Habilita o encaminhamento de pacotes IPv4.

Aplica o ruleset do nftables.

Gera a configuração do Kea a partir do template e variáveis de ambiente.

Inicia o servidor Kea em segundo plano.

Inicia a API Flask em segundo plano.

Mantém o contêiner vivo com tail -f /dev/null.

#### Isolamento da LAN
A rede lan é definida no docker-compose.yml com internal: true. Essa configuração faz com que o Docker:

Impeça que contêineres nessa rede recebam qualquer conectividade externa (a não ser via outro contêiner com interface também nessa rede).

O gateway, por estar conectado às duas redes, age como o único ponto de saída. O firewall reforça esse isolamento.

#### Segurança
Apenas a porta 8080 do gateway é mapeada para o host. O acesso ao Kea (porta 67/UDP) e demais serviços ficam restritos às redes internas.

O nftables protege o próprio gateway com política input drop, reduzindo a superfície de ataque.

A API exige autenticação para operações de modificação, mas endpoints de leitura são públicos para facilitar o monitoramento didático.

O uso de privileged: true no contêiner gateway é uma concessão para simplificar a manipulação de interfaces e regras de firewall. Em um ambiente de produção, deve‑se usar capabilities seletivas e namespaces de rede mais restritos.

As regras de firewall adicionadas via API são efêmeras; não sobrevivem à reinicialização do contêiner.

#### Extensibilidade
A arquitetura permite:

Adicionar mais clientes LAN simplesmente replicando o serviço no docker-compose.yml.

Incluir regras de firewall persistentes editando o ruleset.nft antes da construção.

Substituir o servidor DHCP (Kea) por outra solução, alterando apenas o template e a instalação no Dockerfile.

Expandir a API com novos endpoints (ex.: estatísticas de tráfego, configuração de DNS, etc.).


---

**Como usar:**
1. Copie o conteúdo do primeiro bloco e salve como `README.md` na raiz do projeto.
2. Copie o conteúdo do segundo bloco e salve como `docs/arquitetura.md` (crie a pasta `docs/` se ainda não existir).
3. Se preferir fazer isso via terminal, você pode usar o comando `cat > arquivo <<EOF ... EOF` para cada um.

Se ainda assim houver problemas de cópia, posso tentar compactar os dois arquivos em um formato diferente, mas acredito que agora esteja direto.
