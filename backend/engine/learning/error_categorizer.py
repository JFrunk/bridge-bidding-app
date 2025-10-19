"""
Error Categorization System

Intelligently categorizes bidding mistakes into actionable categories.
Extensible architecture allows adding new categories without code changes.
"""

import sqlite3
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import json
from engine.hand import Hand


@dataclass
class ErrorCategory:
    """Error category definition"""
    category_id: str
    display_name: str
    friendly_name: str
    description: str
    icon: Optional[str] = None


@dataclass
class CategorizedError:
    """Result of error categorization"""
    category: str
    subcategory: Optional[str]
    hand_characteristics: Dict
    helpful_hint: str


class ErrorCategorizer:
    """
    Categorizes bidding errors with context
    """

    def __init__(self, db_path: str = 'backend/bridge.db'):
        self.db_path = db_path
        self._load_categories()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_categories(self):
        """Load error categories from database"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM error_categories WHERE active = TRUE
            ORDER BY sort_order
        """)

        self.categories = {}
        for row in cursor.fetchall():
            self.categories[row['category_id']] = ErrorCategory(
                category_id=row['category_id'],
                display_name=row['display_name'],
                friendly_name=row['friendly_name'],
                description=row['description'],
                icon=row['icon']
            )

        conn.close()

    def categorize(self, hand: Hand, user_bid: str, correct_bid: str,
                  convention_id: Optional[str] = None,
                  auction_context: Optional[Dict] = None) -> CategorizedError:
        """
        Categorize a bidding error

        Args:
            hand: The Hand object
            user_bid: What the user bid
            correct_bid: What they should have bid
            convention_id: Convention being practiced (if applicable)
            auction_context: Additional auction information

        Returns:
            CategorizedError with category, subcategory, and context
        """
        # Extract characteristics
        hand_chars = self._extract_hand_characteristics(hand, auction_context)

        # Parse bids
        user_level, user_strain = self._parse_bid(user_bid)
        correct_level, correct_strain = self._parse_bid(correct_bid)

        # Determine category
        category, subcategory = self._determine_category(
            user_level, user_strain,
            correct_level, correct_strain,
            user_bid, correct_bid,
            hand_chars
        )

        # Generate helpful hint
        hint = self._generate_hint(category, subcategory, hand_chars,
                                   user_bid, correct_bid)

        return CategorizedError(
            category=category,
            subcategory=subcategory,
            hand_characteristics=hand_chars,
            helpful_hint=hint
        )

    def _extract_hand_characteristics(self, hand: Hand,
                                     auction_context: Optional[Dict]) -> Dict:
        """Extract relevant characteristics from hand and context"""
        # Basic hand characteristics
        chars = {
            'hcp': hand.hcp,
            'total_points': hand.total_points,
            'suit_lengths': dict(hand.suit_lengths),
            'is_balanced': hand.is_balanced,
            'longest_suit': max(hand.suit_lengths.items(), key=lambda x: x[1])[0],
            'longest_suit_length': max(hand.suit_lengths.values())
        }

        # Classify HCP range
        if hand.hcp < 6:
            chars['hcp_range'] = '0-5'
        elif hand.hcp < 10:
            chars['hcp_range'] = '6-9'
        elif hand.hcp < 13:
            chars['hcp_range'] = '10-12'
        elif hand.hcp < 16:
            chars['hcp_range'] = '13-15'
        elif hand.hcp < 19:
            chars['hcp_range'] = '16-18'
        else:
            chars['hcp_range'] = '19+'

        # Classify shape
        lengths = sorted(hand.suit_lengths.values(), reverse=True)
        pattern = ''.join(map(str, lengths))

        if pattern in ['4333', '4432', '5332']:
            chars['shape_type'] = 'balanced'
        elif pattern in ['5422', '6322']:
            chars['shape_type'] = 'semi_balanced'
        elif pattern in ['5431', '6331', '5521']:
            chars['shape_type'] = 'unbalanced'
        else:
            chars['shape_type'] = 'extreme'

        # Add auction context if provided
        if auction_context:
            chars.update({
                'vulnerability': auction_context.get('vulnerability', 'none'),
                'has_fit': auction_context.get('has_fit', False),
                'competition_level': auction_context.get('competition', 'unopposed')
            })

        return chars

    def _parse_bid(self, bid: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Parse a bid string into level and strain

        Returns:
            (level, strain) or (None, None) for Pass/X/XX
        """
        if not bid or bid in ['Pass', 'X', 'XX']:
            return (None, None)

        if len(bid) < 2:
            return (None, None)

        try:
            level = int(bid[0])
            strain = bid[1:] if len(bid) > 1 else None
            return (level, strain)
        except (ValueError, IndexError):
            return (None, None)

    def _determine_category(self, user_level: Optional[int], user_strain: Optional[str],
                           correct_level: Optional[int], correct_strain: Optional[str],
                           user_bid: str, correct_bid: str,
                           hand_chars: Dict) -> Tuple[str, Optional[str]]:
        """
        Determine the error category and subcategory

        Returns:
            (category, subcategory)
        """
        # Handle Pass vs Bid errors
        if user_bid == 'Pass' and correct_bid != 'Pass':
            return ('missed_opportunity', 'passed_when_should_bid')

        if user_bid != 'Pass' and correct_bid == 'Pass':
            return ('premature_bid', 'bid_when_should_pass')

        # Handle X/XX separately
        if user_bid in ['X', 'XX'] or correct_bid in ['X', 'XX']:
            return ('convention_meaning', 'defensive_bid')

        # Both are actual bids
        if user_level is not None and correct_level is not None:
            # Wrong level, same strain
            if user_level != correct_level and user_strain == correct_strain:
                subcategory = 'too_high' if user_level > correct_level else 'too_low'
                return ('wrong_level', subcategory)

            # Wrong strain, same level
            if user_level == correct_level and user_strain != correct_strain:
                subcategory = self._classify_strain_error(user_strain, correct_strain, hand_chars)
                return ('wrong_strain', subcategory)

            # Both wrong
            if user_level != correct_level and user_strain != correct_strain:
                # Likely misunderstood the convention
                return ('wrong_meaning', 'misunderstood_convention')

        # Check for strength evaluation errors
        if self._is_strength_error(user_level, correct_level, hand_chars):
            subcategory = 'overvalue' if user_level and correct_level and user_level > correct_level else 'undervalue'
            return ('strength_evaluation', subcategory)

        # Check for missed fit
        if hand_chars.get('has_fit') and user_strain != hand_chars.get('fit_suit'):
            return ('missed_fit', 'didnt_support')

        # Default to convention meaning if can't determine
        return ('wrong_meaning', 'general')

    def _classify_strain_error(self, user_strain: Optional[str],
                               correct_strain: Optional[str],
                               hand_chars: Dict) -> str:
        """Classify what kind of strain error was made"""
        if user_strain == 'NT' or correct_strain == 'NT':
            return 'nt_vs_suit'

        # Check if it's a major vs minor issue
        majors = ['♥', '♠']
        if (user_strain in majors) != (correct_strain in majors):
            return 'major_vs_minor'

        return 'wrong_suit'

    def _is_strength_error(self, user_level: Optional[int],
                          correct_level: Optional[int],
                          hand_chars: Dict) -> bool:
        """Check if error is related to hand strength evaluation"""
        if user_level is None or correct_level is None:
            return False

        level_diff = abs(user_level - correct_level)

        # Significant level difference suggests strength evaluation issue
        if level_diff >= 2:
            return True

        # Bidding at wrong level with borderline HCP
        hcp = hand_chars['hcp']
        if hcp in [12, 13, 15, 16, 18, 19] and level_diff >= 1:
            return True

        return False

    def _generate_hint(self, category: str, subcategory: Optional[str],
                      hand_chars: Dict, user_bid: str, correct_bid: str) -> str:
        """Generate a helpful hint based on the error"""
        hints = {
            'wrong_level': {
                'too_high': f"With {hand_chars['hcp']} HCP, {correct_bid} is more appropriate than {user_bid}.",
                'too_low': f"You have {hand_chars['hcp']} HCP - that's enough for {correct_bid}!"
            },
            'wrong_strain': {
                'nt_vs_suit': f"Consider whether notrump or a suit fit works better with your {hand_chars['shape_type']} shape.",
                'major_vs_minor': "Focus on finding major suit fits (hearts and spades) first.",
                'wrong_suit': f"Look at your longest suit: you have {hand_chars['longest_suit_length']} cards in {hand_chars['longest_suit']}."
            },
            'missed_opportunity': {
                'passed_when_should_bid': f"With {hand_chars['hcp']} HCP, you're strong enough to bid {correct_bid}."
            },
            'strength_evaluation': {
                'overvalue': f"This hand has {hand_chars['hcp']} HCP. Remember to evaluate shape but don't overbid.",
                'undervalue': f"Don't forget distribution! With {hand_chars['total_points']} total points, you can bid {correct_bid}."
            },
            'missed_fit': {
                'didnt_support': "When you have 4+ card support for partner's suit, show it!"
            }
        }

        # Get specific hint or return general one
        if category in hints and subcategory in hints[category]:
            return hints[category][subcategory]

        # Fallback hints
        general_hints = {
            'wrong_level': f"The correct bid is {correct_bid}, not {user_bid}. Focus on point count.",
            'wrong_strain': f"The correct bid is {correct_bid}. Think about suit quality and fit.",
            'wrong_meaning': f"This convention means something specific - review what {correct_bid} shows.",
            'strength_evaluation': f"With {hand_chars['hcp']} HCP, {correct_bid} describes your hand better.",
        }

        return general_hints.get(category, f"The correct bid here is {correct_bid}.")

    def get_category_info(self, category_id: str) -> Optional[ErrorCategory]:
        """Get information about a specific category"""
        return self.categories.get(category_id)

    def get_all_categories(self) -> Dict[str, ErrorCategory]:
        """Get all available categories"""
        return self.categories.copy()


# Singleton instance
_error_categorizer_instance = None


def get_error_categorizer(db_path: str = 'bridge.db') -> ErrorCategorizer:
    """Get singleton ErrorCategorizer instance"""
    global _error_categorizer_instance
    if _error_categorizer_instance is None:
        _error_categorizer_instance = ErrorCategorizer(db_path)
    return _error_categorizer_instance
