import streamlit as st

# ============ FIX: forzar instalación de librerías si faltan ============
import subprocess
import sys

def _asegurar_libreria(modulo, paquete):
    try:
        __import__(modulo)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])

_asegurar_libreria("bs4", "beautifulsoup4")
_asegurar_libreria("requests", "requests")
_asegurar_libreria("pandas", "pandas")
#_asegurar_libreria("lxml", "lxml")

# ============ IMPORTS NORMALES ============
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
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

tab_hoy, tab_historial, tab_estadisticas, tab_datos = st.tabs([
    "📅 Hoy",
    "🔄 Actualizar historial",
    "📈 Estadísticas",
    "📊 Datos guardados"
])


# ============ FUNCIONES ============
def clasificar_turno(texto):
    if "Vespertin" in texto:
        return "Vespertina"
    if "Tarde" in texto:
        return "Tarde"
    if "Nocturn" in texto:
        return "Nocturna"
    return None


def extraer_tarjetas(html):
    sopa = BeautifulSoup(html, "html.parser")
    tarjetas = sopa.find_all("div", class_="quiniela-card")
    sorteos = []
    for tarjeta in tarjetas:
        h4 = tarjeta.find("h4")
        if not h4:
            continue
        turno = clasificar_turno(h4.get_text(strip=True))
        if not turno:
            continue
        tabla = tarjeta.find("table")
        if not tabla:
            continue
        numeros = [td.get_text(strip=True) for td in tabla.find_all("td", class_="num")]
        numeros = [n for n in numeros if re.fullmatch(r"\d{4}", n)]
        if len(numeros) < 20:
            continue
        sorteos.append({
            "turno": turno,
            "numeros": numeros[:20],
            "cabeza": numeros[0][-2:]
        })
    orden = {"Vespertina": 0, "Tarde": 1, "Nocturna": 2}
    sorteos.sort(key=lambda x: orden.get(x["turno"], 99))
    return sorteos


