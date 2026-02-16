"""
Temporal Reference Extractor for Multilingual AI Companion
Supports English, Hindi, and Hinglish time expressions

ENHANCEMENTS:
1. Multi-strategy parsing (Regex + Context + Absolute dates)
2. Ambiguity resolution for Hindi/Hinglish
3. Tense-based context analysis
4. Exponential confidence scoring
5. Language-specific pattern optimization
6. Robust error handling
7. Better orchestrator integration
8. Enhanced testing and validation

VERSION: 2.0 - Enhanced Edition
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

# Optional import - graceful degradation if not available
try:
    import dateparser
    DATEPARSER_AVAILABLE = True
except ImportError:
    DATEPARSER_AVAILABLE = False
    print("⚠️  Warning: dateparser not installed. Some date parsing features will be limited.")
    print("   Install with: pip install dateparser")


# ==========================================================
# ENUMS
# ==========================================================

class AgeCategory(Enum):
    """Temporal age categories for event classification"""
    RECENT = "recent"      # 0-30 days
    MEDIUM = "medium"      # 31-365 days
    DISTANT = "distant"    # 365+ days
    FUTURE = "future"      # Future events
    UNKNOWN = "unknown"    # Could not determine


# ==========================================================
# DATA CLASSES
# ==========================================================

@dataclass
class TimePhrase:
    """Represents a detected temporal phrase in text"""
    text: str
    start_pos: int
    end_pos: int
    pattern_type: str
    language: str
    context_window: str = ""
    
    def __str__(self) -> str:
        return f"TimePhrase('{self.text}', {self.pattern_type}, {self.language})"


@dataclass
class ParsedTemporal:
    """Represents a parsed temporal reference with metadata"""
    phrase: str
    parsed_date: Optional[datetime]
    time_gap_days: Optional[int]
    age_category: str
    confidence: float
    parse_method: str
    days_ago: int = 0  # Added for easier integration
    
    def __post_init__(self):
        """Calculate days_ago if not provided"""
        if self.days_ago == 0 and self.time_gap_days is not None:
            self.days_ago = self.time_gap_days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization"""
        return {
            'phrase': self.phrase,
            'parsed_date': self.parsed_date.isoformat() if self.parsed_date else None,
            'time_gap_days': self.time_gap_days,
            'days_ago': self.days_ago,
            'age_category': self.age_category,
            'confidence': round(self.confidence, 2),
            'parse_method': self.parse_method
        }


# ==========================================================
# TENSE & CONTEXT ANALYZER
# ==========================================================

