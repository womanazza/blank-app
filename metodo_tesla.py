"""
Método Tesla aplicado a la Quiniela.
Incluye funciones de análisis, generación de jugadas y medición sobre el historial.
"""

ESPEJOS = {
    "0": "9", "1": "6", "2": "7", "3": "8", "4": "5",
    "5": "4", "6": "1", "7": "2", "8": "3", "9": "0",
}

TRINIDAD = ["3", "6", "9"]


def reducir_a_raiz(numero):
    numero = str(numero).strip()
    while len(numero) > 1:
        suma = sum(int(d) for d in numero if d.isdigit())
        numero = str(suma)
    return numero


def es_trinidad(digito):
    return str(digito) in TRINIDAD


def espejo(digito):
    return ESPEJOS.get(str(digito), str(digito))


def analizar_numero(numero_base):
    numero_str = str(numero_base).zfill(4)
    raiz = reducir_a_raiz(numero_str)
    espejo_raiz = espejo(raiz)
    en_trinidad = es_trinidad(raiz)
    return {
        "numero_base": numero_str,
        "raiz": raiz,
        "espejo": espejo_raiz,
        "en_trinidad": en_trinidad,
    }


def generar_jugadas(analisis):
    """Devuelve dict con 'ambos', 'ternos', 'cuatro_cifras'"""
    raiz = analisis["raiz"]
    esp = analisis["espejo"]
    base = analisis["numero_base"]

    ambos = set()
    ternos = set()
    cuatro = set()

    if analisis["en_trinidad"]:
        for a in TRINIDAD:
            for b in TRINIDAD:
                ambos.add(f"{a}{b}")
                for c in TRINIDAD:
                    ternos.add(f"{a}{b}{c}")
    else:
        ambos.add(f"{raiz}{esp}")
        ambos.add(f"{esp}{raiz}")

    # Terminaciones del número base
    terminaciones = [base[-2:], base[-3:], base]
    for t in terminaciones:
        if len(t) == 2:
            ambos.add(t)
        elif len(t) == 3:
            ternos.add(t)
        elif len(t) == 4:
            cuatro.add(t)

    ambos.add(f"{raiz}{esp}")
    ambos.add(f"{esp}{raiz}")
    ambos.add(f"{raiz}0")
    ambos.add(f"0{raiz}")

    return {
        "ambos": sorted(ambos),
        "ternos": sorted(ternos),
        "cuatro_cifras": sorted(cuatro),
    }


def medir_metodo_tesla(df):
    """
    Recorre el historial par por par (sorteo anterior -> siguiente) aplicando Tesla.
    Devuelve estadísticas de aciertos.
    """
    import pandas as pd
    from datetime import datetime

    df = df.copy()
    df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.sort_values("fecha_dt").reset_index(drop=True)

    columnas = [f"n{i}" for i in range(1, 21)]

    aciertos_cabeza = []   # Tuplas (num_predicho, fecha, turno)
    aciertos_10 = []
    aciertos_20 = []

    for i in range(len(df) - 1):
        fila_ant = df.iloc[i]
        fila_sig = df.iloc[i + 1]

        num_base = str(fila_ant["n1"]).zfill(4)
        analisis = analizar_numero(num_base)
        jugadas = generar_jugadas(analisis)

        # Números reales del sorteo siguiente
        num_sig = str(fila_sig["n1"]).zfill(4)
        cabeza_sig = num_sig[-2:]
        primeros_10 = [str(fila_sig[f"n{j}"]).zfill(4) for j in range(1, 11)]
        todos_20 = [str(fila_sig[f"n{j}"]).zfill(4) for j in range(1, 21)]

        fecha_sig = fila_sig["fecha"]
        turno_sig = fila_sig["turno"]

        # Aciertos a la cabeza
        predichos_ambos = set(jugadas["ambos"])
        predichos_ternos = set(jugadas["ternos"])
        predichos_4 = set(jugadas["cuatro_cifras"])

        # Cabeza (últimos 2 dígitos del n1)
        if cabeza_sig in predichos_ambos or num_sig in predichos_4:
            aciertos_cabeza.append({
                "numero": cabeza_sig,
                "fecha": fecha_sig,
                "turno": turno_sig,
            })

        # Aciertos en los primeros 10
        for num_real in primeros_10:
            term2 = num_real[-2:]
            if (num_real in predichos_4 or term2 in predichos_ambos
                    or num_real[-3:] in predichos_ternos):
                aciertos_10.append({
                    "numero": num_real,
                    "fecha": fecha_sig,
                    "turno": turno_sig,
                })
                break

        # Aciertos en los 20
        for num_real in todos_20:
            term2 = num_real[-2:]
            if (num_real in predichos_4 or term2 in predichos_ambos
                    or num_real[-3:] in predichos_ternos):
                aciertos_20.append({
                    "numero": num_real,
                    "fecha": fecha_sig,
                    "turno": turno_sig,
                })
                break

    total = len(df) - 1 if len(df) > 1 else 0

    return {
        "total": total,
        "aciertos_cabeza": aciertos_cabeza,
        "aciertos_10": aciertos_10,
        "aciertos_20": aciertos_20,
    }