from flask import Flask, jsonify, send_from_directory, request, Response
import os
import csv
from openpyxl import load_workbook
import unicodedata
from datetime import datetime

app = Flask(__name__)
PLATOS = []
BASE_NUTRICIONAL = {}

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
    texto = texto.strip()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.upper()

def buscar_ingrediente(nombre_ing):
    nombre_norm = normalizar_texto(nombre_ing)
    if not nombre_norm:
        return BASE_NUTRICIONAL.get("AGUA", {"kcal":0,"lip":0,"ags":0,"prot":0,"hdec":0,"azucares":0,"vit_a":0,"vit_c":0,"vit_d":0,"ca":0,"fe":0,"sal":0})

    if nombre_norm in BASE_NUTRICIONAL:
        return BASE_NUTRICIONAL[nombre_norm]

    print(f"⚠️ Ingrediente no encontrado: '{nombre_ing}' → usando 'AGUA'")
    return BASE_NUTRICIONAL.get("AGUA", {"kcal":0,"lip":0,"ags":0,"prot":0,"hdec":0,"azucares":0,"vit_a":0,"vit_c":0,"vit_d":0,"ca":0,"fe":0,"sal":0})

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

def clasificar_platos_dict():
    primeros = [p for p in PLATOS if p["archivo"].startswith("PR.")]
    segundos = [p for p in PLATOS if p["archivo"].startswith("PO.")]
    acompanamientos = [p for p in PLATOS if p["archivo"].startswith("AC.")]
    postres = [p for p in PLATOS if p["archivo"].startswith("DE.")]
    panes = [p for p in PLATOS if p["archivo"].startswith("PA.")]
    return {
        "primeros": primeros,
        "segundos": segundos,
        "acompanamientos": acompanamientos,
        "postres": postres,
        "panes": panes
    }

def traducir_al_ingles(texto):
    if not texto:
        return ""
    traducciones = {
        "LENTEJAS": "Lentils", "ALUBIAS": "Beans", "SOPA": "Soup", "CREMA": "Cream", "PASTA": "Pasta",
        "GUISO": "Stew", "PURÉ": "Mash", "VERDURAS": "Vegetables", "POLLO": "Chicken", "PESCADO": "Fish",
        "CARNE": "Meat", "JAMÓN": "Ham", "CHORIZO": "Chorizo", "MORCILLA": "Blood sausage", "MERLUZA": "Hake",
        "BACALAO": "Cod", "SALMÓN": "Salmon", "ATÚN": "Tuna", "SARDINAS": "Sardines", "PATATA": "Potato",
        "ZANAHORIA": "Carrot", "CEBOLLA": "Onion", "TOMATE": "Tomato", "PIMIENTO": "Pepper", "CALABACÍN": "Zucchini",
        "ESPINACAS": "Spinach", "ACELGAS": "Chard", "JUDÍAS VERDES": "Green beans", "BRÓCOLI": "Broccoli",
        "COLIFLOR": "Cauliflower", "LECHUGA": "Lettuce", "PUERRO": "Leek", "APIO": "Celery", "REMOLACHA": "Beetroot",
        "CHAMPINÓN": "Mushroom", "AJO": "Garlic", "GUISANTES": "Peas", "MAÍZ": "Corn", "MANZANA": "Apple",
        "PERA": "Pear", "PLÁTANO": "Banana", "NARANJA": "Orange", "MANDARINA": "Tangerine", "UVA": "Grape",
        "MELÓN": "Melon", "SANDÍA": "Watermelon", "FRESA": "Strawberry", "KIWI": "Kiwi", "PIÑA": "Pineapple",
        "MELOCOTÓN": "Peach", "CIRUELA": "Plum", "HIGO": "Fig", "AGUACATE": "Avocado", "LECHE": "Milk",
        "YOGUR": "Yogurt", "QUESO FRESCO": "Fresh cheese", "REQUESÓN": "Cottage cheese", "HUEVO": "Egg",
        "GELATINA": "Gelatin", "FLAN": "Flan", "NATILLAS": "Custard", "PAN": "Bread", "AGUA": "Water"
    }
    for es, en in traducciones.items():
        if es in texto:
            texto = texto.replace(es, en)
    return texto

