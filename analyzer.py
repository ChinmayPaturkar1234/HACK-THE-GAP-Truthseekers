import re
from collections import Counter
import string

# Simple text processing functions to replace NLTK
def simple_tokenize(text):
    """Simple word tokenizer that splits on whitespace and removes punctuation."""
    # Remove punctuation
    for punct in string.punctuation:
        text = text.replace(punct, ' ')
    # Split on whitespace and filter out empty strings
    return [word.strip().lower() for word in text.split() if word.strip()]

def simple_sentence_tokenize(text):
    """Simple sentence tokenizer that splits on sentence-ending punctuation."""
    # Replace common sentence-ending punctuation with markers
    text = text.replace('. ', '.\n')
    text = text.replace('! ', '!\n')
    text = text.replace('? ', '?\n')
    # Split on newlines and filter out empty strings
    sentences = [s.strip() for s in text.split('\n') if s.strip()]
    return sentences

# Common English stopwords
STOPWORDS = set([
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 
    'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 
    'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 
    'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
    'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 
    'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 
    'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 
    'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 
    'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 
    'will', 'just', 'don', 'should', 'now'
])

def analyze_text(text):
    """
    Analyze text to extract various metrics and detect potential issues.
    
    Args:
        text (str): The text content to analyze
        
    Returns:
        dict: Analysis results including metrics and detected issues
    """
    # Initialize result dictionary
    results = {
        'word_count': 0,
        'sentence_count': 0,
        'avg_sentence_length': 0,
        'complexity_score': 0,
        'topics': [],
        'clickbait_score': 0,
        'all_caps_percentage': 0,
        'question_percentage': 0,
        'exclamation_percentage': 0,
    }
    
    # Check if text is empty
    if not text or len(text.strip()) == 0:
        return results
    
    # Tokenize text
    sentences = simple_sentence_tokenize(text)
    results['sentence_count'] = len(sentences)
    
    # Process text for word count and other metrics
    clean_text = text.lower()
    words = simple_tokenize(clean_text)
    results['word_count'] = len(words)
    
    # Calculate average sentence length
    if results['sentence_count'] > 0:
        results['avg_sentence_length'] = results['word_count'] / results['sentence_count']
    
    # Calculate text complexity (using average word length as a simple metric)
    if results['word_count'] > 0:
        avg_word_length = sum(len(word) for word in words) / results['word_count']
        results['complexity_score'] = min(10, avg_word_length * 1.5) # Scale to a 0-10 range
    
    # Get topics/themes through keyword frequency
    filtered_words = [word for word in words if word not in STOPWORDS and len(word) > 2]
    
    word_freq = Counter(filtered_words)
    topics = [word for word, freq in word_freq.most_common(5) if freq > 1]
    results['topics'] = topics if topics else ["Unknown"]
    
    # Calculate clickbait metrics
    clickbait_phrases = [
        "you won't believe", "mind blowing", "shocking", "jaw-dropping", "unbelievable",
        "incredible", "insane", "wow", "amazing", "secret", "trick", "this is why",
        "here's why", "you need to know", "can change your life", "will make you"
    ]
    
    headline = sentences[0] if sentences else ""
    headline_lower = headline.lower()
    
    # Check for clickbait phrases
    clickbait_score = 0
    for phrase in clickbait_phrases:
        if phrase in headline_lower:
            clickbait_score += 0.2
    
    # Check for all caps words
    all_caps_count = sum(1 for word in headline.split() if word.isupper() and len(word) > 1)
    results['all_caps_percentage'] = all_caps_count / max(1, len(headline.split()))
    clickbait_score += results['all_caps_percentage'] * 0.3
    
    # Check for questions in headline
    if "?" in headline:
        results['question_percentage'] = headline.count("?") / len(headline)
        clickbait_score += results['question_percentage'] * 0.2
    
    # Check for exclamations in headline
    if "!" in headline:
        results['exclamation_percentage'] = headline.count("!") / len(headline)
        clickbait_score += results['exclamation_percentage'] * 0.3
    
    # Normalize clickbait score to be between 0 and 1
    results['clickbait_score'] = min(1.0, clickbait_score)
    
    return results

