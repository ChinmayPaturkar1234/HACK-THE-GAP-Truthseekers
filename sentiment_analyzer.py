import re
import math
from collections import Counter

# Simple lexicon-based sentiment analysis
class SimpleSentimentAnalyzer:
    def __init__(self):
        # Basic sentiment lexicons
        self.positive_words = {
            'good', 'great', 'excellent', 'wonderful', 'fantastic', 'amazing', 'love', 'best',
            'positive', 'happy', 'joy', 'joyful', 'beautiful', 'nice', 'superior', 'perfect',
            'impressive', 'remarkable', 'outstanding', 'superb', 'brilliant', 'awesome',
            'delightful', 'favorable', 'encouraging', 'beneficial', 'successful', 'helpful',
            'pleasant', 'enjoyable', 'satisfying', 'terrific', 'exceptional', 'marvelous',
            'praise', 'recommended', 'glad', 'pleased', 'excited', 'thrilled', 'blessing',
            'fortunate', 'celebrated', 'acclaimed', 'worthy', 'magnificent', 'splendid'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'horrible', 'awful', 'poor', 'disappointing', 'hate', 'worst',
            'negative', 'sad', 'unfortunately', 'ugly', 'inferior', 'defective', 'inadequate',
            'unimpressive', 'mediocre', 'subpar', 'sucks', 'pathetic', 'atrocious', 'appalling',
            'dreadful', 'lousy', 'unpleasant', 'unfavorable', 'discouraging', 'harmful',
            'unsuccessful', 'unhelpful', 'frustrating', 'annoying', 'disappointing', 'horrific',
            'criticism', 'problem', 'issue', 'challenging', 'broken', 'damaged', 'fails',
            'unfortunate', 'displeased', 'angry', 'upset', 'concerning', 'adverse', 'tragic'
        }
        
        self.intensifiers = {
            'very', 'extremely', 'incredibly', 'absolutely', 'completely', 'highly', 
            'especially', 'particularly', 'utterly', 'really', 'totally', 'thoroughly',
            'exceedingly', 'remarkably', 'truly', 'so', 'such', 'quite', 'enormously'
        }
        
        self.negators = {
            'not', 'no', 'never', 'none', 'neither', 'nor', 'nothing', 'nowhere',
            'hardly', 'scarcely', 'barely', "doesn't", "isn't", "aren't", "wasn't",
            "weren't", "haven't", "hasn't", "hadn't", "won't", "wouldn't", "don't",
            "can't", "couldn't", "shouldn't", "mightn't", "mustn't"
        }
    
    def simple_tokenize(self, text):
        """Simple word tokenizer that splits on whitespace and removes punctuation."""
        # Convert to lowercase
        text = text.lower()
        # Replace punctuation with spaces
        for char in '.,;:!?()[]{}"\'':
            text = text.replace(char, ' ')
        # Split on whitespace and filter out empty strings
        return [word.strip() for word in text.split() if word.strip()]
        
    def polarity_scores(self, text):
        """Calculate sentiment polarity scores for a text."""
        if not text:
            return {'pos': 0.0, 'neg': 0.0, 'neu': 1.0, 'compound': 0.0}
            
        tokens = self.simple_tokenize(text)
        if not tokens:
            return {'pos': 0.0, 'neg': 0.0, 'neu': 1.0, 'compound': 0.0}
            
        word_count = len(tokens)
        positive_count = 0
        negative_count = 0
        
        # Process text with negation handling
        i = 0
        while i < len(tokens):
            word = tokens[i]
            
            # Check for negation
            negated = False
            if i > 0 and tokens[i-1] in self.negators:
                negated = True
                
            # Check for intensifiers
            intensified = False
            intensity_factor = 1.0
            if i > 0 and tokens[i-1] in self.intensifiers:
                intensified = True
                intensity_factor = 1.8
            
            # Apply sentiment scoring with negation and intensification
            if word in self.positive_words:
                if negated:
                    negative_count += 1 * intensity_factor
                else:
                    positive_count += 1 * intensity_factor
            elif word in self.negative_words:
                if negated:
                    positive_count += 0.5  # Negated negative is less positive than explicit positive
                else:
                    negative_count += 1 * intensity_factor
                    
            i += 1
            
        # Calculate scores
        pos_score = positive_count / max(1, word_count)
        neg_score = negative_count / max(1, word_count)
        
        # Calculate neutrality
        neu_score = 1.0 - (pos_score + neg_score)
        neu_score = max(0.0, min(1.0, neu_score))
        
        # Calculate compound score (-1 to 1)
        if pos_score + neg_score == 0:
            compound = 0
        else:
            compound = (pos_score - neg_score) / (pos_score + neg_score)
        
        # Scale scores to match VADER-like values
        return {
            'pos': min(1.0, pos_score),
            'neg': min(1.0, neg_score),
            'neu': neu_score,
            'compound': compound
        }

