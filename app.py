from flask import Flask, jsonify, send_from_directory
import os
import csv
from openpyxl import load_workbook

app = Flask(__name__)
PLATOS = []
BASE_NUTRICIONAL = {}

# ==============================
# CARGAR BASE NUTRICIONAL (UTF-8)
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
    except UnicodeDecodeError as e:
        print(f"❌ Error de codificación en ingredientes.csv: {e}")
        print("💡 Guarda el archivo como 'CSV UTF-8' desde Excel o LibreOffice.")
    except Exception as e:
        print(f"❌ Error al cargar ingredientes.csv: {e}")

# ==============================
# CALCULAR NUTRICIÓN DE UN PLATO
# ==============================
import unicodedata

def normalizar_texto(texto):
    """Convierte a minúsculas, elimina tildes y limpia espacios."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    # Eliminar tildes y caracteres especiales
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

def buscar_ingrediente(nombre_ingrediente, base_nutricional):
    """Busca un ingrediente en la base nutricional con coincidencia flexible."""
    nombre_norm = normalizar_texto(nombre_ingrediente)
    
    # Primero: coincidencia exacta (sin tildes)
    for nombre_base in base_nutricional:
        if normalizar_texto(nombre_base) == nombre_norm:
            return base_nutricional[nombre_base]
    
    # Segundo: coincidencia parcial (el nombre del CSV contiene el nombre del ingrediente)
    for nombre_base in base_nutricional:
        if nombre_norm in normalizar_texto(nombre_base):
            return base_nutricional[nombre_base]
    
    # Tercero: palabras clave comunes
    if "aceite" in nombre_norm and "oliva" in nombre_norm:
        for nombre_base in base_nutricional:
            if "aceite" in normalizar_texto(nombre_base) and "oliva" in normalizar_texto(nombre_base):
                return base_nutricional[nombre_base]
    if "patata" in nombre_norm or "papa" in nombre_norm:
        for nombre_base in base_nutricional:
            if "patata" in normalizar_texto(nombre_base):
                return base_nutricional[nombre_base]
    if "agua" in nombre_norm:
        return base_nutricional.get("Agua", None)
    if "sal" in nombre_norm:
        return base_nutricional.get("Sal", None)
    
    return None
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
        if gramos <= 0:
            continue
            
        nut = buscar_ingrediente(nombre, BASE_NUTRICIONAL)
        if nut:
            factor = gramos / 100.0
            total["kcal"] += nut["kcal"] * factor
            total["grasas"] += nut["grasas"] * factor
            total["grasas_saturadas"] += nut["grasas_saturadas"] * factor
            total["hc"] += nut["hc"] * factor
            total["azucar"] += nut["azucar"] * factor
            total["proteinas"] += nut["proteinas"] * factor
            total["sal"] += nut["sal"] * factor
        else:
            print(f"⚠️ Ingrediente no encontrado: '{nombre}'")
    
    for k in total:
        total[k] = round(total[k], 1)
    return total

# ==============================
# LEER FICHA TÉCNICA (CORREGIDO)
# ==============================
def leer_ficha_tecnica(ruta_excel):
    wb = load_workbook(ruta_excel, data_only=True)
    ws = wb.active

    # 1. Nombre del plato (A7)
    nombre = str(ws["A7"].value).strip() if ws["A7"].value else ""

    # 2. Composición / ingredientes (A10)
    ingredientes = str(ws["A10"].value).strip() if ws["A10"].value else ""

    # 3. Alérgenos – columna 1 (F12:F20)
    alergenos_col1 = [
        "Gluten", "Crustáceos", "Huevos", "Pescado", "Cacahuetes",
        "Soja", "Leche", "Legumbres", "Guisantes"
    ]
    alergenos = []
    for i, nombre_alerg in enumerate(alergenos_col1, start=12):
        if ws[f"F{i}"].value == "X":
            alergenos.append(nombre_alerg)

    # 4. Alérgenos – columna 2 (K12:K20)
    alergenos_col2 = [
        "Frutos de cáscara", "Apio", "Mostaza", "Sésamo", "Sulfuroso",
        "Altramuces", "Moluscos", "Cerdo", "Otros"
    ]
    for i, nombre_alerg in enumerate(alergenos_col2, start=12):
        if ws[f"K{i}"].value == "X":
            alergenos.append(nombre_alerg)

    # 5. Otros campos
    proceso_elaboracion = str(ws["A24"].value).strip() if ws["A24"].value else ""
    etiquetado = str(ws["A29"].value).strip() if ws["A29"].value else ""
    conservacion = str(ws["A32"].value).strip() if ws["A32"].value else ""
    fecha_caducidad = str(ws["A40"].value).strip() if ws["A40"].value else ""
    datos_logisticos = str(ws["A42"].value).strip() if ws["A42"].value else ""

    # 6. Ingredientes con gramaje (E35:E43 = nombre, H35:H43 = gramos)
    ingredientes_gramaje = []  # ✅ DEFINIDO ANTES DEL BUCLE
    for fila in range(35, 44):
        nombre_ing = ws[f"E{fila}"].value
        gramos = ws[f"H{fila}"].value
        if nombre_ing and gramos is not None:
            try:
                gramos = float(gramos)
                ingredientes_gramaje.append({
                    "nombre": str(nombre_ing).strip(),
                    "gramos": gramos
                })
            except (ValueError, TypeError):
                pass

    # 7. Gramaje total (H44)
    gramos_racion = ws["H44"].value
    gramos_racion = float(gramos_racion) if isinstance(gramos_racion, (int, float)) else 0

    # 8. Calcular nutrición
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

# ==============================
# CARGAR TODOS LOS PLATOS
# ==============================
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
