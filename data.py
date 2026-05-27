from datetime import datetime

agora = datetime.now()
dia = agora.strftime("%d-%m-%Y")
hora = agora.strftime("%H:%M:%S")

print(f"{dia} - {hora}")