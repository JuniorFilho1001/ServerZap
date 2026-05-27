import sqlite3
from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

usuarios_conectados = {}


# ======================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS (SQLITE)
# ======================================================================
def init_db():
    conn = sqlite3.connect('pyzap.db')
    cursor = conn.cursor()
    # Cria a tabela de histórico de mensagens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remetente TEXT NOT NULL,
            destinatario TEXT NOT NULL,
            texto TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


# Inicializa o banco de dados assim que o script roda
init_db()


# ======================================================================


@socketio.on('registrar_usuario')
def handle_registrar(data):
    nome_usuario = data.get('usuario')
    if nome_usuario:
        usuarios_conectados[nome_usuario] = request.sid
        print(f"✨ Usuário [{nome_usuario}] registrado.")


# NOVO EVENTO: Envia o histórico antigo para o Android quando ele pedir
@socketio.on('pedir_historico')
def handle_pedir_historico(data):
    user1 = data.get('usuario')
    user2 = data.get('contato')

    conn = sqlite3.connect('pyzap.db')
    cursor = conn.cursor()

    # Busca todas as mensagens trocadas entre esses dois usuários (de A para B ou de B para A)
    cursor.execute('''
        SELECT remetente, texto FROM mensagens 
        WHERE (remetente = ? AND destinatario = ?) 
           OR (remetente = ? AND destinatario = ?)
        ORDER BY id ASC
    ''', (user1, user2, user2, user1))

    linhas = cursor.fetchall()
    conn.close()

    # Formata as mensagens em uma lista de dicionários para o Socket enviar
    historico = [{"remetente": r, "texto": t} for r, t in linhas]

    # Envia o histórico de volta APENAS para quem pediu (request.sid)
    emit('receber_historico', historico, to=request.sid)


@socketio.on('enviar_mensagem')
def handle_enviar_mensagem(data):
    remetente = data.get('remetente')
    destinatario = data.get('destinatario')
    texto = data.get('texto')

    # SALVAR NO BANCO DE DADOS ANTES DE ENVIAR
    conn = sqlite3.connect('pyzap.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO mensagens (remetente, destinatario, texto) VALUES (?, ?, ?)',
        (remetente, destinatario, texto)
    )
    conn.commit()
    conn.close()

    # Repassa a mensagem em tempo real para o destinatário (se ele estiver online)
    if destinatario in usuarios_conectados:
        sid_destinatario = usuarios_conectados[destinatario]
        emit('receber_mensagem', {'remetente': remetente, 'texto': texto}, to=sid_destinatario)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)