def analyze_sentiment(text):
    """
    Analyze sentiment and detect bias in the text.
    Optimized for news content with emotion analysis.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Sentiment analysis results
    """
    # Initialize sentiment analyzer
    sia = SimpleSentimentAnalyzer()
    
    # Initialize results
    results = {
        'compound_score': 0,
        'positivity': 0,
        'negativity': 0,
        'neutrality': 0,
        'is_biased': False,
        'bias_score': 0,
        'emotional_words': [],
        'persuasive_words': [],
        'loaded_language': [],
        # Additional emotion categories for news content
        'emotion_categories': {
            'fear': 0,
            'anger': 0,
            'joy': 0, 
            'sadness': 0,
            'surprise': 0,
            'disgust': 0
        }
    }
    
    # Check if text is empty
    if not text or len(text.strip()) == 0:
        return results
    
    # Get sentiment scores from our custom analyzer
    sentiment_scores = sia.polarity_scores(text)
    
    results['compound_score'] = sentiment_scores['compound']
    results['positivity'] = sentiment_scores['pos']
    results['negativity'] = sentiment_scores['neg']
    results['neutrality'] = sentiment_scores['neu']
    
    # Detect bias through various indicators
    bias_indicators = detect_bias_indicators(text)
    
    # Calculate overall bias score (0-10 scale)
    bias_score = calculate_bias_score(sentiment_scores, bias_indicators)
    results['bias_score'] = bias_score
    results['is_biased'] = bias_score > 6.0  # Threshold for considering biased
    
    # Add bias indicators to results
    results.update(bias_indicators)
    
    # Add emotion analysis specifically for news content
    results['emotion_categories'] = analyze_news_emotions(text)
    
    return results

