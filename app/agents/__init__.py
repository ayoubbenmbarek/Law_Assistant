"""
Multi-Agent System for Legal Assistant
Integrates CrewAI agents for enhanced legal query processing
"""

from .legal_crew import LegalResearchCrew
from .agents import (
    create_legal_researcher,
    create_citation_verifier,
    create_legal_writer,
    create_quality_reviewer
)

__all__ = [
    'LegalResearchCrew',
    'create_legal_researcher',
    'create_citation_verifier',
    'create_legal_writer',
    'create_quality_reviewer'
]