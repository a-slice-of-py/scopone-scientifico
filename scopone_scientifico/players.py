import itertools
import random

import pandas as pd
from IPython.display import HTML, display

from cards import SUITS, Card, make_cards
from utils import (CARTE_GOAL, DENARI_GOAL, MATCH_GOAL, OUT_FORMAT,
                   PRIMIERA_RULES, _compute_primiera, ibold, iemph, obold,
                   oemph)


class Player:

    def __init__(self, name: str, user: bool):
        self.name = name
        self.reset()
        self.user = user

    def reset(self):
        self.hand = []
        self.loot = []
        self.scope = 0

    def __repr__(self):
        return f"{self.name}"

    def get_options(self, table):
        return {
            combo: sum(card.rank for card in combo)
            for combo in filter(
                lambda x: 0 < sum(card.rank for card in x) and sum(
                    card.rank for card in x) <= 10,
                itertools.chain.from_iterable(itertools.combinations(
                    table, r) for r in range(len(table) + 1))
            )}

    def choose_card(self):
        random.shuffle(self.hand)
        return self.hand.pop()

    def play(self, table: list):
        _options = self.get_options(table)
        if self.user and len(self.hand) > 1:
            _hand = pd.Series(sorted(self.hand)).to_frame().transpose()
            hand = f"\n{_hand.to_markdown(index=False)}" if OUT_FORMAT == 'markdown' else _hand.to_html(
                index=False)
            msgs = [
                f"\nWaiting for {self.name}...",
                f"Table: {table}",
                f"Hand: {hand}"
            ]
            for msg in msgs:
                if OUT_FORMAT == 'html':
                    display(HTML(msg))
                elif OUT_FORMAT == 'markdown':
                    print(msg)

            idx = int(input('Enter chosen card index: '))
            chosen_card = sorted(self.hand)[idx]
            self.hand = list(set(self.hand).difference([chosen_card]))
        else:
            chosen_card = self.choose_card()
        options = {combo: value for combo,
                   value in _options.items() if value == chosen_card.rank}
        if options:
            # migliorare il criterio di scelta (se table = [2,3,5], giocando un 5 sono obbligato a prendere un 5...)
            loot = list(list(options.keys())[0])
            log = f"{self.name} prende {loot} da {table} giocando {chosen_card}."
            table = list(set(table) - set(loot))
            self.loot.extend(loot + [chosen_card])
            if not table:
                log += f" {ibold}SCOPA!{obold}"
                self.scope += 1
        else:
            log = f"{self.name} gioca {chosen_card}."
            table.append(chosen_card)
        return table, log

    def compute_primiera(self):
        others = _compute_primiera(
            list(set(make_cards()).difference(self.loot)))
        mine = _compute_primiera(self.loot)
        return (mine / others) / 4  # n players sharing attribution...

    def attribute_score(self):
        _scope = self.scope
        _carte = min(len(self.loot) / CARTE_GOAL, 1)
        _denari = min(
            len(list(filter(lambda card: card.suit == 'D', self.loot))) / DENARI_GOAL, 1)
        _settebello = int(Card(7, 'D') in self.loot)
        _primiera = min(self.compute_primiera(), 1)
        return sum((_scope, _carte, _denari, _settebello, _primiera)) / MATCH_GOAL


class Team:

    def __init__(self, name1: str, name2: str):
        user1, user2 = False, False
        if name1 is ...:
            name1 = input("Enter name for Player 1: ")
            user1 = True
        if name2 is ...:
            name2 = input("Enter name for Player 2: ")
            user2 = True
        self.players = [Player(name=name1, user=user1),
                        Player(name=name2, user=user2)]
        self.score = 0
        self.logs = []

    def reset(self):
        for player in self.players:
            player.reset()
        self.logs = []

    def __len__(self):
        return len(self.players)

    def __getitem__(self, position):
        return self.players[position]

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(player.__repr__() for player in self.players)})"

    def count_scope(self):
        scope = sum(player.scope for player in self.players)
        if scope:
            self.logs.append(f"+{scope} scope")
        return scope

    def compute_denari(self):
        denari = 0
        _denari = len(list(filter(lambda x: x.suit == 'D', self.loot)))
        if _denari >= 5:
            if _denari == 5:
                self.logs.append(f"Denari pari [{_denari}]")
            elif _denari < 10:
                denari = 1
                self.logs.append(f"+1 denari [{_denari}]")
            if _denari == 10:
                denari = 1 + 21
                self.logs.append(f"+1 denari [{_denari} -> CAPPOTTO!]")
        return denari

    def compute_settebello(self):
        settebello = 0
        if Card(7, 'D') in self.loot:
            settebello = 1
            self.logs.append("+1 settebello")
        return settebello

    def compute_carte(self):
        carte = 0
        if len(self.loot) > 20:
            carte = 1
            self.logs.append(f"+1 carte [{len(self.loot)}]")
        elif len(self.loot) == 20:
            self.logs.append(f"Carte pari [{len(self.loot)}]")
        return carte

    def compute_primiera(self):
        looted_suits = [
            list(filter(lambda x: x.suit == suit, self.loot)) for suit in SUITS]
        if not all(looted_suits):
            self.primiera = 0
        else:
            self.primiera = sum(PRIMIERA_RULES.get(max(
                suit, key=lambda x: PRIMIERA_RULES.get(x.rank)).rank) for suit in looted_suits)

    def compute_score(self):
        self.logs.append(f"{iemph}Punti {self.__repr__()}{oemph}")
        self.loot = self.players[0].loot + self.players[1].loot
        scope = self.count_scope()
        carte = self.compute_carte()
        denari = self.compute_denari()
        settebello = self.compute_settebello()
        _score = scope + carte + denari + settebello
        self.score += _score
        self.compute_primiera()
        return _score
