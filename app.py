from flask import Flask, jsonify, send_from_directory, request, Response
import os
import csv
from openpyxl import load_workbook
import unicodedata
from datetime import datetime

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
    if nombre_norm in BASE_NUTRICIONAL:
        return BASE_NUTRICIONAL[nombre_norm]
    for clave in BASE_NUTRICIONAL:
        if nombre_norm in clave or clave in nombre_norm:
            return BASE_NUTRICIONAL[clave]
    # Palabras clave genéricas
    if "pollo" in nombre_norm: return BASE_NUTRICIONAL.get("pollo", {})
    if "cerdo" in nombre_norm: return BASE_NUTRICIONAL.get("cerdo", {})
    if "ternera" in nombre_norm: return BASE_NUTRICIONAL.get("ternera", {})
    if "pescado" in nombre_norm: return BASE_NUTRICIONAL.get("pescado", {})
    if "huevo" in nombre_norm: return BASE_NUTRICIONAL.get("huevos", {})
    if "patata" in nombre_norm: return BASE_NUTRICIONAL.get("patata", {})
    if "zanahoria" in nombre_norm: return BASE_NUTRICIONAL.get("zanahoria", {})
    if "cebolla" in nombre_norm: return BASE_NUTRICIONAL.get("cebolla", {})
    if "tomate" in nombre_norm: return BASE_NUTRICIONAL.get("tomate", {})
    if "lechuga" in nombre_norm: return BASE_NUTRICIONAL.get("lechuga", {})
    if "aceite" in nombre_norm and "oliva" in nombre_norm: return BASE_NUTRICIONAL.get("aceite de oliva", {})
    if "sal" in nombre_norm: return BASE_NUTRICIONAL.get("sal", {})
    if "agua" in nombre_norm: return BASE_NUTRICIONAL.get("agua", {})
    print(f"⚠️ Ingrediente no encontrado, usando 'pollo': '{nombre_ing}'")
    return BASE_NUTRICIONAL.get("pollo", {})

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

    try:
        # Cargar plantilla
        wb = load_workbook("plantilla_menu.xlsx")
        ws = wb.active

        # Rellenar encabezado
        ws["I2"] = f"Menú Escolar - {colegio}"
        ws["AB2"] = mes
        ws["AG2"] = anio

        # Mapeo de días a columnas (B=2, H=8→9, O=15, V=22, AC=29)
        col_inicio = {'Lun': 2, 'Mar': 9, 'Mié': 16, 'Jue': 23, 'Vie': 30}

        # Rellenar cada día
        for fecha_str, menu in menu_datos.items():
            if not any([menu.get("primer"), menu.get("segundo"), menu.get("postre")]):
                continue

            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
            except:
                continue

            dia_semana = fecha.strftime("%a")[:3]
            if dia_semana not in col_inicio:
                continue

            col = col_inicio[dia_semana]
            fila_base = 5  # B5

            # Obtener platos
            p1 = next((p for p in PLATOS if p["nombre"] == menu.get("primer")), None)
            p2 = next((p for p in PLATOS if p["nombre"] == menu.get("segundo")), None)
            pA = next((p for p in PLATOS if p["nombre"] == menu.get("acompanamiento")), None)
            p3 = next((p for p in PLATOS if p["nombre"] == menu.get("postre")), None)
            pPan = next((p for p in PLATOS if p["nombre"] == menu.get("pan")), None)

            # Rellenar celdas combinadas
            from openpyxl.utils import get_column_letter
            from openpyxl.worksheet.merge_cells import MergedCellRange

            # Función para combinar y rellenar
            def combinar_y_rellenar(fila, col_inicio, col_fin, valor):
                ws.merge_cells(start_row=fila, start_column=col_inicio, end_row=fila, end_column=col_fin)
                ws.cell(row=fila, column=col_inicio, value=valor)

            combinar_y_rellenar(fila_base, col, col+5, p1["nombre"] if p1 else "")
            combinar_y_rellenar(fila_base+1, col, col+5, traducir_al_ingles(p1["nombre"] if p1 else ""))
            combinar_y_rellenar(fila_base+2, col, col+5, p2["nombre"] if p2 else "")
            combinar_y_rellenar(fila_base+3, col, col+5, pA["nombre"] if pA else "")
            combinar_y_rellenar(fila_base+4, col, col+5, f"{traducir_al_ingles(p2['nombre'] if p2 else '')} with {traducir_al_ingles(pA['nombre'] if pA else '')}")
            combinar_y_rellenar(fila_base+5, col, col+5, f"{p3['nombre'] if p3 else ''} + Agua + {pPan['nombre'] if pPan else 'Pan'}")
            combinar_y_rellenar(fila_base+6, col, col+5, f"{traducir_al_ingles(p3['nombre'] if p3 else '')} + Water + {traducir_al_ingles(pPan['nombre'] if pPan else 'Bread')}")

            # Nutrición
            nut1 = p1["nutricion"] if p1 else {}
            nut2 = p2["nutricion"] if p2 else {}
            nutA = pA["nutricion"] if pA else {}
            nut3 = p3["nutricion"] if p3 else {}
            nutPan = pPan["nutricion"] if pPan else {}

            def get_val(nut, key):
                return nut.get(key, 0)

            kcal_total = get_val(nut1, "kcal") + get_val(nut2, "kcal") + get_val(nutA, "kcal") + get_val(nut3, "kcal") + get_val(nutPan, "kcal")
            lip_total = get_val(nut1, "lip") + get_val(nut2, "lip") + get_val(nutA, "lip") + get_val(nut3, "lip") + get_val(nutPan, "lip")
            ags_total = get_val(nut1, "ags") + get_val(nut2, "ags") + get_val(nutA, "ags") + get_val(nut3, "ags") + get_val(nutPan, "ags")
            prot_total = get_val(nut1, "prot") + get_val(nut2, "prot") + get_val(nutA, "prot") + get_val(nut3, "prot") + get_val(nutPan, "prot")
            hdec_total = get_val(nut1, "hdec") + get_val(nut2, "hdec") + get_val(nutA, "hdec") + get_val(nut3, "hdec") + get_val(nutPan, "hdec")
            azucares_total = get_val(nut1, "azucares") + get_val(nut2, "azucares") + get_val(nutA, "azucares") + get_val(nut3, "azucares") + get_val(nutPan, "azucares")
            vit_a_total = get_val(nut1, "vit_a") + get_val(nut2, "vit_a") + get_val(nutA, "vit_a") + get_val(nut3, "vit_a") + get_val(nutPan, "vit_a")
            vit_c_total = get_val(nut1, "vit_c") + get_val(nut2, "vit_c") + get_val(nutA, "vit_c") + get_val(nut3, "vit_c") + get_val(nutPan, "vit_c")
            vit_d_total = get_val(nut1, "vit_d") + get_val(nut2, "vit_d") + get_val(nutA, "vit_d") + get_val(nut3, "vit_d") + get_val(nutPan, "vit_d")
            ca_total = get_val(nut1, "ca") + get_val(nut2, "ca") + get_val(nutA, "ca") + get_val(nut3, "ca") + get_val(nutPan, "ca")
            fe_total = get_val(nut1, "fe") + get_val(nut2, "fe") + get_val(nutA, "fe") + get_val(nut3, "fe") + get_val(nutPan, "fe")
            sal_total = get_val(nut1, "sal") + get_val(nut2, "sal") + get_val(nutA, "sal") + get_val(nut3, "sal") + get_val(nutPan, "sal")

            # Encabezados y valores
            encabezados = ["E (Kcal)", "Líp (g)", "AGS (g)", "Prot (g)", "HdeC (g)", "Azucares"]
            valores = [kcal_total, lip_total, ags_total, prot_total, hdec_total, azucares_total]
            for i, (enc, val) in enumerate(zip(encabezados, valores)):
                ws.cell(row=fila_base+7, column=col+i, value=enc)
                ws.cell(row=fila_base+8, column=col+i, value=round(val, 1))

            encabezados_micro = ["Vit A (µg)", "Vit C (mg)", "vit D (µg)", "Ca (mg)", "Fe (mg)", "Sal"]
            valores_micro = [vit_a_total, vit_c_total, vit_d_total, ca_total, fe_total, sal_total]
            for i, (enc, val) in enumerate(zip(encabezados_micro, valores_micro)):
                ws.cell(row=fila_base+9, column=col+i, value=enc)
                ws.cell(row=fila_base+10, column=col+i, value=round(val, 1))

            # Filas de cena (fondo #ffcc99)
            from openpyxl.styles import PatternFill
            fill = PatternFill(start_color="FFCC99", end_color="FFCC99", fill_type="solid")
            ws.cell(row=fila_base+11, column=col, value="cena")
            for c in range(col+1, col+6):
                ws.cell(row=fila_base+11, column=c).fill = fill
            for c in range(col, col+6):
                ws.cell(row=fila_base+12, column=c).fill = fill

            # Columna A: día y día de la semana
            ws.cell(row=fila_base, column=1, value=fecha.day)
            ws.merge_cells(start_row=fila_base+1, start_column=1, end_row=fila_base+7, end_column=1)
            ws.cell(row=fila_base+1, column=1, value=dia_semana)
            ws.cell(row=fila_base+1, column=1).alignment = Alignment(text_rotation=90)

        # Pie de página
        ultima_fila = fila_base + 15
        pie_textos = [
            "Valorado nutricionalmente por Leticia Montoiro Peinado, Diplomada en Nutrición Humana y Dietética. Nº Colegiada CYL00207",
            "La fruta podrá variar en función de su grado de madurez. Valoración nutricional en base a niños de 6-9 años.",
            "Para cualquier consulta del menú o información de alérgenos, puedes enviar un correo a nuestra nutricionista a: nutricion@cofuri.es",
            "* Las recetas elaboradas llevan excluidos los alimentos arriba detallados."
        ]
        for i, texto in enumerate(pie_textos):
            ws.cell(row=ultima_fila + i, column=2, value=texto)

        # Guardar en memoria
        from io import BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment;filename=menu_escolar_{colegio}_{mes}_{anio}.xlsx"}
        )

    except Exception as e:
        print(f"Error al exportar: {e}")
        return jsonify({"error": "Error al generar Excel"}), 500

