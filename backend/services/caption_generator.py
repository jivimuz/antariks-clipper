"""
Caption and Hashtag Generator Service (No API, Smart Template-Based)
Generates viral-worthy social media captions and hashtags using
intelligent analysis of transcript content and viral patterns
"""
import re
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Enhanced caption templates with more viral patterns
CAPTION_TEMPLATES = {
    "engaging": [
        "Wait for it... {key_phrase}! 👀",
        "This is insane! {key_phrase}",
        "Did you see that? {key_phrase}",
        "Mind blown 🤯 {key_phrase}",
        "You won't believe this: {key_phrase}",
        "Just discovered: {key_phrase}! Must watch 🎥",
        "I can't unhear this 👇 {key_phrase}",
        "POV: {key_phrase} just happened",
        "{key_phrase} is unmatched 🔥",
    ],
    "professional": [
        "Key insight: {key_phrase}",
        "Important takeaway: {key_phrase}",
        "Learn why: {key_phrase}",
        "Understanding {key_phrase} is crucial",
        "Expert perspective on {key_phrase}",
        "{key_phrase} - Here's what you need to know",
        "Breaking down {key_phrase}",
        "Everything about {key_phrase}",
    ],
    "casual": [
        "Yo, {key_phrase} is so cool!",
        "Just vibing with {key_phrase}",
        "Check it: {key_phrase} 🔥",
        "{key_phrase} hit different, ngl",
        "Can we talk about {key_phrase}?",
        "{key_phrase} be like... 😂",
        "No bc {key_phrase} >>>",
        "Not {key_phrase} being iconic rn",
    ],
    "funny": [
        "{key_phrase}... and I'm done 💀",
        "POV: You're watching {key_phrase}",
        "Me after learning about {key_phrase}: 😆",
        "{key_phrase} had me cackling 🤣",
        "Not {key_phrase} being this hilarious",
        "I can't stop laughing at {key_phrase}!",
        "Why is {key_phrase} so funny 😭",
        "The way {key_phrase} just—",
    ],
    "viral": [
        "WAIT... {key_phrase}!? 🚨",
        "This is CRAZY! {key_phrase} 😱",
        "NOBODY talks about {key_phrase} but SHOULD 🔥",
        "{key_phrase} just hit different... 💯",
        "HOW IS THIS REAL?? {key_phrase}",
        "IF YOU KNOW, YOU KNOW... {key_phrase} 👇",
        "This needs more attention: {key_phrase}",
        "Tell me {key_phrase} isn't trending yet 📈",
    ]
}

def _extract_key_phrase(transcript: str) -> str:
    """Extract most important key phrase from transcript - smarter analysis"""
    if not transcript:
        return "this amazing content"
    
    # Extended stop words list
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'being',
        'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'that', 'this',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'what', 'which', 'who', 'when', 'where', 'why', 'how', 'just',
        'very', 'so', 'as', 'all', 'each', 'every', 'both', 'some', 'no',
        'yang', 'ini', 'itu', 'dan', 'atau', 'untuk', 'dari', 'di', 'ke',
        'ada', 'adalah', 'jadi', 'bisa', 'akan', 'sudah', 'telah', 'dengan'
    }
    
    # Split transcript into sentences
    sentences = re.split(r'[.!?]+', transcript)
    
    # Find the most compelling sentence (usually has emotional/important words)
    emotional_keywords = {'amazing', 'incredible', 'unbelievable', 'crazy', 'wild',
                         'shocking', 'surprising', 'wow', 'epic', 'insane', 'mind',
                         'blown', 'secret', 'revealed', 'discovered', 'never', 'first',
                         'only', 'actually', 'really', 'seriously'}
    
    best_sentence = ""
    best_score = 0
    
    for sentence in sentences:
        if len(sentence.strip()) < 5:
            continue
        
        # Score sentence based on emotional content
        score = sum(1 for word in sentence.lower().split() if word in emotional_keywords)
        score += len([w for w in sentence.split() if len(w) > 6]) * 0.5  # Longer words = more specific
        
        if score > best_score:
            best_score = score
            best_sentence = sentence
    
    # Use best sentence or first sentence
    target_sentence = best_sentence if best_sentence else sentences[0]
    
    # Extract key words
    words = re.findall(r'\b\w+\b', target_sentence.lower())
    
    # Priority: Find longest meaningful phrase (2-3 words)
    for i in range(len(words) - 1, -1, -1):
        if words[i] not in stop_words and len(words[i]) > 4:
            # Try to grab 2-3 word phrase
            phrase_start = max(0, i - 1)
            phrase = ' '.join([w for w in words[phrase_start:i+2] if w not in stop_words])
            if phrase and len(phrase) > 3:
                return phrase
    
    # Fallback: Single meaningful word
    for word in words:
        if word not in stop_words and len(word) > 4:
            return word
    
    # Final fallback
    meaningful_words = [w for w in words if w not in stop_words][:3]
    return ' '.join(meaningful_words) if meaningful_words else "this"

