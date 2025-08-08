def get_transfer_completion_bid(partner_transfer_bid: str):
    if partner_transfer_bid == "2♦":
        return ("2♥", "Completing the transfer to Hearts.")
    if partner_transfer_bid == "2♥":
        return ("2♠", "Completing the transfer to Spades.")
    return ("Pass", "Error: Logic fall-through in transfer completion.")