def analyze_news_emotions(text):
    """
    Analyze emotions in news text using lexicon-based approach.
    Returns proportions of different emotions found in the text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Emotion category proportions
    """
    # Create emotion lexicons - optimized for news content
    emotion_lexicons = {
        'fear': [
            'fear', 'afraid', 'scared', 'terrified', 'frightened', 'panic', 'terror', 'horror', 'dread', 'alarmed',
            'anxious', 'worried', 'concerned', 'threatening', 'danger', 'dangerous', 'warning', 'crisis', 'threat',
            'risk', 'emergency', 'suspicious', 'vulnerable', 'insecure', 'unsafe', 'uncertain', 'uneasy'
        ],
        'anger': [
            'anger', 'angry', 'furious', 'outraged', 'rage', 'fury', 'irritated', 'annoyed', 'hostile', 'mad',
            'hatred', 'hate', 'resent', 'incensed', 'enraged', 'protest', 'confrontation', 'clash', 'controversy',
            'tensions', 'dispute', 'conflict', 'aggressive', 'violent', 'attacked', 'condemned', 'criticized'
        ],
        'joy': [
            'joy', 'happy', 'happiness', 'delighted', 'pleased', 'glad', 'elated', 'jubilant', 'celebrated',
            'cheered', 'optimistic', 'hopeful', 'positive', 'thrilled', 'excited', 'triumph', 'victorious',
            'success', 'achievement', 'progress', 'gain', 'benefit', 'improvement', 'recovery', 'breakthrough'
        ],
        'sadness': [
            'sad', 'sorrow', 'grief', 'mourning', 'unhappy', 'depressed', 'depression', 'disappointing',
            'disappointed', 'upset', 'regret', 'miserable', 'heartbroken', 'devastated', 'suffering', 'victim',
            'tragedy', 'tragic', 'loss', 'lost', 'failure', 'failed', 'defeat', 'setback', 'crisis', 'damage'
        ],
        'surprise': [
            'surprise', 'surprised', 'astonished', 'amazed', 'shocking', 'shocked', 'unexpected', 'sudden',
            'remarkable', 'extraordinary', 'unprecedented', 'unusual', 'rare', 'mystery', 'mysterious', 
            'breakthrough', 'discovery', 'revealed', 'uncovered', 'bombshell', 'twist', 'dramatic', 'unexpected'
        ],
        'disgust': [
            'disgust', 'disgusting', 'repulsive', 'revolting', 'outrageous', 'offensive', 'scandal', 'scandalous',
            'controversial', 'unethical', 'immoral', 'corrupt', 'corruption', 'violation', 'misconduct',
            'inappropriate', 'accusations', 'alleged', 'controversy', 'criticized', 'condemned', 'criticized'
        ]
    }
    
    # Convert to lowercase
    text_lower = text.lower()
    
    # Count word matches for each emotion
    emotion_counts = {emotion: 0 for emotion in emotion_lexicons}
    total_emotion_words = 0
    
    for emotion, words in emotion_lexicons.items():
        # Count occurrences of each emotion word
        for word in words:
            # Use word boundary to match whole words
            pattern = r'\b' + re.escape(word) + r'\b'
            count = len(re.findall(pattern, text_lower))
            emotion_counts[emotion] += count
            total_emotion_words += count
    
    # Calculate proportions
    if total_emotion_words > 0:
        emotion_proportions = {emotion: count / max(1, total_emotion_words) 
                              for emotion, count in emotion_counts.items()}
    else:
        # Default to neutral distribution if no emotions detected
        emotion_proportions = {emotion: 0.167 for emotion in emotion_lexicons}
    
    # Ensure some level of emotion is always shown (for better visualization)
    min_value = 0.05
    for emotion in emotion_proportions:
        if emotion_proportions[emotion] < min_value:
            emotion_proportions[emotion] = min_value
    
    # Normalize to ensure sum is 1.0
    total = sum(emotion_proportions.values())
    emotion_proportions = {k: v/total for k, v in emotion_proportions.items()}
    
    return emotion_proportions

