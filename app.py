from flask import Flask, jsonify, send_from_directory
import os
import csv

app = Flask(__name__)
PLATOS = []
BASE_NUTRICIONAL = {}  # { "Patata cocida": { "kcal": 87, "grasas": 0.1, ... }, ... }

# ==============================
# CARGAR BASE NUTRICIONAL
# ==============================
def cargar_base_nutricional():
    global BASE_NUTRICIONAL
    ruta = "ingredientes.csv"
    if not os.path.exists(ruta):
        print("❌ No se encontró ingredientes.csv")
        return

    try:
        with open(ruta, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nombre = row["Alimento"].strip()
                BASE_NUTRICIONAL[nombre] = {
                    "kcal": float(row["Valor_energetico_kcal"]),
                    "grasas": float(row["Grasas_g"]),
                    "grasas_saturadas": float(row["Grasas_saturadas_g"]),
                    "hc": float(row["Hidratos_carbono_g"]),
                    "azucar": float(row["Azucar_g"]),
                    "proteinas": float(row["Proteinas_g"]),
                    "sal": float(row["Sal_g"])
                }
        print(f"✅ Base nutricional cargada: {len(BASE_NUTRICIONAL)} ingredientes")
    except Exception as e:
        print(f"❌ Error al cargar ingredientes.csv: {e}")

# ==============================
# CALCULAR NUTRICIÓN DE UN PLATO
# ==============================
def calcular_nutricion_plato(ingredientes_gramaje):
    total = {
        "kcal": 0,
        "grasas": 0,
        "grasas_saturadas": 0,
        "hc": 0,
        "azucar": 0,
        "proteinas": 0,
        "sal": 0
    }

    for item in ingredientes_gramaje:
        nombre = item["nombre"].strip()
        gramos = item["gramos"]
        if nombre in BASE_NUTRICIONAL:
            nut = BASE_NUTRICIONAL[nombre]
            factor = gramos / 100.0
            total["kcal"] += nut["kcal"] * factor
            total["grasas"] += nut["grasas"] * factor
            total["grasas_saturadas"] += nut["grasas_saturadas"] * factor
            total["hc"] += nut["hc"] * factor
            total["azucar"] += nut["azucar"] * factor
            total["proteinas"] += nut["proteinas"] * factor
            total["sal"] += nut["sal"] * factor
        else:
            print(f"⚠️ Ingrediente no encontrado en base: '{nombre}'")
    
    # Redondear a 1 decimal
    for k in total:
        total[k] = round(total[k], 1)
    return total

# ==============================
# CARGAR FICHAS TÉCNICAS
# ==============================
def leer_ficha_tecnica(ruta_excel):
    from openpyxl import load_workbook
    wb = load_workbook(ruta_excel, data_only=True)
    ws = wb.active

    # ... (tu código actual de extracción) ...
    # [Mantén exactamente el mismo código que ya tienes para extraer nombre, ingredientes_gramaje, etc.]

    # Al final, añade el cálculo nutricional
    nutricion = calcular_nutricion_plato(ingredientes_gramaje)
    
    return {
        "nombre": nombre,
        "ingredientes": ingredientes,
        "alergenos": alergenos,
        "proceso_elaboracion": proceso_elaboracion,
        "etiquetado": etiquetado,
        "conservacion": conservacion,
        "fecha_caducidad": fecha_caducidad,
        "datos_logisticos": datos_logisticos,
        "ingredientes_gramaje": ingredientes_gramaje,
        "gramos_racion": gramos_racion,
        "nutricion": nutricion  # ✅ ¡AHORA ES CALCULADO!
    }

def cargar_platos():
    global PLATOS
    PLATOS = []
    for filename in os.listdir("."):
        if filename.endswith(".xlsx"):
            try:
                plato = leer_ficha_tecnica(filename)
                plato["archivo"] = filename
                PLATOS.append(plato)
                print(f"✅ Cargado: {filename}")
            except Exception as e:
                print(f"❌ Error al cargar {filename}: {e}")

# ==============================
# INICIAR APP
# ==============================
cargar_base_nutricional()
cargar_platos()

# ==============================
# RUTAS
# ==============================
@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/api/platos")
def obtener_platos():
    return jsonify({"platos": PLATOS})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
