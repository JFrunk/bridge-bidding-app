"""
Abstract base class for all card play AI implementations

This defines the interface that all AI strategies must implement,
ensuring consistency and enabling easy testing and comparison.
"""

from abc import ABC, abstractmethod
from engine.play_engine import PlayState, Card
from typing import Optional


class BasePlayAI(ABC):
    """
    Abstract base class for Bridge card play AI

    All AI implementations (Simple, Minimax, DDS, etc.) must extend this
    class and implement the required methods. This ensures a consistent
    interface across all AI strategies.

    Example:
        >>> class MyAI(BasePlayAI):
        ...     def choose_card(self, state, position):
        ...         return state.hands[position].cards[0]  # First card
        ...     def get_name(self):
        ...         return "My Simple AI"
        ...     def get_difficulty(self):
        ...         return "beginner"
    """

    @abstractmethod
    def choose_card(self, state: PlayState, position: str) -> Card:
        """
        Choose which card to play from given position

        This is the main method that PlayEngine calls to get the AI's
        card choice. The AI should analyze the current state and return
        the best card to play.

        Args:
            state: Current play state (includes contract, hands, tricks, etc.)
            position: Position making the play ('N', 'E', 'S', 'W')

        Returns:
            Card to play (must be legal according to Bridge rules)

        Raises:
            ValueError: If no legal card can be found (shouldn't happen)

        Example:
            >>> ai = SimplePlayAI()
            >>> card = ai.choose_card(play_state, 'N')
            >>> print(f"AI chose {card.rank}{card.suit}")
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Return human-readable name of this AI

        Used for display in UI and logging.

        Returns:
            Name string (e.g., "Simple AI", "Minimax AI (depth 3)")

        Example:
            >>> ai.get_name()
            'Minimax AI (depth 3)'
        """
        pass

    @abstractmethod
    def get_difficulty(self) -> str:
        """
        Return difficulty level of this AI

        Used for UI display and user selection.

        Returns:
            One of: 'beginner', 'intermediate', 'advanced', 'expert'

        Example:
            >>> ai.get_difficulty()
            'intermediate'
        """
        pass

    def get_explanation(self, card: Card, state: PlayState, position: str) -> str:
        """
        Provide explanation for why this card was chosen

        This is optional - override to provide detailed explanations
        for educational purposes. Default implementation returns basic info.

        Args:
            card: The card that was played
            state: The state when card was chosen
            position: Position that played the card

        Returns:
            Human-readable explanation string

        Example:
            >>> explanation = ai.get_explanation(card, state, 'N')
            >>> print(explanation)
            'Played A♠ to draw trumps'
        """
        return f"Played {card.rank}{card.suit}"

    def get_statistics(self) -> dict:
        """
        Return AI statistics (optional)

        Override to provide performance metrics like nodes searched,
        time taken, cache hits, etc.

        Returns:
            Dictionary of statistics

        Example:
            >>> stats = ai.get_statistics()
            >>> print(f"Searched {stats['nodes']} nodes")
        """
        return {}

    def reset_statistics(self):
        """
        Reset AI statistics (optional)

        Override if your AI tracks statistics that should be reset
        between games or for benchmarking.
        """
        pass

    def __str__(self) -> str:
        """String representation"""
        return f"{self.get_name()} ({self.get_difficulty()})"

    def __repr__(self) -> str:
        """Developer representation"""
        return f"<{self.__class__.__name__}: {self.get_name()}>"
