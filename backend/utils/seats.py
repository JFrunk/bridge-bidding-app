"""
Seat utilities for bridge position calculations.

This module provides a single source of truth for all seat-related
calculations across the application. Use these functions instead of
inline seat math to ensure consistency.

Seat Mapping:
    NORTH = 0, EAST = 1, SOUTH = 2, WEST = 3

The modulo-4 clock:
    - Partner is always +2 (opposite)
    - LHO (Left Hand Opponent) is always +1 (clockwise)
    - RHO (Right Hand Opponent) is always +3 (or -1)

Usage:
    from utils.seats import partner, lho, rho, relative_position

    # Get partner of South
    partner('S')  # Returns 'N'

    # Get display name relative to user
    display_name('E', hero='S')  # Returns 'LHO'

    # Check if two seats are partners
    is_partner('N', 'S')  # Returns True
"""

from typing import Optional, Set, Literal

# === CONSTANTS ===

# Integer indices (for modulo arithmetic)
NORTH: int = 0
EAST: int = 1
SOUTH: int = 2
WEST: int = 3

# Partnerships
NS: int = 0  # North-South
EW: int = 1  # East-West

# String representations
SEATS: list[str] = ['N', 'E', 'S', 'W']
SEAT_NAMES: dict[str, str] = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
RELATIVE_NAMES: list[str] = ['You', 'LHO', 'Partner', 'RHO']

# Partnership sets
NS_SIDE: Set[str] = {'N', 'S'}
EW_SIDE: Set[str] = {'E', 'W'}

# Direct lookup maps (for performance when not using indices)
PARTNERS: dict[str, str] = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
NEXT_PLAYER: dict[str, str] = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}  # LHO / clockwise
PREV_PLAYER: dict[str, str] = {'N': 'W', 'E': 'N', 'S': 'E', 'W': 'S'}  # RHO / counter-clockwise


# === TYPE ALIASES ===

SeatStr = Literal['N', 'E', 'S', 'W']
SeatFull = Literal['North', 'East', 'South', 'West']


# === NORMALIZATION ===

def normalize(position: Optional[str]) -> str:
    """
    Normalize a position to single-letter format.

    Args:
        position: Position string ('North', 'N', 'north', etc.)

    Returns:
        Single letter format ('N', 'E', 'S', 'W')

    Examples:
        normalize('North') -> 'N'
        normalize('s') -> 'S'
        normalize(None) -> 'N'
    """
    if not position:
        return 'N'  # Default

    pos = str(position).strip()

    # Already single letter
    if pos.upper() in SEATS:
        return pos.upper()

    # Full name
    full_map = {'NORTH': 'N', 'EAST': 'E', 'SOUTH': 'S', 'WEST': 'W'}
    return full_map.get(pos.upper(), 'N')


def seat_index(seat: str) -> int:
    """
    Convert seat string to index (0-3).

    Args:
        seat: Seat string ('N', 'E', 'S', 'W' or full name)

    Returns:
        Integer index (0=N, 1=E, 2=S, 3=W)
    """
    return SEATS.index(normalize(seat))


def seat_from_index(index: int) -> str:
    """
    Convert index to seat string.

    Args:
        index: Integer index (0-3, will be wrapped with modulo)

    Returns:
        Seat string ('N', 'E', 'S', 'W')
    """
    return SEATS[index % 4]


# === RELATIONSHIP FUNCTIONS ===

def partner(seat: str) -> str:
    """
    Get the partner of a seat.

    Args:
        seat: Seat string

    Returns:
        Partner's seat string

    Example:
        partner('S') -> 'N'
        partner('E') -> 'W'
    """
    s = normalize(seat)
    return PARTNERS[s]


def lho(seat: str) -> str:
    """
    Get the Left Hand Opponent (next player clockwise).

    Args:
        seat: Seat string

    Returns:
        LHO's seat string

    Example:
        lho('S') -> 'W'
        lho('N') -> 'E'
    """
    s = normalize(seat)
    return NEXT_PLAYER[s]


def rho(seat: str) -> str:
    """
    Get the Right Hand Opponent (previous player clockwise).

    Args:
        seat: Seat string

    Returns:
        RHO's seat string

    Example:
        rho('S') -> 'E'
        rho('N') -> 'W'
    """
    s = normalize(seat)
    return PREV_PLAYER[s]


def partnership(seat: str) -> int:
    """
    Get the partnership of a seat.

    Args:
        seat: Seat string

    Returns:
        Partnership index (0=NS, 1=EW)
    """
    return seat_index(seat) % 2


def partnership_str(seat: str) -> str:
    """
    Get the partnership name of a seat.

    Args:
        seat: Seat string

    Returns:
        Partnership string ('NS' or 'EW')
    """
    return 'NS' if partnership(seat) == NS else 'EW'


