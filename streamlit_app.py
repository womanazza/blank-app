import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import subprocess

st.set_page_config(layout="wide", page_title="Quiniela San Juan")

st.markdown(
    """
    <style>
        .stApp { background-color: #000000; }
        h1, h2, h3, h4, h5, p, span, div, label { color: white; }

        /* Estilo de botones con relieve */
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

st.title("Quiniela San Juan - Datos del día")

url = "https://www.loteriasmundiales.com.ar/Quinielas/san-juan"

try:
    r = requests.get(url, timeout=15)
    sopa = BeautifulSoup(r.text, "html.parser")

    texto_pagina = sopa.get_text(" ", strip=True)
    fecha_match = re.search(
        r"Resultados del d[ií]a\s+\w+\s+(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})",
        texto_pagina, re.IGNORECASE
    )
    fecha_str = fecha_match.group(1) if fecha_match else "Fecha desconocida"
    st.markdown(f"### 📅 {fecha_str}")

    tarjetas = sopa.find_all("div", class_=lambda c: c and "w3-card" in c)

    resultados = []
    for tarjeta in tarjetas:
        texto_tarjeta = tarjeta.get_text(" ", strip=True)
        if "San Juan" not in texto_tarjeta:
            continue

        upper = texto_tarjeta.upper()
        if "VESPERTINA" in upper:
            turno = "Vespertina"
            hora = "14:00 hs"
        elif "NOCTURNA" in upper:
            turno = "Nocturna"
            hora = "21:00 hs"
        elif "TARDE" in upper:
            turno = "Tarde"
            hora = "17:30 hs"
        else:
            continue

        tabla = tarjeta.find("table")
        if not tabla:
            continue

        numeros = []
        for celda in tabla.find_all("td"):
            txt = celda.get_text(strip=True)
            if re.fullmatch(r"\d{4}", txt):
                numeros.append(txt)

        if len(numeros) < 20:
            continue

        numeros = numeros[:20]
        resultados.append({
            "fecha": fecha_str,
            "turno": turno,
            "hora": hora,
            "cabeza": numeros[0][-2:],
            "numeros": numeros,
        })

    orden = {"Vespertina": 0, "Tarde": 1, "Nocturna": 2}
    resultados.sort(key=lambda x: orden.get(x["turno"], 99))

    if resultados:
        columnas = st.columns(3)

        for i, resultado in enumerate(resultados):
            with columnas[i]:
                filas_html = ""
                for j in range(10):
                    n_izq = resultado["numeros"][j]
                    n_der = resultado["numeros"][j + 10]
                    estilo_izq = "font-weight:bold; color:#ff3333;" if j == 0 else "color:white;"

                    filas_html += f"""
                    <tr>
                        <td style="text-align:center; padding:6px; color:#aaaaaa;
                                   border-bottom:1px solid #333;">{j+1}</td>
                        <td style="text-align:center; padding:6px; {estilo_izq}
                                   border-bottom:1px solid #333;">{n_izq}</td>
                        <td style="text-align:center; padding:6px; color:#aaaaaa;
                                   border-bottom:1px solid #333;">{j+11}</td>
                        <td style="text-align:center; padding:6px; color:white;
                                   border-bottom:1px solid #333;">{n_der}</td>
                    </tr>
                    """

                st.html(
                    f"""
                    <div style="
                        border: 2px solid #ffffff;
                        border-radius: 15px;
                        padding: 15px;
                        background-color: #000000;
                    ">
                        <h3 style="text-align:center; margin:0 0 5px 0;
                                   color:white; font-weight:bold;">
                            {resultado['turno'].upper()}
                        </h3>
                        <p style="text-align:center; margin:0 0 10px 0;
                                  color:#cccccc; font-size:13px;">
                            San Juan ({resultado['hora']})
                        </p>
                        <table style="width:100%; border-collapse:collapse;
                                      color:white; font-size:15px;">
                            {filas_html}
                        </table>
                    </div>
                    """
                )

        # Guardar CSV
        df = pd.DataFrame([{
            "fecha": r["fecha"], "turno": r["turno"], "cabeza": r["cabeza"],
            **{f"n{i+1}": r["numeros"][i] for i in range(20)}
        } for r in resultados])

        archivo = "datos_quiniela.csv"
        if os.path.exists(archivo):
            df_previo = pd.read_csv(archivo)
            df = pd.concat([df_previo, df], ignore_index=True)
            df = df.drop_duplicates(subset=["fecha", "turno"], keep="last")
        df.to_csv(archivo, index=False)

        # Botón para subir a GitHub
        st.markdown("---")
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            if st.button("💾 Guardar en GitHub", use_container_width=True):
                try:
                    subprocess.run(["git", "add", "datos_quiniela.csv"],
                                   check=True, capture_output=True)
                    subprocess.run(["git", "commit", "-m",
                                    f"Actualizar datos {fecha_str}"],
                                   check=True, capture_output=True)
                    subprocess.run(["git", "push"],
                                   check=True, capture_output=True)
                    st.success("✅ Datos guardados en GitHub")
                except subprocess.CalledProcessError as e:
                    st.error(f"Error al guardar: {e.stderr.decode() if e.stderr else e}")

    else:
        st.warning("No se encontraron resultados de San Juan.")

except Exception as e:
    st.error(f"Error: {e}")