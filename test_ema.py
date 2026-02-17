"""
Tests for EMA (Exponential Moving Average) approach implementation.
Validates all 14 parameter groups from EMA_approach.md.
"""

import math
import os
import sys
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Set dummy HF token to avoid sys.exit during import
os.environ['hf_token'] = 'dummy_token_for_testing'

from user_profile import (
    UserProfile, ALL_EMOTIONS, INITIAL_WEIGHTS, get_effective_alpha
)


# ==============================================================
# PHASE 4: Adaptive Alpha
# ==============================================================

class TestGetEffectiveAlpha:
    """Test adaptive learning rate decay"""

    def test_initial_message_near_base(self):
        """Message 1 should be nearly the base alpha"""
        alpha = get_effective_alpha(0.15, 1)
        assert 0.14 < alpha < 0.16

    def test_half_life_at_K(self):
        """At K=200 messages, alpha should be half of base"""
        alpha = get_effective_alpha(0.15, 200)
        assert abs(alpha - 0.075) < 0.001

    def test_decay_monotonic(self):
        """Alpha should decrease as message count increases"""
        prev = get_effective_alpha(0.15, 0)
        for count in [10, 50, 100, 200, 500, 1000]:
            curr = get_effective_alpha(0.15, count)
            assert curr < prev, f"Alpha should decrease: {curr} >= {prev} at count={count}"
            prev = curr

    def test_always_positive(self):
        """Alpha should always be positive"""
        for count in [0, 1, 100, 10000]:
            alpha = get_effective_alpha(0.15, count)
            assert alpha > 0

    def test_zero_base_returns_zero(self):
        """Zero base alpha should return zero"""
        assert get_effective_alpha(0.0, 100) == 0.0


# ==============================================================
# PHASE 1: Adaptive Weights (Parameters 1-4)
# ==============================================================

class TestAdaptiveWeightsEMA:
    """Test EMA-based adaptive weight updates"""

    def setup_method(self):
        self.profile = UserProfile('test_user')

    def test_weights_sum_to_one_initially(self):
        """Initial weights should sum to 1.0"""
        total = sum(self.profile.adaptive_weights.values())
        assert abs(total - 1.0) < 0.001

    def test_weights_update_every_message(self):
        """Weights should change after a single message (no 10-msg checkpoint)"""
        old_weights = self.profile.adaptive_weights.copy()
        self.profile.update_emotional_state(
            emotions={'joy': 0.9, 'sadness': 0.05},
            impact_score=0.7,
            state_updates={'joy': {'short_term': 0.5, 'mid_term': 0.2, 'long_term': 0.05}},
            message='Very happy!',
            timestamp=datetime.now()
        )
        # Weights should have changed
        assert self.profile.adaptive_weights != old_weights

    def test_weights_sum_to_one_after_update(self):
        """Weights should still sum to 1.0 after updates"""
        self.profile.update_emotional_state(
            emotions={'joy': 0.8, 'anger': 0.1},
            impact_score=0.6,
            state_updates={'joy': {'short_term': 0.4, 'mid_term': 0.2, 'long_term': 0.05}},
            message='Happy message',
            timestamp=datetime.now()
        )
        total = sum(self.profile.adaptive_weights.values())
        assert abs(total - 1.0) < 0.001

    def test_weights_evolve_from_current_not_initial(self):
        """Weights should evolve from current state (momentum), not restart from initial"""
        for i in range(5):
            self.profile.update_emotional_state(
                emotions={'joy': 0.9},
                impact_score=0.8,
                state_updates={'joy': {'short_term': 0.5, 'mid_term': 0.3, 'long_term': 0.1}},
                message=f'Happy message {i}',
                timestamp=datetime.now()
            )
        weights_after_5 = self.profile.adaptive_weights.copy()

        self.profile.update_emotional_state(
            emotions={'joy': 0.9},
            impact_score=0.8,
            state_updates={'joy': {'short_term': 0.5, 'mid_term': 0.3, 'long_term': 0.1}},
            message='Happy message 6',
            timestamp=datetime.now()
        )
        # Weights should continue from weights_after_5, not jump back to INITIAL
        for key in weights_after_5:
            diff = abs(self.profile.adaptive_weights[key] - weights_after_5[key])
            # Small change from previous (EMA), not a jump
            assert diff < 0.1, f"Weight {key} jumped too much: {diff}"

    def test_no_dead_zones(self):
        """Moderate emotion (0.3-0.7) should still cause weight updates"""
        old_weights = self.profile.adaptive_weights.copy()
        self.profile.update_emotional_state(
            emotions={'neutral': 0.5},  # Moderate, was in dead zone before
            impact_score=0.4,
            state_updates={'neutral': {'short_term': 0.2, 'mid_term': 0.1, 'long_term': 0.02}},
            message='Neutral message',
            timestamp=datetime.now()
        )
        assert self.profile.adaptive_weights != old_weights


