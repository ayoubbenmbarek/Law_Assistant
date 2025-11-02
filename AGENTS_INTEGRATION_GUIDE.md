# 🤖 Guide d'Intégration Multi-Agents

Guide complet pour intégrer le système multi-agents CrewAI dans votre assistant juridique.

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Utilisation](#utilisation)
6. [Exemples d'intégration](#exemples-dintégration)
7. [API Endpoints](#api-endpoints)
8. [Performance & Coûts](#performance--coûts)
9. [Dépannage](#dépannage)

---

## 🎯 Vue d'ensemble

Le système multi-agents améliore votre assistant juridique en orchestrant plusieurs agents IA spécialisés :

### Agents disponibles

1. **Juriste Chercheur** 🔍
   - Recherche les textes de loi, jurisprudence, doctrine
   - Expert en recherche sur Légifrance
   - Identifie les sources juridiques pertinentes

2. **Vérificateur de Citations** ✅
   - Vérifie l'exactitude des références légales
   - Contrôle la validité temporelle des textes
   - Signale les erreurs et incohérences

3. **Rédacteur Juridique** ✍️
   - Rédige des réponses claires et structurées
   - Adapte le ton (professionnel / grand public)
   - Suit un format structuré

4. **Réviseur Qualité** 🎯
   - Contrôle qualité final
   - Vérifie la conformité déontologique
   - Assure la complétude de la réponse

5. **Experts de Domaine** (optionnel) 👨‍⚖️
   - Fiscaliste, droit du travail, immobilier, etc.
   - Expertise approfondie par domaine
   - Connaît les subtilités et pièges

### Modes d'utilisation

| Mode | Agents | Temps | Usage recommandé |
|------|--------|-------|------------------|
| **Standard** | 0 (OpenAI direct) | < 5s | Questions simples |
| **Simple** | 2 agents | 10-30s | Questions courantes |
| **Full** | 4-5 agents | 30-90s | Questions complexes |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Application                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐         ┌──────────────────────┐      │
│  │   Standard   │         │  Agent-Enhanced      │      │
│  │ QueryProcessor│         │  AgentQueryProcessor │      │
│  └──────┬───────┘         └──────┬───────────────┘      │
│         │                         │                       │
│         │ OpenAI Direct           │ Multi-Agent          │
│         ▼                         ▼                       │
│  ┌──────────────┐         ┌──────────────────────┐      │
│  │   OpenAI     │         │   LegalResearchCrew  │      │
│  │   GPT-4      │         │                      │      │
│  └──────────────┘         │  ┌────────────────┐ │      │
│                            │  │ Legal Researcher│ │      │
│                            │  └────────┬───────┘ │      │
│                            │  ┌────────▼───────┐ │      │
│                            │  │Citation Verifier│ │      │
│                            │  └────────┬───────┘ │      │
│                            │  ┌────────▼───────┐ │      │
│                            │  │ Legal Writer   │ │      │
│                            │  └────────┬───────┘ │      │
│                            │  ┌────────▼───────┐ │      │
│                            │  │Quality Reviewer │ │      │
│                            │  └────────────────┘ │      │
│                            └──────────────────────┘      │
│                                     │                     │
│                                     ▼                     │
│                            ┌──────────────────────┐      │
│                            │  Ollama / OpenAI     │      │
│                            │  mistral:latest      │      │
│                            └──────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Installation

### 1. Installer les dépendances

```bash
cd /Users/ayoubmbarek/Projects/law_assistant

# Installer CrewAI et dépendances
pip install crewai langchain-openai python-dotenv

# Si vous utilisez Ollama localement
pip install ollama
```

### 2. Vérifier la structure des fichiers

```
law_assistant/
├── app/
│   ├── agents/                    # 🆕 Nouveau module
│   │   ├── __init__.py
│   │   ├── agents.py              # Définition des agents
│   │   └── legal_crew.py          # Orchestration
│   ├── api/
│   │   └── endpoints/
│   │       └── agent_query.py     # 🆕 Nouveau endpoint
│   ├── models/
│   │   ├── processor.py           # Existant
│   │   └── agent_processor.py     # 🆕 Processeur amélioré
│   └── ...
```

---

## ⚙️ Configuration

### 1. Mettre à jour `.env`

```bash
# Ollama Configuration (pour utilisation locale)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:latest

# OpenAI-compatible endpoint
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama

# OU utiliser OpenAI directement
# OPENAI_API_KEY=sk-your-openai-key
# OPENAI_MODEL=gpt-4
```

### 2. Démarrer Ollama (si utilisation locale)

```bash
# Démarrer Ollama
ollama serve

# Dans un autre terminal, télécharger le modèle
ollama pull mistral:latest

# Vérifier que le modèle est disponible
ollama list
```

---

## 🚀 Utilisation

### Option 1: Via AgentQueryProcessor (Recommandé)

```python
from app.models.agent_processor import AgentQueryProcessor
from app.models.query import QueryRequest

# Créer le processeur
processor = AgentQueryProcessor(
    use_agents=True,
    agent_mode="simple"  # ou "full"
)

# Traiter une requête
query = QueryRequest(
    query="Quel est le délai de rétractation pour un achat en ligne ?",
    domain="consommation"
)

response = await processor.process_query(query, is_professional=False)
print(response)
```

### Option 2: Utilisation directe du Crew

```python
from app.agents.legal_crew import LegalResearchCrew

# Créer l'équipe
crew = LegalResearchCrew(
    process_type="sequential",
    domain_specialization="fiscal"  # Optionnel: expert de domaine
)

# Recherche
result = crew.research_legal_query(
    query="Conditions pour bénéficier du régime de la micro-entreprise ?",
    domain="fiscal",
    context={"activity": "Consultant", "revenue": "40000€"},
    is_professional=False
)

print(result)
```

### Option 3: Mode hybride (Intelligent)

```python
from app.models.agent_processor import get_recommended_processor
from app.models.query import QueryRequest

# Détection automatique de la complexité
def process_smart(query_text: str, domain: str = None):
    # Analyse de complexité
    if len(query_text) < 50:
        processor = get_recommended_processor("simple")
    elif "analyse" in query_text or "implications" in query_text:
        processor = get_recommended_processor("complex")
    else:
        processor = get_recommended_processor("medium")

    query = QueryRequest(query=query_text, domain=domain)
    return await processor.process_query(query)

# Usage
response = await process_smart(
    "Quelles sont les implications fiscales d'une donation-partage ?"
)
```

---

## 📚 Exemples d'intégration

### Exemple 1: Ajouter à une route FastAPI existante

```python
# app/api/endpoints/query.py

from fastapi import APIRouter, Depends
from app.models.agent_processor import AgentQueryProcessor
from app.models.query import QueryRequest

router = APIRouter()

@router.post("/query/enhanced")
async def enhanced_query(
    request: QueryRequest,
    use_agents: bool = True,
    current_user = Depends(get_current_user)
):
    """Requête avec agents activés"""
    processor = AgentQueryProcessor(
        use_agents=use_agents,
        agent_mode="full" if current_user.is_premium else "simple"
    )

    return await processor.process_query(
        request,
        is_professional=current_user.is_professional
    )
```

### Exemple 2: Intégration dans le QueryProcessor existant

```python
# app/models/processor.py

from app.agents.legal_crew import SimpleLegalCrew

class QueryProcessor:
    def __init__(self):
        self.agent_crew = SimpleLegalCrew()

    async def process_query(
        self,
        request: QueryRequest,
        is_professional: bool = False,
        use_agents: bool = False  # 🆕 Nouveau paramètre
    ):
        if use_agents:
            # Utiliser les agents
            result = self.agent_crew.quick_research(
                query=request.query,
                domain=request.domain
            )
            return self._format_agent_response(result)
        else:
            # Mode standard existant
            return await self._standard_processing(request)
```

### Exemple 3: Sélection conditionnelle

```python
# Règles métier pour décider quand utiliser les agents

def should_use_agents(query: str, user_tier: str) -> bool:
    """
    Décide si on utilise les agents selon:
    - Complexité de la question
    - Tier de l'utilisateur
    - Coût/performance
    """
    complexity_indicators = [
        "implications", "analyse", "stratégie",
        "procédure", "recours", "conséquences"
    ]

    is_complex = any(ind in query.lower() for ind in complexity_indicators)
    is_premium = user_tier in ["premium", "professional"]

    # Agents pour questions complexes OU utilisateurs premium
    return is_complex or is_premium

# Usage
if should_use_agents(query.query, user.tier):
    processor = AgentQueryProcessor(use_agents=True, agent_mode="full")
else:
    processor = QueryProcessor()  # Standard
```

---

## 🌐 API Endpoints

### POST `/api/agent-query`

Requête avec système multi-agents.

**Body:**
```json
{
  "query": "Quel est le délai de rétractation pour un achat en ligne ?",
  "domain": "consommation",
  "context": "Achat sur site français"
}
```

**Query params:**
- `agent_mode`: `auto` | `simple` | `full` | `disabled`

**Response:**
```json
{
  "introduction": "Réponse générée par notre équipe d'agents IA...",
  "legal_framework": "Selon l'article L221-18 du Code de la consommation...",
  "application": "Dans votre cas...",
  "exceptions": "Sauf pour...",
  "recommendations": ["Consultez un avocat", "..."],
  "sources": ["Article L221-18", "..."],
  "date_updated": "2025-11-02",
  "disclaimer": "Cette réponse est fournie à titre informatif..."
}
```

### POST `/api/agent-research`

Recherche directe sans structure LegalResponse.

**Query params:**
- `query`: La question juridique
- `domain`: Domaine juridique
- `use_domain_specialist`: `true` | `false`

**Response:**
```json
{
  "success": true,
  "result": "Résultat brut des agents...",
  "timestamp": "2025-11-02T12:00:00"
}
```

### GET `/api/agent-status`

Statut du système multi-agents.

**Response:**
```json
{
  "agents_available": true,
  "llm_backend": "ollama",
  "ollama_model": "mistral:latest",
  "llm_connected": true,
  "modes_available": ["simple", "full"],
  "agent_types": ["Legal Researcher", "..."]
}
```

---

## ⚡ Performance & Coûts

### Comparaison des modes

| Mode | Temps moyen | Tokens | Coût (OpenAI) | Qualité |
|------|-------------|--------|---------------|---------|
| Standard | 3-5s | 1,500 | $0.03 | ⭐⭐⭐ |
| Simple (2 agents) | 15-25s | 3,000 | $0.06 | ⭐⭐⭐⭐ |
| Full (4-5 agents) | 40-90s | 8,000 | $0.15 | ⭐⭐⭐⭐⭐ |

### Avec Ollama (local)

| Mode | Temps moyen | Coût | Qualité |
|------|-------------|------|---------|
| Simple | 20-35s | GRATUIT | ⭐⭐⭐⭐ |
| Full | 60-120s | GRATUIT | ⭐⭐⭐⭐⭐ |

### Recommandations

1. **Questions simples** (< 10 mots)
   - Mode: Standard
   - Raison: Rapide, suffisant

2. **Questions courantes** (définitions, délais)
   - Mode: Simple
   - Raison: Bon équilibre qualité/performance

3. **Questions complexes** (implications, stratégie)
   - Mode: Full
   - Raison: Analyse approfondie nécessaire

4. **Utilisateurs Premium/Pro**
   - Mode: Full par défaut
   - Raison: Meilleure qualité, valeur ajoutée

---

## 🔧 Dépannage

### Problème: "Model not found"

```bash
# Vérifier qu'Ollama est lancé
curl http://localhost:11434/api/tags

# Lancer Ollama
ollama serve

# Télécharger le modèle
ollama pull mistral:latest
```

### Problème: Agents très lents

**Solution 1:** Utiliser mode "simple" au lieu de "full"
```python
processor = AgentQueryProcessor(use_agents=True, agent_mode="simple")
```

**Solution 2:** Désactiver le mode verbose
```python
crew = LegalResearchCrew(verbose=False)
```

**Solution 3:** Utiliser un modèle plus rapide
```bash
# Dans .env
OLLAMA_MODEL=llama3.2:latest  # Plus petit, plus rapide
```

### Problème: Erreurs de connexion

```python
# Vérifier la configuration
import os
print(os.getenv("OPENAI_BASE_URL"))
print(os.getenv("OPENAI_API_KEY"))

# Tester la connexion
from app.agents.agents import get_llm
llm = get_llm()
response = llm.invoke("Test")
print(response)
```

### Problème: Agent name mismatch

Si vous voyez `NameError: name 'security_reviewer_agent' is not defined`:

✅ **Déjà corrigé** dans le code fourni! Le mapping agent name → role est géré automatiquement.

---

## 🎯 Checklist d'intégration

- [ ] Dépendances installées (`crewai`, `langchain-openai`)
- [ ] Ollama installé et lancé (`ollama serve`)
- [ ] Modèle téléchargé (`ollama pull mistral:latest`)
- [ ] `.env` configuré avec `OPENAI_BASE_URL` et `OPENAI_API_KEY`
- [ ] Module `app/agents/` créé avec les fichiers
- [ ] `AgentQueryProcessor` importable
- [ ] Test basique réussi
- [ ] Endpoint API ajouté (optionnel)
- [ ] Mode hybride configuré selon vos besoins

---

## 📞 Support

Pour toute question ou problème:

1. Vérifier cette documentation
2. Consulter les logs: `logs/app.log`
3. Tester avec le mode verbose activé
4. Vérifier le statut: `GET /api/agent-status`

---

## 🚀 Prochaines étapes

### Améliorations possibles

1. **Cache des résultats**
   - Éviter de retraiter les mêmes questions
   - Redis pour le cache distribué

2. **Agents asynchrones**
   - Exécution parallèle des agents indépendants
   - Réduction du temps de traitement

3. **Feedback loop**
   - Amélioration continue basée sur les retours utilisateurs
   - Fine-tuning des agents

4. **Métriques**
   - Temps de réponse par mode
   - Satisfaction utilisateur
   - Coût par requête

5. **A/B Testing**
   - Comparer Standard vs Agents
   - Mesurer l'impact sur la satisfaction

---

**Bonne intégration! 🎉**
