import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import subprocess
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Quiniela San Juan")

st.markdown(
    """
    <style>
        .stApp { background-color: #000000; }
        h1, h2, h3, h4, h5, p, span, div, label { color: white; }

        .stButton > button {
            background: linear-gradient(145deg, #3a3a3a, #2a2a2a);
            color: white;
            border: 1px solid #555;
            border-radius: 12px;
            padding: 10px 20px;
            box-shadow: 4px 4px 8px #0a0a0a, -4px -4px 8px #444;
            font-weight: bold;
            transition: all 0.2s;
        }
        .stButton > button:hover {
            background: linear-gradient(145deg, #444, #333);
            box-shadow: 2px 2px 4px #0a0a0a, -2px -2px 4px #444;
        }
        .stButton > button:active {
            box-shadow: inset 4px 4px 8px #0a0a0a, inset -4px -4px 8px #444;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Quiniela San Juan")

# ---------------- Pestañas ----------------
tab_hoy, tab_historial, tab_datos = st.tabs(["📅 Hoy", "🔄 Actualizar historial", "📊 Datos guardados"])

# ============ TAB 1: Datos del día (CAS) ============
with tab_hoy:
    st.markdown("### Resultados del día (fuente oficial CAS)")

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    url_cas = f"https://cas.gob.ar/juegos/sorteos/resultados?juego=quiniela&fecha={fecha_hoy}"

    try:
        r = requests.get(url_cas, timeout=15)
        sopa = BeautifulSoup(r.text, "html.parser")

        tarjetas = sopa.find_all("div", class_="quiniela-card")

        orden = {"Vespertino": 0, "Vespertina": 0, "Tarde": 1, "Nocturno": 2, "Nocturna": 2}
        datos_dia = []

        for tarjeta in tarjetas:
            h4 = tarjeta.find("h4")
            if not h4:
                continue
            turno_txt = h4.get_text(strip=True)

            if "Vespertin" in turno_txt:
                turno = "Vespertina"
            elif "Tarde" in turno_txt:
                turno = "Tarde"
            elif "Nocturn" in turno_txt:
                turno = "Nocturna"
            else:
                continue

            # Extraer fecha del sorteo
            info = tarjeta.find("div", class_="quiniela-sorteo-info")
            fecha_sorteo = fecha_hoy
            if info:
                spans = info.find_all("span")
                for s in spans:
                    txt = s.get_text(strip=True)
                    if re.match(r"\d{2}/\d{2}/\d{4}", txt):
                        fecha_sorteo = txt
                        break

            # Extraer números
            tabla = tarjeta.find("table")
            if not tabla:
                continue
            numeros = [td.get_text(strip=True) for td in tabla.find_all("td", class_="num")]
            if len(numeros) < 20:
                continue

            datos_dia.append({
                "turno": turno,
                "fecha": fecha_sorteo,
                "numeros": numeros[:20],
                "orden": orden.get(turno, 99)
            })

        datos_dia.sort(key=lambda x: x["orden"])

        if datos_dia:
            columnas = st.columns(3)
            for i, d in enumerate(datos_dia):
                with columnas[i]:
                    filas_html = ""
                    for j in range(10):
                        n_izq = d["numeros"][j]
                        n_der = d["numeros"][j + 10]
                        estilo = "font-weight:bold; color:#ff3333;" if j == 0 else "color:white;"
                        filas_html += f"""
                        <tr>
                            <td style="text-align:center; padding:6px; color:#aaaaaa;
                                       border-bottom:1px solid #333;">{j+1}</td>
                            <td style="text-align:center; padding:6px; {estilo}
                                       border-bottom:1px solid #333;">{n_izq}</td>
                            <td style="text-align:center; padding:6px; color:#aaaaaa;
                                       border-bottom:1px solid #333;">{j+11}</td>
                            <td style="text-align:center; padding:6px; color:white;
                                       border-bottom:1px solid #333;">{n_der}</td>
                        </tr>
                        """

                    st.html(f"""
                        <div style="
                            border: 2px solid #ffffff;
                            border-radius: 15px;
                            padding: 15px;
                            background-color: #000000;
                        ">
                            <h3 style="text-align:center; margin:0 0 5px 0;
                                       color:white; font-weight:bold;">
                                {d['turno'].upper()}
                            </h3>
                            <p style="text-align:center; margin:0 0 10px 0;
                                      color:#cccccc; font-size:13px;">
                                San Juan ({d['fecha']})
                            </p>
                            <table style="width:100%; border-collapse:collapse;
                                          color:white; font-size:15px;">
                                {filas_html}
                            </table>
                        </div>
                    """)
        else:
            st.warning("No se encontraron datos para hoy en la CAS.")

    except Exception as e:
        st.error(f"Error al leer la CAS: {e}")

# ============ TAB 2: Actualizar historial ============
with tab_historial:
    st.markdown("### Traer historial desde la CAS (web oficial)")

    st.markdown("""
    Esta opción recorre **día por día** la web oficial de la Caja de Acción Social 
    y guarda los 3 sorteos (Vespertina, Tarde, Nocturna) en `historial_quiniela.csv`.
    
    - 📅 **Desde**: hace 6 meses
    - 📅 **Hasta**: hoy
    - ⏱️ **Tiempo estimado**: 2-3 minutos
    """)

    dias_atras = st.slider("Días hacia atrás", 7, 200, 180, step=1)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Traer historial completo", use_container_width=True):
            ARCHIVO = "historial_quiniela.csv"
            if os.path.exists(ARCHIVO):
                df_previo = pd.read_csv(ARCHIVO)
                fechas_hechas = set(df_previo["fecha"].unique())
                st.info(f"📂 Ya hay {len(fechas_hechas)} días guardados. Se van a saltear.")
            else:
                df_previo = pd.DataFrame()
                fechas_hechas = set()

            hoy = datetime.now()
            resultados = []
            progress = st.progress(0)
            status = st.empty()
            errores = 0

            for i in range(dias_atras):
                fecha = hoy - timedelta(days=i)
                fecha_str = fecha.strftime("%d/%m/%Y")
                fecha_url = fecha.strftime("%Y-%m-%d")

                if fecha_str in fechas_hechas:
                    progress.progress((i + 1) / dias_atras)
                    continue

                status.text(f"📅 {fecha_str}... ({i+1}/{dias_atras})")

                try:
                    url = f"https://cas.gob.ar/juegos/sorteos/resultados?juego=quiniela&fecha={fecha_url}"
                    r = requests.get(url, timeout=10)
                    sopa = BeautifulSoup(r.text, "html.parser")
                    tarjetas = sopa.find_all("div", class_="quiniela-card")

                    for tarjeta in tarjetas:
                        h4 = tarjeta.find("h4")
                        if not h4:
                            continue
                        turno_txt = h4.get_text(strip=True)
                        if "Vespertin" in turno_txt:
                            turno = "Vespertina"
                        elif "Tarde" in turno_txt:
                            turno = "Tarde"
                        elif "Nocturn" in turno_txt:
                            turno = "Nocturna"
                        else:
                            continue

                        tabla = tarjeta.find("table")
                        if not tabla:
                            continue
                        numeros = [td.get_text(strip=True) for td in tabla.find_all("td", class_="num")]
                        if len(numeros) < 20:
                            continue

                        resultados.append({
                            "fecha": fecha_str,
                            "turno": turno,
                            "cabeza": numeros[0][-2:],
                            **{f"n{j+1}": numeros[j] for j in range(20)}
                        })

                except Exception:
                    errores += 1

                progress.progress((i + 1) / dias_atras)

            # Guardar
            if resultados:
                df_nuevo = pd.DataFrame(resultados)
                df_final = pd.concat([df_previo, df_nuevo], ignore_index=True)
                df_final = df_final.drop_duplicates(subset=["fecha", "turno"], keep="last")
                df_final.to_csv("historial_quiniela.csv", index=False)
                status.success(f"🎉 Listo: {len(df_nuevo)} sorteos nuevos, {len(df_final)} filas totales")
                if errores:
                    st.warning(f"⚠️ {errores} días no se pudieron leer (probablemente no hay datos)")
            else:
                status.warning("No se encontraron datos nuevos")

    with col2:
        if st.button("💾 Guardar historial en GitHub", use_container_width=True):
            try:
                subprocess.run(["git", "add", "historial_quiniela.csv"], check=True, capture_output=True)
                subprocess.run(["git", "commit", "-m", "Actualizar historial CAS"], check=True, capture_output=True)
                subprocess.run(["git", "push"], check=True, capture_output=True)
                st.success("✅ Historial guardado en GitHub")
            except subprocess.CalledProcessError as e:
                st.error(f"Error: {e.stderr.decode() if e.stderr else e}")

# ============ TAB 3: Datos guardados ============
with tab_datos:
    st.markdown("### Datos guardados")

    for archivo in ["datos_quiniela.csv", "historial_quiniela.csv"]:
        if os.path.exists(archivo):
            df = pd.read_csv(archivo)
            st.subheader(f"📄 {archivo} ({len(df)} filas)")
            st.dataframe(df.tail(20), use_container_width=True)
        else:
            st.info(f"📄 {archivo} todavía no existe")