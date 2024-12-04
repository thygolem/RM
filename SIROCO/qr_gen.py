import qrcode
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import emoji
import os
import re

# Configuración de márgenes y espaciado
MARGEN_POR_LINEA = 5  # Ajusta este valor para cambiar el margen extra por cada línea
TAMANO_TEXTO_GENERO = 20  # Ajusta este valor para cambiar el tamaño del texto de género/disciplina
CARACTERES_POR_LINEA = 80  # Nueva constante para controlar el número de caracteres por línea

def eliminar_emojis(texto):
    # Usar una expresión regular para eliminar emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticonos
        "\U0001F300-\U0001F5FF"  # Símbolos y pictogramas
        "\U0001F680-\U0001F6FF"  # Transporte y símbolos de mapas
        "\U0001F1E0-\U0001F1FF"  # Banderas (iOS)
        "\U00002500-\U00002BEF"  # CJK símbolos
        "\U00002702-\U000027B0"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # Dingbats
        "\u3030"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', texto)

def crear_qr(url):
    if pd.isna(url) or url == '':
        qr = qrcode.QRCode(box_size=10)
        qr.add_data("No disponible")
        return qr.make_image()
    
    # Eliminar espacios al inicio y final
    url = url.strip()
    
    # Si no es una URL, crear enlace de búsqueda de Google
    if not url.startswith(('http://', 'https://', '@http')):
        # Si empieza con @, quitar el @ para la búsqueda
        if url.startswith('@'):
            url = url[1:]
        # Crear URL de búsqueda de Google
        url = f"https://www.google.com/search?q={url}"
    
    qr = qrcode.QRCode(box_size=10)
    qr.add_data(url)
    return qr.make_image()

def procesar_entrada(row):
    ancho_total = 800
    alto_total = 400
    imagen_final = Image.new('RGB', (ancho_total, alto_total), 'white')
    draw = ImageDraw.Draw(imagen_final)
    
    try:
        # Fuente para el nombre artístico
        fuente = ImageFont.truetype("Arial.ttf", 30)
        # Fuentes para género/disciplina (más pequeñas)
        fuente_genero = ImageFont.truetype("Arial.ttf", TAMANO_TEXTO_GENERO)
        fuente_genero_negrita = ImageFont.truetype("Arial Bold.ttf", TAMANO_TEXTO_GENERO)
    except:
        fuente = ImageFont.load_default()
        fuente_genero = fuente
        fuente_genero_negrita = fuente
    
    # Escribir el nombre artístico
    nombre = f"{row['NOMBRE ARTÍSTICO']}"
    draw.text((20, 20), nombre, fill='black', font=fuente)
    
    # Eliminar emojis del texto de género/disciplina
    texto = eliminar_emojis(row['#género #disciplina'])
    
    # Insertar saltos de línea cada CARACTERES_POR_LINEA caracteres (máximo 2 líneas)
    lineas = []
    while len(texto) > CARACTERES_POR_LINEA and len(lineas) < 1:
        corte = texto.rfind(' ', 0, CARACTERES_POR_LINEA)
        if corte == -1:
            corte = CARACTERES_POR_LINEA
        lineas.append(texto[:corte])
        texto = texto[corte:].strip()
    
    # Truncar la última línea a CARACTERES_POR_LINEA caracteres si es necesario
    if len(texto) > CARACTERES_POR_LINEA:
        corte = texto.rfind(' ', 0, CARACTERES_POR_LINEA)
        if corte == -1:
            texto = texto[:CARACTERES_POR_LINEA]
        else:
            texto = texto[:corte]
    lineas.append(texto)
    
    x_pos = 20
    y_pos = 60
    
    for linea in lineas:
        palabras = linea.split()
        for palabra in palabras:
            if palabra.startswith('#'):
                # Palabra con hashtag en azul y negrita
                draw.text((x_pos, y_pos), palabra, fill='blue', font=fuente_genero_negrita)
                bbox = draw.textbbox((x_pos, y_pos), palabra, font=fuente_genero_negrita)
            else:
                # Palabra normal en negro
                draw.text((x_pos, y_pos), palabra, fill='black', font=fuente_genero)
                bbox = draw.textbbox((x_pos, y_pos), palabra, font=fuente_genero)
            
            x_pos += bbox[2] - bbox[0] + 10  # Espacio entre palabras
        y_pos += 30  # Espacio entre líneas (reducido para texto más pequeño)
        x_pos = 20  # Reiniciar posición x para la nueva línea
    
    # Ajustar la posición de los QR según el número de líneas
    margen_extra = len(lineas) * MARGEN_POR_LINEA
    
    # Generar y pegar los QR
    qr1 = crear_qr(row['LINK_WEB_1'])
    tamano_qr = 300
    qr1 = qr1.resize((tamano_qr, tamano_qr))
    
    # Si LINK_WEB_2 está vacío, centrar qr1
    if pd.isna(row['LINK_WEB_2']) or row['LINK_WEB_2'].strip() == '':
        imagen_final.paste(qr1, (250, 100 + margen_extra))
    else:
        # Si hay dos QRs, mantener el layout original
        qr2 = crear_qr(row['LINK_WEB_2'])
        qr2 = qr2.resize((tamano_qr, tamano_qr))
        imagen_final.paste(qr1, (50, 100 + margen_extra))
        imagen_final.paste(qr2, (450, 100 + margen_extra))
    
    return imagen_final

# Configuración de rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, 'data', 'gen.csv')
images_dir = os.path.join(current_dir, 'data', 'images')

# Crear directorio de imágenes
os.makedirs(images_dir, exist_ok=True)

# Leer CSV y procesar
df = pd.read_csv(csv_path)
print("Nombres de las columnas:")
print(df.columns.tolist())

for index, row in df.iterrows():
    imagen = procesar_entrada(row)
    nombre_archivo = "".join(x for x in row['NOMBRE ARTÍSTICO'] if x.isalnum() or x in (' ', '-', '_'))
    ruta_imagen = os.path.join(images_dir, f"qr_layout_{nombre_archivo}.png")
    imagen.save(ruta_imagen)
    print(f"Imagen guardada: {ruta_imagen}")