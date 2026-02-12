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

HF_TOKEN = "please_insert_an_acess_token_mam!!!"

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
        result = client.text_classification(
            text,
            model=MODEL_NAME,
        )
        
        if not result:
            return {}
        
        # Convert list to dictionary
        emotions_dict = {}
        for item in result:
            emotions_dict[item['label']] = item['score']
        
        return emotions_dict
    
    except Exception as e:
        print(f"❌ Error in emotion classification: {e}")
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
        emotions = classify_emotions(text)
        
        if not emotions:
            return {}
        
        # Sort by score descending
        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        
        # Return as dict
        return {k: v for k, v in sorted_emotions[:top_n]}
    
    except Exception as e:
        print(f"❌ Error getting top emotions: {e}")
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
                print("\n�� Goodbye!\n")
                break

            if not user_input:
                print("⚠️  Please enter some text.\n")
                continue

            emotions = classify_emotions(user_input)

            if emotions:
                # Sort emotions by score (descending)
                sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)

                print("\n🔎 Emotion Predictions:")
                for emotion, score in sorted_emotions[:5]:  # Top 5 emotions
                    bar = "█" * int(score * 20)
                    print(f"   {emotion:20s} │ {bar:20s} │ {score:.4f}")
            else:
                print("⚠️  No emotions detected.")

            print("-" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print("Please try again.\n")