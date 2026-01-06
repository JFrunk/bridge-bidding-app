"""
Differential Analyzer for Bridge Bidding Feedback

Compares user's bid against optimal bid using rule-based analysis.
Provides educational feedback showing exactly why bids differ and
what specific constraints separate them.

This transforms feedback from binary "right/wrong" to a physics-based
differential analysis using the same Golden Master logic that powers the AI.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from engine.hand import Hand
from engine.v2.features.enhanced_extractor import extract_flat_features
from engine.v2.interpreters.schema_interpreter import SchemaInterpreter


class DiagnosticDomain(Enum):
    """Learning domains for categorizing feedback."""
    SAFETY = "safety"          # LoTT ceiling violations
    VALUE = "value"            # Positional/Working HCP issues
    CONTROL = "control"        # Ruffing/Trump quality
    TACTICAL = "tactical"      # Preempt/Sacrifice decisions
    DEFENSIVE = "defensive"    # Quick tricks, penalty opportunities
    GENERAL = "general"        # Other/mixed


@dataclass
class DifferentialFactor:
    """A specific factor that differentiates user's bid from optimal."""
    feature: str                    # e.g., "lott_safe_level"
    label: str                      # Human-readable label
    actual_value: Any               # What user had
    required_value: Any             # What the rule required
    gap: str                        # Human-readable gap description
    impact: str                     # How this affected the bid
    status: str                     # "PASS", "FAIL", "WARNING", "INFO"
    shortfall: Optional[float] = None  # Numeric shortfall if applicable


@dataclass
class RuleMatch:
    """Information about a rule that matches a bid."""
    rule_id: str
    bid: str
    priority: int
    description: str
    category: str
    conditions_met: int
    conditions_total: int
    conditions: List[Dict]
    forcing: str = "none"


@dataclass
class PhysicsSummary:
    """Summary of the hand's physics-based features."""
    hcp: int
    total_points: int
    shape: str
    lott_safe_level: Optional[int]
    working_hcp_ratio: float
    quick_tricks: float
    support_points: Optional[int]
    control_multiplier: float
    is_balanced: bool
    is_misfit: bool
    is_fragile_ruff: bool
    longest_suit: str
    fit_length: Optional[int]
    stoppers: Dict[str, bool]


@dataclass
class DifferentialResult:
    """Complete result of differential analysis."""
    user_bid: str
    optimal_bid: str
    rating: str                     # "optimal", "acceptable", "suboptimal", "error"
    score: int                      # 0-100

    # Rule matching analysis
    user_bid_rules: List[RuleMatch]
    optimal_bid_rules: List[RuleMatch]

    # The differential
    differential_factors: List[DifferentialFactor]

    # Physics context
    physics: PhysicsSummary

    # Educational output
    primary_reason: str
    learning_point: str
    diagnostic_domain: DiagnosticDomain
    tutorial_link: Optional[str]

    # HTML formatted commentary
    commentary_html: str


