"""
User Emotional Profile Manager with Adaptive Weight Learning
NOW WITH: Dynamic weight adjustment based on chat history patterns
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import json
import os
from collections import Counter
import math


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
# INITIAL WEIGHTS (Hierarchy: emotion > recency > repetition > confidence)
# ==========================================================

INITIAL_WEIGHTS = {
    'emotion_intensity': 0.45,      # Highest - emotion is primary
    'recency_weight': 0.30,         # High - recent events matter
    'recurrence_boost': 0.15,       # Medium - patterns matter
    'temporal_confidence': 0.10     # Lowest - exact timing less critical
}


# ==========================================================
# USER PROFILE CLASS
# ==========================================================

class UserProfile:
    """
    Manages user's emotional profile across three temporal dimensions
    WITH ADAPTIVE WEIGHT LEARNING
    
    Attributes:
        user_id: Unique user identifier
        short_term_state: Recent emotions (0-30 days) - Always active
        mid_term_state: Rolling window patterns (31-365 days) - Activates after 14 days OR 40 messages
        long_term_state: Frequency-based baseline (365+ days) - Activates after 90 days OR 150 messages
        adaptive_weights: Dynamically adjusted weights based on chat patterns
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
        
        # ===== ADAPTIVE WEIGHTS SYSTEM =====
        # Initialize with hierarchy: emotion > recency > repetition > confidence
        self.adaptive_weights = INITIAL_WEIGHTS.copy()
        self.weights_learning_enabled = False  # Enable when mid_term activates
        self.weight_adjustment_history = []    # Track weight changes over time

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
    # ADAPTIVE WEIGHT LEARNING SYSTEM
    # ============================================================

    def analyze_chat_patterns(self) -> Dict[str, Any]:
        """
        Analyze chat history to understand user's emotional patterns
        
        Returns:
            {
                'emotion_frequency': {emotion: count},
                'emotion_intensity_avg': float,
                'recency_pattern': 'talks about recent/past/mixed',
                'temporal_specificity': float (0-1, how specific are dates),
                'repetition_pattern': {emotion: repeat_count},
                'dominant_emotion': str,
                'temporal_ref_ratio': float
            }
        """
        if not self.message_history:
            return {}
        
        # Count emotions
        emotion_frequency = Counter()
        emotion_intensity_sum = 0.0
        temporal_refs_count = 0
        all_emotions_list = []
        
        for msg_entry in self.message_history:
            emotions = msg_entry.get('emotions_detected', {})
            time_refs = msg_entry.get('time_references', {})
            
            # Collect emotions
            for emotion, score in emotions.items():
                emotion_frequency[emotion] += 1
                emotion_intensity_sum += score
                all_emotions_list.append((emotion, score))
            
            # Track temporal references
            if time_refs.get('has_temporal_ref', False):
                temporal_refs_count += 1
        
        # Calculate averages
        avg_emotion_intensity = emotion_intensity_sum / len(all_emotions_list) if all_emotions_list else 0.0
        temporal_ref_ratio = temporal_refs_count / len(self.message_history) if self.message_history else 0.0
        
        # Analyze temporal specificity
        temporal_confidence_sum = 0.0
        for msg_entry in self.message_history:
            parsed_dates = msg_entry.get('time_references', {}).get('parsed_dates', [])
            for date_info in parsed_dates:
                temporal_confidence_sum += date_info.get('confidence', 0.5)
        
        avg_temporal_specificity = temporal_confidence_sum / temporal_refs_count if temporal_refs_count > 0 else 0.0
        
        # Find dominant emotion
        dominant_emotion = emotion_frequency.most_common(1)[0][0] if emotion_frequency else None
        
        # Analyze recurrence patterns
        repetition_pattern = {}
        for emotion, freq in emotion_frequency.items():
            if freq > 1:
                repetition_pattern[emotion] = freq
        
        # Determine recency pattern
        recency_pattern = self._analyze_recency_pattern()
        
        return {
            'emotion_frequency': dict(emotion_frequency),
            'emotion_intensity_avg': round(avg_emotion_intensity, 4),
            'recency_pattern': recency_pattern,
            'temporal_specificity': round(avg_temporal_specificity, 4),
            'repetition_pattern': repetition_pattern,
            'dominant_emotion': dominant_emotion,
            'temporal_ref_ratio': round(temporal_ref_ratio, 4),
            'message_count': len(self.message_history)
        }

    def _analyze_recency_pattern(self) -> str:
        """
        Analyze if user talks about recent events, past events, or mixed
        """
        if not self.message_history:
            return 'unknown'
        
        recent_count = 0
        past_count = 0
        
        for msg_entry in self.message_history:
            parsed_dates = msg_entry.get('time_references', {}).get('parsed_dates', [])
            for date_info in parsed_dates:
                age_category = date_info.get('age_category', 'unknown')
                if age_category == 'recent':
                    recent_count += 1
                elif age_category in ['medium', 'distant']:
                    past_count += 1
        
        total = recent_count + past_count
        if total == 0:
            return 'no_temporal_data'
        
        recent_ratio = recent_count / total
        
        if recent_ratio > 0.6:
            return 'recent_focused'
        elif recent_ratio < 0.4:
            return 'past_focused'
        else:
            return 'mixed'

    def calculate_adaptive_weights(self) -> Dict[str, float]:
        """
        Calculate adaptive weights based on chat patterns
        
        Logic:
        - If user talks about emotions with high intensity → increase emotion_intensity weight
        - If user talks about recent events → increase recency_weight
        - If user repeats same incidents → increase recurrence_boost weight
        - If user is vague about timing → decrease temporal_confidence weight
        
        Returns:
            Adjusted weights that sum to 1.0
        """
        
        if not self.weights_learning_enabled or len(self.message_history) < 10:
            return self.adaptive_weights.copy()
        
        patterns = self.analyze_chat_patterns()
        
        if not patterns:
            return self.adaptive_weights.copy()
        
        # Start with initial weights
        new_weights = INITIAL_WEIGHTS.copy()
        
        # ===== ADJUSTMENT 1: Emotion Intensity =====
        # If emotions are consistently HIGH intensity, boost this weight
        emotion_intensity = patterns.get('emotion_intensity_avg', 0.5)
        
        if emotion_intensity > 0.7:
            # Very emotional user - increase emotion weight
            new_weights['emotion_intensity'] = min(0.55, INITIAL_WEIGHTS['emotion_intensity'] + 0.05)
        elif emotion_intensity < 0.3:
            # Low emotional expression - decrease emotion weight
            new_weights['emotion_intensity'] = max(0.35, INITIAL_WEIGHTS['emotion_intensity'] - 0.05)
        
        # ===== ADJUSTMENT 2: Recency Weight =====
        # If user talks mostly about RECENT events, boost recency weight
        recency_pattern = patterns.get('recency_pattern', 'mixed')
        
        if recency_pattern == 'recent_focused':
            # User cares about recent events
            new_weights['recency_weight'] = min(0.40, INITIAL_WEIGHTS['recency_weight'] + 0.05)
        elif recency_pattern == 'past_focused':
            # User focuses on past - decrease recency weight
            new_weights['recency_weight'] = max(0.20, INITIAL_WEIGHTS['recency_weight'] - 0.05)
        
        # ===== ADJUSTMENT 3: Recurrence Boost =====
        # If user repeats same emotions/incidents, boost this weight
        repetition_pattern = patterns.get('repetition_pattern', {})
        repetition_count = len(repetition_pattern)
        
        if repetition_count > 3:
            # Many repeated emotions - increase recurrence weight
            new_weights['recurrence_boost'] = min(0.25, INITIAL_WEIGHTS['recurrence_boost'] + 0.05)
        elif repetition_count == 0:
            # No repetition - decrease recurrence weight
            new_weights['recurrence_boost'] = max(0.05, INITIAL_WEIGHTS['recurrence_boost'] - 0.05)
        
        # ===== ADJUSTMENT 4: Temporal Confidence =====
        # If user is VAGUE about timing, decrease temporal confidence weight
        temporal_specificity = patterns.get('temporal_specificity', 0.5)
        temporal_ref_ratio = patterns.get('temporal_ref_ratio', 0.5)
        
        if temporal_ref_ratio < 0.3:
            # User rarely mentions dates - decrease temporal confidence weight
            new_weights['temporal_confidence'] = max(0.05, INITIAL_WEIGHTS['temporal_confidence'] - 0.03)
        elif temporal_specificity > 0.8:
            # User is very specific about dates - increase temporal confidence weight
            new_weights['temporal_confidence'] = min(0.15, INITIAL_WEIGHTS['temporal_confidence'] + 0.03)
        
        # Normalize weights to sum to 1.0
        total_weight = sum(new_weights.values())
        normalized_weights = {k: v/total_weight for k, v in new_weights.items()}
        
        # Store in history
        self.weight_adjustment_history.append({
            'timestamp': datetime.now().isoformat(),
            'message_count': self.message_count,
            'old_weights': self.adaptive_weights.copy(),
            'new_weights': normalized_weights.copy(),
            'patterns': patterns,
            'reason': self._get_adjustment_reason(INITIAL_WEIGHTS, normalized_weights)
        })
        
        return normalized_weights

    @staticmethod
    def _get_adjustment_reason(old: dict, new: dict) -> str:
        """Explain why weights changed"""
        reasons = []
        
        for key in old:
            diff = new[key] - old[key]
            if abs(diff) > 0.01:
                direction = "increased" if diff > 0 else "decreased"
                reasons.append(f"{key}: {direction} by {abs(diff):.3f}")
        
        return " | ".join(reasons) if reasons else "No significant changes"

    def enable_weight_learning(self):
        """Enable adaptive weight learning (called when mid_term activates)"""
        print(f"\n✨ ENABLING ADAPTIVE WEIGHT LEARNING")
        print(f"   System will now adjust weights based on chat patterns...\n")
        self.weights_learning_enabled = True
        
        # Calculate initial adaptive weights
        self.adaptive_weights = self.calculate_adaptive_weights()
        
        print(f"📊 Initial Adaptive Weights:")
        for weight_name, value in self.adaptive_weights.items():
            print(f"   {weight_name:25s}: {value:.4f} ({value*100:.1f}%)")

    def update_adaptive_weights(self):
        """
        Update weights periodically based on new chat patterns
        Called every 10 messages after mid-term activation
        """
        if not self.weights_learning_enabled:
            return
        
        if self.message_count % 10 != 0:
            return  # Only update every 10 messages
        
        old_weights = self.adaptive_weights.copy()
        self.adaptive_weights = self.calculate_adaptive_weights()
        
        # Check if weights actually changed
        weight_changed = any(
            abs(self.adaptive_weights[k] - old_weights[k]) > 0.01 
            for k in old_weights
        )
        
        if weight_changed:
            print(f"\n🔄 WEIGHT ADJUSTMENT at Message {self.message_count}")
            print(f"   Analyzing chat patterns and updating weights...\n")
            
            for weight_name in old_weights:
                old_val = old_weights[weight_name]
                new_val = self.adaptive_weights[weight_name]
                change = new_val - old_val
                
                if abs(change) > 0.001:
                    direction = "↑" if change > 0 else "↓"
                    print(f"   {direction} {weight_name:25s}: {old_val:.4f} → {new_val:.4f}")

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
            lambda_factor = 0.1
            weight = (i + 1) / len(window_messages)  # Linear increase (0 to 1)
            
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
        
        # Enable adaptive weight learning
        self.enable_weight_learning()
        
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
        
        Also updates adaptive weights periodically
        
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
        
        # Update adaptive weights every 10 messages
        self.update_adaptive_weights()
        
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
    # LEGACY STATE UPDATE METHODS
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
            'adaptive_weights': self.adaptive_weights,
            'weights_learning_enabled': self.weights_learning_enabled,
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
            profile.adaptive_weights = data.get('adaptive_weights', INITIAL_WEIGHTS.copy())
            profile.weights_learning_enabled = data.get('weights_learning_enabled', False)
            
            return profile
        except Exception as e:
            print(f"❌ Error loading profile: {e}")
            return None

    # ============================================================
    # DISPLAY
    # ============================================================

    def display_profile(self, top_n: int = 5):
        """Pretty print user profile with activation status and adaptive weights"""
        print("\n" + "="*100)
        print(f"📊 USER EMOTIONAL PROFILE: {self.user_id}")
        print("="*100)
        print(f"Created: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Last Updated: {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Messages Analyzed: {self.message_count}")
        print(f"Profile Age: {self.calculate_profile_age()} days")
        print("="*100)
        
        # Show activation status
        activation_info = self.get_state_activation_info()
        print("\n🔓 STATE ACTIVATION STATUS:")
        print("-" * 100)
        
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
        
        # Show adaptive weights
        print("\n" + "="*100)
        print("⚖️  ADAPTIVE WEIGHTS:")
        print("-" * 100)
        
        if self.weights_learning_enabled:
            print("\n✅ LEARNING ENABLED (Adjusting based on chat patterns)\n")
        else:
            print("\n⏳ LEARNING DISABLED (Will enable at mid-term activation)\n")
        
        print(f"Current Weights (Hierarchy: emotion > recency > repetition > confidence):\n")
        
        # Sort by value (descending) to show hierarchy
        sorted_weights = sorted(self.adaptive_weights.items(), key=lambda x: x[1], reverse=True)
        for rank, (weight_name, value) in enumerate(sorted_weights, 1):
            bar = "█" * int(value * 30)
            print(f"  {rank}. {weight_name:25s} │ {bar:30s} │ {value:.4f} ({value*100:.1f}%)")
        
        # Show weight adjustment history
        if self.weight_adjustment_history:
            print(f"\n📈 WEIGHT ADJUSTMENT HISTORY ({len(self.weight_adjustment_history)} adjustments):")
            print("-" * 100)
            for adjustment in self.weight_adjustment_history[-3:]:  # Show last 3
                print(f"\n   📍 Message {adjustment['message_count']}")
                print(f"      {adjustment['reason']}")
        
        print("\n" + "="*100)
        
        states = self.get_all_states_with_top_emotions(top_n)
        
        # SHORT-TERM
        print(f"\n⚡ SHORT-TERM STATE (Recent: 0-30 days)")
        print("-" * 100)
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
            print("-" * 100)
            if states['mid_term']:
                for rank, (emotion, score) in enumerate(states['mid_term'], 1):
                    bar = "█" * int(score * 30) + "░" * int((1 - score) * 30)
                    print(f"  {rank}. {emotion:20s} │ {bar} │ {score:.4f}")
            else:
                print("  No emotions in window yet")
        else:
            print(f"\n📈 MID-TERM STATE (Medium: 31-365 days) ⏳ INACTIVE")
            print("-" * 100)
            print(f"  Unlocks in: {activation_info['mid_term']['days_remaining']} days OR {activation_info['mid_term']['messages_remaining']} messages")
        
        # LONG-TERM
        if activation_info['long_term']['is_active']:
            print(f"\n🏛️  LONG-TERM STATE (Baseline: 365+ days) ✅ ACTIVE")
            print(f"   (Top 3 emotions by frequency from all {len(self.message_history)} messages)")
            print("-" * 100)
            
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
            print("-" * 100)
            print(f"  Unlocks in: {activation_info['long_term']['days_remaining']} days OR {activation_info['long_term']['messages_remaining']} messages")
        
        print("\n" + "="*100 + "\n")


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