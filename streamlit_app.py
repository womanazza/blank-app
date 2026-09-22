import streamlit as st
import subprocess
import sys

# ============ FIX: forzar instalación de librerías si faltan ============
def _asegurar_libreria(modulo, paquete):
    try:
        __import__(modulo)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])

_asegurar_libreria("bs4", "beautifulsoup4")
_asegurar_libreria("requests", "requests")
_asegurar_libreria("pandas", "pandas")

# ============ IMPORTS NORMALES ============
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from datetime import datetime, timedelta
from collections import Counter

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

tab_hoy, tab_historial, tab_combinado, tab_estadisticas, tab_suenios, tab_datos = st.tabs([
    "📅 Hoy",
    "🔄 Actualizar historial",
    "🧠 Análisis combinado",
    "📈 Estadísticas",
    "🌙 Sueños y Oficios",
    "📊 Datos guardados"
])

ARCHIVO_HISTORIAL = "historial_quiniela.csv"
ARCHIVO_ULTIMO_GUARDADO = "ultimo_guardado.txt"


# ============ FUNCIONES AUXILIARES ============
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


def guardar_dias_en_historial(dias=7):
    if os.path.exists(ARCHIVO_HISTORIAL):
        df_previo = pd.read_csv(ARCHIVO_HISTORIAL)
        fechas_hechas = set(df_previo["fecha"].unique())
    else:
        df_previo = pd.DataFrame()
        fechas_hechas = set()

    hoy = datetime.now()
    resultados = []
    errores = 0

    for i in range(dias):
        fecha = hoy - timedelta(days=i)
        fecha_str = fecha.strftime("%d/%m/%Y")
        fecha_url = fecha.strftime("%Y-%m-%d")

        if fecha_str in fechas_hechas:
            continue

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

    if resultados:
        df_nuevo = pd.DataFrame(resultados)
        df_final = pd.concat([df_previo, df_nuevo], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=["fecha", "turno"], keep="last")
        df_final.to_csv(ARCHIVO_HISTORIAL, index=False)
        return len(df_nuevo), len(df_final), errores
    return 0, len(df_previo), errores


def auto_guardar_si_corresponde():
    ahora = datetime.now()
    if os.path.exists(ARCHIVO_ULTIMO_GUARDADO):
        try:
            with open(ARCHIVO_ULTIMO_GUARDADO, "r") as f:
                ultimo = datetime.fromisoformat(f.read().strip())
            if (ahora - ultimo) < timedelta(hours=12):
                return 0, 0
        except Exception:
            pass
    try:
        nuevos, total, _ = guardar_dias_en_historial(7)
        with open(ARCHIVO_ULTIMO_GUARDADO, "w") as f:
            f.write(ahora.isoformat())
        return nuevos, total
    except Exception:
        return 0, 0


def mostrar_cuadros_verdes(aciertos, max_mostrar=60):
    if not aciertos:
        st.info("Sin aciertos.")
        return
    html_items = "".join([
        f'<div style="'
        f'display:inline-block; '
        f'background: linear-gradient(145deg, #1a3a1a, #0d200d); '
        f'border: 1px solid #2e7d32; '
        f'border-radius: 8px; '
        f'padding: 3px 6px; '
        f'margin: 2px; '
        f'text-align: center; '
        f'min-width: 55px;'
        f'">'
        f'<div style="font-size:13px; font-weight:bold; color:#7ef77e;">{a["numero"]}</div>'
        f'<div style="font-size:8px; color:#888;">{a["fecha"][:5]} · {a["turno"][:3]}</div>'
        f'</div>'
        for a in aciertos[:max_mostrar]
    ])
    st.html(f'<div style="line-height:1;">{html_items}</div>')


def mostrar_jugadas_en_caja(titulo, lista_numeros):
    if not lista_numeros:
        html_items = '<span style="color:#888;">Sin números</span>'
    else:
        html_items = "".join([
            f'<span style="display:inline-block; background:#222; padding:6px 12px; '
            f'border-radius:8px; margin:4px; font-weight:bold; color:#ff3333; '
            f'font-size:15px;">{n}</span>'
            for n in lista_numeros
        ])
    st.html(f"""
        <div style="
            border: 2px solid #ffffff;
            border-radius: 15px;
            padding: 12px;
            background-color: #000000;
            min-height: 100px;
        ">
            <h4 style="text-align:center; margin:0 0 10px 0; color:white;">
                {titulo}
            </h4>
            <div style="display:flex; flex-wrap:wrap; justify-content:center;">
                {html_items}
            </div>
        </div>
    """)


