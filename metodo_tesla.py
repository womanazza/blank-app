"""
Método Tesla aplicado a la Quiniela.
Corrección: las jugadas se generan combinando raíz + espejo + dígitos del base,
sin incluir el número base en sí (evita el bug donde el 4-cifras era igual al base).
"""

ESPEJOS = {
    "0": "9", "1": "6", "2": "7", "3": "8", "4": "5",
    "5": "4", "6": "1", "7": "2", "8": "3", "9": "0",
}

TRINIDAD = ["3", "6", "9"]


def reducir_a_raiz(numero):
    """Suma dígitos hasta un solo dígito. Ej: 4728 -> 21 -> 3"""
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
    """Aplica la reducción y calcula raíz + espejo."""
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
    """
    Genera las jugadas combinando la raíz, el espejo y los dígitos del número base.
    NUNCA incluye el número base en sí.
    """
    raiz = analisis["raiz"]
    esp = analisis["espejo"]
    base = analisis["numero_base"]
    digitos_base = [d for d in base]

    ambos = set()
    ternos = set()
    cuatro = set()

    # ============ AMBOS (2 cifras) ============
    # Combinaciones de raíz + espejo y raíz/espejo + cada dígito del base
    ambos.add(f"{raiz}{esp}")
    ambos.add(f"{esp}{raiz}")
    for d in digitos_base:
        ambos.add(f"{raiz}{d}")
        ambos.add(f"{d}{raiz}")
        ambos.add(f"{esp}{d}")
        ambos.add(f"{d}{esp}")

    # ============ TERNOS (3 cifras) ============
    # raíz + espejo + dígito, en distintas posiciones
    for d in digitos_base:
        ternos.add(f"{raiz}{esp}{d}")
        ternos.add(f"{raiz}{d}{esp}")
        ternos.add(f"{esp}{raiz}{d}")
        ternos.add(f"{d}{raiz}{esp}")
        ternos.add(f"{d}{esp}{raiz}")
        ternos.add(f"{esp}{d}{raiz}")
    # Si está en trinidad, agregar combinaciones 3-6-9
    if analisis["en_trinidad"]:
        for a in TRINIDAD:
            for b in TRINIDAD:
                for c in TRINIDAD:
                    ternos.add(f"{a}{b}{c}")

    # ============ CUATRO CIFRAS ============
    # Mezclas de los 4 dígitos del base con raíz y espejo intercalados
    # Ejemplo: base=4904, raiz=8, espejo=3
    # -> 8390, 8304, 8430, 3948, 3490, ...
    for i in range(len(digitos_base)):
        # reemplazar la posición i por la raíz
        nueva = digitos_base.copy()
        nueva[i] = raiz
        cuatro.add("".join(nueva))

        # reemplazar la posición i por el espejo
        nueva = digitos_base.copy()
        nueva[i] = esp
        cuatro.add("".join(nueva))

    # Además, algunas combinaciones extra con raíz y espejo al inicio
    cuatro.add(f"{raiz}{esp}{digitos_base[0]}{digitos_base[1]}")
    cuatro.add(f"{esp}{raiz}{digitos_base[0]}{digitos_base[1]}")
    cuatro.add(f"{digitos_base[2]}{digitos_base[3]}{raiz}{esp}")
    cuatro.add(f"{digitos_base[2]}{digitos_base[3]}{esp}{raiz}")

    # Limpieza: longitudes correctas y sin el número base
    ambos = sorted({j for j in ambos if len(j) == 2})
    ternos = sorted({j for j in ternos if len(j) == 3})
    cuatro = sorted({j for j in cuatro if len(j) == 4 and j != base})

    return {
        "ambos": ambos,
        "ternos": ternos,
        "cuatro_cifras": cuatro,
    }


def _chequear_numero(num_real, predichos_ambos, predichos_ternos, predichos_4):
    term2 = num_real[-2:]
    term3 = num_real[-3:]
    return (num_real in predichos_4 or term2 in predichos_ambos
            or term3 in predichos_ternos)


def medir_metodo_tesla(df):
    """
    Recorre el historial par por par (sorteo anterior -> siguiente) aplicando Tesla.
    Compara contra el sorteo siguiente.
    Cuenta un acierto por cada número acertado.
    """
    import pandas as pd

    df = df.copy()
    df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.sort_values("fecha_dt").reset_index(drop=True)

    aciertos_cabeza = []
    aciertos_10 = []
    aciertos_20 = []

    total_cabeza = 0
    total_10 = 0
    total_20 = 0

    for i in range(len(df) - 1):
        fila_ant = df.iloc[i]
        fila_sig = df.iloc[i + 1]

        num_base = str(fila_ant["n1"]).zfill(4)
        analisis = analizar_numero(num_base)
        jugadas = generar_jugadas(analisis)

        predichos_ambos = set(jugadas["ambos"])
        predichos_ternos = set(jugadas["ternos"])
        predichos_4 = set(jugadas["cuatro_cifras"])

        num_sig = str(fila_sig["n1"]).zfill(4)
        cabeza_sig = num_sig[-2:]
        fecha_sig = fila_sig["fecha"]
        turno_sig = fila_sig["turno"]

        # Aciertos a la cabeza
        total_cabeza += 1
        if _chequear_numero(num_sig, predichos_ambos, predichos_ternos, predichos_4):
            aciertos_cabeza.append({
                "numero": cabeza_sig, "fecha": fecha_sig, "turno": turno_sig
            })

        # Primeros 10
        for j in range(1, 11):
            num_real = str(fila_sig[f"n{j}"]).zfill(4)
            total_10 += 1
            if _chequear_numero(num_real, predichos_ambos, predichos_ternos, predichos_4):
                aciertos_10.append({
                    "numero": num_real, "fecha": fecha_sig, "turno": turno_sig
                })

        # Los 20
        for j in range(1, 21):
            num_real = str(fila_sig[f"n{j}"]).zfill(4)
            total_20 += 1
            if _chequear_numero(num_real, predichos_ambos, predichos_ternos, predichos_4):
                aciertos_20.append({
                    "numero": num_real, "fecha": fecha_sig, "turno": turno_sig
                })

    return {
        "total": len(df) - 1 if len(df) > 1 else 0,
        "total_cabeza": total_cabeza,
        "total_10": total_10,
        "total_20": total_20,
        "aciertos_cabeza": aciertos_cabeza,
        "aciertos_10": aciertos_10,
        "aciertos_20": aciertos_20,
    }