# ==============================================================
# PHASE 2: Emotional State EMA (Parameters 11-13)
# ==============================================================

class TestShortTermEMA:
    """Test short-term state EMA updates (Parameter 11)"""

    def setup_method(self):
        self.profile = UserProfile('test_user')

    def test_ema_boost_on_mention(self):
        """Emotion should increase when mentioned"""
        self.profile.update_emotional_state(
            emotions={'joy': 0.9},
            impact_score=0.8,
            state_updates={'joy': {'short_term': 0.5, 'mid_term': 0.3, 'long_term': 0.1}},
            message='Very happy!',
            timestamp=datetime.now()
        )
        assert self.profile.short_term_state['joy'] > 0

    def test_ema_decay_on_no_mention(self):
        """Emotion should decay when not mentioned"""
        # First, set joy
        self.profile.update_emotional_state(
            emotions={'joy': 0.9},
            impact_score=0.8,
            state_updates={'joy': {'short_term': 0.5, 'mid_term': 0.3, 'long_term': 0.1}},
            message='Very happy!',
            timestamp=datetime.now()
        )
        joy_after_first = self.profile.short_term_state['joy']

        # Now send a message about sadness (joy not mentioned)
        self.profile.update_emotional_state(
            emotions={'sadness': 0.8},
            impact_score=0.7,
            state_updates={'sadness': {'short_term': 0.4, 'mid_term': 0.2, 'long_term': 0.05}},
            message='Very sad',
            timestamp=datetime.now()
        )
        joy_after_second = self.profile.short_term_state['joy']

        # Joy should have decayed
        assert joy_after_second < joy_after_first, \
            f"Joy should decay: {joy_after_second} >= {joy_after_first}"

    def test_no_unbounded_growth(self):
        """Values should stay bounded even after many updates"""
        for i in range(100):
            self.profile.update_emotional_state(
                emotions={'joy': 0.99},
                impact_score=0.99,
                state_updates={'joy': {'short_term': 0.99, 'mid_term': 0.5, 'long_term': 0.1}},
                message=f'Extremely happy {i}',
                timestamp=datetime.now()
            )
        assert self.profile.short_term_state['joy'] <= 1.0


class TestMidTermEMA:
    """Test mid-term state EMA updates (Parameter 12)"""

    def setup_method(self):
        self.profile = UserProfile('test_user')
        # Force activate mid-term
        self.profile.message_count = 30

    def test_mid_term_ema_updates_when_active(self):
        """Mid-term should update via EMA when activated"""
        self.profile.update_emotional_state(
            emotions={'joy': 0.8},
            impact_score=0.6,
            state_updates={'joy': {'short_term': 0.4, 'mid_term': 0.3, 'long_term': 0.05}},
            message='Happy!',
            timestamp=datetime.now()
        )
        # Mid-term should have been updated
        assert self.profile.mid_term_state['joy'] > 0