# ============ AUTO-GUARDADO ============
with st.spinner("Verificando historial..."):
    resultado = auto_guardar_si_corresponde()
    if resultado:
        nuevos, total = resultado
    else:
        nuevos, total = 0, 0


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

        st.markdown("---")
        if st.button("💾 Guardar los últimos 7 días en el historial", width='stretch'):
            with st.spinner("Guardando..."):
                nuevos, total, errores = guardar_dias_en_historial(7)
                with open(ARCHIVO_ULTIMO_GUARDADO, "w") as f:
                    f.write(datetime.now().isoformat())
            if nuevos > 0:
                st.success(f"✅ {nuevos} sorteos nuevos guardados. Total: {total} filas.")
            else:
                st.info(f"ℹ️ No había sorteos nuevos. Total: {total} filas.")


# ============ TAB 2: HISTORIAL ============
with tab_historial:
    st.markdown("### Traer historial desde la CAS")
    st.markdown("Recorre día por día la web oficial y guarda los sorteos en `historial_quiniela.csv`.")

    dias_atras = st.slider("Días hacia atrás", 7, 200, 30, step=1)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Traer historial completo", width='stretch'):
            with st.spinner("Trayendo datos..."):
                nuevos, total, errores = guardar_dias_en_historial(dias_atras)
                with open(ARCHIVO_ULTIMO_GUARDADO, "w") as f:
                    f.write(datetime.now().isoformat())

            if nuevos > 0:
                st.success(f"🎉 {nuevos} sorteos nuevos, {total} filas totales.")
                if errores:
                    st.warning(f"⚠️ {errores} días no se pudieron leer")
            else:
                st.info(f"No había sorteos nuevos. Total: {total} filas.")

    with col2:
        st.info("💡 Para guardar en GitHub, usá la terminal de Codespaces con `git push`.")


