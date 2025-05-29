# Law Assistant Data Processing Architecture

This document provides a comprehensive overview of the data processing architecture used in the AI Legal Assistant platform.

## Core Components

1. **ETL Manager**
   - Central orchestrator for Extract, Transform, Load operations
   - Manages different data sources with custom extraction methods
   - Handles chunking of large documents

2. **Vector Store**
   - Abstraction layer over vector databases (Qdrant primarily)
   - Handles document storage, embedding, and retrieval
   - Provides search functionality for semantic queries

3. **Data Enrichment**
   - Enhances documents with NLP features
   - Adds metadata, summaries, classifications, and readability metrics
   - Uses multiple ML models for different enrichment tasks

4. **Legifrance API**
   - Interface to the official French legal data API
   - Handles authentication and endpoint-specific requests
   - Provides structured access to legal documents

## Data Flow

```
[External Data Sources] → [Extraction] → [Chunking] → [Enrichment] → [Vectorization] → [Storage] → [Search/Retrieval]
```

## Detailed Process Steps

### 1. Data Extraction

- **Multiple Source Types**:
  - Legifrance API (codes, jurisprudence, tables)
  - Web scraping (CNIL, BOFIP, court decisions)
  - PDF extraction
  - Mock data for testing

- **Source-Specific Extraction Methods**:
  - Each source has a dedicated extraction method in ETLManager
  - Authentication handling for protected sources
  - Rate limiting and error handling

### 2. Document Chunking

- **Chunking Strategy**:
  - Breaks large documents into manageable pieces (~1000 chars)
  - Maintains sentence boundaries using NLTK
  - Implements 200-character overlap between chunks
  - Preserves document metadata across chunks

- **Implementation**:
  The `chunk_text` function in `etl_manager.py` implements a sophisticated text chunking strategy:

  ```python
  def chunk_text(text: str, title: str = "", id_prefix: str = "") -> List[Dict[str, Any]]:
      """
      Découpe un texte juridique en chunks de taille appropriée avec chevauchement
      
      Args:
          text: Texte à découper
          title: Titre du document
          id_prefix: Préfixe pour les IDs des chunks
          
      Returns:
          Liste de chunks avec métadonnées
      """
      if not text:
          return []
      
      # Utilisation de NLTK pour découper en phrases
      sentences = sent_tokenize(text)
      
      chunks = []
      current_chunk = []
      current_size = 0
      
      for sentence in sentences:
          sentence_size = len(sentence)
          
          # Si l'ajout de cette phrase dépasse la taille maximale et qu'on a déjà du contenu
          if current_size + sentence_size > CHUNK_SIZE and current_chunk:
              # Créer un chunk avec le contenu accumulé
              chunk_text = " ".join(current_chunk)
              chunk_id = f"{id_prefix}_{len(chunks)}" if id_prefix else f"chunk_{uuid.uuid4().hex[:8]}"
              
              chunks.append({
                  "id": chunk_id,
                  "text": chunk_text,
                  "title": title,
                  "size": current_size
              })
              
              # Garder les dernières phrases pour le chevauchement
              overlap_size = 0
              overlap_chunks = []
              
              # Parcourir les phrases en sens inverse jusqu'à atteindre le chevauchement souhaité
              for s in reversed(current_chunk):
                  if overlap_size < CHUNK_OVERLAP:
                      overlap_chunks.insert(0, s)
                      overlap_size += len(s)
                  else:
                      break
              
              # Réinitialiser avec le chevauchement
              current_chunk = overlap_chunks
              current_size = overlap_size
          
          # Ajouter la phrase au chunk actuel
          current_chunk.append(sentence)
          current_size += sentence_size
      
      # Ajouter le dernier chunk s'il contient du texte
      if current_chunk:
          chunk_text = " ".join(current_chunk)
          chunk_id = f"{id_prefix}_{len(chunks)}" if id_prefix else f"chunk_{uuid.uuid4().hex[:8]}"
          
          chunks.append({
              "id": chunk_id,
              "text": chunk_text,
              "title": title,
              "size": current_size
          })
      
      return chunks
  ```

- **Key Features of Chunking**:
  - Sentence-aware chunking preserves context
  - Configurable chunk size (CHUNK_SIZE = 1000 by default)
  - Overlap between chunks (CHUNK_OVERLAP = 200 by default)
  - Unique ID generation for each chunk
  - Metadata preservation across chunks

### 3. Data Enrichment

- **NLP Processing Pipeline**:
  - Uses spaCy for linguistic feature extraction
  - Named entity recognition
  - Keyword extraction
  - Domain classification