class TenseAnalyzer:
    """Analyze verb tenses to resolve ambiguous temporal references"""

    PAST_INDICATORS = {
        'english': ['was', 'were', 'did', 'had', 'went', 'came', 'happened', 
                   'occurred', 'took', 'found', 'made', 'got', 'became', 'felt',
                   'thought', 'said', 'told', 'saw', 'heard', 'remembered'],
        'hindi': ['tha', 'thi', 'the', 'gaya', 'gai', 'hui', 'hua', 
                 'raha', 'rahi', 'rahe', 'kiya', 'kiye', 'kaha', 'dekha'],
        'hinglish': ['tha', 'was', 'gaya', 'happened', 'went', 'hui', 'did', 'kiya']
    }

    FUTURE_INDICATORS = {
        'english': ['will', 'going to', 'shall', 'is going', 'are going', 
                   'would', 'planning', 'supposed to', 'gonna', 'about to',
                   'will be', 'plan to', 'intend to'],
        'hindi': ['hoga', 'hogi', 'honge', 'hain', 'hai', 'baad mein', 'ayenge',
                 'karenge', 'karegi', 'jaenge', 'jayenge'],
        'hinglish': ['will', 'hoga', 'going to', 'hai', 'baad mein', 'karenge']
    }

    IMMEDIATE_PAST = {
        'english': ['just', 'recently', 'just now', 'few moments ago', 'earlier',
                   'a moment ago', 'moments ago'],
        'hindi': ['abhi', 'abhi hi', 'abhi-abhi', 'ek dum', 'thodi der pehle',
                 'thodi der pahle', 'bas abhi'],
        'hinglish': ['just', 'abhi', 'just now', 'recently', 'abhi hi']
    }

    @staticmethod
    def analyze_tense(full_message: str, language: str = 'mixed') -> Dict[str, float]:
        """
        Analyze message tense and return scoring for past/future/present
        
        Args:
            full_message: Full text message to analyze
            language: Language hint ('english', 'hindi', 'hinglish', or 'mixed')
        
        Returns:
            Dict with tense scores and dominant tense
        """
        if not full_message:
            return {
                'past_score': 0.0,
                'future_score': 0.0,
                'present_score': 1.0,
                'dominant_tense': 'present'
            }
        
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
        present_score = max(0.0, 1.0 - (past_score + future_score))
        
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
        },
        'narso': {
            'past_days': -3,
            'future_days': 3,
            'patterns': r'\bnarso\b'
        }
    }

    @staticmethod
    def resolve_ambiguous_reference(
        phrase_text: str,
        full_message: str,
        reference_time: datetime,
        tense_analysis: Dict[str, float]
    ) -> Optional[datetime]:
        """
        Resolve ambiguous Hindi temporal references using tense analysis
        
        Args:
            phrase_text: The temporal phrase to resolve
            full_message: Full message for context
            reference_time: Current/reference datetime
            tense_analysis: Tense analysis results
        
        Returns:
            Resolved datetime or None if cannot resolve
        """
        if not phrase_text or not full_message:
            return None
        
        phrase_lower = phrase_text.lower()
        
        for ambig_word, ambig_data in AmbiguityResolver.AMBIGUOUS_WORDS.items():
            if ambig_word in phrase_lower:
                past_score = tense_analysis.get('past_score', 0.0)
                future_score = tense_analysis.get('future_score', 0.0)
                
                # Use tense analysis to determine direction
                if past_score > future_score:
                    offset = ambig_data['past_days']
                elif future_score > past_score:
                    offset = ambig_data['future_days']
                else:
                    # Default to past if uncertain (more common in conversation)
                    offset = ambig_data['past_days']
                
                try:
                    return reference_time + timedelta(days=offset)
                except (ValueError, OverflowError):
                    return None
        
        return None


# ==========================================================
# PATTERN REGISTRY
# ==========================================================

