from flask import Flask, jsonify, send_from_directory
import os
import csv
from openpyxl import load_workbook
import unicodedata

app = Flask(__name__)
PLATOS = []

# ==============================
# BASE NUTRICIONAL POR DEFECTO (para evitar errores si el CSV falla)
# ==============================
BASE_NUTRICIONAL = {
    "agua": {"kcal": 0, "grasas": 0, "grasas_saturadas": 0, "hc": 0, "azucar": 0, "proteinas": 0, "sal": 0},
    "sal": {"kcal": 0, "grasas": 0, "grasas_saturadas": 0, "hc": 0, "azucar": 0, "proteinas": 0, "sal": 100},
    "aceite de oliva": {"kcal": 884, "grasas": 100, "grasas_saturadas": 14, "hc": 0, "azucar": 0, "proteinas": 0, "sal": 0},
    "patata": {"kcal": 87, "grasas": 0.1, "grasas_saturadas": 0, "hc": 20, "azucar": 0.8, "proteinas": 2, "sal": 0.01},
    "zanahoria": {"kcal": 41, "grasas": 0.2, "grasas_saturadas": 0, "hc": 10, "azucar": 4.7, "proteinas": 0.9, "sal": 0.07},
    "cebolla": {"kcal": 40, "grasas": 0.1, "grasas_saturadas": 0, "hc": 9.3, "azucar": 4.2, "proteinas": 1.1, "sal": 0.01},
    "ajo": {"kcal": 149, "grasas": 0.5, "grasas_saturadas": 0.1, "hc": 33.1, "azucar": 1, "proteinas": 6.4, "sal": 0.02},
    "pimiento": {"kcal": 31, "grasas": 0.3, "grasas_saturadas": 0.1, "hc": 6, "azucar": 4.2, "proteinas": 1, "sal": 0.01},
    "calabacin": {"kcal": 17, "grasas": 0.3, "grasas_saturadas": 0.1, "hc": 3.1, "azucar": 2.5, "proteinas": 1.2, "sal": 0.01},
    "lentejas": {"kcal": 116, "grasas": 0.4, "grasas_saturadas": 0.1, "hc": 20, "azucar": 1.8, "proteinas": 9, "sal": 0.01},
    "alubias": {"kcal": 120, "grasas": 0.5, "grasas_saturadas": 0.1, "hc": 20.8, "azucar": 1.4, "proteinas": 8.3, "sal": 0.01},
    "pescado": {"kcal": 100, "grasas": 2, "grasas_saturadas": 0.5, "hc": 0, "azucar": 0, "proteinas": 20, "sal": 0.1},
    "chorizo": {"kcal": 450, "grasas": 40, "grasas_saturadas": 15, "hc": 2, "azucar": 1, "proteinas": 20, "sal": 3},
    "harina de maiz": {"kcal": 360, "grasas": 3, "grasas_saturadas": 0.5, "hc": 78, "azucar": 1, "proteinas": 8, "sal": 0.01},
    "zumo de limon": {"kcal": 22, "grasas": 0.1, "grasas_saturadas": 0, "hc": 7, "azucar": 2, "proteinas": 0.4, "sal": 0.01}
}

def normalizar_texto(texto):
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

