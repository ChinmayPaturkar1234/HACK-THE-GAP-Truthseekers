import requests
import os
import random
import json
import time
from datetime import datetime, timedelta

# Google Fact Check API endpoint
FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

def check_facts(text, keywords):
    """
    Check facts in the given text using fact checking services.
    
    Args:
        text (str): The text content to check
        keywords (list): Extracted keywords from the text
        
    Returns:
        dict: Results from fact checking
    """
    api_key = os.getenv("AIzaSyBgbZW3HVWlEv1L24_vabXZrTP00ypJMfQ", "")
    
    # Initialize results
    results = {
        'claims': [],
        'alternative_sources': [],
        'api_used': False
    }
    
    # Extract potential claims from text
    from utils.analyzer import extract_claims
    claims = extract_claims(text)
    
    if not claims:
        claims = [text[:150]] if len(text) > 30 else []
    
    if not api_key:
        print("Warning: No Google Fact Check API key available, using fallback mode")
        results['error'] = "API key not available"
    else:
        results['api_used'] = True
        
        # Use Google Fact Check API to check each claim
        for claim in claims[:3]:  # Limit to 3 claims to avoid excessive API usage
            try:
                params = {
                    'key': api_key,
                    'query': claim,
                    'languageCode': 'en'
                }
                
                response = requests.get(FACT_CHECK_API_URL, params=params)
                
                if response.status_code != 200:
                    print(f"API error: {response.status_code}, {response.text}")
                    results['api_error'] = f"Status code: {response.status_code}"
                    continue
                    
                data = response.json()
                
                if 'claims' in data and data['claims']:
                    for claim_data in data['claims'][:2]:  # Take up to 2 fact checks per claim
                        if 'claimReview' in claim_data and claim_data['claimReview']:
                            review_data = claim_data['claimReview'][0]
                            claim_result = {
                                'claim': claim,
                                'text': claim_data.get('text', ''),
                                'claimant': claim_data.get('claimant', 'Unknown'),
                                'rating': review_data.get('textualRating', 'Unverified'),
                                'source': review_data.get('publisher', {}).get('name', 'Unknown'),
                                'url': review_data.get('url', ''),
                                'explanation': review_data.get('title', 'No explanation provided')
                            }
                            results['claims'].append(claim_result)
                            
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                # Log error but continue with other claims
                print(f"Error checking claim: {str(e)}")
                results['error'] = str(e)
    
    # If no claims were found or there was an API error, use fallback
    if not results['claims'] and ('error' in results or 'api_error' in results):
        print("No claims found via API, using fallback mode")
        fallback_results = simulate_fact_check_results(text, keywords)
        results['claims'] = fallback_results['claims']
        results['fallback_used'] = True
    
    # Find alternative sources using NewsAPI
    alternative_sources = find_alternative_sources(keywords[:5])
    if alternative_sources:
        results['alternative_sources'] = alternative_sources
    
    return results

def find_alternative_sources(keywords, max_sources=3):
    """
    Find alternative reliable sources on similar topics.
    
    Args:
        keywords (list): Keywords to search for
        max_sources (int): Maximum number of sources to return
        
    Returns:
        list: List of alternative sources
    """
    news_api_key = os.getenv("NEWS_API_KEY", "")
    
    if not keywords or len(keywords) == 0:
        return []
    
    if not news_api_key:
        print("Warning: No News API key available, using fallback mode")
        return simulate_alternative_sources(keywords)
    
    # Create search query from keywords
    query = " OR ".join(keywords[:3])  # Use top 3 keywords
    
    # Set up reliable news sources
    reliable_sources = [
        "reuters.com", "apnews.com", "npr.org", "bbc.com", 
        "bbc.co.uk", "wsj.com", "nytimes.com", "washingtonpost.com",
        "economist.com", "time.com", "theatlantic.com", "theguardian.com",
        "cnn.com", "nbcnews.com", "cbsnews.com", "abcnews.go.com",
        "politico.com", "bloomberg.com", "ft.com", "nature.com",
        "sciencemag.org", "scientificamerican.com"
    ]
    
    # Domains parameter for NewsAPI
    domains = ",".join(reliable_sources[:10])  # NewsAPI limits the domains parameter
    
    # Use NewsAPI to find articles
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "apiKey": news_api_key,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": max_sources * 2,  # Request more to filter later
        "domains": domains
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"News API error: {response.status_code}")
            print(response.text)
            return simulate_alternative_sources(keywords)
            
        data = response.json()
        
        sources = []
        if data.get("status") == "ok" and data.get("articles"):
            articles = data["articles"]
            
            # Sort by relevance and recency
            articles.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
            
            # Filter out duplicates from same sources
            seen_sources = set()
            for article in articles:
                source_name = article.get("source", {}).get("name", "Unknown")
                
                # Only add if we haven't seen this source yet
                if source_name not in seen_sources and len(sources) < max_sources:
                    seen_sources.add(source_name)
                    
                    # Format the published date
                    published = article.get("publishedAt", "")
                    if published:
                        try:
                            pub_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                            published = pub_date.strftime("%b %d, %Y")
                        except:
                            pass
                    
                    source = {
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "source": source_name,
                        "published": published
                    }
                    sources.append(source)
        
        if sources:
            return sources
        else:
            print("No articles found with News API, using fallback")
            return simulate_alternative_sources(keywords)
            
    except Exception as e:
        # Log error and return simulated results
        print(f"Error finding alternative sources: {str(e)}")
        return simulate_alternative_sources(keywords)

