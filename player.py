from itertools import combinations
from treys import Evaluator, Card as TreysCard
import neural
import random
import consts
import numpy as np
import math

class Player:
    # players can have either 0 or 2 cards, given to them by deck
    def __init__(self, name):
        self.name = name
        self.chips = 1000 # TODO change this to be initialised at input
        self.committed = 0
        self.pot_committed = 0

        self.in_hand = False
        self.hands_played = 0
        self.hands_won = 0
        self.vpip = 0
        self.pfr = 0
        self.game = None

        #linked list
        self.next = None
        self.prev = None

        # Attributes to be reset at the end of each hand
        self.cards = [None, None]
        self.trey_hand = None

        self.current_hand = None
        self.current_hand_type = None
        self.current_hand_score = None

        # actions to be reset at the end of each hand
        self.folded = False
        self.all_in = False
        self.current_bet = 0
        self.last_action = None
        self.last_action_amount = 0

    def get_win_pct(self):
        winrate = self.hands_won / self.hands_played
        return winrate

    def add_game(self, game):
        self.game = game

    def add_board(self, board):
        self.board = board

    def reset(self):
        self.cards = [None, None]
        self.trey_hand = None

        self.current_hand = None
        self.current_hand_type = None
        self.current_hand_score = None

        self.committed = 0
        self.pot_committed = 0
        self.last_action = None
        self.last_action_amount = 0
        self.folded = False
        self.all_in = False

        if self.in_hand:
            self.hands_played += 1

        if self.game is not None:
            self.vpip = self.hands_played / self.game.hands_played
        

    # handling card distribution and knowledge
    def receive_card(self, card, index):
        self.cards[index] = card

    def print_cards(self):
        print(self.cards[0], self.cards[1])

    def get_cards(self):
        return self.cards

    def get_trey_hand(self, all_cards):
        return [TreysCard.new(card.value + card.suit) for card in all_cards if card is not None]

    def evaluate_current_hand(self):
        """Given the board state, identify current hand"""

        all_cards = [card for card in (self.board.cards + self.cards) if card is not None]
        treys_hand = self.get_trey_hand(all_cards)

        # only ever gets here if the flop has been dealt. If not dealt, handled elsewhere
        # 7 choose 5 possible combinations of hands
        evaluator = Evaluator()
        best_score = 7463
        best_hand = None

        for combo in combinations(treys_hand, 5):
            score = evaluator.evaluate([], list(combo))
            if score < best_score:
                best_score = score
                best_hand = combo

        self.current_hand = [TreysCard.int_to_pretty_str(c) for c in best_hand]
        self.current_hand_type = evaluator.class_to_string(evaluator.get_rank_class(best_score))
        self.current_hand_score = best_score

    def print_current_hand(self):
        print(self.current_hand_score, self.current_hand_type)

    def get_hand_score(self):
        self.evaluate_current_hand()
        return self.current_hand_score

    def pay_blind(self, blind):
        amount_paid = min(self.chips, blind)
        self.chips -= amount_paid
        self.committed += amount_paid
        self.pot_committed += amount_paid
        return amount_paid

    # THE BRAINS. Action changes depending on player
    def decision(self, current_bet, min_raise):
        raise NotImplementedError("Subclasses must implement decision()")

class Human(Player):
    def decision(self, current_bet, min_raise):
        amount_to_call = current_bet - self.committed
        print(f"{self.name} to act:")
        print(f"{self.cards}")
        print(f"Community cards: {self.board.print_board()}")
        print(f"{self.chips} chips available")
        print(f"{self.committed} chips committed already")
        print(f"{amount_to_call} chips to call")
        print(f"{min_raise} chips is the minimum raise")
        print("What would you like to do? (call, raise, fold, check)?")
        
        option = True
        while True:
            decision = input()
            if decision == "call":
                if amount_to_call <= 0:
                    return (consts.CHECK, 0)
                self.chips -= amount_to_call
                self.committed += amount_to_call
                return (consts.CALL, min(self.chips, amount_to_call))
            elif decision == "fold":
                self.folded = True
                return (consts.FOLD, 0)
            elif decision == "check":
                if amount_to_call <= 0:
                    return (consts.CHECK, 0)
                else:
                    print(f"Cannot check! {amount_to_call} chips required to play in hand")
            elif decision == "raise":
                raise_amount = int(input(f"How much would you like to raise to? (Minimum = {current_bet + min_raise})\n"))
                if raise_amount >= current_bet + min_raise:
                    self.chips -= raise_amount - self.committed
                    self.committed += raise_amount
                    return (consts.RAISE, raise_amount)
                else:
                    print(f"Raise amount too small! Must raise at least {min_raise} chips")



    
