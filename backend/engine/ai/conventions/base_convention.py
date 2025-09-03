from engine.hand import Hand
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict

class ConventionModule(ABC):
    """Base class for all bidding conventions."""
    
    @abstractmethod
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Return (bid, explanation) or None if convention doesn't apply."""
        pass

    def get_constraints(self) -> Dict:
        """
        Return a dictionary of constraints for the hand constructor.
        This is optional for conventions that don't need hand generation.
        """
        return {}