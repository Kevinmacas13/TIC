import requests

# URL del servicio que procesa el código (esto es solo un ejemplo, necesitarás un servicio real)
url = "https://example.com/printcode"

# Código que deseas enviar
code = """
def hello_world():
    print("Hello, world!")

hello_world()
"""

# Datos JSON que envías en la solicitud
payload = {
    "code": code,
    "line_numbers": False
}

# Headers de la solicitud (opcional, dependiendo del servicio)
headers = {
    "Content-Type": "application/json"
}

# Realizar la solicitud POST
response = requests.post(url, json=payload, headers=headers)

# Verificar la respuesta
if response.status_code == 200:
    print("Solicitud exitosa")
    print("Respuesta del servidor:")
    print(response.json())
else:
    print("Error en la solicitud")
    print("Código de estado:", response.status_code)
    print("Mensaje:", response.text)
