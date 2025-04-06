from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from loguru import logger
import os
import tempfile
from pydantic import BaseModel
from typing import List, Optional, Dict
import weasyprint
import jinja2
import uuid
from datetime import datetime

from app.models.user import get_current_active_user, User

router = APIRouter()

# Configurer le moteur de templates Jinja2
template_loader = jinja2.FileSystemLoader(searchpath="./app/templates")
template_env = jinja2.Environment(loader=template_loader)

class Recommendation(BaseModel):
    """Recommandation dans une réponse juridique"""
    content: str

class Source(BaseModel):
    """Source dans une réponse juridique"""
    id: str
    title: str
    type: str
    content: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    
class PDFRequest(BaseModel):
    """Requête pour générer un PDF à partir d'une réponse juridique"""
    response: dict

def cleanup_temp_file(file_path: str):
    """Nettoyer les fichiers temporaires après un délai"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du fichier temporaire {file_path}: {e}")

@router.post("/generate-pdf", response_class=FileResponse)
async def generate_pdf(
    request: PDFRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Génère un PDF à partir d'une réponse juridique
    """
    try:
        # Créer un répertoire temporaire pour les PDF s'il n'existe pas
        pdf_dir = os.path.join(tempfile.gettempdir(), "legal_assistant_pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Générer un nom de fichier unique
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"reponse_juridique_{timestamp}_{uuid.uuid4().hex[:8]}.pdf"
        output_path = os.path.join(pdf_dir, filename)
        
        # Récupérer les données de la réponse
        response_data = request.response
        
        # Préparer le contexte pour le template
        context = {
            "introduction": response_data.get("introduction", ""),
            "legal_framework": response_data.get("legal_framework", ""),
            "application": response_data.get("application", ""),
            "exceptions": response_data.get("exceptions", ""),
            "recommendations": response_data.get("recommendations", []),
            "sources": response_data.get("sources", []),
            "disclaimer": response_data.get("disclaimer", ""),
            "date_updated": response_data.get("date_updated", datetime.now().isoformat()),
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        
        # Charger et rendre le template HTML
        template = template_env.get_template("pdf_template.html")
        html_content = template.render(**context)
        
        # Générer le PDF
        pdf = weasyprint.HTML(string=html_content).write_pdf()
        
        # Écrire le PDF dans un fichier temporaire
        with open(output_path, "wb") as f:
            f.write(pdf)
        
        # Définir une tâche en arrière-plan pour supprimer le fichier après 5 minutes
        background_tasks.add_task(cleanup_temp_file, output_path)
        
        # Retourner le fichier
        return FileResponse(
            path=output_path,
            filename=filename,
            media_type="application/pdf",
            background=background_tasks
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du PDF: {str(e)}"
        ) 