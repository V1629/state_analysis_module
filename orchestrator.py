"""
Emotional State Orchestrator
Combines temporal extraction + emotion detection
Analyzes incident impact and updates user profile accordingly
NOW WITH: Adaptive weight learning and production-grade impact calculation
"""

import math
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from temporal_extractor import TemporalExtractor
from emotional_detector import classify_emotions
from user_profile import UserProfile, ALL_EMOTIONS, INITIAL_WEIGHTS


# ==========================================================
# IMPACT CALCULATION MODELS
# ==========================================================

class ImpactCalculator:
    """
    Calculate how much an incident impacts user's emotional state
    Using weighted sum approach (production-grade)
    + REPETITION BOOST for repeated incidents
    + ADAPTIVE WEIGHTS from user patterns
    """

    # Class variables for behavioral analysis
    typing_speed_mean = 1.0  # Default typing speed
    typing_speed_std = 0.5   # Default standard deviation

    # ==========================================================
    # RECENCY WEIGHTING
    # ==========================================================

    @staticmethod
    def calculate_recency_weight(days_ago: int, max_days: int = 730) -> float:
        """
        Exponential decay function for past events
        
        Formula: weight = e^(-lambda * days_ago)
        
        Where:
        - Recent events (0-30 days): weight ≈ 1.0 (full impact)
        - Medium events (31-365 days): weight ≈ 0.1-0.9 (medium impact)
        - Old events (>365 days): weight → 0 (low impact)
        
        Args:
            days_ago: Number of days in the past
            max_days: Reference point for decay (default 730 = 2 years)
        
        Returns:
            Weight factor [0, 1]
        """
        if days_ago < 0:  # Future events
            return 0.7  # Anticipatory emotions
        
        # Lambda = ln(0.05) / max_days ≈ 0.0041
        lambda_factor = math.log(0.05) / max_days
        weight = math.exp(lambda_factor * days_ago)
        
        return max(0.0, min(1.0, weight))

    @staticmethod
    def calculate_emotion_intensity(emotions_dict: Dict[str, float]) -> float:
        """
        Calculate normalized intensity from emotion probabilities
        
        intensity = max_probability * (1 - entropy_penalty)
        
        Where entropy_penalty reduces intensity if emotions are distributed
        (avoids overweighting uncertain emotions)
        
        Args:
            emotions_dict: {emotion_name: probability}
        
        Returns:
            Intensity score [0, 1]
        """
        if not emotions_dict:
            return 0.0
        
        max_prob = max(emotions_dict.values())
        
        # Shannon entropy (normalized)
        entropy = 0.0
        for p in emotions_dict.values():
            if p > 0:
                entropy -= p * math.log(p)
        
        n_emotions = len(emotions_dict)
        if n_emotions > 1:
            normalized_entropy = entropy / math.log(n_emotions)
        else:
            normalized_entropy = 0.0
        
        # High entropy (uncertain) → penalty; Low entropy (confident) → no penalty
        entropy_penalty = normalized_entropy * 0.3
        
        intensity = max_prob * (1 - entropy_penalty)
        
        return max(0.0, min(1.0, intensity))

    @staticmethod
    def calculate_recurrence_boost(incident_count: int) -> float:
        """
        Increase emotional weight if same emotion appears repeatedly
        
        Formula: boost = 1 + (incident_count - 1) * 0.3
        
        Example:
        - First occurrence: boost = 1.0 (no boost)
        - Second occurrence: boost = 1.3 (30% increase)
        - Third occurrence: boost = 1.6 (60% increase)
        - Caps at 2.5x
        
        Args:
            incident_count: Number of times emotion has been detected
        
        Returns:
            Boost multiplier [1.0, 2.5]
        """
        boost = 1 + (max(0, incident_count - 1) * 0.3)
        return min(2.5, boost)

    # ==========================================================
    # STATE IMPACT DISTRIBUTION
    # ==========================================================

    @staticmethod
    def get_state_impact_multipliers(age_category: str) -> Dict[str, float]:
        """
        Determine which emotional states are affected by incident
        based on temporal category
        
        Args:
            age_category: 'recent', 'medium', 'distant', 'future', or 'unknown'
        
        Returns:
            {
                'short_term': multiplier [0, 1],
                'mid_term': multiplier [0, 1],
                'long_term': multiplier [0, 1]
            }
        """
        impact_map = {
            "recent": {
                "short_term": 1.0,    # Full impact on recent state
                "mid_term": 0.6,      # Moderate spillover
                "long_term": 0.2      # Minimal on long-term
            },
            "medium": {
                "short_term": 0.3,    # Decaying impact on short-term
                "mid_term": 0.9,      # Primary impact on mid-term
                "long_term": 0.5      # Moderate on long-term
            },
            "distant": {
                "short_term": 0.05,   # Negligible on short-term
                "mid_term": 0.3,      # Low on mid-term
                "long_term": 0.8      # High impact on long-term (historical)
            },
            "unknown": {
                "short_term": 0.5,    # Assume recent
                "mid_term": 0.5,
                "long_term": 0.3
            },
            "future": {
                "short_term": 0.7,    # Strong anticipatory emotions
                "mid_term": 0.4,      # Moderate projection
                "long_term": 0.0      # Never update long-term for future
            }
        }
        
        return impact_map.get(age_category, impact_map["unknown"])
    

    # ----------------------------
    # Behavioral Multiplier
    # ----------------------------
    @staticmethod
    def calculate_behavior_multiplier(message_length: int, writing_time: float) -> float:
        """
        Calculate behavior multiplier based on typing speed
        
        Args:
            message_length: Length of message
            writing_time: Time taken to write message
        
        Returns:
            Multiplier [0.8, 1.2]
        """
        # Avoid division by zero
        if writing_time <= 0:
            return 1.0

        # Calculate typing speed
        speed = message_length / writing_time
        
        # Use class variables
        mu = ImpactCalculator.typing_speed_mean
        sigma = max(ImpactCalculator.typing_speed_std, 0.1)

        # Calculate z-score
        z = (speed - mu) / sigma
        
        # Influence cap at 20%
        alpha = 0.2

        # Use tanh to bound the result
        behavior_mult = 1 + alpha * math.tanh(abs(z))
        
        return max(0.8, min(1.2, behavior_mult))
    

    # ==========================================================
    # UPDATE TYPING BASELINE
    # ==========================================================

    @staticmethod
    def update_typing_baseline(speed: float) -> None:
        """
        Update typing speed baseline using exponential moving average
        
        Args:
            speed: Current typing speed (chars per second)
        """
        beta = 0.05

        mu = ImpactCalculator.typing_speed_mean
        ImpactCalculator.typing_speed_mean = beta * speed + (1 - beta) * mu

    # ==========================================================
    # COMPOUND IMPACT CALCULATION - PRODUCTION GRADE
    # ==========================================================

    @staticmethod
    def calculate_compound_impact(
        emotion_intensity: float,
        recency_weight: float,
        temporal_confidence: float,
        recurrence_boost: float = 1.0,
        writing_time: float = 0.0,
        message_length: int = 0,
        adaptive_weights: dict = None,

    ) -> float:
        """
        Calculate final compound impact weight using WEIGHTED SUM approach
        WITH ADAPTIVE WEIGHTS (PRODUCTION-GRADE)
        
        Production-ready formula:
        base_impact = (w_ei × emotion_intensity) 
                    + (w_rw × recency_weight) 
                    + (w_tc × temporal_confidence)
                    + (w_rb × recurrence_boost)
        
        Then apply behavior multiplier
        
        Args:
            emotion_intensity: Intensity of emotion (0-1)
            recency_weight: How recent is the event (0-1)
            temporal_confidence: How confident about timing (0-1)
            recurrence_boost: Boost from repeated incidents (1.0-2.5)
            writing_time: Time taken to write message
            message_length: Length of message
            adaptive_weights: User-specific weights (if None, use initial)
        
        Returns:
            Compound weight [0, 1]
        """
        
        # Use adaptive weights if provided, otherwise use initial
        if adaptive_weights is None:
            adaptive_weights = INITIAL_WEIGHTS
        
        # Normalize recurrence_boost to 0-1 range for fair weighting
        # (since it ranges from 1.0-2.5, map it to 0-1)
        normalized_recurrence = (recurrence_boost - 1.0) / 1.5
        
        # ===== WEIGHTED SUM APPROACH WITH ADAPTIVE WEIGHTS =====
        base_impact = (
            (adaptive_weights['emotion_intensity'] * emotion_intensity) +
            (adaptive_weights['recency_weight'] * recency_weight) +
            (adaptive_weights['temporal_confidence'] * temporal_confidence) +
            (adaptive_weights['recurrence_boost'] * normalized_recurrence)
        )
        
        # Normalize to [0, 1] since we're using weighted sum
        base_impact = max(0.0, min(1.0, base_impact))
        
        # ===== APPLY BEHAVIOR MULTIPLIER =====
        behavior_multiplier = ImpactCalculator.calculate_behavior_multiplier(
            message_length, 
            writing_time
        )
        
        # Final impact with behavior adjustment
        final_impact = base_impact * behavior_multiplier
        
        # Update typing baseline
        if writing_time > 0:
            speed = message_length / writing_time
            ImpactCalculator.update_typing_baseline(speed)
        
        # Clamp to valid range
        return max(0.0, min(1.0, final_impact))


