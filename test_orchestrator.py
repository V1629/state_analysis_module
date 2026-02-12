"""
Direct Test Script for Orchestrator with Advanced State Tracking
Shows detailed state aggregation and frequency analysis
"""

import sys
from datetime import datetime
import time

print("\n" + "="*100)
print("🧪 ORCHESTRATOR TEST - Advanced Emotional State Analysis")
print("="*100)

# Try importing
print("\n📦 Importing modules...")
try:
    from orchestrator import create_orchestrator
    print("   ✅ orchestrator imported")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

try:
    from user_profile import UserProfile
    print("   ✅ user_profile imported")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Logger import
try:
    from chat_logger import ChatLogger
    logger = ChatLogger("chat_logs.xlsx")
    print("   ✅ ChatLogger initialized")
except Exception as e:
    print(f"   ⚠️ Logger not initialized: {e}")
    logger = None

# Create orchestrator
print("\n🔧 Creating orchestrator...")
try:
    orchestrator = create_orchestrator()
    print("   ✅ Ready\n")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# User input loop
print("="*100)
print("INSTRUCTIONS:")
print("="*100)
print("• Enter a message to analyze")
print("• Type 'profile' to view full profile with advanced state info")
print("• Type 'history' to see emotion frequency analysis")
print("• Type 'exit' to quit\n")

message_count = 0