def generate_caption_with_ai(
    transcript: str,
    style: str = "engaging",
    max_length: int = 150
) -> Optional[str]:
    """
    Generate engaging caption for social media using smart analysis
    
    Args:
        transcript: Video transcript text
        style: Caption style (engaging, professional, casual, funny, viral)
        max_length: Maximum caption length
        
    Returns:
        Generated caption or None if failed
    """
    if not transcript or len(transcript.strip()) < 5:
        return "Check this out! 👀"
    
    try:
        import random
        
        logger.info(f"Generating {style} caption from transcript: {transcript[:100]}...")
        
        # Get templates for this style
        templates = CAPTION_TEMPLATES.get(style, CAPTION_TEMPLATES["engaging"])
        
        # Extract key phrase using smart analysis
        key_phrase = _extract_key_phrase(transcript)
        
        # Select random template for variety (not always first)
        template = random.choice(templates)
        
        # Generate caption from template
        caption = template.format(key_phrase=key_phrase)
        
        # Ensure length limit
        if len(caption) > max_length:
            caption = caption[:max_length].rsplit(' ', 1)[0] + "..."
        
        logger.info(f"✓ Generated {style} caption: {caption[:80]}...")
        return caption
        
    except Exception as e:
        logger.error(f"Caption generation error: {e}", exc_info=True)
        return None


def _post_process_caption(caption: str, style: str) -> str:
    """Post-process caption based on style"""
    caption = caption.strip()
    
    # Add style-specific touches
    if style == "engaging":
        if not any(c in caption for c in ['!', '?']):
            caption += "! 👀"
    elif style == "funny":
        if not any(c in caption for c in ['😄', '😂', '🤣']):
            caption += " 😄"
    elif style == "viral":
        if caption and caption[0].islower():
            caption = caption[0].upper() + caption[1:]
        if not any(c in caption for c in ['!', '?']):
            caption += "!"
    elif style == "professional":
        if caption and caption[-1] not in '.!?':
            caption += "."
    
    return caption


def generate_hashtags_with_ai(transcript: str, count: int = 10) -> Optional[str]:
    """
    Generate relevant hashtags for social media using keyword extraction
    
    Args:
        transcript: Video transcript text
        count: Number of hashtags to generate
        
    Returns:
        Space-separated hashtags or None if failed
    """
    if not transcript:
        return None
    
    try:
        # Extract keywords manually from transcript
        hashtags = _extract_hashtags(transcript, count)
        
        if hashtags:
            logger.info(f"Generated hashtags: {hashtags}")
            return hashtags
        else:
            logger.error("Failed to generate hashtags")
            return None
            
    except Exception as e:
        logger.error(f"Hashtag generation error: {e}")
        return None


def _extract_hashtags(transcript: str, count: int = 10) -> str:
    """Extract viral-worthy hashtags using smart keyword analysis"""
    # Mandatory hashtags
    mandatory_tags = ["fyp", "viral"]
    
    # Viral-adjacent tags grouped by potential virality
    high_virality_tags = {
        "trending": ["trending", "trending2024", "viral", "moments"],
        "emotional": ["mindblown", "shocking", "revealed", "unbelievable", "wtf"],
        "urgency": ["mustsee", "mustwatch", "dontmiss", "foryou", "foryoupage"],
        "engagement": ["follow", "share", "comment", "engage", "reaction"],
        "time": ["now", "today", "latest", "news", "update"],
        "superlatives": ["best", "amazing", "incredible", "epic", "insane"]
    }
    
    # Extract meaningful keywords from transcript
    keywords = _extract_meaningful_keywords(transcript, count=8)
    
    # Analyze transcript sentiment/content type
    content_type = _analyze_content_type(transcript)
    
    # Build hashtag list with smart selection
    all_tags = mandatory_tags.copy()
    
    # Add content-type specific high-virality tags
    if content_type and content_type in high_virality_tags:
        virality_tags = high_virality_tags[content_type]
        all_tags.extend(virality_tags[:2])  # Add top 2 virality tags
    
    # Add extracted keywords
    all_tags.extend(keywords)
    
    # Add fallback viral tags if still under count
    if len(all_tags) < count:
        fallback_tags = ["reels", "shorts", "contentcreator", "explore", 
                        "explorepage", "foryoupage", "fy", "foryou"]
        for tag in fallback_tags:
            if tag not in all_tags and len(all_tags) < count:
                all_tags.append(tag)
    
    # Remove duplicates preserving order
    unique_tags = []
    seen = set()
    for tag in all_tags[:count]:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag_lower)
    
    # Format as hashtags
    formatted_tags = [f"#{tag}" for tag in unique_tags[:count]]
    return " ".join(formatted_tags)


