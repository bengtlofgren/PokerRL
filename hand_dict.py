from pypokerengine.engine.deck import Deck
from pypokerengine.utils.card_utils import estimate_hole_card_win_rate, gen_cards
import itertools as it

class HandDict():
    def __init__(self):
        self.hand_list = list(it.combinations([str(card) for card in Deck().deck], 2))
        self.hand_dict = self.make_hand_dict(self.hand_list)
        self.preflop_dict = self.calc_preflop_dict()
  
    def make_hand_dict(self, hand_list):
        hand_dict = {}
        # (52 choose 2 == 1326)
        hand_zip = list(zip(hand_list, [1/1326]*1326 ))
        hand_dict.update(hand_zip)
        return hand_dict

    @classmethod
    def sort_key(cls, card):
        card_translator = {
        2  :  '2',
        3  :  '3',
        4  :  '4',
        5  :  '5',
        6  :  '6',
        7  :  '7',
        8  :  '8',
        9  :  '9',
        10 : 'T',
        11 : 'J',
        12 : 'Q',
        13 : 'K',
        14 : 'A'
        }
        inverse = lambda hsh: {v:k for k,v in hsh.items()}
        card_translator = inverse(card_translator)
        card = list(card)
        first_card = card[0]
        second_card = card_translator.get(card[1])
        return(first_card,second_card)

    def update_prob(self):
        for card in self.hand_list:
            pass
    
    def calc_preflop_dict(self, nb_player=4):
        preflop_dict = {}
        win_rate_list = []
        for card in self.hand_list:
            win_rate = estimate_hole_card_win_rate(
                nb_simulation=100,
                nb_player=nb_player,
                hole_card=gen_cards(list(card)),
                community_card=gen_cards([])
                )     
            win_rate_list.append(win_rate)
        preflop_zip = list(zip(self.hand_list, win_rate_list))
        preflop_dict.update(preflop_zip)
        return preflop_dict

print(HandDict().preflop_dict)