def traducir_al_ingles(texto):
    traducciones = {
        "Lentejas": "Lentils", "Alubias": "Beans", "Sopa": "Soup", "Crema": "Cream", "Pasta": "Pasta",
        "Guiso": "Stew", "Puré": "Mash", "Verduras": "Vegetables", "Pollo": "Chicken", "Pescado": "Fish",
        "Carne": "Meat", "Jamón": "Ham", "Chorizo": "Chorizo", "Morcilla": "Blood sausage", "Merluza": "Hake",
        "Bacalao": "Cod", "Salmón": "Salmon", "Atún": "Tuna", "Sardinas": "Sardines", "Patata": "Potato",
        "Zanahoria": "Carrot", "Cebolla": "Onion", "Tomate": "Tomato", "Pimiento": "Pepper", "Calabacín": "Zucchini",
        "Espinacas": "Spinach", "Acelgas": "Chard", "Judías verdes": "Green beans", "Brócoli": "Broccoli",
        "Coliflor": "Cauliflower", "Lechuga": "Lettuce", "Puerro": "Leek", "Apio": "Celery", "Remolacha": "Beetroot",
        "Champiñón": "Mushroom", "Ajo": "Garlic", "Guisantes": "Peas", "Maíz": "Corn", "Manzana": "Apple",
        "Pera": "Pear", "Plátano": "Banana", "Naranja": "Orange", "Mandarina": "Tangerine", "Uva": "Grape",
        "Melón": "Melon", "Sandía": "Watermelon", "Fresa": "Strawberry", "Kiwi": "Kiwi", "Piña": "Pineapple",
        "Melocotón": "Peach", "Ciruela": "Plum", "Higo": "Fig", "Aguacate": "Avocado", "Leche": "Milk",
        "Yogur": "Yogurt", "Queso fresco": "Fresh cheese", "Requesón": "Cottage cheese", "Huevo": "Egg",
        "Gelatina": "Gelatin", "Flan": "Flan", "Natillas": "Custard", "Pan": "Bread", "Agua": "Water"
    }
    for es, en in traducciones.items():
        if es in texto:
            texto = texto.replace(es, en)
    return texto

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
