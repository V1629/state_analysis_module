"""
Temporal Reference Extractor for Multilingual AI Companion
Supports English, Hindi, and Hinglish time expressions

ENHANCEMENTS:
1. Multi-strategy parsing (Regex + Context + Absolute dates)
2. Ambiguity resolution for Hindi/Hinglish
3. Tense-based context analysis
4. Exponential confidence scoring
5. Language-specific pattern optimization
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import dateparser
import math


# ==========================================================
# ENUMS
# ==========================================================

class AgeCategory(Enum):
    RECENT = "recent"
    MEDIUM = "medium"
    DISTANT = "distant"
    FUTURE = "future"
    UNKNOWN = "unknown"


# ==========================================================
# DATA CLASSES
# ==========================================================

@dataclass
class TimePhrase:
    text: str
    start_pos: int
    end_pos: int
    pattern_type: str
    language: str
    context_window: str = ""


@dataclass
class ParsedTemporal:
    phrase: str
    parsed_date: Optional[datetime]
    time_gap_days: Optional[int]
    age_category: str
    confidence: float
    parse_method: str


# ==========================================================
# TENSE & CONTEXT ANALYZER
# ==========================================================

class TenseAnalyzer:
    """Analyze verb tenses to resolve ambiguous temporal references"""

    PAST_INDICATORS = {
        'english': ['was', 'were', 'did', 'had', 'went', 'came', 'happened', 
                   'occurred', 'took', 'found', 'made', 'got', 'became'],
        'hindi': ['tha', 'thi', 'the', 'gaya', 'gai', 'hui', 'hua', 
                 'raha', 'rahi', 'rahe'],
        'hinglish': ['tha', 'was', 'gaya', 'happened', 'went', 'hui', 'did']
    }

    FUTURE_INDICATORS = {
        'english': ['will', 'going to', 'shall', 'is going', 'are going', 
                   'would', 'planning', 'supposed to', 'gonna'],
        'hindi': ['hoga', 'hogi', 'honge', 'hain', 'hai', 'baad mein', 'ayenge'],
        'hinglish': ['will', 'hoga', 'going to', 'hai', 'baad mein']
    }

    IMMEDIATE_PAST = {
        'english': ['just', 'recently', 'just now', 'few moments ago', 'earlier'],
        'hindi': ['abhi', 'abhi hi', 'abhi-abhi', 'ek dum', 'thodi der pehle'],
        'hinglish': ['just', 'abhi', 'just now', 'recently']
    }

    @staticmethod
    def analyze_tense(full_message: str, language: str = 'mixed') -> Dict[str, float]:
        """
        Analyze message tense and return scoring for past/future/present
        """
        message_lower = full_message.lower()
        
        past_count = 0
        future_count = 0
        
        # Count indicators across all languages
        for indicators in TenseAnalyzer.PAST_INDICATORS.values():
            past_count += sum(1 for ind in indicators if ind in message_lower)
        
        for indicators in TenseAnalyzer.FUTURE_INDICATORS.values():
            future_count += sum(1 for ind in indicators if ind in message_lower)
        
        # Immediate past indicators (boost past score)
        for indicators in TenseAnalyzer.IMMEDIATE_PAST.values():
            past_count += sum(1 for ind in indicators if ind in message_lower) * 2
        
        total = past_count + future_count + 1
        
        past_score = past_count / total
        future_score = future_count / total
        present_score = 1 - (past_score + future_score)
        
        # Determine dominant tense
        if past_score > future_score and past_score > present_score:
            dominant = 'past'
        elif future_score > past_score and future_score > present_score:
            dominant = 'future'
        else:
            dominant = 'present'
        
        return {
            'past_score': min(1.0, past_score),
            'future_score': min(1.0, future_score),
            'present_score': min(1.0, present_score),
            'dominant_tense': dominant
        }


# ==========================================================
# AMBIGUITY RESOLVER
# ==========================================================

class AmbiguityResolver:
    """Resolve ambiguous temporal references using context"""

    AMBIGUOUS_WORDS = {
        'kal': {
            'past_days': -1,
            'future_days': 1,
            'patterns': r'\bkal\b'
        },
        'parso': {
            'past_days': -2,
            'future_days': 2,
            'patterns': r'\bparso\b'
        },
        'kal se': {
            'past_days': -1,
            'future_days': 1,
            'patterns': r'\bkal\s+se\b'
        }
    }

    @staticmethod
    def resolve_ambiguous_reference(
        phrase_text: str,
        full_message: str,
        reference_time: datetime,
        tense_analysis: Dict[str, float]
    ) -> Optional[datetime]:
        """Resolve ambiguous Hindi temporal references using tense analysis"""
        phrase_lower = phrase_text.lower()
        
        for ambig_word, ambig_data in AmbiguityResolver.AMBIGUOUS_WORDS.items():
            if ambig_word in phrase_lower:
                past_score = tense_analysis['past_score']
                future_score = tense_analysis['future_score']
                
                if past_score > future_score:
                    offset = ambig_data['past_days']
                elif future_score > past_score:
                    offset = ambig_data['future_days']
                else:
                    offset = ambig_data['past_days']
                
                return reference_time + timedelta(days=offset)
        
        return None


# ==========================================================
# PATTERN REGISTRY
# ==========================================================

class TemporalPatternRegistry:

    ENGLISH_RELATIVE = [
        (r'\b(\d+)\s+(years?|months?|weeks?|days?|hours?|minutes?|seconds?)\s+ago\b', 'relative_quantity'),
        (r'\b(\d+)\s+(yrs?|mos?|wks?|hrs?|mins?)\s+ago\b', 'relative_quantity_abbrev'),
        (r'\b(last|previous)\s+(year|month|week|day|night)\b', 'relative_named'),
        (r'\bthis\s+(year|month|week|day)\b', 'relative_this'),
        (r'\bnext\s+(year|month|week|day)\b', 'relative_next'),
        (r'\b(yesterday|today|tomorrow)\b', 'simple_relative'),
        (r'\b(day\s+)?before\s+yesterday\b', 'simple_relative'),
        (r'\b(?:day\s+)?after\s+tomorrow\b', 'simple_relative'),
    ]

    ENGLISH_ABSOLUTE = [
        (r'\b(19\d{2}|20\d{2})\b', 'year_only'),
        (r'\bin\s+(19\d{2}|20\d{2})\b', 'year_with_in'),
        (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', 'numeric_date'),
    ]

    HINDI_RELATIVE = [
        (r'\b(\d+)\s+(saal|sal|mahine|mahina|hafte|hafta|din)\s+(pehle|pahle|baad)\b', 'hindi_quantity'),
        (r'\b(pichle|agle|is)\s+(saal|sal|mahine|mahina|hafte|hafta|din)\b', 'hindi_relative_named'),
        (r'\bkal\b', 'hindi_ambiguous'),
        (r'\bparso\b', 'hindi_ambiguous'),
        (r'\baaj\b', 'hindi_simple'),
        (r'\babhi\b', 'hindi_immediate'),
    ]

    HINGLISH_MIXED = [
        (r'\b(\d+)\s+(year|saal|sal|month|mahina|mahine|week|hafta|hafte|day|din)\s+(ago|pehle|back|baad)\b', 'hinglish_mixed'),
        (r'\blast\s+(year|saal|month|mahina|week|hafta|day|din)\b', 'hinglish_last'),
        (r'\bnext\s+(year|saal|month|mahina|week|hafta|day|din)\b', 'hinglish_next'),
    ]

    VAGUE_EXPRESSIONS = [
        (r'\b(long\s+time|very\s+long\s+time)\s+ago\b', 'vague_long'),
        (r'\bwhen\s+i\s+was\s+(young|a\s+kid|a\s+child|small)\b', 'vague_childhood'),
        (r'\byears?\s+back\b', 'vague_years_back'),
    ]

    @classmethod
    def get_all_patterns(cls):
        """Return all patterns with (pattern_list, pattern_type, language)"""
        return [
            (cls.ENGLISH_RELATIVE, 'relative', 'en'),
            (cls.ENGLISH_ABSOLUTE, 'absolute', 'en'),
            (cls.HINDI_RELATIVE, 'relative', 'hi'),
            (cls.HINGLISH_MIXED, 'relative', 'hinglish'),
            (cls.VAGUE_EXPRESSIONS, 'vague', 'mixed'),
        ]


# ==========================================================
# MAIN EXTRACTOR
# ==========================================================

class TemporalExtractor:

    def __init__(self, reference_time: Optional[datetime] = None):
        self.reference_time = reference_time or datetime.now()
        self.dateparser_settings = {
            'PREFER_DATES_FROM': 'past',
            'RELATIVE_BASE': self.reference_time,
            'STRICT_PARSING': False,
            'NORMALIZE': True,
        }

    def extract_time_phrases(self, message: str) -> List[TimePhrase]:
        """Extract all temporal phrases with their context"""
        phrases = []

        for patterns, pattern_type, language in TemporalPatternRegistry.get_all_patterns():
            for pattern_tuple in patterns:
                pattern = pattern_tuple[0] if isinstance(pattern_tuple, tuple) else pattern_tuple
                
                matches = re.finditer(pattern, message, re.IGNORECASE)
                for match in matches:
                    context = self._get_context_window(message, match.start(), match.end())
                    
                    phrases.append(TimePhrase(
                        text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        pattern_type=pattern_type,
                        language=language,
                        context_window=context
                    ))

        return self._deduplicate_phrases(phrases)

    def _deduplicate_phrases(self, phrases: List[TimePhrase]) -> List[TimePhrase]:
        """Remove overlapping phrases, prefer longer/more specific matches"""
        if not phrases:
            return []

        phrases.sort(key=lambda x: (x.start_pos, -(x.end_pos - x.start_pos)))
        result = []

        for phrase in phrases:
            overlap = False
            for selected in result:
                if not (phrase.end_pos <= selected.start_pos or
                        phrase.start_pos >= selected.end_pos):
                    overlap = True
                    break
            if not overlap:
                result.append(phrase)

        return result

    def parse_time_phrase(self, phrase: TimePhrase) -> ParsedTemporal:
        """Multi-strategy parsing of temporal phrases"""

        # STRATEGY 1: Ambiguous references (Hindi/Hinglish)
        if phrase.language in ['hi', 'hinglish']:
            tense_analysis = TenseAnalyzer.analyze_tense(phrase.context_window, phrase.language)
            parsed_date = AmbiguityResolver.resolve_ambiguous_reference(
                phrase.text, phrase.context_window, self.reference_time, tense_analysis
            )
            
            if parsed_date:
                return self._create_parsed_temporal(phrase, parsed_date, "ambiguity_resolver + tense_analysis")
        
        # STRATEGY 2: Try dateparser
        parsed_date = self._try_dateparser(phrase.text)
        if parsed_date:
            return self._create_parsed_temporal(phrase, parsed_date, "dateparser")

        # STRATEGY 3: Custom parsing
        parsed_date = self._try_custom_parsing(phrase)
        if parsed_date:
            return self._create_parsed_temporal(phrase, parsed_date, "regex+custom")

        # STRATEGY 4: Vague expressions
        if phrase.pattern_type == "vague":
            parsed_date = self._handle_vague_expression(phrase)
            if parsed_date:
                return self._create_parsed_temporal(phrase, parsed_date, "vague_heuristic")

        # FAILED
        return ParsedTemporal(
            phrase=phrase.text,
            parsed_date=None,
            time_gap_days=None,
            age_category=AgeCategory.UNKNOWN.value,
            confidence=0.0,
            parse_method="failed"
        )

    def _try_dateparser(self, text: str) -> Optional[datetime]:
        """Use dateparser library"""
        try:
            parsed = dateparser.parse(text, settings=self.dateparser_settings)
            return parsed
        except Exception:
            return None

    def _try_custom_parsing(self, phrase: TimePhrase) -> Optional[datetime]:
        """Custom regex-based parsing"""
        text = phrase.text.lower()
        
        simple_map = {
            'yesterday': -1, 'today': 0, 'tomorrow': 1,
            'kal': -1, 'aaj': 0, 'parso': -2,
        }

        for word, offset in simple_map.items():
            if word in text:
                return self.reference_time + timedelta(days=offset)

        period_map = {
            'last week': -7, 'last month': -30, 'last year': -365,
            'this week': 0, 'this month': 0, 'this year': 0,
            'next week': 7, 'next month': 30, 'next year': 365,
            'pichle hafte': -7, 'pichle mahine': -30, 'pichle saal': -365,
            'is hafte': 0, 'is mahine': 0, 'is saal': 0,
            'agle hafte': 7, 'agle saal': 365,
        }

        for period, offset in period_map.items():
            if period in text:
                return self.reference_time + timedelta(days=offset)

        quantity_match = re.search(
            r'(\d+)\s+(years?|months?|weeks?|days?|saal|sal|mahine?|hafte?|din)\s+(ago|pehle|back|baad)',
            text
        )

        if quantity_match:
            num = int(quantity_match.group(1))
            unit = quantity_match.group(2).lower()
            direction = quantity_match.group(3).lower()

            unit_days = {
                'year': 365, 'years': 365, 'yrs': 365, 'yr': 365,
                'month': 30, 'months': 30, 'mos': 30, 'mo': 30,
                'week': 7, 'weeks': 7, 'wks': 7, 'wk': 7,
                'day': 1, 'days': 1, 'saal': 365, 'sal': 365,
                'mahine': 30, 'mahina': 30, 'hafte': 7, 'hafta': 7, 'din': 1,
            }

            if unit in unit_days:
                day_offset = int(num * unit_days[unit])
                if direction in ['ago', 'pehle', 'back']:
                    return self.reference_time - timedelta(days=day_offset)
                elif direction in ['baad', 'after']:
                    return self.reference_time + timedelta(days=day_offset)

        year_match = re.search(r'(19\d{2}|20\d{2})', text)
        if year_match and phrase.pattern_type == "absolute":
            year = int(year_match.group(1))
            return datetime(year, 1, 1)

        return None

    def _handle_vague_expression(self, phrase: TimePhrase) -> Optional[datetime]:
        """Handle vague temporal expressions"""
        text = phrase.text.lower()

        if re.search(r'(long\s+time|very\s+long)', text):
            return self.reference_time - timedelta(days=730)
        if re.search(r'when\s+i\s+was\s+(young|a\s+kid|a\s+child|small)', text):
            return self.reference_time - timedelta(days=5840)
        if re.search(r'years?\s+back', text):
            return self.reference_time - timedelta(days=1825)

        return None

    def _get_context_window(self, message: str, start: int, end: int, window_size: int = 100) -> str:
        """Extract context around temporal phrase"""
        context_start = max(0, start - window_size)
        context_end = min(len(message), end + window_size)
        return message[context_start:context_end].strip()

    def _create_parsed_temporal(self, phrase: TimePhrase, parsed_date: datetime, parse_method: str) -> ParsedTemporal:
        """Create ParsedTemporal object"""
        time_gap_days = (self.reference_time - parsed_date).days
        age_category = self._classify_age(time_gap_days)
        confidence = self._calculate_confidence(phrase, parsed_date, parse_method)

        return ParsedTemporal(
            phrase=phrase.text,
            parsed_date=parsed_date,
            time_gap_days=time_gap_days,
            age_category=age_category,
            confidence=confidence,
            parse_method=parse_method
        )

    def _classify_age(self, gap: int) -> str:
        """Classify temporal distance"""
        if gap < 0:
            return AgeCategory.FUTURE.value
        elif gap <= 30:
            return AgeCategory.RECENT.value
        elif gap <= 365:
            return AgeCategory.MEDIUM.value
        else:
            return AgeCategory.DISTANT.value

    def _calculate_confidence(self, phrase: TimePhrase, parsed_date: datetime, parse_method: str) -> float:
        """Calculate confidence score"""
        base_confidence = 0.5

        if phrase.pattern_type == "absolute":
            base_confidence += 0.35
        elif phrase.pattern_type == "relative":
            base_confidence += 0.25
        elif phrase.pattern_type == "vague":
            base_confidence -= 0.2

        method_confidence = {
            "ambiguity_resolver + tense_analysis": 0.15,
            "dateparser": 0.2,
            "regex+custom": 0.15,
            "vague_heuristic": 0.0,
            "failed": -0.5
        }
        base_confidence += method_confidence.get(parse_method, 0.1)

        if re.search(r'\d{4}', phrase.text):
            base_confidence += 0.2
        elif re.search(r'\d+', phrase.text):
            base_confidence += 0.1

        if phrase.language == 'en':
            base_confidence += 0.05
        elif phrase.language in ['hi', 'hinglish']:
            base_confidence += 0.02

        return max(0.0, min(1.0, base_confidence))

    def process_message(self, message: str) -> Dict[str, Any]:
        """Main entry point"""
        time_phrases = self.extract_time_phrases(message)
        parsed_results = [self.parse_time_phrase(p) for p in time_phrases]

        if parsed_results:
            valid = [r for r in parsed_results if r.parsed_date is not None]
            overall_confidence = (sum(r.confidence for r in valid) / len(valid)) if valid else 0.0
        else:
            overall_confidence = 0.0

        output = {
            "original_message": message,
            "reference_time": self.reference_time.isoformat(),
            "time_phrases_detected": [
                {
                    "text": phrase.text,
                    "start": phrase.start_pos,
                    "end": phrase.end_pos,
                    "type": phrase.pattern_type,
                    "language": phrase.language
                }
                for phrase in time_phrases
            ],
            "parsed_dates": [
                {
                    "phrase": r.phrase,
                    "parsed_date": r.parsed_date.isoformat() if r.parsed_date else None,
                    "time_gap_days": r.time_gap_days,
                    "age_category": r.age_category,
                    "confidence": round(r.confidence, 2),
                    "parse_method": r.parse_method
                }
                for r in parsed_results
            ],
            "summary": {
                "total_phrases_found": len(time_phrases),
                "successfully_parsed": len([r for r in parsed_results if r.parsed_date]),
                "overall_confidence": round(overall_confidence, 2),
                "has_temporal_reference": len(time_phrases) > 0
            }
        }

        return output


def create_extractor(reference_time: Optional[datetime] = None):
    """Factory function"""
    return TemporalExtractor(reference_time)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("⏰ Temporal Reference Extractor - Test Mode")
    print("="*60 + "\n")
    
    extractor = TemporalExtractor()
    
    test_messages = [
        "My father passed away last year",
        "Kal exam tha aur mujhe bohot tension hua",
        "5 years pehle",
        "I met him yesterday",
        "Parso I'm going out",
    ]
    
    for msg in test_messages:
        print(f"📝 Input: {msg}")
        result = extractor.process_message(msg)
        print(f"   Found: {result['summary']['total_phrases_found']} phrases")
        for parsed in result['parsed_dates']:
            if parsed['parsed_date']:
                print(f"   → {parsed['phrase']:30s} ({parsed['age_category']:10s}) confidence: {parsed['confidence']}")
        print()