from flask import Flask, jsonify, send_from_directory, request, Response
import os
import csv
from openpyxl import load_workbook
import unicodedata
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment

app = Flask(__name__)
PLATOS = []
BASE_NUTRICIONAL = {}

# ==============================
# CARGAR BASE NUTRICIONAL
# ==============================
def cargar_base_nutricional():
    global BASE_NUTRICIONAL
    ruta = "ingredientes.csv"
    if os.path.exists(ruta):
        try:
            with open(ruta, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                required_cols = ["Alimento", "E (Kcal)", "Líp (g)", "AGS (g)", "Prot (g)", "HdeC (g)", "Azucares", "Vit A (µg)", "Vit C (mg)", "vit D (µg)", "Ca (mg)", "Fe (mg)", "Sal"]
                if not all(col in reader.fieldnames for col in required_cols):
                    print("❌ CSV no tiene columnas requeridas.")
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
        print("⚠️ ingredientes.csv no encontrado.")

def normalizar_texto(texto):
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

def buscar_ingrediente(nombre_ing):
    nombre_norm = normalizar_texto(nombre_ing)
    if not nombre_norm:
        return BASE_NUTRICIONAL.get("agua", {"kcal":0,"lip":0,"ags":0,"prot":0,"hdec":0,"azucares":0,"vit_a":0,"vit_c":0,"vit_d":0,"ca":0,"fe":0,"sal":0})

    # 1. Coincidencia exacta
    if nombre_norm in BASE_NUTRICIONAL:
        return BASE_NUTRICIONAL[nombre_norm]

    # 2. Buscar por palabras clave (más robusto)
    palabras_ing = set(nombre_norm.split())
    mejor_coincidencia = None
    max_coincidencias = 0

    for clave_norm, nut in BASE_NUTRICIONAL.items():
        palabras_clave = set(clave_norm.split())
        coincidencias = len(palabras_ing & palabras_clave)  # intersección
        
        # También buscar subcadenas de al menos 3 letras
        for palabra in palabras_ing:
            if len(palabra) >= 3:
                for palabra_clave in palabras_clave:
                    if palabra in palabra_clave or palabra_clave in palabra:
                        coincidencias += 1
        
        if coincidencias > max_coincidencias:
            max_coincidencias = coincidencias
            mejor_coincidencia = nut

    if mejor_coincidencia and max_coincidencias >= 1:
        print(f"🔍 Coincidencia por palabras: '{nombre_ing}' → '{mejor_coincidencia}' ({max_coincidencias} coincidencias)")
        return mejor_coincidencia

    # 3. Último recurso: usar "agua"
    print(f"⚠️ Ingrediente no encontrado, usando 'agua': '{nombre_ing}'")
    return BASE_NUTRICIONAL.get("agua", {"kcal":0,"lip":0,"ags":0,"prot":0,"hdec":0,"azucares":0,"vit_a":0,"vit_c":0,"vit_d":0,"ca":0,"fe":0,"sal":0})

def calcular_nutricion_plato(ingredientes_gramaje):
    total = {"kcal": 0, "lip": 0, "ags": 0, "prot": 0, "hdec": 0, "azucares": 0, "vit_a": 0, "vit_c": 0, "vit_d": 0, "ca": 0, "fe": 0, "sal": 0}
    for item in ingredientes_gramaje:
        nombre = item["nombre"]
        gramos = item["gramos"]
        if gramos <= 0: continue
        nut = buscar_ingrediente(nombre)
        factor = gramos / 100.0
        for k in total:
            total[k] += nut.get(k, 0) * factor
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

    gramos_racion = float(ws["H44"].value) if isinstance(ws["H44"].value, (int, float)) else sum(item["gramos"] for item in ingredientes_gramaje)
    nutricion = calcular_nutricion_plato(ingredientes_gramaje)

    return {
        "nombre": nombre,
        "ingredientes": ingredientes,
        "alergenos": alergenos,
        "ingredientes_gramaje": ingredientes_gramaje,
        "gramos_racion": gramos_racion,
        "nutricion": nutricion,
        "archivo": os.path.basename(ruta_excel)
    }

def cargar_platos():
    global PLATOS
    PLATOS = []
    for filename in os.listdir("."):
        if filename.endswith(".xlsx") and filename != "plantilla_menu.xlsx":
            try:
                plato = leer_ficha_tecnica(filename)
                PLATOS.append(plato)
                print(f"✅ Cargado: {filename}")
            except Exception as e:
                print(f"❌ Error al cargar {filename}: {e}")

# ==============================
# RUTA PARA EXPORTAR USANDO PLANTILLA
# ==============================
@app.route("/api/exportar", methods=["POST"])
def exportar_menu():
    data = request.json
    colegio = data.get("colegio")
    mes = data.get("mes")
    anio = data.get("anio")
    menu_datos = data.get("menu", {})

    if not colegio or not menu_datos:
        return jsonify({"error": "Faltan datos"}), 400

    # Generar HTML con formato de Excel
    html = f"""
    <html xmlns:o="urn:schemas-microsoft-com:office:office" 
          xmlns:x="urn:schemas-microsoft-com:office:excel" 
          xmlns="http://www.w3.org/TR/REC-html40">
    <head>
    <meta http-equiv=Content-Type content="text/html; charset=utf-8">
    <style>
        body {{ font-family: Arial; font-size: 11pt; }}
        table {{ border-collapse: collapse; }}
        td, th {{ border: 1px solid black; padding: 4px; }}
        .encabezado {{ font-family: 'Very Simple Chalk'; font-size: 22pt; color: #385724; text-align: center; }}
        .cena {{ background-color: #ffcc99; }}
        .rotado {{ writing-mode: tb-rl; text-align: center; }}
    </style>
    <!--[if gte mso 9]><xml>
    <x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet>
    <x:Name>Menú Mensual</x:Name>
    <x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions>
    </x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->
    </head>
    <body>
    <table>
    <tr>
        <td colspan="8"></td>
        <td colspan="28" class="encabezado">Menú Escolar - {colegio}</td>
    </tr>
    <tr>
        <td colspan="8"></td>
        <td colspan="20" class="encabezado">{mes}</td>
        <td colspan="8" class="encabezado">{anio}</td>
    </tr>
    """

    # Aquí iría la lógica para generar filas por día
    # (simplificada para el ejemplo)

    html += """
    </table>
    </body>
    </html>
    """

    return Response(
        html,
        mimetype="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment;filename=menu_{colegio}_{mes}_{anio}.xls"}
    )
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
