"""
Direct Test Script for Orchestrator with Advanced State Tracking
Shows detailed state aggregation and frequency analysis

ROBUST VERSION: Handles incomplete orchestrator.py implementation
"""

import sys
from datetime import datetime
import time
from typing import Optional

print("\n" + "="*100)
print("🧪 ORCHESTRATOR TEST - Advanced Emotional State Analysis")
print("="*100)

# ==========================================================
# MODULE IMPORTS WITH ERROR HANDLING
# ==========================================================

print("\n📦 Importing modules...")

# Import orchestrator components
try:
    from orchestrator import (
        ImpactCalculator, 
        IncidentAnalysis, 
        IncidentDetector, 
        EmotionalStateOrchestrator
    )
    print("   ✅ orchestrator imported")
except ImportError as e:
    print(f"   ❌ Error importing orchestrator: {e}")
    print("   Make sure orchestrator.py is in the same directory")
    sys.exit(1)

# Import user profile
try:
    from user_profile import UserProfile, ALL_EMOTIONS, INITIAL_WEIGHTS
    print("   ✅ user_profile imported")
except ImportError as e:
    print(f"   ❌ Error importing user_profile: {e}")
    print("   Make sure user_profile.py is in the same directory")
    sys.exit(1)

# Import emotional detector
try:
    from emotional_detector import classify_emotions, get_top_emotions
    print("   ✅ emotional_detector imported")
except ImportError as e:
    print(f"   ❌ Error importing emotional_detector: {e}")
    print("   Make sure emotional_detector.py is in the same directory")
    sys.exit(1)

# Import temporal extractor
try:
    from temporal_extractor import TemporalExtractor
    print("   ✅ temporal_extractor imported")
except ImportError as e:
    print(f"   ❌ Error importing temporal_extractor: {e}")
    print("   Make sure temporal_extractor.py is in the same directory")
    sys.exit(1)

# Optional: Try importing logger (not critical)
logger = None
try:
    from chat_logger import ChatLogger
    logger = ChatLogger("chat_logs.xlsx")
    print("   ✅ ChatLogger initialized")
except Exception as e:
    print(f"   ⚠️  Logger not available: {e}")
    print("   Continuing without logging feature")

# ==========================================================
# CREATE ORCHESTRATOR & TEST IT
# ==========================================================

print("\n🔧 Creating orchestrator...")
try:
    orchestrator = EmotionalStateOrchestrator()
    print("   ✅ Orchestrator created")
