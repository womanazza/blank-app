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
    "Sábado 90s": "Si hoy es sábado, la decena de los 90 (90-99) recibe +1 punto de score.",
    "Lunes repite sábado": "Si hoy es lunes, la cabeza del sábado anterior (y su invertido) reciben +1 punto.",
    "Martes dobles": "Si hoy es martes, los números dobles (11, 22, 33...99) reciben +1 punto.",
    "Decena 70 se repite": "Si el sorteo base tiene cabeza en la decena 70, esa decena recibe +1 punto.",
    "Nocturna repite matutina": "Si hay sorteo matutino hoy, su cabeza (derecho e invertido) recibe +1 punto en la nocturna.",
    "Viernes 35/19": "Si hoy es viernes, los números 35, 19 y sus invertidos reciben +1 punto.",
    "Secreto del segundo": "Toma el 2° premio del sorteo elegido. Sus variantes (derecho y revés) se juegan en los próximos 3 sorteos.",
    "Atrasados": "Números que hace 30 o más sorteos que no salen a la cabeza. Se consideran 'fríos' y con alta chance de aparecer.",
    "Decena + cifra": "Busca la decena y la cifra (unidad) que más salieron a la cabeza en el historial, y arma combinaciones con esos dígitos.",
    "Ambos repetidos": "Si en el sorteo elegido algún ambo (2 últimas cifras) se repite 2 o más veces, se espera que vuelva a salir a la cabeza.",
    "Animales": "Si el ambo de la cabeza del sorteo elegido corresponde a un animal en la tabla de sueños (Gato, Perro, Caballo, etc.), se espera que vengan los demás animales. Devuelve los 10 números de animales.",
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
# ============ MÉTODOS DE BONUS (REGLA DE SCORE) ============
# Cada uno devuelve un diccionario:
# { "aplica": True/False, "motivo": "texto", "numeros": [...lista de números que reciben +1...] }

def bonus_sabados_90(df, sorteo_elegido=None, fecha_hoy=None):
    """Sábados: +1 a los números de la decena 90 que ya salieron en otros métodos."""
    if fecha_hoy is None:
        fecha_hoy = datetime.now()

    aplica = fecha_hoy.weekday() == 5  # 5 = sábado
    numeros = [f"{d}" for d in range(90, 100)]  # 90, 91, ..., 99

    return {
        "nombre": "Sábado 90s",
        "aplica": aplica,
        "motivo": "Hoy es sábado: la decena 90 tiene +1 punto.",
        "numeros": numeros,
    }


def bonus_lunes_repite_sabado(df, sorteo_elegido=None, fecha_hoy=None):
    """Lunes: +1 a la cabeza del sábado anterior (derecho e invertido)."""
    if fecha_hoy is None:
        fecha_hoy = datetime.now()

    aplica = fecha_hoy.weekday() == 0  # 0 = lunes
    numeros = []

    if aplica and df is not None and not df.empty:
        df_temp = df.copy()
        df_temp["fecha_dt"] = pd.to_datetime(df_temp["fecha"], format="%d/%m/%Y", errors="coerce")
        # Buscar el sábado anterior más cercano
        df_sabados = df_temp[df_temp["fecha_dt"].dt.weekday == 5]
        df_sabados = df_sabados[df_sabados["fecha_dt"] < fecha_hoy]
        if not df_sabados.empty:
            ultimo_sabado = df_sabados.sort_values("fecha_dt", ascending=False).iloc[0]
            cabeza = str(ultimo_sabado["n1"]).zfill(4)[-2:]
            numeros = [cabeza, cabeza[::-1]]

    return {
        "nombre": "Lunes repite sábado",
        "aplica": aplica,
        "motivo": "Hoy es lunes: la cabeza del sábado anterior recibe +1.",
        "numeros": numeros,
    }