@app.route("/api/exportar", methods=["POST"])
def exportar_menu():
    data = request.json
    colegio = data.get("colegio")
    mes = data.get("mes")
    anio = data.get("anio")
    menu_datos = data.get("menu", {})

    if not colegio or not menu_datos:
        return jsonify({"error": "Faltan datos"}), 400

    platos_dict = clasificar_platos_dict()
    primeros = platos_dict["primeros"]
    segundos = platos_dict["segundos"]
    acompanamientos = platos_dict["acompanamientos"]
    postres = platos_dict["postres"]
    panes = platos_dict["panes"]
    todos_platos = primeros + segundos + acompanamientos + postres + panes

    def get_plato(nombre):
        for p in todos_platos:
            if p["nombre"] == nombre:
                return p
        return None

    html = '''<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office" 
      xmlns:x="urn:schemas-microsoft-com:office:excel" 
      xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta http-equiv=Content-Type content="text/html; charset=utf-8">
<style>
body { font-family: Arial; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 1px solid #000; padding: 4px; font-size: 11pt; height: 20px; }
.encabezado { font-family: "Very Simple Chalk"; font-size: 22pt; color: #385724; text-align: center; height: 30px; }
.celda-combinada { text-align: center; vertical-align: middle; font-size: 16pt; height: 25px; }
.cena { background-color: #ffcc99; }
.columna-dia { width: 20px; text-align: center; vertical-align: middle; font-size: 12pt; }
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
    <td colspan="28" class="encabezado">Menú Escolar - ''' + colegio + '''</td>
</tr>
<tr>
    <td colspan="8"></td>
    <td colspan="20" class="encabezado">''' + mes + '''</td>
    <td colspan="8" class="encabezado">''' + str(anio) + '''</td>
</tr>
'''

    dias_procesados = 0
    for fecha_str, menu in menu_datos.items():
        if not any([menu.get("primer"), menu.get("segundo"), menu.get("postre")]):
            continue

        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        except:
            continue

        dia_semana = fecha.strftime("%a")[:3]
        if dia_semana not in ['Lun', 'Mar', 'Mié', 'Jue', 'Vie']:
            continue

        p1 = get_plato(menu.get("primer", ""))
        p2 = get_plato(menu.get("segundo", ""))
        pA = get_plato(menu.get("acompanamiento", ""))
        p3 = get_plato(menu.get("postre", ""))
        pPan = get_plato(menu.get("pan", ""))

        def get_nut(plato):
            return plato["nutricion"] if plato else {"kcal":0,"lip":0,"ags":0,"prot":0,"hdec":0,"azucares":0,"vit_a":0,"vit_c":0,"vit_d":0,"ca":0,"fe":0,"sal":0}

        nut1, nut2, nutA, nut3, nutPan = map(get_nut, [p1, p2, pA, p3, pPan])

        def sumar_nut(clave):
            return round(nut1[clave] + nut2[clave] + nutA[clave] + nut3[clave] + nutPan[clave], 1)

        html += f'''
        <tr>
            <td class="columna-dia" rowspan="13">{fecha.day}</td>
            <td class="celda-combinada" colspan="6">{p1["nombre"] if p1 else ""}</td>
        </tr>
        <tr><td class="celda-combinada" colspan="6">{traducir_al_ingles(p1["nombre"] if p1 else "")}</td></tr>
        <tr><td class="celda-combinada" colspan="6">{p2["nombre"] if p2 else ""}</td></tr>
        <tr><td class="celda-combinada" colspan="6">{pA["nombre"] if pA else ""}</td></tr>
        <tr><td class="celda-combinada" colspan="6">{traducir_al_ingles(p2["nombre"] if p2 else "")} with {traducir_al_ingles(pA["nombre"] if pA else "")}</td></tr>
        <tr><td class="celda-combinada" colspan="6">{(p3["nombre"] if p3 else "") + " + Agua + " + (pPan["nombre"] if pPan else "Pan")}</td></tr>
        <tr><td class="celda-combinada" colspan="6">{traducir_al_ingles(p3["nombre"] if p3 else "")} + Water + {traducir_al_ingles(pPan["nombre"] if pPan else "Bread")}</td></tr>
        <tr>
            <td>E (Kcal)</td><td>Líp (g)</td><td>AGS (g)</td><td>Prot (g)</td><td>HdeC (g)</td><td>Azucares</td>
        </tr>
        <tr>
            <td>{sumar_nut("kcal")}</td><td>{sumar_nut("lip")}</td><td>{sumar_nut("ags")}</td><td>{sumar_nut("prot")}</td><td>{sumar_nut("hdec")}</td><td>{sumar_nut("azucares")}</td>
        </tr>
        <tr>
            <td>Vit A (µg)</td><td>Vit C (mg)</td><td>vit D (µg)</td><td>Ca (mg)</td><td>Fe (mg)</td><td>Sal</td>
        </tr>
        <tr>
            <td>{sumar_nut("vit_a")}</td><td>{sumar_nut("vit_c")}</td><td>{sumar_nut("vit_d")}</td><td>{sumar_nut("ca")}</td><td>{sumar_nut("fe")}</td><td>{sumar_nut("sal")}</td>
        </tr>
        <tr>
            <td class="cena">cena</td>
            <td class="cena" colspan="5"></td>
        </tr>
        <tr>
            <td class="cena"></td>
            <td class="cena" colspan="5"></td>
        </tr>
        '''

        dias_procesados += 1
        if dias_procesados >= 25:
            break

    html += '''
    </table>
    <br><br>
    <div style="font-size: 12pt; font-family: Arial;">
    Valorado nutricionalmente por Leticia Montoiro Peinado, Diplomada en Nutrición Humana y Dietética. Nº Colegiada CYL00207<br>
    La fruta podrá variar en función de su grado de madurez. Valoración nutricional en base a niños de 6-9 años.<br>
    Para cualquier consulta del menú o información de alérgenos, puedes enviar un correo a nuestra nutricionista a: nutricion@cofuri.es<br>
    * Las recetas elaboradas llevan excluidos los alimentos arriba detallados.
    </div>
    </body>
    </html>
    '''

    return Response(
        html,
        mimetype="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment;filename=menu_escolar_{colegio.replace(' ', '_')}_{mes}_{anio}.xls"}
    )

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/api/platos")
def obtener_platos():
    return jsonify({"platos": PLATOS})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