class Neural_AI(Player):
    def __init__(self, name):
        super().__init__(name)
        self.evaluator = Evaluator()
        self.brain = neural.Poker_Bot()
    
    def update_bot(self, game):
        self.players = game.players
        for i in range(len(self.players)):
            if self.players[i].name != self.name:
                self.brain.add_opposition(self.players[i].name, 1000)

    def decision(self, current_bet, min_raise):
        self.dealer = self.game.dealer
        position = False
        if self.dealer.name == self.name:
            position = True
        if self.last_action is None:
            last_action = -1
        else:
            last_action = int(self.last_action)
        self.brain.update_self(hand_strength=self.get_hand_strength(), stack_size=self.chips, amount_committed_this_action=self.committed, 
                               amount_committed_to_pot=self.pot_committed, last_action=last_action, last_action_amount=self.last_action_amount,
                               position=position, vpip=self.vpip)
        for i in range(len(self.players)):
            if self.players[i].name != self.name:
                position = False
                if self.dealer.name == self.players[i].name:
                    position = True
                if self.players[i].last_action is None:
                    last_action = -1
                else:
                    last_action = int(self.players[i].last_action)
                self.brain.update_opposition(player_number=self.players[i].name, stack_size=self.players[i].chips, amount_committed_this_action=self.players[i].committed, 
                                             amount_committed_to_pot=self.players[i].pot_committed, last_action=last_action, 
                                             last_action_amount=self.players[i].last_action_amount, position=position, vpip = self.players[i].vpip)
        # generate empty players if there are less than 8 players
        for i in range(len(self.players) - 8):
            self.brain.update_opposition(player_number=f"Empty Player {i}", stack_size=0, amount_committed_this_action=0, 
                                         amount_committed_to_pot=0, last_action=-1, last_action_amount=0, position=False)
        self.brain.update_game(self.game.stage.value, self.game.pot, self.game.big_blind, self.game.get_average_stack())
        self.brain.generate_inputs()        
        # if self.brain.weights is None:  # or some other check
        self.brain.generate_weights()
        # options should be a list of length 4, with probabilities for each decision
        # check, fold, call, raise. Game logic is then applied and decision is made
        options = self.brain.make_decision()
        action = np.argmax(options)  # Pick the highest probability action

        amount_to_call = current_bet - self.committed
        if action == 0:  # Check
            if amount_to_call == 0:
                self.last_action = consts.CHECK
                self.last_action_amount = 0
                return (consts.CHECK, 0)
            else:
                # Can't check if there is an outstanding bet
                if options[2] >= options[1]:  # Prefer CALL over FOLD if close
                    return self.make_call(amount_to_call)
                else:
                    return self.make_fold()

        elif action == 1:  # Fold
            if amount_to_call > 0:
                return self.make_fold()
            else:
                # No need to fold if you can check
                self.last_action = consts.CHECK
                self.last_action_amount = 0
                return (consts.CHECK, 0)

        elif action == 2:  # Call
            if amount_to_call == 0:
                self.last_action = consts.CHECK
                self.last_action_amount = 0
                return (consts.CHECK, 0)
            elif amount_to_call >= self.chips:
                return self.make_all_in()
            else:
                return self.make_call(amount_to_call)

        elif action == 3:  # Raise
            
            can_raise = self.chips > amount_to_call + min_raise
            if can_raise:
                return self.make_raise(current_bet, min_raise)
            elif amount_to_call > 0:
                if amount_to_call >= self.chips:
                    return self.make_all_in()
                else:
                    return self.make_call(amount_to_call)
            else:
                self.last_action = consts.CHECK
                self.last_action_amount = 0
                return (consts.CHECK, 0)  
        return None
    
    def make_call(self, amount):
        temp = min(self.chips, amount)
        self.chips -= temp
        self.committed += temp
        self.pot_committed += temp
        self.last_action = consts.CALL
        self.last_action_amount = temp
        return (consts.CALL, temp)

    def make_all_in(self):
        amount = self.chips
        self.committed += amount
        self.pot_committed += amount
        self.last_action = consts.ALL_IN
        self.last_action_amount = amount
        self.chips = 0
        return (consts.ALL_IN, amount)

    def make_fold(self):
        self.last_action = consts.FOLD
        self.last_action_amount = 0
        return (consts.FOLD, 0)

    def make_raise(self, current_bet, min_raise):
        """Make a raise smarter based on pot size, hand strength, and bluffing chance."""
        max_raise = self.chips - (current_bet - self.committed)
        pot_size = self.game.pot

        hand_strength = self.get_hand_strength()  # 0.0 (terrible) -> 1.0 (the nuts)

        # -------- Bluff chance --------
        # 10% chance to bluff if hand is weak (< 0.4)
        bluff = False
        if hand_strength < 0.4:
            if np.random.random() < 0.1:  # 10% bluff chance
                bluff = True

        # -------- Base raise calculation --------
        if bluff:
            # Act like we have a stronger hand
            base_multiplier = np.random.uniform(1.2, 2.0)  # Overbet the pot sometimes
        else:
            base_multiplier = 0.5 + hand_strength  # Normal raise logic

        target_raise = pot_size * base_multiplier

        # -------- Add some randomness --------
        random_noise = np.random.uniform(-0.2, 0.2) * pot_size
        target_raise += random_noise

        # Clamp to legal values
        target_raise = max(min_raise, int(target_raise))
        total_bet = current_bet + target_raise

        # Cap by available chips
        if total_bet >= self.chips:
            return self.make_all_in()
        
        amount_to_put_in = total_bet - self.committed

        total_bet = math.ceil(total_bet/5) * 5

        # Update player state
        # self.chips -= amount_to_put_in
        # self.committed += amount_to_put_in
        # self.pot_committed += amount_to_put_in
        # self.last_action = consts.RAISE
        # self.last_action_amount = total_bet

        # returns the total new bet - including the raise and amount already committed this action
        # print(amount_to_put_in, total_bet)
        return (consts.RAISE, total_bet)


    
    def get_hand_strength(self):
        """Calculates hand strength using Treys Evaluator"""
        all_cards = self.board.cards + self.cards
        treys_hand = [TreysCard.new(card.value + card.suit) for card in all_cards if card is not None]

        best_score = 7463  # Highest possible hand strength value
        for combo in combinations(treys_hand, 5):
            score = self.evaluator.evaluate([], list(combo))
            if score < best_score:
                best_score = score

        hand_strength = 1 - (best_score / 7463)  # Normalize hand strength to [0, 1] range
        return hand_strength