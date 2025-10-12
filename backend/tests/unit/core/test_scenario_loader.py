"""
Unit tests for ScenarioLoader.

Tests loading and validating bidding and play scenarios.
"""

import pytest
import json
import tempfile
from pathlib import Path
from core.scenario_loader import ScenarioLoader


class TestScenarioLoader:
    """Test ScenarioLoader functionality."""

    def test_load_bidding_scenarios_old_format(self):
        """Test loading bidding scenarios from old format (scenarios.json)."""
        loader = ScenarioLoader()
        scenarios = loader.load_bidding_scenarios()

        # Should load from existing scenarios.json
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0
        assert all('name' in s for s in scenarios)

    def test_get_scenario_by_name(self):
        """Test retrieving scenario by name."""
        loader = ScenarioLoader()
        scenario = loader.get_scenario_by_name('bidding', 'Stayman Test')

        if scenario:  # May not exist in test environment
            assert scenario['name'] == 'Stayman Test'
            assert 'setup' in scenario

    def test_get_nonexistent_scenario(self):
        """Test retrieving non-existent scenario returns None."""
        loader = ScenarioLoader()
        scenario = loader.get_scenario_by_id('bidding', 'nonexistent_scenario')
        assert scenario is None

    def test_validate_bidding_scenario_valid(self):
        """Test validating a valid bidding scenario."""
        loader = ScenarioLoader()

        valid_scenario = {
            'name': 'Test Scenario',
            'description': 'A test scenario',
            'setup': [
                {'position': 'North', 'constraints': {'hcp_range': [15, 17]}}
            ]
        }

        assert loader.validate_bidding_scenario(valid_scenario) is True

    def test_validate_bidding_scenario_missing_name(self):
        """Test validating scenario without name."""
        loader = ScenarioLoader()

        invalid_scenario = {
            'setup': []
        }

        assert loader.validate_bidding_scenario(invalid_scenario) is False

    def test_validate_bidding_scenario_missing_setup(self):
        """Test validating scenario without setup."""
        loader = ScenarioLoader()

        invalid_scenario = {
            'name': 'Test'
        }

        assert loader.validate_bidding_scenario(invalid_scenario) is False

    def test_validate_play_scenario_valid(self):
        """Test validating a valid play scenario."""
        loader = ScenarioLoader()

        valid_scenario = {
            'id': 'test_scenario',
            'name': 'Test Play Scenario',
            'contract': {
                'level': 3,
                'strain': 'NT',
                'declarer': 'S'
            },
            'hands': {
                'N': ['AK3', 'Q54', 'AK3', '9876'],
                'E': ['J987', 'J98', 'Q876', '43'],
                'S': ['Q64', 'AK3', '543', 'AKQJ'],
                'W': ['T52', 'T762', 'JT92', 'T52']
            }
        }

        assert loader.validate_play_scenario(valid_scenario) is True

    def test_validate_play_scenario_missing_contract(self):
        """Test validating play scenario without contract."""
        loader = ScenarioLoader()

        invalid_scenario = {
            'id': 'test',
            'hands': {'N': [], 'E': [], 'S': [], 'W': []}
        }

        assert loader.validate_play_scenario(invalid_scenario) is False

    def test_validate_play_scenario_incomplete_contract(self):
        """Test validating play scenario with incomplete contract."""
        loader = ScenarioLoader()

        invalid_scenario = {
            'id': 'test',
            'contract': {
                'level': 3
                # Missing strain and declarer
            },
            'hands': {'N': [], 'E': [], 'S': [], 'W': []}
        }

        assert loader.validate_play_scenario(invalid_scenario) is False

    def test_validate_play_scenario_missing_hands(self):
        """Test validating play scenario without hands."""
        loader = ScenarioLoader()

        invalid_scenario = {
            'id': 'test',
            'contract': {
                'level': 3,
                'strain': 'NT',
                'declarer': 'S'
            }
        }

        assert loader.validate_play_scenario(invalid_scenario) is False

    def test_validate_play_scenario_incomplete_hands(self):
        """Test validating play scenario with incomplete hands."""
        loader = ScenarioLoader()

        invalid_scenario = {
            'id': 'test',
            'contract': {
                'level': 3,
                'strain': 'NT',
                'declarer': 'S'
            },
            'hands': {
                'N': [],
                'S': []
                # Missing E and W
            }
        }

        assert loader.validate_play_scenario(invalid_scenario) is False

    def test_get_scenario_count_bidding(self):
        """Test getting count of bidding scenarios."""
        loader = ScenarioLoader()
        count = loader.get_scenario_count('bidding')

        assert isinstance(count, int)
        assert count >= 0

    def test_get_scenario_count_play(self):
        """Test getting count of play scenarios."""
        loader = ScenarioLoader()
        count = loader.get_scenario_count('play')

        assert isinstance(count, int)
        # May be 0 if play_scenarios.json doesn't exist yet

    def test_load_play_scenarios_list_format(self):
        """Test loading play scenarios from list format."""
        # Create temporary scenarios file
        with tempfile.TemporaryDirectory() as tmpdir:
            scenarios_dir = Path(tmpdir)
            play_file = scenarios_dir / "play_scenarios.json"

            scenarios_data = [
                {
                    'id': 'test1',
                    'name': 'Test 1',
                    'contract': {'level': 3, 'strain': 'NT', 'declarer': 'S'},
                    'hands': {'N': [], 'E': [], 'S': [], 'W': []}
                }
            ]

            with open(play_file, 'w') as f:
                json.dump(scenarios_data, f)

            loader = ScenarioLoader(scenarios_dir=str(scenarios_dir))
            scenarios = loader.load_play_scenarios()

            assert len(scenarios) == 1
            assert scenarios[0]['id'] == 'test1'

    def test_load_play_scenarios_dict_format(self):
        """Test loading play scenarios from dict format with 'scenarios' key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenarios_dir = Path(tmpdir)
            play_file = scenarios_dir / "play_scenarios.json"

            scenarios_data = {
                'scenarios': [
                    {
                        'id': 'test1',
                        'name': 'Test 1',
                        'contract': {'level': 3, 'strain': 'NT', 'declarer': 'S'},
                        'hands': {'N': [], 'E': [], 'S': [], 'W': []}
                    }
                ]
            }

            with open(play_file, 'w') as f:
                json.dump(scenarios_data, f)

            loader = ScenarioLoader(scenarios_dir=str(scenarios_dir))
            scenarios = loader.load_play_scenarios()

            assert len(scenarios) == 1
            assert scenarios[0]['id'] == 'test1'

    def test_get_scenario_by_id_or_name(self):
        """Test that get_scenario_by_id works with both id and name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenarios_dir = Path(tmpdir)
            play_file = scenarios_dir / "play_scenarios.json"

            scenarios_data = [
                {
                    'id': 'test_id',
                    'name': 'Test Name',
                    'contract': {'level': 3, 'strain': 'NT', 'declarer': 'S'},
                    'hands': {'N': [], 'E': [], 'S': [], 'W': []}
                }
            ]

            with open(play_file, 'w') as f:
                json.dump(scenarios_data, f)

            loader = ScenarioLoader(scenarios_dir=str(scenarios_dir))

            # Should find by id
            scenario_by_id = loader.get_scenario_by_id('play', 'test_id')
            assert scenario_by_id is not None
            assert scenario_by_id['id'] == 'test_id'

            # Should find by name
            scenario_by_name = loader.get_scenario_by_id('play', 'Test Name')
            assert scenario_by_name is not None
            assert scenario_by_name['name'] == 'Test Name'


def test_get_scenario_loader_singleton():
    """Test singleton pattern for global scenario loader."""
    from core.scenario_loader import get_scenario_loader

    loader1 = get_scenario_loader()
    loader2 = get_scenario_loader()

    assert loader1 is loader2
