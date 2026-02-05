#!/usr/bin/env python
"""Test script for improved caption and hashtag generation"""

from services.caption_generator import generate_caption_with_ai, generate_hashtags_with_ai

# Test transcript
transcript = "This is absolutely crazy! I just discovered the most shocking secret that nobody talks about. The way this works is completely unbelievable. I literally can't believe what just happened. You won't believe your eyes when you see this. This is trending right now and everyone should know about it."

print("=" * 70)
print("SMART CAPTION & HASHTAG GENERATION TEST")
print("=" * 70)

print("\n📝 CAPTION GENERATION TEST")
print("-" * 70)

styles = ["engaging", "professional", "casual", "funny", "viral"]
for style in styles:
    caption = generate_caption_with_ai(transcript, style=style)
    print(f"\n[{style.upper():12}] {caption}")

print("\n" + "=" * 70)
print("🏷️  HASHTAG GENERATION TEST")
print("-" * 70)

hashtags = generate_hashtags_with_ai(transcript)
print(f"\n{hashtags}")

print("\n" + "=" * 70)
print("✓ Test completed successfully!")
print("=" * 70)