# Feature to hint mapping for educational messages
FEATURE_HINTS = {
    'lott_safe_level': {
        'domain': DiagnosticDomain.SAFETY,
        'label': 'LoTT Safe Level',
        'hint_template': "Law of Total Tricks: Your {fit_length}-card fit supports bidding to level {safe_level}.",
        'tutorial': '/learn/lott'
    },
    'working_hcp_ratio': {
        'domain': DiagnosticDomain.VALUE,
        'label': 'Working HCP Ratio',
        'hint_template': "Only {ratio:.0%} of your HCP are 'working' in useful suits.",
        'tutorial': '/learn/working-points'
    },
    'quick_tricks': {
        'domain': DiagnosticDomain.DEFENSIVE,
        'label': 'Quick Tricks',
        'hint_template': "With {qt:.1f} Quick Tricks, you have strong defensive potential.",
        'tutorial': '/learn/quick-tricks'
    },
    'control_multiplier': {
        'domain': DiagnosticDomain.CONTROL,
        'label': 'Control Multiplier',
        'hint_template': "Your trump quality ({quality}) affects the value of shortness.",
        'tutorial': '/learn/trump-control'
    },
    'is_fragile_ruff': {
        'domain': DiagnosticDomain.CONTROL,
        'label': 'Fragile Ruff',
        'hint_template': "Weak trumps make your shortness vulnerable to over-ruffs.",
        'tutorial': '/learn/ruffing-value'
    },
    'is_misfit': {
        'domain': DiagnosticDomain.VALUE,
        'label': 'Misfit Detection',
        'hint_template': "No good fit found with partner. Misfits play poorly.",
        'tutorial': '/learn/misfits'
    },
    'support_points': {
        'domain': DiagnosticDomain.VALUE,
        'label': 'Support Points',
        'hint_template': "With {sp} support points, your hand is worth more than raw HCP.",
        'tutorial': '/learn/support-points'
    },
    'hcp': {
        'domain': DiagnosticDomain.GENERAL,
        'label': 'High Card Points',
        'hint_template': "You have {hcp} HCP. The bid requires {required}.",
        'tutorial': '/learn/hcp'
    },
    'stoppers_count': {
        'domain': DiagnosticDomain.GENERAL,
        'label': 'Stoppers',
        'hint_template': "NT contracts require stoppers in unbid suits.",
        'tutorial': '/learn/stoppers'
    }
}


