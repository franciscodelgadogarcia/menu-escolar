from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "¡Menú escolar online! ✅"

@app.route("/api/platos")
def platos():
    return {
        "platos": [
            {"nombre": "Lentejas", "tipo": "1º"},
            {"nombre": "Pescado", "tipo": "2º"}
        ]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