def _analyze_content_type(transcript: str) -> Optional[str]:
    """Analyze transcript to determine content type for better hashtag selection"""
    text_lower = transcript.lower()
    
    # Trending/News indicators
    if any(word in text_lower for word in ['broke', 'revealed', 'shocking', 'just happened', 'reported', 'announce']):
        return "trending"
    
    # Emotional/Reaction indicators  
    if any(word in text_lower for word in ['crazy', 'insane', 'unbelievable', 'wow', 'omg', 'wait', 'mind']):
        return "emotional"
    
    # Urgency indicators
    if any(word in text_lower for word in ['must', 'dont miss', "can't", 'never', 'only']):
        return "urgency"
    
    # Engagement/Interactive indicators
    if any(word in text_lower for word in ['comment', 'tag', 'follow', 'subscribe', 'agree', 'disagree']):
        return "engagement"
    
    # Time-sensitive indicators
    if any(word in text_lower for word in ['today', 'tonight', 'now', 'breaking', 'latest']):
        return "time"
    
    # Superlative indicators
    if any(word in text_lower for word in ['best', 'worst', 'first', 'only', 'biggest', 'greatest']):
        return "superlatives"
    
    return None


def _extract_meaningful_keywords(transcript: str, count: int = 8) -> List[str]:
    """Extract the most meaningful keywords from transcript for hashtags"""
    if not transcript:
        return []
    
    # Stop words - expanded list
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'being',
        'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'that', 'this',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'what', 'which', 'who', 'when', 'where', 'why', 'how', 'just',
        'very', 'so', 'as', 'all', 'each', 'every', 'both', 'some', 'no',
        'yang', 'ini', 'itu', 'dan', 'atau', 'untuk', 'dari', 'di', 'ke',
        'ada', 'adalah', 'jadi', 'bisa', 'akan', 'sudah', 'telah', 'dengan',
        'sa', 'am', 'pm', 'like', 'really', 'actually', 'basically', 'literally'
    }
    
    # Extract words with frequency scoring
    words = re.findall(r'\b[\w]+\b', transcript.lower())
    
    # Score words by length and frequency
    word_scores = {}
    for word in words:
        clean_word = re.sub(r'[^a-z0-9]', '', word)
        
        # Skip if too short, or in stop words
        if len(clean_word) < 3 or clean_word in stop_words:
            continue
        
        # Score: longer words = more specific = better hashtags
        # Add frequency bonus
        length_score = len(clean_word) * 0.5
        frequency_bonus = (words.count(word) - 1) * 0.2
        
        word_scores[clean_word] = length_score + frequency_bonus
    
    # Sort by score and get top words
    top_keywords = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, score in top_keywords[:count]]
    
    return keywords


