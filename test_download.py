#!/usr/bin/env python3
"""
Test script for downloading a PDF from the Legifrance API
"""

import os
import sys
import requests
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules
from app.data.legifrance_api import LegifranceAPI

# Constants
PDF_STORAGE_DIR = Path("data/pdf_downloads")
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

async def test_pdf_download():
    """
    Test function to download a PDF file from the Legifrance API
    """
    # Initialize API client
    legifrance_api = LegifranceAPI()
    
    # Authenticate
    try:
        token = await legifrance_api.authenticate()
        logger.info(f"Successfully authenticated with Legifrance API")
        logger.info(f"Token: {token[:10]}...{token[-10:]}")
    except Exception as e:
        logger.error(f"Failed to authenticate with Legifrance API: {str(e)}")
        return False
    
    # Try to download a specific PDF file
    test_paths = [
        "/TB/TB_2012_ANA.pdf",
        "/TB/TB_2015_ANA.pdf",
        "/TB/TB_1990_ANA.pdf"
    ]
    
    base_url = legifrance_api.base_url
    
    for path_to_file in test_paths:
        logger.info(f"=== Testing download of {path_to_file} ===")
        
        output_path = PDF_STORAGE_DIR / Path(path_to_file).name
        
        # Method 1: Using consult/tableFile endpoint with proper POST payload
        try:
            logger.info(f"Method 1: Attempting to download PDF using consult/tableFile endpoint")
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
            
            logger.info(f"Request URL: {download_url}")
            logger.info(f"Request headers: {headers}")
            logger.info(f"Request payload: {payload}")
            
            response = requests.post(download_url, headers=headers, json=payload, stream=True)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.warning(f"Error response content: {response.text[:500]}")
            
            response.raise_for_status()
            
            if response.headers.get('content-type') == 'application/pdf':
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"Downloaded PDF to {output_path} ({output_path.stat().st_size} bytes)")
                    return True
                else:
                    logger.warning(f"Downloaded PDF is empty: {output_path}")
            else:
                logger.warning(f"Response is not a PDF: {response.headers.get('content-type')}")
                logger.warning(f"Response content: {response.text[:500]}...")
                
        except Exception as e:
            logger.warning(f"Method 1 failed: {str(e)}")
        
        # Method 2: Using direct download URL format
        try:
            logger.info(f"Method 2: Attempting to download PDF using direct URL format")
            # First variation: with table prefix
            download_url = f"https://www.legifrance.gouv.fr/download/pdf/table{path_to_file}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/pdf"
            }
            
            logger.info(f"Request URL: {download_url}")
            logger.info(f"Request headers: {headers}")
            
            response = requests.get(download_url, headers=headers, stream=True)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.warning(f"Error response content: {response.text[:500]}")
            
            response.raise_for_status()
            
            if response.headers.get('content-type') == 'application/pdf':
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"Downloaded PDF to {output_path} ({output_path.stat().st_size} bytes)")
                    return True
                else:
                    logger.warning(f"Downloaded PDF is empty: {output_path}")
            else:
                logger.warning(f"Response is not a PDF: {response.headers.get('content-type')}")
                logger.warning(f"Response content: {response.text[:500]}...")
                
        except Exception as e:
            logger.warning(f"Method 2 failed: {str(e)}")
            
        # Method 3: Using another URL format without table prefix
        try:
            logger.info(f"Method 3: Attempting to download PDF using direct URL without table prefix")
            download_url = f"https://www.legifrance.gouv.fr/download/pdf{path_to_file}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/pdf"
            }
            
            logger.info(f"Request URL: {download_url}")
            logger.info(f"Request headers: {headers}")
            
            response = requests.get(download_url, headers=headers, stream=True)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.warning(f"Error response content: {response.text[:500]}")
            
            response.raise_for_status()
            
            if response.headers.get('content-type') == 'application/pdf':
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"Downloaded PDF to {output_path} ({output_path.stat().st_size} bytes)")
                    return True
                else:
                    logger.warning(f"Downloaded PDF is empty: {output_path}")
            else:
                logger.warning(f"Response is not a PDF: {response.headers.get('content-type')}")
                logger.warning(f"Response content: {response.text[:500]}...")
                
        except Exception as e:
            logger.warning(f"Method 3 failed: {str(e)}")
        
        # Method 4: Using base API URL with download/pdf endpoint
        try:
            logger.info(f"Method 4: Attempting to download PDF using API base URL with download/pdf endpoint")
            endpoint = f"download/pdf{path_to_file}"
            download_url = f"{base_url}/{endpoint}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/pdf"
            }
            
            logger.info(f"Request URL: {download_url}")
            logger.info(f"Request headers: {headers}")
            
            response = requests.get(download_url, headers=headers, stream=True)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.warning(f"Error response content: {response.text[:500]}")
            
            response.raise_for_status()
            
            if response.headers.get('content-type') == 'application/pdf':
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"Downloaded PDF to {output_path} ({output_path.stat().st_size} bytes)")
                    return True
                else:
                    logger.warning(f"Downloaded PDF is empty: {output_path}")
            else:
                logger.warning(f"Response is not a PDF: {response.headers.get('content-type')}")
                logger.warning(f"Response content: {response.text[:500]}...")
                
        except Exception as e:
            logger.warning(f"Method 4 failed: {str(e)}")
            
        logger.error(f"All download methods failed for {path_to_file}")
    
    return False

async def main():
    """Main function"""
    load_dotenv()  # Load environment variables
    result = await test_pdf_download()
    return result

if __name__ == "__main__":
    asyncio.run(main()) 