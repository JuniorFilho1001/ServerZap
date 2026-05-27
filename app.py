import sqlite3
from flask import Flask, request
from flask_socketio import SocketIO, emit
from datetime import datetime

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
            dia   VARCHAR(10),
            hora   VARCHAR(10),
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
# NOVO EVENTO: Envia o histórico antigo para o Android quando ele pedir
@socketio.on('pedir_historico')
def handle_pedir_historico(data):
    user1 = data.get('usuario')
    user2 = data.get('contato')
    print(f"🔍 Android pediu histórico entre: {user1} e {user2}")

    conn = sqlite3.connect('pyzap.db')
    cursor = conn.cursor()

    # CORREÇÃO AQUI: Incluímos 'dia' e 'hora' no SELECT
    cursor.execute('''
        SELECT remetente, texto, dia, hora FROM mensagens 
        WHERE (remetente = ? AND destinatario = ?) 
           OR (remetente = ? AND destinatario = ?)
        ORDER BY id ASC
    ''', (user1, user2, user2, user1))

    linhas = cursor.fetchall()
    conn.close()

    # CORREÇÃO AQUI: Montamos o JSON incluindo os novos campos
    # row[0]=remetente, row[1]=texto, row[2]=dia, row[3]=hora
    historico = [{"remetente": r, "texto": t, "dia": d, "hora": h} for r, t, d, h in linhas]

    print(f"📦 JSON enviado para o Android: {historico}")

    emit('receber_historico', historico, to=request.sid)


@socketio.on('enviar_mensagem')
def handle_enviar_mensagem(data):
    # 1. Pega o dia e a hora atuais no servidor
    agora = datetime.now()
    dia_atual = agora.strftime('%d/%m/%Y') # Ex: "26/05/2026"
    hora_atual = agora.strftime('%H:%M')    # Ex: "20:15"

    # 2. Monta o pacote que será salvo no banco e enviado ao receptor
    pacote_para_envio = {
        'remetente': data['remetente'],
        'destinatario': data['destinatario'],
        'texto': data['texto'],
        'dia': dia_atual,    # <-- ESSENCIAL: Garante que o receptor vai receber o dia
        'hora': hora_atual   # <-- ESSENCIAL: Garante que o receptor vai receber a hora
    }

    # 3. Aqui vai o seu código existente para salvar no Banco de Dados
    # Ex: salvar_no_banco(pacote_para_envio)

    # 4. Transmite para todo mundo (ou para o quarto do destinatário)
    # Garanta que você está enviando o "pacote_para_envio" com os novos campos!
    emit('receber_mensagem', pacote_para_envio, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)