def mostrar_tarjetas(sorteos, fecha_str):
    columnas = st.columns(3)
    for i, s in enumerate(sorteos):
        with columnas[i]:
            filas_html = ""
            for j in range(10):
                n_izq = s["numeros"][j]
                n_der = s["numeros"][j + 10]
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
                        {s['turno'].upper()}
                    </h3>
                    <p style="text-align:center; margin:0 0 10px 0;
                              color:#cccccc; font-size:13px;">
                        San Juan ({fecha_str})
                    </p>
                    <table style="width:100%; border-collapse:collapse;
                                  color:white; font-size:15px;">
                        {filas_html}
                    </table>
                </div>
            """)


def obtener_sorteos(fecha):
    fecha_url = fecha.strftime("%Y-%m-%d")
    try:
        r = requests.get(
            f"https://cas.gob.ar/juegos/sorteos/resultados?juego=quiniela&fecha={fecha_url}",
            timeout=15
        )
        return extraer_tarjetas(r.text)
    except Exception:
        return None


def mostrar_cuadros_verdes(aciertos, max_mostrar=50):
    if not aciertos:
        st.info("Sin aciertos.")
        return
    cols = st.columns(5)
    for i, a in enumerate(aciertos[:max_mostrar]):
        with cols[i % 5]:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(145deg, #1a3a1a, #0d200d);
                    border: 1px solid #2e7d32;
                    border-radius: 12px;
                    padding: 8px;
                    text-align: center;
                    margin: 5px 0;
                ">
                    <div style="font-size:18px; font-weight:bold; color:#7ef77e;">{a['numero']}</div>
                    <div style="font-size:10px; color:#888;">{a['fecha']} · {a['turno']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ============ TAB 1: HOY ============
with tab_hoy:
    st.markdown("### Resultados del día")
    hoy = datetime.now()
    fecha_display_hoy = hoy.strftime("%d/%m/%Y")

    sorteos = obtener_sorteos(hoy)
    fecha_mostrada = fecha_display_hoy
    es_de_hoy = True

    if not sorteos:
        for i in range(1, 8):
            fecha_buscar = hoy - timedelta(days=i)
            sorteos = obtener_sorteos(fecha_buscar)
            if sorteos:
                fecha_mostrada = fecha_buscar.strftime("%d/%m/%Y")
                es_de_hoy = False
                break

    if es_de_hoy and sorteos:
        st.markdown(f"#### 📅 {fecha_mostrada}")
    elif not es_de_hoy and sorteos:
        st.warning(
            f"⚠️ **Todavía no hay resultados para hoy ({fecha_display_hoy}).** "
            f"Mostrando el último sorteo disponible: **{fecha_mostrada}**"
        )
        st.markdown(f"#### 📅 {fecha_mostrada}")
    else:
        st.error("No se encontraron datos en los últimos 7 días.")

    if sorteos:
        mostrar_tarjetas(sorteos, fecha_mostrada)


# ============ TAB 2: HISTORIAL ============
with tab_historial:
    st.markdown("### Traer historial desde la CAS")
    st.markdown("Recorre día por día la web oficial y guarda los sorteos en `historial_quiniela.csv`.")

    dias_atras = st.slider("Días hacia atrás", 7, 200, 30, step=1)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Traer historial completo", width='stretch'):
            ARCHIVO = "historial_quiniela.csv"
            if os.path.exists(ARCHIVO):
                df_previo = pd.read_csv(ARCHIVO)
                fechas_hechas = set(df_previo["fecha"].unique())
                st.info(f"📂 Ya hay {len(fechas_hechas)} días guardados.")
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
                    sorteos = extraer_tarjetas(r.text)
                    for s in sorteos:
                        resultados.append({
                            "fecha": fecha_str,
                            "turno": s["turno"],
                            "cabeza": s["cabeza"],
                            **{f"n{j+1}": s["numeros"][j] for j in range(20)}
                        })
                except Exception:
                    errores += 1

                progress.progress((i + 1) / dias_atras)

            if resultados:
                df_nuevo = pd.DataFrame(resultados)
                df_final = pd.concat([df_previo, df_nuevo], ignore_index=True)
                df_final = df_final.drop_duplicates(subset=["fecha", "turno"], keep="last")
                df_final.to_csv(ARCHIVO, index=False)
                status.success(f"🎉 Listo: {len(df_nuevo)} sorteos nuevos, {len(df_final)} filas totales")
                if errores:
                    st.warning(f"⚠️ {errores} días no se pudieron leer")
            else:
                status.warning("No se encontraron datos nuevos")

    with col2:
        st.info("💡 Para guardar en GitHub, usá la terminal de Codespaces con `git push`.")


# ============ TAB 3: ESTADÍSTICAS ============
with tab_estadisticas:
    st.markdown("### Análisis estadístico de la Quiniela")

    import reglas
    import metodo_tesla
    import metodo_piramide

    ARCHIVO = "historial_quiniela.csv"
    if not os.path.exists(ARCHIVO):
        st.warning("Todavía no hay historial. Andá a 'Actualizar historial' y traé datos primero.")
    else:
        df = pd.read_csv(ARCHIVO)
        st.markdown(f"Analizando **{len(df)} filas** de historial.")

        # SCORE COMBINADO
        st.markdown("## 🎯 Score combinado (top 20)")
        st.markdown("Combina las 5 reglas ponderadas según su confiabilidad.")
        ranking = reglas.score_combinado(df)
        cols = st.columns(5)
        for i, (num, score) in enumerate(ranking):
            with cols[i % 5]:
                st.markdown(
                    f"""
                    <div style="border:2px solid #fff; border-radius:10px;
                                padding:8px; text-align:center; margin:5px 0;">
                        <div style="font-size:20px; font-weight:bold; color:#ff3333;">{num}</div>
                        <div style="font-size:11px; color:#aaa;">score {score:.0f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("---")

        # FRECUENCIA TOTAL
        st.markdown("## 📊 Frecuencia total (los que más salieron)")
        top = reglas.regla_frecuencia_total(df)
        cols = st.columns(5)
        for i, (num, cant) in enumerate(top):
            with cols[i % 5]:
                st.markdown(
                    f"""
                    <div style="border:1px solid #555; border-radius:8px;
                                padding:6px; text-align:center; margin:4px 0;">
                        <span style="font-size:17px; font-weight:bold;">{num}</span>
                        <span style="font-size:11px; color:#aaa;"> · {cant}x</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("---")

        # SALIDORES RECIENTES
        st.markdown("## 🔥 Salidores recientes (últimos 30 días)")
        top = reglas.regla_salidores_recientes(df, 30)
        cols = st.columns(5)
        for i, (num, cant) in enumerate(top):
            with cols[i % 5]:
                st.markdown(
                    f"""
                    <div style="border:1px solid #555; border-radius:8px;
                                padding:6px; text-align:center; margin:4px 0;">
                        <span style="font-size:17px; font-weight:bold;">{num}</span>
                        <span style="font-size:11px; color:#aaa;"> · {cant}x</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("---")

        # ATRASADOS
        st.markdown("## 🧊 Atrasados (hace más días que no salen)")
        top = reglas.regla_atrasados(df)
        cols = st.columns(5)
        for i, (num, dias) in enumerate(top):
            with cols[i % 5]:
                st.markdown(
                    f"""
                    <div style="border:1px solid #555; border-radius:8px;
                                padding:6px; text-align:center; margin:4px 0;">
                        <span style="font-size:17px; font-weight:bold;">{num}</span>
                        <span style="font-size:11px; color:#aaa;"> · {dias}d</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("---")

        # POR DÍA DE LA SEMANA
        hoy = datetime.now().weekday()
        nombre_dia = reglas.DIAS_ES[hoy]
        st.markdown(f"## 📅 Frecuencia por día ({nombre_dia})")
        top = reglas.regla_por_dia_semana(df, hoy)
        cols = st.columns(5)
        for i, (num, cant) in enumerate(top):
            with cols[i % 5]:
                st.markdown(
                    f"""
                    <div style="border:1px solid #555; border-radius:8px;
                                padding:6px; text-align:center; margin:4px 0;">
                        <span style="font-size:17px; font-weight:bold;">{num}</span>
                        <span style="font-size:11px; color:#aaa;"> · {cant}x</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("---")

        # POR DECENA
        st.markdown("## 🔢 Decenas más frecuentes")
        top = reglas.regla_por_decena(df)
        cols = st.columns(5)
        for i, (dec, cant) in enumerate(top):
            with cols[i % 5]:
                st.markdown(
                    f"""
                    <div style="border:1px solid #555; border-radius:8px;
                                padding:6px; text-align:center; margin:4px 0;">
                        <span style="font-size:17px; font-weight:bold;">{dec}</span>
                        <span style="font-size:11px; color:#aaa;"> · {cant}x</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # OPCIONES PARA MÉTODOS
        df_sorted = df.copy()
        df_sorted["fecha_dt"] = pd.to_datetime(df_sorted["fecha"], format="%d/%m/%Y", errors="coerce")
        df_sorted = df_sorted.sort_values("fecha_dt", ascending=False)
        opciones = df_sorted.apply(
            lambda r: f"{r['fecha']} - {r['turno']}", axis=1
        ).tolist()

        # MÉTODO TESLA
        st.markdown("---")
        st.markdown("## 🎩 Método Tesla")
        st.markdown("Seleccioná un sorteo base y el método calcula los números sugeridos.")

        seleccion = st.selectbox("Elegí el sorteo base (Tesla):", opciones[:50], key="tesla_base")

        if seleccion:
            idx = opciones.index(seleccion)
            fila = df_sorted.iloc[idx]
            num_base = str(fila["n1"]).zfill(4)

            st.markdown(f"### Número base: **{num_base}**")

            analisis = metodo_tesla.analizar_numero(num_base)
            jugadas = metodo_tesla.generar_jugadas(analisis)

            st.markdown("### 🎯 Jugadas sugeridas")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Ambos (2 cifras)**")
                for j in jugadas["ambos"]:
                    st.markdown(
                        f'<span style="background:#222; padding:5px 10px; '
                        f'border-radius:8px; margin:3px; display:inline-block; '
                        f'font-weight:bold; color:#ff3333;">{j}</span>',
                        unsafe_allow_html=True
                    )
            with col2:
                st.markdown("**Ternos (3 cifras)**")
                for j in jugadas["ternos"]:
                    st.markdown(
                        f'<span style="background:#222; padding:5px 10px; '
                        f'border-radius:8px; margin:3px; display:inline-block; '
                        f'font-weight:bold; color:#ff3333;">{j}</span>',
                        unsafe_allow_html=True
                    )
            with col3:
                st.markdown("**Números completos (4 cifras)**")
                for j in jugadas["cuatro_cifras"]:
                    st.markdown(
                        f'<span style="background:#222; padding:5px 10px; '
                        f'border-radius:8px; margin:3px; display:inline-block; '
                        f'font-weight:bold; color:#ff3333;">{j}</span>',
                        unsafe_allow_html=True
                    )

        # RENDIMIENTO TESLA
        st.markdown("---")
        st.markdown("## 📊 Rendimiento del Método Tesla en el historial")

        stats = metodo_tesla.medir_metodo_tesla(df)

        if stats["total"] == 0:
            st.info("Necesitás al menos 2 sorteos cargados para medir el método.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Aciertos a la cabeza",
                          f"{len(stats['aciertos_cabeza'])}/{stats['total']}",
                          f"{100*len(stats['aciertos_cabeza'])/stats['total']:.1f}%")
            with c2:
                st.metric("Aciertos en los primeros 10",
                          f"{len(stats['aciertos_10'])}/{stats['total']}",
                          f"{100*len(stats['aciertos_10'])/stats['total']:.1f}%")
            with c3:
                st.metric("Aciertos en los 20",
                          f"{len(stats['aciertos_20'])}/{stats['total']}",
                          f"{100*len(stats['aciertos_20'])/stats['total']:.1f}%")

            st.markdown("### ✅ Números acertados A LA CABEZA")
            mostrar_cuadros_verdes(stats["aciertos_cabeza"])

            st.markdown("### ✅ Números acertados EN LOS PRIMEROS 10")
            mostrar_cuadros_verdes(stats["aciertos_10"])

            st.markdown("### ✅ Números acertados EN LOS 20")
            mostrar_cuadros_verdes(stats["aciertos_20"])

        # MÉTODO PIRÁMIDE
        st.markdown("---")
        st.markdown("## 🔺 Método de la Pirámide")
        st.markdown("Elegí un sorteo del historial, **o** escribí un número propio (máx 10 dígitos).")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            seleccion_pir = st.selectbox(
                "Sorteo base (opcional):",
                ["(ninguno)"] + opciones[:50],
                key="pir_base"
            )
        with col_b:
            numero_manual = st.text_input(
                "Número propio (opcional, máx 10 dígitos):",
                key="pir_manual",
                max_chars=10,
                placeholder="Ej: 15092026"
            )

        num_base_pir = None
        origen = ""
        if numero_manual and numero_manual.isdigit():
            num_base_pir = numero_manual
            origen = "Número propio"
        elif seleccion_pir and seleccion_pir != "(ninguno)":
            idx_pir = opciones.index(seleccion_pir)
            fila_pir = df_sorted.iloc[idx_pir]
            num_base_pir = str(fila_pir["n1"]).zfill(4)
            origen = f"Sorteo: {seleccion_pir}"

        if num_base_pir:
            st.markdown(f"### Número base: **{num_base_pir}** ({origen})")

            jugadas_pir = metodo_piramide.generar_jugadas(num_base_pir)
            filas_pir = jugadas_pir["filas"]

            st.markdown("#### 🔺 Pirámide")
            for fila in filas_pir:
                html_fila = "".join([
                    f'<span style="display:inline-block; width:28px; height:28px; '
                    f'line-height:28px; text-align:center; margin:2px; '
                    f'background:#222; border-radius:6px; font-weight:bold; '
                    f'color:{"#ff3333" if len(fila) == 1 else "white"};">{d}</span>'
                    for d in fila
                ])
                st.markdown(
                    f'<div style="text-align:center;">{html_fila}</div>',
                    unsafe_allow_html=True
                )

            st.markdown("### 🎯 Jugadas sugeridas")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Ambos (2 cifras)**")
                for j in jugadas_pir["ambos"]:
                    st.markdown(
                        f'<span style="background:#222; padding:5px 10px; '
                        f'border-radius:8px; margin:3px; display:inline-block; '
                        f'font-weight:bold; color:#ff3333;">{j}</span>',
                        unsafe_allow_html=True
                    )
            with col2:
                st.markdown("**Ternos (3 cifras)**")
                for j in jugadas_pir["ternos"]:
                    st.markdown(
                        f'<span style="background:#222; padding:5px 10px; '
                        f'border-radius:8px; margin:3px; display:inline-block; '
                        f'font-weight:bold; color:#ff3333;">{j}</span>',
                        unsafe_allow_html=True
                    )
            with col3:
                st.markdown("**Números completos (4 cifras)**")
                for j in jugadas_pir["cuatro_cifras"]:
                    st.markdown(
                        f'<span style="background:#222; padding:5px 10px; '
                        f'border-radius:8px; margin:3px; display:inline-block; '
                        f'font-weight:bold; color:#ff3333;">{j}</span>',
                        unsafe_allow_html=True
                    )
        else:
            st.info("Elegí un sorteo o escribí un número para ver las jugadas.")

        # RENDIMIENTO PIRÁMIDE
        st.markdown("---")
        st.markdown("## 📊 Rendimiento del Método Pirámide en el historial")
        st.markdown("Aplica la pirámide a la **fecha de cada día** y compara contra los 3 sorteos de ese día.")

        stats_pir = metodo_piramide.medir_metodo_piramide(df)

        if stats_pir["total_20"] == 0:
            st.info("Necesitás historial cargado para medir el método.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(
                    "Aciertos a la cabeza",
                    f"{len(stats_pir['aciertos_cabeza'])}/{stats_pir['total_cabeza']}",
                    f"{100*len(stats_pir['aciertos_cabeza'])/stats_pir['total_cabeza']:.1f}%"
                )
            with c2:
                st.metric(
                    "Aciertos en los primeros 10",
                    f"{len(stats_pir['aciertos_10'])}/{stats_pir['total_10']}",
                    f"{100*len(stats_pir['aciertos_10'])/stats_pir['total_10']:.1f}%"
                )
            with c3:
                st.metric(
                    "Aciertos en los 20",
                    f"{len(stats_pir['aciertos_20'])}/{stats_pir['total_20']}",
                    f"{100*len(stats_pir['aciertos_20'])/stats_pir['total_20']:.1f}%"
                )

            st.markdown("### ✅ Números acertados A LA CABEZA")
            mostrar_cuadros_verdes(stats_pir["aciertos_cabeza"])

            st.markdown("### ✅ Números acertados EN LOS PRIMEROS 10")
            mostrar_cuadros_verdes(stats_pir["aciertos_10"])

            st.markdown("### ✅ Números acertados EN LOS 20")
            mostrar_cuadros_verdes(stats_pir["aciertos_20"])


# ============ TAB 4: DATOS ============
with tab_datos:
    st.markdown("### Datos guardados")

    for archivo in ["datos_quiniela.csv", "historial_quiniela.csv"]:
        if os.path.exists(archivo):
            df = pd.read_csv(archivo)
            st.subheader(f"📄 {archivo} ({len(df)} filas)")
            st.dataframe(df.tail(30), width='stretch')
        else:
            st.info(f"📄 {archivo} todavía no existe")