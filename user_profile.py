"""
User Emotional Profile Manager with Adaptive Weight Learning
NOW WITH: Dynamic weight adjustment based on chat history patterns

VERSION: 2.0 - Enhanced Edition
- Robust error handling
- Better null safety
- Enhanced data validation
- Improved edge case handling
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
        'min_messages': 30,
        'description': 'Patterns over 2 weeks / ~6 msgs per day',
        'window_size': 15  # Rolling window: look at last 15 messages
    },
    'long_term': {
        'name': '🏛️ Long-term (365+ days)',
        'min_days': 90,
        'min_messages': 50,
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
        """
        Initialize user profile
        
        Args:
            user_id: Unique user identifier
        """
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        
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
        self.weights_learning_enabled = False  # Enable when mid_term activates#########################will be enalbled after 50 messages
        self.weight_adjustment_history = []    # Track weight changes over time

    # ============================================================
    # PROFILE AGE CALCULATION
    # ============================================================

    def calculate_profile_age(self) -> int:
        """
        Calculate days since profile creation
        
        Returns:
            Number of days since profile creation
        """
        try:
            self.profile_age_days = (datetime.now() - self.created_at).days
            return self.profile_age_days
        except Exception as e:
            print(f"⚠️  Error calculating profile age: {e}")
            return 0

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
        
        try:
            # Update age first
            self.calculate_profile_age()
            
            min_days = threshold.get('min_days', 0)
            min_messages = threshold.get('min_messages', 0)
            
            days_met = self.profile_age_days >= min_days
            messages_met = self.message_count >= min_messages
            
            # OR logic: activate if either condition is met
            is_activated = days_met or messages_met
            
            # Update status tracking
            self.state_activation_status[state_type] = is_activated
            
            return is_activated
        except Exception as e:
            print(f"⚠️  Error checking state activation for {state_type}: {e}")
            return False

    def get_state_activation_info(self) -> Dict[str, Dict]:
        """
        Get current activation status and progress for all states
        
        Returns:
            Dictionary with activation info for each state
        """
        try:
            self.calculate_profile_age()
            
            info = {}
            for state_type, threshold in STATE_ACTIVATION_CONFIG.items():
                min_days = threshold.get('min_days', 0)
                min_messages = threshold.get('min_messages', 0)
                
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
                
                days_remaining = max(0, min_days - self.profile_age_days)
                messages_remaining = max(0, min_messages - self.message_count)
                
                info[state_type] = {
                    'is_active': days_met or messages_met,
                    'days_progress': min(100.0, days_progress),
                    'messages_progress': min(100.0, messages_progress),
                    'days_remaining': days_remaining,
                    'messages_remaining': messages_remaining,
                    'activated_by': activated_by
                }
            
            return info
        except Exception as e:
            print(f"⚠️  Error getting state activation info: {e}")
            return {
                'short_term': {'is_active': True, 'days_progress': 0, 'messages_progress': 0, 
                              'days_remaining': 0, 'messages_remaining': 0, 'activated_by': 'error'},
                'mid_term': {'is_active': False, 'days_progress': 0, 'messages_progress': 0,
                            'days_remaining': 14, 'messages_remaining': 40, 'activated_by': 'not_yet'},
                'long_term': {'is_active': False, 'days_progress': 0, 'messages_progress': 0,
                             'days_remaining': 90, 'messages_remaining': 150, 'activated_by': 'not_yet'}
            }

    # ============================================================
    # EMOTIONAL STATE UPDATES
    # ============================================================

    def update_emotional_state(
        self,
        emotions: Dict[str, float],
        impact_score: float,
        state_updates: Dict[str, Dict[str, float]],
        message: str,
        timestamp: datetime,
        temporal_category: str = "unknown"
    ):
        """
        Update user's emotional state based on new message
        
        Args:
            emotions: Detected emotions {emotion: score}
            impact_score: Overall impact score
            state_updates: State-specific updates
            message: Original message
            timestamp: Message timestamp
            temporal_category: Temporal category of reference
        """
        try:
            self.message_count += 1
            self.last_updated = datetime.now()
            
            # Store in message history
            self.message_history.append({
                'message': message,
                'timestamp': timestamp,
                'emotions_detected': emotions,
                'impact_score': impact_score,
                'temporal_category': temporal_category
            })
            
            # Update each emotional state
            for emotion, impacts in state_updates.items():
                if emotion not in ALL_EMOTIONS:
                    continue
                
                # Update short-term (always active)
                if self.is_state_activated('short_term'):
                    self.short_term_state[emotion] = max(0.0, min(1.0, 
                        self.short_term_state.get(emotion, 0.0) + impacts.get('short_term', 0.0)
                    ))
                
                # Update mid-term (if activated)
                if self.is_state_activated('mid_term'):
                    self.mid_term_state[emotion] = max(0.0, min(1.0,
                        self.mid_term_state.get(emotion, 0.0) + impacts.get('mid_term', 0.0)
                    ))
                
                # Update long-term (if activated)
                if self.is_state_activated('long_term'):
                    self.long_term_state[emotion] = max(0.0, min(1.0,
                        self.long_term_state.get(emotion, 0.0) + impacts.get('long_term', 0.0)
                    ))
            
            # Normalize states
            self._normalize_state('short_term')
            if self.is_state_activated('mid_term'):
                self._normalize_state('mid_term')
            if self.is_state_activated('long_term'):
                self._normalize_state('long_term')
            
            # Update advanced states
            self._update_mid_term_rolling_window()
            self._update_long_term_frequency_based()
            
            # Enable weight learning when mid-term activates
            if self.is_state_activated('mid_term') and not self.weights_learning_enabled:
                self.weights_learning_enabled = True
                self._enable_weight_learning()
            
            # Update adaptive weights every 10 messages (after learning is enabled)
            if self.weights_learning_enabled and self.message_count % 10 == 0:
                self._update_adaptive_weights()
            
        except Exception as e:
            print(f"⚠️  Error updating emotional state: {e}")

    def _normalize_state(self, state_type: str):
        """Normalize emotional state to sum to 1.0"""
        try:
            if state_type == 'short_term':
                state = self.short_term_state
            elif state_type == 'mid_term':
                state = self.mid_term_state
            elif state_type == 'long_term':
                state = self.long_term_state
            else:
                return
            
            total = sum(state.values())
            if total > 0:
                for emotion in state:
                    state[emotion] = state[emotion] / total
        except Exception as e:
            print(f"⚠️  Error normalizing {state_type} state: {e}")

    # ============================================================
    # ADAPTIVE WEIGHT LEARNING SYSTEM
    # ============================================================

    def _analyze_chat_patterns(self) -> Dict[str, Any]:
        """
        Analyze chat history to understand user's emotional patterns
        
        Returns:
            Dictionary with pattern analysis results
        """
        if not self.message_history or len(self.message_history) < 10:
            return {}
        
        try:
            from collections import Counter
            
            emotion_frequency = Counter()
            emotion_intensity_sum = 0.0
            temporal_refs_count = 0
            all_emotions_list = []
            recent_count = 0
            past_count = 0
            
            for msg_entry in self.message_history:
                emotions = msg_entry.get('emotions_detected', {})
                
                # Collect emotions
                for emotion, score in emotions.items():
                    emotion_frequency[emotion] += 1
                    emotion_intensity_sum += score
                    all_emotions_list.append((emotion, score))
                
                # Track temporal references
                temporal_cat = msg_entry.get('temporal_category', 'unknown')
                if temporal_cat == 'recent':
                    recent_count += 1
                    temporal_refs_count += 1
                elif temporal_cat in ['medium', 'distant']:
                    past_count += 1
                    temporal_refs_count += 1
            
            # Calculate averages
            avg_emotion_intensity = emotion_intensity_sum / len(all_emotions_list) if all_emotions_list else 0.5
            temporal_ref_ratio = temporal_refs_count / len(self.message_history) if self.message_history else 0.0
            
            # Analyze recency pattern
            total_temporal = recent_count + past_count
            if total_temporal == 0:
                recency_pattern = 'no_temporal_data'
            else:
                recent_ratio = recent_count / total_temporal
                if recent_ratio > 0.6:
                    recency_pattern = 'recent_focused'
                elif recent_ratio < 0.4:
                    recency_pattern = 'past_focused'
                else:
                    recency_pattern = 'mixed'
            
            # Find dominant emotion
            dominant_emotion = emotion_frequency.most_common(1)[0][0] if emotion_frequency else None
            
            # Analyze repetition patterns
            repetition_pattern = {}
            for emotion, freq in emotion_frequency.items():
                if freq > 1:
                    repetition_pattern[emotion] = freq
            
            # Temporal specificity (simplified - based on temporal ref ratio)
            temporal_specificity = temporal_ref_ratio
            
            return {
                'emotion_frequency': dict(emotion_frequency),
                'emotion_intensity_avg': round(avg_emotion_intensity, 4),
                'recency_pattern': recency_pattern,
                'temporal_specificity': round(temporal_specificity, 4),
                'repetition_pattern': repetition_pattern,
                'dominant_emotion': dominant_emotion,
                'temporal_ref_ratio': round(temporal_ref_ratio, 4),
                'message_count': len(self.message_history)
            }
        except Exception as e:
            print(f"⚠️  Error analyzing chat patterns: {e}")
            return {}

    def _calculate_adaptive_weights(self) -> Dict[str, float]:
        """
        Calculate adaptive weights based on chat patterns
        
        Returns:
            Adjusted weights that sum to 1.0
        """
        if not self.weights_learning_enabled or len(self.message_history) < 10:
            return self.adaptive_weights.copy()
        
        try:
            patterns = self._analyze_chat_patterns()
            
            if not patterns:
                return self.adaptive_weights.copy()
            
            # Start with initial weights
            new_weights = INITIAL_WEIGHTS.copy()
            
            # ===== ADJUSTMENT 1: Emotion Intensity =====
            emotion_intensity = patterns.get('emotion_intensity_avg', 0.5)
            
            if emotion_intensity > 0.7:
                # Very emotional user - increase emotion weight
                new_weights['emotion_intensity'] = min(0.55, INITIAL_WEIGHTS['emotion_intensity'] + 0.05)
            elif emotion_intensity < 0.3:
                # Low emotional expression - decrease emotion weight
                new_weights['emotion_intensity'] = max(0.35, INITIAL_WEIGHTS['emotion_intensity'] - 0.05)
            
            # ===== ADJUSTMENT 2: Recency Weight =====
            recency_pattern = patterns.get('recency_pattern', 'mixed')
            
            if recency_pattern == 'recent_focused':
                # User cares about recent events
                new_weights['recency_weight'] = min(0.40, INITIAL_WEIGHTS['recency_weight'] + 0.05)
            elif recency_pattern == 'past_focused':
                # User focuses on past - decrease recency weight
                new_weights['recency_weight'] = max(0.20, INITIAL_WEIGHTS['recency_weight'] - 0.05)
            
            # ===== ADJUSTMENT 3: Recurrence Boost =====
            repetition_pattern = patterns.get('repetition_pattern', {})
            repetition_count = len(repetition_pattern)
            
            if repetition_count > 3:
                # Many repeated emotions - increase recurrence weight
                new_weights['recurrence_boost'] = min(0.25, INITIAL_WEIGHTS['recurrence_boost'] + 0.05)
            elif repetition_count == 0:
                # No repetition - decrease recurrence weight
                new_weights['recurrence_boost'] = max(0.05, INITIAL_WEIGHTS['recurrence_boost'] - 0.05)
            
            # ===== ADJUSTMENT 4: Temporal Confidence =====
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
            if total_weight > 0:
                normalized_weights = {k: v/total_weight for k, v in new_weights.items()}
            else:
                normalized_weights = INITIAL_WEIGHTS.copy()
            
            # Store in history
            self.weight_adjustment_history.append({
                'timestamp': datetime.now().isoformat(),
                'message_count': self.message_count,
                'old_weights': self.adaptive_weights.copy(),
                'new_weights': normalized_weights.copy(),
                'patterns': patterns,
                'reason': self._get_adjustment_reason(self.adaptive_weights, normalized_weights)
            })
            
            return normalized_weights
        except Exception as e:
            print(f"⚠️  Error calculating adaptive weights: {e}")
            return self.adaptive_weights.copy()

    @staticmethod
    def _get_adjustment_reason(old: dict, new: dict) -> str:
        """Explain why weights changed"""
        try:
            reasons = []
            
            for key in old:
                if key in new:
                    diff = new[key] - old[key]
                    if abs(diff) > 0.01:
                        direction = "increased" if diff > 0 else "decreased"
                        reasons.append(f"{key}: {direction} by {abs(diff):.3f}")
            
            return " | ".join(reasons) if reasons else "No significant changes"
        except Exception as e:
            return f"Error: {e}"

    def _enable_weight_learning(self):
        """Enable adaptive weight learning (called when mid_term activates)"""
        try:
            print(f"\n✨ ENABLING ADAPTIVE WEIGHT LEARNING")
            print(f"   System will now adjust weights based on chat patterns...\n")
            
            # Calculate initial adaptive weights
            self.adaptive_weights = self._calculate_adaptive_weights()
            
            print(f"📊 Initial Adaptive Weights:")
            for weight_name, value in self.adaptive_weights.items():
                print(f"   {weight_name:25s}: {value:.4f} ({value*100:.1f}%)")
            print()
        except Exception as e:
            print(f"⚠️  Error enabling weight learning: {e}")

    def _update_adaptive_weights(self):
        """
        Update weights periodically based on new chat patterns
        Called every 10 messages after mid-term activation
        """
        if not self.weights_learning_enabled:
            return
        
        try:
            old_weights = self.adaptive_weights.copy()
            self.adaptive_weights = self._calculate_adaptive_weights()
            
            # Check if weights actually changed
            weight_changed = any(
                abs(self.adaptive_weights.get(k, 0) - old_weights.get(k, 0)) > 0.01 
                for k in old_weights
            )
            
            if weight_changed:
                print(f"\n🔄 WEIGHT ADJUSTMENT at Message {self.message_count}")
                print(f"   Analyzing chat patterns and updating weights...\n")
                
                for weight_name in old_weights:
                    old_val = old_weights[weight_name]
                    new_val = self.adaptive_weights.get(weight_name, old_val)
                    change = new_val - old_val
                    
                    if abs(change) > 0.001:
                        direction = "↑" if change > 0 else "↓"
                        print(f"   {direction} {weight_name:25s}: {old_val:.4f} → {new_val:.4f}")
                print()
        except Exception as e:
            print(f"⚠️  Error updating adaptive weights: {e}")

    # ============================================================
    # STATE AGGREGATION
    # ============================================================

    def _update_mid_term_rolling_window(self):
        """Update mid-term state using rolling window"""
        try:
            if not self.is_state_activated('mid_term'):
                return
            
            window_size = STATE_ACTIVATION_CONFIG['mid_term'].get('window_size', 15)
            recent_messages = self.message_history[-window_size:]
            
            if not recent_messages:
                return
            
            # Aggregate emotions from recent messages
            emotion_sums = {emotion: 0.0 for emotion in ALL_EMOTIONS}
            for msg in recent_messages:
                emotions = msg.get('emotions_detected', {})
                impact = msg.get('impact_score', 1.0)
                for emotion, score in emotions.items():
                    if emotion in emotion_sums:
                        emotion_sums[emotion] += score * impact
            
            # Normalize
            total = sum(emotion_sums.values())
            if total > 0:
                self.mid_term_state = {
                    emotion: emotion_sums[emotion] / total
                    for emotion in ALL_EMOTIONS
                }
        except Exception as e:
            print(f"⚠️  Error updating mid-term rolling window: {e}")

    def _update_long_term_frequency_based(self):
        """Update long-term state based on frequency analysis"""
        try:
            if not self.is_state_activated('long_term'):
                return
            
            if not self.message_history:
                return
            
            # Get top 3 emotions by frequency
            top_emotions = self.get_top_emotions_by_frequency(top_n=3)
            
            if not top_emotions:
                return
            
            # Reset long-term state
            self.long_term_state = {emotion: 0.0 for emotion in ALL_EMOTIONS}
            
            # Distribute weight among top 3 emotions
            total_frequency = sum(freq for _, _, freq in top_emotions)
            if total_frequency > 0:
                for emotion, avg_score, frequency in top_emotions:
                    weight = frequency / total_frequency
                    self.long_term_state[emotion] = weight * avg_score
            
            # Normalize
            self._normalize_state('long_term')
        except Exception as e:
            print(f"⚠️  Error updating long-term frequency state: {e}")

    # ============================================================
    # QUERY METHODS
    # ============================================================

    def get_top_emotions_by_frequency(self, top_n: int = 3) -> List[Tuple[str, float, int]]:
        """
        Get top emotions by frequency across all messages
        
        Args:
            top_n: Number of top emotions to return
        
        Returns:
            List of (emotion, avg_score, frequency) tuples
        """
        try:
            if not self.message_history:
                return []
            
            emotion_data = {}
            
            for msg in self.message_history:
                emotions = msg.get('emotions_detected', {})
                for emotion, score in emotions.items():
                    if emotion not in emotion_data:
                        emotion_data[emotion] = {'scores': [], 'count': 0}
                    emotion_data[emotion]['scores'].append(score)
                    emotion_data[emotion]['count'] += 1
            
            if not emotion_data:
                return []
            
            # Calculate average scores and frequencies
            emotion_stats = []
            for emotion, data in emotion_data.items():
                avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0.0
                frequency = data['count']
                emotion_stats.append((emotion, avg_score, frequency))
            
            # Sort by frequency (descending), then by avg_score
            emotion_stats.sort(key=lambda x: (x[2], x[1]), reverse=True)
            
            return emotion_stats[:top_n]
        except Exception as e:
            print(f"⚠️  Error getting top emotions by frequency: {e}")
            return []

    def get_all_states_with_top_emotions(self, top_n: int = 5) -> Dict[str, List[Tuple[str, float]]]:
        """
        Get top N emotions for all three states
        
        Args:
            top_n: Number of top emotions per state
        
        Returns:
            Dict with state names as keys and lists of (emotion, score) tuples
        """
        try:
            result = {}
            
            # Short-term (always active)
            sorted_short = sorted(
                self.short_term_state.items(),
                key=lambda x: x[1],
                reverse=True
            )
            result['short_term'] = sorted_short[:top_n]
            
            # Mid-term (if active)
            if self.is_state_activated('mid_term'):
                sorted_mid = sorted(
                    self.mid_term_state.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                result['mid_term'] = sorted_mid[:top_n]
            else:
                result['mid_term'] = [("N/A", 0.0)]
            
            # Long-term (if active)
            if self.is_state_activated('long_term'):
                sorted_long = sorted(
                    self.long_term_state.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                result['long_term'] = sorted_long[:top_n]
            else:
                result['long_term'] = [("N/A", 0.0)]
            
            return result
        except Exception as e:
            print(f"⚠️  Error getting all states: {e}")
            return {
                'short_term': [("N/A", 0.0)],
                'mid_term': [("N/A", 0.0)],
                'long_term': [("N/A", 0.0)]
            }

    def get_top_emotions_or_placeholder(self, state_type: str, top_n: int = 1) -> List[Tuple[str, float]]:
        """
        Get top emotions for a state or placeholder if not active
        
        Args:
            state_type: 'short_term', 'mid_term', or 'long_term'
            top_n: Number of emotions to return
        
        Returns:
            List of (emotion, score) tuples or [("N/A", 0.0)]
        """
        try:
            if not self.is_state_activated(state_type):
                return [("N/A", 0.0)]
            
            if state_type == 'short_term':
                state = self.short_term_state
            elif state_type == 'mid_term':
                state = self.mid_term_state
            elif state_type == 'long_term':
                state = self.long_term_state
            else:
                return [("N/A", 0.0)]
            
            sorted_emotions = sorted(
                state.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            result = sorted_emotions[:top_n]
            return result if result else [("N/A", 0.0)]
        except Exception as e:
            print(f"⚠️  Error getting top emotions for {state_type}: {e}")
            return [("N/A", 0.0)]

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        try:
            activation_info = self.get_state_activation_info()
            
            return {
                'user_id': self.user_id,
                'created_at': self.created_at.isoformat(),
                'last_updated': self.last_updated.isoformat(),
                'message_count': self.message_count,
                'profile_age_days': self.profile_age_days,
                'short_term_state': self.short_term_state,
                'mid_term_state': self.mid_term_state,
                'long_term_state': self.long_term_state,
                'top_emotions': self.get_all_states_with_top_emotions(),
                'state_activation_info': activation_info,
                'adaptive_weights': self.adaptive_weights,
                'weights_learning_enabled': self.weights_learning_enabled,
                'message_history_count': len(self.message_history),
            }
        except Exception as e:
            print(f"⚠️  Error converting profile to dict: {e}")
            return {
                'user_id': self.user_id,
                'error': str(e)
            }

    def to_json(self) -> str:
        """Convert profile to JSON string"""
        try:
            return json.dumps(self.to_dict(), indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Error converting profile to JSON: {e}")
            return json.dumps({'user_id': self.user_id, 'error': str(e)})

    def save_to_file(self, filename: str) -> bool:
        """
        Save profile to JSON file
        
        Args:
            filename: Path to save file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if needed
            directory = os.path.dirname(filename)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            return True
        except Exception as e:
            print(f"❌ Error saving profile: {e}")
            return False

    @classmethod
    def load_from_file(cls, filename: str) -> Optional['UserProfile']:
        """
        Load profile from JSON file
        
        Args:
            filename: Path to load file
        
        Returns:
            UserProfile instance or None if failed
        """
        try:
            if not os.path.exists(filename):
                return None
            
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'user_id' not in data:
                print("❌ Error: Invalid profile file (missing user_id)")
                return None
            
            profile = cls(data['user_id'])
            
            # Load emotional states
            profile.short_term_state = {
                k: float(v) for k, v in data.get('short_term_state', {}).items()
                if k in ALL_EMOTIONS
            }
            profile.mid_term_state = {
                k: float(v) for k, v in data.get('mid_term_state', {}).items()
                if k in ALL_EMOTIONS
            }
            profile.long_term_state = {
                k: float(v) for k, v in data.get('long_term_state', {}).items()
                if k in ALL_EMOTIONS
            }
            
            # Load timestamps
            if 'created_at' in data:
                profile.created_at = datetime.fromisoformat(data['created_at'])
            if 'last_updated' in data:
                profile.last_updated = datetime.fromisoformat(data['last_updated'])
            
            # Load counts
            profile.message_count = data.get('message_count', 0)
            
            # Load adaptive weights
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
        try:
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
                info = activation_info.get(state_type, {})
                status = "✅ ACTIVE" if info.get('is_active', False) else "⏳ INACTIVE"
                threshold = STATE_ACTIVATION_CONFIG.get(state_type, {})
                
                print(f"\n{threshold.get('name', state_type)} {status}")
                print(f"   Days:     {info.get('days_progress', 0):5.1f}% ({self.profile_age_days}/{threshold.get('min_days', 0)} days)")
                print(f"   Messages: {info.get('messages_progress', 0):5.1f}% ({self.message_count}/{threshold.get('min_messages', 0)} messages)")
                
                if not info.get('is_active', False):
                    remaining = []
                    if info.get('days_remaining', 0) > 0:
                        remaining.append(f"{info['days_remaining']} days")
                    if info.get('messages_remaining', 0) > 0:
                        remaining.append(f"{info['messages_remaining']} messages")
                    if remaining:
                        print(f"   Need: {' OR '.join(remaining)}")
                else:
                    print(f"   Activated by: {info.get('activated_by', 'unknown')}")
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
                    print(f"\n   📍 Message {adjustment.get('message_count', 'N/A')}")
                    print(f"      {adjustment.get('reason', 'No reason provided')}")
            
            print("\n" + "="*100)
            
            states = self.get_all_states_with_top_emotions(top_n)
            
            # SHORT-TERM
            print(f"\n⚡ SHORT-TERM STATE (Recent: 0-30 days)")
            print("-" * 100)
            short_term_emotions = states.get('short_term', [])
            if short_term_emotions and short_term_emotions[0][0] != "N/A":
                for rank, (emotion, score) in enumerate(short_term_emotions, 1):
                    bar = "█" * int(score * 30) + "░" * int((1 - score) * 30)
                    print(f"  {rank}. {emotion:20s} │ {bar} │ {score:.4f}")
            else:
                print("  No emotions detected yet")
            
            # MID-TERM
            if activation_info.get('mid_term', {}).get('is_active', False):
                print(f"\n📈 MID-TERM STATE (Medium: 31-365 days) ✅ ACTIVE")
                print(f"   (Rolling window of 15 messages)")
                print("-" * 100)
                mid_term_emotions = states.get('mid_term', [])
                if mid_term_emotions and mid_term_emotions[0][0] != "N/A":
                    for rank, (emotion, score) in enumerate(mid_term_emotions, 1):
                        bar = "█" * int(score * 30) + "░" * int((1 - score) * 30)
                        print(f"  {rank}. {emotion:20s} │ {bar} │ {score:.4f}")
                else:
                    print("  No emotions in window yet")
            else:
                print(f"\n📈 MID-TERM STATE (Medium: 31-365 days) ⏳ INACTIVE")
                print("-" * 100)
                mid_info = activation_info.get('mid_term', {})
                print(f"  Unlocks in: {mid_info.get('days_remaining', 14)} days OR {mid_info.get('messages_remaining', 40)} messages")
            
            # LONG-TERM
            if activation_info.get('long_term', {}).get('is_active', False):
                print(f"\n🏛️  LONG-TERM STATE (Baseline: 365+ days) ✅ ACTIVE")
                print(f"   (Top 3 emotions by frequency from all {len(self.message_history)} messages)")
                print("-" * 100)
                
                # Show frequency analysis
                top_by_freq = self.get_top_emotions_by_frequency(top_n=3)
                if top_by_freq:
                    for rank, (emotion, avg_score, frequency) in enumerate(top_by_freq, 1):
                        print(f"  {rank}. {emotion:20s} │ Avg: {avg_score:.4f} │ Frequency: {frequency} messages")
                
                long_term_emotions = states.get('long_term', [])
                if long_term_emotions and long_term_emotions[0][0] != "N/A":
                    print("\n  Current State Distribution:")
                    for rank, (emotion, score) in enumerate(long_term_emotions, 1):
                        bar = "█" * int(score * 30) + "░" * int((1 - score) * 30)
                        print(f"  {rank}. {emotion:20s} │ {bar} │ {score:.4f}")
                else:
                    print("  No baseline established yet")
            else:
                print(f"\n🏛️  LONG-TERM STATE (Baseline: 365+ days) ⏳ INACTIVE")
                print("-" * 100)
                long_info = activation_info.get('long_term', {})
                print(f"  Unlocks in: {long_info.get('days_remaining', 90)} days OR {long_info.get('messages_remaining', 150)} messages")
            
            print("\n" + "="*100 + "\n")
        except Exception as e:
            print(f"\n❌ Error displaying profile: {e}\n")


if __name__ == "__main__":
    print("🎯 User Profile Manager - Enhanced Edition\n")
    
    try:
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
            print("Please chat first using test_orchestrator.py\n")
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")