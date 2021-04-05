import random
import pandas as pd
import itertools
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from tqdm.notebook import tqdm
from IPython.display import HTML

RANKS = {1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: 'J', 9: 'Q', 10: 'K'}
SUITS = {'P': '♠', 'F': '♣', 'D': '♢', 'C': '♡'}
SEP = '<br>'

OUT_FORMAT = 'html'

if OUT_FORMAT == 'html':
    ibold = '<b>'
    iemph = '<i>'
    obold = '</b>'
    oemph = '</i>'
elif OUT_FORMAT == 'markdown':
    ibold = '**'
    iemph = '_'
    obold = ibold
    oemph = iemph


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
            (self.rank == other.rank and _SUITS.index(self.suit) < _SUITS.index(other.suit))
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

class Player:
    
    def __init__(self, name: str):        
        self.name = name
        self.reset()
        
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
                lambda x: 0 < sum(card.rank for card in x) and sum(card.rank for card in x) <= 10, 
                itertools.chain.from_iterable(itertools.combinations(table, r) for r in range(len(table) + 1))
            )}
    
    def choose_card(self):
        random.shuffle(self.hand)
        return self.hand.pop()        
        
    def play(self, table: list):        
        _options = self.get_options(table)
        chosen_card = self.choose_card()               
        options = {combo: value for combo, value in _options.items() if value == chosen_card.rank}
        if options:
            loot = list(list(options.keys())[0]) # migliorare il criterio di scelta (se table = [2,3,5], giocando un 5 sono obbligato a prendere un 5...)
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

class Team:
    
    def __init__(self, name1: str, name2: str):
        self.players = [Player(name1), Player(name2)]
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
                self.logs.append("Denari pari")
            elif _denari < 10:
                denari = 1
                self.logs.append("+1 denari")
            if _denari == 10:
                denari = 1 + 21
                self.logs.append("CAPPOTTO!")
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
            self.logs.append("+1 carte")
        elif len(self.loot) == 20:
            self.logs.append("Carte pari") 
        return carte        
    
    def compute_primiera(self):
        rules = {7: 21, 6: 18, 1: 16, 5: 15, 4: 14, 3: 13, 2: 12, 8: 10, 9: 10, 10: 10}
        looted_suits = [list(filter(lambda x: x.suit == suit, self.loot)) for suit in SUITS]
        if not all(looted_suits):
            self.primiera = 0
        else:
            self.primiera = sum(rules.get(max(suit, key=lambda x: rules.get(x.rank)).rank) for suit in looted_suits)
    
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

class Hand:
    
    def __init__(self, teams: Tuple[Team], rotation: list):
        self.teams = teams
        self.reset()
        self.rotation = rotation
    
    def reset(self):
        for team in self.teams:
            team.reset()
        self.players = list(player for team in self.teams for player in team)
        self.deck = Deck()
        self.table = []
        self.last_looter: Optional[Player] = None
        self.logs = []
        
    def distribute_cards(self):        
        cards = self.deck.cards
        for player in self.players:
            player.hand = sorted(random.sample(cards, int(len(self.deck.cards)/len(self.players))))
            cards = tuple(set(cards) - set(player.hand))
            
    def run(self):
        self.reset()
        self.distribute_cards()
        for n in range(len(self.players[0].hand)):
            self.logs.append(f"{iemph}Turno {n + 1}{oemph}") 
            for player in self.rotation:
                _table, log = player.play(self.table)
                self.logs.append(log)                
                if len(_table) < len(self.table):
                    self.last_looter_idx = self.players.index(player)
                self.table = _table
            self.logs.append('')
        if self.table:
            self.logs.append(f"{self.players[self.last_looter_idx]} pulisce il tavolo {self.table}.{SEP}")
            self.players[self.last_looter_idx].loot.extend(self.table)            
            self.table = []
        
        self.logs.append(f"{iemph}Prese{oemph}")
        for player in self.players:
            self.logs.append(f"{player.name} ➜ {player.loot}")
        self.logs.append('')

        scores = {team: team.compute_score() for team in self.teams}

        # assign primiera point via scores comparison
        if self.teams[0].primiera > self.teams[1].primiera:
            scores[self.teams[0]] += 1
            self.teams[0].score += 1
            self.teams[0].logs.append("+1 primiera")
        elif self.teams[1].primiera > self.teams[0].primiera:
            scores[self.teams[1]] += 1
            self.teams[1].score += 1
            self.teams[1].logs.append("+1 primiera")
        else:
            self.teams[0].logs.append("Primiera pari")
            self.teams[1].logs.append("Primiera pari")

        for team in self.teams:
            self.logs.extend(team.logs)
            self.logs.append('')
            
        return scores

    def show_logs(self):
        return HTML(SEP.join(self.logs))
            
class Match:
    
    def __init__(self, team1: Team, team2: Team, seats: list):
        self.teams2scores = {team1: 0, team2: 0}
        self.goal = 21
        self.scoreboard = pd.DataFrame(columns=[team.__repr__() for team in self.teams2scores])
        self.winner = None
        self.set_rotation(seats)
        self.hands = []

    def set_rotation(self, seats: list):
        first_player = random.choice([player for team in self.teams2scores.keys() for player in team.players])
        self.rotation = seats[seats.index(first_player):] + seats[:seats.index(first_player)]
        
    def run(self):
        for n in itertools.count():
            still_no_winners = all(score < self.goal for score in self.teams2scores.values())
            temporary_tie = len(set(self.teams2scores.values())) == 1
            if still_no_winners or temporary_tie:
                hand = Hand(tuple(self.teams2scores.keys()), rotation=self.rotation)
                scores = hand.run()
                self.hands.append(hand)
                for team in self.teams2scores:
                    self.teams2scores[team] += scores[team]
                self.scoreboard.loc[n + 1, :] = [self.teams2scores[team] for team in self.teams2scores]
                # shift rotation
                self.rotation.append(self.rotation.pop(0))
            else:
                self.scoreboard.index.name = 'hand'
                break

        self.n_hands = len(self.scoreboard)
        self.winner = self.scoreboard.max().idxmax()

    def elect_mvp():
        # per ogni giocatore, calcola frazione di punti totali del team di cui è responsabile
        pass
                
class Tournament:
    
    def __init__(
        self, 
        team1: tuple, 
        team2: tuple,
        n_match: int = 10
        ):
        self.teams = [Team(*team1), Team(*team2)]
        self.n_match = n_match
        self.matches = []
        self.assign_seats()

    def assign_seats(self):
        random.shuffle(self.teams)
        random.shuffle(self.teams[0].players)
        random.shuffle(self.teams[1].players)
        self.seats = [self.teams[k].players[h] for h in range(2) for k in range(2)]
        
    def run(self):
        for n in tqdm(range(self.n_match), "Partite: "):
            match = Match(team1=self.teams[0], team2=self.teams[1], seats=self.seats)
            match.run()
            self.matches.append(match)
        self.scoreboard = pd.DataFrame(
            data=[
                [
                    match.n_hands,
                    match.winner,
                    int(match.scoreboard.max().loc[self.teams[0].__repr__()]),
                    int(match.scoreboard.max().loc[self.teams[1].__repr__()])
                ]
                for match in self.matches],
            columns=['hands', 'winner', self.teams[0].__repr__(), self.teams[1].__repr__()],
            index=range(1, self.n_match + 1)
            )