def bonus_martes_dobles(df, sorteo_elegido=None, fecha_hoy=None):
    """Martes: +1 a los números dobles (11, 22, 33, ..., 99)."""
    if fecha_hoy is None:
        fecha_hoy = datetime.now()

    aplica = fecha_hoy.weekday() == 1  # 1 = martes
    numeros = [f"{d}{d}" for d in range(1, 10)]  # 11, 22, ..., 99

    return {
        "nombre": "Martes dobles",
        "aplica": aplica,
        "motivo": "Hoy es martes: los números dobles reciben +1.",
        "numeros": numeros,
    }


def bonus_decena_70(df, sorteo_elegido=None, fecha_hoy=None):
    """Si el primer premio del sorteo base está en la decena 70, +1 a esa decena."""
    if fecha_hoy is None:
        fecha_hoy = datetime.now()

    numeros = []
    aplica = False
    motivo = "La decena 70 no salió como cabeza en el sorteo base."

    if sorteo_elegido is not None:
        try:
            cabeza_base = str(sorteo_elegido["n1"]).zfill(4)[-2:]
            if cabeza_base.startswith("7"):
                aplica = True
                numeros = [f"{d}" for d in range(70, 80)]
                motivo = f"La cabeza del sorteo base ({cabeza_base}) está en la decena 70: recibe +1."
        except Exception:
            pass

    return {
        "nombre": "Decena 70 se repite",
        "aplica": aplica,
        "motivo": motivo,
        "numeros": numeros,
    }


def bonus_nocturna_repite_matutina(df, sorteo_elegido=None, fecha_hoy=None):
    """Nocturna repite la cabeza de la matutina (derecho e invertido)."""
    if fecha_hoy is None:
        fecha_hoy = datetime.now()

    numeros = []
    aplica = False
    motivo = "No hay sorteo matutino de hoy para comparar."

    if df is not None and not df.empty:
        hoy_str = fecha_hoy.strftime("%d/%m/%Y")
        df_hoy = df[df["fecha"] == hoy_str]
        # Buscar sorteo de la mañana (Vespertina o Tarde, según tu criterio)
        df_mat = df_hoy[df_hoy["turno"].str.contains("Vesper", case=False, na=False)]
        if not df_mat.empty:
            cabeza = str(df_mat.iloc[0]["n1"]).zfill(4)[-2:]
            numeros = [cabeza, cabeza[::-1]]
            aplica = True
            motivo = f"Cabeza de la matutina ({cabeza}): +1 al derecho y al revés."

    return {
        "nombre": "Nocturna repite matutina",
        "aplica": aplica,
        "motivo": motivo,
        "numeros": numeros,
    }


def bonus_viernes_35_19(df, sorteo_elegido=None, fecha_hoy=None):
    """Viernes: +1 a los números 35, 19 y sus invertidos 53, 91."""
    if fecha_hoy is None:
        fecha_hoy = datetime.now()

    aplica = fecha_hoy.weekday() == 4  # 4 = viernes
    numeros = ["35", "53", "19", "91"]

    return {
        "nombre": "Viernes 35/19",
        "aplica": aplica,
        "motivo": "Hoy es viernes: 35, 19 y sus invertidos reciben +1.",
        "numeros": numeros,
    }


# Lista consolidada de todos los bonus
BONUS_METODOS = [
    bonus_sabados_90,
    bonus_lunes_repite_sabado,
    bonus_martes_dobles,
    bonus_decena_70,
    bonus_nocturna_repite_matutina,
    bonus_viernes_35_19,
]# ============ MÉTODO 2: SECRETO DEL SEGUNDO ============
def metodo_secreto_segundo(df, sorteo_elegido=None, num_base=None):
    """
    Toma el 2° premio del sorteo elegido y devuelve sus variantes (derecho y revés).
    Se debe jugar en los próximos 3 sorteos.
    """
    if sorteo_elegido is None:
        return []
    try:
        n2 = str(sorteo_elegido["n2"]).zfill(4)
    except Exception:
        return []

    cabeza = n2[-2:]
    invertido = n2[::-1]
    cabeza_inv = cabeza[::-1]

    return _limitar([n2, invertido, cabeza, cabeza_inv])