def detect_bias_indicators(text):
    """
    Detect various indicators of bias in text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Dictionary of bias indicators
    """
    results = {
        'emotional_words': [],
        'persuasive_words': [],
        'loaded_language': [],
        'weasel_words': [],
        'subjective_intensifiers': 0,
        'opinion_phrases': 0
    }
    
    # Lists of indicator words
    emotional_words = [
        'horrible', 'terrible', 'amazing', 'awesome', 'fantastic', 'wonderful',
        'awful', 'disgusting', 'outrageous', 'shocking', 'appalling', 'astonishing',
        'incredible', 'unbelievable', 'stunning', 'remarkable', 'extraordinary',
        'heartbreaking', 'devastating', 'tragic', 'catastrophic', 'horrific'
    ]
    
    persuasive_words = [
        'clearly', 'obviously', 'undoubtedly', 'certainly', 'definitely',
        'absolutely', 'unquestionably', 'indisputably', 'without doubt',
        'surely', 'evidently', 'plainly', 'of course', 'no doubt',
        'naturally', 'inevitably', 'incontrovertibly'
    ]
    
    loaded_language = [
        'radical', 'extreme', 'fanatical', 'fundamentalist', 'terrorist',
        'illegal', 'alien', 'invader', 'regime', 'dictator', 'tyranny', 
        'freedom fighter', 'patriot', 'hero', 'coward', 'traitor', 'enemy'
    ]
    
    weasel_words = [
        'some', 'many', 'most', 'experts say', 'critics claim', 
        'people think', 'it is reported', 'it is believed', 'sources say',
        'allegedly', 'reportedly', 'apparently', 'seemingly', 'possibly',
        'it has been said', 'it is said'
    ]
    
    intensifiers = [
        'very', 'extremely', 'incredibly', 'highly', 'exceptionally',
        'terribly', 'absolutely', 'completely', 'totally', 'utterly',
        'really', 'quite', 'thoroughly', 'entirely', 'fully', 'deeply'
    ]
    
    # Use our simple tokenizer
    tokenizer = SimpleSentimentAnalyzer()
    tokens = tokenizer.simple_tokenize(text.lower())
    
    # Count emotional words
    for word in emotional_words:
        if word in tokens:
            results['emotional_words'].append(word)
    
    # Count persuasive words
    for word in persuasive_words:
        if word in tokens:
            results['persuasive_words'].append(word)
    
    # Count loaded language
    for word in loaded_language:
        if word in tokens:
            results['loaded_language'].append(word)
    
    # Count weasel words/phrases
    for word in weasel_words:
        if word.lower() in text.lower():
            results['weasel_words'].append(word)
    
    # Count subjective intensifiers
    results['subjective_intensifiers'] = sum(1 for word in intensifiers if word in tokens)
    
    # Count opinion phrases
    opinion_patterns = [
        r'\b(I|we) (think|believe|feel|suggest|argue|assert)\b',
        r'\bin my opinion\b',
        r'\bin my view\b',
        r'\bmy understanding\b'
    ]
    
    results['opinion_phrases'] = sum(len(re.findall(pattern, text, re.IGNORECASE)) 
                                 for pattern in opinion_patterns)
    
    return results

def calculate_bias_score(sentiment_scores, bias_indicators):
    """
    Calculate an overall bias score based on sentiment and other indicators.
    
    Args:
        sentiment_scores (dict): VADER sentiment scores
        bias_indicators (dict): Dictionary of bias indicators
        
    Returns:
        float: Bias score (0-10 scale)
    """
    # Start with base score
    bias_score = 0
    
    # Add score based on sentiment extremity (more extreme = potentially more biased)
    sentiment_extremity = abs(sentiment_scores['compound']) * 2  # 0-2 range
    bias_score += sentiment_extremity
    
    # Add score based on number of emotional words (0-2 range)
    emotional_word_factor = min(2, len(bias_indicators['emotional_words']) * 0.4)
    bias_score += emotional_word_factor
    
    # Add score based on persuasive words (0-1.5 range)
    persuasive_word_factor = min(1.5, len(bias_indicators['persuasive_words']) * 0.3)
    bias_score += persuasive_word_factor
    
    # Add score based on loaded language (0-2 range)
    loaded_language_factor = min(2, len(bias_indicators['loaded_language']) * 0.5)
    bias_score += loaded_language_factor
    
    # Add score based on weasel words (0-1 range)
    weasel_word_factor = min(1, len(bias_indicators['weasel_words']) * 0.2)
    bias_score += weasel_word_factor
    
    # Add score based on intensifiers (0-0.75 range)
    intensifier_factor = min(0.75, bias_indicators['subjective_intensifiers'] * 0.15)
    bias_score += intensifier_factor
    
    # Add score based on opinion phrases (0-0.75 range)
    opinion_factor = min(0.75, bias_indicators['opinion_phrases'] * 0.25)
    bias_score += opinion_factor
    
    # Normalize to 0-10 scale
    bias_score = (bias_score / 10) * 10
    
    return bias_score
