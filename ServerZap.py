from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# O cors_allowed_origins="*" permite que o seu app Android Linux/Emulador se conecte sem travar
socketio = SocketIO(app, cors_allowed_origins="*")

# Dicionário para mapear: { "nome_do_usuario": "id_do_socket" }
usuarios_conectados = {}


@socketio.on('connect')
def handle_connect():
    print(f"Dispositivo conectado ao servidor. ID temporário: {request.sid}")


# 1. O Android PRECISA disparar esse evento logo após se conectar!
@socketio.on('registrar_usuario')
def handle_registrar(data):
    nome_usuario = data.get('usuario')
    if nome_usuario:
        # Salva o ID atual do socket para este usuário
        usuarios_conectados[nome_usuario] = request.sid
        print(f"✨ Usuário [{nome_usuario}] registrado com o ID: {request.sid}")
        print(f"Usuários ativos no momento: {list(usuarios_conectados.keys())}")


# 2. O evento que você já configurou no botão enviar do seu Android
@socketio.on('enviar_mensagem')
def handle_enviar_mensagem(data):
    remetente = data.get('remetente')
    destinatario = data.get('destinatario')
    texto = data.get('texto')

    print(f"📩 {remetente} enviou para {destinatario}: {texto}")

    # Procura se a pessoa que vai receber está online com o app aberto
    if destinatario in usuarios_conectados:
        sid_destinatario = usuarios_conectados[destinatario]

        # Envia o pacote EXATAMENTE para o socket daquela pessoa
        emit('receber_mensagem', {
            'remetente': remetente,
            'texto': texto
        }, to=sid_destinatario)
        print(f"🚀 Mensagem entregue para {destinatario} com sucesso.")
    else:
        print(f"⚠️ {destinatario} está offline. (Aqui salvaríamos no banco de dados para entregar depois)")


@socketio.on('disconnect')
def handle_disconnect():
    # Remove o usuário da lista quando ele fecha o app para não tentar enviar para um ID morto
    usuario_para_remover = None
    for usuario, sid in usuarios_conectados.items():
        if sid == request.sid:
            usuario_para_remover = usuario
            break

    if usuario_para_remover:
        del usuarios_conectados[usuario_para_remover]
        print(f"❌ Usuário [{usuario_para_remover}] desconectou.")


if __name__ == '__main__':
    # Roda o servidor na sua rede local (porta 5000)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)