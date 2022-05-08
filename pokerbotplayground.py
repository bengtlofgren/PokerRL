from sklearn import linear_model
from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils import card_utils
from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.engine.deck import Deck
import random
import numpy as np
import torch
import torch.nn as nn

estimate_hole_card_win_rate, gen_cards = card_utils.estimate_hole_card_win_rate, card_utils.gen_cards


class LinearNN(nn.Module):

    def __init__(self, input_dim = 5, bump = 10, hlayers = 3, output_dim=3):
        super(Net, self).__init__()
        # Bump is just a parameter to scale size of first hidden layer
        # Subsequent hidden layers increase by factor of 2 in pyramid fashion
        starting_size = input * bump
        layers = [nn.Linear(input, starting_size)]
        current_size = starting_size
        for i in range(hlayers):
            if i <= hlayers//2 + 1:
                next_size = current_size*2
            else:
                next_size = current_size/2
            layers.append(nn.Linear(current_size, next_size))
            layers.append(nn.ReLU())
            current_size = next_size
        # an affine operation: y = Wx + b
        #Output is 1 hot for raise, call, fold
        output = nn.Linear(current_size, output_dim)
        layers.append(output)
        layers.append(nn.Sigmoid())
        self.model = nn.Sequential(layers)

    def forward(self, x):
        x = self.model(x)
        return x

class CallOnlyPlayer(BasePokerPlayer):  # Do not forget to make parent class as "BasePokerPlayer"

    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions format => [raise_action_info, call_action_info, fold_action_info]
        call_action_info = valid_actions[1]
        action, amount = call_action_info["action"], call_action_info["amount"]
        return action, amount   # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        # print('picketts hole card is %s' %(hole_card)) 
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

class Folder(BasePokerPlayer):  # Do not forget to make parent class as "BasePokerPlayer"

    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions format => [raise_action_info, call_action_info, fold_action_info]
        if round_state['street'] == 'turn':
            raise_action_info = valid_actions[0]
            action, amount = raise_action_info["action"], 1.3 * raise_action_info["amount"]
        else:
            call_action_info = valid_actions[1]
            action, amount = call_action_info["action"], call_action_info["amount"]
        # print(round_state['seats'])
        return action, amount   # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

class Harjan(BasePokerPlayer):
    def make_a_call(self, valid_actions):
        action = valid_actions[1]['action'] # fetch CALL action info
        amount = valid_actions[1]['amount']
        return (action, amount)

    def make_a_fold(self, valid_actions):
        action = valid_actions[0]['action'] # fetch FOLD action info
        amount = valid_actions[0]['amount']
        return (action, amount)

    def declare_action(self, valid_actions, hole_card, round_state):
        split_hole_cards = [card.split() for card in hole_card]
        if '2' in split_hole_cards and '7' in split_hole_cards:
            print("harjan has a 2,7!! :  %s" %hole_card)
            all_in_info = valid_actions[2]
            action, amount = all_in_info["action"], all_in_info['amount']['max']
        elif random.random() <= 0.5:
            action, amount = self.make_a_call(valid_actions)
        else:
            action, amount = self.make_a_fold(valid_actions)


        return action, amount   # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        # print('harjans hole card is %s' %(hole_card)) 
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

class HonestPlayer(BasePokerPlayer):
    def __init__(self, tighntess = 0.8):
        self.tightness = tighntess
        self.remaining_rounds = 0
        self.nb_player = 0
        self.hole_card = []
        self.opponents = {}
        self.pot = 0
        self.net = LinearNN()
    
    def make_a_raise(self, valid_actions):
        action = valid_actions[2]['action']
        min_raise, max_raise = valid_actions[2]['amount']['min'], valid_actions[2]['amount']['max']
        willing_raise = min(self.pot * np.random.choice([1/3, 1/2, 3/4, 1], p=[1/2, 1/4, 1/8, 1/8]), max_raise*self.tightness)
        amount = max(np.floor(willing_raise), min_raise)
        return (action, amount)

    def make_a_call(self, valid_actions):
        action = valid_actions[1]['action'] # fetch CALL action info
        amount = valid_actions[1]['amount']
        return (action, amount)

    def make_a_fold(self, valid_actions):
        action = valid_actions[0]['action'] # fetch CALL action info
        amount = valid_actions[0]['amount']
        return (action, amount)
    
    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state['community_card']
        win_rate = estimate_hole_card_win_rate(
                nb_simulation=100,
                nb_player=self.nb_player,
                hole_card=gen_cards(hole_card),
                community_card=gen_cards(community_card)
                )
        
        # action_pref = self.model()
        if win_rate >= 1/self.nb_player:
            if random.random() < self.tightness:
                action, amount = self.make_a_call(valid_actions)
            else:
                action, amount = self.make_a_raise(valid_actions)
        
        elif random.random() >= self.tightness:
            action, amount = self.make_a_raise(valid_actions)
        elif valid_actions[1]['amount'] == 0:
            action, amount = self.make_a_call(valid_actions)
        else:
            action, amount = self.make_a_fold(valid_actions)
        return action, amount

    def receive_game_start_message(self, game_info):
        self.remaining_rounds = game_info['rule']['max_round'] + 1
        for player in game_info['seats']:
            self.opponents[player['uuid']] = {'tightness': 0.7}
    
    def receive_round_start_message(self, round_count, hole_card, seats):
        self.nb_player = find_current_players(seats)
        self.hole_card = hole_card
        self.remaining_rounds-=1
        for opponent in self.opponents.values():
            opponent['poss_hands'] = []
        # print('freddys hole card is %s' %hole_card) 

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        # TODO: no ref to side pot here!
        pot = round_state['pot']['main']['amount']
        self.pot = pot
        if action['action'] == 'fold':
            self.nb_player-=1
        if action['action'] == 'raise':
            call_odds = action['amount']/pot
            # this assumes half of remaining players also call, gives slightly better odds
            call_odds_forward = action['amount']/(pot + action['amount']* (self.nb_player-2) * 0.5)

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

def find_current_players(seats):
    count = 0
    for player in seats:
        if player['state'] != 'folded':
            count+=1
    return count

config = setup_config(max_round=500, initial_stack=10000, small_blind_amount=20)
config.register_player(name="Pickett", algorithm=CallOnlyPlayer())
config.register_player(name="Freddy", algorithm=HonestPlayer())
config.register_player(name="Harjan", algorithm=Harjan())
game_result = start_poker(config, verbose=0)
print(game_result)