# ==========================================================
# INCIDENT ANALYZER
# ==========================================================

@dataclass
class IncidentAnalysis:
    """Result of analyzing an incident"""
    original_message: str
    emotions_detected: Dict[str, float]
    temporal_references: Dict[str, Any]
    impact_score: float
    state_updates: Dict[str, Dict[str, float]]
    analysis_summary: str
    recurrence_count: int = 0
    current_state: Dict[str, List] = None  # Current emotional state for logging
    profile_state: Dict[str, List] = None  # Profile state for logging


# ==========================================================
# INCIDENT DETECTOR (REPETITION TRACKING)
# ==========================================================

class IncidentDetector:
    """
    Detects if current message is about a repeated incident
    Compares with message history to find similar incidents
    """
    
    @staticmethod
    def extract_entities(message: str) -> List[str]:
        """
        Extract key entities/topics from message
        
        Simple approach: extract capitalized words (names) + key emotional words
        More advanced: would use NER (Named Entity Recognition)
        
        Args:
            message: User message
        
        Returns:
            List of entities/keywords
        """
        entities = []
        
        # Extract capitalized words (likely names)
        words = message.split()
        for word in words:
            # Remove punctuation and check if capitalized
            clean_word = word.strip('.,!?;:')
            if clean_word and clean_word[0].isupper() and len(clean_word) > 1:
                entities.append(clean_word.lower())
        
        # Extract key emotional keywords
        emotional_keywords = [
            'died', 'death', 'passed away', 'passed', 'loss',
            'broken', 'heartbroken', 'sad', 'sadness',
            'miss', 'missing', 'loss', 'gone',
            'accident', 'injury', 'hurt', 'pain',
            'promoted', 'success', 'achievement', 'won',
            'celebration', 'happy', 'joy', 'celebrate',
            'grandmother', 'grandfather', 'father', 'mother',
            'brother', 'sister', 'friend', 'love', 'loved',
            'breakup', 'broke up', 'divorced', 'separated'
        ]
        
        message_lower = message.lower()
        for keyword in emotional_keywords:
            if keyword in message_lower:
                entities.append(keyword)
        
        return list(set(entities))  # Remove duplicates

    @staticmethod
    def calculate_similarity(current_entities: List[str], history_entities: List[str]) -> float:
        """
        Calculate similarity between two sets of entities
        
        Uses Jaccard similarity: |intersection| / |union|
        
        Args:
            current_entities: Entities in current message
            history_entities: Entities in historical message
        
        Returns:
            Similarity score [0, 1]
        """
        if not current_entities or not history_entities:
            return 0.0
        
        current_set = set(current_entities)
        history_set = set(history_entities)
        
        intersection = len(current_set & history_set)
        union = len(current_set | history_set)
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        return similarity

    @staticmethod
    def find_repeated_incidents(
        current_message: str,
        message_history: List[Dict],
        similarity_threshold: float = 0.2
    ) -> Dict[str, Any]:
        """
        Find similar incidents in message history
        
        Args:
            current_message: Current user message
            message_history: List of previous messages
            similarity_threshold: Minimum similarity to count as repeat (0-1)
        
        Returns:
            {
                'incident_count': int,
                'similar_messages': List[Dict],
                'top_entities': List[str],
                'average_similarity': float
            }
        """
        if not message_history:
            return {
                'incident_count': 1,
                'similar_messages': [],
                'top_entities': [],
                'average_similarity': 0.0
            }
        
        # Extract entities from current message
        current_entities = IncidentDetector.extract_entities(current_message)
        
        if not current_entities:
            return {
                'incident_count': 1,
                'similar_messages': [],
                'top_entities': [],
                'average_similarity': 0.0
            }
        
        # Compare with history
        similar_messages = []
        similarities = []
        
        for history_entry in message_history:
            history_message = history_entry.get('message', '')
            history_entities = IncidentDetector.extract_entities(history_message)
            
            similarity = IncidentDetector.calculate_similarity(
                current_entities, 
                history_entities
            )
            
            # If similarity exceeds threshold, consider it a similar incident
            if similarity >= similarity_threshold:
                similar_messages.append({
                    'message': history_message,
                    'timestamp': history_entry.get('timestamp', ''),
                    'similarity': similarity,
                    'emotions': history_entry.get('emotions_detected', {})
                })
                similarities.append(similarity)
        
        # Count includes current message + similar ones found
        incident_count = 1 + len(similar_messages)
        average_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        
        return {
            'incident_count': incident_count,
            'similar_messages': similar_messages,
            'top_entities': current_entities,
            'average_similarity': average_similarity
        }


