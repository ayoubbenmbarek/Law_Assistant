from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class LegalDomain(str, Enum):
    """Domaines juridiques possibles pour une question"""
    FISCAL = "fiscal"
    TRAVAIL = "travail"
    AFFAIRES = "affaires"
    FAMILLE = "famille"
    IMMOBILIER = "immobilier"
    CONSOMMATION = "consommation"
    PENAL = "penal"
    AUTRE = "autre"

class QueryRequest(BaseModel):
    """Modèle pour les requêtes d'assistance juridique"""
    query: str = Field(..., min_length=10, max_length=2000, 
                      description="Question juridique détaillée")
    domain: Optional[LegalDomain] = Field(None, 
                                        description="Domaine juridique concerné")
    context: Optional[str] = Field(None, max_length=5000, 
                                 description="Contexte supplémentaire pour la question")
    documents: Optional[List[str]] = Field(None, 
                                        description="Références à des documents à consulter")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Quelles sont les obligations d'un employeur lors d'un licenciement économique ?",
                "domain": "travail",
                "context": "Entreprise de 25 salariés dans le secteur de la restauration",
                "documents": None
            }
        } 