import os
import csv
import pandas as pd
import urllib.parse
from utils.scraper import get_article_metadata

# Cache for unreliable sources to avoid repeated file reads
_unreliable_sources_cache = None

def calculate_credibility_score(text_analysis, sentiment_analysis, fact_check_results, url=None):
    """
    Calculate an overall credibility score based on various analyses.
    
    Args:
        text_analysis (dict): Results from text analysis
        sentiment_analysis (dict): Results from sentiment analysis
        fact_check_results (dict): Results from fact checking
        url (str, optional): The URL of the content, if available
        
    Returns:
        tuple: (overall_score, score_breakdown)
    """
    # Initialize score components
    score_components = {
        'Source Credibility': 0,
        'Content Analysis': 0,
        'Fact Checking': 0,
        'Bias Assessment': 0
    }
    
    # 1. Source Credibility (0-100)
    if url:
        source_score = evaluate_source_credibility(url)
    else:
        # If no URL, give neutral source score
        source_score = 50
    
    score_components['Source Credibility'] = source_score
    
    # 2. Content Analysis (0-100)
    content_score = evaluate_content(text_analysis)
    score_components['Content Analysis'] = content_score
    
    # 3. Fact Checking (0-100)
    fact_check_score = evaluate_fact_checks(fact_check_results)
    score_components['Fact Checking'] = fact_check_score
    
    # 4. Bias Assessment (0-100)
    bias_score = 100 - (sentiment_analysis['bias_score'] * 10)  # Convert 0-10 to 0-100 and invert
    score_components['Bias Assessment'] = bias_score
    
    # Calculate weighted average for final score
    weights = {
        'Source Credibility': 0.25,
        'Content Analysis': 0.25,
        'Fact Checking': 0.30,
        'Bias Assessment': 0.20
    }
    
    overall_score = sum(score_components[component] * weights[component] 
                       for component in score_components)
    
    # Round to nearest integer
    overall_score = round(overall_score)
    
    return overall_score, score_components

def evaluate_source_credibility(url):
    """
    Evaluate the credibility of the source based on its domain.
    
    Args:
        url (str): URL of the content
        
    Returns:
        float: Source credibility score (0-100)
    """
    try:
        # Get domain from URL
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check against list of known reliable and unreliable sources
        reliable_score = check_source_reliability(domain)
        
        # Get metadata for additional factors
        try:
            metadata = get_article_metadata(url)
            metadata_factors = evaluate_metadata_factors(metadata)
        except Exception as e:
            print(f"Metadata extraction error: {str(e)}")
            # If metadata extraction fails, use neutral values
            metadata_factors = 0
        
        # Combine domain reliability and metadata factors
        source_score = reliable_score + metadata_factors
        
        # Ensure score is within 0-100 range
        return max(0, min(100, source_score))
    except Exception as e:
        print(f"Source credibility evaluation error: {str(e)}")
        return 50  # Return neutral score on error

def check_source_reliability(domain):
    """
    Check if the domain is in lists of known reliable and unreliable sources.
    
    Args:
        domain (str): The domain to check
        
    Returns:
        float: Base reliability score (0-90)
    """
    # Highly reliable news sources - major established outlets with strong fact-checking
    highly_reliable = [
        'reuters.com', 'apnews.com', 'npr.org', 'bbc.com', 'bbc.co.uk',
        'economist.com', 'wsj.com', 'nytimes.com', 'washingtonpost.com',
        'time.com', 'theatlantic.com', 'nature.com', 'science.org',
        'scientificamerican.com', 'nationalgeographic.com', 'newyorker.com',
        'ft.com', 'theguardian.com', 'independent.co.uk', 'pbs.org',
        'cspan.org', 'france24.com', 'dw.com'
    ]
    
    # Generally reliable news sources - established outlets with good reporting standards
    generally_reliable = [
        'cnn.com', 'nbcnews.com', 'abcnews.go.com', 'cbsnews.com', 'usatoday.com',
        'latimes.com', 'chicagotribune.com', 'politico.com', 'thehill.com',
        'bloomberg.com', 'businessinsider.com', 'forbes.com', 'fortune.com',
        'vox.com', 'slate.com', 'axios.com', 'fivethirtyeight.com', 'propublica.org',
        'aljazeera.com', 'msnbc.com', 'foxnews.com', 'cnbc.com', 'nymag.com',
        'thedailybeast.com', 'buzzfeednews.com', 'motherjones.com'
    ]
    
    # Mixed reliability sources - varying quality depending on content
    mixed_reliability = [
        'medium.com', 'huffpost.com', 'vice.com', 'salon.com', 'newsweek.com',
        'dailymail.co.uk', 'nypost.com', 'washingtontimes.com', 'reason.com',
        'spectator.co.uk', 'theintercept.com', 'nationalreview.com'
    ]
    
    # Check if domain exists in data file of unreliable sources
    unreliable_score = check_unreliable_sources(domain)
    if unreliable_score is not None:
        return unreliable_score
    
    # Check against lists of reliable sources
    if domain in highly_reliable:
        return 90  # Very high reliability
    elif domain in generally_reliable:
        return 80  # High reliability
    elif domain in mixed_reliability:
        return 60  # Mixed reliability
    
    # For unknown sources, give a neutral score
    return 50

