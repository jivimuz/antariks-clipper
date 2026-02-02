"""
Enhanced highlight clip generation with improved scoring for long videos.
Supports detecting multiple punchlines/segments with dynamic durations.
"""
import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from config import MIN_CLIP_DURATION, MAX_CLIP_DURATION, IDEAL_CLIP_DURATION, DEFAULT_CLIP_COUNT

logger = logging.getLogger(__name__)

# Enhanced hook keywords (Indonesian + English) with categories
HOOK_KEYWORDS = {
    'importance': [
        "ini penting", "yang penting", "kuncinya", "serius", "harus tahu",
        "important", "must know", "critical", "essential", "crucial"
    ],
    'revelation': [
        "gila", "ternyata", "rahasia", "trik", "tips", "cara terbaik",
        "secret", "amazing", "incredible", "shocking", "revelation", "turns out"
    ],
    'summary': [
        "jadi intinya", "kesimpulannya", "yang paling", "pokoknya",
        "in conclusion", "to summarize", "the point is", "basically"
    ],
    'teaching': [
        "cara", "bagaimana", "tutorial", "langkah", "pro tip",
        "how to", "step by step", "game changer", "breakthrough"
    ]
}

# Question patterns that often indicate interesting content
QUESTION_PATTERNS = [
    r'\b(apa|kenapa|mengapa|bagaimana|kapan|dimana|siapa)\b',
    r'\b(what|why|how|when|where|who)\b',
    r'\?'
]

def detect_keyword_categories(text: str) -> Dict[str, int]:
    """Detect which keyword categories are present in text"""
    text_lower = text.lower()
    categories = {}
    
    for category, keywords in HOOK_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > 0:
            categories[category] = matches
    
    return categories


def score_segment(text: str, start: float, end: float, total_duration: float, 
                  segment_index: int = 0, total_segments: int = 1) -> Tuple[float, Dict[str, Any]]:
    """
    Enhanced scoring with detailed metadata for better selection.
    
    Returns:
        Tuple of (score, metadata)
        
    Scoring breakdown (100 points max):
    - Hook keywords: up to 35 points (weighted by category)
    - Content quality: up to 25 points (word density, questions)
    - Duration fit: up to 25 points (flexible, not just ideal)
    - Position bonus: up to 15 points (favor beginning/end segments)
    """
    score = 0.0
    metadata = {
        'keywords': [],
        'categories': [],
        'has_question': False,
        'word_count': 0,
        'unique_word_ratio': 0.0
    }
    
    text_lower = text.lower()
    clip_duration = end - start
    
    # 1. Hook keywords with category weighting (up to 35 points)
    keyword_categories = detect_keyword_categories(text)
    metadata['categories'] = list(keyword_categories.keys())
    
    # Weight different categories differently
    category_weights = {
        'importance': 10,
        'revelation': 9,
        'summary': 8,
        'teaching': 7
    }
    
    keyword_score = 0
    for category, count in keyword_categories.items():
        weight = category_weights.get(category, 5)
        keyword_score += min(count * weight, weight * 2)  # Cap per category
    
    score += min(keyword_score, 35)
    
    # 2. Content quality analysis (up to 25 points)
    words = re.findall(r'\b\w+\b', text_lower)
    metadata['word_count'] = len(words)
    
    if words:
        unique_ratio = len(set(words)) / len(words)
        metadata['unique_word_ratio'] = unique_ratio
        score += unique_ratio * 15  # Up to 15 points for vocabulary diversity
        
        # Word count bonus (sweet spot: 50-150 words for engaging content)
        word_count = len(words)
        if 50 <= word_count <= 150:
            score += 5
        elif 30 <= word_count <= 200:
            score += 3
    
    # Check for questions (indicates engagement)
    for pattern in QUESTION_PATTERNS:
        if re.search(pattern, text_lower):
            metadata['has_question'] = True
            score += 5
            break
    
    # 3. Duration flexibility (up to 25 points)
    # Instead of penalizing deviation from ideal, reward good duration ranges
    if MIN_CLIP_DURATION <= clip_duration <= MAX_CLIP_DURATION:
        # Flexible scoring based on ranges
        if 20 <= clip_duration <= 45:  # Sweet spot
            score += 25
        elif 15 <= clip_duration <= 60:  # Good range
            score += 20
        else:  # Acceptable but not ideal
            score += 15
    
    # 4. Position bonus (up to 15 points)
    # Favor content from different parts of the video to get diverse highlights
    if total_segments > 0:
        position_ratio = segment_index / total_segments
        
        # Strong starts and endings are often memorable
        if position_ratio < 0.15 or position_ratio > 0.85:
            score += 10
        # Middle sections can also be good
        elif 0.4 <= position_ratio <= 0.6:
            score += 8
        else:
            score += 5
    
    return score, metadata