- **Text Enhancement**:
  - Automatic summarization with transformer models
  - Legal reference extraction through regex patterns
  - Readability metrics calculation

- **Batch Processing**:
  - Processes documents in configurable batches
  - Parallel processing with ThreadPoolExecutor
  - Graceful fallback for missing models

### 4. Vectorization

- **Embedding Generation**:
  - Uses sentence-transformers models
  - Default: paraphrase-multilingual-mpnet-base-v2
  - 768-dimension vectors

- **Document Preparation**:
  - Structures documents with consistent fields
  - Generates unique IDs for vector storage
  - Maintains full text and metadata

### 5. Vector Storage

- **Database Options**:
  - Primary: Qdrant
  - Fallback: Weaviate

- **Storage Structure**:
  - Collection: LegalTexts
  - Vector similarity: Cosine
  - Payload includes full document and metadata

- **Document Format**:
  ```
  {
      "id": "unique_id",
      "title": "Document title",
      "content": "Full document text",
      "type": "Document category",
      "date": "ISO date",
      "url": "Source URL",
      "metadata": {
          "source": "Origin name",
          "entities": {...},
          "summary": "Auto-generated summary",
          "domains": ["legal domain classifications"],
          "readability": {...},
          "legal_references": [...]
      }
  }
  ```

### 6. Search and Retrieval

- **Semantic Search**:
  - Converts query to vector representation
  - Finds similar vectors in the database
  - Returns scored results

- **Filtering Capabilities**:
  - By document type
  - By date ranges
  - By metadata properties
  - Custom filter combinations

## Key Classes and Functions

1. **ETLManager**
   - Manages extraction pipeline
   - Schedules recurring data updates
   - Handles different source types

2. **VectorStore**
   - Abstracts vector database operations
   - Manages document embedding and storage
   - Provides search interface

3. **DataEnrichment**
   - Enriches documents with NLP features
   - Adds domain classification and keywords
   - Generates summaries and extracts references

4. **LegifranceAPI**
   - Handles authentication
   - Provides methods for each API endpoint
   - Manages error handling and retries

## Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  External Data  │     │    ETL System   │     │   Vector Store  │
│    Sources      │────▶│                 │────▶│                 │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                        │
                                ▼                        ▼
                         ┌─────────────────┐     ┌─────────────────┐
                         │                 │     │                 │
                         │ Data Enrichment │     │   API Backend   │
                         │                 │     │                 │
                         └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │                 │
                                                │  Frontend App   │
                                                │                 │
                                                └─────────────────┘
```

## Configuration Settings

- **Environment Variables**:
  - `EMBEDDING_MODEL`: Vector embedding model
  - `EMBEDDING_DIMENSION`: Vector size
  - `VECTOR_DB_TYPE`: Database backend
  - `QDRANT_URL`: Vector database location
  - `CHUNK_SIZE`: Size of document chunks
  - `CHUNK_OVERLAP`: Overlap between chunks
  - `ETL_BATCH_SIZE`: Document batch size

## Optimizations

1. **Memory Efficiency**:
   - Batch processing to control memory usage
   - Streaming for large file downloads
   - Chunking to handle large documents

2. **Performance**:
   - Parallel processing with ThreadPoolExecutor
   - Asynchronous operations with asyncio
   - Caching of embedding models

3. **Reliability**:
   - Graceful error handling and fallbacks
   - Logging of all operations
   - Structured data validation

## ETL Source Configuration

The ETLManager supports multiple data sources with custom extraction methods:

```python
self.sources = {
    "legifrance_codes": {
        "name": "Légifrance Codes",
        "type": "code",
        "extraction_method": self._extract_legifrance_codes,
        "frequency": "monthly"
    },
    "legifrance_jurisprudence": {
        "name": "Légifrance Jurisprudence",
        "type": "jurisprudence",
        "extraction_method": self._extract_legifrance_jurisprudence,
        "frequency": "weekly"
    },
    "bofip": {
        "name": "Bulletin Officiel des Finances Publiques",
        "url": "https://bofip.impots.gouv.fr/bofip/ext/opendata/export",
        "type": "fiscal",
        "extraction_method": self._extract_bofip,
        "frequency": "weekly"
    },
    "cnil": {
        "name": "Commission Nationale de l'Informatique et des Libertés",
        "url": "https://www.cnil.fr/fr/deliberations",
        "type": "rgpd",
        "extraction_method": self._extract_cnil,
        "frequency": "monthly"
    },
    # Additional sources...
}
```

This architecture provides a robust, scalable solution for processing, enriching, and retrieving French legal documents with advanced NLP capabilities and semantic search functionality. 