import random
from dataclasses import dataclass, field
from typing import List

from utils import OUT_FORMAT

RANKS = {1: 'A', 2: '2', 3: '3', 4: '4', 5: '5',
         6: '6', 7: '7', 8: 'J', 9: 'Q', 10: 'K'}
SUITS = {'P': '♠', 'F': '♣', 'D': '♢', 'C': '♡'} if OUT_FORMAT == 'html' else {
    'P': '🔺', 'F': '🍁', 'D': '🔶', 'C': '🧡'}


@dataclass
class Card:
    rank: int
    suit: str

    def __repr__(self):
        return f"{RANKS[self.rank]}{SUITS[self.suit]}"

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __lt__(self, other):
        _SUITS = list(SUITS.keys())
        return (
            self.rank < other.rank or
            (self.rank == other.rank and _SUITS.index(
                self.suit) < _SUITS.index(other.suit))
        )

    def __hash__(self):
        return hash(self.__repr__())


def make_cards():
    return [Card(rank, suit) for suit in SUITS for rank in RANKS]


@dataclass
class Deck:
    cards: List[Card] = field(default_factory=make_cards)

    def __len__(self):
        return len(self.cards)

    def __getitem__(self, position):
        return self.cards[position]

    def shuffle(self):
        random.shuffle(self.cards)