class TestLongTermEMA:
    """Test long-term state EMA updates (Parameter 13)"""

    def setup_method(self):
        self.profile = UserProfile('test_user')
        # Force activate long-term
        self.profile.message_count = 50

    def test_long_term_ema_updates_when_active(self):
        """Long-term should update via EMA when activated"""
        self.profile.update_emotional_state(
            emotions={'sadness': 0.7},
            impact_score=0.5,
            state_updates={'sadness': {'short_term': 0.3, 'mid_term': 0.2, 'long_term': 0.1}},
            message='Sad event',
            timestamp=datetime.now()
        )
        assert self.profile.long_term_state['sadness'] > 0

    def test_long_term_slow_change(self):
        """Long-term should change slower than short-term"""
        self.profile.update_emotional_state(
            emotions={'joy': 0.9},
            impact_score=0.8,
            state_updates={'joy': {'short_term': 0.5, 'mid_term': 0.3, 'long_term': 0.1}},
            message='Very happy!',
            timestamp=datetime.now()
        )
        st_joy = self.profile.short_term_state['joy']
        lt_joy = self.profile.long_term_state['joy']
        # Short-term impact should be larger than long-term (faster α)
        assert st_joy > lt_joy


# ==============================================================
# PHASE 3: Per-User Constants (Parameters 5-10, 14)
# ==============================================================

class TestPerUserEMAParameters:
    """Test per-user EMA parameters stored on UserProfile"""

    def test_initial_values(self):
        """New profile should have default per-user parameters"""
        profile = UserProfile('test_user')
        assert profile.entropy_penalty_coeff == 0.3
        assert profile.recurrence_step == 0.3
        assert profile.behavior_alpha == 0.2
        assert profile.similarity_threshold == 0.2
        assert 'recent' in profile.impact_multipliers

    def test_serialization_includes_ema_params(self):
        """to_dict should include all EMA parameters"""
        profile = UserProfile('test_user')
        d = profile.to_dict()
        assert 'entropy_penalty_coeff' in d
        assert 'recurrence_step' in d
        assert 'behavior_alpha' in d
        assert 'similarity_threshold' in d
        assert 'impact_multipliers' in d


# ==============================================================
# ORCHESTRATOR TESTS
# ==============================================================

class TestImpactCalculatorEMA:
    """Test EMA changes in ImpactCalculator"""

    def setup_method(self):
        # Must import after setting env
        from orchestrator import ImpactCalculator
        self.calc = ImpactCalculator
        # Reset class variables
        self.calc.typing_speed_mean = 1.0
        self.calc.typing_speed_std = 0.5

    def test_typing_speed_std_updates(self):
        """Parameter 6: typing_speed_std should update via EMA"""
        old_std = self.calc.typing_speed_std
        self.calc.update_typing_baseline(5.0)  # Very different speed
        new_std = self.calc.typing_speed_std
        assert new_std != old_std, "Std should update after typing baseline update"

    def test_entropy_penalty_per_user(self):
        """Parameter 7: entropy penalty should accept per-user coefficient"""
        emotions = {'joy': 0.7, 'sadness': 0.2, 'fear': 0.1}
        i1 = self.calc.calculate_emotion_intensity(emotions, entropy_penalty_coeff=0.1)
        i2 = self.calc.calculate_emotion_intensity(emotions, entropy_penalty_coeff=0.9)
        # Higher coeff should mean less penalty → higher intensity
        assert i2 >= i1

    def test_recurrence_step_per_user(self):
        """Parameter 8: recurrence step should be customizable"""
        b1 = self.calc.calculate_recurrence_boost(3, recurrence_step=0.1)
        b2 = self.calc.calculate_recurrence_boost(3, recurrence_step=0.5)
        assert b2 > b1, "Higher step should give higher boost"

    def test_state_multipliers_per_user(self):
        """Parameter 9: impact multipliers should accept per-user overrides"""
        custom = {
            "recent": {"short_term": 0.5, "mid_term": 0.5, "long_term": 0.5},
            "unknown": {"short_term": 0.5, "mid_term": 0.5, "long_term": 0.3}
        }
        result = self.calc.get_state_impact_multipliers('recent', user_multipliers=custom)
        assert result['short_term'] == 0.5  # Custom, not default 1.0

    def test_behavior_alpha_per_user(self):
        """Parameter 10: behavior multiplier should accept per-user alpha"""
        self.calc.typing_speed_mean = 5.0
        self.calc.typing_speed_std = 1.0
        m1 = self.calc.calculate_behavior_multiplier(100, 5.0, behavior_alpha=0.0)
        # With alpha=0, behavior should have no effect (mult should be ~1.0)
        assert abs(m1 - 1.0) < 0.01

    def test_compound_impact_with_behavior_alpha(self):
        """Compound impact should accept behavior_alpha parameter"""
        result = self.calc.calculate_compound_impact(
            emotion_intensity=0.7,
            recency_weight=0.8,
            temporal_confidence=0.6,
            recurrence_boost=1.3,
            behavior_alpha=0.1
        )
        assert 0.0 <= result <= 1.0

    def test_backward_compatibility(self):
        """All methods should work with default parameters (no breaking changes)"""
        emotions = {'joy': 0.8, 'sadness': 0.1}
        # These should all work without new parameters
        intensity = self.calc.calculate_emotion_intensity(emotions)
        boost = self.calc.calculate_recurrence_boost(2)
        mults = self.calc.get_state_impact_multipliers('recent')
        self.calc.typing_speed_mean = 5.0
        self.calc.typing_speed_std = 1.0
        behavior = self.calc.calculate_behavior_multiplier(100, 10.0)
        impact = self.calc.calculate_compound_impact(0.7, 0.8, 0.6)

        assert 0.0 <= intensity <= 1.0
        assert boost >= 1.0
        assert 'short_term' in mults
        assert 0.8 <= behavior <= 1.2
        assert 0.0 <= impact <= 1.0


