# 🚀 Quick Start: Multi-Agent Integration

**5-minute guide to get your multi-agent system running**

## ✅ Prerequisites Checklist

```bash
# 1. Install dependencies
cd /Users/ayoubmbarek/Projects/law_assistant
pip install crewai langchain-openai python-dotenv

# 2. Start Ollama
ollama serve

# 3. Download model (in another terminal)
ollama pull mistral:latest

# 4. Verify model is ready
ollama list
# Should show: mistral:latest
```

## ⚙️ Configuration (2 minutes)

Edit your `.env` file:

```bash
# Add these lines
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OLLAMA_MODEL=mistral:latest
```

## 🧪 Test Installation (1 minute)

```bash
# Run the test suite
python test_agents_integration.py
```

Expected output: `✅ All tests passed!`

## 🎯 Quick Usage Examples

### Example 1: Simple Query (2 agents, ~20 seconds)

```python
from app.models.agent_processor import AgentQueryProcessor
from app.models.query import QueryRequest

# Create processor
processor = AgentQueryProcessor(
    use_agents=True,
    agent_mode="simple"
)

# Ask a question
query = QueryRequest(
    query="Quel est le délai de rétractation pour un achat en ligne ?",
    domain="consommation"
)

response = await processor.process_query(query)
print(response.legal_framework)
```

### Example 2: Complex Query (4 agents, ~60 seconds)

```python
processor = AgentQueryProcessor(
    use_agents=True,
    agent_mode="full"
)

query = QueryRequest(
    query="Quelles sont les conditions de licenciement pour inaptitude ?",
    domain="travail",
    context="Employé avec 10 ans d'ancienneté"
)

response = await processor.process_query(query, is_professional=True)
```

### Example 3: Direct Crew Usage

```python
from app.agents.legal_crew import SimpleLegalCrew

crew = SimpleLegalCrew()
result = crew.quick_research(
    query="Conditions pour créer une micro-entreprise ?",
    domain="affaires"
)
print(result)
```

## 🌐 API Endpoints

### Start your FastAPI server

```bash
cd /Users/ayoubmbarek/Projects/law_assistant
uvicorn app.main:app --reload
```

### Test the agent endpoint

```bash
# Simple test
curl -X POST "http://localhost:8000/api/agent-query?agent_mode=simple" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quel est le délai de rétractation ?",
    "domain": "consommation"
  }'

# Check agent status
curl "http://localhost:8000/api/agent-status"
```

## 📊 Modes Comparison

| Mode | Time | Agents | Best For |
|------|------|--------|----------|
| `simple` | 20s | 2 | Quick questions |
| `full` | 60s | 4-5 | Complex analysis |
| `disabled` | 5s | 0 | Very simple queries |

## 🔧 Troubleshooting

### "Model not found" error
```bash
ollama pull mistral:latest
ollama list  # Verify it's there
```

### Agents are slow
```python
# Use simple mode instead of full
processor = AgentQueryProcessor(use_agents=True, agent_mode="simple")
```

### Import errors
```bash
pip install crewai langchain-openai
```

## 📚 File Structure

```
law_assistant/
├── app/
│   ├── agents/                    # 🆕 New module
│   │   ├── __init__.py
│   │   ├── agents.py              # 5 specialized agents
│   │   └── legal_crew.py          # Orchestration
│   ├── models/
│   │   └── agent_processor.py     # 🆕 Enhanced processor
│   └── api/endpoints/
│       └── agent_query.py         # 🆕 New API endpoint
├── AGENTS_INTEGRATION_GUIDE.md    # Full documentation
├── AGENTS_QUICKSTART.md           # This file
└── test_agents_integration.py     # Test suite
```

## 🎓 Available Agents

1. **Juriste Chercheur** - Searches legal texts and jurisprudence
2. **Vérificateur de Citations** - Verifies legal citations
3. **Rédacteur Juridique** - Writes clear legal responses
4. **Réviseur Qualité** - Quality control and compliance
5. **Expert de Domaine** (optional) - Domain specialists (fiscal, travail, etc.)

## 🚦 Next Steps

1. ✅ Run `test_agents_integration.py` to verify setup
2. 📖 Read `AGENTS_INTEGRATION_GUIDE.md` for detailed docs
3. 🔌 Integrate with your existing `QueryProcessor`
4. 🌐 Add API endpoints to your routes
5. 🎯 Configure smart mode selection based on query complexity

## 💡 Integration Patterns

### Pattern 1: Replace QueryProcessor
```python
# Old
from app.models.processor import QueryProcessor
processor = QueryProcessor()

# New
from app.models.agent_processor import AgentQueryProcessor
processor = AgentQueryProcessor(use_agents=True, agent_mode="simple")
```

### Pattern 2: Conditional Usage
```python
# Use agents for complex queries only
if is_complex_query(query):
    processor = AgentQueryProcessor(use_agents=True, agent_mode="full")
else:
    processor = QueryProcessor()  # Standard
```

### Pattern 3: Premium Feature
```python
# Agents for premium users
if user.is_premium:
    processor = AgentQueryProcessor(use_agents=True, agent_mode="full")
else:
    processor = QueryProcessor()  # Free tier
```

## 📞 Support

**Issues?** Check:
1. Is Ollama running? `ollama serve`
2. Is model downloaded? `ollama list`
3. Is `.env` configured? Check `OPENAI_BASE_URL`
4. Run test script: `python test_agents_integration.py`

**For detailed docs:** See `AGENTS_INTEGRATION_GUIDE.md`

---

**You're ready! 🎉** Start with `simple` mode and scale up to `full` as needed.
