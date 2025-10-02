from flask import Flask, jsonify
import os
from openpyxl import load_workbook

app = Flask(__name__)
PLATOS = []

def leer_ficha_tecnica(ruta_excel):
    wb = load_workbook(ruta_excel, data_only=True)
    ws = wb.active

    # 1. Nombre del plato (A7)
    nombre = str(ws["A7"].value).strip() if ws["A7"].value else ""

    # 2. Composición / ingredientes descriptivos (A10)
    ingredientes = str(ws["A10"].value).strip() if ws["A10"].value else ""

    # 3. Alérgenos – columna 1 (E12:E20 = nombres, F12:F20 = "X")
    alergenos_col1 = [
        "Gluten", "Crustáceos", "Huevos", "Pescado", "Cacahuetes",
        "Soja", "Leche", "Legumbres", "Guisantes"
    ]
    alergenos = []
    for i, nombre_alerg in enumerate(alergenos_col1, start=12):
        if ws[f"F{i}"].value == "X":
            alergenos.append(nombre_alerg)

    # 4. Alérgenos – columna 2 (H12:H20 = nombres, K12:K20 = "X")
    alergenos_col2 = [
        "Frutos de cáscara", "Apio", "Mostaza", "Sésamo", "Sulfuroso",
        "Altramuces", "Moluscos", "Cerdo", "Otros"
    ]
    for i, nombre_alerg in enumerate(alergenos_col2, start=12):
        if ws[f"K{i}"].value == "X":
            alergenos.append(nombre_alerg)

    # 5. Proceso de elaboración (A24)
    proceso_elaboracion = str(ws["A24"].value).strip() if ws["A24"].value else ""

    # 6. Etiquetado (A29)
    etiquetado = str(ws["A29"].value).strip() if ws["A29"].value else ""

    # 7. Conservación y distribución (A32)
    conservacion = str(ws["A32"].value).strip() if ws["A32"].value else ""

    # 8. Fecha de caducidad (A40)
    fecha_caducidad = str(ws["A40"].value).strip() if ws["A40"].value else ""

    # 9. Datos logísticos (A42)
    datos_logisticos = str(ws["A42"].value).strip() if ws["A42"].value else ""

    # 10. Ingredientes con gramaje (E35:E43 = nombre, H35:H43 = gramos)
    ingredientes_gramaje = []
    for fila in range(35, 44):  # filas 35 a 43
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
                pass  # ignorar si no es número

    # 11. Gramaje total (H44)
    gramos_racion = ws["H44"].value
    gramos_racion = float(gramos_racion) if isinstance(gramos_racion, (int, float)) else 0

    # 12. Información nutricional
    nutricion = {
        "kcal_totales": float(ws["H45"].value) if ws["H45"].value else 0,
        "kcal_100g": float(ws["H46"].value) if ws["H46"].value else 0,
        "proteinas_totales": float(ws["I44"].value) if ws["I44"].value else 0,
        "proteinas_100g": float(ws["I46"].value) if ws["I46"].value else 0,
        "lipidos_totales": float(ws["J44"].value) if ws["J44"].value else 0,
        "lipidos_100g": float(ws["J46"].value) if ws["J46"].value else 0,
        "hc_totales": float(ws["K44"].value) if ws["K44"].value else 0,
        "hc_100g": float(ws["K46"].value) if ws["K46"].value else 0,
        "fibra_totales": float(ws["L44"].value) if ws["L44"].value else 0,
        "fibra_100g": float(ws["L46"].value) if ws["L46"].value else 0,
    }

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

# Cargar al iniciar
cargar_platos()

@app.route("/")
def home():
    return f"¡Menú escolar online! ✅<br>Platos cargados: {len(PLATOS)}"

@app.route("/api/platos")
def obtener_platos():
    return jsonify({"platos": PLATOS})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
