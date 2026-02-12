"""
Emotional State Orchestrator
Combines temporal extraction + emotion detection
Analyzes incident impact and updates user profile accordingly
NOW WITH: Repetition-based incident importance detection + Advanced state aggregation
"""

import math
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from temporal_extractor import TemporalExtractor
from emotional_detector import classify_emotions
from user_profile import UserProfile, ALL_EMOTIONS


# ==========================================================
# IMPACT CALCULATION MODELS
# ==========================================================

class ImpactCalculator:
    """
    Calculate how much an incident impacts user's emotional state
    Using recency weight + emotion intensity + contextual factors
    + REPETITION BOOST for repeated incidents
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
    # COMPOUND IMPACT CALCULATION
    # ==========================================================

    @staticmethod
    def calculate_compound_impact(
        emotion_intensity: float,
        recency_weight: float,
        temporal_confidence: float,
        recurrence_boost: float = 1.0,
        writing_time: float = 0.0,
        message_length: int = 0,

    ) -> float:
        """
        Calculate final compound impact weight
        
        compound_impact = emotion_intensity 
                        × recency_weight 
                        × temporal_confidence 
                        × recurrence_boost
        
        Args:
            emotion_intensity: Intensity of emotion (0-1)
            recency_weight: How recent is the event (0-1)
            temporal_confidence: How confident we are about timing (0-1)
            recurrence_boost: Boost from repeated incidents (1.0-2.5)
            writing_time: Time taken to write message
            message_length: Length of message
        
        Returns:
            Compound weight [0, 1]
        """
        base_impact = (
            emotion_intensity 
            * recency_weight 
            * temporal_confidence 
            * recurrence_boost
        )
        
        # Calculate behavior multiplier
        behavior_multiplier = ImpactCalculator.calculate_behavior_multiplier(
            message_length, 
            writing_time
        )
        
        impact = base_impact * behavior_multiplier
        
        # Update typing baseline for future calculations
        if writing_time > 0:
            speed = message_length / writing_time
            ImpactCalculator.update_typing_baseline(speed)
        
        return max(0.0, min(1.0, impact))


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
    4. Impact calculation
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
        4. Calculate incident impact (with repetition boost)
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
        
        # Get or create user profile
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id)
        
        user_profile = self.user_profiles[user_id]
        
        # ===== PHASE 1: EMOTION DETECTION =====
        emotions_detected = self._detect_emotions(message)
        
        # ===== PHASE 2: TEMPORAL EXTRACTION =====
        temporal_data = self._extract_temporal_references(message, reference_date)
        
        # ===== PHASE 3: INCIDENT REPETITION DETECTION =====
        repetition_data = self._detect_incident_repetition(
            message, 
            user_profile.message_history
        )
        
        # ===== PHASE 4: IMPACT CALCULATION =====
        state_updates, impact_score, summary = self._calculate_and_apply_impact(
            user_id=user_id,
            emotions_detected=emotions_detected,
            temporal_data=temporal_data,
            repetition_data=repetition_data,
            reference_date=reference_date,
            writing_time=writing_time,
            message_length=len(message)
        )
        
        # ===== PHASE 5: ADD TO HISTORY =====
        user_profile.add_message_to_history(
            message=message,
            emotions=emotions_detected,
            time_refs=temporal_data,
            impact_score=impact_score
        )
        
        # ===== PHASE 6: PROFILE UPDATE WITH ADVANCED AGGREGATION =====
        self._update_user_profile(user_profile, state_updates)
        
        # Get current state after update
        states = user_profile.get_all_states_with_top_emotions(top_n=3)
        
        # ===== RETURN ANALYSIS =====
        return IncidentAnalysis(
            original_message=message,
            emotions_detected=emotions_detected,
            temporal_references=temporal_data,
            impact_score=impact_score,
            state_updates=state_updates,
            analysis_summary=summary,
            recurrence_count=repetition_data['incident_count'],
            current_state=states,
            profile_state=states
        )

    # ============================================================
    # HELPER: EMOTION DETECTION
    # ============================================================

    def _detect_emotions(self, message: str) -> Dict[str, float]:
        """
        Detect emotions using HuggingFace classifier
        Returns top emotions only (filter out very low scores)
        
        Returns:
            {emotion_name: probability}
        """
        try:
            results = classify_emotions(message)
            
            if not results:
                return {}
            
            # Handle both list and dict returns from classify_emotions
            if isinstance(results, list):
                # Convert list format to dict
                emotions_dict = {}
                for item in results:
                    if isinstance(item, dict):
                        emotions_dict[item.get('label', '')] = item.get('score', 0)
            else:
                emotions_dict = results
            
            # Filter emotions with score < 0.01 (noise reduction)
            filtered = {k: v for k, v in emotions_dict.items() if v >= 0.01}
            
            if not filtered:
                return {}
            
            # Normalize to sum to 1
            total = sum(filtered.values())
            if total > 0:
                emotions_dict = {k: v/total for k, v in filtered.items()}
            
            return emotions_dict
        
        except Exception as e:
            print(f"❌ Emotion detection error: {e}")
            return {}

    # ============================================================
    # HELPER: TEMPORAL EXTRACTION
    # ============================================================

    def _extract_temporal_references(
        self,
        message: str,
        reference_date: datetime
    ) -> Dict[str, Any]:
        """
        Extract temporal references from message
        
        Returns:
            {
                'phrases_found': List[str],
                'parsed_dates': List[Dict],
                'has_temporal_ref': bool
            }
        """
        try:
            # Update extractor's reference time
            self.temporal_extractor.reference_time = reference_date
            
            # Process message
            result = self.temporal_extractor.process_message(message)
            
            return {
                'phrases_found': [p['text'] for p in result['time_phrases_detected']],
                'parsed_dates': result['parsed_dates'],
                'has_temporal_ref': result['summary']['has_temporal_reference'],
                'total_phrases': result['summary']['total_phrases_found'],
                'successfully_parsed': result['summary']['successfully_parsed'],
            }
        
        except Exception as e:
            print(f"❌ Temporal extraction error: {e}")
            return {
                'phrases_found': [],
                'parsed_dates': [],
                'has_temporal_ref': False,
                'total_phrases': 0,
                'successfully_parsed': 0,
            }

    # ============================================================
    # HELPER: INCIDENT REPETITION DETECTION
    # ============================================================

    def _detect_incident_repetition(
        self,
        message: str,
        message_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Detect if current message is about a repeated incident
        
        Returns:
            {
                'incident_count': int,
                'similar_messages': List[Dict],
                'top_entities': List[str],
                'average_similarity': float
            }
        """
        try:
            repetition_data = self.incident_detector.find_repeated_incidents(
                current_message=message,
                message_history=message_history,
                similarity_threshold=0.2
            )
            
            return repetition_data
        
        except Exception as e:
            print(f"❌ Incident repetition detection error: {e}")
            return {
                'incident_count': 1,
                'similar_messages': [],
                'top_entities': [],
                'average_similarity': 0.0
            }

    # ============================================================
    # HELPER: IMPACT CALCULATION
    # ============================================================

    def _calculate_and_apply_impact(
        self,
        user_id: str,
        emotions_detected: Dict[str, float],
        temporal_data: Dict[str, Any],
        repetition_data: Dict[str, Any],
        reference_date: datetime,
        writing_time: float,
        message_length: int
    ) -> tuple:
        """
        Calculate impact and determine state updates
        
        Returns:
            (state_updates_dict, overall_impact_score, summary_string)
        """
        
        state_updates = {
            'short_term': {},
            'mid_term': {},
            'long_term': {}
        }
        
        total_impact = 0.0
        impact_details = []
        
        # Only process if there are emotions to process
        if not emotions_detected:
            return state_updates, 0.0, "No emotions detected."
        
        # Get repetition boost
        incident_count = repetition_data.get('incident_count', 1)
        recurrence_boost = self.impact_calculator.calculate_recurrence_boost(incident_count)
        
        # If no temporal reference, treat as immediate/recent
        if not temporal_data['has_temporal_ref']:
            parsed_dates = [{
                'age_category': 'recent',
                'confidence': 0.5,
                'time_gap_days': 0,
            }]
        else:
            parsed_dates = temporal_data['parsed_dates']
        
        # Handle case where parsed_dates might be None or empty
        if not parsed_dates:
            parsed_dates = [{
                'age_category': 'recent',
                'confidence': 0.5,
                'time_gap_days': 0,
            }]
        
        # ===== FOR EACH DETECTED TEMPORAL REFERENCE =====
        for time_info in parsed_dates:
            age_category = time_info.get('age_category', 'unknown')
            confidence = time_info.get('confidence', 0.5)
            time_gap_days = time_info.get('time_gap_days', 0)
            
            # Calculate recency weight
            recency_weight = self.impact_calculator.calculate_recency_weight(time_gap_days)
            
            # ===== FOR EACH DETECTED EMOTION =====
            for emotion, probability in emotions_detected.items():
                # Emotion intensity
                emotion_intensity = probability
                
                # Compound impact
                compound_impact = self.impact_calculator.calculate_compound_impact(
                    emotion_intensity=emotion_intensity,
                    recency_weight=recency_weight,
                    temporal_confidence=confidence,
                    recurrence_boost=recurrence_boost,
                    writing_time=writing_time,
                    message_length=message_length,
                )
                
                # Get state multipliers
                state_multipliers = self.impact_calculator.get_state_impact_multipliers(
                    age_category
                )
                
                # Apply to each state
                for state_type, multiplier in state_multipliers.items():
                    if multiplier > 0:
                        impact_weight = compound_impact * multiplier
                        
                        if emotion not in state_updates[state_type]:
                            state_updates[state_type][emotion] = 0.0
                        
                        state_updates[state_type][emotion] += impact_weight
                
                total_impact += compound_impact
                
                impact_details.append({
                    'emotion': emotion,
                    'probability': probability,
                    'age_category': age_category,
                    'recency_weight': recency_weight,
                    'compound_impact': compound_impact,
                    'recurrence_boost': recurrence_boost,
                    'incident_count': incident_count,
                })
        
        # Normalize total impact to [0, 1]
        normalized_total_impact = min(1.0, total_impact)
        
        # Generate summary
        if impact_details:
            top_emotion = max(impact_details, key=lambda x: x['compound_impact'])
            
            if incident_count > 1:
                summary = (
                    f"Detected {top_emotion['emotion'].upper()} incident "
                    f"({top_emotion['age_category']}). "
                    f"Repeated {incident_count} times (boost: {recurrence_boost:.2f}x). "
                    f"Impact score: {normalized_total_impact:.3f}"
                )
            else:
                summary = (
                    f"Detected {top_emotion['emotion'].upper()} incident "
                    f"({top_emotion['age_category']}). "
                    f"Impact score: {normalized_total_impact:.3f}"
                )
        else:
            summary = "No significant emotional incident detected."
        
        return state_updates, normalized_total_impact, summary

    # ============================================================
    # HELPER: PROFILE UPDATE - WITH ADVANCED AGGREGATION
    # ============================================================

    def _update_user_profile(
        self,
        user_profile: UserProfile,
        state_updates: Dict[str, Dict[str, float]]
    ):
        """
        Update user profile with activation checks and smart initialization
        
        When states activate:
        - mid_term: Initializes with aggregated emotions from ALL prior messages
        - long_term: Initializes with top 3 emotions by frequency from ALL prior messages
        """
        
        # ===== CHECK FOR STATE ACTIVATIONS AND INITIALIZE =====
        
        # Mid-term: Check if just activated
        if user_profile.is_state_activated('mid_term') and not user_profile.mid_term_initialized:
            user_profile.initialize_mid_term_on_activation()
        
        # Long-term: Check if just activated
        if user_profile.is_state_activated('long_term') and not user_profile.long_term_initialized:
            user_profile.initialize_long_term_on_activation()
        
        # ===== UPDATE STATES =====
        
        # Update short-term (always active)
        if state_updates.get('short_term'):
            try:
                user_profile.update_short_term(state_updates['short_term'])
            except Exception as e:
                print(f"Error updating short-term: {e}")
        
        # Update mid-term (window-based if activated)
        if state_updates.get('mid_term'):
            try:
                user_profile.update_mid_term_with_window(state_updates['mid_term'])
            except Exception as e:
                print(f"Error updating mid-term: {e}")
        
        # Update long-term (frequency-based if activated)
        if state_updates.get('long_term'):
            try:
                user_profile.update_long_term_with_frequency(state_updates['long_term'])
            except Exception as e:
                print(f"Error updating long-term: {e}")

    # ============================================================
    # USER PROFILE RETRIEVAL
    # ============================================================

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user's emotional profile"""
        return self.user_profiles.get(user_id)

    def get_top_emotions(self, user_id: str, state_type: str, top_n: int = 5):
        """Get top N emotions for user's state"""
        profile = self.get_user_profile(user_id)
        if profile:
            return profile.get_top_emotions(state_type, top_n)
        return []

    def display_user_profile(self, user_id: str, top_n: int = 5):
        """Display user's full emotional profile"""
        profile = self.get_user_profile(user_id)
        if profile:
            profile.display_profile(top_n)
        else:
            print(f"❌ No profile found for user: {user_id}")


# ==========================================================
# FACTORY
# ==========================================================

def create_orchestrator() -> EmotionalStateOrchestrator:
    """Create and return orchestrator instance"""
    return EmotionalStateOrchestrator()