# ============ MÉTODO 7: ATRASADOS ============
def metodo_atrasados(df, sorteo_elegido=None, num_base=None):
    """
    Números (a la cabeza, 2 cifras) que hace 30+ sorteos que no salen.
    """
    df = _preparar_df(df)
    if df.empty:
        return []

    cabezas = [str(int(n)).zfill(4)[-2:] for n in df["n1"].dropna()]

    # Encontrar la última aparición de cada número
    ultima_aparicion = {}
    for i, cab in enumerate(cabezas):
        if cab not in ultima_aparicion:
            ultima_aparicion[cab] = i

    # Calcular atraso (cantidad de sorteos sin salir)
    atrasos = []
    for num in [f"{i:02d}" for i in range(100)]:
        if num in ultima_aparicion:
            atraso = ultima_aparicion[num]
        else:
            atraso = len(cabezas)  # Nunca salió
        if atraso >= 30:
            atrasos.append((num, atraso))

    atrasos.sort(key=lambda x: x[1], reverse=True)
    return _limitar([num for num, _ in atrasos])


# ============ MÉTODO 9: DECENA + CIFRA ============
def metodo_decena_cifra(df, sorteo_elegido=None, num_base=None):
    """
    Busca la decena y la cifra (unidad) que más salieron a la cabeza.
    Arma combinaciones con esos 2 dígitos.
    """
    df = _preparar_df(df)
    if df.empty:
        return []

    cabezas = [str(int(n)).zfill(4)[-2:] for n in df["n1"].dropna()]

    contador_decenas = Counter()
    contador_cifras = Counter()

    for cab in cabezas:
        if len(cab) == 2:
            contador_decenas[cab[0]] += 1
            contador_cifras[cab[1]] += 1

    if not contador_decenas or not contador_cifras:
        return []

    decena_top = contador_decenas.most_common(3)
    cifra_top = contador_cifras.most_common(3)

    resultados = []
    for d, _ in decena_top:
        for c, _ in cifra_top:
            resultados.append(f"{d}{c}")
            resultados.append(f"{c}{d}")

    return _limitar(resultados)


# ============ MÉTODO 11: AMBOS REPETIDOS ============
def metodo_ambos_repetidos(df, sorteo_elegido=None, num_base=None):
    """
    Busca en el sorteo elegido si algún ambo (2 últimas cifras) se repite 2+ veces.
    """
    if sorteo_elegido is None:
        return []

    ambos = []
    for j in range(1, 21):
        num = str(sorteo_elegido.get(f"n{j}", "")).zfill(4)
        if len(num) == 4:
            ambos.append(num[-2:])

    contador = Counter(ambos)
    repetidos = [ambo for ambo, cant in contador.items() if cant >= 2]

    return _limitar(repetidos)
# ============ MÉTODO 18: ANIMALES ============
# Lista de números de la tabla de sueños que representan animales
ANIMALES = {
    "05": "El Gato",
    "06": "El Perro",
    "19": "El Pescado",
    "24": "El Caballo",
    "25": "La Gallina",
    "35": "El Pajarito",
    "54": "La Vaca",
    "66": "Lombrices",
    "67": "La Víbora",
    "89": "La Rata",
}


def metodo_animales(df, sorteo_elegido=None, num_base=None):
    """
    Si el ambo de la cabeza del sorteo elegido corresponde a un animal
    (según la tabla de sueños), devuelve los 10 números de animales.
    """
    if sorteo_elegido is None:
        return []

    try:
        n1 = str(sorteo_elegido["n1"]).zfill(4)
        ambo = n1[-2:]
    except Exception:
        return []

    if ambo in ANIMALES:
        # Devuelve los 10 números de animales
        return _limitar(list(ANIMALES.keys()))

    return []