def extract_keywords(text, num_keywords=15):
    """
    Extract the most significant keywords from the text.
    
    Args:
        text (str): The text to extract keywords from
        num_keywords (int): The number of keywords to extract
        
    Returns:
        list: List of extracted keywords
    """
    # Check if text is empty
    if not text or len(text.strip()) == 0:
        return []
    
    # Tokenize and clean text
    words = simple_tokenize(text.lower())
    
    # Remove stop words and digits
    filtered_words = [word for word in words if word not in STOPWORDS 
                     and len(word) > 2
                     and not word.isdigit()]
    
    # Count word frequencies
    word_freq = Counter(filtered_words)
    
    # Extract the most common words as keywords
    keywords = [word for word, _ in word_freq.most_common(num_keywords)]
    
    return keywords

def extract_claims(text):
    """
    Extract potential claims from text that could be fact-checked.
    
    Args:
        text (str): The text to extract claims from
        
    Returns:
        list: List of potential claims
    """
    # Check if text is empty
    if not text or len(text.strip()) == 0:
        return []
    
    sentences = simple_sentence_tokenize(text)
    claims = []
    
    # Enhanced patterns that might indicate a claim
    claim_indicators = [
        # Attribution patterns
        r'(according to|said|says|claimed|reported|confirmed|announced|revealed|stated|disclosed|asserted)',
        # Superlative statements
        r'(is|are|was|were) (the first|the best|the largest|the only|the highest|the lowest|the most|the least)',
        # Statistical claims
        r'(increased|decreased|grew|fell|rose|declined|jumped|plunged|surged|dropped) by',
        # Numerical claims
        r'(more than|less than|about|approximately|nearly|over|under|around) \d+',
        # Quantifier statements
        r'(all|none|most|many|some|few|several) of the',
        # Research claims
        r'(research|study|survey|poll|analysis|data) (shows|indicates|suggests|confirms|proves|reveals|demonstrates|finds)',
        # Factual assertions
        r'(in fact|actually|certainly|definitely|undoubtedly|clearly|obviously)',
        # Causal claims
        r'(causes|leads to|results in|because of|due to|consequently)',
        # Temporal claims with specific dates
        r'\b(in|on|during) (January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(st|nd|rd|th)?, \d{4}\b',
        # Claims with percentages
        r'\d+(\.\d+)?\s?(%|percent)',
        # Claims with specific names of people or organizations
        r'(President|CEO|Director|Secretary|Minister|Dr\.|Professor|Sen\.|Rep\.) [A-Z][a-z]+ [A-Z][a-z]+',
        # Policy statements
        r'(policy|law|regulation|legislation|bill|act) (requires|mandates|prohibits|allows|restricts)'
    ]
    
    # Check each sentence for claim patterns
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for pattern in claim_indicators:
            if re.search(pattern, sentence_lower):
                # Clean the claim
                clean_claim = sentence.strip()
                if len(clean_claim) > 20 and len(clean_claim.split()) <= 50:  # Substantial but not too long
                    claims.append(clean_claim)
                    break
    
    # Deduplicate and filter claims
    unique_claims = []
    seen_starts = set()
    
    for claim in claims:
        # Use first 5 words as a signature to avoid near-duplicate claims
        start_signature = ' '.join(claim.split()[:5]).lower()
        if start_signature not in seen_starts:
            seen_starts.add(start_signature)
            unique_claims.append(claim)
    
    # If no claims were found with patterns, use the most informative sentences
    if not unique_claims:
        # Calculate information density with enhanced metrics
        sentence_scores = []
        for sentence in sentences:
            if len(sentence.split()) > 5 and len(sentence.split()) <= 40:  # Reasonable length
                # Score based on multiple factors
                word_count = len(sentence.split())
                contains_numbers = bool(re.search(r'\d', sentence))
                contains_quotes = bool(re.search(r'[""].*?[""]', sentence))
                contains_names = bool(re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', sentence))
                
                # Calculate a composite score
                score = word_count * (
                    1.5 if contains_numbers else 1.0) * (
                    1.3 if contains_quotes else 1.0) * (
                    1.2 if contains_names else 1.0
                )
                sentence_scores.append((sentence, score))
        
        # Sort sentences by score and take top 3
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        unique_claims = [sent for sent, _ in sentence_scores[:3]]
    
    # If still no claims, use the first few sentences
    if not unique_claims and sentences:
        for sentence in sentences[:3]:
            if len(sentence) > 30:
                unique_claims.append(sentence)
    
    return unique_claims[:5]  # Return up to 5 most likely claims
