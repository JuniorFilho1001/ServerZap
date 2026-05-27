from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# O cors_allowed_origins="*" permite que o app Android se conecte sem bloqueios
socketio = SocketIO(app, cors_allowed_origins="*")

# Dicionário para mapear: { "nome_do_usuario": "id_do_socket" }
usuarios_conectados = {}


@socketio.on('connect')
def handle_connect():
    print(f"Nova conexão estabelecida provisoriamente! ID: {request.sid}")


@socketio.on('register')
def handle_register(data):
    """
    Registra o usuário associando o nome dele ao ID da conexão atual.
    Espera um JSON: {'username': 'professor'}
    """
    username = data.get('username')
    if username:
        usuarios_conectados[username] = request.sid
        print(f"\n✅ Usuário [{username}] registrado com sucesso no ID: {request.sid}")
        print(f"Usuários online: {list(usuarios_conectados.keys())}\n")

        # Confirma para o cliente que o registro deu certo
        emit('register_response', {'status': 'success', 'message': f'Registrado como {username}'})


@socketio.on('send_message')
def handle_message(data):
    """
    Recebe a mensagem de um cliente e repassa para o destinatário correto.
    Espera um JSON: {'sender': 'joao', 'receiver': 'maria', 'message': 'Olá!'}
    """
    sender = data.get('sender')
    receiver = data.get('receiver')
    message = data.get('message')

    print(f"Tentativa de envio: de [{sender}] para [{receiver}]: {message}")

    # Verifica se o destinatário está online
    if receiver in usuarios_conectados:
        receiver_sid = usuarios_conectados[receiver]

        payload = {
            'sender': sender,
            'message': message
        }

        # Envia especificamente para o túnel (room) do destinatário
        emit('receive_message', payload, room=receiver_sid)
        print(f"⚡ Mensagem entregue para [{receiver}] com sucesso.")
    else:
        print(f"❌ Falha: [{receiver}] está offline. Mensagem descartada.")
        # Avisa o remetente que o alvo está offline
        emit('receive_message', {'sender': 'Sistema', 'message': f'O usuário {receiver} está offline.'},
             room=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    """
    Remove o usuário do dicionário quando ele fecha o aplicativo ou perde conexão.
    """
    usuario_removido = None
    for username, sid in list(usuarios_conectados.items()):
        if sid == request.sid:
            usuario_removido = username
            del usuarios_conectados[username]
            break

    if usuario_removido:
        print(f"❌ Usuário [{usuario_removido}] desconectou.")
        print(f"Usuários restantes online: {list(usuarios_conectados.keys())}")


if __name__ == '__main__':
    # Roda o servidor na porta 5000 acessível por qualquer dispositivo na mesma rede (0.0.0.0)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)