from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime, timedelta
import pandas as pd
import os

URL = "https://www.loteriasmundiales.com.ar/Quinielas/san-juan"
MESES_ATRAS = 6
ARCHIVO = "historial_quiniela.csv"
GUARDAR_CADA = 10

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}

# Cargar progreso previo
if os.path.exists(ARCHIVO):
    df_previo = pd.read_csv(ARCHIVO)
    fechas_hechas = set(df_previo["fecha"].unique())
    print(f"📂 Progreso previo: {len(fechas_hechas)} días ya cargados")
else:
    df_previo = pd.DataFrame()
    fechas_hechas = set()
    print("📂 Empezando de cero")

def extraer_sorteos(html, fecha_str):
    sopa = BeautifulSoup(html, "html.parser")
    tarjetas = sopa.find_all("div", class_=lambda c: c and "w3-card" in c)
    sorteos = []
    for tarjeta in tarjetas:
        texto = tarjeta.get_text(" ", strip=True)
        if "San Juan" not in texto:
            continue
        upper = texto.upper()
        if "VESPERTINA" in upper:
            turno = "Vespertina"
        elif "NOCTURNA" in upper:
            turno = "Nocturna"
        elif "TARDE" in upper:
            turno = "Tarde"
        else:
            continue
        tabla = tarjeta.find("table")
        if not tabla:
            continue
        numeros = [c.get_text(strip=True) for c in tabla.find_all("td")
                   if re.fullmatch(r"\d{4}", c.get_text(strip=True))]
        if len(numeros) < 20:
            continue
        numeros = numeros[:20]
        sorteos.append({
            "fecha": fecha_str, "turno": turno, "cabeza": numeros[0][-2:],
            **{f"n{i+1}": numeros[i] for i in range(20)}
        })
    return sorteos

def leer_mes_calendario(page):
    """Lee el título del mes actual del calendario, devuelve (mes, año)"""
    try:
        label = page.locator('[data-calendar-label="month"]').first.inner_text(timeout=3000)
        partes = label.lower().split()
        if len(partes) >= 2:
            mes = MESES_ES.get(partes[0], 0)
            anio = int(partes[1])
            return mes, anio
    except:
        pass
    return 0, 0

def navegar_al_mes(page, mes_objetivo, anio_objetivo, max_clics=24):
    """Hace clic en ← hasta llegar al mes objetivo"""
    for _ in range(max_clics):
        mes_actual, anio_actual = leer_mes_calendario(page)

        if mes_actual == mes_objetivo and anio_actual == anio_objetivo:
            return True

        if mes_actual == 0:
            return False

        # Si estamos antes del objetivo, no podemos avanzar
        if (anio_actual, mes_actual) < (anio_objetivo, mes_objetivo):
            return False

        try:
            page.click('[data-calendar-toggle="previous"]', timeout=3000)
            time.sleep(0.4)
        except:
            return False

    return False

hoy = datetime.now()
resultados_nuevos = []
total_dias = MESES_ATRAS * 30

with sync_playwright() as p:
    print("🌐 Abriendo navegador...")
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page()
    page.goto(URL, timeout=30000)
    time.sleep(3)
    print("✅ Página cargada")
    print(f"🎯 Objetivo: {total_dias} días hacia atrás\n")

    for i in range(total_dias):
        fecha = hoy - timedelta(days=i)
        fecha_display = fecha.strftime("%d/%m/%Y")

        if fecha_display in fechas_hechas:
            continue

        if i > 0 and i % 10 == 0:
            print(f"\n📊 Progreso: {i}/{total_dias} días ({i*100//total_dias}%)\n")

        print(f"📅 {fecha_display}... ", end="", flush=True)

        try:
            # Asegurar que no haya popup abierto
            page.keyboard.press("Escape")
            time.sleep(0.3)

            # Abrir calendario
            page.click("text=Otras fechas", timeout=5000)
            time.sleep(1.0)

            # Navegar al mes correcto
            mes_obj = fecha.month
            anio_obj = fecha.year

            if not navegar_al_mes(page, mes_obj, anio_obj):
                print(f"⚠️ no se pudo llegar al mes")
                page.keyboard.press("Escape")
                time.sleep(0.5)
                continue

            # Buscar el día correcto
            dia_num = str(fecha.day)
            dias = page.locator("[data-calendar-date]")
            cantidad = dias.count()

            encontrado = False
            for j in range(cantidad):
                dia_elem = dias.nth(j)
                texto_dia = dia_elem.inner_text().strip()
                if texto_dia == dia_num:
                    dia_elem.click(timeout=5000)
                    time.sleep(1.5)
                    encontrado = True
                    break

            if not encontrado:
                print(f"⚠️ día {dia_num} no encontrado")
                page.keyboard.press("Escape")
                time.sleep(0.5)
                continue

            # Extraer
            html = page.content()
            sorteos = extraer_sorteos(html, fecha_display)

            if sorteos:
                resultados_nuevos.extend(sorteos)
                print(f"✅ {len(sorteos)} sorteos")
            else:
                print("⚠️ sin datos")

            # Guardado parcial
            if len(resultados_nuevos) > 0 and (i + 1) % GUARDAR_CADA == 0:
                df_nuevo = pd.DataFrame(resultados_nuevos)
                df_final = pd.concat([df_previo, df_nuevo], ignore_index=True)
                df_final = df_final.drop_duplicates(subset=["fecha", "turno"], keep="last")
                df_final.to_csv(ARCHIVO, index=False)
                print(f"💾 Guardado ({len(df_final)} filas)")

        except Exception as e:
            print(f"❌ {str(e)[:60]}")
            try:
                page.keyboard.press("Escape")
                time.sleep(0.5)
            except:
                pass
            continue

    browser.close()

# Guardado final
if resultados_nuevos:
    df_nuevo = pd.DataFrame(resultados_nuevos)
    df_final = pd.concat([df_previo, df_nuevo], ignore_index=True)
    df_final = df_final.drop_duplicates(subset=["fecha", "turno"], keep="last")
    df_final.to_csv(ARCHIVO, index=False)
    print(f"\n🎉 ¡LISTO! {len(df_final)} filas en {ARCHIVO}")
else:
    print(f"\n⚠️ No se extrajeron datos nuevos")