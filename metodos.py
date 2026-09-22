"""
Métodos de análisis multi-método para la Quiniela de San Juan.
Cada método recibe:
  - df: el historial completo (DataFrame con columnas fecha, turno, n1..n20)
  - num_base: número opcional de 4 dígitos (para métodos que lo usan)
Devuelve una lista de hasta 20 strings (números de 2, 3 o 4 cifras).

También cada método tiene un diccionario INFO_METODOS con su explicación.
"""
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter


# ============ INFORMACIÓN DE LOS MÉTODOS ============
INFO_METODOS = {
    "Redoble": "Analiza los últimos 30 días del historial. Busca números que salieron exactamente 2 veces a la cabeza. La idea es que, estadísticamente, los que salen 2 veces suelen repetir una tercera vez. NO usa el número base: trabaja solo con el historial.",
    "Suma/Resta 11": "Toma el número base y lo divide en sus dos ambos (los 2 primeros dígitos y los 2 últimos). A cada ambo le suma 11 y le resta 11. Con eso se generan 4 números de 2 cifras, más los 4-cifras completos que resulten.",
    "Números simpáticos": "Se basa en una tabla de 'números simpáticos' o relacionados: cuando sale uno, se espera el otro. La tabla actual es: 99→15, 18→34, 31→42, 03→29. Busca en las cabezas de los últimos 20 sorteos.",
    "Vigésimo a la cabeza": "Toma el 20° premio del sorteo elegido. La idea es que, según la estadística, ese número suele aparecer a la cabeza en el sorteo siguiente. Devuelve el número completo, su cabeza y la cabeza invertida.",
    "Suma de los 3 primeros": "Suma los 3 primeros premios del sorteo elegido. Muestra los últimos 4, 3 y 2 dígitos del resultado, más el total completo.",
    "Sorteo al revés": "Toma el primer premio del sorteo elegido y lo invierte dígito por dígito (ej: 2354 → 4532). Devuelve el invertido completo y su cabeza invertida.",
}


# ============ UTILIDADES ============
def _preparar_df(df):
    df = df.copy()
    df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.sort_values("fecha_dt", ascending=False).reset_index(drop=True)
    return df


def _limitar(lista, maximo=20):
    vistos = set()
    resultado = []
    for x in lista:
        if x not in vistos:
            vistos.add(x)
            resultado.append(x)
        if len(resultado) >= maximo:
            break
    return resultado


# ============ MÉTODO 1: REDOBLE ============
def metodo_redoble(df, num_base=None):
    df = _preparar_df(df)
    if df.empty:
        return []

    hace_30 = datetime.now() - timedelta(days=30)
    df_30 = df[df["fecha_dt"] >= hace_30]

    if df_30.empty:
        return []

    cabezas = [str(int(n)).zfill(4)[-2:] for n in df_30["n1"].dropna()]
    contador = Counter(cabezas)

    candidatos = [num for num, cant in contador.items() if cant == 2]
    candidatos_ordenados = []
    for cab in cabezas:
        if cab in candidatos and cab not in candidatos_ordenados:
            candidatos_ordenados.append(cab)

    return _limitar(candidatos_ordenados)


# ============ MÉTODO 5: SUMA 11 / RESTA 11 ============
def metodo_suma_resta_11(df, num_base=None):
    """
    Suma 11 y resta 11 a cada ambo del número base.
    Genera 4 números de 2 cifras + sus variantes de 4 cifras.
    """
    if not num_base:
        return []

    base = str(num_base).zfill(4)
    if len(base) < 4:
        base = base.zfill(4)

    ambo1 = int(base[:2])
    ambo2 = int(base[2:])

    resultados = []

    # Para cada ambo, sumamos y restamos 11 (módulo 100)
    for ambo in [ambo1, ambo2]:
        for delta in [11, -11]:
            nuevo = (ambo + delta) % 100
            resultados.append(f"{nuevo:02d}")

    # Versiones de 4 cifras (combinando los nuevos ambos con los del base)
    for delta1 in [11, -11]:
        for delta2 in [11, -11]:
            n1 = (ambo1 + delta1) % 100
            n2 = (ambo2 + delta2) % 100
            resultados.append(f"{n1:02d}{n2:02d}")

    return _limitar(resultados)


# ============ MÉTODO 17: NÚMEROS SIMPÁTICOS ============
TABLA_SIMPATICOS = {
    "99": "15",
    "18": "34",
    "31": "42",
    "03": "29",
}

def metodo_simpaticos(df, num_base=None):
    df = _preparar_df(df)
    if df.empty:
        return []

    cabezas = [str(int(n)).zfill(4)[-2:] for n in df["n1"].dropna()][:20]
    resultados = []

    for cab in cabezas:
        if cab in TABLA_SIMPATICOS:
            resultados.append(TABLA_SIMPATICOS[cab])
        for origen, destino in TABLA_SIMPATICOS.items():
            if cab == destino:
                resultados.append(origen)

    return _limitar(resultados)
    # ============ MÉTODO 4: VIGÉSIMO A LA CABEZA ============
def metodo_vigesimo_a_la_cabeza(df, sorteo_elegido=None, num_base=None):
    """
    Toma el 20° premio (n20) del sorteo elegido.
    Devuelve: n20 completo, su cabeza (últimos 2 dígitos) y su invertido.
    """
    if sorteo_elegido is None:
        return []

    try:
        n20 = str(sorteo_elegido["n20"]).zfill(4)
    except Exception:
        return []

    cabeza = n20[-2:]
    cabeza_inv = cabeza[::-1]

    return _limitar([n20, cabeza, cabeza_inv])


# ============ MÉTODO 8: SUMA DE LOS 3 PRIMEROS ============
def metodo_suma_3_primeros(df, sorteo_elegido=None, num_base=None):
    """
    Suma los 3 primeros premios (n1 + n2 + n3) del sorteo elegido.
    Devuelve: últimos 4, últimos 3, últimos 2, y el total completo.
    """
    if sorteo_elegido is None:
        return []

    try:
        n1 = int(str(sorteo_elegido["n1"]).zfill(4))
        n2 = int(str(sorteo_elegido["n2"]).zfill(4))
        n3 = int(str(sorteo_elegido["n3"]).zfill(4))
    except Exception:
        return []

    suma = n1 + n2 + n3
    s = str(suma)

    resultados = []
    # Últimos 4 dígitos
    ult4 = s[-4:] if len(s) >= 4 else s.zfill(4)
    resultados.append(ult4)
    # Últimos 3 dígitos
    ult3 = s[-3:] if len(s) >= 3 else s.zfill(3)
    resultados.append(ult3)
    # Últimos 2 dígitos
    ult2 = s[-2:] if len(s) >= 2 else s.zfill(2)
    resultados.append(ult2)
    # Total completo
    resultados.append(s)

    return _limitar(resultados)


# ============ MÉTODO 20: SORTEO ANTERIOR AL REVÉS ============
def metodo_sorteo_al_reves(df, sorteo_elegido=None, num_base=None):
    """
    Toma el primer premio (n1) del sorteo elegido y lo invierte dígito por dígito.
    Devuelve: el número invertido completo y su cabeza invertida.
    NO devuelve el original.
    """
    if sorteo_elegido is None:
        return []

    try:
        n1 = str(sorteo_elegido["n1"]).zfill(4)
    except Exception:
        return []

    invertido = n1[::-1]
    cabeza_inv = invertido[-2:]

    return _limitar([invertido, cabeza_inv])