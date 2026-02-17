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
from user_profile import UserProfile, ALL_EMOTIONS, INITIAL_WEIGHTS, get_effective_alpha


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
    def calculate_emotion_intensity(emotions_dict: Dict[str, float], entropy_penalty_coeff: float = 0.3) -> float:
        """
        Calculate normalized intensity from emotion probabilities
        
        intensity = max_probability * (1 - entropy_penalty)
        
        Where entropy_penalty reduces intensity if emotions are distributed
        (avoids overweighting uncertain emotions)
        
        Args:
            emotions_dict: {emotion_name: probability}
            entropy_penalty_coeff: Per-user entropy penalty coefficient (default 0.3)
        
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
        entropy_penalty = max(0, normalized_entropy - entropy_penalty_coeff)
        
        intensity = max_prob * (1 - entropy_penalty)
        
        return max(0.0, min(1.0, intensity))

    @staticmethod
    def calculate_recurrence_boost(incident_count: int, recurrence_step: float = 0.3) -> float:
        """
        Increase emotional weight if same emotion appears repeatedly
        
        Formula: boost = 1 + (incident_count - 1) * recurrence_step
        
        Example (with default recurrence_step=0.3):
        - First occurrence: boost = 1.0 (no boost)
        - Second occurrence: boost = 1.3 (30% increase)
        - Third occurrence: boost = 1.6 (60% increase)
        - Caps at 2.5x
        
        Args:
            incident_count: Number of times emotion has been detected
            recurrence_step: Per-user step size for recurrence boost (default 0.3)
        
        Returns:
            Boost multiplier [1.0, 2.5]
        """
        boost = 1 + (max(0, incident_count - 1) * recurrence_step)
        return min(2.5, boost)

    # ==========================================================
    # STATE IMPACT DISTRIBUTION
    # ==========================================================

    @staticmethod
    def get_state_impact_multipliers(age_category: str, user_multipliers: Dict = None) -> Dict[str, float]:
        """
        Determine which emotional states are affected by incident
        based on temporal category
        
        Args:
            age_category: 'recent', 'medium', 'distant', 'future', or 'unknown'
            user_multipliers: Optional per-user multiplier overrides
        
        Returns:
            {
                'short_term': multiplier [0, 1],
                'mid_term': multiplier [0, 1],
                'long_term': multiplier [0, 1]
            }
        """
        default_map = {
            "recent": {"short_term": 1.0, "mid_term": 0.6, "long_term": 0.2},
            "medium": {"short_term": 0.3, "mid_term": 0.9, "long_term": 0.5},
            "distant": {"short_term": 0.05, "mid_term": 0.3, "long_term": 0.8},
            "unknown": {"short_term": 0.5, "mid_term": 0.5, "long_term": 0.3},
            "future": {"short_term": 0.7, "mid_term": 0.4, "long_term": 0.0}
        }
        
        impact_map = user_multipliers if user_multipliers else default_map
        return impact_map.get(age_category, impact_map.get("unknown", default_map["unknown"]))
    

    # ----------------------------
    # Behavioral Multiplier
    # ----------------------------
    @staticmethod
    def calculate_behavior_multiplier(message_length: int, writing_time: float, behavior_alpha: float = 0.2) -> float:
        """
        Calculate behavior multiplier based on typing speed
        
        Args:
            message_length: Length of message
            writing_time: Time taken to write message
            behavior_alpha: Per-user influence cap (default 0.2)
        
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
        
        # Influence cap
        alpha = behavior_alpha

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
        Updates both mean and std (MAD-based)
        
        Args:
            speed: Current typing speed (chars per second)
        """
        beta = 0.05

        mu = ImpactCalculator.typing_speed_mean
        ImpactCalculator.typing_speed_mean = beta * speed + (1 - beta) * mu

        # EMA update for std using Mean Absolute Deviation
        sigma = ImpactCalculator.typing_speed_std
        deviation = abs(speed - mu)
        ImpactCalculator.typing_speed_std = beta * deviation + (1 - beta) * sigma

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
        behavior_alpha: float = 0.2,

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
            behavior_alpha: Per-user behavior influence cap (default 0.2)
        
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
            writing_time,
            behavior_alpha=behavior_alpha
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
        
        # ==============================================================
        # STEP 1: DETECT EMOTIONS
        # ==============================================================
        
        emotions_detected = classify_emotions(message)
        
        if not emotions_detected:
            # No emotions detected - return minimal analysis
            return IncidentAnalysis(
                original_message=message,
                emotions_detected={},
                temporal_references={
                    'has_temporal_ref': False,
                    'phrases_found': [],
                    'parsed_dates': []
                },
                impact_score=0.0,
                state_updates={},
                analysis_summary="No emotions detected in message",
                recurrence_count=0
            )
        
        # ==============================================================
        # STEP 2: EXTRACT TEMPORAL REFERENCES
        # ==============================================================
        
        temporal_info = self.temporal_extractor.extract_temporal_references(
            message, 
            reference_date
        )
        
        # Get age category for impact calculation
        age_category = "unknown"
        temporal_confidence = 0.5  # Default medium confidence
        days_ago = 0
        
        if temporal_info['has_temporal_ref'] and temporal_info['parsed_dates']:
            # Use the first (highest confidence) temporal reference
            best_match = temporal_info['parsed_dates'][0]
            ###By usig these three lines we take out age category , temporal_confidence and how many days ago it had happened
            age_category = best_match.get('age_category', 'unknown')
            temporal_confidence = best_match.get('confidence', 0.5)
            days_ago = best_match.get('days_ago', 0)
        

        
        # ==============================================================
        # STEP 3: INITIALIZE OR GET USER PROFILE
        # ==============================================================
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id)
        
        profile = self.user_profiles[user_id]
        
        # ==============================================================
        # STEP 4: DETECT REPEATED INCIDENTS
        # ==============================================================
        
        repetition_info = self.incident_detector.find_repeated_incidents(
            current_message=message,
            message_history=profile.message_history,
            similarity_threshold=profile.similarity_threshold
        )
        
        incident_count = repetition_info['incident_count']
        
        # ==============================================================
        # STEP 5: CALCULATE IMPACT
        # ==============================================================
        
        # Calculate emotion intensity
        emotion_intensity = self.impact_calculator.calculate_emotion_intensity(
            emotions_detected, entropy_penalty_coeff=profile.entropy_penalty_coeff
        )
        
        # Calculate recency weight
        recency_weight = self.impact_calculator.calculate_recency_weight(days_ago)
        
        # Calculate recurrence boost
        recurrence_boost = self.impact_calculator.calculate_recurrence_boost(
            incident_count, recurrence_step=profile.recurrence_step
        )
        
        # Get adaptive weights from profile
        adaptive_weights = profile.adaptive_weights
        
        # Calculate compound impact
        impact_score = self.impact_calculator.calculate_compound_impact(
            emotion_intensity=emotion_intensity,
            recency_weight=recency_weight,
            temporal_confidence=temporal_confidence,
            recurrence_boost=recurrence_boost,
            writing_time=writing_time,
            message_length=len(message),
            adaptive_weights=adaptive_weights,
            behavior_alpha=profile.behavior_alpha
        )
        
        # ==============================================================
        # STEP 6: GET STATE IMPACT MULTIPLIERS
        # ==============================================================
        
        state_multipliers = self.impact_calculator.get_state_impact_multipliers(
            age_category, user_multipliers=profile.impact_multipliers
        )
        
        # ==============================================================
        # STEP 7: UPDATE USER PROFILE
        # ==============================================================
        
        state_updates = {}
        
        for emotion, score in emotions_detected.items():
            # Calculate weighted impact for each state
            weighted_impacts = {
                'short_term': score * impact_score * state_multipliers['short_term'],
                'mid_term': score * impact_score * state_multipliers['mid_term'],
                'long_term': score * impact_score * state_multipliers['long_term']
            }
            
            state_updates[emotion] = weighted_impacts
        
        # Store computed factors on profile for adaptive weight learning
        normalized_recurrence = (recurrence_boost - 1.0) / 1.5
        profile._last_computed_factors = {
            'emotion_intensity': emotion_intensity,
            'recency_weight': recency_weight,
            'recurrence_boost': normalized_recurrence,
            'temporal_confidence': temporal_confidence,
        }
        
        # Update profile with new emotional data
        profile.update_emotional_state(
            emotions=emotions_detected,
            impact_score=impact_score,
            state_updates=state_updates,
            message=message,
            timestamp=reference_date,
            temporal_category=age_category
        )
        
        # ==============================================================
        # STEP 7b: UPDATE PER-USER EMA PARAMETERS
        # ==============================================================
        
        # Update entropy_penalty_coeff (Parameter 7)
        if emotions_detected:
            entropy = 0.0
            for p in emotions_detected.values():
                if p > 0:
                    entropy -= p * math.log(p)
            n_emo = len(emotions_detected)
            h_norm = entropy / math.log(n_emo) if n_emo > 1 else 0.0
            alpha_e = get_effective_alpha(0.10, profile.message_count)
            profile.entropy_penalty_coeff = alpha_e * h_norm + (1 - alpha_e) * profile.entropy_penalty_coeff
        
        # Update recurrence_step (Parameter 8)
        if incident_count > 1 and hasattr(profile, '_last_emotion_intensity'):
            delta_intensity = abs(emotion_intensity - profile._last_emotion_intensity)
            alpha_r = get_effective_alpha(0.15, profile.message_count)
            profile.recurrence_step = alpha_r * delta_intensity + (1 - alpha_r) * profile.recurrence_step
        profile._last_emotion_intensity = emotion_intensity
        
        # Update impact_multipliers (Parameter 9)
        # Use weighted average across all detected emotions
        if age_category in profile.impact_multipliers:
            alpha_m = get_effective_alpha(0.08, profile.message_count)
            for state_type in ['short_term', 'mid_term', 'long_term']:
                expected = impact_score
                if expected > 0:
                    weighted_mult_sum = 0.0
                    weight_sum = 0.0
                    for emotion, score in emotions_detected.items():
                        if emotion in profile.short_term_state:
                            actual_change = score * impact_score * state_multipliers[state_type]
                            observed_mult = actual_change / expected
                            weighted_mult_sum += observed_mult * score
                            weight_sum += score
                    if weight_sum > 0:
                        avg_observed_mult = weighted_mult_sum / weight_sum
                        old_mult = profile.impact_multipliers[age_category][state_type]
                        profile.impact_multipliers[age_category][state_type] = (
                            alpha_m * avg_observed_mult + (1 - alpha_m) * old_mult
                        )
        
        # Update behavior_alpha (Parameter 10)
        # Correlation proxy: measures co-occurrence of typing speed deviation
        # (z-score) with emotion intensity. High z × high intensity suggests
        # typing speed is a meaningful emotional signal for this user.
        if writing_time > 0:
            speed = len(message) / writing_time
            mu = ImpactCalculator.typing_speed_mean
            sigma = max(ImpactCalculator.typing_speed_std, 0.1)
            z = abs((speed - mu) / sigma)
            correlation_proxy = min(1.0, z * emotion_intensity)
            alpha_b = get_effective_alpha(0.10, profile.message_count)
            profile.behavior_alpha = alpha_b * (0.5 * correlation_proxy) + (1 - alpha_b) * profile.behavior_alpha
        
        # Update similarity_threshold (Parameter 14)
        # Only update when there are actual repetitions to avoid driving toward 0
        avg_sim = repetition_info.get('average_similarity', 0.0)
        if avg_sim > 0:
            alpha_theta = get_effective_alpha(0.10, profile.message_count)
            profile.similarity_threshold = alpha_theta * avg_sim + (1 - alpha_theta) * profile.similarity_threshold
            profile.similarity_threshold = max(0.1, min(0.4, profile.similarity_threshold))
        
        # ==============================================================
        # STEP 8: GENERATE ANALYSIS SUMMARY
        # ==============================================================
        
        # Get top emotion
        top_emotion = max(emotions_detected.items(), key=lambda x: x[1])
        top_emotion_name = top_emotion[0]
        top_emotion_score = top_emotion[1]
        
        # Build summary
        summary_parts = []
        summary_parts.append(f"Primary emotion: {top_emotion_name} ({top_emotion_score:.2f})")
        
        if temporal_info['has_temporal_ref']:
            summary_parts.append(f"Temporal reference: {age_category}")
        
        if incident_count > 1:
            summary_parts.append(f"Repeated incident (x{incident_count})")
        
        summary_parts.append(f"Impact: {impact_score:.2f}")
        
        analysis_summary = " | ".join(summary_parts)
        
        # ==============================================================
        # STEP 9: RETURN ANALYSIS
        # ==============================================================
        
        return IncidentAnalysis(
            original_message=message,
            emotions_detected=emotions_detected,
            temporal_references=temporal_info,
            impact_score=impact_score,
            state_updates=state_updates,
            analysis_summary=analysis_summary,
            recurrence_count=incident_count
        )
    




    
    # ==============================================================
    # HELPER METHOD: GET USER PROFILE
    # ==============================================================
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by ID
        
        Args:
            user_id: User identifier
            
        Returns:
            UserProfile object or None if not found
        """
        return self.user_profiles.get(user_id)
    
    # ==============================================================
    # HELPER METHOD: GET ALL USER IDS
    # ==============================================================
    
    def get_all_user_ids(self) -> List[str]:
        """
        Get list of all user IDs with profiles
        
        Returns:
            List of user IDs
        """
        return list(self.user_profiles.keys())