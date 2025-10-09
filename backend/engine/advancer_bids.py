from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class AdvancerBidsModule(ConventionModule):
    """Playbook for the partner of an overcaller (the Advancer)."""
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        partner_overcall = features['auction_features']['partner_last_bid']
        opener_bid = features['auction_features']['opening_bid']

        # Validate that partner actually made an overcall (not Pass, not opening)
        if not partner_overcall or partner_overcall == 'Pass':
            return None  # Not an advancing situation

        # Partner doubled for takeout - handle separately (could add logic later)
        if partner_overcall in ['X', 'XX']:
            return None  # Responding to doubles needs different logic

        # Partner bid NT - different logic needed
        if 'NT' in partner_overcall:
            return None  # NT overcalls need different response logic

        # Partner overcalled a suit - now we can advance
        if len(partner_overcall) < 2:
            return None  # Invalid bid format

        overcall_suit = partner_overcall[1]

        if hand.suit_lengths.get(overcall_suit, 0) >= 3 and hand.total_points >= 8:
            bid_level = str(int(partner_overcall[0]) + 1)
            return (f"{bid_level}{overcall_suit}", "Raising partner's overcalled suit with support.")

        if hand.total_points >= 12:
            cuebid_level = str(int(opener_bid[0]) + 1)
            return (f"{cuebid_level}{opener_bid[1]}", "Cuebid. Shows a very strong hand, likely game-forcing.")

        return ("Pass", "Not enough strength or fit to advance the overcall.")