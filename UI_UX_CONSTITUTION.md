# My Bridge Buddy: UI/UX Constitution (Clubhouse Theme)

You are an expert Frontend Engineer. You must strictly adhere to the existing visual brand and logical structure of the application.

## 1. Visual Identity (Immutable)
- **Primary Canvas:** `#FDFBF7` (Beige/Cream). Use for all background containers.
- **Game Surface:** `#1B4D3E` (Deep Green). Use for the card table and primary headers.
- **Accent Gold:** `#EAB308`. Use for "Your Turn" toasts and primary action highlights.

## 2. Card Physics & Orientation
- **Global Rule:** North, South, East, and West hands MUST render in **Vertical Portrait** orientation.
- **Visibility:** Every card face must clearly display the **Rank** and **Suit** symbol.
- **Forbidden:** Never collapse cards into "horizontal edges" or "stacked fanned" views that hide the rank.

## 3. Typography & Contrast Logic
- **Suit Consistency:**
    - Hearts (♥) and Diamonds (♦) MUST be `text-red-600`.
    - Spades (♠), Clubs (♣), and No Trump (NT) MUST be `text-gray-900`.
- **The "Bid Chip" Rule:** In the Bidding History or on dark green surfaces, wrap every bid in a white rounded pill (`bg-white rounded px-2 py-0.5 shadow-sm`) to ensure the Red/Black suit colors are legible.
- **Normalization:** Use `items-center` on all header strips to prevent "ransom note" typography (jumping baselines).

## 4. Layout Constraints
- **South Hand:** Must be pinned to the bottom of the viewport with a fixed height (e.g., `h-64`) to prevent clipping.
- **Toasts:** Move all "Your Turn" or system alerts to `top-20` (below header) or `bottom-32` (above hand) to avoid obscuring the central trick area.
- **Affordances:** Buttons like "Last Trick" or "Claim" must have clear text labels; do not use empty dark rectangles.
