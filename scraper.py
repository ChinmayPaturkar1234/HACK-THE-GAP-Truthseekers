import trafilatura
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

def extract_text_from_url(url):
    """
    Extract the main content text from a URL.
    
    Args:
        url (str): The URL of the webpage to extract text from
        
    Returns:
        str: The extracted text content
    """
    # Check if the URL is valid
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # First try using trafilatura for extraction
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text and len(text) > 100:  # Ensure we got meaningful content
                return text
        
        # Fallback to requests + BeautifulSoup if trafilatura fails
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script, style elements and comments
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
            
        # Try to find the main content
        main_content = None
        
        # Try common article containers
        for container in ['article', 'main', '.content', '#content', '.post', '.article', '.story']:
            if main_content:
                break
                
            if container.startswith('.') or container.startswith('#'):
                elements = soup.select(container)
            else:
                elements = soup.find_all(container)
                
            if elements:
                main_content = elements[0].get_text(separator=' ', strip=True)
        
        # If no main content found, use the body
        if not main_content or len(main_content) < 100:
            main_content = soup.body.get_text(separator=' ', strip=True)
        
        # Clean up the text
        main_content = re.sub(r'\s+', ' ', main_content)
        
        return main_content
        
    except Exception as e:
        raise Exception(f"Failed to extract content: {str(e)}")

def get_article_metadata(url):
    """
    Extract metadata from an article URL, such as title, author, publication date.
    
    Args:
        url (str): The URL of the article
        
    Returns:
        dict: A dictionary containing metadata
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        metadata = {
            'title': '',
            'author': '',
            'date': '',
            'publisher': '',
        }
        
        # Get title
        if soup.title:
            metadata['title'] = soup.title.string
        
        # Try meta tags for other data
        for meta in soup.find_all('meta'):
            property = meta.get('property', '').lower()
            name = meta.get('name', '').lower()
            content = meta.get('content', '')
            
            if property == 'og:site_name' or name == 'publisher':
                metadata['publisher'] = content
            elif property == 'article:published_time' or name == 'publication-date':
                metadata['date'] = content
            elif property == 'og:title' and not metadata['title']:
                metadata['title'] = content
            elif name == 'author' or property == 'article:author':
                metadata['author'] = content
        
        # Get domain as fallback publisher
        if not metadata['publisher']:
            parsed_url = urllib.parse.urlparse(url)
            metadata['publisher'] = parsed_url.netloc.replace('www.', '')
            
        return metadata
        
    except Exception as e:
        # Return empty metadata if extraction fails
        return {
            'title': '',
            'author': '',
            'date': '',
            'publisher': '',
        }
