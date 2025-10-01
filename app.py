from flask import Flask, jsonify
import os
from openpyxl import load_workbook

app = Flask(__name__)

# Lista de platos (se llenará al iniciar)
PLATOS = []

def leer_ficha_tecnica(ruta_excel):
    wb = load_workbook(ruta_excel)
    ws = wb.active

    # Nombre del plato (celda A7)
    nombre = ws["A7"].value or ""

    # Ingredientes (celda A10)
    ingredientes = ws["A10"].value or ""

    # Conservación y distribución (rango A32:C37 → juntamos todo en un string)
    conservacion = ""
    for row in ws.iter_rows(min_row=32, max_row=37, min_col=1, max_col=3):
        for cell in row:
            if cell.value:
                conservacion += str(cell.value) + " "
    conservacion = conservacion.strip()

    # Fecha de caducidad (celda A40:C40)
    fecha_caducidad = ""
    for col in range(1, 4):  # A, B, C
        cell = ws.cell(row=40, column=col)
        if cell.value:
            fecha_caducidad += str(cell.value) + " "
    fecha_caducidad = fecha_caducidad.strip()

    # Datos logísticos (celda A42:C42)
    datos_logisticos = ""
    for col in range(1, 4):
        cell = ws.cell(row=42, column=col)
        if cell.value:
            datos_logisticos += str(cell.value) + " "
    datos_logisticos = datos_logisticos.strip()

    # Gramos totales (celda H44)
    gramos_racion = ws["H44"].value or 0

    # Alérgenos: buscar "X" en el rango E11:L20
    alergenos_posibles = [
        ("Gluten", "E11"),
        ("Crustáceos", "E12"),
        ("Huevos", "E13"),
        ("Pescado", "E14"),
        ("Cacahuetes", "E15"),
        ("Soja", "E16"),
        ("Leche", "E17"),
        ("Frutos de cáscara", "G11"),
        ("Apio", "G12"),
        ("Mostaza", "G13"),
        ("Sésamo", "G14"),
        ("Sulfuroso", "G15"),
        ("Altramuces", "G16"),
        ("Moluscos", "G17"),
        ("Legumbres", "E18"),
        ("Cerdo", "G18"),
        ("Guisantes", "E19"),
        ("Otros", "G19")
    ]
    alergenos = []
    for nombre_alerg, celda in alergenos_posibles:
        if ws[celda].value == "X":
            alergenos.append(nombre_alerg)

    # Información nutricional (rango E45:L46)
    # Suponemos que la tabla tiene encabezados en E45, y valores en E46
    nutricion = {}
    headers = [ws.cell(row=45, column=col).value for col in range(5, 13)]  # E to L
    values = [ws.cell(row=46, column=col).value for col in range(5, 13)]
    for i, header in enumerate(headers):
        if header and i < len(values):
            nutricion[header] = values[i]

    # Ingredientes con gramaje (rango E35:H43)
    ingredientes_gramaje = []
    for row in ws.iter_rows(min_row=35, max_row=43, min_col=5, max_col=8):  # E to H
        ingrediente = row[0].value
        gramos = row[3].value if len(row) > 3 else None
        if ingrediente and gramos is not None:
            ingredientes_gramaje.append({
                "nombre": str(ingrediente),
                "gramos": float(gramos) if isinstance(gramos, (int, float)) else 0
            })

    return {
        "nombre": nombre,
        "ingredientes": ingredientes,
        "alergenos": alergenos,
        "conservacion": conservacion,
        "fecha_caducidad": fecha_caducidad,
        "datos_logisticos": datos_logisticos,
        "gramos_racion": gramos_racion,
        "nutricion": nutricion,
        "ingredientes_gramaje": ingredientes_gramaje
    }

# Al iniciar la app, lee todos los archivos .xlsx en la raíz
def cargar_platos():
    global PLATOS
    PLATOS = []
    for filename in os.listdir("."):
        if filename.endswith(".xlsx") and not filename.startswith("platos_"):
            try:
                plato = leer_ficha_tecnica(filename)
                plato["archivo"] = filename
                PLATOS.append(plato)
                print(f"✅ Cargado: {filename}")
            except Exception as e:
                print(f"❌ Error al cargar {filename}: {e}")

# Cargar platos al iniciar
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
