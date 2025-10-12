"""
Contract utilities for parsing and manipulating bridge contracts

This module provides utilities for working with contracts independently
of the bidding phase, enabling standalone play testing and development.
"""

from engine.play_engine import Contract
from typing import Optional
import re


def parse_contract(contract_str: str) -> Contract:
    """
    Parse a contract string into a Contract object

    Supports formats:
    - "3NT by S"
    - "4♠ by N"
    - "6♣X by E" (doubled)
    - "7♥XX by W" (redoubled)

    Args:
        contract_str: String representation of contract

    Returns:
        Contract object

    Raises:
        ValueError: If contract string is invalid

    Examples:
        >>> parse_contract("3NT by S")
        Contract(level=3, strain='NT', declarer='S', doubled=0)

        >>> parse_contract("4♠X by N")
        Contract(level=4, strain='♠', declarer='N', doubled=1)

        >>> parse_contract("7♥XX by W")
        Contract(level=7, strain='♥', declarer='W', doubled=2)
    """
    # Remove extra whitespace
    contract_str = contract_str.strip()

    # Pattern: <level><strain>[X|XX] by <declarer>
    # Level: 1-7
    # Strain: ♣, ♦, ♥, ♠, or NT
    # Doubled: optional X or XX
    # Declarer: N, E, S, W

    pattern = r'^([1-7])(♣|♦|♥|♠|NT)(X{0,2})\s+by\s+([NESW])$'
    match = re.match(pattern, contract_str, re.IGNORECASE)

    if not match:
        raise ValueError(
            f"Invalid contract string: '{contract_str}'. "
            "Expected format: '<level><strain>[X|XX] by <declarer>' "
            "(e.g., '3NT by S', '4♠X by N')"
        )

    level_str, strain, double_str, declarer = match.groups()

    level = int(level_str)
    declarer = declarer.upper()

    # Determine doubled status
    if double_str == '':
        doubled = 0
    elif double_str.upper() == 'X':
        doubled = 1
    elif double_str.upper() == 'XX':
        doubled = 2
    else:
        doubled = 0

    return Contract(
        level=level,
        strain=strain,
        declarer=declarer,
        doubled=doubled
    )


def contract_to_string(contract: Contract) -> str:
    """
    Convert a Contract object to a readable string

    Args:
        contract: Contract object

    Returns:
        String representation

    Example:
        >>> contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        >>> contract_to_string(contract)
        '3NT by S'
    """
    double_str = '' if contract.doubled == 0 else 'X' if contract.doubled == 1 else 'XX'
    return f"{contract.level}{contract.strain}{double_str} by {contract.declarer}"


def parse_vulnerability(vuln_str: str) -> dict:
    """
    Parse vulnerability string into vulnerability dictionary

    Args:
        vuln_str: One of "None", "NS", "EW", "Both"

    Returns:
        Dictionary with 'ns' and 'ew' boolean keys

    Examples:
        >>> parse_vulnerability("None")
        {'ns': False, 'ew': False}

        >>> parse_vulnerability("NS")
        {'ns': True, 'ew': False}

        >>> parse_vulnerability("Both")
        {'ns': True, 'ew': True}
    """
    vuln_map = {
        'None': {'ns': False, 'ew': False},
        'NS': {'ns': True, 'ew': False},
        'EW': {'ns': False, 'ew': True},
        'Both': {'ns': True, 'ew': True}
    }

    vuln_str = vuln_str.strip()
    if vuln_str not in vuln_map:
        raise ValueError(
            f"Invalid vulnerability: '{vuln_str}'. "
            "Expected one of: None, NS, EW, Both"
        )

    return vuln_map[vuln_str]


def vulnerability_to_string(vulnerability: dict) -> str:
    """
    Convert vulnerability dict to string

    Args:
        vulnerability: Dictionary with 'ns' and 'ew' keys

    Returns:
        String representation ("None", "NS", "EW", or "Both")

    Example:
        >>> vulnerability_to_string({'ns': True, 'ew': False})
        'NS'
    """
    ns_vuln = vulnerability.get('ns', False)
    ew_vuln = vulnerability.get('ew', False)

    if ns_vuln and ew_vuln:
        return 'Both'
    elif ns_vuln:
        return 'NS'
    elif ew_vuln:
        return 'EW'
    else:
        return 'None'


if __name__ == '__main__':
    # Self-test
    print("Testing contract parser...")

    test_cases = [
        ("3NT by S", Contract(3, 'NT', 'S', 0)),
        ("4♠ by N", Contract(4, '♠', 'N', 0)),
        ("6♣X by E", Contract(6, '♣', 'E', 1)),
        ("7♥XX by W", Contract(7, '♥', 'W', 2)),
    ]

    for test_str, expected in test_cases:
        result = parse_contract(test_str)
        assert result == expected, f"Failed: {test_str}"
        print(f"✓ {test_str} -> {result}")

    print("\nTesting vulnerability parser...")
    vuln_tests = [
        ("None", {'ns': False, 'ew': False}),
        ("NS", {'ns': True, 'ew': False}),
        ("EW", {'ns': False, 'ew': True}),
        ("Both", {'ns': True, 'ew': True}),
    ]

    for test_str, expected in vuln_tests:
        result = parse_vulnerability(test_str)
        assert result == expected, f"Failed: {test_str}"
        print(f"✓ {test_str} -> {result}")

    print("\nAll tests passed! ✓")