# ==========================================================
# MAIN ORCHESTRATOR
# ==========================================================

class EmotionalStateOrchestrator:
    """
    Main orchestrator that combines:
    1. Temporal extraction
    2. Emotion detection
    3. Incident repetition detection
    4. Impact calculation (with adaptive weights)
    5. User profile updates (with advanced state aggregation)
    """

    def __init__(self):
        self.temporal_extractor = TemporalExtractor()
        self.impact_calculator = ImpactCalculator()
        self.incident_detector = IncidentDetector()
        self.user_profiles: Dict[str, UserProfile] = {}

    # ============================================================
    # CORE PROCESSING
    # ============================================================

    def process_user_message(
        self,
        user_id: str,
        message: str,
        reference_date: Optional[datetime] = None,
        writing_time: float = 0.0

    ) -> IncidentAnalysis:
        """
        Main pipeline: Process single user message through full pipeline
        
        Steps:
        1. Detect emotions in message
        2. Extract temporal references
        3. Detect if incident is repeated
        4. Calculate incident impact (with adaptive weights)
        5. Update user profile (with advanced state aggregation)
        6. Return analysis
        
        Args:
            user_id: Unique user identifier
            message: User's message
            reference_date: Current date (default: now)
            writing_time: Time taken to write the message
        
        Returns:
            IncidentAnalysis object with full details
        """
        
        if reference_date is None:
            reference_date = datetime.now()
        