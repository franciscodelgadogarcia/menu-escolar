from flask import Flask, jsonify, send_from_directory
import os
import csv
from openpyxl import load_workbook
import unicodedata

app = Flask(__name__)
PLATOS = []

# ==============================
# BASE NUTRICIONAL POR DEFECTO
# ==============================
BASE_NUTRICIONAL = {
    "agua": {"kcal": 0, "lip": 0, "ags": 0, "prot": 0, "hdec": 0, "azucares": 0, "vit_a": 0, "vit_c": 0, "vit_d": 0, "ca": 0, "fe": 0, "sal": 0},
    "sal": {"kcal": 0, "lip": 0, "ags": 0, "prot": 0, "hdec": 0, "azucares": 0, "vit_a": 0, "vit_c": 0, "vit_d": 0, "ca": 0, "fe": 0, "sal": 100},
    "aceite de oliva": {"kcal": 884, "lip": 100, "ags": 14, "prot": 0, "hdec": 0, "azucares": 0, "vit_a": 0, "vit_c": 0, "vit_d": 0, "ca": 0, "fe": 0, "sal": 0},
    "patata": {"kcal": 87, "lip": 0.1, "ags": 0, "prot": 2, "hdec": 20, "azucares": 0.8, "vit_a": 0, "vit_c": 12, "vit_d": 0, "ca": 6, "fe": 0.4, "sal": 0.01},
    "zanahoria": {"kcal": 41, "lip": 0.2, "ags": 0, "prot": 0.9, "hdec": 10, "azucares": 4.7, "vit_a": 835, "vit_c": 6, "vit_d": 0, "ca": 33, "fe": 0.3, "sal": 0.07},
    "cebolla": {"kcal": 40, "lip": 0.1, "ags": 0, "prot": 1.1, "hdec": 9.3, "azucares": 4.2, "vit_a": 0, "vit_c": 7, "vit_d": 0, "ca": 23, "fe": 0.2, "sal": 0.01},
    "tomate": {"kcal": 18, "lip": 0.2, "ags": 0, "prot": 0.9, "hdec": 3.9, "azucares": 2.6, "vit_a": 42, "vit_c": 23, "vit_d": 0, "ca": 10, "fe": 0.3, "sal": 0.01},
    "lechuga": {"kcal": 15, "lip": 0.2, "ags": 0, "prot": 1.3, "hdec": 3.0, "azucares": 1.5, "vit_a": 150, "vit_c": 10, "vit_d": 0, "ca": 30, "fe": 1.0, "sal": 0.01},
    "maiz": {"kcal": 96, "lip": 1.2, "ags": 0.2, "prot": 3.2, "hdec": 21.0, "azucares": 6.3, "vit_a": 10, "vit_c": 7, "vit_d": 0, "ca": 2, "fe": 0.5, "sal": 0.01},
    "remolacha": {"kcal": 44, "lip": 0.2, "ags": 0, "prot": 1.7, "hdec": 10.0, "azucares": 8.0, "vit_a": 2, "vit_c": 4, "vit_d": 0, "ca": 16, "fe": 0.8, "sal": 0.05},
    "aceitunas": {"kcal": 115, "lip": 10.7, "ags": 1.4, "prot": 0.8, "hdec": 6.3, "azucares": 0, "vit_a": 0, "vit_c": 0, "vit_d": 0, "ca": 88, "fe": 6.3, "sal": 2.5},
    "calabacin": {"kcal": 17, "lip": 0.3, "ags": 0.1, "prot": 1.2, "hdec": 3.1, "azucares": 2.5, "vit_a": 10, "vit_c": 17, "vit_d": 0, "ca": 16, "fe": 0.4, "sal": 0.01},
    "pimiento": {"kcal": 31, "lip": 0.3, "ags": 0.1, "prot": 1, "hdec": 6, "azucares": 4.2, "vit_a": 157, "vit_c": 128, "vit_d": 0, "ca": 10, "fe": 0.3, "sal": 0.01},
    "guisantes": {"kcal": 81, "lip": 0.4, "ags": 0.1, "prot": 5.4, "hdec": 14.5, "azucares": 3.3, "vit_a": 20, "vit_c": 12, "vit_d": 0, "ca": 25, "fe": 1.5, "sal": 0.01},
    "leche": {"kcal": 64, "lip": 3.6, "ags": 2.3, "prot": 3.3, "hdec": 4.8, "azucares": 4.8, "vit_a": 28, "vit_c": 1, "vit_d": 0.1, "ca": 120, "fe": 0.1, "sal": 0.1},
    "mantequilla": {"kcal": 717, "lip": 81, "ags": 51, "prot": 0.9, "hdec": 0.6, "azucares": 0.6, "vit_a": 200, "vit_c": 0, "vit_d": 1.5, "ca": 24, "fe": 0.1, "sal": 0.1},
    "lentejas": {"kcal": 116, "lip": 0.4, "ags": 0.1, "prot": 9, "hdec": 20, "azucares": 1.8, "vit_a": 2, "vit_c": 2, "vit_d": 0, "ca": 35, "fe": 3.3, "sal": 0.01},
    "alubias": {"kcal": 120, "lip": 0.5, "ags": 0.1, "prot": 8.3, "hdec": 20.8, "azucares": 1.4, "vit_a": 2, "vit_c": 1, "vit_d": 0, "ca": 50, "fe": 2.5, "sal": 0.01},
    "pescado": {"kcal": 100, "lip": 2, "ags": 0.5, "prot": 20, "hdec": 0, "azucares": 0, "vit_a": 10, "vit_c": 0, "vit_d": 0.1, "ca": 15, "fe": 0.4, "sal": 0.1},
    "huevos": {"kcal": 155, "lip": 11, "ags": 3.3, "prot": 13, "hdec": 1.1, "azucares": 1.1, "vit_a": 149, "vit_c": 0, "vit_d": 2.2, "ca": 56, "fe": 1.8, "sal": 0.12}
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
                required_cols = ["Alimento", "E (Kcal)", "Líp (g)", "AGS (g)", "Prot (g)", "HdeC (g)", "Azucares", "Vit A (µg)", "Vit C (mg)", "vit D (µg)", "Ca (mg)", "Fe (mg)", "Sal"]
                if not all(col in reader.fieldnames for col in required_cols):
                    print("❌ CSV no tiene columnas requeridas. Usando base por defecto.")
                    return
                for row in reader:
                    nombre = normalizar_texto(row["Alimento"])
                    if nombre:
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
            print(f"⚠️ Error al cargar ingredientes.csv: {e}")
    else:
        print("⚠️ ingredientes.csv no encontrado. Usando base por defecto.")

def buscar_ingrediente(nombre_ing):
    nombre_norm = normalizar_texto(nombre_ing)
    if not nombre_norm:
        return None
    if nombre_norm in BASE_NUTRICIONAL:
        return BASE_NUTRICIONAL[nombre_norm]
    for clave in BASE_NUTRICIONAL:
        if nombre_norm in clave or clave in nombre_norm:
            return BASE_NUTRICIONAL[clave]
    # Palabras clave
    if "agua" in nombre_norm: return BASE_NUTRICIONAL["agua"]
    if "sal" in nombre_norm: return BASE_NUTRICIONAL["sal"]
    if "aceite" in nombre_norm and "oliva" in nombre_norm: return BASE_NUTRICIONAL["aceite de oliva"]
    if "patata" in nombre_norm or "papa" in nombre_norm: return BASE_NUTRICIONAL["patata"]
    if "zanahoria" in nombre_norm: return BASE_NUTRICIONAL["zanahoria"]
    if "cebolla" in nombre_norm: return BASE_NUTRICIONAL["cebolla"]
    if "tomate" in nombre_norm: return BASE_NUTRICIONAL["tomate"]
    if "lechuga" in nombre_norm: return BASE_NUTRICIONAL["lechuga"]
    if "maiz" in nombre_norm: return BASE_NUTRICIONAL["maiz"]
    if "remolacha" in nombre_norm: return BASE_NUTRICIONAL["remolacha"]
    if "aceituna" in nombre_norm: return BASE_NUTRICIONAL["aceitunas"]
    if "calabacin" in nombre_norm: return BASE_NUTRICIONAL["calabacin"]
    if "pimiento" in nombre_norm: return BASE_NUTRICIONAL["pimiento"]
    if "guisante" in nombre_norm: return BASE_NUTRICIONAL["guisantes"]
    if "leche" in nombre_norm: return BASE_NUTRICIONAL["leche"]
    if "mantequilla" in nombre_norm: return BASE_NUTRICIONAL["mantequilla"]
    if "lenteja" in nombre_norm: return BASE_NUTRICIONAL["lentejas"]
    if "alubia" in nombre_norm or "judia" in nombre_norm: return BASE_NUTRICIONAL["alubias"]
    if "pescado" in nombre_norm: return BASE_NUTRICIONAL["pescado"]
    if "huevo" in nombre_norm: return BASE_NUTRICIONAL["huevos"]
    print(f"⚠️ Ingrediente no encontrado: '{nombre_ing}'")
    return None

def calcular_nutricion_plato(ingredientes_gramaje):
    total = {"kcal": 0, "lip": 0, "ags": 0, "prot": 0, "hdec": 0, "azucares": 0, "vit_a": 0, "vit_c": 0, "vit_d": 0, "ca": 0, "fe": 0, "sal": 0}
    for item in ingredientes_gramaje:
        nombre = item["nombre"]
        gramos = item["gramos"]
        if gramos <= 0: continue
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

    nombre_norm = normalizar_texto(nombre)
    nuevo_ingredientes = None

    # ✅ DETECCIÓN DE ACOMPAÑAMIENTOS COMPUESTOS
    if "lechuga con tomate" in nombre_norm:
        nuevo_ingredientes = [("Lechuga", 60), ("Tomate", 60)]
    elif "lechuga con zanahoria" in nombre_norm:
        nuevo_ingredientes = [("Lechuga", 60), ("Zanahoria", 60)]
    elif "lechuga con remolacha" in nombre_norm:
        nuevo_ingredientes = [("Lechuga", 60), ("Remolacha", 60)]
    elif "lechuga con aceituna" in nombre_norm:
        nuevo_ingredientes = [("Lechuga", 70), ("Aceitunas", 10)]
    elif "lechuga con maiz" in nombre_norm:
        nuevo_ingredientes = [("Lechuga", 60), ("Maíz", 30)]
    elif "tomate con maiz" in nombre_norm:
        nuevo_ingredientes = [("Tomate", 70), ("Maíz", 30)]
    elif "tomate con zanahoria" in nombre_norm:
        nuevo_ingredientes = [("Tomate", 60), ("Zanahoria", 60)]
    elif "pure de patata" in nombre_norm:
        nuevo_ingredientes = [("Patata", 120), ("Leche", 20), ("Mantequilla", 5)]
    elif "patatas fritas" in nombre_norm:
        nuevo_ingredientes = [("Patata", 100)]
    elif "patata cocida" in nombre_norm:
        nuevo_ingredientes = [("Patata", 120)]
    elif "patata al horno" in nombre_norm:
        nuevo_ingredientes = [("Patata", 120), ("Aceite de oliva", 5)]
    elif "menestra de verdura" in nombre_norm:
        nuevo_ingredientes = [("Guisantes", 40), ("Zanahoria", 30), ("Maíz", 30)]
    elif "verduras asadas" in nombre_norm:
        nuevo_ingredientes = [("Calabacín", 40), ("Pimiento", 40), ("Cebolla", 40), ("Aceite de oliva", 5)]

    # ✅ DETECCIÓN DE POSTRES
    es_postre = any(term in nombre_norm for term in [
        "fruta", "yogur", "flan", "natilla", "gelatina", "queso fresco",
        "manzana", "pera", "plátano", "naranja", "uva", "melón", "sandía",
        "fresa", "kiwi", "ciruela", "higo", "piña", "mandarina"
    ])

    if nuevo_ingredientes:
        ingredientes_gramaje = [{"nombre": n, "gramos": g} for n, g in nuevo_ingredientes]
        gramos_racion = sum(g for _, g in nuevo_ingredientes)
    elif es_postre:
        nuevos_ingredientes = []
        for item in ingredientes_gramaje:
            nombre_norm_ing = normalizar_texto(item["nombre"])
            gramos = item["gramos"]
            if any(fruta in nombre_norm_ing for fruta in ["manzana", "pera", "plátano", "naranja", "mandarina", "kiwi", "ciruela", "higo"]):
                gramos = 150.0
            elif any(fruta in nombre_norm_ing for fruta in ["melón", "sandía", "piña", "fresa", "uva", "frutas"]):
                gramos = 120.0
            elif "yogur" in nombre_norm_ing:
                gramos = 125.0
            elif "queso fresco" in nombre_norm_ing:
                gramos = 60.0
            elif any(postre in nombre_norm_ing for postre in ["flan", "natilla", "gelatina"]):
                gramos = 120.0
            nuevos_ingredientes.append({"nombre": item["nombre"], "gramos": gramos})
        ingredientes_gramaje = nuevos_ingredientes
        gramos_racion = sum(item["gramos"] for item in ingredientes_gramaje)
    else:
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
