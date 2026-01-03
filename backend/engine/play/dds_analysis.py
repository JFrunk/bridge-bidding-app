"""
DDS Analysis Service - Full Double Dummy Analysis for Bridge Hands

This module provides comprehensive DDS analysis capabilities:
- Full 20-result DD table (4 players x 5 strains)
- Par score calculation with vulnerability awareness
- Deal parsing from PBN format (including 3-hand inference)

These features support:
- Post-game analysis ("What if you played 4 Spades?")
- ACBL result import and comparison
- Training feedback ("4 Hearts makes 11 tricks")
- Par score comparison ("Did you reach the optimal contract?")

Dependencies:
- endplay library (includes DDS bindings)

Platform Notes:
- Works reliably on Linux (production default)
- May crash on macOS M1/M2 - functions return None gracefully
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from engine.hand import Hand, Card, PBN_SUITS
import logging

logger = logging.getLogger(__name__)

# Try to import endplay - graceful degradation if unavailable
try:
    from endplay.types import Deal, Player, Denom, Vul
    from endplay.dds import calc_dd_table, par
    DDS_AVAILABLE = True
except ImportError as e:
    DDS_AVAILABLE = False
    Deal = None
    Player = None
    Denom = None
    Vul = None
    calc_dd_table = None
    par = None
    logger.warning(f"endplay not available: {e}")


# Position mappings
POSITION_ORDER = ['N', 'E', 'S', 'W']
# endplay Denom enum order: spades=0, hearts=1, diamonds=2, clubs=3, nt=4
# This is the order returned by calc_dd_table.to_list()[strain_idx]
STRAIN_ORDER = ['S', 'H', 'D', 'C', 'NT']
STRAIN_SYMBOLS = {'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠', 'NT': 'NT'}


@dataclass
class DDTable:
    """
    Double Dummy Table - 20 results showing tricks makeable by each player in each strain.

    Format: table[player][strain] = tricks (0-13)

    Example:
        dd_table.table['N']['NT'] = 9  # North can make 9 tricks in NT
        dd_table.table['S']['H'] = 10  # South can make 10 tricks in Hearts
    """
    table: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def __post_init__(self):
        # Initialize empty table if not provided
        if not self.table:
            for player in POSITION_ORDER:
                self.table[player] = {}
                for strain in STRAIN_ORDER:
                    self.table[player][strain] = 0

    def get_tricks(self, player: str, strain: str) -> int:
        """Get tricks makeable by player in strain."""
        return self.table.get(player, {}).get(strain, 0)

    def get_best_contract(self, declarer_side: str = 'NS') -> Tuple[str, str, int]:
        """
        Find the best contract for a side.

        Args:
            declarer_side: 'NS' or 'EW'

        Returns:
            (strain, declarer, tricks) - Best contract info
        """
        players = ['N', 'S'] if declarer_side == 'NS' else ['E', 'W']
        best = (None, None, 0)

        for strain in STRAIN_ORDER:
            for player in players:
                tricks = self.get_tricks(player, strain)
                if tricks > best[2]:
                    best = (strain, player, tricks)

        return best

    def to_dict(self) -> Dict[str, Dict[str, int]]:
        """Export as dictionary for JSON serialization."""
        return self.table

    def format_display(self) -> str:
        """Format table for text display."""
        lines = []
        lines.append("      " + "  ".join(f"{s:>3}" for s in STRAIN_ORDER))
        lines.append("-" * 30)
        for player in POSITION_ORDER:
            row = [f"{self.table[player][s]:>3}" for s in STRAIN_ORDER]
            lines.append(f"{player}:    " + "  ".join(row))
        return "\n".join(lines)


@dataclass
class ParResult:
    """
    Par (Minimax) result - the optimal contract assuming perfect bidding and defense.

    The par score represents the equilibrium where neither side can gain
    by further bidding or sacrificing.
    """
    score: int  # Par score (positive for NS, negative for EW advantage)
    contracts: List[str]  # Possible par contracts (e.g., ["4HN", "4HS"])
    declarer_side: str  # 'NS' or 'EW' (who declares at par)

    def format_display(self) -> str:
        """Format for display."""
        contracts_str = " or ".join(self.contracts)
        if self.score > 0:
            return f"Par: {contracts_str} ({self.declarer_side}) +{self.score}"
        elif self.score < 0:
            return f"Par: {contracts_str} ({self.declarer_side}) {self.score}"
        else:
            return f"Par: {contracts_str} (Tie)"

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary for JSON serialization."""
        return {
            'score': self.score,
            'contracts': self.contracts,
            'declarer_side': self.declarer_side
        }


@dataclass
class DealAnalysis:
    """
    Complete DDS analysis for a bridge deal.

    Combines DD table and par calculation for comprehensive analysis.
    """
    dd_table: Optional[DDTable] = None
    par_result: Optional[ParResult] = None
    dealer: str = 'N'
    vulnerability: str = 'None'
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Check if analysis completed successfully."""
        return self.dd_table is not None and self.error is None

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary for JSON serialization."""
        result = {
            'dealer': self.dealer,
            'vulnerability': self.vulnerability,
            'is_valid': self.is_valid
        }

        if self.dd_table:
            result['dd_table'] = self.dd_table.to_dict()
        if self.par_result:
            result['par'] = self.par_result.to_dict()
        if self.error:
            result['error'] = self.error

        return result


class DDSAnalysisService:
    """
    Service for performing DDS analysis on bridge deals.

    Usage:
        service = DDSAnalysisService()

        # Analyze from hands dictionary
        analysis = service.analyze_deal(hands, dealer='N', vulnerability='NS')

        # Analyze from PBN string
        analysis = service.analyze_pbn("N:AKQ.KJ3.T98.432 ...")

        # Get specific results
        tricks = analysis.dd_table.get_tricks('S', 'NT')
        par_score = analysis.par_result.score
    """

    def __init__(self):
        """Initialize the analysis service."""
        self._cache: Dict[str, DealAnalysis] = {}
        self.stats = {
            'analyses': 0,
            'cache_hits': 0,
            'errors': 0
        }

    @property
    def is_available(self) -> bool:
        """Check if DDS is available on this platform."""
        return DDS_AVAILABLE

    def analyze_deal(
        self,
        hands: Dict[str, Hand],
        dealer: str = 'N',
        vulnerability: str = 'None'
    ) -> DealAnalysis:
        """
        Perform full DDS analysis on a deal.

        Args:
            hands: Dictionary mapping positions to Hand objects {'N': Hand, 'E': Hand, ...}
            dealer: Dealer position ('N', 'E', 'S', 'W')
            vulnerability: Vulnerability ('None', 'NS', 'EW', 'Both')

        Returns:
            DealAnalysis with DD table and par result
        """
        if not DDS_AVAILABLE:
            return DealAnalysis(
                dealer=dealer,
                vulnerability=vulnerability,
                error="DDS not available on this platform"
            )

        # Build PBN string for caching and analysis
        try:
            pbn = self._hands_to_pbn(hands)
        except Exception as e:
            return DealAnalysis(
                dealer=dealer,
                vulnerability=vulnerability,
                error=f"Failed to build PBN: {e}"
            )

        # Check cache
        cache_key = f"{pbn}:{dealer}:{vulnerability}"
        if cache_key in self._cache:
            self.stats['cache_hits'] += 1
            return self._cache[cache_key]

        self.stats['analyses'] += 1

        try:
            # Create endplay Deal
            deal = Deal(pbn)

            # Calculate DD table
            dd_table = self._calculate_dd_table(deal)

            # Calculate par score
            par_result = self._calculate_par(deal, dealer, vulnerability)

            analysis = DealAnalysis(
                dd_table=dd_table,
                par_result=par_result,
                dealer=dealer,
                vulnerability=vulnerability
            )

            # Cache result
            self._cache[cache_key] = analysis

            return analysis

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"DDS analysis failed: {e}")
            return DealAnalysis(
                dealer=dealer,
                vulnerability=vulnerability,
                error=str(e)
            )

    def analyze_pbn(
        self,
        pbn_string: str,
        dealer: str = 'N',
        vulnerability: str = 'None'
    ) -> DealAnalysis:
        """
        Perform full DDS analysis from a PBN deal string.

        Args:
            pbn_string: Full deal in PBN format (e.g., "N:AKQ.KJ3... EJT9...")
            dealer: Dealer position
            vulnerability: Vulnerability string

        Returns:
            DealAnalysis with DD table and par result
        """
        if not DDS_AVAILABLE:
            return DealAnalysis(
                dealer=dealer,
                vulnerability=vulnerability,
                error="DDS not available on this platform"
            )

        # Check cache
        cache_key = f"{pbn_string}:{dealer}:{vulnerability}"
        if cache_key in self._cache:
            self.stats['cache_hits'] += 1
            return self._cache[cache_key]

        self.stats['analyses'] += 1

        try:
            # Handle 3-hand PBN with inference
            deal = self._parse_pbn_with_inference(pbn_string)

            # Calculate DD table
            dd_table = self._calculate_dd_table(deal)

            # Calculate par score
            par_result = self._calculate_par(deal, dealer, vulnerability)

            analysis = DealAnalysis(
                dd_table=dd_table,
                par_result=par_result,
                dealer=dealer,
                vulnerability=vulnerability
            )

            # Cache result
            self._cache[cache_key] = analysis

            return analysis

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"DDS analysis from PBN failed: {e}")
            return DealAnalysis(
                dealer=dealer,
                vulnerability=vulnerability,
                error=str(e)
            )

    def get_tricks(
        self,
        hands: Dict[str, Hand],
        declarer: str,
        strain: str
    ) -> Optional[int]:
        """
        Quick query: How many tricks can declarer make in this strain?

        Args:
            hands: Dictionary mapping positions to Hand objects
            declarer: Declarer position ('N', 'E', 'S', 'W')
            strain: Trump strain ('C', 'D', 'H', 'S', 'NT') or ('♣', '♦', '♥', '♠', 'NT')

        Returns:
            Number of tricks declarer can make (0-13), or None if DDS unavailable
        """
        analysis = self.analyze_deal(hands)
        if not analysis.is_valid:
            return None

        # Normalize strain symbol to letter
        strain_map = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}
        strain = strain_map.get(strain, strain)

        return analysis.dd_table.get_tricks(declarer, strain)

    def compare_with_par(
        self,
        hands: Dict[str, Hand],
        contract_level: int,
        contract_strain: str,
        declarer: str,
        tricks_made: int,
        vulnerability: str = 'None'
    ) -> Dict[str, Any]:
        """
        Compare a played contract with par.

        Args:
            hands: Dictionary mapping positions to Hand objects
            contract_level: Contract level (1-7)
            contract_strain: Trump strain
            declarer: Declarer position
            tricks_made: Tricks actually made
            vulnerability: Vulnerability string

        Returns:
            Dictionary with comparison results
        """
        analysis = self.analyze_deal(hands, vulnerability=vulnerability)

        if not analysis.is_valid:
            return {
                'error': analysis.error,
                'available': False
            }

        # Normalize strain
        strain_map = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}
        strain = strain_map.get(contract_strain, contract_strain)

        # Get DD tricks for this contract
        dd_tricks = analysis.dd_table.get_tricks(declarer, strain)
        tricks_needed = 6 + contract_level

        # Calculate scores
        declarer_side = 'NS' if declarer in ['N', 'S'] else 'EW'
        made_contract = tricks_made >= tricks_needed
        overtricks = tricks_made - tricks_needed if made_contract else 0
        undertricks = tricks_needed - tricks_made if not made_contract else 0

        return {
            'available': True,
            'dd_tricks': dd_tricks,
            'tricks_made': tricks_made,
            'tricks_needed': tricks_needed,
            'made_contract': made_contract,
            'overtricks': overtricks,
            'undertricks': undertricks,
            'optimal_play': tricks_made >= dd_tricks,
            'par_score': analysis.par_result.score if analysis.par_result else None,
            'par_contracts': analysis.par_result.contracts if analysis.par_result else None,
            'declarer_side': declarer_side
        }

    def _hands_to_pbn(self, hands: Dict[str, Hand]) -> str:
        """Convert hands dictionary to PBN deal string."""
        hand_strs = []
        for pos in POSITION_ORDER:
            if pos in hands:
                hand_strs.append(hands[pos].to_pbn())
            else:
                raise ValueError(f"Missing hand for position {pos}")

        return f"N:{' '.join(hand_strs)}"

    def _parse_pbn_with_inference(self, pbn_string: str) -> Deal:
        """
        Parse PBN string, inferring 4th hand if only 3 provided.

        Standard PBN format: "N:AKQ.KJ3.T98.432 JT98.Q42.KJ4.987 765.AT9.AQ5.KQJ 43.8765.7632.AT6"

        If one hand is missing (empty or "~"), infers it from remaining 52-card deck.
        """
        # First try direct parsing
        try:
            return Deal(pbn_string)
        except (ValueError, KeyError):
            pass

        # Need to infer missing hand
        # Parse the PBN format: "D:hand1 hand2 hand3 hand4"
        if ':' not in pbn_string:
            raise ValueError(f"Invalid PBN format: {pbn_string}")

        first_pos, hands_part = pbn_string.split(':', 1)
        first_pos = first_pos.strip().upper()

        if first_pos not in POSITION_ORDER:
            raise ValueError(f"Invalid starting position: {first_pos}")

        hand_segments = hands_part.strip().split()

        # Build position mapping
        positions = {}
        all_cards = set()
        missing_pos = None

        for i, segment in enumerate(hand_segments):
            pos = POSITION_ORDER[(POSITION_ORDER.index(first_pos) + i) % 4]

            if not segment or segment == '~' or segment == '-':
                missing_pos = pos
                continue

            # Parse this hand's cards
            suit_parts = segment.split('.')
            if len(suit_parts) != 4:
                continue

            for suit_idx, cards_str in enumerate(suit_parts):
                suit = PBN_SUITS[suit_idx]
                for rank in cards_str.upper():
                    if rank in 'AKQJT98765432':
                        all_cards.add((rank, suit))

            positions[pos] = segment

        # If we have 3 hands, infer the 4th
        if len(positions) == 3 and missing_pos:
            # Full deck
            full_deck = {(r, s) for r in 'AKQJT98765432' for s in PBN_SUITS}
            remaining = full_deck - all_cards

            if len(remaining) != 13:
                raise ValueError(f"Cannot infer hand: expected 13 cards, found {len(remaining)}")

            # Build the missing hand in PBN format
            by_suit = {s: [] for s in PBN_SUITS}
            for rank, suit in remaining:
                by_suit[suit].append(rank)

            # Sort by rank order
            rank_order = 'AKQJT98765432'
            for suit in by_suit:
                by_suit[suit].sort(key=lambda r: rank_order.index(r))

            inferred_pbn = '.'.join(''.join(by_suit[s]) for s in PBN_SUITS)
            positions[missing_pos] = inferred_pbn

        # Rebuild full PBN string
        hand_strs = [positions[pos] for pos in POSITION_ORDER]
        full_pbn = f"N:{' '.join(hand_strs)}"

        return Deal(full_pbn)

    def _calculate_dd_table(self, deal: Deal) -> DDTable:
        """Calculate the full 20-result DD table."""
        raw_table = calc_dd_table(deal)
        data = raw_table.to_list()

        # endplay format: data[suit_idx][player_idx]
        # Suits: 0=C, 1=D, 2=H, 3=S, 4=NT
        # Players: 0=N, 1=E, 2=S, 3=W

        table = {}
        for p_idx, player in enumerate(POSITION_ORDER):
            table[player] = {}
            for s_idx, strain in enumerate(STRAIN_ORDER):
                table[player][strain] = data[s_idx][p_idx]

        return DDTable(table=table)

    def _calculate_par(self, deal: Deal, dealer: str, vulnerability: str) -> Optional[ParResult]:
        """Calculate par (minimax) result."""
        try:
            # Map vulnerability string to endplay Vul enum
            vul_map = {
                'None': Vul.none,
                'NS': Vul.ns,
                'EW': Vul.ew,
                'Both': Vul.both,
                'All': Vul.both
            }
            vul = vul_map.get(vulnerability, Vul.none)

            # Map dealer to endplay Player enum
            dealer_map = {
                'N': Player.north,
                'E': Player.east,
                'S': Player.south,
                'W': Player.west
            }
            dealer_player = dealer_map.get(dealer, Player.north)

            # Calculate DD table first (needed for par)
            dd_table_raw = calc_dd_table(deal)

            # Get par result
            result = par(dd_table_raw, vul, dealer_player)

            # Parse the par result
            # result.score is the par score (positive = NS advantage)
            # result is iterable with contract objects
            contracts = []
            for contract in result:
                # Format: level + strain + declarer
                contracts.append(str(contract))

            # Determine which side declares at par
            if contracts:
                # Check first contract's declarer
                first_contract = str(contracts[0])
                if first_contract and len(first_contract) >= 3:
                    declarer_char = first_contract[-1] if first_contract[-1] in 'NESW' else 'N'
                    declarer_side = 'NS' if declarer_char in 'NS' else 'EW'
                else:
                    declarer_side = 'NS' if result.score >= 0 else 'EW'
            else:
                declarer_side = 'NS' if result.score >= 0 else 'EW'

            return ParResult(
                score=result.score,
                contracts=contracts if contracts else ['Pass'],
                declarer_side=declarer_side
            )

        except Exception as e:
            logger.warning(f"Par calculation failed: {e}")
            return None

    def clear_cache(self):
        """Clear the analysis cache."""
        self._cache.clear()

    def get_stats(self) -> Dict[str, int]:
        """Get usage statistics."""
        return {
            **self.stats,
            'cache_size': len(self._cache)
        }


# Module-level singleton for convenience
_service: Optional[DDSAnalysisService] = None

def get_dds_service() -> DDSAnalysisService:
    """Get the singleton DDS analysis service."""
    global _service
    if _service is None:
        _service = DDSAnalysisService()
    return _service


def is_dds_available() -> bool:
    """Check if DDS is available on this platform."""
    return DDS_AVAILABLE


# Convenience functions for common operations

def analyze_deal(
    hands: Dict[str, Hand],
    dealer: str = 'N',
    vulnerability: str = 'None'
) -> DealAnalysis:
    """
    Convenience function to analyze a deal.

    Args:
        hands: Dictionary mapping positions to Hand objects
        dealer: Dealer position
        vulnerability: Vulnerability string

    Returns:
        DealAnalysis with DD table and par result
    """
    return get_dds_service().analyze_deal(hands, dealer, vulnerability)


def get_dd_table(hands: Dict[str, Hand]) -> Optional[DDTable]:
    """
    Get just the DD table for a deal.

    Args:
        hands: Dictionary mapping positions to Hand objects

    Returns:
        DDTable or None if DDS unavailable
    """
    analysis = get_dds_service().analyze_deal(hands)
    return analysis.dd_table if analysis.is_valid else None


def get_par_score(
    hands: Dict[str, Hand],
    dealer: str = 'N',
    vulnerability: str = 'None'
) -> Optional[ParResult]:
    """
    Get just the par result for a deal.

    Args:
        hands: Dictionary mapping positions to Hand objects
        dealer: Dealer position
        vulnerability: Vulnerability string

    Returns:
        ParResult or None if DDS unavailable
    """
    analysis = get_dds_service().analyze_deal(hands, dealer, vulnerability)
    return analysis.par_result if analysis.is_valid else None
