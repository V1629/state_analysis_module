"""
Multilingual Emotion Detector
Uses AnasAlokla/multilingual_go_emotions model
Supports English, Hindi, and Hinglish
"""

import os
import sys
from huggingface_hub import InferenceClient
from typing import Dict, List, Optional

# ==========================================
# CONFIGURATION
# ==========================================
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()
HF_TOKEN = os.getenv('hf_token')

if not HF_TOKEN:
    print("❌ Error: HF_TOKEN environment variable not set.")
    print("Please run: export HF_TOKEN='your_token_here'")
    sys.exit(1)

try:
    client = InferenceClient(
        provider="hf-inference",
        api_key=HF_TOKEN,
    )
    print("✅ HuggingFace client initialized successfully")
except Exception as e:
    print(f"❌ Error initializing HuggingFace client: {e}")
    sys.exit(1)

MODEL_NAME = "AnasAlokla/multilingual_go_emotions"


# ==========================================
# EMOTION DETECTION FUNCTIONS
# ==========================================

def classify_emotions(text: str) -> Dict[str, float]:
    """
    Classify emotions in multilingual text
    
    Args:
        text: Input text (English, Hindi, or Hinglish)
    
    Returns:
        Dict: {emotion_name: probability} sorted by probability
    """
    if not text or len(text.strip()) == 0:
        print("⚠️  Empty text provided to emotion classifier")
        return {}
    
    try:
        classification_result = client.text_classification(
            text,
            model=MODEL_NAME,
        )
        
        if not classification_result:
            return {}
        
        # Convert list to dictionary
        emotions_with_scores = {}
        for emotion_item in classification_result:
            emotion_name = emotion_item['label']
            emotion_probability = emotion_item['score']
            emotions_with_scores[emotion_name] = emotion_probability
        
        return emotions_with_scores
    
    except Exception as error:
        print(f"❌ Error in emotion classification: {error}")
        return {}


def get_top_emotions(text: str, top_n: int = 5) -> Dict[str, float]:
    """
    Get top N emotions for text
    
    Args:
        text: Input text
        top_n: Number of top emotions to return
    
    Returns:
        Dict of top emotions sorted by score descending
    """
    try:
        all_emotions = classify_emotions(text)
        
        if not all_emotions:
            return {}
        
        # Sort by score descending
        sorted_emotion_pairs = sorted(all_emotions.items(), key=lambda pair: pair[1], reverse=True)
        
        # Return as dict with only top N emotions
        top_emotions = {emotion_name: emotion_score for emotion_name, emotion_score in sorted_emotion_pairs[:top_n]}
        return top_emotions
    
    except Exception as error:
        print(f"❌ Error getting top emotions: {error}")
        return {}


# ==========================================
# MAIN EXECUTION - TESTING
# ==========================================

if __name__ == "__main__":

    print("\n" + "="*60)
    print("🌍 Multilingual Emotion Detector")
    print("="*60)
    print(f"Model: {MODEL_NAME}")
    print("Supports: English, Hindi, Hinglish")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("📝 Enter text: ").strip()

            if user_input.lower() == "exit":
                print("\n👋 Goodbye!\n")
                break

            if not user_input:
                print("⚠️  Please enter some text.\n")
                continue

            detected_emotions = classify_emotions(user_input)

            if detected_emotions:
                # Sort emotions by score (descending)
                sorted_emotion_pairs = sorted(detected_emotions.items(), key=lambda pair: pair[1], reverse=True)

                print("\n🔎 Emotion Predictions:")
                for emotion_name, emotion_score in sorted_emotion_pairs[:5]:  # Top 5 emotions
                    visual_bar = "█" * int(emotion_score * 20)
                    print(f"   {emotion_name:20s} │ {visual_bar:20s} │ {emotion_score:.4f}")
            else:
                print("⚠️  No emotions detected.")

            print("-" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except Exception as error:
            print(f"❌ Error: {str(error)}")
            print("Please try again.\n")