def is_partner(seat1: str, seat2: str) -> bool:
    """
    Check if two seats are partners.

    Args:
        seat1: First seat string
        seat2: Second seat string

    Returns:
        True if seats are partners
    """
    return partner(seat1) == normalize(seat2)


def is_opponent(seat1: str, seat2: str) -> bool:
    """
    Check if two seats are opponents.

    Args:
        seat1: First seat string
        seat2: Second seat string

    Returns:
        True if seats are opponents
    """
    return partnership(seat1) != partnership(seat2)


def same_side(seat1: str, seat2: str) -> bool:
    """
    Check if two seats are on the same side (partners).

    Args:
        seat1: First seat string
        seat2: Second seat string

    Returns:
        True if seats are on the same partnership
    """
    return partnership(seat1) == partnership(seat2)


# === RELATIVE POSITION ===

def relative_position(target: str, hero: str) -> int:
    """
    Get the relative position of target from hero's perspective.

    Uses modulo-4 clock arithmetic:
        0 = Self
        1 = LHO (Left Hand Opponent)
        2 = Partner
        3 = RHO (Right Hand Opponent)

    Args:
        target: Target seat string
        hero: Hero/user seat string

    Returns:
        Relative position index (0-3)

    Example:
        relative_position('W', 'S') -> 1 (LHO)
        relative_position('N', 'S') -> 2 (Partner)
        relative_position('E', 'S') -> 3 (RHO)
    """
    return (seat_index(target) - seat_index(hero)) % 4


def display_name(seat: str, hero: str = 'S', relative: bool = True) -> str:
    """
    Get a display name for a seat.

    Args:
        seat: Target seat string
        hero: Hero/user seat string (default 'S')
        relative: If True, return relative name ('Partner');
                  if False, return absolute name ('North')

    Returns:
        Display name string

    Example:
        display_name('N', hero='S') -> 'Partner'
        display_name('N', hero='S', relative=False) -> 'North'
        display_name('E', hero='S') -> 'RHO'
    """
    s = normalize(seat)
    if relative:
        rel = relative_position(s, hero)
        return RELATIVE_NAMES[rel]
    return SEAT_NAMES[s]


def bidder_role(bidder: str, user: str) -> str:
    """
    Get the role description for a bidder relative to the user.

    Args:
        bidder: Bidder's seat string
        user: User's seat string

    Returns:
        Role string with seat name, e.g., 'North (Partner)'

    Example:
        bidder_role('N', 'S') -> 'North (Partner)'
        bidder_role('E', 'S') -> 'East (Opponent)'
        bidder_role('S', 'S') -> 'South (You)'
    """
    b = normalize(bidder)
    u = normalize(user)

    rel = relative_position(b, u)
    seat_name = SEAT_NAMES[b]

    if rel == 0:
        return f"{seat_name} (You)"
    elif rel == 2:
        return f"{seat_name} (Partner)"
    else:
        return f"{seat_name} (Opponent)"


# === PLAY PHASE HELPERS ===

def dummy(declarer: str) -> str:
    """
    Get the dummy seat given the declarer.

    Args:
        declarer: Declarer's seat string

    Returns:
        Dummy's seat string (declarer's partner)
    """
    return partner(declarer)


def opening_leader(declarer: str) -> str:
    """
    Get the opening leader seat given the declarer.

    Args:
        declarer: Declarer's seat string

    Returns:
        Opening leader's seat string (LHO of declarer)
    """
    return lho(declarer)


def is_declaring_side(seat: str, declarer: str) -> bool:
    """
    Check if a seat is on the declaring side.

    Args:
        seat: Seat to check
        declarer: Declarer's seat string

    Returns:
        True if seat is declarer or dummy
    """
    return same_side(seat, declarer)


def is_defending_side(seat: str, declarer: str) -> bool:
    """
    Check if a seat is on the defending side.

    Args:
        seat: Seat to check
        declarer: Declarer's seat string

    Returns:
        True if seat is a defender
    """
    return not is_declaring_side(seat, declarer)


# === BIDDING PHASE HELPERS ===

def active_seat_bidding(dealer: str, bid_count: int) -> str:
    """
    Get the active seat during bidding.

    Args:
        dealer: Dealer's seat string
        bid_count: Number of bids made so far

    Returns:
        Active seat string
    """
    dealer_idx = seat_index(dealer)
    return seat_from_index(dealer_idx + bid_count)


def active_seat_play(trick_leader: str, cards_played: int) -> str:
    """
    Get the active seat during play.

    Args:
        trick_leader: Trick leader's seat string
        cards_played: Number of cards played in current trick (0-3)

    Returns:
        Active seat string
    """
    leader_idx = seat_index(trick_leader)
    return seat_from_index(leader_idx + cards_played)
