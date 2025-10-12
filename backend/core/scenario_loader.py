"""
ScenarioLoader - Unified scenario loading for bidding and play scenarios.

Loads and validates scenarios from JSON files, supporting both bidding
practice scenarios and play practice scenarios.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class ScenarioLoader:
    """
    Load scenarios from JSON files.

    Supports:
    - Bidding scenarios (convention practice)
    - Play scenarios (declarer play practice)
    - Validation of scenario format

    Usage:
        loader = ScenarioLoader()
        scenarios = loader.load_bidding_scenarios()
        scenario = loader.get_scenario_by_id('bidding', 'stayman_test')
    """

    def __init__(self, scenarios_dir: str = "scenarios"):
        """
        Initialize scenario loader.

        Args:
            scenarios_dir: Directory containing scenario JSON files
        """
        self.scenarios_dir = Path(scenarios_dir)

    def load_bidding_scenarios(self) -> List[Dict]:
        """
        Load bidding practice scenarios.

        Returns:
            List of scenario dictionaries

        Format:
            [{
                "name": "Scenario Name",
                "description": "What this scenario teaches",
                "setup": [position configurations],
                ...
            }, ...]
        """
        # Check if new format exists
        new_format_path = self.scenarios_dir / "bidding_scenarios.json"
        if new_format_path.exists():
            return self._load_json_file(new_format_path)

        # Fall back to old format (scenarios.json in parent directory)
        old_format_path = Path("scenarios.json")
        if old_format_path.exists():
            return self._load_json_file(old_format_path)

        return []

    def load_play_scenarios(self) -> List[Dict]:
        """
        Load play practice scenarios.

        Returns:
            List of scenario dictionaries

        Format:
            [{
                "id": "scenario_id",
                "name": "Scenario Name",
                "description": "What this scenario teaches",
                "difficulty": "beginner|intermediate|advanced",
                "contract": {
                    "level": 3,
                    "strain": "NT",
                    "declarer": "S"
                },
                "hands": {
                    "N": ["suit distribution"],
                    "E": ["suit distribution"],
                    "S": ["suit distribution"],
                    "W": ["suit distribution"]
                },
                "vulnerability": "None|NS|EW|Both",
                "teaching_points": ["Point 1", "Point 2"]
            }, ...]
        """
        file_path = self.scenarios_dir / "play_scenarios.json"
        if not file_path.exists():
            return []

        data = self._load_json_file(file_path)

        # Handle both formats: list or dict with 'scenarios' key
        if isinstance(data, dict) and 'scenarios' in data:
            return data['scenarios']
        return data if isinstance(data, list) else []

    def get_scenario_by_id(
        self,
        scenario_type: str,
        scenario_id: str
    ) -> Optional[Dict]:
        """
        Get specific scenario by ID.

        Args:
            scenario_type: 'bidding' or 'play'
            scenario_id: Scenario identifier

        Returns:
            Scenario dict or None if not found
        """
        if scenario_type == 'bidding':
            scenarios = self.load_bidding_scenarios()
            # Bidding scenarios use 'name' as identifier
            for scenario in scenarios:
                if scenario.get('name') == scenario_id or \
                   scenario.get('id') == scenario_id:
                    return scenario
        elif scenario_type == 'play':
            scenarios = self.load_play_scenarios()
            # Play scenarios use 'id' as identifier
            for scenario in scenarios:
                if scenario.get('id') == scenario_id or \
                   scenario.get('name') == scenario_id:
                    return scenario

        return None

    def get_scenario_by_name(
        self,
        scenario_type: str,
        scenario_name: str
    ) -> Optional[Dict]:
        """
        Get specific scenario by name (for backward compatibility).

        Args:
            scenario_type: 'bidding' or 'play'
            scenario_name: Scenario name

        Returns:
            Scenario dict or None if not found
        """
        return self.get_scenario_by_id(scenario_type, scenario_name)

    def validate_play_scenario(self, scenario: Dict) -> bool:
        """
        Validate play scenario format.

        Args:
            scenario: Scenario dictionary

        Returns:
            True if valid, False otherwise

        Required fields:
            - id or name
            - contract (with level, strain, declarer)
            - hands (N, E, S, W)
        """
        # Check required fields
        if 'id' not in scenario and 'name' not in scenario:
            return False

        if 'contract' not in scenario:
            return False

        contract = scenario['contract']
        if not all(k in contract for k in ['level', 'strain', 'declarer']):
            return False

        if 'hands' not in scenario:
            return False

        hands = scenario['hands']
        if not all(pos in hands for pos in ['N', 'E', 'S', 'W']):
            return False

        return True

    def validate_bidding_scenario(self, scenario: Dict) -> bool:
        """
        Validate bidding scenario format.

        Args:
            scenario: Scenario dictionary

        Returns:
            True if valid, False otherwise

        Required fields:
            - name
            - setup (list of position configurations)
        """
        if 'name' not in scenario:
            return False

        if 'setup' not in scenario:
            return False

        if not isinstance(scenario['setup'], list):
            return False

        return True

    def _load_json_file(self, file_path: Path) -> List[Dict]:
        """
        Load JSON file and handle errors.

        Args:
            file_path: Path to JSON file

        Returns:
            List of scenarios or empty list on error
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Handle both formats
            if isinstance(data, dict) and 'scenarios' in data:
                return data['scenarios']
            return data if isinstance(data, list) else []

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading scenarios from {file_path}: {e}")
            return []

    def get_scenario_count(self, scenario_type: str) -> int:
        """
        Get count of scenarios by type.

        Args:
            scenario_type: 'bidding' or 'play'

        Returns:
            Number of scenarios
        """
        if scenario_type == 'bidding':
            return len(self.load_bidding_scenarios())
        elif scenario_type == 'play':
            return len(self.load_play_scenarios())
        return 0


# Global scenario loader instance
_scenario_loader = None


def get_scenario_loader(scenarios_dir: str = "scenarios") -> ScenarioLoader:
    """
    Get the global scenario loader instance (singleton pattern).

    Args:
        scenarios_dir: Directory containing scenario files

    Returns:
        ScenarioLoader instance
    """
    global _scenario_loader
    if _scenario_loader is None:
        _scenario_loader = ScenarioLoader(scenarios_dir)
    return _scenario_loader