def check_unreliable_sources(domain):
    """
    Check if domain is in the unreliable sources data file.
    Uses a cache to avoid repeated file reads.
    
    Args:
        domain (str): The domain to check
        
    Returns:
        float or None: Score if found, None otherwise
    """
    global _unreliable_sources_cache
    
    # Path to unreliable sources data file
    file_path = 'data/unreliable_sources.csv'
    
    # Check if file exists
    if not os.path.exists(file_path):
        return None
    
    # Load the unreliable sources into cache if not already loaded
    if _unreliable_sources_cache is None:
        try:
            _unreliable_sources_cache = {}
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header row
                for row in reader:
                    if row and len(row) >= 2:
                        _unreliable_sources_cache[row[0].lower()] = row[1].lower()
        except Exception as e:
            print(f"Error loading unreliable sources database: {str(e)}")
            _unreliable_sources_cache = {}
    
    # Check the domain against the cache
    if domain.lower() in _unreliable_sources_cache:
        category = _unreliable_sources_cache[domain.lower()]
        
        # Map categories to reliability scores
        if category in ["fake", "hate"]:
            return 0  # Completely unreliable
        elif category in ["conspiracy"]:
            return 5  # Almost completely unreliable
        elif category in ["questionable", "junksci"]:
            return 20  # Very low reliability
        elif category in ["political"]:
            return 30  # Low reliability with political bias
        elif category in ["satire"]:
            return 10  # Satire sources (very low for factual reporting)
        else:
            return 25  # Default for any other unreliable category
    
    return None

def evaluate_metadata_factors(metadata):
    """
    Evaluate additional factors from article metadata.
    
    Args:
        metadata (dict): Metadata from the article
        
    Returns:
        float: Score adjustment based on metadata factors (-10 to +10)
    """
    score_adjustment = 0
    
    # Check for author presence (articles with named authors tend to be more credible)
    if metadata.get('author') and len(metadata.get('author', '')) > 3:
        score_adjustment += 5
    
    # Check for publication date (having a date is a positive sign)
    if metadata.get('date'):
        score_adjustment += 5
    
    return score_adjustment

def evaluate_content(text_analysis):
    """
    Evaluate content based on text analysis results.
    
    Args:
        text_analysis (dict): Results from text analysis
        
    Returns:
        float: Content quality score (0-100)
    """
    score = 50  # Start with neutral score
    
    # Factor 1: Text complexity (higher complexity can indicate more substantial content)
    complexity = text_analysis.get('complexity_score', 0)
    if complexity > 7:
        score += 10  # High complexity
    elif complexity > 5:
        score += 5   # Medium complexity
    
    # Factor 2: Clickbait detection
    clickbait_score = text_analysis.get('clickbait_score', 0)
    if clickbait_score > 0.7:
        score -= 30  # Heavy clickbait
    elif clickbait_score > 0.4:
        score -= 15  # Moderate clickbait
    
    # Factor 3: Text length/substance
    word_count = text_analysis.get('word_count', 0)
    if word_count > 800:
        score += 15  # Longer articles tend to be more substantive
    elif word_count > 400:
        score += 10
    elif word_count < 100:
        score -= 15  # Very short content is often less credible
    
    # Ensure score is within 0-100 range
    return max(0, min(100, score))

def evaluate_fact_checks(fact_check_results):
    """
    Evaluate fact checks to determine content accuracy.
    
    Args:
        fact_check_results (dict): Results from fact checking
        
    Returns:
        float: Fact check score (0-100)
    """
    claims = fact_check_results.get('claims', [])
    
    # If no claims were checked, assign a neutral score
    if not claims:
        return 50
    
    # Calculate score based on claim ratings
    total_score = 0
    
    for claim in claims:
        rating = claim.get('rating', '').lower()
        
        # Map ratings to scores
        if rating in ['true', 'correct', 'accurate', 'confirmed']:
            total_score += 100
        elif rating in ['mostly true', 'mostly correct', 'mostly accurate']:
            total_score += 80
        elif rating in ['half true', 'partly true', 'mixed']:
            total_score += 50
        elif rating in ['mostly false', 'mostly incorrect']:
            total_score += 20
        elif rating in ['false', 'incorrect', 'inaccurate']:
            total_score += 0
        elif rating in ['unverified', 'unclear']:
            total_score += 50
        elif rating in ['misleading']:
            total_score += 30
        elif rating in ['lacks context']:
            total_score += 40
        else:
            # Default for unknown ratings
            total_score += 50
    
    # Average score across all claims
    avg_score = total_score / len(claims)
    
    return avg_score
