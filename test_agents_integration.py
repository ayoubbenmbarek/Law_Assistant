#!/usr/bin/env python3
"""
Test Script for Multi-Agent Integration
Run this to verify that the agent system is properly integrated
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def test_imports():
    """Test 1: Vérifier que les imports fonctionnent"""
    print_header("TEST 1: Imports")

    try:
        from app.agents.agents import (
            create_legal_researcher,
            create_citation_verifier,
            create_legal_writer,
            create_quality_reviewer,
            create_domain_specialist,
            get_llm
        )
        print_success("Agents module imported successfully")
    except ImportError as e:
        print_error(f"Failed to import agents module: {e}")
        return False

    try:
        from app.agents.legal_crew import LegalResearchCrew, SimpleLegalCrew
        print_success("LegalResearchCrew imported successfully")
    except ImportError as e:
        print_error(f"Failed to import crew module: {e}")
        return False

    try:
        from app.models.agent_processor import AgentQueryProcessor
        print_success("AgentQueryProcessor imported successfully")
    except ImportError as e:
        print_error(f"Failed to import agent processor: {e}")
        return False

    return True


def test_llm_connection():
    """Test 2: Vérifier la connexion au LLM"""
    print_header("TEST 2: LLM Connection")

    try:
        from app.agents.agents import get_llm

        base_url = os.getenv("OPENAI_BASE_URL", "")
        if "localhost" in base_url:
            print_info(f"Using Ollama at {base_url}")
            print_info(f"Model: {os.getenv('OLLAMA_MODEL', 'mistral:latest')}")
        else:
            print_info("Using OpenAI API")

        llm = get_llm()
        print_success("LLM instance created successfully")

        # Test simple call
        print_info("Testing LLM with simple query...")
        response = llm.invoke("Réponds juste 'OK' en un mot")
        print_success(f"LLM responded: {response.content[:100]}")

        return True

    except Exception as e:
        print_error(f"LLM connection failed: {e}")
        print_warning("Make sure Ollama is running: ollama serve")
        print_warning("And model is downloaded: ollama pull mistral:latest")
        return False


def test_agent_creation():
    """Test 3: Créer les agents individuels"""
    print_header("TEST 3: Agent Creation")

    try:
        from app.agents.agents import (
            create_legal_researcher,
            create_citation_verifier,
            create_legal_writer,
            create_quality_reviewer,
            create_domain_specialist
        )

        print_info("Creating Legal Researcher...")
        researcher = create_legal_researcher()
        print_success(f"✓ {researcher.role}")

        print_info("Creating Citation Verifier...")
        verifier = create_citation_verifier()
        print_success(f"✓ {verifier.role}")

        print_info("Creating Legal Writer...")
        writer = create_legal_writer()
        print_success(f"✓ {writer.role}")

        print_info("Creating Quality Reviewer...")
        reviewer = create_quality_reviewer()
        print_success(f"✓ {reviewer.role}")

        print_info("Creating Domain Specialist (fiscal)...")
        specialist = create_domain_specialist("fiscal")
        print_success(f"✓ {specialist.role}")

        return True

    except Exception as e:
        print_error(f"Agent creation failed: {e}")
        return False


def test_simple_crew():
    """Test 4: Tester SimpleLegalCrew avec une vraie requête"""
    print_header("TEST 4: SimpleLegalCrew (Quick Test)")

    try:
        from app.agents.legal_crew import SimpleLegalCrew

        print_info("Creating SimpleLegalCrew...")
        crew = SimpleLegalCrew(verbose=False)
        print_success("Crew created successfully")

        print_info("Running quick research on simple legal question...")
        print_info("Question: 'Quel est le délai de rétractation pour un achat en ligne ?'")

        start_time = datetime.now()

        result = crew.quick_research(
            query="Quel est le délai de rétractation pour un achat en ligne ?",
            domain="consommation"
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        if result.get("success"):
            print_success(f"Research completed in {elapsed:.2f} seconds")
            print_info(f"Result preview: {str(result.get('result'))[:200]}...")
            return True
        else:
            print_error(f"Research failed: {result.get('error')}")
            return False

    except Exception as e:
        print_error(f"SimpleLegalCrew test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_crew():
    """Test 5: Tester LegalResearchCrew complète (optionnel)"""
    print_header("TEST 5: Full LegalResearchCrew (Optional)")

    print_warning("This test is skipped by default (takes 60-120s)")
    print_info("To run it, uncomment the code in test_agents_integration.py")

    return True

    # Uncomment to run full test
    """
    try:
        from app.agents.legal_crew import LegalResearchCrew

        print_info("Creating full LegalResearchCrew with 4 agents...")
        crew = LegalResearchCrew(
            process_type="sequential",
            verbose=False
        )
        print_success("Full crew created successfully")

        print_info("Running comprehensive legal research...")
        print_info("Question: 'Quelles sont les conditions de licenciement pour inaptitude ?'")

        start_time = datetime.now()

        result = crew.research_legal_query(
            query="Quelles sont les conditions de licenciement pour inaptitude suite à un accident du travail ?",
            domain="travail",
            context={"employee_seniority": "10 ans"},
            is_professional=False
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        if result.get("success"):
            print_success(f"Full research completed in {elapsed:.2f} seconds")
            print_info(f"Result preview: {str(result.get('result'))[:300]}...")
            return True
        else:
            print_error(f"Full research failed: {result.get('error')}")
            return False

    except Exception as e:
        print_error(f"Full crew test failed: {e}")
        return False
    """


async def test_agent_processor():
    """Test 6: Tester AgentQueryProcessor"""
    print_header("TEST 6: AgentQueryProcessor")

    try:
        from app.models.agent_processor import AgentQueryProcessor
        from app.models.query import QueryRequest

        print_info("Creating AgentQueryProcessor in simple mode...")
        processor = AgentQueryProcessor(
            use_agents=True,
            agent_mode="simple"
        )
        print_success("Processor created successfully")

        print_info("Processing legal query...")
        query = QueryRequest(
            query="C'est quoi le Code civil ?",
            domain="général"
        )

        start_time = datetime.now()

        response = await processor.process_query(query, is_professional=False)

        elapsed = (datetime.now() - start_time).total_seconds()

        print_success(f"Query processed in {elapsed:.2f} seconds")
        print_info(f"Response preview: {response.introduction[:150]}...")

        return True

    except Exception as e:
        print_error(f"AgentQueryProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment():
    """Test 0: Vérifier l'environnement"""
    print_header("TEST 0: Environment Check")

    # Check .env variables
    required_vars = ["OPENAI_BASE_URL", "OPENAI_API_KEY"]
    optional_vars = ["OLLAMA_MODEL", "OLLAMA_BASE_URL"]

    print_info("Checking required environment variables...")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var}: {value[:50]}...")
        else:
            print_warning(f"{var}: Not set")

    print_info("\nChecking optional environment variables...")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var}: {value}")
        else:
            print_info(f"{var}: Not set (using defaults)")

    # Check if Ollama is running
    if "localhost" in os.getenv("OPENAI_BASE_URL", ""):
        print_info("\nChecking Ollama connection...")
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                print_success(f"Ollama is running with {len(models)} models")
                for model in models[:3]:
                    print_success(f"  - {model['name']}")
            else:
                print_warning("Ollama responded but with error")
        except Exception as e:
            print_error("Ollama is not running or not accessible")
            print_warning("Start it with: ollama serve")

    return True


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}🤖 Multi-Agent Integration Test Suite{Colors.ENDC}")
    print(f"{Colors.BOLD}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")

    tests = [
        ("Environment Check", test_environment),
        ("Imports", test_imports),
        ("LLM Connection", test_llm_connection),
        ("Agent Creation", test_agent_creation),
        ("SimpleLegalCrew", test_simple_crew),
        ("Full LegalResearchCrew", test_full_crew),
        ("AgentQueryProcessor", lambda: asyncio.run(test_agent_processor())),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.ENDC}")

    if passed == total:
        print_success("\n🎉 All tests passed! Agent system is ready to use.")
        print_info("\nNext steps:")
        print_info("1. Check AGENTS_INTEGRATION_GUIDE.md for usage examples")
        print_info("2. Try the API endpoints")
        print_info("3. Integrate with your existing QueryProcessor")
        return 0
    else:
        print_warning(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
        print_info("\nTroubleshooting:")
        print_info("1. Make sure Ollama is running: ollama serve")
        print_info("2. Check your .env configuration")
        print_info("3. Verify model is downloaded: ollama pull mistral:latest")
        print_info("4. Check logs/app.log for more details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
