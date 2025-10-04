from flask import Flask, jsonify, send_from_directory
import os
import csv
from openpyxl import load_workbook
import unicodedata

app = Flask(__name__)
PLATOS = []
BASE_NUTRICIONAL = {}

def normalizar_texto(texto):
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

def cargar_base_nutricional():
    global BASE_NUTRICIONAL
    ruta = "ingredientes.csv"
    if not os.path.exists(ruta):
        print("❌ ingredientes.csv no encontrado")
        return

    try:
        with open(ruta, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            required_cols = ["Alimento", "E (Kcal)", "Líp (g)", "AGS (g)", "Prot (g)", "HdeC (g)", "Azucares", "Vit A (µg)", "Vit C (mg)", "vit D (µg)", "Ca (mg)", "Fe (mg)", "Sal"]
            if not all(col in reader.fieldnames for col in required_cols):
                print(f"❌ Faltan columnas en CSV. Esperadas: {required_cols}")
                return

            for row in reader:
                nombre = normalizar_texto(row["Alimento"])
                if not nombre:
                    continue
                BASE_NUTRICIONAL[nombre] = {
                    "kcal": float(row["E (Kcal)"]),
                    "lip": float(row["Líp (g)"]),
                    "ags": float(row["AGS (g)"]),
                    "prot": float(row["Prot (g)"]),
                    "hdec": float(row["HdeC (g)"]),
                    "azucares": float(row["Azucares"]),
                    "vit_a": float(row["Vit A (µg)"]),
                    "vit_c": float(row["Vit C (mg)"]),
                    "vit_d": float(row["vit D (µg)"]),
                    "ca": float(row["Ca (mg)"]),
                    "fe": float(row["Fe (mg)"]),
                    "sal": float(row["Sal"])
                }
        print(f"✅ Base nutricional cargada: {len(BASE_NUTRICIONAL)} ingredientes")
    except Exception as e:
        print(f"❌ Error al cargar ingredientes.csv: {e}")

def buscar_ingrediente(nombre_ing):
    nombre_norm = normalizar_texto(nombre_ing)
    if not nombre_norm:
        return None
    return BASE_NUTRICIONAL.get(nombre_norm)

def calcular_nutricion_plato(ingredientes_gramaje):
    total = {
        "kcal": 0, "lip": 0, "ags": 0, "prot": 0, "hdec": 0,
        "azucares": 0, "vit_a": 0, "vit_c": 0, "vit_d": 0,
        "ca": 0, "fe": 0, "sal": 0
    }
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
        else:
            print(f"⚠️ Ingrediente no encontrado: '{nombre}'")
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
