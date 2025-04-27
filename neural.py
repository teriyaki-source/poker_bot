import numpy as np
import matplotlib.pyplot as plt

class Poker_Bot:
    """
    TODO:
    [ ] Take in a bunch of data about up to 8 players, (set the values to 0 by default if not entered)
    [ ] Init should 
    
    Usage: init and add opposition for each player
    update_game, update_self and update_opposition for each player every time action is on the bot
    forward_prop with the weights and all the outputs to determine the next action"""
    def __init__(self): #etc etc add a bunch of data here, set all other player data to 0
        self.hand_strength = 0
        self.stack_size = 0
        self.amount_committed_this_action = 0
        self.amount_committed_to_pot = 0
        self.last_action = 0
        self.last_action_amount = 0
        self.position = 0
        
        # list of dictionaries
        self.opposition_params = {}
        
        # info about the game
        self.game_stage = 0
        self.pot_size = 0
        self.average_active_stack = 0
        self.big_blind = 0

        # inputs, weights + biases
        self.inputs = []
        self.weights = []
        self.biases = []
        self.Zs = []
        self.As = []

        return None

    def add_opposition(self, player_number, starting_stack): #etc etc add a bunch of data here
        # add other parameters here and to update_opposition to 'improve' model
        self.opposition_params[player_number] = {
            "stack_size": starting_stack,
            "position" : 0,
            "amounted_committed_to_pot" : 0,
            "amount_commited_this_action"  : 0,
            "last_action" : 0,
            "last_action_amount" : 0,
            "VPIP %" : 0.0,
            "PFR %": 0.0,
        }
        
        return None
    
    def update_self(self, hand_strength, stack_size, 
                    amount_committed_this_action, amount_committed_to_pot, 
                    last_action, last_action_amount, position):
        self.hand_strength = hand_strength
        self.stack_size = stack_size
        self.amount_committed_this_action = amount_committed_this_action
        self.amount_committed_to_pot = amount_committed_to_pot
        self.last_action = last_action
        self.last_action_amount = last_action_amount
        self.position = int(position)
        return None
    
    def update_opposition(self, player_number, stack_size, 
                          amount_committed_this_action, amount_committed_to_pot, 
                          last_action, last_action_amount, position, vpip = None, pfr = None
                          ):
        temp = self.opposition_params[player_number]
        
        temp["stack_size"] = stack_size
        temp["position"] = int(position)
        temp["amount_committed_to_pot"] = amount_committed_to_pot
        temp["amount_committed_this_action"] = amount_committed_this_action
        temp["last_action"] = last_action
        temp["last_action_amount"] = last_action_amount
        if vpip is not None:
            temp["VPIP %"] = vpip
        if pfr is not None:
            temp["PFR %"] = pfr
        return None
    
    def update_game(self, game_stage, pot_size, big_blind, average_active_stack):
        self.game_stage = game_stage
        self.pot_size = pot_size
        self.average_active_stack = average_active_stack
        self.big_blind = big_blind
        return None
    
    def generate_weights(self):
        # create weights and bias matrices based on the size of the inputs, 
        # with a number of hidden layers and hidden layer sizes.
        # output is size 4

        # for now, just 2 hidden layers with size 15
        self.weights = [[] for _ in range(3)]
        self.biases = [[] for _ in range(3)]
        self.Zs = [[] for _ in range(3)]
        self.As = [[] for _ in range(3)]


        for i in range(len(self.weights)):
            if i == 0:
                self.weights[i] = np.random.rand(15, len(self.inputs)) - 0.5
                self.biases[i] = np.random.rand(15, 1) - 0.5
            elif i == len(self.weights) - 1:
                self.weights[i] = np.random.rand(4, 15) - 0.5
                self.biases[i] = np.random.rand(4, 1) - 0.5
            else:
                self.weights[i] = np.random.rand(15, 15) - 0.5
                self.biases[i] = np.random.rand(15, 1) - 0.5

        return None

    def generate_inputs(self):
        # clearing previous inputs
        self.inputs = []

        # adding player inputs
        self.inputs.extend([self.hand_strength, self.stack_size, 
                            self.amount_committed_this_action, self.amount_committed_to_pot, 
                            self.last_action, self.last_action_amount, self.position])
        # adding all opposition values
        for player_data in self.opposition_params.values():
            for value in player_data.values():
                self.inputs.append(value)

        # adding game state values
        self.inputs.extend([self.game_stage, self.pot_size, self.average_active_stack, self.big_blind])
        self.inputs = np.array(self.inputs).reshape(-1, 1)

    def make_decision(self):
        for i in range(len(self.weights)):
            if i == 0:
                self.Zs[i] = self.weights[i].dot(self.inputs) + self.biases[i]
                self.As[i] = self.reLU(self.Zs[i])
            elif i == len(self.weights) - 1:
                self.Zs[i] = self.weights[i].dot(self.As[i-1]) + self.biases[i]
                self.As[i] = self.softmax(self.Zs[i])
            else:
                self.Zs[i] = self.weights[i].dot(self.As[i-1]) + self.biases[i]
                self.As[i] = self.reLU(self.Zs[i])
        
        # add stochasticity (randomness)
        probs = self.As[-1]
        probs += np.random.normal(0, 0.02, size=probs.shape)  # Add small noise
        probs = np.clip(probs, 0, 1)  # Keep inside [0, 1]
        probs /= np.sum(probs)        # Normalize back to sum = 1
        return probs

    def reLU(self, z):
        return np.maximum(0, z)
    
    def softmax(self, z):
        z_shift = z - np.max(z, axis=0, keepdims=True)
        expZ = np.exp(z_shift)
        return expZ / np.sum(expZ, axis=0, keepdims=True)

