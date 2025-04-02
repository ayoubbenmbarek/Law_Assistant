from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import date

class SourceType(str, Enum):
    """Types de sources juridiques"""
    # Types de base
    LOI = "loi"
    JURISPRUDENCE = "jurisprudence"
    DOCTRINE = "doctrine"
    REGLEMENTATION = "reglementation"
    CIRCULAIRE = "circulaire"
    
    # Types européens
    REGULATION_EU = "regulation_eu"
    DIRECTIVE_EU = "directive_eu"
    
    # Types jurisprudentiels spécifiques
    JURISPRUDENCE_ADMINISTRATIVE = "jurisprudence_administrative"
    JURISPRUDENCE_JUDICIAIRE = "jurisprudence_judiciaire"
    DECISION_CONSTITUTIONNELLE = "decision_constitutionnelle"
    
    # Types fiscaux et financiers
    FISCAL = "fiscal"
    
    # Types liés à la protection des données
    RGPD = "rgpd"
    
    # Types liés au logement
    JURISPRUDENCE_LOGEMENT = "jurisprudence_logement"
    
    # Autres
    AUTRE = "autre"

class SourceOrigin(str, Enum):
    """Origine de la source juridique"""
    LEGIFRANCE = "legifrance"
    EURLEX = "eurlex"
    CONSEIL_CONSTITUTIONNEL = "conseil_constitutionnel"
    CONSEIL_ETAT = "conseil_etat"
    COUR_CASSATION = "cour_cassation"
    BOFIP = "bofip"
    CNIL = "cnil"
    ANIL = "anil"
    AUTRE = "autre"

class JurisdictionType(str, Enum):
    """Types de juridictions"""
    CONSEIL_CONSTITUTIONNEL = "conseil_constitutionnel"
    CONSEIL_ETAT = "conseil_etat"
    COUR_CASSATION = "cour_cassation"
    COUR_APPEL = "cour_appel"
    TRIBUNAL_ADMINISTRATIF = "tribunal_administratif"
    TRIBUNAL_JUDICIAIRE = "tribunal_judiciaire"
    TRIBUNAL_COMMERCE = "tribunal_commerce"
    CJUE = "cjue"  # Cour de Justice de l'Union Européenne
    CEDH = "cedh"  # Cour Européenne des Droits de l'Homme
    AUTRE = "autre"

class LegalDomain(str, Enum):
    """Domaines juridiques pour les sources"""
    FISCAL = "fiscal"
    TRAVAIL = "travail"
    AFFAIRES = "affaires"
    FAMILLE = "famille"
    IMMOBILIER = "immobilier"
    CONSOMMATION = "consommation"
    PENAL = "penal"
    ADMINISTRATIF = "administratif"
    CONSTITUTIONNEL = "constitutionnel"
    RGPD = "rgpd"
    PROPRIETE_INTELLECTUELLE = "propriete_intellectuelle"
    ENVIRONNEMENT = "environnement"
    SANTE = "sante"
    SECURITE_SOCIALE = "securite_sociale"
    EUROPEEN = "europeen"
    AUTRE = "autre"

class LegalSource(BaseModel):
    """Modèle pour les sources juridiques"""
    id: str = Field(..., description="Identifiant unique de la source")
    title: str = Field(..., description="Titre de la source")
    type: SourceType = Field(..., description="Type de source juridique")
    content: str = Field(..., description="Contenu principal de la source")
    date: str = Field(..., description="Date de publication ou d'application")
    url: Optional[str] = Field(None, description="URL vers la source officielle")
    metadata: Dict[str, Any] = Field(default_factory=dict, 
                                  description="Métadonnées additionnelles sur la source")
    origin: Optional[SourceOrigin] = Field(SourceOrigin.AUTRE, description="Origine de la source")
    domain: Optional[List[LegalDomain]] = Field(default_factory=list, 
                                             description="Domaines juridiques concernés")
    jurisdiction: Optional[JurisdictionType] = Field(None, 
                                                  description="Type de juridiction pour les jurisprudences")
    score: Optional[float] = Field(None, description="Score de pertinence (lors des recherches)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "cc-1134",
                "title": "Article 1134 du Code Civil",
                "type": "loi",
                "content": "Les conventions légalement formées tiennent lieu de loi à ceux qui les ont faites.",
                "date": "2023-01-01",
                "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006436298",
                "metadata": {
                    "code": "Code Civil",
                    "section": "Des contrats",
                    "keywords": ["contrat", "convention", "engagement"]
                },
                "origin": "legifrance",
                "domain": ["affaires"],
                "jurisdiction": None,
                "score": 0.95
            }
        }

class SearchSourceRequest(BaseModel):
    """Modèle pour une requête de recherche de sources"""
    query: str = Field(..., description="Termes de recherche")
    types: Optional[List[SourceType]] = Field(None, description="Types de sources à rechercher")
    origins: Optional[List[SourceOrigin]] = Field(None, description="Origines des sources")
    domains: Optional[List[LegalDomain]] = Field(None, description="Domaines juridiques à rechercher")
    date_start: Optional[str] = Field(None, description="Date de début (format YYYY-MM-DD)")
    date_end: Optional[str] = Field(None, description="Date de fin (format YYYY-MM-DD)")
    limit: int = Field(10, ge=1, le=100, description="Nombre maximal de résultats")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "responsabilité contractuelle",
                "types": ["loi", "jurisprudence"],
                "origins": ["legifrance", "cour_cassation"],
                "domains": ["affaires"],
                "date_start": "2020-01-01",
                "date_end": "2023-12-31",
                "limit": 20
            }
        }

class SearchSourceResponse(BaseModel):
    """Modèle pour une réponse de recherche de sources"""
    sources: List[LegalSource] = Field(..., description="Sources trouvées")
    total_count: int = Field(..., description="Nombre total de résultats trouvés")
    query_time: float = Field(..., description="Temps d'exécution de la requête en secondes")
    
    class Config:
        schema_extra = {
            "example": {
                "sources": [
                    {
                        "id": "cc-1134",
                        "title": "Article 1134 du Code Civil",
                        "type": "loi",
                        "content": "Les conventions légalement formées tiennent lieu de loi à ceux qui les ont faites.",
                        "date": "2023-01-01",
                        "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006436298",
                        "metadata": {
                            "code": "Code Civil",
                            "section": "Des contrats"
                        },
                        "origin": "legifrance",
                        "domain": ["affaires"],
                        "jurisdiction": None,
                        "score": 0.95
                    }
                ],
                "total_count": 145,
                "query_time": 0.235
            }
        } 