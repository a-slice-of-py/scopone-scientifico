
from typing import Union

from IPython.display import HTML, display

from cards import SUITS

OUT_FORMAT = 'markdown'
MATCH_GOAL = 21
DENARI_GOAL = 5 + 1
CARTE_GOAL = 20 + 1
PRIMIERA_RULES = {7: 21, 6: 18, 1: 16, 5: 15,
                  4: 14, 3: 13, 2: 12, 8: 10, 9: 10, 10: 10}

if OUT_FORMAT == 'html':
    ibold = '<b>'
    iemph = '<i>'
    obold = '</b>'
    oemph = '</i>'
    SEP = '<br>'
elif OUT_FORMAT == 'markdown':
    ibold = '[b]'
    iemph = '[i]'
    obold = '[/b]'
    oemph = '[/i]'
    SEP = '\n'


def show_logs(source: Union[list, str, 'Hand']) -> None:
    if type(source) is str:
        source = [source]
    if type(source) is list:
        msg = SEP.join(source)
    else:
        msg = SEP.join(source.logs)

    if OUT_FORMAT == 'html':
        display(HTML(msg))
    elif OUT_FORMAT == 'markdown':
        print(msg)


def _compute_primiera(loot: list):
    looted_suits = [
        list(filter(lambda x: x.suit == suit, loot)) for suit in SUITS]
    # Exclude empty suits
    looted_suits = [suit for suit in looted_suits if suit]
    return sum(PRIMIERA_RULES.get(max(suit, key=lambda x: PRIMIERA_RULES.get(x.rank)).rank) for suit in looted_suits)