# ============ TAB: ANÁLISIS COMBINADO ============
with tab_combinado:
    st.markdown("### 🧠 Análisis combinado de métodos")

    import metodos

    if not os.path.exists(ARCHIVO_HISTORIAL):
        st.warning("Todavía no hay historial. Andá a 'Actualizar historial' y traé datos primero.")
    else:
        df_comb = pd.read_csv(ARCHIVO_HISTORIAL)
        st.markdown(f"Analizando **{len(df_comb)} filas** de historial.")

        st.markdown("#### Elegí el número base (opcional)")
        df_sorted_comb = df_comb.copy()
        df_sorted_comb["fecha_dt"] = pd.to_datetime(df_sorted_comb["fecha"], format="%d/%m/%Y", errors="coerce")
        df_sorted_comb = df_sorted_comb.sort_values("fecha_dt", ascending=False)
        opciones_comb = df_sorted_comb.apply(
            lambda r: f"{r['fecha']} - {r['turno']}", axis=1
        ).tolist()

        col_a, col_b = st.columns([1, 1])
        with col_a:
            seleccion_comb = st.selectbox(
                "Sorteo base (opcional):",
                ["(ninguno)"] + opciones_comb[:50],
                key="comb_base"
            )
        with col_b:
            num_manual_comb = st.text_input(
                "O escribí un número (opcional, máx 10 dígitos):",
                key="comb_manual",
                max_chars=10,
                placeholder="Ej: 4904"
            )

        num_base_comb = None
        if num_manual_comb and num_manual_comb.isdigit():
            num_base_comb = num_manual_comb
        elif seleccion_comb and seleccion_comb != "(ninguno)":
            idx_comb = opciones_comb.index(seleccion_comb)
            fila_comb = df_sorted_comb.iloc[idx_comb]
            num_base_comb = str(fila_comb["n1"]).zfill(4)

        if num_base_comb:
            st.markdown(f"**Número base elegido:** `{num_base_comb}`")
        else:
            st.markdown("**Sin número base** — algunos métodos no van a devolver resultados.")

        # --- Ejecutar todos los métodos ---
        METODOS = [
            ("Redoble", metodos.metodo_redoble),
            ("Suma/Resta 11", metodos.metodo_suma_resta_11),
            ("Números simpáticos", metodos.metodo_simpaticos),
            ("Vigésimo a la cabeza", metodos.metodo_vigesimo_a_la_cabeza),
            ("Suma de los 3 primeros", metodos.metodo_suma_3_primeros),
            ("Sorteo al revés", metodos.metodo_sorteo_al_reves),
            ("Secreto del segundo", metodos.metodo_secreto_segundo),
            ("Atrasados", metodos.metodo_atrasados),
            ("Decena + cifra", metodos.metodo_decena_cifra),
            ("Ambos repetidos", metodos.metodo_ambos_repetidos),
            ("Animales", metodos.metodo_animales),
        ]
        # Preparar el sorteo elegido
        sorteo_elegido = None
        if seleccion_comb and seleccion_comb != "(ninguno)":
            idx_comb = opciones_comb.index(seleccion_comb)
            sorteo_elegido = df_sorted_comb.iloc[idx_comb].to_dict()

        resultados_por_metodo = {}
        for nombre, funcion in METODOS:
            try:
                resultado = funcion(df_comb, sorteo_elegido=sorteo_elegido, num_base=num_base_comb)
            except TypeError:
                try:
                    resultado = funcion(df_comb, num_base_comb)
                except Exception:
                    resultado = []
            except Exception:
                resultado = []
            resultados_por_metodo[nombre] = resultado

        st.markdown("---")
        st.markdown("### Resultados por método")

        cols = st.columns(3)
        for i, (nombre, _) in enumerate(METODOS):
            with cols[i % 3]:
                lista = resultados_por_metodo[nombre]
                if lista:
                    items_html = "".join([
                        f'<span style="display:inline-block; background:#222; '
                        f'padding:4px 9px; border-radius:6px; margin:3px; '
                        f'font-weight:bold; color:#ff3333; font-size:14px;">{n}</span>'
                        for n in lista
                    ])
                else:
                    items_html = '<span style="color:#666; font-size:12px;">sin resultados</span>'

                info = metodos.INFO_METODOS.get(nombre, "")

                st.html(f"""
                    <div style="
                        border: 2px solid #ffffff;
                        border-radius: 12px;
                        padding: 10px;
                        background-color: #000000;
                        margin-bottom: 10px;
                        min-height: 80px;
                    ">
                        <h4 style="text-align:center; margin:0 0 8px 0;
                                   color:white; font-size:14px;">
                            {nombre}
                        </h4>
                        <div style="text-align:center;">
                            {items_html}
                        </div>
                    </div>
                """)
                with st.expander("ℹ️ ¿Qué hace este método?"):
                    st.markdown(f"<small>{info}</small>", unsafe_allow_html=True)

        # --- Bonus del día ---
        st.markdown("---")
        st.markdown("## 🎁 Bonus del día")
        st.markdown("Reglas que aplican hoy y suman puntos extra a los números que ya salieron.")

        bonus_aplicados = []
        cols_bonus = st.columns(3)
        for i, funcion_bonus in enumerate(metodos.BONUS_METODOS):
            try:
                info = funcion_bonus(df_comb, sorteo_elegido=sorteo_elegido)
            except Exception as e:
                info = {"nombre": "Error", "aplica": False, "motivo": str(e), "numeros": []}
            bonus_aplicados.append(info)
            with cols_bonus[i % 3]:
                if info["aplica"]:
                    color = "#2e7d32"
                    icono = "✅"
                    bg = "linear-gradient(145deg, #1a3a1a, #0d200d)"
                else:
                    color = "#555"
                    icono = "❌"
                    bg = "#0a0a0a"
                st.html(f"""
                    <div style="
                        background: {bg};
                        border: 1px solid {color};
                        border-radius: 10px;
                        padding: 8px;
                        margin-bottom: 8px;
                        min-height: 70px;
                    ">
                        <div style="font-size:12px; font-weight:bold; color:white;">
                            {icono} {info['nombre']}
                        </div>
                        <div style="font-size:10px; color:#aaa; margin-top:4px;">
                            {info['motivo']}
                        </div>
                    </div>
                """)

        # --- Score combinado ---
        st.markdown("---")
        st.markdown("## 🎯 Score combinado (Top 20)")
        st.markdown("+1 por cada método donde aparece, +1 extra por cada bonus del día que aplica.")

        contador = Counter()
        for nombre, _ in METODOS:
            vistos_en_metodo = set(resultados_por_metodo[nombre])
            for num in vistos_en_metodo:
                contador[num] += 1

        for info in bonus_aplicados:
            if info["aplica"] and info["numeros"]:
                for num in info["numeros"]:
                    if num in contador:
                        contador[num] += 1

        top_comb = contador.most_common(20)

        if top_comb:
            score_max = max(s for _, s in top_comb) if top_comb else 1

            cols_top = st.columns(8)
            for i, (num, score) in enumerate(top_comb):
                if score_max > 1:
                    intensidad = (score - 1) / (score_max - 1)
                else:
                    intensidad = 0

                r = int(0 + intensidad * 27)
                g = int(0 + intensidad * 94)
                b = int(0 + intensidad * 32)
                fondo = f"rgb({r},{g},{b})"
                borde_color = "#fff" if intensidad < 0.5 else "#7ef77e"

                with cols_top[i % 8]:
                    st.markdown(
                        f"""
                        <div style="border:1px solid {borde_color};
                                    border-radius:8px;
                                    padding:4px; text-align:center; margin:3px 0;
                                    background: {fondo};
                                    transition: background 0.3s;">
                            <div style="font-size:15px; font-weight:bold;
                                        color:#ff3333;">{num}</div>
                            <div style="font-size:9px; color:#bbb;">score {score}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("Ningún método devolvió resultados.")


# ============ TAB 4: ESTADÍSTICAS ============
with tab_estadisticas:
    st.markdown("### Análisis estadístico de la Quiniela")

    import reglas
    import metodo_tesla
    import metodo_piramide

    if not os.path.exists(ARCHIVO_HISTORIAL):
        st.warning("Todavía no hay historial. Andá a 'Actualizar historial' y traé datos primero.")
    else:
        df = pd.read_csv(ARCHIVO_HISTORIAL)
        st.markdown(f"Analizando **{len(df)} filas** de historial.")

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

        df_sorted = df.copy()
        df_sorted["fecha_dt"] = pd.to_datetime(df_sorted["fecha"], format="%d/%m/%Y", errors="coerce")
        df_sorted = df_sorted.sort_values("fecha_dt", ascending=False)
        opciones = df_sorted.apply(
            lambda r: f"{r['fecha']} - {r['turno']}", axis=1
        ).tolist()

        # MÉTODO TESLA
        st.markdown("---")
        st.markdown("## 🎩 Método Tesla")
        st.markdown("Elegí un sorteo del historial, **o** escribí un número propio (máx 10 dígitos).")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            seleccion = st.selectbox("Sorteo base (opcional):", ["(ninguno)"] + opciones[:50], key="tesla_base")
        with col_b:
            numero_manual_tesla = st.text_input("Número propio (opcional, máx 10 dígitos):", key="tesla_manual", max_chars=10, placeholder="Ej: 4904")

        num_base = None
        origen = ""
        if numero_manual_tesla and numero_manual_tesla.isdigit():
            num_base = numero_manual_tesla.zfill(4)
            origen = "Número propio"
        elif seleccion and seleccion != "(ninguno)":
            idx = opciones.index(seleccion)
            fila = df_sorted.iloc[idx]
            num_base = str(fila["n1"]).zfill(4)
            origen = f"Sorteo: {seleccion}"

        if num_base:
            st.markdown(f"### Número base: **{num_base}** ({origen})")
            analisis = metodo_tesla.analizar_numero(num_base)
            jugadas = metodo_tesla.generar_jugadas(analisis)
            st.markdown("### 🎯 Jugadas sugeridas")
            col1, col2, col3 = st.columns(3)
            with col1:
                mostrar_jugadas_en_caja("Ambos (2 cifras)", jugadas["ambos"])
            with col2:
                mostrar_jugadas_en_caja("Ternos (3 cifras)", jugadas["ternos"])
            with col3:
                mostrar_jugadas_en_caja("Números completos (4 cifras)", jugadas["cuatro_cifras"])
        else:
            st.info("Elegí un sorteo o escribí un número para ver las jugadas.")

        st.markdown("---")
        st.markdown("## 📊 Rendimiento del Método Tesla en el historial")
        stats = metodo_tesla.medir_metodo_tesla(df)
        if stats["total"] == 0:
            st.info("Necesitás al menos 2 sorteos cargados para medir el método.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Aciertos a la cabeza", f"{len(stats['aciertos_cabeza'])}/{stats['total']}", f"{100*len(stats['aciertos_cabeza'])/stats['total']:.1f}%")
            with c2:
                st.metric("Aciertos en los primeros 10", f"{len(stats['aciertos_10'])}/{stats['total']}", f"{100*len(stats['aciertos_10'])/stats['total']:.1f}%")
            with c3:
                st.metric("Aciertos en los 20", f"{len(stats['aciertos_20'])}/{stats['total']}", f"{100*len(stats['aciertos_20'])/stats['total']:.1f}%")
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
            seleccion_pir = st.selectbox("Sorteo base (opcional):", ["(ninguno)"] + opciones[:50], key="pir_base")
        with col_b:
            numero_manual = st.text_input("Número propio (opcional, máx 10 dígitos):", key="pir_manual", max_chars=10, placeholder="Ej: 15092026")

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
                st.markdown(f'<div style="text-align:center;">{html_fila}</div>', unsafe_allow_html=True)
            st.markdown("### 🎯 Jugadas sugeridas")
            col1, col2, col3 = st.columns(3)
            with col1:
                mostrar_jugadas_en_caja("Ambos (2 cifras)", jugadas_pir["ambos"])
            with col2:
                mostrar_jugadas_en_caja("Ternos (3 cifras)", jugadas_pir["ternos"])
            with col3:
                mostrar_jugadas_en_caja("Números completos (4 cifras)", jugadas_pir["cuatro_cifras"])
        else:
            st.info("Elegí un sorteo o escribí un número para ver las jugadas.")

        st.markdown("---")
        st.markdown("## 📊 Rendimiento del Método Pirámide en el historial")
        stats_pir = metodo_piramide.medir_metodo_piramide(df)
        if stats_pir["total_20"] == 0:
            st.info("Necesitás historial cargado para medir el método.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Aciertos a la cabeza", f"{len(stats_pir['aciertos_cabeza'])}/{stats_pir['total_cabeza']}", f"{100*len(stats_pir['aciertos_cabeza'])/stats_pir['total_cabeza']:.1f}%")
            with c2:
                st.metric("Aciertos en los primeros 10", f"{len(stats_pir['aciertos_10'])}/{stats_pir['total_10']}", f"{100*len(stats_pir['aciertos_10'])/stats_pir['total_10']:.1f}%")
            with c3:
                st.metric("Aciertos en los 20", f"{len(stats_pir['aciertos_20'])}/{stats_pir['total_20']}", f"{100*len(stats_pir['aciertos_20'])/stats_pir['total_20']:.1f}%")
            st.markdown("### ✅ Números acertados A LA CABEZA")
            mostrar_cuadros_verdes(stats_pir["aciertos_cabeza"])
            st.markdown("### ✅ Números acertados EN LOS PRIMEROS 10")
            mostrar_cuadros_verdes(stats_pir["aciertos_10"])
            st.markdown("### ✅ Números acertados EN LOS 20")
            mostrar_cuadros_verdes(stats_pir["aciertos_20"])

# ============ TAB: SUEÑOS Y OFICIOS ============
with tab_suenios:
    st.markdown("### 🌙 Sueños y Oficios")
    st.markdown("Buscá por número o por nombre y descubrí su significado.")

    import significados

      # --- Buscador ---
    st.markdown("#### 🔍 Buscador")
    st.markdown("Escribí un número (ej: 44) o un nombre (ej: La Cárcel).")

    col_busq, _ = st.columns([1, 3])
    with col_busq:
        consulta = st.text_input(
            "Buscar:",
            key="suenios_consulta",
            placeholder="Ej: 44  o  La Cárcel"
        )

    if consulta:
        consulta_limpia = consulta.strip()

        # Si es un número, mostramos sueño y oficio
        if consulta_limpia.isdigit():
            numero = consulta_limpia.zfill(2)[-2:]
            info = significados.buscar_por_numero(numero)
            st.markdown(f"### Número: **{info['numero']}**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    f"""
                    <div style="border:2px solid #fff; border-radius:12px;
                                padding:15px; background:#000; text-align:center;">
                        <div style="font-size:14px; color:#aaa;">🌙 Sueño</div>
                        <div style="font-size:22px; font-weight:bold; color:#ff3333; margin-top:8px;">
                            {info['suenio']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f"""
                    <div style="border:2px solid #fff; border-radius:12px;
                                padding:15px; background:#000; text-align:center;">
                        <div style="font-size:14px; color:#aaa;">🔨 Oficio</div>
                        <div style="font-size:22px; font-weight:bold; color:#ff3333; margin-top:8px;">
                            {info['oficio']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Si es texto, buscamos coincidencias
        else:
            resultados = significados.buscar_por_texto(consulta_limpia)
            if resultados:
                st.markdown(f"### Resultados para: **{consulta_limpia}**")
                cols = st.columns(5)
                for i, r in enumerate(resultados):
                    with cols[i % 5]:
                        st.markdown(
                            f"""
                            <div style="border:2px solid #fff; border-radius:10px;
                                        padding:10px; text-align:center; margin:5px 0;
                                        background:#000;">
                                <div style="font-size:22px; font-weight:bold; color:#ff3333;">
                                    {r['numero']}
                                </div>
                                <div style="font-size:11px; color:#aaa; margin-top:4px;">
                                    {r['tipo']}
                                </div>
                                <div style="font-size:12px; color:white; margin-top:2px;">
                                    {r['nombre']}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            else:
                st.info(f"No se encontró nada para '{consulta_limpia}'.")


    # --- Tablas completas ---
    sub_suenios, sub_oficios = st.tabs(["🌙 Sueños (0-99)", "🔨 Oficios (0-99)"])

    with sub_suenios:
        cols = st.columns(8)
        for i, (num, nombre) in enumerate(significados.SUENIOS.items()):
            with cols[i % 8]:
                st.markdown(
                    f"""
                    <div style="border:1px solid #555; border-radius:6px;
                                padding:3px; text-align:center; margin:2px 0;
                                background:#000;">
                        <div style="font-size:14px; font-weight:bold; color:#ff3333;
                                    line-height:1.1;">
                            {num}
                        </div>
                        <div style="font-size:10px; color:white;
                                    font-weight:600; line-height:1.1;
                                    margin-top:1px;">
                            {nombre}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with sub_oficios:
            cols = st.columns(8)
        for i, (num, nombre) in enumerate(significados.OFICIOS.items()):
            with cols[i % 8]:
                st.markdown(
                    f"""
                    <div style="border:1px solid #555; border-radius:6px;
                                padding:3px; text-align:center; margin:2px 0;
                                background:#000;">
                        <div style="font-size:14px; font-weight:bold; color:#ff3333;
                                    line-height:1.1;">
                            {num}
                        </div>
                        <div style="font-size:10px; color:white;
                                    font-weight:600; line-height:1.1;
                                    margin-top:1px;">
                            {nombre}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
# ============ TAB 5: DATOS ============
with tab_datos:
    st.markdown("### Datos guardados")
    for archivo in ["datos_quiniela.csv", ARCHIVO_HISTORIAL]:
        if os.path.exists(archivo):
            df = pd.read_csv(archivo)
            st.subheader(f"📄 {archivo} ({len(df)} filas)")
            st.dataframe(df.tail(30), width='stretch')
        else:
            st.info(f"📄 {archivo} todavía no existe")