from fastapi import FastAPI, Request, UploadFile, File, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List
import os
import shutil
import logging
import json
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Crear directorios si no existen
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Agregar esta ruta para servir las imágenes subidas
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Variable para almacenar la última vez que se guardó cada archivo
ultimos_guardados = {}

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/process-files")
async def process_files(files: List[UploadFile] = File(...)):
    try:
        saved_files = []
        
        for file in files:
            # Crear la ruta completa donde se guardará el archivo
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            logger.debug(f"Guardando archivo en: {file_path}")
            
            # Guardar el archivo
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_files.append({
                "filename": file.filename,
                "path": file_path
            })
        
        return {
            "success": True,
            "message": f"Guardados {len(saved_files)} archivos",
            "files": saved_files
        }
    except Exception as e:
        logger.error(f"Error guardando archivos: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Crear la ruta completa donde se guardará el archivo
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        logger.debug(f"Guardando imagen en: {file_path}")
        
        # Guardar el archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Devolver la URL de la imagen guardada
        return {
            "success": True,
            "filename": file.filename,
            "url": f"/uploads/{file.filename}"
        }
    except Exception as e:
        logger.error(f"Error guardando imagen: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.post("/guardar-estado")
async def guardar_estado(request: Request, background_tasks: BackgroundTasks):
    try:
        # Obtener el estado del cuerpo de la petición
        estado = await request.json()
        
        # Generar nombre de archivo único para el estado
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        archivo_estado = f"estados/estado_{timestamp}.json"
        
        # Verificar si el contenido ha cambiado
        if archivo_estado in ultimos_guardados:
            with open(archivo_estado, 'r') as f:
                estado_anterior = json.load(f)
                if estado == estado_anterior:
                    return {"success": True, "message": "No hay cambios que guardar"}

        # Guardar el nuevo estado en segundo plano
        background_tasks.add_task(guardar_estado_archivo, archivo_estado, estado)
        ultimos_guardados[archivo_estado] = time.time()
        
        return {
            "success": True,
            "message": "Estado guardado correctamente",
            "archivo": archivo_estado
        }
    except Exception as e:
        logger.error(f"Error guardando estado: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

async def guardar_estado_archivo(archivo, estado):
    try:
        os.makedirs(os.path.dirname(archivo), exist_ok=True)
        with open(archivo, 'w') as f:
            json.dump(estado, f, indent=2)
        logger.info(f"Estado guardado en {archivo}")
    except Exception as e:
        logger.error(f"Error guardando archivo de estado: {str(e)}")
