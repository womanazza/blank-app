"""
Reglas y análisis para la Quiniela de San Juan.
Cada regla devuelve un diccionario {numero: puntaje} o una lista de tuplas (numero, puntaje).
"""
import pandas as pd
from datetime import datetime
from collections import Counter

DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def extraer_todos_los_numeros(df):
    """Devuelve una lista con TODOS los números de todos los sorteos"""
    columnas = [f"n{i}" for i in range(1, 21)]
    numeros = []
    for _, fila in df.iterrows():
        for col in columnas:
            if pd.notna(fila.get(col)):
                numeros.append(str(fila[col]).zfill(4))
    return numeros


def extraer_cabezas(df):
    """Devuelve solo las cabezas (n1)"""
    return [str(n).zfill(4) for n in df["n1"].dropna().tolist()]


# ============ REGLAS ============

def regla_frecuencia_total(df):
    """Los 20 números que más salieron en todo el historial (a los 20)"""
    todos = extraer_todos_los_numeros(df)
    contador = Counter(todos)
    return contador.most_common(20)


def regla_salidores_recientes(df, dias=30):
    """Los 20 números que más salieron en los últimos N días"""
    # Convertir fecha a datetime
    df = df.copy()
    df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    fecha_limite = datetime.now() - pd.Timedelta(days=dias)
    df_reciente = df[df["fecha_dt"] >= fecha_limite]

    if df_reciente.empty:
        return []

    todos = extraer_todos_los_numeros(df_reciente)
    contador = Counter(todos)
    return contador.most_common(20)


def regla_atrasados(df):
    """Los 20 números que hace más tiempo que no salen"""
    df = df.copy()
    df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.sort_values("fecha_dt", ascending=False)

    columnas = [f"n{i}" for i in range(1, 21)]
    ultima_aparicion = {}

    # Recorremos los sorteos del más reciente al más viejo
    for idx, fila in df.iterrows():
        fecha = fila["fecha_dt"]
        for col in columnas:
            num = str(fila.get(col, "")).zfill(4)
            if num and num not in ultima_aparicion:
                ultima_aparicion[num] = fecha

    # Calcular días sin salir
    hoy = datetime.now()
    atrasos = []
    for num, fecha in ultima_aparicion.items():
        if pd.notna(fecha):
            dias = (hoy - fecha.to_pydatetime()).days
            atrasos.append((num, dias))

    atrasos.sort(key=lambda x: x[1], reverse=True)
    return atrasos[:20]


def regla_por_dia_semana(df, dia_semana):
    """
    Los 20 números que más salieron un día específico de la semana.
    dia_semana: 0=Lunes, 1=Martes, ..., 6=Domingo
    """
    df = df.copy()
    df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    df["dia"] = df["fecha_dt"].dt.dayofweek

    df_dia = df[df["dia"] == dia_semana]
    if df_dia.empty:
        return []

    todos = extraer_todos_los_numeros(df_dia)
    contador = Counter(todos)
    return contador.most_common(20)


def regla_por_decena(df):
    """
    Devuelve las 20 decenas (00-09, 10-19, ..., 90-99) que más salieron.
    El 'número' representativo de cada decena es la decena + '0' (ej: 90 para 90-99).
    """
    todos = extraer_todos_los_numeros(df)
    contador = Counter()

    for num in todos:
        if len(num) == 4:
            decena = num[:2]  # primeros dos dígitos
            contador[decena] += 1

    top = contador.most_common(20)
    # Convertimos a números representativos tipo "9000" para mostrarlo
    return [(f"{dec}xx", cant) for dec, cant in top]


def score_combinado(df):
    """
    Combina todas las reglas en un score único por número.
    Cada regla aporta puntos según la posición en el top.
    """
    todos_numeros = set(extraer_todos_los_numeros(df))
    scores = {num: 0 for num in todos_numeros}

    # Regla 1: frecuencia total (peso 1.0)
    for i, (num, _) in enumerate(regla_frecuencia_total(df)):
        if num in scores:
            scores[num] += (20 - i) * 1.0

    # Regla 2: salidores recientes (peso 1.5)
    for i, (num, _) in enumerate(regla_salidores_recientes(df, 30)):
        if num in scores:
            scores[num] += (20 - i) * 1.5

    # Regla 3: atrasados (peso 0.5, porque "compensar" es falacia)
    for i, (num, _) in enumerate(regla_atrasados(df)):
        if num in scores:
            scores[num] += (20 - i) * 0.5

    # Regla 4: día de la semana actual (peso 1.0)
    hoy = datetime.now().weekday()
    for i, (num, _) in enumerate(regla_por_dia_semana(df, hoy)):
        if num in scores:
            scores[num] += (20 - i) * 1.0

    # Regla 5: decenas más frecuentes (peso 0.5)
    decenas_top = regla_por_decena(df)
    decenas_buenas = [d.replace("xx", "") for d, _ in decenas_top[:5]]
    for num in scores:
        if num[:2] in decenas_buenas:
            scores[num] += 5

    # Ordenar por score
    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranking[:20]