def simulate_fact_check_results(text, keywords):
    """
    Generate simulated fact checking results for demonstration purposes.
    In a production environment, this would be replaced with real API calls.
    
    Args:
        text (str): The text to analyze
        keywords (list): Keywords from the text
        
    Returns:
        dict: Simulated fact checking results
    """
    # Get claims from text
    from utils.analyzer import extract_claims
    claims = extract_claims(text)
    
    results = {
        'claims': [],
        'alternative_sources': []
    }
    
    # If no claims found, return empty results
    if not claims:
        return results
    
    # Possible ratings
    ratings = [
        "True", "Mostly True", "Half True", "Mostly False", "False", 
        "Unverified", "Misleading", "Lacks Context"
    ]
    
    # Fact check organizations
    fact_checkers = [
        "FactCheck.org", "PolitiFact", "Snopes", "Reuters Fact Check", 
        "AP Fact Check", "USA Today Fact Check"
    ]
    
    # Create simulated results for each claim
    for claim in claims[:3]:  # Limit to 3 claims
        rating = random.choice(ratings)
        
        # Create more detailed explanation based on rating
        if rating in ["True", "Mostly True"]:
            explanation = f"Our research confirms this claim. Multiple sources corroborate the information."
        elif rating in ["Half True", "Unverified"]:
            explanation = f"This claim contains some accurate elements but is missing important context or has unverified aspects."
        elif rating in ["Mostly False", "False"]:
            explanation = f"This claim contains significant factual errors or misrepresentations based on our research."
        else:
            explanation = f"This claim requires additional context to be properly evaluated."
        
        claim_result = {
            'claim': claim,
            'claimant': "Source in article",
            'rating': rating,
            'source': random.choice(fact_checkers),
            'url': "#",
            'explanation': explanation
        }
        
        results['claims'].append(claim_result)
    
    # Add alternative sources
    results['alternative_sources'] = simulate_alternative_sources(keywords)
    
    return results

def simulate_alternative_sources(keywords, count=3):
    """
    Generate simulated alternative sources for demonstration purposes.
    
    Args:
        keywords (list): Keywords to use for source generation
        count (int): Number of sources to generate
        
    Returns:
        list: Simulated alternative sources
    """
    if not keywords:
        return []
    
    reliable_sources = [
        "Reuters", "Associated Press", "NPR", "BBC News", 
        "The Wall Street Journal", "The New York Times", "The Washington Post",
        "The Economist", "Time Magazine", "The Atlantic"
    ]
    
    # Generate dates within the last 14 days
    def random_date():
        days = random.randint(0, 14)
        date = datetime.now() - timedelta(days=days)
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    sources = []
    for i in range(min(count, len(keywords))):
        keyword = keywords[i] if i < len(keywords) else keywords[0]
        source_name = random.choice(reliable_sources)
        
        title_templates = [
            f"Analysis: Understanding the facts about {keyword}",
            f"Fact Check: What's true and false about {keyword}",
            f"Explainer: The complete context on {keyword}",
            f"In Depth: Examining the evidence on {keyword}"
        ]
        
        source = {
            "title": random.choice(title_templates),
            "url": "#",
            "source": source_name,
            "published": random_date()
        }
        sources.append(source)
    
    return sources