def generate_caption(
    title: str,
    transcript_snippet: str,
    metadata: Dict = None
) -> str:
    """
    Generate social media caption from audience/POV-3 perspective.
    
    Format: Descriptive, engaging caption written as if the viewer is describing 
    what they're watching or what's happening in the clip. More natural and relatable
    than direct transcript quotes.
    """
    if not title and not transcript_snippet:
        return "Check this out! 🎯"

    # Clean and process transcript for better caption
    description = ""
    if transcript_snippet:
        description = _clean_transcript(transcript_snippet).strip()
    
    # Create audience-perspective caption
    # Use opening phrases that make viewers feel like they're discovering something
    pov_templates = [
        "Watch this: {text}",
        "You won't believe what happens next: {text}",
        "Just discovered: {text}",
        "Listen to this: {text}",
        "Check out: {text}",
        "Here's something wild: {text}",
        "This just got interesting: {text}",
        "Take a look: {text}",
    ]
    
    # Get content snippet (first 60-80 chars for readability)
    if description:
        # Remove common filler words for better captions
        words = description.split()
        filtered = [w for w in words if len(w) > 2 and w.lower() not in ['the', 'and', 'but', 'just', 'that', 'this', 'with', 'from', 'have', 'been']]
        
        # Create short, punchy description
        if filtered:
            snippet = " ".join(filtered[:8])  # Limit to ~8 important words
        else:
            snippet = description[:70]
    elif title:
        snippet = title[:70]
    else:
        return "Check this out! 🎯"
    
    # Build caption from template
    import random
    template = random.choice(pov_templates)
    caption = template.format(text=snippet)
    
    # Limit length for video sync
    if len(caption) > 120:
        caption = caption[:120].rsplit(' ', 1)[0] + "..."
    
    # Add emoji based on metadata categories
    if metadata and 'categories' in metadata:
        categories = metadata['categories']
        emoji = None
        if 'importance' in categories:
            emoji = "⚠️"
        elif 'revelation' in categories:
            emoji = "💡"
        elif 'teaching' in categories:
            emoji = "📚"
        elif 'summary' in categories:
            emoji = "📌"
        
        if emoji and emoji not in caption:
            caption = f"{emoji} {caption}"

    return caption.strip()


def generate_hashtags(
    title: str = "",
    transcript_snippet: str = "",
    metadata: Dict = None,
    custom_tags: List[str] = None
) -> str:
    """
    Generate hashtags for social media post
    
    Args:
        title: Clip title
        transcript_snippet: Transcript text
        metadata: Optional metadata with categories
        custom_tags: Optional list of custom hashtags to include
    
    Returns:
        Space-separated hashtag string (e.g., "#fyp #viral #antariksclipper")
    """
    hashtags = []
    
    # Default hashtags (always include)
    default_tags = ["fyp", "viral", "antariksclipper"]
    hashtags.extend(default_tags)
    
    # Add category-based hashtags
    if metadata and 'categories' in metadata:
        categories = metadata['categories']
        if 'importance' in categories:
            hashtags.extend(["important", "mustknow", "tips"])
        if 'revelation' in categories:
            hashtags.extend(["amazing", "mindblown", "facts"])
        if 'teaching' in categories:
            hashtags.extend(["tutorial", "howto", "learn"])
        if 'summary' in categories:
            hashtags.extend(["summary", "recap", "highlights"])
    
    # Extract topic keywords from title
    if title:
        topic_keywords = _extract_keywords(title)
        hashtags.extend(topic_keywords[:3])  # Add top 3 keywords
    
    # Add content type hashtags
    hashtags.extend(["reels", "shorts", "contentcreator"])
    
    # Add custom tags if provided
    if custom_tags:
        hashtags.extend(custom_tags)
    
    # Remove duplicates while preserving order
    unique_hashtags = []
    seen = set()
    for tag in hashtags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_hashtags.append(tag_lower)
    
    # Format as hashtags (max 15 tags to avoid spam)
    formatted_tags = [f"#{tag}" for tag in unique_hashtags[:15]]
    
    return " ".join(formatted_tags)


def _clean_transcript(text: str) -> str:
    """Clean and format transcript text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove timestamps if present
    text = re.sub(r'\[\d+:\d+:\d+\]', '', text)
    
    # Capitalize first letter
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
    
    return text


def _extract_keywords(text: str) -> List[str]:
    """Extract potential hashtag keywords from text"""
    if not text:
        return []
    
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Split into words
    words = text.split()
    
    # Filter out common words (stopwords)
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'yang', 'ini', 'itu', 'dan', 'atau', 'untuk', 'dari', 'di', 'ke',
        'ada', 'adalah', 'jadi', 'bisa', 'akan', 'sudah', 'telah', 'dengan'
    }
    
    # Filter and get unique keywords (min length 3)
    keywords = [
        word for word in words
        if len(word) >= 3 and word not in stopwords
    ]
    
    # Remove duplicates while preserving order
    unique_keywords = []
    seen = set()
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords
