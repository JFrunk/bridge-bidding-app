"""
Session Manager - Multi-hand game session tracking

Manages Chicago Bridge sessions (4 hands with rotating dealer/vulnerability)
and other session types. Fully integrated with user management system.

Features:
- Multi-user session tracking
- Chicago Bridge format (4 hands, rotating dealer, predetermined vulnerability)
- Complete hand history with scoring
- Session statistics and analytics
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
import json
from datetime import datetime
import logging
from engine.play_engine import Contract

# Use database abstraction layer for SQLite/PostgreSQL compatibility
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_connection

# DDS analysis for post-game insights (optional - graceful degradation)
try:
    from engine.play.dds_analysis import get_dds_service, is_dds_available
    DDS_ENABLED = is_dds_available()
except ImportError:
    DDS_ENABLED = False
    get_dds_service = None

logger = logging.getLogger(__name__)


@dataclass
class GameSession:
    """Manages multi-hand game sessions"""
    id: Optional[int] = None
    user_id: int = 1
    session_type: str = 'chicago'
    hands_completed: int = 0
    current_hand_number: int = 1
    max_hands: int = 4
    ns_score: int = 0
    ew_score: int = 0
    status: str = 'active'
    player_position: str = 'S'  # User plays South by default
    ai_difficulty: str = 'intermediate'
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_time_seconds: int = 0

    # Chicago schedule constants
    CHICAGO_DEALERS = ['N', 'E', 'S', 'W']
    CHICAGO_VULNERABILITY = ['None', 'NS', 'EW', 'Both']

    def get_current_dealer(self) -> str:
        """Get dealer for current hand based on Chicago rotation"""
        return self.CHICAGO_DEALERS[(self.current_hand_number - 1) % 4]

    def get_current_vulnerability(self) -> str:
        """Get vulnerability for current hand based on Chicago schedule"""
        return self.CHICAGO_VULNERABILITY[(self.current_hand_number - 1) % 4]

    def add_hand_score(self, declarer: str, score: int) -> None:
        """
        Add score from completed hand to the appropriate side

        Args:
            declarer: Position who declared ('N', 'E', 'S', 'W')
            score: Points scored from declarer's perspective
                   (positive for making, negative for going down)

        Bridge Scoring Logic:
        - If score > 0: Declarer made contract, add to declarer's side
        - If score < 0: Defenders set the contract, add absolute value to defending side

        Examples:
        - NS declares 3NT, makes (+400): NS gets +400
        - NS declares 3NT, down 1 (-50): EW gets +50 (defenders' reward)
        - EW declares 4♠, makes (+420): EW gets +420
        - EW declares 4♠, down 2 (-100): NS gets +100 (defenders' reward)
        """
        declarer_is_ns = declarer in ['N', 'S']

        if score >= 0:
            # Contract made - points go to declaring side
            if declarer_is_ns:
                self.ns_score += score
            else:
                self.ew_score += score
        else:
            # Contract defeated - penalty points go to defending side
            penalty_points = abs(score)
            if declarer_is_ns:
                # NS declared and went down, EW gets the penalty points
                self.ew_score += penalty_points
            else:
                # EW declared and went down, NS gets the penalty points
                self.ns_score += penalty_points

        self.hands_completed += 1
        self.current_hand_number += 1

        if self.hands_completed >= self.max_hands:
            self.status = 'completed'

    def is_complete(self) -> bool:
        """Check if session has completed all hands"""
        return self.hands_completed >= self.max_hands

    def get_winner(self) -> Optional[str]:
        """Get session winner (NS, EW, or Tied)"""
        if not self.is_complete():
            return None

        if self.ns_score > self.ew_score:
            return 'NS'
        elif self.ew_score > self.ns_score:
            return 'EW'
        else:
            return 'Tied'

    def get_user_won(self) -> Optional[bool]:
        """Check if user won the session based on their position"""
        if not self.is_complete():
            return None

        winner = self.get_winner()
        if winner == 'Tied':
            return None

        user_on_ns = self.player_position in ['N', 'S']
        return (winner == 'NS') == user_on_ns

    def get_score_difference(self) -> int:
        """Get absolute score difference"""
        return abs(self.ns_score - self.ew_score)

    def get_current_leader(self) -> str:
        """Get current leader (NS, EW, or Tied)"""
        if self.ns_score > self.ew_score:
            return 'NS'
        elif self.ew_score > self.ns_score:
            return 'EW'
        else:
            return 'Tied'

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_type': self.session_type,
            'hands_completed': self.hands_completed,
            'current_hand_number': self.current_hand_number,
            'max_hands': self.max_hands,
            'ns_score': self.ns_score,
            'ew_score': self.ew_score,
            'status': self.status,
            'dealer': self.get_current_dealer(),
            'vulnerability': self.get_current_vulnerability(),
            'is_complete': self.is_complete(),
            'winner': self.get_winner(),
            'current_leader': self.get_current_leader(),
            'score_difference': self.get_score_difference(),
            'player_position': self.player_position,
            'ai_difficulty': self.ai_difficulty,
            'started_at': self.started_at
        }


class SessionManager:
    """Database operations for game sessions"""

    def __init__(self, db_path: str = 'backend/bridge.db'):
        self.db_path = db_path  # Kept for backward compatibility, but not used

    def _get_connection(self):
        """Get database connection using abstraction layer"""
        return get_connection()

    def create_session(self, user_id: int = 1,
                      session_type: str = 'chicago',
                      player_position: str = 'S',
                      ai_difficulty: str = 'intermediate') -> GameSession:
        """
        Create new game session

        Args:
            user_id: User ID (default 1 for backward compatibility)
            session_type: Type of session ('chicago', 'rubber', 'practice')
            player_position: Which position user plays (default 'S')
            ai_difficulty: AI difficulty level

        Returns:
            GameSession object with new session ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        max_hands = 4 if session_type == 'chicago' else 100  # Arbitrary large number for practice

        cursor.execute("""
            INSERT INTO game_sessions
            (user_id, session_type, max_hands, player_position, ai_difficulty)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, session_type, max_hands, player_position, ai_difficulty))

        session_id = cursor.lastrowid
        conn.commit()

        # Get the created session with timestamp
        cursor.execute("SELECT started_at FROM game_sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        started_at = row['started_at'] if row else None

        conn.close()

        return GameSession(
            id=session_id,
            user_id=user_id,
            session_type=session_type,
            max_hands=max_hands,
            player_position=player_position,
            ai_difficulty=ai_difficulty,
            started_at=started_at
        )

    def get_active_session(self, user_id: int = 1) -> Optional[GameSession]:
        """
        Get user's active session

        Args:
            user_id: User ID to look up

        Returns:
            GameSession if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, session_type, hands_completed, current_hand_number,
                   max_hands, ns_score, ew_score, status, player_position,
                   ai_difficulty, started_at, total_time_seconds
            FROM game_sessions
            WHERE user_id = ? AND status = 'active'
            ORDER BY started_at DESC
            LIMIT 1
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return GameSession(
            id=row['id'],
            user_id=row['user_id'],
            session_type=row['session_type'],
            hands_completed=row['hands_completed'],
            current_hand_number=row['current_hand_number'],
            max_hands=row['max_hands'],
            ns_score=row['ns_score'],
            ew_score=row['ew_score'],
            status=row['status'],
            player_position=row['player_position'],
            ai_difficulty=row['ai_difficulty'],
            started_at=row['started_at'],
            total_time_seconds=row['total_time_seconds']
        )

    def get_session(self, session_id: int) -> Optional[GameSession]:
        """Get specific session by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, session_type, hands_completed, current_hand_number,
                   max_hands, ns_score, ew_score, status, player_position,
                   ai_difficulty, started_at, completed_at, total_time_seconds
            FROM game_sessions
            WHERE id = ?
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return GameSession(
            id=row['id'],
            user_id=row['user_id'],
            session_type=row['session_type'],
            hands_completed=row['hands_completed'],
            current_hand_number=row['current_hand_number'],
            max_hands=row['max_hands'],
            ns_score=row['ns_score'],
            ew_score=row['ew_score'],
            status=row['status'],
            player_position=row['player_position'],
            ai_difficulty=row['ai_difficulty'],
            started_at=row['started_at'],
            completed_at=row['completed_at'],
            total_time_seconds=row['total_time_seconds']
        )

    def save_hand_result(self, session: GameSession, hand_data: Dict) -> None:
        """
        Save hand result and update session scores

        Args:
            session: Current GameSession object
            hand_data: Dictionary with hand details:
                - hand_number: Hand number in session
                - dealer: Dealer position
                - vulnerability: Vulnerability string
                - contract: Contract object (or None if passed out)
                - tricks_taken: Tricks taken by declarer
                - hand_score: Score for this hand
                - breakdown: Score breakdown dict
                - deal_data: Full deal (all 4 hands)
                - auction_history: List of bids
                - play_history: List of played cards (optional)
                - user_was_declarer: Bool
                - user_was_dummy: Bool
                - hand_duration_seconds: Time taken
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        contract = hand_data.get('contract')

        # Check if DDS columns exist (migration 007)
        cursor.execute("PRAGMA table_info(session_hands)")
        columns = {row['name'] for row in cursor.fetchall()}
        has_dds_columns = 'dds_analysis' in columns

        # Perform DDS analysis if available (non-blocking)
        dds_analysis_json = None
        par_score = None
        par_contract = None
        dd_tricks = None

        if has_dds_columns and DDS_ENABLED and contract and hand_data.get('deal_data'):
            try:
                dds_result = self._perform_dds_analysis(
                    hand_data['deal_data'],
                    hand_data.get('dealer', 'N'),
                    hand_data.get('vulnerability', 'None'),
                    contract
                )
                if dds_result:
                    dds_analysis_json = dds_result.get('analysis_json')
                    par_score = dds_result.get('par_score')
                    par_contract = dds_result.get('par_contract')
                    dd_tricks = dds_result.get('dd_tricks')
                    logger.info(f"DDS analysis complete: par={par_score}, dd_tricks={dd_tricks}")
            except Exception as e:
                logger.warning(f"DDS analysis failed (non-blocking): {e}")

        # Insert hand result - use appropriate query based on schema
        if has_dds_columns:
            cursor.execute("""
                INSERT INTO session_hands
                (session_id, hand_number, dealer, vulnerability,
                 contract_level, contract_strain, contract_declarer, contract_doubled,
                 tricks_taken, tricks_needed, made,
                 hand_score, score_breakdown, honors_bonus,
                 ns_total_after, ew_total_after,
                 deal_data, auction_history, play_history,
                 user_played_position, user_was_declarer, user_was_dummy,
                 hand_duration_seconds,
                 dds_analysis, par_score, par_contract, dd_tricks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id,
                hand_data['hand_number'],
                hand_data['dealer'],
                hand_data['vulnerability'],
                contract.level if contract else None,
                contract.strain if contract else None,
                contract.declarer if contract else None,
                contract.doubled if contract else 0,
                hand_data.get('tricks_taken'),
                contract.tricks_needed if contract else None,
                hand_data.get('made', False),
                hand_data['hand_score'],
                json.dumps(hand_data.get('breakdown', {})),
                hand_data.get('breakdown', {}).get('honors_bonus', 0),
                session.ns_score,
                session.ew_score,
                json.dumps(hand_data.get('deal_data', {})),
                json.dumps(hand_data.get('auction_history', [])),
                json.dumps(hand_data.get('play_history', [])),
                session.player_position,
                hand_data.get('user_was_declarer', False),
                hand_data.get('user_was_dummy', False),
                hand_data.get('hand_duration_seconds', 0),
                dds_analysis_json,
                par_score,
                par_contract,
                dd_tricks
            ))
        else:
            # Fallback for databases without DDS columns
            cursor.execute("""
                INSERT INTO session_hands
                (session_id, hand_number, dealer, vulnerability,
                 contract_level, contract_strain, contract_declarer, contract_doubled,
                 tricks_taken, tricks_needed, made,
                 hand_score, score_breakdown, honors_bonus,
                 ns_total_after, ew_total_after,
                 deal_data, auction_history, play_history,
                 user_played_position, user_was_declarer, user_was_dummy,
                 hand_duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id,
                hand_data['hand_number'],
                hand_data['dealer'],
                hand_data['vulnerability'],
                contract.level if contract else None,
                contract.strain if contract else None,
                contract.declarer if contract else None,
                contract.doubled if contract else 0,
                hand_data.get('tricks_taken'),
                contract.tricks_needed if contract else None,
                hand_data.get('made', False),
                hand_data['hand_score'],
                json.dumps(hand_data.get('breakdown', {})),
                hand_data.get('breakdown', {}).get('honors_bonus', 0),
                session.ns_score,
                session.ew_score,
                json.dumps(hand_data.get('deal_data', {})),
                json.dumps(hand_data.get('auction_history', [])),
                json.dumps(hand_data.get('play_history', [])),
                session.player_position,
                hand_data.get('user_was_declarer', False),
                hand_data.get('user_was_dummy', False),
                hand_data.get('hand_duration_seconds', 0)
            ))

        # Update session
        cursor.execute("""
            UPDATE game_sessions
            SET hands_completed = ?,
                current_hand_number = ?,
                ns_score = ?,
                ew_score = ?,
                status = ?,
                completed_at = CASE WHEN ? = 'completed'
                    THEN CURRENT_TIMESTAMP ELSE completed_at END
            WHERE id = ?
        """, (
            session.hands_completed,
            session.current_hand_number,
            session.ns_score,
            session.ew_score,
            session.status,
            session.status,
            session.id
        ))

        conn.commit()
        conn.close()

    def _perform_dds_analysis(self, deal_data: Dict, dealer: str,
                              vulnerability: str, contract: Contract) -> Optional[Dict]:
        """
        Perform DDS analysis on a completed hand.

        Args:
            deal_data: Dictionary with hand data for all 4 positions
            dealer: Dealer position ('N', 'E', 'S', 'W')
            vulnerability: Vulnerability string ('None', 'NS', 'EW', 'Both')
            contract: Contract object with level, strain, declarer

        Returns:
            Dictionary with analysis_json, par_score, par_contract, dd_tricks
            or None if analysis fails
        """
        if not DDS_ENABLED or get_dds_service is None:
            return None

        try:
            dds_service = get_dds_service()
            if dds_service is None:
                return None

            # Convert deal_data to PBN format for DDS
            # deal_data format: {'North': Hand, 'East': Hand, 'South': Hand, 'West': Hand}
            # or {'North': {'spades': [...], ...}, ...}

            # Build hands in PBN format
            hands_pbn = []
            for pos in ['N', 'E', 'S', 'W']:
                pos_name = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}[pos]
                hand_data = deal_data.get(pos_name, deal_data.get(pos))

                if hand_data is None:
                    logger.warning(f"Missing hand data for {pos_name}")
                    return None

                # Handle different hand data formats
                if hasattr(hand_data, 'cards'):
                    # Hand object
                    suits = {'S': [], 'H': [], 'D': [], 'C': []}
                    for card in hand_data.cards:
                        suits[card.suit].append(card.rank)
                elif isinstance(hand_data, dict):
                    # Dictionary format {'spades': [...], 'hearts': [...], ...}
                    suit_map = {'spades': 'S', 'hearts': 'H', 'diamonds': 'D', 'clubs': 'C'}
                    suits = {'S': [], 'H': [], 'D': [], 'C': []}
                    for suit_name, suit_letter in suit_map.items():
                        cards = hand_data.get(suit_name, [])
                        suits[suit_letter] = [c if isinstance(c, str) else str(c) for c in cards]
                else:
                    logger.warning(f"Unknown hand data format for {pos_name}")
                    return None

                # Convert to PBN format (SHDC order)
                hand_pbn = '.'.join([
                    ''.join(suits['S']),
                    ''.join(suits['H']),
                    ''.join(suits['D']),
                    ''.join(suits['C'])
                ])
                hands_pbn.append(hand_pbn)

            # Full PBN deal string: "N:spades.hearts.diamonds.clubs spades.hearts..."
            deal_pbn = f"N:{' '.join(hands_pbn)}"

            # Perform full analysis
            analysis = dds_service.analyze_deal(deal_pbn, dealer, vulnerability)

            if analysis is None:
                return None

            # Get DD tricks for the actual contract played
            dd_tricks = None
            if analysis.dd_table and contract:
                declarer = contract.declarer
                strain = contract.strain
                # DD table is indexed by declarer and strain
                strain_map = {'C': 0, 'D': 1, 'H': 2, 'S': 3, 'NT': 4}
                declarer_map = {'N': 0, 'E': 1, 'S': 2, 'W': 3}

                strain_idx = strain_map.get(strain)
                declarer_idx = declarer_map.get(declarer)

                if strain_idx is not None and declarer_idx is not None:
                    dd_tricks = analysis.dd_table.tricks[declarer_idx][strain_idx]

            return {
                'analysis_json': json.dumps(analysis.to_dict()) if hasattr(analysis, 'to_dict') else None,
                'par_score': analysis.par_result.score if analysis.par_result else None,
                'par_contract': analysis.par_result.contract if analysis.par_result else None,
                'dd_tricks': dd_tricks
            }

        except Exception as e:
            logger.warning(f"DDS analysis failed: {e}")
            return None

    def get_session_hands(self, session_id: int) -> List[Dict]:
        """Get all hands for a session"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM v_hand_history
            WHERE session_id = ?
            ORDER BY hand_number
        """, (session_id,))

        hands = []
        for row in cursor.fetchall():
            hands.append(dict(row))

        conn.close()
        return hands

    def get_user_session_stats(self, user_id: int) -> Dict:
        """Get user's overall session statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM v_user_session_stats
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else {}

    def abandon_session(self, session_id: int) -> None:
        """Mark session as abandoned"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE game_sessions
            SET status = 'abandoned',
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session_id,))

        conn.commit()
        conn.close()