while True:
    start_time = time.perf_counter()
    command = input("💬 You: ").strip()
    end_time = time.perf_counter()
    
    if not command:
        continue
    
    if command.lower() == 'exit':
        print("\n👋 Goodbye!\n")
        break
    
    if command.lower() == 'profile':
        profile = orchestrator.get_user_profile("test_user")
        if profile:
            profile.display_profile(top_n=5)
        else:
            print("⚠️  No profile yet\n")
        continue
    
    if command.lower() == 'history':
        profile = orchestrator.get_user_profile("test_user")
        if profile and len(profile.message_history) > 0:
            print("\n" + "="*100)
            print("📊 EMOTION FREQUENCY ANALYSIS")
            print("="*100)
            
            top_emotions = profile.get_top_emotions_by_frequency(top_n=10)
            
            print(f"\nAnalyzing {len(profile.message_history)} messages...\n")
            print(f"{'Rank':<6} {'Emotion':<20} {'Avg Score':<15} {'Frequency':<15}")
            print("-" * 100)
            
            for rank, (emotion, avg_score, frequency) in enumerate(top_emotions, 1):
                bar = "█" * int(frequency / max([f[2] for f in top_emotions]) * 30)
                print(f"{rank:<6} {emotion:<20} {avg_score:<15.4f} {frequency:<15} {bar}")
            
            print("\n" + "="*100 + "\n")
        else:
            print("⚠️  No chat history yet\n")
        continue
    
    # Process message
    message_count += 1

    writing_time = end_time - start_time
    
    print(f"\n{'─'*100}")
    print(f"Message #{message_count}")
    print(f"{'─'*100}\n")
    
    try:
        analysis = orchestrator.process_user_message(
            user_id="test_user",
            message=command,
            reference_date=datetime.now(),
            writing_time=writing_time
        )
        
        # 1. EMOTIONS DETECTED
        print("😊 EMOTIONS DETECTED:")
        if analysis.emotions_detected:
            sorted_emotions = sorted(
                analysis.emotions_detected.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for rank, (emotion, score) in enumerate(sorted_emotions[:5], 1):
                bar = "█" * int(score * 25)
                print(f"   {rank}. {emotion:20s} │ {bar:25s} │ {score:.4f}")
        else:
            print("   No emotions detected")
        
        # 2. TEMPORAL REFERENCES
        print("\n⏰ TEMPORAL REFERENCES:")
        temp_ref = analysis.temporal_references
        
        if temp_ref['has_temporal_ref']:
            print(f"   Phrases found: {temp_ref['phrases_found']}")
            if temp_ref['parsed_dates']:
                for parsed in temp_ref['parsed_dates'][:3]:
                    print(f"\n   • {parsed['phrase']}")
                    print(f"     Category: {parsed['age_category']} | Confidence: {parsed['confidence']}\n")
        else:
            print("   No temporal references detected\n")

        # Writing time
        print(f"Writing time: {writing_time:.4f} seconds.\n")
        
        # 3. IMPACT
        print(f"💥 IMPACT SCORE: {analysis.impact_score:.4f}", end="")
        if analysis.impact_score > 0.8:
            print(" 🔴 HIGH")
        elif analysis.impact_score > 0.4:
            print(" 🟡 MEDIUM")
        else:
            print(" 🟢 LOW")
        
        print(f"\n📌 Summary: {analysis.analysis_summary}")
        
        # 4. STATE ACTIVATION STATUS
        print(f"\n🔓 STATE ACTIVATION STATUS:")
        profile = orchestrator.get_user_profile("test_user")
        if profile:
            activation_info = profile.get_state_activation_info()
            
            for state_type in ['short_term', 'mid_term', 'long_term']:
                info = activation_info[state_type]
                status = "✅ ACTIVE" if info['is_active'] else "⏳ INACTIVE"
                
                icon = "⚡" if state_type == "short_term" else ("📈" if state_type == "mid_term" else "🏛️")
                
                print(f"\n   {icon} {state_type.upper():12s}: {status}")
                print(f"      Days: {profile.profile_age_days} | Messages: {profile.message_count}")

        # 5. CURRENT STATE
        print(f"\n👤 CURRENT EMOTIONAL STATE:")
        if profile:
            states = profile.get_all_states_with_top_emotions(top_n=2)
            
            for state_type in ['short_term', 'mid_term', 'long_term']:
                icon = "⚡" if state_type == "short_term" else ("📈" if state_type == "mid_term" else "🏛️")
                emotions = states[state_type]
                
                if not profile.is_state_activated(state_type):
                    print(f"\n   {icon} {state_type.upper():12s}: ⏳ Not activated")
                elif emotions and emotions[0][0] != "N/A":
                    print(f"\n   {icon} {state_type.upper():12s}: {emotions[0][0]} ({emotions[0][1]:.4f})")
                    if len(emotions) > 1:
                        print(f"      Secondary: {emotions[1][0]} ({emotions[1][1]:.4f})")
                else:
                    print(f"\n   {icon} {state_type.upper():12s}: No emotions yet")

            # 6. LOG TO EXCEL
            if logger:
                try:
                    if analysis.emotions_detected:
                        top_detected = max(analysis.emotions_detected.items(), key=lambda x: x[1])
                        detected_emotion = top_detected[0]
                        detected_score = top_detected[1]
                    else:
                        detected_emotion = ""
                        detected_score = 0.0
                    
                    log_data_current = {
                        'short_term': [(detected_emotion, detected_score)] if detected_emotion else [],
                        'mid_term': [(detected_emotion, detected_score)] if detected_emotion else [],
                        'long_term': [(detected_emotion, detected_score)] if detected_emotion else [],
                    }
                    
                    log_data_profile = {
                        'short_term': profile.get_top_emotions_or_placeholder('short_term', 1),
                        'mid_term': profile.get_top_emotions_or_placeholder('mid_term', 1),
                        'long_term': profile.get_top_emotions_or_placeholder('long_term', 1),
                    }
                    
                    logger.log_chat(
                        message=command,
                        impact_score=analysis.impact_score,
                        current_state=log_data_current,
                        profile_state=log_data_profile,
                        activation_status=activation_info,
                        profile_age_days=profile.profile_age_days,
                        message_count=profile.message_count
                    )
                    print(f"\n✅ Logged to chat_logs.xlsx")
                except Exception as log_error:
                    print(f"\n⚠️ Logging failed: {log_error}")
        
        print(f"\n{'─'*100}\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        print()

print("="*100)
print("TEST COMPLETE")
print("="*100)