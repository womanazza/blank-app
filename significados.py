"""
Tabla de Sueños y Oficios con sus números asociados (0-99).
Fuente: loteriasmundiales.com.ar
"""

SUENIOS = {
    "00": "Los Huevos", "01": "El Agua", "02": "El Niño", "03": "San Cono",
    "04": "La Cama", "05": "El Gato", "06": "El Perro", "07": "El Revólver",
    "08": "El Incendio", "09": "El Arroyo", "10": "El Cañón", "11": "El Minero",
    "12": "El Soldado", "13": "La Yeta", "14": "El Borracho", "15": "La Niña Bonita",
    "16": "El Anillo", "17": "La Desgracia", "18": "La Sangre", "19": "El Pescado",
    "20": "La Fiesta", "21": "La Mujer", "22": "El Loco", "23": "El Cocinero",
    "24": "El Caballo", "25": "La Gallina", "26": "La Misa", "27": "El Peine",
    "28": "Las Estrellas", "29": "San Pedro", "30": "Santa Rosa", "31": "La Luz",
    "32": "Dinero", "33": "Cristo", "34": "La Cabeza", "35": "El Pajarito",
    "36": "La Manteca", "37": "El Dentista", "38": "Las Piedras", "39": "La Lluvia",
    "40": "El Cura", "41": "El Cuchillo", "42": "Las Joyas", "43": "El Balcón",
    "44": "La Cárcel", "45": "El Vino", "46": "Tomates", "47": "Muerto",
    "48": "El Muerto Habla", "49": "La Carne", "50": "El Pan", "51": "El Serrucho",
    "52": "Madre", "53": "El Barco", "54": "La Vaca", "55": "Los Gallegos",
    "56": "La Caída", "57": "El Jorobado", "58": "El Ahogado", "59": "Planta",
    "60": "La Virgen", "61": "Escopeta", "62": "Inundación", "63": "Casamiento",
    "64": "Llanto", "65": "Cazador", "66": "Lombrices", "67": "Víbora",
    "68": "Los Sobrinos", "69": "Vicios", "70": "Limosnero", "71": "Excrementos",
    "72": "Sorpresa", "73": "El Rengo", "74": "El Negro", "75": "Los Besos",
    "76": "Las Llamas", "77": "Las Muletas", "78": "Prostitutas", "79": "Ladrón",
    "80": "Las Bochas", "81": "Las Flores", "82": "La Pelea", "83": "El Mal Tiempo",
    "84": "La Iglesia", "85": "La Linterna", "86": "El Humo", "87": "Los Piojos",
    "88": "El Papa", "89": "La Rata", "90": "El Miedo", "91": "La Letrina",
    "92": "El Médico", "93": "Enamorados", "94": "Cementerio", "95": "Anteojos",
    "96": "El Marido", "97": "La Mesa", "98": "La Lavandera", "99": "Los Hermanos",
}

OFICIOS = {
    "00": "Almacenero", "01": "Plomero", "02": "Maestro", "03": "Artesano",
    "04": "Herrero", "05": "Gomero", "06": "Veterinario", "07": "Policía",
    "08": "Bombero", "09": "Diseñador", "10": "Repostero", "11": "Ferretero",
    "12": "Soldado", "13": "Jubilado", "14": "Barman", "15": "Modista",
    "16": "Secretaria", "17": "Chapista", "18": "Chofer", "19": "Pescador",
    "20": "Bailarina", "21": "Ama de Casa", "22": "Psicólogo", "23": "Cocinero",
    "24": "Jockey", "25": "Feriante", "26": "Cantante", "27": "Peluquero",
    "28": "Astrólogo", "29": "Farmacéutico", "30": "Planografista", "31": "Electricista",
    "32": "Quinielero", "33": "Eclesiástico", "34": "Contador", "35": "Pintor",
    "36": "Transportista", "37": "Dentista", "38": "Vidriero", "39": "Sodero",
    "40": "Profesor", "41": "Afilador", "42": "Joyero", "43": "Ferroviario",
    "44": "Cajero", "45": "Portero", "46": "Fumigador", "47": "Fotógrafo",
    "48": "Vendedor", "49": "Carnicero", "50": "Carpintero", "51": "Doméstica",
    "52": "Marinero", "53": "Panadero", "54": "Tapicero", "55": "Músico",
    "56": "Masajista", "57": "Zapatero", "58": "Guardavidas", "59": "Jardinero",
    "60": "Telefonista", "61": "Locutor", "62": "Ingeniero", "63": "Gráfico",
    "64": "Obrero", "65": "Taxista", "66": "Agricultor", "67": "Político",
    "68": "Librero", "69": "Buscavidas", "70": "Heladero", "71": "Bancario",
    "72": "Diariero", "73": "Pedicura", "74": "Albañil", "75": "Actor",
    "76": "Periodista", "77": "Enfermera", "78": "Prostituta", "79": "Cerrajero",
    "80": "Tornero", "81": "Florista", "82": "Deportista", "83": "Cartero",
    "84": "Arquitecto", "85": "Mecánico", "86": "Parrillero", "87": "Cadete",
    "88": "Sastre", "89": "Kiosquero", "90": "Fletero", "91": "Gasista",
    "92": "Médico", "93": "Técnico", "94": "Funebrero", "95": "Oculista",
    "96": "Empleado", "97": "Mozo", "98": "Lavandero", "99": "Viajante",
}


def normalizar(texto):
    """Saca acentos, pasa a minúsculas y saca 'el ', 'la ', 'los ', 'las '."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    reemplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    for prefijo in ["el ", "la ", "los ", "las "]:
        if texto.startswith(prefijo):
            texto = texto[len(prefijo):]
    return texto


def buscar_por_numero(numero):
    """Dado un número (str o int), devuelve el sueño y el oficio."""
    num = str(numero).zfill(2)
    if len(num) > 2:
        num = num[-2:]
    return {
        "numero": num,
        "suenio": SUENIOS.get(num, "Desconocido"),
        "oficio": OFICIOS.get(num, "Desconocido"),
    }


def buscar_por_texto(texto):
    """Busca el número asociado a un sueño o un oficio."""
    objetivo = normalizar(texto)
    resultados = []

    for num, nombre in SUENIOS.items():
        if normalizar(nombre) == objetivo or objetivo in normalizar(nombre):
            resultados.append({"numero": num, "tipo": "Sueño", "nombre": nombre})

    for num, nombre in OFICIOS.items():
        if normalizar(nombre) == objetivo or objetivo in normalizar(nombre):
            resultados.append({"numero": num, "tipo": "Oficio", "nombre": nombre})

    return resultados