def cargar_base_nutricional():
    ruta = "ingredientes.csv"
    if os.path.exists(ruta):
        try:
            with open(ruta, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if "Alimento" not in reader.fieldnames:
                    print("❌ El CSV no tiene la columna 'Alimento'. Usando base por defecto.")
                    return
                for row in reader:
                    nombre = normalizar_texto(row["Alimento"])
                    if nombre:
                        BASE_NUTRICIONAL[nombre] = {
                            "kcal": float(row["Valor_energetico_kcal"]),
                            "grasas": float(row["Grasas_g"]),
                            "grasas_saturadas": float(row["Grasas_saturadas_g"]),
                            "hc": float(row["Hidratos_carbono_g"]),
                            "azucar": float(row["Azucar_g"]),
                            "proteinas": float(row["Proteinas_g"]),
                            "sal": float(row["Sal_g"])
                        }
            print(f"✅ Base nutricional cargada desde CSV: {len(BASE_NUTRICIONAL)} ingredientes")
        except Exception as e:
            print(f"⚠️ Error al cargar ingredientes.csv: {e}. Usando base por defecto.")
    else:
        print("⚠️ ingredientes.csv no encontrado. Usando base nutricional por defecto.")

def buscar_ingrediente(nombre_ing):
    nombre_norm = normalizar_texto(nombre_ing)
    if not nombre_norm:
        return None

    # Buscar en base nutricional
    if nombre_norm in BASE_NUTRICIONAL:
        return BASE_NUTRICIONAL[nombre_norm]

    # Coincidencias parciales
    for clave in BASE_NUTRICIONAL:
        if nombre_norm in clave or clave in nombre_norm:
            return BASE_NUTRICIONAL[clave]

    # Palabras clave
    if "agua" in nombre_norm:
        return BASE_NUTRICIONAL["agua"]
    if "sal" in nombre_norm:
        return BASE_NUTRICIONAL["sal"]
    if "aceite" in nombre_norm and "oliva" in nombre_norm:
        return BASE_NUTRICIONAL["aceite de oliva"]
    if "patata" in nombre_norm or "papa" in nombre_norm:
        return BASE_NUTRICIONAL["patata"]
    if "zanahoria" in nombre_norm:
        return BASE_NUTRICIONAL["zanahoria"]
    if "cebolla" in nombre_norm:
        return BASE_NUTRICIONAL["cebolla"]
    if "ajo" in nombre_norm:
        return BASE_NUTRICIONAL["ajo"]
    if "pimiento" in nombre_norm:
        return BASE_NUTRICIONAL["pimiento"]
    if "calabac" in nombre_norm:
        return BASE_NUTRICIONAL["calabacin"]
    if "lenteja" in nombre_norm:
        return BASE_NUTRICIONAL["lentejas"]
    if "alubia" in nombre_norm or "judia" in nombre_norm:
        return BASE_NUTRICIONAL["alubias"]
    if "pescado" in nombre_norm:
        return BASE_NUTRICIONAL["pescado"]
    if "chorizo" in nombre_norm:
        return BASE_NUTRICIONAL["chorizo"]
    if "harina" in nombre_norm and "maiz" in nombre_norm:
        return BASE_NUTRICIONAL["harina de maiz"]
    if "zumo" in nombre_norm and "limon" in nombre_norm:
        return BASE_NUTRICIONAL["zumo de limon"]

    print(f"⚠️ Ingrediente no encontrado: '{nombre_ing}'")
    return None

def calcular_nutricion_plato(ingredientes_gramaje):
    total = {"kcal": 0, "grasas": 0, "grasas_saturadas": 0, "hc": 0, "azucar": 0, "proteinas": 0, "sal": 0}
    for item in ingredientes_gramaje:
        nombre = item["nombre"]
        gramos = item["gramos"]
        if gramos <= 0:
            continue
        nut = buscar_ingrediente(nombre)
        if nut:
            factor = gramos / 100.0
            for k in total:
                total[k] += nut[k] * factor
    for k in total:
        total[k] = round(total[k], 1)
    return total

def leer_ficha_tecnica(ruta_excel):
    wb = load_workbook(ruta_excel, data_only=True)
    ws = wb.active

    nombre = str(ws["A7"].value).strip() if ws["A7"].value else ""
    ingredientes = str(ws["A10"].value).strip() if ws["A10"].value else ""

    alergenos = []
    alergenos_col1 = ["Gluten", "Crustáceos", "Huevos", "Pescado", "Cacahuetes", "Soja", "Leche", "Legumbres", "Guisantes"]
    for i, nombre_alerg in enumerate(alergenos_col1, start=12):
        if ws[f"F{i}"].value == "X":
            alergenos.append(nombre_alerg)

    alergenos_col2 = ["Frutos de cáscara", "Apio", "Mostaza", "Sésamo", "Sulfuroso", "Altramuces", "Moluscos", "Cerdo", "Otros"]
    for i, nombre_alerg in enumerate(alergenos_col2, start=12):
        if ws[f"K{i}"].value == "X":
            alergenos.append(nombre_alerg)

    proceso_elaboracion = str(ws["A24"].value).strip() if ws["A24"].value else ""
    etiquetado = str(ws["A29"].value).strip() if ws["A29"].value else ""
    conservacion = str(ws["A32"].value).strip() if ws["A32"].value else ""
    fecha_caducidad = str(ws["A40"].value).strip() if ws["A40"].value else ""
    datos_logisticos = str(ws["A42"].value).strip() if ws["A42"].value else ""

    ingredientes_gramaje = []
    for fila in range(35, 44):
        nombre_ing = ws[f"E{fila}"].value
        gramos = ws[f"H{fila}"].value
        if nombre_ing and gramos is not None:
            try:
                gramos = float(gramos)
                ingredientes_gramaje.append({"nombre": str(nombre_ing).strip(), "gramos": gramos})
            except (ValueError, TypeError):
                pass

    gramos_racion = float(ws["H44"].value) if isinstance(ws["H44"].value, (int, float)) else 0
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
        "nutricion": nutricion
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

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/api/platos")
def obtener_platos():
    return jsonify({"platos": PLATOS})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
