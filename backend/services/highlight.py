"""Highlight clip generation with scoring"""
import logging
import re
from typing import List, Dict, Any, Tuple
from config import MIN_CLIP_DURATION, MAX_CLIP_DURATION, IDEAL_CLIP_DURATION, DEFAULT_CLIP_COUNT

logger = logging.getLogger(__name__)

# Hook keywords (Indonesian + English)
HOOK_KEYWORDS = [
    "ini penting", "gila", "ternyata", "jadi intinya", "kuncinya", "serius",
    "yang paling", "rahasia", "trik", "tips", "cara terbaik", "harus tahu",
    "important", "secret", "amazing", "incredible", "shocking", "must know",
    "pro tip", "game changer", "breakthrough", "revelation"
]

def score_segment(text: str, start: float, end: float, duration: float) -> float:
    """
    Score a segment based on heuristics:
    - Hook keywords presence
    - Word density (unique words ratio)
    - Duration preference (closer to ideal = better)
    """
    score = 0.0
    text_lower = text.lower()
    
    # 1. Hook keywords (up to 30 points)
    keyword_matches = sum(1 for kw in HOOK_KEYWORDS if kw in text_lower)
    score += min(keyword_matches * 10, 30)
    
    # 2. Word density (up to 30 points)
    words = re.findall(r'\b\w+\b', text_lower)
    if words:
        unique_ratio = len(set(words)) / len(words)
        score += unique_ratio * 30
    
    # 3. Duration preference (up to 40 points)
    # Prefer clips closer to ideal duration
    clip_duration = end - start
    if clip_duration > 0:
        duration_diff = abs(clip_duration - IDEAL_CLIP_DURATION)
        # Normalize: ideal = 40 points, max diff = 0 points
        max_diff = max(IDEAL_CLIP_DURATION - MIN_CLIP_DURATION, 
                       MAX_CLIP_DURATION - IDEAL_CLIP_DURATION)
        duration_score = max(0, 40 * (1 - duration_diff / max_diff))
        score += duration_score
    
    return score

def generate_candidates(segments: List[Dict[str, Any]], total_duration: float) -> List[Dict[str, Any]]:
    """
    Generate highlight clip candidates from transcript segments
    Returns list of {start, end, score, text}
    """
    candidates = []
    
    i = 0
    while i < len(segments):
        # Try to build clips of various lengths
        for j in range(i + 1, len(segments) + 1):
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
            
            # Score this candidate
            score = score_segment(text, start, end, total_duration)
            
            candidates.append({
                'start': start,
                'end': end,
                'duration': duration,
                'score': score,
                'text': text
            })
        
        i += 1
    
    return candidates

def remove_overlaps(candidates: List[Dict[str, Any]], top_n: int) -> List[Dict[str, Any]]:
    """
    Remove overlapping clips, keeping highest scored ones
    """
    # Sort by score descending
    sorted_candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
    
    selected = []
    for candidate in sorted_candidates:
        # Check if it overlaps with any selected clip
        overlaps = False
        for sel in selected:
            # Check for time overlap
            if not (candidate['end'] <= sel['start'] or candidate['start'] >= sel['end']):
                overlaps = True
                break
        
        if not overlaps:
            selected.append(candidate)
            if len(selected) >= top_n:
                break
    
    # Sort by start time
    return sorted(selected, key=lambda x: x['start'])

def generate_highlights(transcript: Dict[str, Any], top_n: int = DEFAULT_CLIP_COUNT) -> List[Dict[str, Any]]:
    """
    Generate top N highlight clips from transcript
    Returns list of {start, end, score, title, snippet}
    """
    try:
        segments = transcript.get('segments', [])
        total_duration = transcript.get('duration', 0)
        
        if not segments:
            logger.warning("No segments in transcript")
            return []
        
        logger.info(f"Generating highlights from {len(segments)} segments")
        
        # Generate all candidates
        candidates = generate_candidates(segments, total_duration)
        logger.info(f"Generated {len(candidates)} candidates")
        
        # Remove overlaps and select top N
        highlights = remove_overlaps(candidates, top_n)
        logger.info(f"Selected {len(highlights)} highlights")
        
        # Format output
        result = []
        for i, hl in enumerate(highlights):
            result.append({
                'start': hl['start'],
                'end': hl['end'],
                'score': hl['score'],
                'title': f"Highlight {i + 1}",
                'snippet': hl['text'][:200] + ('...' if len(hl['text']) > 200 else '')
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Generate highlights error: {e}")
        return []