except Exception as e:
    print(f"   ❌ Error creating orchestrator: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test if process_user_message is implemented
print("\n🔍 Testing orchestrator.process_user_message()...")
try:
    test_result = orchestrator.process_user_message(
        user_id="test_check",
        message="test message",
        reference_date=datetime.now(),
        writing_time=1.0
    )
    
    if test_result is None:
        print("   ❌ ERROR: process_user_message() returns None!")
        print("\n" + "="*100)
        print("CRITICAL: Your orchestrator.py file is incomplete!")
        print("="*100)
        print("\nThe process_user_message() method is not fully implemented.")
        print("It's missing the implementation body and returns None by default.")
        print("\nTo fix this:")
        print("1. Check orchestrator_completion.py for the missing code")
        print("2. Add the missing implementation to your orchestrator.py")
        print("3. The method should return an IncidentAnalysis object")
        print("\nExpected structure:")
        print("  - Step 1: Detect emotions (classify_emotions)")
        print("  - Step 2: Extract temporal references")
        print("  - Step 3: Initialize/get user profile")
        print("  - Step 4: Detect repeated incidents")
        print("  - Step 5: Calculate impact")
        print("  - Step 6: Get state impact multipliers")
        print("  - Step 7: Update user profile")
        print("  - Step 8: Generate analysis summary")
        print("  - Step 9: Return IncidentAnalysis object")
        print("\n" + "="*100)
        sys.exit(1)
    elif not isinstance(test_result, IncidentAnalysis):
        print(f"   ❌ ERROR: process_user_message() returns {type(test_result)}, expected IncidentAnalysis")
        sys.exit(1)
    else:
        print("   ✅ process_user_message() working correctly")
        # Clean up test profile
        if "test_check" in orchestrator.user_profiles:
            del orchestrator.user_profiles["test_check"]
except Exception as e:
    print(f"   ❌ Error testing orchestrator: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("   ✅ All checks passed - ready to start!\n")

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def display_emotions(emotions_dict: dict, top_n: int = 5):
    """Display emotions with visual bars"""
    if not emotions_dict:
        print("   No emotions detected")
        return
    
    sorted_emotions = sorted(
        emotions_dict.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    for rank, (emotion, score) in enumerate(sorted_emotions[:top_n], 1):
        bar = "█" * int(score * 25)
        print(f"   {rank}. {emotion:20s} │ {bar:25s} │ {score:.4f}")


def display_temporal_references(temp_ref: dict):
    """Display temporal references found in message"""
    if not temp_ref or not temp_ref.get('has_temporal_ref'):
        print("   No temporal references detected")
        return
    
    print(f"   Phrases found: {temp_ref.get('phrases_found', [])}")
    
    parsed_dates = temp_ref.get('parsed_dates', [])
    if parsed_dates:
        for parsed in parsed_dates[:3]:  # Show top 3
            print(f"\n   • {parsed.get('phrase', 'N/A')}")
            print(f"     Category: {parsed.get('age_category', 'unknown')}", end="")
            print(f" | Confidence: {parsed.get('confidence', 0.0):.2f}")


def display_current_states(profile: UserProfile):
    """Display current emotional states for all time periods"""
    print(f"\n💤 CURRENT EMOTIONAL STATE:")
    
    states = profile.get_all_states_with_top_emotions(top_n=2)
    
    for state_type in ['short_term', 'mid_term', 'long_term']:
        icon = "⚡" if state_type == "short_term" else ("📈" if state_type == "mid_term" else "🏛️")
        emotions = states.get(state_type, [])
        
        if not profile.is_state_activated(state_type):
            print(f"\n   {icon} {state_type.upper():12s}: ⏳ Not activated")
        elif emotions and len(emotions) > 0 and emotions[0][0] != "N/A":
            print(f"\n   {icon} {state_type.upper():12s}: {emotions[0][0]} ({emotions[0][1]:.4f})")
            if len(emotions) > 1 and emotions[1][0] != "N/A":
                print(f"      Secondary: {emotions[1][0]} ({emotions[1][1]:.4f})")
        else:
            print(f"\n   {icon} {state_type.upper():12s}: No emotions yet")


def display_activation_status(profile: UserProfile):
    """Display state activation status"""
    print(f"\n🔓 STATE ACTIVATION STATUS:")
    
    activation_info = profile.get_state_activation_info()
    
    for state_type in ['short_term', 'mid_term', 'long_term']:
        info = activation_info[state_type]
        status = "✅ ACTIVE" if info['is_active'] else "⏳ INACTIVE"
        
        icon = "⚡" if state_type == "short_term" else ("📈" if state_type == "mid_term" else "🏛️")
        
        print(f"\n   {icon} {state_type.upper():12s}: {status}")
        print(f"      Days: {profile.profile_age_days} | Messages: {profile.message_count}")


def display_frequency_analysis(profile: UserProfile):
    """Display emotion frequency analysis from history"""
    if not profile.message_history or len(profile.message_history) == 0:
        print("⚠️  No chat history yet\n")
        return
    
    print("\n" + "="*100)
    print("📊 EMOTION FREQUENCY ANALYSIS")
    print("="*100)
    
    top_emotions = profile.get_top_emotions_by_frequency(top_n=10)
    
    print(f"\nAnalyzing {len(profile.message_history)} messages...\n")
    print(f"{'Rank':<6} {'Emotion':<20} {'Avg Score':<15} {'Frequency':<15}")
    print("-" * 100)
    
    if top_emotions:
        max_freq = max([f[2] for f in top_emotions])
        for rank, (emotion, avg_score, frequency) in enumerate(top_emotions, 1):
            bar = "█" * int(frequency / max_freq * 30) if max_freq > 0 else ""
            print(f"{rank:<6} {emotion:<20} {avg_score:<15.4f} {frequency:<15} {bar}")
    else:
        print("No emotion data available yet")
    
    print("\n" + "="*100 + "\n")


def log_to_excel(logger, profile: UserProfile, analysis, message: str):
    """Log chat data to Excel file"""
    if not logger:
        return
    
    try:
        # Get detected emotions
        if analysis.emotions_detected:
            top_detected = max(analysis.emotions_detected.items(), key=lambda x: x[1])
            detected_emotion = top_detected[0]
            detected_score = top_detected[1]
        else:
            detected_emotion = ""
            detected_score = 0.0
        
        # Current state (from current message)
        log_data_current = {
            'short_term': [(detected_emotion, detected_score)] if detected_emotion else [],
            'mid_term': [(detected_emotion, detected_score)] if detected_emotion else [],
            'long_term': [(detected_emotion, detected_score)] if detected_emotion else [],
        }
        
        # Profile state (from accumulated profile)
        log_data_profile = {
            'short_term': profile.get_top_emotions_or_placeholder('short_term', 1),
            'mid_term': profile.get_top_emotions_or_placeholder('mid_term', 1),
            'long_term': profile.get_top_emotions_or_placeholder('long_term', 1),
        }
        
        # Get activation info
        activation_info = profile.get_state_activation_info()
        
        # Log to Excel
        logger.log_chat(
            message=message,
            impact_score=analysis.impact_score,
            current_state=log_data_current,
            profile_state=log_data_profile,
            activation_status=activation_info,
            profile_age_days=profile.profile_age_days,
            message_count=profile.message_count
        )
        print(f"\n✅ Logged to chat_logs.xlsx")
    except Exception as log_error:
        print(f"\n⚠️  Logging failed: {log_error}")


# ==========================================================
# MAIN INTERACTION LOOP
# ==========================================================

print("="*100)
print("INSTRUCTIONS:")
print("="*100)
print("• Enter a message to analyze")
print("• Type 'profile' to view full profile with advanced state info")
print("• Type 'history' to see emotion frequency analysis")
print("• Type 'states' to see current activation status")
print("• Type 'exit' to quit\n")

message_count = 0
user_id = "test_user"

while True:
    try:
        # Measure input time
        start_time = time.perf_counter()
        command = input("💬 You: ").strip()
        end_time = time.perf_counter()
        
        if not command:
            continue
        
        # Handle commands
        if command.lower() == 'exit':
            print("\n👋 Goodbye!\n")
            break
        
        if command.lower() == 'profile':
            # Get profile from orchestrator's user_profiles dict
            profile = orchestrator.user_profiles.get(user_id)
            if profile:
                profile.display_profile(top_n=5)
            else:
                print("⚠️  No profile yet. Send a message first.\n")
            continue
        
        if command.lower() == 'history':
            profile = orchestrator.user_profiles.get(user_id)
            if profile:
                display_frequency_analysis(profile)
            else:
                print("⚠️  No profile yet. Send a message first.\n")
            continue
        
        if command.lower() == 'states':
            profile = orchestrator.user_profiles.get(user_id)
            if profile:
                display_activation_status(profile)
                display_current_states(profile)
                print()
            else:
                print("⚠️  No profile yet. Send a message first.\n")
            continue
        
        # Process message
        message_count += 1
        writing_time = end_time - start_time
        
        print(f"\n{'─'*100}")
        print(f"Message #{message_count}")
        print(f"{'─'*100}\n")
        
        # Call orchestrator to process message
        analysis = orchestrator.process_user_message(
            user_id=user_id,
            message=command,
            reference_date=datetime.now(),
            writing_time=writing_time
        )
        
        # Critical check: ensure analysis is not None
        if analysis is None:
            print("❌ ERROR: orchestrator.process_user_message() returned None!")
            print("This should not happen after our initial check.")
            print("Please check your orchestrator.py implementation.")
            continue
        
        # ==========================================================
        # DISPLAY ANALYSIS RESULTS
        # ==========================================================
        
        # 1. EMOTIONS DETECTED
        print("😊 EMOTIONS DETECTED:")
        display_emotions(analysis.emotions_detected, top_n=5)
        
        # 2. TEMPORAL REFERENCES
        print("\n⏰ TEMPORAL REFERENCES:")
        display_temporal_references(analysis.temporal_references)
        
        # 3. WRITING TIME
        print(f"\n⌨️  Writing time: {writing_time:.4f} seconds")
        
        # 4. IMPACT SCORE
        print(f"\n💥 IMPACT SCORE: {analysis.impact_score:.4f}", end="")
        if analysis.impact_score > 0.8:
            print(" 🔴 HIGH")
        elif analysis.impact_score > 0.4:
            print(" 🟡 MEDIUM")
        else:
            print(" 🟢 LOW")
        
        # 5. ANALYSIS SUMMARY
        if hasattr(analysis, 'analysis_summary') and analysis.analysis_summary:
            print(f"\n📌 Summary: {analysis.analysis_summary}")
        
        # 6. GET PROFILE
        profile = orchestrator.user_profiles.get(user_id)
        
        if profile:
            # 7. STATE ACTIVATION STATUS
            display_activation_status(profile)
            
            # 8. CURRENT EMOTIONAL STATE
            display_current_states(profile)
            
            # 9. LOG TO EXCEL
            log_to_excel(logger, profile, analysis, command)
        else:
            print("\n⚠️  Profile not created properly")
        
        print(f"\n{'─'*100}\n")
        
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!\n")
        break
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        print()

print("="*100)
print("TEST COMPLETE")
print("="*100)