def generate_candidates(segments: List[Dict[str, Any]], total_duration: float,
                       adaptive_step: bool = True) -> List[Dict[str, Any]]:
    """
    Generate highlight clip candidates with improved algorithm for long videos.
    
    Args:
        segments: Transcript segments
        total_duration: Total video duration
        adaptive_step: If True, use adaptive stepping for long videos (faster)
    
    Returns:
        List of candidate clips with scores and metadata
    """
    candidates = []
    total_segments = len(segments)
    
    # For very long videos (>1 hour), use adaptive stepping to avoid O(n^2) complexity
    # Step size of 3 reduces candidate generation from O(n²) to O(n²/9) while maintaining
    # adequate coverage for hour+ videos (still generates thousands of candidates)
    is_long_video = total_duration > 3600  # 1 hour
    step_size = 3 if is_long_video and adaptive_step else 1
    
    logger.info(f"Generating candidates for video of {total_duration/60:.1f} minutes")
    logger.info(f"Using step size: {step_size} (adaptive: {adaptive_step})")
    
    i = 0
    while i < total_segments:
        # Calculate relative position for scoring
        segment_position = i
        
        # Try to build clips of various lengths
        # For long videos, we sample fewer combinations but still get good coverage
        max_j = min(i + 150, total_segments + 1)  # Limit window size for performance
        
        for j in range(i + 1, max_j):
            start = segments[i]['start']
            end = segments[j - 1]['end']
            duration = end - start
            
            # Check duration constraints
            if duration < MIN_CLIP_DURATION:
                continue
            if duration > MAX_CLIP_DURATION:
                break
            
            # Combine text
            text = ' '.join(seg['text'] for seg in segments[i:j])
            
            # Score this candidate with enhanced metadata
            score, metadata = score_segment(
                text, start, end, total_duration,
                segment_index=segment_position,
                total_segments=total_segments
            )
            
            candidates.append({
                'start': start,
                'end': end,
                'duration': duration,
                'score': score,
                'text': text,
                'metadata': metadata,
                'segment_count': j - i
            })
        
        i += step_size
    
    logger.info(f"Generated {len(candidates)} candidate clips")
    return candidates

def remove_overlaps(candidates: List[Dict[str, Any]], top_n: int, 
                   min_gap: float = 10.0) -> List[Dict[str, Any]]:
    """
    Remove overlapping clips, keeping highest scored ones.
    
    Args:
        candidates: List of candidate clips
        top_n: Maximum number of clips to select
        min_gap: Minimum gap in seconds between clips (default 10s)
    
    Returns:
        List of non-overlapping clips sorted by start time
    """
    # Sort by score descending
    sorted_candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
    
    selected = []
    for candidate in sorted_candidates:
        # Check if it overlaps with any selected clip (with min_gap buffer)
        overlaps = False
        for sel in selected:
            # Check for time overlap with buffer:
            # Candidate must either end before selected starts (with gap)
            # OR start after selected ends (no gap needed at start check)
            if not (candidate['end'] <= sel['start'] - min_gap or 
                   candidate['start'] >= sel['end']):
                overlaps = True
                break
        
        if not overlaps:
            selected.append(candidate)
            if len(selected) >= top_n:
                break
    
    # Sort by start time
    selected_sorted = sorted(selected, key=lambda x: x['start'])
    
    logger.info(f"Selected {len(selected_sorted)} non-overlapping clips from {len(candidates)} candidates")
    return selected_sorted