class DifferentialAnalyzer:
    """
    Compares user's bid against optimal bid using rule-based analysis.
    Provides educational feedback showing exactly why bids differ.
    """

    def __init__(self):
        self.interpreter = SchemaInterpreter()

    def analyze(
        self,
        user_bid: str,
        optimal_bid: str,
        hand: Hand,
        auction_history: List[str],
        position: str,
        vulnerability: str,
        dealer: str = 'North'
    ) -> DifferentialResult:
        """
        Main entry point for differential analysis.

        Compares the user's bid against the optimal bid and identifies
        the specific features/constraints that differentiate them.

        Args:
            user_bid: The bid the user made
            optimal_bid: The optimal bid from the engine
            hand: The user's hand
            auction_history: List of bids in the auction
            position: Player position (North/East/South/West)
            vulnerability: Vulnerability string
            dealer: Dealer position

        Returns:
            DifferentialResult with complete analysis
        """
        # Extract features for this hand/auction
        features = extract_flat_features(
            hand, auction_history, position, vulnerability, dealer
        )

        # Get gap analysis for all rules
        all_rule_analysis = self.interpreter.get_rule_gap_analysis(
            features, target_bid=None, max_rules=50
        )

        # Find rules matching user's bid
        user_bid_rules = self._get_rules_for_bid(user_bid, all_rule_analysis)

        # Find rules matching optimal bid
        optimal_bid_rules = self._get_rules_for_bid(optimal_bid, all_rule_analysis)

        # Calculate differential factors
        differential_factors = self._calculate_differential(
            user_bid, optimal_bid, user_bid_rules, optimal_bid_rules, features
        )

        # Determine diagnostic domain
        domain = self._classify_domain(differential_factors)

        # Calculate rating and score
        rating, score = self._calculate_rating(
            user_bid, optimal_bid, differential_factors
        )

        # Build physics summary
        physics = self._build_physics_summary(features)

        # Generate educational content
        primary_reason = self._generate_primary_reason(
            user_bid, optimal_bid, differential_factors, features
        )
        learning_point = self._generate_learning_point(
            differential_factors, domain, features
        )
        tutorial_link = self._get_tutorial_link(domain, differential_factors)
        commentary_html = self._generate_commentary_html(
            user_bid, optimal_bid, rating, primary_reason,
            differential_factors, user_bid_rules, optimal_bid_rules
        )

        return DifferentialResult(
            user_bid=user_bid,
            optimal_bid=optimal_bid,
            rating=rating,
            score=score,
            user_bid_rules=user_bid_rules,
            optimal_bid_rules=optimal_bid_rules,
            differential_factors=differential_factors,
            physics=physics,
            primary_reason=primary_reason,
            learning_point=learning_point,
            diagnostic_domain=domain,
            tutorial_link=tutorial_link,
            commentary_html=commentary_html
        )

    def _get_rules_for_bid(
        self,
        bid: str,
        all_rules: List[Dict]
    ) -> List[RuleMatch]:
        """Get rules that match or nearly match a specific bid."""
        matches = []

        for rule in all_rules:
            if rule['bid'] == bid:
                matches.append(RuleMatch(
                    rule_id=rule['rule_id'],
                    bid=rule['bid'],
                    priority=rule['priority'],
                    description=rule['description'],
                    category=rule['category'],
                    conditions_met=sum(1 for c in rule['conditions'] if c['passed']),
                    conditions_total=len(rule['conditions']),
                    conditions=rule['conditions'],
                    forcing=rule.get('forcing', 'none')
                ))

        # Sort by priority (highest first), then by conditions met
        matches.sort(key=lambda r: (-r.priority, -r.conditions_met))
        return matches

    def _calculate_differential(
        self,
        user_bid: str,
        optimal_bid: str,
        user_rules: List[RuleMatch],
        optimal_rules: List[RuleMatch],
        features: Dict[str, Any]
    ) -> List[DifferentialFactor]:
        """
        Calculate the specific factors that differentiate the bids.

        Returns a list of DifferentialFactors explaining why the optimal
        bid is better than the user's bid.
        """
        factors = []

        # If bids are the same, no differential
        if user_bid == optimal_bid:
            return factors

        # Get the highest priority matching rule for optimal bid
        optimal_rule = None
        for rule in optimal_rules:
            if rule.conditions_met == rule.conditions_total:
                optimal_rule = rule
                break

        # Get the highest priority matching rule for user's bid
        user_rule = None
        for rule in user_rules:
            if rule.conditions_met == rule.conditions_total:
                user_rule = rule
                break

        # Priority-based differential
        if optimal_rule and user_rule:
            if optimal_rule.priority > user_rule.priority:
                factors.append(DifferentialFactor(
                    feature='rule_priority',
                    label='Rule Priority',
                    actual_value=user_rule.priority,
                    required_value=optimal_rule.priority,
                    gap=f"Optimal rule has higher priority ({optimal_rule.priority} > {user_rule.priority})",
                    impact=f"'{optimal_rule.rule_id}' takes precedence over '{user_rule.rule_id}'",
                    status='INFO'
                ))

        # LoTT Safety differential
        lott_safe = features.get('lott_safe_level')
        if lott_safe is not None:
            user_level = self._get_bid_level(user_bid)
            optimal_level = self._get_bid_level(optimal_bid)

            if user_level and user_level > lott_safe:
                factors.append(DifferentialFactor(
                    feature='lott_safe_level',
                    label='LoTT Safe Level',
                    actual_value=lott_safe,
                    required_value=user_level,
                    gap=f"Level {user_level} exceeds safe level {lott_safe}",
                    impact=f"Overbid by {user_level - lott_safe} level(s)",
                    status='FAIL',
                    shortfall=user_level - lott_safe
                ))

        # HCP differential for specific rules
        if optimal_rule:
            for cond in optimal_rule.conditions:
                if cond['key'] == 'hcp' and not cond['passed']:
                    shortfall = cond.get('min_shortfall', 0)
                    factors.append(DifferentialFactor(
                        feature='hcp',
                        label='High Card Points',
                        actual_value=features.get('hcp', 0),
                        required_value=cond.get('required'),
                        gap=cond.get('gap', f"Need {shortfall} more HCP"),
                        impact=f"Insufficient strength for {optimal_bid}",
                        status='FAIL',
                        shortfall=shortfall
                    ))

        # Check why user's bid rule might not be optimal
        if user_rules and not user_rule:
            # User bid doesn't fully match any rule
            best_near_miss = None
            for rule in user_rules:
                if rule.conditions_met < rule.conditions_total:
                    best_near_miss = rule
                    break

            if best_near_miss:
                for cond in best_near_miss.conditions:
                    if not cond['passed']:
                        feature_info = FEATURE_HINTS.get(cond['key'], {})
                        factors.append(DifferentialFactor(
                            feature=cond['key'],
                            label=feature_info.get('label', cond['key'].replace('_', ' ').title()),
                            actual_value=cond.get('actual'),
                            required_value=cond.get('required'),
                            gap=cond.get('gap', 'Condition not met'),
                            impact=f"Prevents matching rule '{best_near_miss.rule_id}'",
                            status='FAIL',
                            shortfall=cond.get('min_shortfall')
                        ))

        # Working HCP ratio for value-based differential
        working_ratio = features.get('working_hcp_ratio', 1.0)
        if working_ratio < 0.5 and optimal_bid.lower() == 'pass':
            factors.append(DifferentialFactor(
                feature='working_hcp_ratio',
                label='Working HCP Ratio',
                actual_value=working_ratio,
                required_value=0.5,
                gap=f"Only {working_ratio:.0%} of HCP are working",
                impact="Too many wasted points for aggressive action",
                status='WARNING',
                shortfall=0.5 - working_ratio
            ))

        # Misfit detection
        is_misfit = features.get('is_misfit', False)
        if is_misfit and optimal_bid.lower() == 'pass':
            factors.append(DifferentialFactor(
                feature='is_misfit',
                label='Misfit Detection',
                actual_value=True,
                required_value=False,
                gap="No fit found with partner",
                impact="Misfits play poorly; conservative action recommended",
                status='WARNING'
            ))

        # Quick tricks for defensive differential
        qt = features.get('quick_tricks', 0)
        if qt >= 3.0 and 'x' in optimal_bid.lower():  # Double
            factors.append(DifferentialFactor(
                feature='quick_tricks',
                label='Quick Tricks',
                actual_value=qt,
                required_value=3.0,
                gap=f"{qt:.1f} quick tricks = defensive powerhouse",
                impact="Consider penalty double instead of competing",
                status='INFO'
            ))

        # Fragile ruff warning
        is_fragile = features.get('is_fragile_ruff', False)
        if is_fragile:
            factors.append(DifferentialFactor(
                feature='is_fragile_ruff',
                label='Fragile Ruff',
                actual_value=True,
                required_value=False,
                gap="Weak trumps with shortness",
                impact="Shortness value reduced due to over-ruff risk",
                status='WARNING'
            ))

        return factors

    def _classify_domain(
        self,
        factors: List[DifferentialFactor]
    ) -> DiagnosticDomain:
        """Classify the primary learning domain based on differential factors."""
        if not factors:
            return DiagnosticDomain.GENERAL

        # Count domains from factors
        domain_counts = {}
        for factor in factors:
            feature = factor.feature
            if feature in FEATURE_HINTS:
                domain = FEATURE_HINTS[feature]['domain']
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            elif feature == 'lott_safe_level':
                domain_counts[DiagnosticDomain.SAFETY] = \
                    domain_counts.get(DiagnosticDomain.SAFETY, 0) + 2  # Weight safety higher
            elif feature == 'hcp':
                domain_counts[DiagnosticDomain.GENERAL] = \
                    domain_counts.get(DiagnosticDomain.GENERAL, 0) + 1

        if not domain_counts:
            return DiagnosticDomain.GENERAL

        # Return most common domain
        return max(domain_counts, key=domain_counts.get)

    def _calculate_rating(
        self,
        user_bid: str,
        optimal_bid: str,
        factors: List[DifferentialFactor]
    ) -> Tuple[str, int]:
        """Calculate rating and score based on differential."""
        if user_bid == optimal_bid:
            return "optimal", 100

        # Count severity of factors
        fail_count = sum(1 for f in factors if f.status == 'FAIL')
        warning_count = sum(1 for f in factors if f.status == 'WARNING')

        # Check if it's a level difference (overbid/underbid)
        user_level = self._get_bid_level(user_bid)
        optimal_level = self._get_bid_level(optimal_bid)
        level_diff = abs((user_level or 0) - (optimal_level or 0))

        if fail_count == 0 and warning_count <= 1:
            return "acceptable", 75 - (warning_count * 10)
        elif fail_count == 1 and level_diff <= 1:
            return "suboptimal", 55 - (warning_count * 5)
        elif fail_count <= 2:
            return "suboptimal", 40 - (fail_count * 5)
        else:
            return "error", max(10, 30 - (fail_count * 10))

    def _build_physics_summary(self, features: Dict[str, Any]) -> PhysicsSummary:
        """Build a summary of physics-based features."""
        shape = (f"{features.get('spades_length', 0)}-"
                 f"{features.get('hearts_length', 0)}-"
                 f"{features.get('diamonds_length', 0)}-"
                 f"{features.get('clubs_length', 0)}")

        return PhysicsSummary(
            hcp=features.get('hcp', 0),
            total_points=features.get('total_points', 0),
            shape=shape,
            lott_safe_level=features.get('lott_safe_level'),
            working_hcp_ratio=features.get('working_hcp_ratio', 1.0),
            quick_tricks=features.get('quick_tricks', 0.0),
            support_points=features.get('support_points'),
            control_multiplier=features.get('control_multiplier', 1.0),
            is_balanced=features.get('is_balanced', False),
            is_misfit=features.get('is_misfit', False),
            is_fragile_ruff=features.get('is_fragile_ruff', False),
            longest_suit=features.get('longest_suit', ''),
            fit_length=features.get('fit_length'),
            stoppers={
                'spades': features.get('spades_stopped', False),
                'hearts': features.get('hearts_stopped', False),
                'diamonds': features.get('diamonds_stopped', False),
                'clubs': features.get('clubs_stopped', False)
            }
        )

    def _generate_primary_reason(
        self,
        user_bid: str,
        optimal_bid: str,
        factors: List[DifferentialFactor],
        features: Dict[str, Any]
    ) -> str:
        """Generate a single-sentence explanation of the differential."""
        if user_bid == optimal_bid:
            return "Your bid matches the optimal choice."

        # Find the most impactful factor
        fail_factors = [f for f in factors if f.status == 'FAIL']
        if fail_factors:
            main_factor = fail_factors[0]
            return main_factor.gap

        warning_factors = [f for f in factors if f.status == 'WARNING']
        if warning_factors:
            main_factor = warning_factors[0]
            return main_factor.gap

        # Default based on bid comparison
        user_level = self._get_bid_level(user_bid)
        optimal_level = self._get_bid_level(optimal_bid)

        if user_level and optimal_level:
            if user_level > optimal_level:
                return f"Your bid at level {user_level} is too aggressive."
            elif user_level < optimal_level:
                return f"Your bid at level {user_level} is too conservative."

        return f"The optimal bid is {optimal_bid} instead of {user_bid}."

    def _generate_learning_point(
        self,
        factors: List[DifferentialFactor],
        domain: DiagnosticDomain,
        features: Dict[str, Any]
    ) -> str:
        """Generate an educational learning point."""
        # Find the primary factor for this domain
        for factor in factors:
            if factor.feature in FEATURE_HINTS:
                hint_info = FEATURE_HINTS[factor.feature]
                template = hint_info.get('hint_template', '')

                # Fill in template variables
                try:
                    return template.format(
                        fit_length=features.get('fit_length', 8),
                        safe_level=features.get('lott_safe_level', 2),
                        ratio=features.get('working_hcp_ratio', 1.0),
                        qt=features.get('quick_tricks', 0.0),
                        quality=features.get('trump_suit_quality', 'moderate'),
                        sp=features.get('support_points', 0),
                        hcp=features.get('hcp', 0),
                        required=factor.required_value
                    )
                except (KeyError, ValueError):
                    continue

        # Domain-specific fallback messages
        domain_messages = {
            DiagnosticDomain.SAFETY: "Consider the Law of Total Tricks when competing.",
            DiagnosticDomain.VALUE: "Evaluate where your HCP are located relative to the bidding.",
            DiagnosticDomain.CONTROL: "Trump quality affects the value of distribution.",
            DiagnosticDomain.TACTICAL: "Preemptive actions should balance risk and reward.",
            DiagnosticDomain.DEFENSIVE: "Strong defensive hands may prefer penalty over competition.",
            DiagnosticDomain.GENERAL: "Bridge bidding balances many factors - strength, fit, and position."
        }

        return domain_messages.get(domain, domain_messages[DiagnosticDomain.GENERAL])

    def _get_tutorial_link(
        self,
        domain: DiagnosticDomain,
        factors: List[DifferentialFactor]
    ) -> Optional[str]:
        """Get the most relevant tutorial link."""
        for factor in factors:
            if factor.feature in FEATURE_HINTS:
                return FEATURE_HINTS[factor.feature].get('tutorial')

        # Domain-based fallback
        domain_tutorials = {
            DiagnosticDomain.SAFETY: '/learn/lott',
            DiagnosticDomain.VALUE: '/learn/working-points',
            DiagnosticDomain.CONTROL: '/learn/trump-control',
            DiagnosticDomain.DEFENSIVE: '/learn/quick-tricks'
        }
        return domain_tutorials.get(domain)

    def _generate_commentary_html(
        self,
        user_bid: str,
        optimal_bid: str,
        rating: str,
        primary_reason: str,
        factors: List[DifferentialFactor],
        user_rules: List[RuleMatch],
        optimal_rules: List[RuleMatch]
    ) -> str:
        """Generate HTML-formatted commentary for the UI."""
        if user_bid == optimal_bid:
            return f"<strong>Excellent!</strong> Your bid of {user_bid} is optimal."

        html_parts = []

        # Rating header
        rating_class = {
            'optimal': 'success',
            'acceptable': 'info',
            'suboptimal': 'warning',
            'error': 'danger'
        }.get(rating, 'warning')

        html_parts.append(
            f'<div class="rating-{rating_class}">'
            f'<strong>{rating.title()}</strong>: '
            f'You bid {user_bid}, optimal is {optimal_bid}'
            f'</div>'
        )

        # Primary reason
        html_parts.append(f'<p class="primary-reason">{primary_reason}</p>')

        # Key factors
        if factors:
            html_parts.append('<div class="factors">')
            html_parts.append('<strong>Key Factors:</strong>')
            html_parts.append('<ul>')
            for factor in factors[:3]:  # Limit to top 3
                status_icon = {
                    'FAIL': '❌',
                    'WARNING': '⚠️',
                    'INFO': 'ℹ️',
                    'PASS': '✓'
                }.get(factor.status, '•')
                html_parts.append(
                    f'<li>{status_icon} <strong>{factor.label}:</strong> {factor.gap}</li>'
                )
            html_parts.append('</ul>')
            html_parts.append('</div>')

        # Rule comparison (if available)
        if optimal_rules:
            best_optimal = optimal_rules[0]
            html_parts.append(
                f'<div class="rule-info">'
                f'<small>Rule: {best_optimal.rule_id} (Priority: {best_optimal.priority})</small>'
                f'</div>'
            )

        return '\n'.join(html_parts)

    def _get_bid_level(self, bid: str) -> Optional[int]:
        """Extract the level from a bid string."""
        if not bid:
            return None
        bid_upper = bid.upper()
        if bid_upper in ['PASS', 'X', 'XX', 'DOUBLE', 'REDOUBLE']:
            return None
        try:
            return int(bid[0])
        except (ValueError, IndexError):
            return None


def get_differential_analyzer() -> DifferentialAnalyzer:
    """Factory function to get a DifferentialAnalyzer instance."""
    return DifferentialAnalyzer()
