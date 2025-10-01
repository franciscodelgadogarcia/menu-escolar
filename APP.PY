from flask import Flask
import os

# Crea la aplicación Flask
app = Flask(__name__)

# Ruta principal: muestra un mensaje de bienvenida
@app.route("/")
def home():
    return "¡Sistema de menús escolares activo! ✅"

# Ruta de ejemplo: devuelve una lista de platos (más adelante vendrá de tus fichas)
@app.route("/api/platos")
def obtener_platos():
    return {
        "platos": [
            {"id": 1, "nombre": "Lentejas estofadas", "tipo": "1º"},
            {"id": 2, "nombre": "Merluza al horno", "tipo": "2º"},
            {"id": 3, "nombre": "Manzana", "tipo": "postre"}
        ]
    }

# Inicia la aplicación
if __name__ == "__main__":
    # Render define el puerto en la variable de entorno PORT
    port = int(os.environ.get("PORT", 10000))
    # Escucha en todas las interfaces (0.0.0.0), no solo en localhost
    app.run(host="0.0.0.0", port=port)