def calculate_dynamic_clip_count(total_duration: float, base_count: int = DEFAULT_CLIP_COUNT) -> int:
    """
    Calculate appropriate number of clips based on video duration.
    For longer videos, generate more clips to capture more highlights.
    
    Args:
        total_duration: Video duration in seconds
        base_count: Base number of clips (default from config)
    
    Returns:
        Recommended number of clips
    """
    duration_minutes = total_duration / 60
    
    if duration_minutes <= 10:
        return max(base_count, 5)
    elif duration_minutes <= 30:
        return max(base_count, 12)
    elif duration_minutes <= 60:
        return max(base_count, 20)
    elif duration_minutes <= 120:  # 2 hours
        return max(base_count, 30)
    else:  # Very long videos (>2 hours)
        # Scale with duration but cap at reasonable limit
        return min(int(duration_minutes / 3), 50)


def generate_highlights(transcript: Dict[str, Any], 
                       top_n: Optional[int] = None,
                       adaptive: bool = True) -> List[Dict[str, Any]]:
    """
    Generate highlight clips from transcript with enhanced detection for long videos.
    
    Args:
        transcript: Transcript data with segments and duration
        top_n: Number of clips to generate (None = auto-calculate based on duration)
        adaptive: Use adaptive algorithms for long videos
    
    Returns:
        List of highlight clips with metadata
    """
    try:
        segments = transcript.get('segments', [])
        total_duration = transcript.get('duration', 0)
        
        if not segments:
            logger.warning("No segments in transcript")
            return []
        
        # Auto-calculate clip count if not specified
        if top_n is None:
            top_n = calculate_dynamic_clip_count(total_duration)
            logger.info(f"Auto-calculated clip count: {top_n} for {total_duration/60:.1f} min video")
        
        logger.info(f"=" * 60)
        logger.info(f"HIGHLIGHT GENERATION START")
        logger.info(f"Video duration: {total_duration/60:.1f} minutes ({total_duration:.1f}s)")
        logger.info(f"Transcript segments: {len(segments)}")
        logger.info(f"Target clips: {top_n}")
        logger.info(f"Adaptive mode: {adaptive}")
        logger.info(f"=" * 60)
        
        # Generate all candidates
        candidates = generate_candidates(segments, total_duration, adaptive_step=adaptive)
        
        if not candidates:
            logger.warning("No valid candidates generated")
            return []
        
        # Log candidate statistics
        scores = [c['score'] for c in candidates]
        durations = [c['duration'] for c in candidates]
        logger.info(f"Candidate statistics:")
        logger.info(f"  Score range: {min(scores):.1f} - {max(scores):.1f}")
        logger.info(f"  Average score: {sum(scores)/len(scores):.1f}")
        logger.info(f"  Duration range: {min(durations):.1f}s - {max(durations):.1f}s")
        logger.info(f"  Average duration: {sum(durations)/len(durations):.1f}s")
        
        # Remove overlaps and select top N
        highlights = remove_overlaps(candidates, top_n)
        
        if not highlights:
            logger.warning("No highlights after overlap removal")
            return []
        
        logger.info(f"Selected {len(highlights)} final highlights")
        
        # Format output with enhanced metadata
        result = []
        for i, hl in enumerate(highlights):
            # Create a descriptive title based on metadata
            title_parts = [f"Highlight {i + 1}"]
            if hl['metadata'].get('categories'):
                # Add category hint to title
                category = hl['metadata']['categories'][0]
                if category == 'importance':
                    title_parts.append("(Important)")
                elif category == 'revelation':
                    title_parts.append("(Key Point)")
                elif category == 'teaching':
                    title_parts.append("(Tutorial)")
            
            result.append({
                'start': hl['start'],
                'end': hl['end'],
                'duration': hl['duration'],
                'score': hl['score'],
                'title': ' '.join(title_parts),
                'snippet': hl['text'][:200] + ('...' if len(hl['text']) > 200 else ''),
                'metadata': {
                    'word_count': hl['metadata']['word_count'],
                    'categories': hl['metadata']['categories'],
                    'has_question': hl['metadata']['has_question'],
                    'segment_count': hl['segment_count']
                }
            })
            
            logger.info(f"  Clip {i+1}: {hl['start']:.1f}s - {hl['end']:.1f}s "
                       f"(dur: {hl['duration']:.1f}s, score: {hl['score']:.1f})")
        
        logger.info(f"=" * 60)
        logger.info(f"HIGHLIGHT GENERATION COMPLETE")
        logger.info(f"=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"Generate highlights error: {e}", exc_info=True)
        return []
