"""
Método de la Pirámide (Piramidación) aplicado a la Quiniela.
Suma sucesivamente los dígitos de a pares, quedándose con el último dígito
cuando la suma es >= 10, hasta llegar a la punta de la pirámide.
"""
import pandas as pd


def reducir_fila(fila):
    nueva = []
    for i in range(len(fila) - 1):
        suma = int(fila[i]) + int(fila[i + 1])
        nueva.append(str(suma % 10))
    return nueva


def construir_piramide(numero_base):
    numero_str = str(numero_base).strip()
    filas = [[d for d in numero_str]]
    while len(filas[-1]) > 1:
        filas.append(reducir_fila(filas[-1]))
    return filas


def generar_jugadas(numero_base):
    filas = construir_piramide(numero_base)
    punta = filas[-1][0]
    penultima = filas[-2] if len(filas) >= 2 else filas[-1]
    base = filas[0]

    ambos = set()
    ternos = set()
    cuatro = set()

    # Combinaciones con la punta y la penúltima
    for d in penultima:
        ambos.add(f"{punta}{d}")
        ambos.add(f"{d}{punta}")

    # Ternos
    if len(penultima) >= 3:
        ternos.add("".join(penultima[:3]))
        ternos.add("".join(penultima[-3:]))
    for i in range(len(penultima) - 1):
        ternos.add(f"{punta}{penultima[i]}{penultima[i+1]}")
        ternos.add(f"{penultima[i]}{penultima[i+1]}{punta}")

    # 4 cifras
    if len(base) >= 4:
        cuatro.add("".join(base[:4]))
        cuatro.add("".join(base[-4:]))
    if len(penultima) >= 4:
        cuatro.add("".join(penultima[:4]))

    ambos = sorted({j for j in ambos if len(j) == 2})
    ternos = sorted({j for j in ternos if len(j) == 3})
    cuatro = sorted({j for j in cuatro if len(j) == 4})

    return {
        "ambos": ambos,
        "ternos": ternos,
        "cuatro_cifras": cuatro,
        "punta": punta,
        "filas": filas,
    }


def _chequear_numero(num_real, predichos_ambos, predichos_ternos, predichos_4):
    """Devuelve True si el número real (o sus terminaciones) está en las jugadas"""
    term2 = num_real[-2:]
    term3 = num_real[-3:]
    return (num_real in predichos_4 or term2 in predichos_ambos
            or term3 in predichos_ternos)


def medir_metodo_piramide(df):
    """
    Recorre el historial día por día, aplicando la pirámide a la fecha del día.
    Compara contra los 3 sorteos de ese mismo día.
    Cuenta cada número acertado (no cada sorteo).
    """
    df = df.copy()
    df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.sort_values("fecha_dt").reset_index(drop=True)

    aciertos_cabeza = []
    aciertos_10 = []
    aciertos_20 = []

    total_cabeza = 0
    total_10 = 0
    total_20 = 0

    # Agrupar por fecha (día)
    fechas_unicas = df["fecha"].unique()

    for fecha_str in fechas_unicas:
        fecha_dt = pd.to_datetime(fecha_str, format="%d/%m/%Y", errors="coerce")
        if pd.isna(fecha_dt):
            continue

        # Número base: la fecha en formato DDMMYYYY
        num_base = fecha_dt.strftime("%d%m%Y")
        jugadas = generar_jugadas(num_base)

        predichos_ambos = set(jugadas["ambos"])
        predichos_ternos = set(jugadas["ternos"])
        predichos_4 = set(jugadas["cuatro_cifras"])

        sorteos_del_dia = df[df["fecha"] == fecha_str]

        for _, fila in sorteos_del_dia.iterrows():
            turno = fila["turno"]
            n1 = str(fila["n1"]).zfill(4)
            cabeza = n1[-2:]

            # Cabeza
            total_cabeza += 1
            if _chequear_numero(n1, predichos_ambos, predichos_ternos, predichos_4):
                aciertos_cabeza.append({
                    "numero": cabeza, "fecha": fecha_str, "turno": turno
                })

            # Primeros 10
            for j in range(1, 11):
                num_real = str(fila[f"n{j}"]).zfill(4)
                total_10 += 1
                if _chequear_numero(num_real, predichos_ambos, predichos_ternos, predichos_4):
                    aciertos_10.append({
                        "numero": num_real, "fecha": fecha_str, "turno": turno
                    })

            # Los 20
            for j in range(1, 21):
                num_real = str(fila[f"n{j}"]).zfill(4)
                total_20 += 1
                if _chequear_numero(num_real, predichos_ambos, predichos_ternos, predichos_4):
                    aciertos_20.append({
                        "numero": num_real, "fecha": fecha_str, "turno": turno
                    })

    return {
        "total_cabeza": total_cabeza,
        "total_10": total_10,
        "total_20": total_20,
        "aciertos_cabeza": aciertos_cabeza,
        "aciertos_10": aciertos_10,
        "aciertos_20": aciertos_20,
    }