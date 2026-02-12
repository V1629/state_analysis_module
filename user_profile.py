"""
User Emotional Profile Manager with Advanced State Aggregation
NOW WITH: Smart mid-term windowing and long-term frequency-based selection
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import json
import os
from collections import Counter


# ==========================================================
# ALL 27 EMOTIONS
# ==========================================================

ALL_EMOTIONS = [
    'admiration', 'amusement', 'anger', 'annoyance', 'approval',
    'caring', 'confusion', 'curiosity', 'desire', 'disappointment',
    'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear',
    'gratitude', 'grief', 'joy', 'love', 'nervousness',
    'neutral', 'optimism', 'pride', 'realization', 'relief',
    'remorse', 'sadness', 'surprise'
]


# ==========================================================
# STATE ACTIVATION THRESHOLDS
# ==========================================================

STATE_ACTIVATION_CONFIG = {
    'short_term': {
        'name': '⚡ Short-term (0-30 days)',
        'min_days': 0,
        'min_messages': 1,
        'description': 'Recent emotions, always tracking'
    },
    'mid_term': {
        'name': '📈 Mid-term (31-365 days)',
        'min_days': 14,
        'min_messages': 40,
        'description': 'Patterns over 2 weeks / ~6 msgs per day',
        'window_size': 15  # Rolling window: look at last 15 messages
    },
    'long_term': {
        'name': '🏛️ Long-term (365+ days)',
        'min_days': 90,
        'min_messages': 150,
        'description': 'Baseline personality over 3 months / ~1.7 msgs per day'
    }
}


# ==========================================================
# USER PROFILE CLASS
# ==========================================================

class UserProfile:
    """
    Manages user's emotional profile across three temporal dimensions
    
    Attributes:
        user_id: Unique user identifier
        short_term_state: Recent emotions (0-30 days) - Always active
        mid_term_state: Rolling window patterns (31-365 days) - Activates after 14 days OR 40 messages
        long_term_state: Frequency-based baseline (365+ days) - Activates after 90 days OR 150 messages
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # Initialize all 27 emotions with zero scores
        self.short_term_state = {emotion: 0.0 for emotion in ALL_EMOTIONS}
        self.mid_term_state = {emotion: 0.0 for emotion in ALL_EMOTIONS}
        self.long_term_state = {emotion: 0.0 for emotion in ALL_EMOTIONS}
        
        # Message history - stores all messages with emotions
        self.message_history = []

        # User's baseline typing speed
        self.typing_speed_mean = 5.0
        self.typing_speed_std = 1.0
        
        # State activation tracking
        self.message_count = 0
        self.profile_age_days = 0
        self.state_activation_status = {
            'short_term': True,    # Always active
            'mid_term': False,
            'long_term': False
        }
        
        # Flags to track if states have been initialized
        self.mid_term_initialized = False
        self.long_term_initialized = False

    # ============================================================
    # PROFILE AGE CALCULATION
    # ============================================================

    def calculate_profile_age(self) -> int:
        """Calculate days since profile creation"""
        self.profile_age_days = (datetime.now() - self.created_at).days
        return self.profile_age_days

    # ============================================================
    # STATE ACTIVATION LOGIC
    # ============================================================

    def is_state_activated(self, state_type: str) -> bool:
        """
        Check if a state should be updated based on thresholds
        
        Uses HYBRID approach: Activates if EITHER time OR message threshold met
        
        Args:
            state_type: 'short_term', 'mid_term', or 'long_term'
        
        Returns:
            True if state is activated, False otherwise
        """
        
        threshold = STATE_ACTIVATION_CONFIG.get(state_type)
        if not threshold:
            return False
        
        # Update age first
        self.calculate_profile_age()
        
        min_days = threshold['min_days']
        min_messages = threshold['min_messages']
        
        days_met = self.profile_age_days >= min_days
        messages_met = self.message_count >= min_messages
        
        # OR logic: activate if either condition is met
        is_activated = days_met or messages_met
        
        # Update status tracking
        self.state_activation_status[state_type] = is_activated
        
        return is_activated

    def get_state_activation_info(self) -> Dict[str, Dict]:
        """
        Get current activation status and progress for all states
        
        Returns:
            {
                'state_type': {
                    'is_active': bool,
                    'days_progress': float (0-100),
                    'messages_progress': float (0-100),
                    'days_remaining': int,
                    'messages_remaining': int,
                    'activated_by': str ('days', 'messages', 'both', or 'not_yet')
                }
            }
        """
        self.calculate_profile_age()
        
        info = {}
        for state_type, threshold in STATE_ACTIVATION_CONFIG.items():
            min_days = threshold['min_days']
            min_messages = threshold['min_messages']
            
            days_progress = (self.profile_age_days / min_days * 100) if min_days > 0 else 100
            messages_progress = (self.message_count / min_messages * 100) if min_messages > 0 else 100
            
            days_met = self.profile_age_days >= min_days
            messages_met = self.message_count >= min_messages
            
            # Determine what activated the state
            if days_met and messages_met:
                activated_by = 'both'
            elif days_met:
                activated_by = 'days'
            elif messages_met:
                activated_by = 'messages'
            else:
                activated_by = 'not_yet'
            
            info[state_type] = {
                'is_active': self.is_state_activated(state_type),
                'days_progress': min(100, days_progress),
                'messages_progress': min(100, messages_progress),
                'days_remaining': max(0, min_days - self.profile_age_days),
                'messages_remaining': max(0, min_messages - self.message_count),
                'activated_by': activated_by
            }
        
        return info

    # ============================================================
    # ADVANCED STATE AGGREGATION
    # ============================================================

    def aggregate_emotions_from_window(self, window_messages: List[Dict]) -> Dict[str, float]:
        """
        Aggregate emotions from a list of messages using exponential decay
        More recent messages get higher weight
        
        Args:
            window_messages: List of message history dicts
        
        Returns:
            Aggregated {emotion: weighted_score}
        """
        if not window_messages:
            return {}
        
        aggregated = {emotion: 0.0 for emotion in ALL_EMOTIONS}
        
        # Calculate weights using exponential decay (recent = high weight)
        for i, msg_entry in enumerate(window_messages):
            # Newer messages (higher index) get exponentially higher weight
            # weight = e^(lambda * position), where lambda controls decay
            lambda_factor = 0.1  # Adjust for how much to favor recent messages
            weight = (i + 1) / len(window_messages)  # Linear increase (0 to 1)
            # weight = math.exp(lambda_factor * i) / math.exp(lambda_factor * len(window_messages))  # Exponential increase
            
            emotions = msg_entry.get('emotions_detected', {})
            impact_score = msg_entry.get('impact_score', 0.0)
            
            for emotion, score in emotions.items():
                # Combine: base score × message weight × impact score
                weighted_contribution = score * weight * (0.5 + impact_score * 0.5)
                aggregated[emotion] += weighted_contribution
        
        # Normalize
        max_val = max(aggregated.values()) if aggregated else 1.0
        if max_val > 0:
            aggregated = {e: v / max_val for e, v in aggregated.items()}
        
        return aggregated

    def get_top_emotions_by_frequency(self, top_n: int = 3) -> List[Tuple[str, float, int]]:
        """
        Get top N emotions from entire message history
        Uses: 1) Highest cumulative score, 2) Frequency as tiebreaker
        
        Returns:
            List of [(emotion, avg_score, frequency), ...]
        """
        if not self.message_history:
            return []
        
        # Collect all emotions with their scores and frequencies
        emotion_stats = {}
        
        for msg_entry in self.message_history:
            emotions = msg_entry.get('emotions_detected', {})
            
            for emotion, score in emotions.items():
                if emotion not in emotion_stats:
                    emotion_stats[emotion] = {
                        'total_score': 0.0,
                        'frequency': 0,
                        'scores': []
                    }
                
                emotion_stats[emotion]['total_score'] += score
                emotion_stats[emotion]['frequency'] += 1
                emotion_stats[emotion]['scores'].append(score)
        
        # Calculate average score and prepare ranking
        ranked_emotions = []
        for emotion, stats in emotion_stats.items():
            avg_score = stats['total_score'] / stats['frequency']
            frequency = stats['frequency']
            ranked_emotions.append((emotion, avg_score, frequency))
        
        # Sort by: 1) average score (descending), 2) frequency (descending) as tiebreaker
        ranked_emotions.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        return ranked_emotions[:top_n]

    def initialize_mid_term_on_activation(self):
        """
        When mid_term activates, seed it with aggregated emotions from ALL prior messages
        Uses exponential decay - older messages have lower weight
        """
        if self.mid_term_initialized or not self.is_state_activated('mid_term'):
            return
        
        print(f"\n✨ MID-TERM STATE ACTIVATED!")
        print(f"   Initializing with emotions from {len(self.message_history)} messages...")
        
        # Get all messages up to now
        aggregated = self.aggregate_emotions_from_window(self.message_history)
        
        if aggregated:
            # Initialize mid_term with aggregated data
            self.mid_term_state = aggregated.copy()
            self._normalize_state('mid_term')
            self.mid_term_initialized = True
            
            # Show initialization details
            top_emotions = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"   Top emotions: {', '.join([f'{e[0]} ({e[1]:.3f})' for e in top_emotions])}")

    def initialize_long_term_on_activation(self):
        """
        When long_term activates, seed it with top 3 emotions from entire history
        Uses frequency as tiebreaker for equal scores
        """
        if self.long_term_initialized or not self.is_state_activated('long_term'):
            return
        
        print(f"\n✨ LONG-TERM STATE ACTIVATED!")
        print(f"   Analyzing {len(self.message_history)} messages for baseline personality...")
        
        # Get top 3 emotions by frequency and score
        top_emotions = self.get_top_emotions_by_frequency(top_n=3)
        
        if top_emotions:
            # Initialize long_term with equal weight for top 3
            for emotion, avg_score, frequency in top_emotions:
                self.long_term_state[emotion] = 0.333  # Equal weight for top 3
            
            self._normalize_state('long_term')
            self.long_term_initialized = True
            
            # Show initialization details
            print(f"   Baseline emotions (top 3):")
            for rank, (emotion, avg_score, frequency) in enumerate(top_emotions, 1):
                print(f"      {rank}. {emotion:20s} | Avg Score: {avg_score:.3f} | Frequency: {frequency} messages")

    def update_mid_term_with_window(self, emotions_dict: Dict[str, float], impact_weight: float = 1.0):
        """
        Update mid_term using a rolling window approach
        Aggregates emotions from the last 15 messages (configurable)
        
        Args:
            emotions_dict: Current message emotions (not used directly, recalculated from window)
            impact_weight: Scaling factor for updates
        """
        if not self.is_state_activated('mid_term'):
            return
        
        # Initialize if not done yet
        if not self.mid_term_initialized:
            self.initialize_mid_term_on_activation()
            return
        
        # Get window size from config
        window_size = STATE_ACTIVATION_CONFIG['mid_term'].get('window_size', 15)
        
        # Get the last N messages (rolling window)
        window_messages = self.message_history[-window_size:] if len(self.message_history) > 0 else []
        
        if window_messages:
            # Aggregate emotions from this window
            windowed_emotions = self.aggregate_emotions_from_window(window_messages)
            
            # Update mid_term with windowed aggregation
            for emotion, score in windowed_emotions.items():
                self.mid_term_state[emotion] = score * (0.7 + 0.3 * impact_weight)
        
        self._normalize_state('mid_term')
        self.last_updated = datetime.now()

    def update_long_term_with_frequency(self, emotions_dict: Dict[str, float], impact_weight: float = 1.0):
        """
        Update long_term using frequency-based approach
        Periodically recalculates top 3 emotions from entire history
        
        Args:
            emotions_dict: Current message emotions (not used, recalculated)
            impact_weight: Scaling factor for updates
        """
        if not self.is_state_activated('long_term'):
            return
        
        # Initialize if not done yet
        if not self.long_term_initialized:
            self.initialize_long_term_on_activation()
            return
        
        # Every 10 messages, recalculate long-term baseline
        if self.message_count % 10 == 0:
            top_emotions = self.get_top_emotions_by_frequency(top_n=3)
            
            if top_emotions:
                # Reset long_term
                self.long_term_state = {emotion: 0.0 for emotion in ALL_EMOTIONS}
                
                # Set top 3 with equal weight
                for emotion, avg_score, frequency in top_emotions:
                    self.long_term_state[emotion] = 0.333
                
                self._normalize_state('long_term')

        self.last_updated = datetime.now()

    # ============================================================
    # LEGACY STATE UPDATE METHODS (Short-term only now)
    # ============================================================

    def update_short_term(self, emotions_dict: Dict[str, float], impact_weight: float = 1.0):
        """
        Update short-term emotional state
        Short-term is ALWAYS active - accumulates current emotions
        """
        if not self.is_state_activated('short_term'):
            return
        
        # Add new emotions
        for emotion, score in emotions_dict.items():
            if emotion in self.short_term_state:
                self.short_term_state[emotion] += (score * impact_weight)
        
        # Normalize
        self._normalize_state('short_term')
        self.last_updated = datetime.now()

    def update_mid_term(self, emotions_dict: Dict[str, float], impact_weight: float = 1.0):
        """
        Wrapper that calls the window-based update
        """
        self.update_mid_term_with_window(emotions_dict, impact_weight)

    def update_long_term(self, emotions_dict: Dict[str, float], impact_weight: float = 1.0):
        """
        Wrapper that calls the frequency-based update
        """
        self.update_long_term_with_frequency(emotions_dict, impact_weight)

    # ============================================================
    # NORMALIZATION METHOD
    # ============================================================

    def _normalize_state(self, state_type: str):
        """
        Normalize emotional state so all values stay in [0, 1]
        and max value doesn't exceed 1.0
        """
        if state_type == 'short_term':
            state = self.short_term_state
        elif state_type == 'mid_term':
            state = self.mid_term_state
        elif state_type == 'long_term':
            state = self.long_term_state
        else:
            return
        
        # Find max value
        max_val = max(state.values()) if state.values() else 1.0
        
        # If max exceeds 1.0, scale down proportionally
        if max_val > 1.0:
            scale_factor = 1.0 / max_val
            for emotion in state:
                state[emotion] = state[emotion] * scale_factor
        
        # Cap individual values at 1.0
        for emotion in state:
            state[emotion] = min(1.0, max(0.0, state[emotion]))

    # ============================================================
    # RANKING & RETRIEVAL
    # ============================================================

    def get_top_emotions(self, state_type: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """Get top N emotions from specified state"""
        if state_type == 'short_term':
            state = self.short_term_state
        elif state_type == 'mid_term':
            state = self.mid_term_state
        elif state_type == 'long_term':
            state = self.long_term_state
        else:
            raise ValueError(f"Invalid state_type: {state_type}")
        
        # Filter out zero scores and very small scores (< 0.001)
        non_zero = {k: v for k, v in state.items() if v > 0.001}
        
        # Sort by score descending
        sorted_emotions = sorted(non_zero.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_emotions[:top_n]

    def get_all_states_with_top_emotions(self, top_n: int = 5) -> Dict[str, List[Tuple[str, float]]]:
        """Get top emotions for all three states"""
        return {
            'short_term': self.get_top_emotions('short_term', top_n),
            'mid_term': self.get_top_emotions('mid_term', top_n),
            'long_term': self.get_top_emotions('long_term', top_n),
        }

    def get_top_emotions_or_placeholder(self, state_type: str, top_n: int = 1) -> List[Tuple[str, float]]:
        """
        Get top emotions, but return placeholder if state not activated
        
        Returns:
            List of (emotion, score) tuples, or [("N/A", 0.0)] if not activated
        """
        if not self.is_state_activated(state_type):
            return [("N/A", 0.0)]
        
        return self.get_top_emotions(state_type, top_n)

    # ============================================================
    # MESSAGE HISTORY
    # ============================================================

    def add_message_to_history(self, message: str, emotions: Dict[str, float], 
                               time_refs: Dict, impact_score: float):
        """
        Log message and its analysis
        Called after processing each message
        """
        self.message_history.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'emotions_detected': emotions,
            'time_references': time_refs,
            'impact_score': impact_score,
        })
        
        # Increment message counter
        self.message_count += 1

    def get_message_history(self, limit: int = 10) -> List[Dict]:
        """Get last N messages from history"""
        return self.message_history[-limit:]

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(self) -> Dict:
        """Convert profile to dictionary"""
        activation_info = self.get_state_activation_info()
        
        return {
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'profile_age_days': self.calculate_profile_age(),
            'message_count': self.message_count,
            'short_term_state': self.short_term_state,
            'mid_term_state': self.mid_term_state,
            'long_term_state': self.long_term_state,
            'top_emotions': self.get_all_states_with_top_emotions(),
            'state_activation_info': activation_info,
            'message_history_count': len(self.message_history),
        }

    def to_json(self) -> str:
        """Convert profile to JSON"""
        return json.dumps(self.to_dict(), indent=2, default=str)

    def save_to_file(self, filename: str) -> bool:
        """Save profile to JSON file"""
        try:
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
            with open(filename, 'w') as f:
                f.write(self.to_json())
            return True
        except Exception as e:
            print(f"❌ Error saving profile: {e}")
            return False

    @classmethod
    def load_from_file(cls, filename: str) -> Optional['UserProfile']:
        """Load profile from JSON file"""
        try:
            if not os.path.exists(filename):
                return None
            
            with open(filename, 'r') as f:
                data = json.load(f)
            
            profile = cls(data['user_id'])
            profile.short_term_state = {k: float(v) for k, v in data['short_term_state'].items()}
            profile.mid_term_state = {k: float(v) for k, v in data['mid_term_state'].items()}
            profile.long_term_state = {k: float(v) for k, v in data['long_term_state'].items()}
            profile.created_at = datetime.fromisoformat(data['created_at'])
            profile.last_updated = datetime.fromisoformat(data['last_updated'])
            profile.message_count = data.get('message_count', 0)
            
            return profile
        except Exception as e:
            print(f"❌ Error loading profile: {e}")
            return None

    # ============================================================
    # DISPLAY
    # ============================================================

    def display_profile(self, top_n: int = 5):
        """Pretty print user profile with activation status"""
        print("\n" + "="*90)
        print(f"📊 USER EMOTIONAL PROFILE: {self.user_id}")
        print("="*90)
        print(f"Created: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Last Updated: {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Messages Analyzed: {self.message_count}")
        print(f"Profile Age: {self.calculate_profile_age()} days")
        print("="*90)
        
        # Show activation status
        activation_info = self.get_state_activation_info()
        print("\n🔓 STATE ACTIVATION STATUS:")
        print("-" * 90)
        
        for state_type in ['short_term', 'mid_term', 'long_term']:
            info = activation_info[state_type]
            status = "✅ ACTIVE" if info['is_active'] else "⏳ INACTIVE"
            threshold = STATE_ACTIVATION_CONFIG[state_type]
            
            print(f"\n{threshold['name']} {status}")
            print(f"   Days:     {info['days_progress']:5.1f}% ({self.profile_age_days}/{threshold['min_days']} days)")
            print(f"   Messages: {info['messages_progress']:5.1f}% ({self.message_count}/{threshold['min_messages']} messages)")
            
            if not info['is_active']:
                remaining = []
                if info['days_remaining'] > 0:
                    remaining.append(f"{info['days_remaining']} days")
                if info['messages_remaining'] > 0:
                    remaining.append(f"{info['messages_remaining']} messages")
                if remaining:
                    print(f"   Need: {' OR '.join(remaining)}")
            else:
                print(f"   Activated by: {info['activated_by']}")
                if state_type == 'mid_term':
                    print(f"   Using: Rolling window of 15 messages")
                elif state_type == 'long_term':
                    print(f"   Using: Top 3 emotions by frequency from entire history")
        
        print("\n" + "="*90)
        
        states = self.get_all_states_with_top_emotions(top_n)
        
        # SHORT-TERM
        print(f"\n⚡ SHORT-TERM STATE (Recent: 0-30 days)")
        print("-" * 90)
        if states['short_term']:
            for rank, (emotion, score) in enumerate(states['short_term'], 1):
                bar = "█" * int(score * 30) + "░" * int((1 - score) * 30)
                print(f"  {rank}. {emotion:20s} │ {bar} │ {score:.4f}")
        else:
            print("  No emotions detected yet")
        
        # MID-TERM
        if activation_info['mid_term']['is_active']:
            print(f"\n📈 MID-TERM STATE (Medium: 31-365 days) ✅ ACTIVE")
            print(f"   (Rolling window of 15 messages)")
            print("-" * 90)
            if states['mid_term']:
                for rank, (emotion, score) in enumerate(states['mid_term'], 1):
                    bar = "█" * int(score * 30) + "░" * int((1 - score) * 30)
                    print(f"  {rank}. {emotion:20s} │ {bar} │ {score:.4f}")
            else:
                print("  No emotions in window yet")
        else:
            print(f"\n📈 MID-TERM STATE (Medium: 31-365 days) ⏳ INACTIVE")
            print("-" * 90)
            print(f"  Unlocks in: {activation_info['mid_term']['days_remaining']} days OR {activation_info['mid_term']['messages_remaining']} messages")
        
        # LONG-TERM
        if activation_info['long_term']['is_active']:
            print(f"\n🏛️  LONG-TERM STATE (Baseline: 365+ days) ✅ ACTIVE")
            print(f"   (Top 3 emotions by frequency from all {len(self.message_history)} messages)")
            print("-" * 90)
            
            # Show frequency analysis
            top_by_freq = self.get_top_emotions_by_frequency(top_n=3)
            if top_by_freq:
                for rank, (emotion, avg_score, frequency) in enumerate(top_by_freq, 1):
                    print(f"  {rank}. {emotion:20s} │ Avg: {avg_score:.4f} │ Frequency: {frequency} messages")
            
            if states['long_term']:
                print("\n  Current State Distribution:")
                for rank, (emotion, score) in enumerate(states['long_term'], 1):
                    bar = "█" * int(score * 30) + "░" * int((1 - score) * 30)
                    print(f"  {rank}. {emotion:20s} │ {bar} │ {score:.4f}")
            else:
                print("  No baseline established yet")
        else:
            print(f"\n🏛️  LONG-TERM STATE (Baseline: 365+ days) ⏳ INACTIVE")
            print("-" * 90)
            print(f"  Unlocks in: {activation_info['long_term']['days_remaining']} days OR {activation_info['long_term']['messages_remaining']} messages")
        
        print("\n" + "="*90 + "\n")


if __name__ == "__main__":
    print("🎯 User Profile Manager\n")
    
    user_id = input("Enter your username: ").strip()
    if not user_id:
        user_id = "default_user"
    
    profile_path = os.path.join("user_profiles", f"{user_id}.json")
    profile = UserProfile.load_from_file(profile_path)
    
    if profile:
        print(f"\n✅ Profile found for {user_id}")
        profile.display_profile(top_n=5)
    else:
        print(f"\n⚠️  No profile found for {user_id}")
        print("Please chat first using test_orchestrator.py or simple_chat.py\n")