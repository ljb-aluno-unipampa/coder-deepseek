#!/usr/bin/env python3
import subprocess
import json
import csv
import io
import os
from functools import wraps
from flask import Flask, request, jsonify, Response, render_template

app = Flask(__name__)

# ─── Configuração ─────────────────────────────────────────────────
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "lab123")
LEASES_FILE = "/var/lib/kea/kea-leases4.csv"

# ─── Autenticação ─────────────────────────────────────────────────
def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASSWORD

def authenticate():
    return Response(
        'Acesso não autorizado',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ─── Endpoints ────────────────────────────────────────────────────


@app.route('/api/status')
def status():
    """Informações básicas do gateway."""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
    except Exception:
        uptime_seconds = 0

    # IP das interfaces
    result = subprocess.run(['ip', '-j', 'addr', 'show'], capture_output=True, text=True)
    interfaces = json.loads(result.stdout) if result.returncode == 0 else []

    return jsonify({
        'status': 'running',
        'uptime_seconds': uptime_seconds,
        'interfaces': interfaces
    })

@app.route('/api/leases')
def leases():
    """Lista de concessões DHCP ativas (arquivo Kea)."""
    leases_list = []
    if os.path.exists(LEASES_FILE):
        with open(LEASES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                leases_list.append(row)
    return jsonify(leases_list)

@app.route('/api/firewall/rules')
def firewall_rules():
    """Regras atuais da tabela filter (cadeia forward)."""
    try:
        result = subprocess.run(
            ['nft', '-j', 'list', 'table', 'inet', 'filter'],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        # Extrai apenas a cadeia forward (se existir)
        table = data.get('nftables', [])
        forward_rules = []
        for item in table:
            if 'chain' in item and item['chain'].get('name') == 'forward':
                # O chain contém uma lista 'rules'? Na verdade, a estrutura:
                # {"chain": {"name": "forward", ..., "rules": [...]}}
                forward_rules = item['chain'].get('rules', [])
                break
        return jsonify(forward_rules)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Falha ao listar regras', 'detail': str(e)}), 500

@app.route('/api/firewall/rule', methods=['POST'])
@requires_auth
def add_firewall_rule():
    """Adiciona uma regra na cadeia forward da tabela inet filter."""
    data = request.get_json()
    if not data or 'expression' not in data:
        return jsonify({'error': 'Corpo JSON requerido com "expression"'}), 400

    table = data.get('table', 'inet filter')
    chain = data.get('chain', 'forward')
    expr = data['expression']

    # Para segurança, restringir operações à tabela inet filter
    if table != 'inet filter':
        return jsonify({'error': 'Apenas a tabela "inet filter" é permitida'}), 400
    if chain not in ('forward', 'input', 'output'):  # permite outras, mas com cautela
        return jsonify({'error': 'Cadeia não permitida'}), 400

    # Monta o comando nft em formato seguro (sem shell)
    # A expressão é separada em argumentos por espaços
    cmd = ['nft', '-j', 'add', 'rule', table, chain] + expr.split()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = json.loads(result.stdout)
        # Extrai o handle da resposta
        # Exemplo: {"add": {"rule": {"family": "inet", ..., "handle": 42}}}
        handle = output['add']['rule']['handle']
        return jsonify({'status': 'Regra adicionada', 'handle': handle}), 201
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Erro ao adicionar regra', 'detail': e.stderr.strip()}), 400

@app.route('/api/firewall/rule/<int:handle>', methods=['DELETE'])
@requires_auth
def delete_firewall_rule(handle):
    """Remove uma regra pelo handle."""
    cmd = ['nft', 'delete', 'rule', 'inet', 'filter', 'forward', 'handle', str(handle)]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return jsonify({'status': 'Regra removida'})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Erro ao remover regra', 'detail': e.stderr.strip()}), 400

# ─── Inicialização ────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)