# ==============================================================
# INTEGRATION TEST
# ==============================================================

class TestEMAIntegration:
    """Integration test: multiple messages evolving profile"""

    def setup_method(self):
        self.profile = UserProfile('integration_user')

    def test_smooth_weight_evolution(self):
        """Weights should evolve smoothly over many messages"""
        weight_history = [self.profile.adaptive_weights.copy()]

        for i in range(20):
            self.profile.update_emotional_state(
                emotions={'joy': 0.8, 'gratitude': 0.1},
                impact_score=0.6,
                state_updates={
                    'joy': {'short_term': 0.4, 'mid_term': 0.2, 'long_term': 0.05},
                    'gratitude': {'short_term': 0.05, 'mid_term': 0.02, 'long_term': 0.01}
                },
                message=f'Happy message {i}',
                timestamp=datetime.now()
            )
            weight_history.append(self.profile.adaptive_weights.copy())

        # Check smooth evolution: no jumps > 0.05 between consecutive updates
        for i in range(1, len(weight_history)):
            for key in weight_history[0]:
                diff = abs(weight_history[i][key] - weight_history[i-1][key])
                assert diff < 0.05, \
                    f"Weight {key} jumped {diff:.4f} between msg {i-1} and {i}"

    def test_emotion_decay_over_time(self):
        """Emotions not mentioned should decay naturally"""
        # Set strong joy
        self.profile.update_emotional_state(
            emotions={'joy': 0.95},
            impact_score=0.9,
            state_updates={'joy': {'short_term': 0.8, 'mid_term': 0.4, 'long_term': 0.1}},
            message='Extremely happy!',
            timestamp=datetime.now()
        )
        initial_joy = self.profile.short_term_state['joy']

        # Send 5 messages about anger (no joy)
        for i in range(5):
            self.profile.update_emotional_state(
                emotions={'anger': 0.8},
                impact_score=0.6,
                state_updates={'anger': {'short_term': 0.4, 'mid_term': 0.2, 'long_term': 0.05}},
                message=f'Angry message {i}',
                timestamp=datetime.now()
            )

        final_joy = self.profile.short_term_state['joy']

        # Joy should have decayed significantly
        assert final_joy < initial_joy * 0.5, \
            f"Joy should have decayed: {final_joy:.4f} vs initial {initial_joy:.4f}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
