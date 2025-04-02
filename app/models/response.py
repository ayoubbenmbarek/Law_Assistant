from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date

class LegalResponse(BaseModel):
    """Modèle de réponse structurée pour les questions juridiques"""
    
    # Introduction générale à la question
    introduction: str = Field(..., 
                            description="Introduction et résumé de la question juridique")
    
    # Cadre légal applicable
    legal_framework: str = Field(..., 
                               description="Cadre légal, lois et règlements applicables")
    
    # Application concrète au cas exposé
    application: str = Field(..., 
                           description="Application de la loi au cas spécifique")
    
    # Exceptions et cas particuliers
    exceptions: Optional[str] = Field(None, 
                                    description="Exceptions et cas particuliers applicables")
    
    # Recommandations et actions à entreprendre
    recommendations: List[str] = Field(..., 
                                     description="Recommandations et prochaines étapes suggérées")
    
    # Sources et références légales
    sources: List[str] = Field(..., 
                             description="Références précises des articles et textes légaux")
    
    # Date de mise à jour des informations
    date_updated: str = Field(..., 
                            description="Date de dernière mise à jour des informations")
    
    # Avertissement légal
    disclaimer: str = Field("Cette réponse est fournie à titre informatif uniquement et ne constitue pas un avis juridique. Consultez un professionnel pour une analyse personnalisée.", 
                          description="Avertissement légal")
    
    class Config:
        schema_extra = {
            "example": {
                "introduction": "Votre question porte sur le licenciement économique, une procédure encadrée par le Code du travail.",
                "legal_framework": "Le licenciement économique est régi par les articles L. 1233-1 et suivants du Code du travail. Il doit être justifié par des difficultés économiques, des mutations technologiques, une réorganisation nécessaire à la sauvegarde de la compétitivité ou la cessation d'activité de l'entreprise.",
                "application": "Pour une entreprise de 25 salariés, vous devez respecter une procédure spécifique incluant la consultation des représentants du personnel, l'information de la DIRECCTE, et proposer un contrat de sécurisation professionnelle (CSP) à chaque salarié concerné.",
                "exceptions": "Des règles particulières s'appliquent si l'entreprise appartient à un groupe ou si elle est en procédure collective.",
                "recommendations": [
                    "Vérifier que le motif économique est établi et documenté",
                    "Établir des critères d'ordre des licenciements",
                    "Préparer un plan de reclassement interne",
                    "Consulter le CSE"
                ],
                "sources": [
                    "Code du travail, articles L. 1233-1 à L. 1233-91",
                    "Loi n° 2016-1088 du 8 août 2016 relative au travail"
                ],
                "date_updated": "2023-09-15",
                "disclaimer": "Cette réponse est fournie à titre informatif uniquement et ne constitue pas un avis juridique. Consultez un avocat en droit du travail pour une analyse personnalisée."
            }
        } 