class TemporalPatternRegistry:
    """Registry of temporal patterns for different languages"""

    ENGLISH_RELATIVE = [
        (r'\b(\d+)\s+(years?|months?|weeks?|days?|hours?|minutes?|seconds?)\s+ago\b', 'relative_quantity'),
        (r'\b(\d+)\s+(yrs?|mos?|wks?|hrs?|mins?|secs?)\s+ago\b', 'relative_quantity_abbrev'),
        (r'\b(last|previous)\s+(year|month|week|day|night)\b', 'relative_named'),
        (r'\bthis\s+(year|month|week|day|morning|evening|night)\b', 'relative_this'),
        (r'\bnext\s+(year|month|week|day|morning|evening|night)\b', 'relative_next'),
        (r'\b(yesterday|today|tomorrow)\b', 'simple_relative'),
        (r'\b(?:the\s+)?day\s+before\s+yesterday\b', 'simple_relative'),
        (r'\b(?:the\s+)?day\s+after\s+tomorrow\b', 'simple_relative'),
        (r'\ba\s+(?:few|couple\s+of)\s+(days?|weeks?|months?|years?)\s+ago\b', 'relative_fuzzy'),
    ]

    ENGLISH_ABSOLUTE = [
        (r'\b(19\d{2}|20\d{2})\b', 'year_only'),
        (r'\bin\s+(19\d{2}|20\d{2})\b', 'year_with_in'),
        (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', 'numeric_date'),
        (r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b', 'month_day_year'),
    ]

    HINDI_RELATIVE = [
        (r'\b(\d+)\s+(saal|sal|mahine|mahina|hafte|hafta|din)\s+(pehle|pahle|baad)\b', 'hindi_quantity'),
        (r'\b(pichle|agle|is)\s+(saal|sal|mahine|mahina|hafte|hafta|din)\b', 'hindi_relative_named'),
        (r'\bkal\b', 'hindi_ambiguous'),
        (r'\bparso\b', 'hindi_ambiguous'),
        (r'\bnarso\b', 'hindi_ambiguous'),
        (r'\baaj\b', 'hindi_simple'),
        (r'\babhi\b', 'hindi_immediate'),
        (r'\bkuch\s+(din|hafte|mahine|saal)\s+(pehle|pahle)\b', 'hindi_fuzzy'),
    ]

    HINGLISH_MIXED = [
        (r'\b(\d+)\s+(year|saal|sal|month|mahina|mahine|week|hafta|hafte|day|din)\s+(ago|pehle|pahle|back|baad)\b', 'hinglish_mixed'),
        (r'\blast\s+(year|saal|month|mahina|week|hafta|day|din)\b', 'hinglish_last'),
        (r'\bnext\s+(year|saal|month|mahina|week|hafta|day|din)\b', 'hinglish_next'),
        (r'\bkuch\s+(days?|weeks?|months?|years?)\s+(ago|pehle|back)\b', 'hinglish_fuzzy'),
    ]

    VAGUE_EXPRESSIONS = [
        (r'\b(?:a\s+)?long\s+time\s+ago\b', 'vague_long'),
        (r'\bvery\s+long\s+time\s+ago\b', 'vague_very_long'),
        (r'\bwhen\s+i\s+was\s+(young|a\s+kid|a\s+child|small|little)\b', 'vague_childhood'),
        (r'\byears?\s+back\b', 'vague_years_back'),
        (r'\bages?\s+ago\b', 'vague_ages'),
        (r'\brecently\b', 'vague_recent'),
        (r'\bsoon\b', 'vague_soon'),
    ]

    @classmethod
    def get_all_patterns(cls) -> List[Tuple[List, str, str]]:
        """
        Return all patterns with (pattern_list, pattern_type, language)
        
        Returns:
            List of tuples: (patterns, type, language)
        """
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
    """
    Main temporal reference extractor
    
    Extracts and parses temporal references from multilingual text
    using multiple strategies and confidence scoring.
    """

    def __init__(self, reference_time: Optional[datetime] = None):
        """
        Initialize temporal extractor
        
        Args:
            reference_time: Reference datetime (default: now)
        """
        self.reference_time = reference_time or datetime.now()
        
        if DATEPARSER_AVAILABLE:
            self.dateparser_settings = {
                'PREFER_DATES_FROM': 'past',
                'RELATIVE_BASE': self.reference_time,
                'STRICT_PARSING': False,
                'NORMALIZE': True,
            }
        else:
            self.dateparser_settings = None

    # ==========================================================
    # PUBLIC METHODS
    # ==========================================================

    def extract_temporal_references(
        self, 
        message: str, 
        reference_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Main method for orchestrator integration
        
        Args:
            message: Text message to analyze
            reference_date: Reference datetime (default: self.reference_time)
        
        Returns:
            Dict with temporal reference information
        """
        if reference_date:
            self.reference_time = reference_date
        
        return self.process_message(message)

    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Main entry point for processing messages
        
        Args:
            message: Text message to analyze
        
        Returns:
            Dictionary with extraction results
        """
        if not message or not message.strip():
            return self._empty_result(message)
        
        try:
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
                "has_temporal_ref": len(time_phrases) > 0,
                "phrases_found": [phrase.text for phrase in time_phrases],
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
                "parsed_dates": [r.to_dict() for r in parsed_results],
                "summary": {
                    "total_phrases_found": len(time_phrases),
                    "successfully_parsed": len([r for r in parsed_results if r.parsed_date]),
                    "overall_confidence": round(overall_confidence, 2),
                    "has_temporal_reference": len(time_phrases) > 0
                }
            }

            return output
        
        except Exception as e:
            print(f"⚠️  Error processing message: {e}")
            return self._empty_result(message)

    def extract_time_phrases(self, message: str) -> List[TimePhrase]:
        """
        Extract all temporal phrases with their context
        
        Args:
            message: Text to extract from
        
        Returns:
            List of TimePhrase objects
        """
        if not message:
            return []
        
        phrases = []

        try:
            for patterns, pattern_type, language in TemporalPatternRegistry.get_all_patterns():
                for pattern_tuple in patterns:
                    pattern = pattern_tuple[0] if isinstance(pattern_tuple, tuple) else pattern_tuple
                    
                    try:
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
                    except re.error as e:
                        print(f"⚠️  Regex error with pattern {pattern}: {e}")
                        continue

            return self._deduplicate_phrases(phrases)
        
        except Exception as e:
            print(f"⚠️  Error extracting phrases: {e}")
            return []

    def parse_time_phrase(self, phrase: TimePhrase) -> ParsedTemporal:
        """
        Multi-strategy parsing of temporal phrases
        
        Args:
            phrase: TimePhrase object to parse
        
        Returns:
            ParsedTemporal object with parsing results
        """
        try:
            # STRATEGY 1: Ambiguous references (Hindi/Hinglish)
            if phrase.language in ['hi', 'hinglish']:
                tense_analysis = TenseAnalyzer.analyze_tense(phrase.context_window, phrase.language)
                parsed_date = AmbiguityResolver.resolve_ambiguous_reference(
                    phrase.text, phrase.context_window, self.reference_time, tense_analysis
                )
                
                if parsed_date:
                    return self._create_parsed_temporal(phrase, parsed_date, "ambiguity_resolver + tense_analysis")
            
            # STRATEGY 2: Try dateparser (if available)
            if DATEPARSER_AVAILABLE:
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
            return self._create_failed_temporal(phrase)
        
        except Exception as e:
            print(f"⚠️  Error parsing phrase '{phrase.text}': {e}")
            return self._create_failed_temporal(phrase)

    # ==========================================================
    # PRIVATE HELPER METHODS
    # ==========================================================

    def _empty_result(self, message: str) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "original_message": message,
            "reference_time": self.reference_time.isoformat(),
            "has_temporal_ref": False,
            "phrases_found": [],
            "time_phrases_detected": [],
            "parsed_dates": [],
            "summary": {
                "total_phrases_found": 0,
                "successfully_parsed": 0,
                "overall_confidence": 0.0,
                "has_temporal_reference": False
            }
        }

    def _create_failed_temporal(self, phrase: TimePhrase) -> ParsedTemporal:
        """Create a ParsedTemporal object for failed parsing"""
        return ParsedTemporal(
            phrase=phrase.text,
            parsed_date=None,
            time_gap_days=None,
            age_category=AgeCategory.UNKNOWN.value,
            confidence=0.0,
            parse_method="failed"
        )

    def _deduplicate_phrases(self, phrases: List[TimePhrase]) -> List[TimePhrase]:
        """
        Remove overlapping phrases, prefer longer/more specific matches
        
        Args:
            phrases: List of TimePhrase objects
        
        Returns:
            Deduplicated list
        """
        if not phrases:
            return []

        # Sort by start position, then by length (descending)
        phrases.sort(key=lambda x: (x.start_pos, -(x.end_pos - x.start_pos)))
        result = []

        for phrase in phrases:
            overlap = False
            for selected in result:
                # Check if phrases overlap
                if not (phrase.end_pos <= selected.start_pos or
                        phrase.start_pos >= selected.end_pos):
                    overlap = True
                    break
            if not overlap:
                result.append(phrase)

        return result

    def _try_dateparser(self, text: str) -> Optional[datetime]:
        """
        Use dateparser library
        
        Args:
            text: Text to parse
        
        Returns:
            Parsed datetime or None
        """
        if not DATEPARSER_AVAILABLE or not self.dateparser_settings:
            return None
        
        try:
            parsed = dateparser.parse(text, settings=self.dateparser_settings)
            return parsed
        except Exception as e:
            return None

    def _try_custom_parsing(self, phrase: TimePhrase) -> Optional[datetime]:
        """
        Custom regex-based parsing
        
        Args:
            phrase: TimePhrase to parse
        
        Returns:
            Parsed datetime or None
        """
        text = phrase.text.lower()
        
        # Simple day offsets
        simple_map = {
            'yesterday': -1, 
            'today': 0, 
            'tomorrow': 1,
            'kal': -1,  # Default to past for ambiguous cases
            'aaj': 0, 
            'parso': -2,
            'narso': -3,
            'day before yesterday': -2,
            'day after tomorrow': 2,
        }

        for word, offset in simple_map.items():
            if word in text:
                try:
                    return self.reference_time + timedelta(days=offset)
                except (ValueError, OverflowError):
                    return None

        # Period-based offsets
        period_map = {
            'last week': -7, 'last month': -30, 'last year': -365,
            'this week': 0, 'this month': 0, 'this year': 0,
            'next week': 7, 'next month': 30, 'next year': 365,
            'pichle hafte': -7, 'pichle mahine': -30, 'pichle saal': -365,
            'is hafte': 0, 'is mahine': 0, 'is saal': 0,
            'agle hafte': 7, 'agle mahine': 30, 'agle saal': 365,
            'previous week': -7, 'previous month': -30, 'previous year': -365,
        }

        for period, offset in period_map.items():
            if period in text:
                try:
                    return self.reference_time + timedelta(days=offset)
                except (ValueError, OverflowError):
                    return None

        # Quantity-based parsing (e.g., "5 days ago")
        quantity_match = re.search(
            r'(\d+)\s+(years?|months?|weeks?|days?|saal|sal|mahine?|hafte?|din)\s+(ago|pehle|pahle|back|baad)',
            text
        )

        if quantity_match:
            try:
                num = int(quantity_match.group(1))
                unit = quantity_match.group(2).lower()
                direction = quantity_match.group(3).lower()

                unit_days = {
                    'year': 365, 'years': 365, 'yrs': 365, 'yr': 365,
                    'month': 30, 'months': 30, 'mos': 30, 'mo': 30,
                    'week': 7, 'weeks': 7, 'wks': 7, 'wk': 7,
                    'day': 1, 'days': 1, 
                    'saal': 365, 'sal': 365,
                    'mahine': 30, 'mahina': 30, 
                    'hafte': 7, 'hafta': 7, 
                    'din': 1,
                }

                if unit in unit_days:
                    day_offset = int(num * unit_days[unit])
                    if direction in ['ago', 'pehle', 'pahle', 'back']:
                        return self.reference_time - timedelta(days=day_offset)
                    elif direction in ['baad', 'after']:
                        return self.reference_time + timedelta(days=day_offset)
            except (ValueError, OverflowError):
                return None

        # Year extraction
        year_match = re.search(r'(19\d{2}|20\d{2})', text)
        if year_match and phrase.pattern_type == "absolute":
            try:
                year = int(year_match.group(1))
                if 1900 <= year <= 2100:  # Sanity check
                    return datetime(year, 1, 1)
            except (ValueError, OverflowError):
                return None

        return None

    def _handle_vague_expression(self, phrase: TimePhrase) -> Optional[datetime]:
        """
        Handle vague temporal expressions
        
        Args:
            phrase: TimePhrase with vague expression
        
        Returns:
            Estimated datetime or None
        """
        text = phrase.text.lower()

        try:
            # Long time ago
            if re.search(r'long\s+time', text):
                if 'very' in text:
                    return self.reference_time - timedelta(days=1095)  # ~3 years
                return self.reference_time - timedelta(days=730)  # ~2 years
            
            # Childhood references
            if re.search(r'when\s+i\s+was\s+(young|a\s+kid|a\s+child|small|little)', text):
                return self.reference_time - timedelta(days=7300)  # ~20 years
            
            # Years back
            if re.search(r'years?\s+back', text):
                return self.reference_time - timedelta(days=1825)  # ~5 years
            
            # Ages ago
            if re.search(r'ages?\s+ago', text):
                return self.reference_time - timedelta(days=2555)  # ~7 years
            
            # Recently
            if 'recently' in text:
                return self.reference_time - timedelta(days=7)  # 1 week
            
            # Soon
            if 'soon' in text:
                return self.reference_time + timedelta(days=7)  # 1 week
        
        except (ValueError, OverflowError):
            return None

        return None

    def _get_context_window(self, message: str, start: int, end: int, window_size: int = 100) -> str:
        """
        Extract context around temporal phrase
        
        Args:
            message: Full message
            start: Start position of phrase
            end: End position of phrase
            window_size: Characters before/after to include
        
        Returns:
            Context string
        """
        if not message:
            return ""
        
        context_start = max(0, start - window_size)
        context_end = min(len(message), end + window_size)
        return message[context_start:context_end].strip()

    def _create_parsed_temporal(
        self, 
        phrase: TimePhrase, 
        parsed_date: datetime, 
        parse_method: str
    ) -> ParsedTemporal:
        """
        Create ParsedTemporal object
        
        Args:
            phrase: Original TimePhrase
            parsed_date: Parsed datetime
            parse_method: Method used for parsing
        
        Returns:
            ParsedTemporal object
        """
        try:
            time_gap_days = (self.reference_time - parsed_date).days
            age_category = self._classify_age(time_gap_days)
            confidence = self._calculate_confidence(phrase, parsed_date, parse_method)

            return ParsedTemporal(
                phrase=phrase.text,
                parsed_date=parsed_date,
                time_gap_days=time_gap_days,
                age_category=age_category,
                confidence=confidence,
                parse_method=parse_method,
                days_ago=time_gap_days
            )
        except Exception as e:
            print(f"⚠️  Error creating parsed temporal: {e}")
            return self._create_failed_temporal(phrase)

    def _classify_age(self, gap: int) -> str:
        """
        Classify temporal distance
        
        Args:
            gap: Days between reference and event
        
        Returns:
            Age category string
        """
        if gap < 0:
            return AgeCategory.FUTURE.value
        elif gap <= 30:
            return AgeCategory.RECENT.value
        elif gap <= 365:
            return AgeCategory.MEDIUM.value
        else:
            return AgeCategory.DISTANT.value

    def _calculate_confidence(
        self, 
        phrase: TimePhrase, 
        parsed_date: datetime, 
        parse_method: str
    ) -> float:
        """
        Calculate confidence score for parsing
        
        Args:
            phrase: TimePhrase object
            parsed_date: Parsed datetime
            parse_method: Parsing method used
        
        Returns:
            Confidence score [0.0, 1.0]
        """
        base_confidence = 0.5

        # Pattern type contribution
        if phrase.pattern_type == "absolute":
            base_confidence += 0.35
        elif phrase.pattern_type == "relative":
            base_confidence += 0.25
        elif phrase.pattern_type == "vague":
            base_confidence -= 0.2

        # Parse method contribution
        method_confidence = {
            "ambiguity_resolver + tense_analysis": 0.15,
            "dateparser": 0.2,
            "regex+custom": 0.15,
            "vague_heuristic": 0.0,
            "failed": -0.5
        }
        base_confidence += method_confidence.get(parse_method, 0.1)

        # Specific indicators boost confidence
        if re.search(r'\d{4}', phrase.text):  # Year present
            base_confidence += 0.2
        elif re.search(r'\d+', phrase.text):  # Any number present
            base_confidence += 0.1

        # Language clarity
        if phrase.language == 'en':
            base_confidence += 0.05
        elif phrase.language in ['hi', 'hinglish']:
            base_confidence += 0.02

        # Ensure within bounds
        return max(0.0, min(1.0, base_confidence))


# ==========================================================
# FACTORY FUNCTION
# ==========================================================

def create_extractor(reference_time: Optional[datetime] = None) -> TemporalExtractor:
    """
    Factory function to create TemporalExtractor
    
    Args:
        reference_time: Reference datetime (default: now)
    
    Returns:
        TemporalExtractor instance
    """
    return TemporalExtractor(reference_time)


# ==========================================================
# MAIN - TESTING
# ==========================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("⏰ Temporal Reference Extractor - Enhanced Test Mode")
    print("="*80)
    print(f"DateParser Available: {DATEPARSER_AVAILABLE}")
    print("="*80 + "\n")
    
    extractor = TemporalExtractor()
    
    test_messages = [
        "My father passed away last year",
        "Kal exam tha aur mujhe bohot tension hua",
        "5 years pehle I visited Delhi",
        "I met him yesterday",
        "Parso I'm going out",
        "When I was young, I loved cricket",
        "Recently started a new job",
        "Long time ago I used to live in Mumbai",
        "Next week I have an interview",
        "Abhi hi maine khana khaya",
    ]
    
    print("Testing with sample messages:\n")
    
    for i, msg in enumerate(test_messages, 1):
        print(f"{i}. 📝 Input: {msg}")
        result = extractor.process_message(msg)
        
        summary = result['summary']
        print(f"   Found: {summary['total_phrases_found']} phrases, "
              f"Parsed: {summary['successfully_parsed']}, "
              f"Confidence: {summary['overall_confidence']}")
        
        for parsed in result['parsed_dates']:
            if parsed['parsed_date']:
                print(f"   → '{parsed['phrase']:30s}' | "
                      f"{parsed['age_category']:10s} | "
                      f"Days: {parsed['days_ago']:4d} | "
                      f"Conf: {parsed['confidence']:.2f} | "
                      f"Method: {parsed['parse_method']}")
        
        if summary['total_phrases_found'] == 0:
            print("   ⚠️  No temporal references detected")
        
        print()
    
    print("="*80)
    print("✅ Test complete!")
    print("="*80 + "\n")