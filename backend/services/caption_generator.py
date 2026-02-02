"""
Caption and Hashtag Generator Service
Generates social media ready captions and hashtags for video clips
"""
import re
from typing import List, Dict


def generate_caption(
    title: str,
    transcript_snippet: str,
    metadata: Dict = None
) -> str:
    """
    Generate a social media ready caption from clip metadata
    
    Args:
        title: Clip title
        transcript_snippet: Transcript text of the clip
        metadata: Optional metadata dict with categories, keywords, etc.
    
    Returns:
        Caption text ready for social media post
    """
    if not title and not transcript_snippet:
        return "Check out this amazing clip! 🎬"
    
    # Use title as the main caption
    caption = title if title else ""
    
    # Add engaging context from transcript if available
    if transcript_snippet:
        # Clean and truncate transcript
        snippet = _clean_transcript(transcript_snippet)
        
        # If title doesn't exist or is too short, use transcript as main content
        if not caption or len(caption) < 20:
            caption = snippet[:150]  # Max 150 chars for main caption
        else:
            # Add transcript as supporting text if it adds value
            if len(snippet) > 30 and snippet.lower() not in caption.lower():
                caption = f"{caption}\n\n{snippet[:100]}"
    
    # Add emoji based on content categories
    if metadata and 'categories' in metadata:
        categories = metadata['categories']
        if 'importance' in categories:
            caption = f"⚠️ {caption}"
        elif 'revelation' in categories:
            caption = f"💡 {caption}"
        elif 'teaching' in categories:
            caption = f"📚 {caption}"
        elif 'summary' in categories:
            caption = f"📌 {caption}"
    
    # Add call to action
    caption += "\n\n💬 What do you think? Comment below!"
    
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
