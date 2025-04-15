#!/usr/bin/env python3
"""
Test script for extracting data from Legifrance API using the Tables endpoint
"""

import os
import sys
import json
import asyncio
import tempfile
import requests
from datetime import datetime
import logging
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules
from app.data.legifrance_api import LegifranceAPI
from app.utils.vector_store import vector_store

# Constants
PDF_STORAGE_DIR = Path("data/pdf_downloads")

# Create PDF storage directory if it doesn't exist
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Try to import PDF extraction libraries
try:
    import fitz  # PyMuPDF
    PDF_EXTRACTION_AVAILABLE = True
except ImportError:
    logger.warning("PyMuPDF not found, PDF extraction will not be available. Install with: pip install pymupdf")
    PDF_EXTRACTION_AVAILABLE = False

async def extract_legifrance_tables(start_year=None, end_year=None):
    """
    Extract annual tables from Legifrance API
    
    Args:
        start_year: Starting year (defaults to current year - 1)
        end_year: Ending year (defaults to current year)
        
    Returns:
        List of extracted documents
    """
    # Initialize API client
    legifrance_api = LegifranceAPI()
    
    # Authenticate
    try:
        await legifrance_api.authenticate()
        logger.info("Successfully authenticated with Legifrance API")
    except Exception as e:
        logger.error(f"Failed to authenticate with Legifrance API: {str(e)}")
        return []
    
    # Set default year range if not provided
    current_year = datetime.now().year
    if not start_year:
        start_year = current_year - 1
    if not end_year:
        end_year = current_year
    
    logger.info(f"Extracting tables for years {start_year} to {end_year}")
    
    # Extract data
    try:
        # Use the get_tables method directly
        response = await legifrance_api.get_tables(start_year=start_year, end_year=end_year)
        
        # Save raw response for inspection
        with open('tables_response.json', 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Raw API response saved to tables_response.json")
        
        if not response or 'tables' not in response:
            logger.warning("No tables found in API response")
            return []
        
        tables = response.get('tables', [])
        logger.info(f"Retrieved {len(tables)} tables")
        
        # Transform tables data into documents
        documents = []
        for table in tables:
            table_id = table.get('id', '')
            file_name = table.get('fileName', '')
            path_to_file = table.get('pathToFile', '')
            date_publi = table.get('datePubli', 0)
            year = str(datetime.fromtimestamp(date_publi/1000).year) if date_publi else 'Unknown'
            table_type = table.get('type', '')
            file_size = table.get('displaySize', '')
            
            # Construct a title from available information
            title = f"Annual Table {year} - {table_type}"
            
            # Generate structured content from available information
            structured_content = [
                f"Légifrance Annual Table Documentation for Year {year}",
                f"Type: {table_type}",
                f"ID: {table_id}",
                f"Publication Date: {datetime.fromtimestamp(date_publi/1000).strftime('%Y-%m-%d') if date_publi else 'Unknown'}",
                f"File Size: {file_size}",
                f"File Name: {file_name}",
            ]
            
            # Add section information if available
            if 'sections' in table:
                structured_content.append("\nTable Sections:")
                for section in table.get('sections', []):
                    section_title = section.get('title', '')
                    structured_content.append(f"- {section_title}")
                    
                    # Add subsections if available
                    for subsection in section.get('sections', []):
                        subsection_title = subsection.get('title', '')
                        structured_content.append(f"  - {subsection_title}")
            
            # Create document structure
            doc = {
                'doc_id': f"table_{table_id}",
                'title': title,
                'content': "\n".join(structured_content),  # Use structured content as fallback
                'doc_type': 'table',
                'date': f"{year}-12-31",
                'url': '',  # Will be filled later if needed
                'metadata': {
                    'source': 'legifrance',
                    'type': 'table',
                    'table_type': table_type,
                    'year': year,
                    'table_id': table_id,
                    'file_name': file_name,
                    'file_size': file_size,
                    'path_to_file': path_to_file,
                    'api_data': table  # Store full API data for potential later use
                }
            }
            
            documents.append(doc)
        
        logger.info(f"Extracted {len(documents)} table documents from Legifrance API")
        return documents, legifrance_api
        
    except Exception as e:
        logger.error(f"Error extracting tables from Legifrance API: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return [], None

async def download_pdf_with_api(api_client, path_to_file, output_path):
    """
    Download a PDF file using the API client for proper authentication
    
    Args:
        api_client: LegifranceAPI client instance with valid authentication
        path_to_file: Path to file from API response
        output_path: Path to save the PDF file
        
    Returns:
        Path to the downloaded file or None if failed
    """
    if not path_to_file:
        logger.warning("No path provided for PDF download")
        return None
        
    # Don't re-download if file exists and has content
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"PDF already exists at {output_path}, skipping download")
        return output_path
    
    try:
        # Construct the proper URL format for downloading PDFs
        token = await api_client.authenticate()
        base_url = api_client.base_url
        
        # Method 1 (Primary): Using consult/tableFile endpoint with proper POST payload
        try:
            logger.info(f"Attempting to download PDF using consult/tableFile endpoint")
            endpoint = "consult/tableFile"
            download_url = f"{base_url}/{endpoint}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/pdf"
            }
            
            payload = {
                "path": path_to_file
            }
            
            logger.info(f"Downloading PDF with path: {path_to_file}")
            response = requests.post(download_url, headers=headers, json=payload, stream=True)
            
            # Log full request details for debugging
            logger.info(f"Request URL: {download_url}")
            logger.info(f"Request headers: {headers}")
            logger.info(f"Request payload: {payload}")
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content-type: {response.headers.get('content-type', 'unknown')}")
            
            response.raise_for_status()
            
            if response.headers.get('content-type') == 'application/pdf':
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"Downloaded PDF to {output_path} ({output_path.stat().st_size} bytes)")
                    return output_path
                else:
                    logger.warning(f"Downloaded PDF is empty: {output_path}")
            else:
                logger.warning(f"Response is not a PDF: {response.headers.get('content-type')}")
                
        except Exception as e:
            logger.warning(f"Method 1 failed: {str(e)}")
        
        # Method 2: Using direct download URL format
        try:
            logger.info(f"Attempting to download PDF using direct URL format")
            # First variation: with table prefix
            download_url = f"https://www.legifrance.gouv.fr/download/pdf/table{path_to_file}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/pdf"
            }
            
            logger.info(f"Downloading PDF from: {download_url}")
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            
            if response.headers.get('content-type') == 'application/pdf':
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"Downloaded PDF to {output_path} ({output_path.stat().st_size} bytes)")
                    return output_path
                else:
                    logger.warning(f"Downloaded PDF is empty: {output_path}")
            else:
                logger.warning(f"Response is not a PDF: {response.headers.get('content-type')}")
                
        except Exception as e:
            logger.warning(f"Method 2 failed: {str(e)}")
            
        # Method 3: Using another URL format without table prefix
        try:
            logger.info(f"Attempting to download PDF using direct URL without table prefix")
            download_url = f"https://www.legifrance.gouv.fr/download/pdf{path_to_file}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/pdf"
            }
            
            logger.info(f"Downloading PDF from: {download_url}")
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            
            if response.headers.get('content-type') == 'application/pdf':
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"Downloaded PDF to {output_path} ({output_path.stat().st_size} bytes)")
                    return output_path
                else:
                    logger.warning(f"Downloaded PDF is empty: {output_path}")
            else:
                logger.warning(f"Response is not a PDF: {response.headers.get('content-type')}")
                
        except Exception as e:
            logger.warning(f"Method 3 failed: {str(e)}")
        
        # Method 4: Using base API URL with download/pdf endpoint
        try:
            logger.info(f"Attempting to download PDF using API base URL with download/pdf endpoint")
            endpoint = f"download/pdf{path_to_file}"
            download_url = f"{base_url}/{endpoint}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/pdf"
            }
            
            logger.info(f"Downloading PDF from: {download_url}")
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            
            if response.headers.get('content-type') == 'application/pdf':
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"Downloaded PDF to {output_path} ({output_path.stat().st_size} bytes)")
                    return output_path
                else:
                    logger.warning(f"Downloaded PDF is empty: {output_path}")
            else:
                logger.warning(f"Response is not a PDF: {response.headers.get('content-type')}")
                
        except Exception as e:
            logger.warning(f"Method 4 failed: {str(e)}")
            
        logger.error(f"All download methods failed for {path_to_file}")
        return None
            
    except Exception as e:
        logger.error(f"Error downloading PDF with API client: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a PDF file
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    if not PDF_EXTRACTION_AVAILABLE:
        logger.warning("PDF extraction not available, install PyMuPDF")
        return ""
        
    try:
        pdf_document = fitz.open(pdf_path)
        text_content = []
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text_content.append(page.get_text())
            
        pdf_document.close()
        
        full_text = "\n".join(text_content)
        
        # Basic text cleaning
        full_text = full_text.strip()
        
        logger.info(f"Extracted {len(full_text)} characters from PDF {pdf_path}")
        return full_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        return ""

async def process_pdf_documents(documents, api_client):
    """
    Process PDF documents to extract their text content using the API client
    
    Args:
        documents: List of document dictionaries
        api_client: LegifranceAPI client instance with valid authentication
        
    Returns:
        Updated list of documents with PDF content
    """
    if not PDF_EXTRACTION_AVAILABLE:
        logger.warning("PDF extraction not available, install PyMuPDF")
        return documents
    
    if not api_client:
        logger.warning("No API client provided, cannot download PDFs")
        return documents
        
    updated_documents = []
    
    for doc in documents:
        path_to_file = doc.get('metadata', {}).get('path_to_file', '')
        file_name = doc.get('metadata', {}).get('file_name', '')
        
        if path_to_file:
            # Create a filename based on document ID
            pdf_filename = file_name if file_name else f"{doc['doc_id']}.pdf"
            pdf_path = PDF_STORAGE_DIR / pdf_filename
            
            # Download the PDF using API client
            downloaded_path = await download_pdf_with_api(api_client, path_to_file, pdf_path)
            
            if downloaded_path:
                # Extract text from PDF
                pdf_text = extract_text_from_pdf(downloaded_path)
                
                if pdf_text:
                    # Update document content with extracted PDF text
                    doc['content'] = pdf_text
                    doc['metadata']['extracted_from_pdf'] = True
                    doc['metadata']['pdf_local_path'] = str(downloaded_path)
                    logger.info(f"Added PDF content to document {doc['doc_id']}")
                else:
                    logger.warning(f"No text extracted from PDF for document {doc['doc_id']}, using structured content instead")
            else:
                logger.warning(f"Failed to download PDF for document {doc['doc_id']}, using structured content instead")
        
        updated_documents.append(doc)
    
    return updated_documents

def import_to_vector_store(documents):
    """
    Import documents to vector store
    
    Args:
        documents: List of documents to import
        
    Returns:
        Number of successfully imported documents
    """
    if not vector_store or not vector_store.is_functional:
        logger.error("Vector store is not available or not functional")
        return 0
    
    logger.info(f"Importing {len(documents)} documents to vector store")
    
    imported_count = 0
    for doc in documents:
        result = vector_store.add_document(
            doc_id=doc['doc_id'],
            title=doc['title'],
            content=doc['content'],
            doc_type=doc['doc_type'],
            date=doc['date'],
            url=doc['url'],
            metadata=doc['metadata']
        )
        
        if result:
            imported_count += 1
            logger.info(f"Imported document: {doc['title']}")
        else:
            logger.warning(f"Failed to import document: {doc['title']}")
    
    logger.info(f"Successfully imported {imported_count}/{len(documents)} documents to vector store")
    return imported_count

async def async_main():
    """Async main function to execute the extraction and import process"""
    logger.info("Starting Legifrance tables extraction")
    
    # Extract documents from Legifrance API - using a small range for testing
    documents, api_client = await extract_legifrance_tables(start_year=1900, end_year=2025)
    
    if not documents:
        logger.error("No documents extracted from Legifrance API")
        return False
    
    logger.info(f"Extracted {len(documents)} documents")
    
    # Process PDFs to extract content
    documents_with_pdfs = await process_pdf_documents(documents, api_client)
    
    # Import documents to vector store
    imported_count = import_to_vector_store(documents_with_pdfs)
    
    logger.info(f"ETL process completed: {imported_count}/{len(documents)} documents imported")
    return imported_count > 0

def main():
    """Main function to run the async code"""
    return asyncio.run(async_main())

if __name__ == "__main__":
    load_dotenv()  # Load environment variables
    success = main()
    sys.exit(0 if success else 1)
