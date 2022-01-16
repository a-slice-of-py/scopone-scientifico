import itertools
import random
from typing import Optional, Tuple

import pandas as pd
from IPython.display import HTML, display
from rich import print

from cards import Deck
from players import Player, Team
from utils import MATCH_GOAL, OUT_FORMAT, SEP, iemph, oemph, show_logs


class Hand:

    def __init__(self, teams: Tuple[Team], rotation: list):
        self.teams = teams
        self.reset()
        self.rotation = rotation

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(team.__repr__() for team in self.teams)})"

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
            player.hand = sorted(random.sample(
                cards, int(len(self.deck.cards)/len(self.players))))
            cards = tuple(set(cards) - set(player.hand))

    def run(self, interactive: bool = False):
        interactive = interactive or any(
            player.user for player in self.players)
        self.reset()
        self.distribute_cards()
        for n in range(len(self.players[0].hand)):
            self.logs.append(f"{iemph}Turno {n + 1}{oemph}")
            if interactive:
                show_logs(self.logs[-1])
            self.logs.append(f"Tavolo: {self.table}")
            if interactive:
                show_logs(self.logs[-1])
            for player in self.rotation:
                _table, log = player.play(self.table)
                self.logs.append(log)
                if interactive:
                    show_logs(self.logs[-1])
                if len(_table) < len(self.table):
                    self.last_looter_idx = self.players.index(player)
                self.table = _table
            self.logs.append('')
            if interactive:
                show_logs(self.logs[-1])
        if self.table:
            self.logs.append(
                f"{self.players[self.last_looter_idx]} pulisce il tavolo {self.table}.{SEP}")
            if interactive:
                show_logs(self.logs[-1])
            self.players[self.last_looter_idx].loot.extend(self.table)
            self.table = []

        self.logs.append(f"{iemph}Prese{oemph}")
        if interactive:
            show_logs(self.logs[-1])
        for player in self.players:
            self.logs.append(f"{player.name} ➜ {player.loot}")
            if interactive:
                show_logs(self.logs[-1])
        self.logs.append('')
        if interactive:
            show_logs(self.logs[-1])

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
            if interactive:
                show_logs(team.logs)
            self.logs.append('')
            if interactive:
                show_logs(self.logs[-1])

        return scores


class Match:

    def __init__(self, team1: Team, team2: Team, seats: list):
        self.teams2scores = {team1: 0, team2: 0}
        self.goal = MATCH_GOAL
        self.scoreboard = pd.DataFrame(columns=[team.__repr__() for team in self.teams2scores] + [
                                       player for team in self.teams2scores for player in team.players])
        self.winner, self.mvp = None, None
        self.set_rotation(seats)
        self.hands = []

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(team.__repr__() for team in self.teams2scores)})"

    def set_rotation(self, seats: list):
        first_player = random.choice(
            [player for team in self.teams2scores.keys() for player in team.players])
        self.rotation = seats[seats.index(
            first_player):] + seats[:seats.index(first_player)]

    def run(self, interactive: bool = False):
        interactive = interactive or any(
            player.user for team in self.teams2scores for player in team.players)
        for n in itertools.count():
            still_no_winners = all(
                score < self.goal for score in self.teams2scores.values())
            temporary_tie = len(set(self.teams2scores.values())) == 1
            if still_no_winners or temporary_tie:
                hand = Hand(tuple(self.teams2scores.keys()),
                            rotation=self.rotation)
                scores = hand.run(interactive)
                attribution = [player.attribute_score()
                               for player in hand.players]
                self.hands.append(hand)
                for team in self.teams2scores:
                    self.teams2scores[team] += scores[team]
                self.scoreboard.loc[n + 1, :] = [self.teams2scores[team]
                                                 for team in self.teams2scores] + attribution
                # shift rotation
                self.rotation.append(self.rotation.pop(0))
                if interactive:
                    scoreboard = self.scoreboard.to_html(
                    ) if OUT_FORMAT == 'html' else self.scoreboard.to_markdown()
                    if OUT_FORMAT == 'html':
                        display(HTML(scoreboard))
                    elif OUT_FORMAT == 'markdown':
                        print(scoreboard)
                    input('\nPress any key to proceed...\n')
            else:
                self.scoreboard.index.name = 'hand'
                break

        self.n_hands = len(self.scoreboard)
        self.winner = self.scoreboard.max(
        ).sort_values().reset_index().iloc[-1]['index']
        self.mvp = self.elect_mvp()

    def elect_mvp(self):
        return self.scoreboard[[player for team in self.teams2scores for player in team.players]].sum().sort_values().reset_index().iloc[-1]['index']


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

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(team.__repr__() for team in self.teams)}, partite={self.n_match})"

    def assign_seats(self):
        random.shuffle(self.teams)
        random.shuffle(self.teams[0].players)
        random.shuffle(self.teams[1].players)
        self.seats = [self.teams[k].players[h]
                      for h in range(2) for k in range(2)]

    def run(self, interactive: bool = False):
        interactive = interactive or any(
            player.user for team in self.teams for player in team.players)
        for _ in range(self.n_match):
            match = Match(team1=self.teams[0],
                          team2=self.teams[1], seats=self.seats)
            match.run(interactive)
            self.matches.append(match)
        self.scoreboard = pd.DataFrame(
            data=[
                [
                    match.n_hands,
                    match.winner,
                    int(match.scoreboard.max().loc[self.teams[0].__repr__()]),
                    int(match.scoreboard.max().loc[self.teams[1].__repr__()]),
                    match.mvp,
                    match.scoreboard.sum().loc[match.mvp]
                ]
                for match in self.matches],
            columns=['hands', 'winner', self.teams[0].__repr__(
            ), self.teams[1].__repr__(), 'mvp', 'mvp_score'],
            index=range(1, self.n_match + 1)
        )
        self.scoreboard.index.name = 'match'
        if interactive:
            scoreboard = self.scoreboard.to_html(
            ) if OUT_FORMAT == 'html' else self.scoreboard.to_markdown()
            if OUT_FORMAT == 'html':
                display(HTML(scoreboard))
            elif OUT_FORMAT == 'markdown':
                print(scoreboard)
