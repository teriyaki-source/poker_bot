import player
from itertools import combinations
import consts
from treys import Evaluator, Card as TreysCard
import random

class Basic_AI(player.Player):
    def decision(self, current_bet, min_raise):
        """Returns (decision_type, amount_to_put_in_now):
        - (0, 0) = CHECK
        - (1, raise_to_amount) = RAISE
        - (2, call_amount) = CALL
        - (3, 0) = FOLD
        """
        amount_to_call = current_bet - self.committed  # Chips still owed this round
        valid_choices = []

        if amount_to_call <= 0:
            # Player can check or raise or fold
            # if they have enough to raise
            valid_choices = [(consts.CHECK, 0), (consts.RAISE, min(current_bet + min_raise, self.chips)), (consts.FOLD, 0)]
        else:
            # Player can fold, call, or raise
            # if they have enough to raise
            if self.chips >= amount_to_call + min_raise:
                raise_amount = current_bet + random.choice([min_raise, min_raise + 20])
                valid_choices = [(consts.RAISE, min(raise_amount, self.chips)), (consts.CALL, min(self.chips, amount_to_call)), (consts.FOLD, 0)]
            # if they can only call
            else:
                valid_choices = [(consts.CALL, min(self.chips, amount_to_call)), (consts.FOLD, 0)]

        decision = random.choice(valid_choices)

        if decision[0] in [consts.RAISE, consts.CALL]:  # Only deduct chips for call or raise
            self.chips -= decision[1]
            self.committed += decision[1]

        return decision
    
class Smart_AI(player.Player):
    # I cant believe this works
    # TODO: add ways to track other player VPIP and PFR %s. might need an additional function in game or this class
    def __init__(self, name, board):
        super().__init__(name, board)
        self.evaluator = Evaluator()

    def decision(self, current_bet, min_raise):
        """Returns (decision_type, amount_to_put_in_now)"""
        amount_to_call = current_bet - self.committed  # Chips still owed this round

        # Evaluate the hand strength
        hand_strength = self.get_hand_strength()

        # If the bot has a strong hand, it will raise
        if hand_strength >= 0.85:
            return self.make_raise(current_bet, min_raise)

        # If the bot has a medium hand, it will either call or raise
        elif hand_strength >= 0.60:
            if random.random() < 0.5:  # 50% chance to raise or call
                return self.make_raise(current_bet, min_raise)
            else:
                return self.make_call(amount_to_call)

        # If the bot has a weak hand, it will fold or call only if necessary
        elif hand_strength >= 0.40:
            return self.make_call(amount_to_call) if amount_to_call <= self.chips else self.make_fold()

        # If the bot has a very weak hand, it will fold
        else:
            return self.make_fold()

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

    def make_raise(self, current_bet, min_raise):
        """Makes a raise based on the current bet and minimum raise"""
        raise_amount = current_bet + random.choice([min_raise, min_raise + 20])  # Slightly randomize the raise
        if raise_amount <= self.chips:
            self.chips -= raise_amount - self.committed
            self.committed += raise_amount
            self.pot_committed += raise_amount
            return (consts.RAISE, raise_amount)
        else:
            return self.make_all_in()

    def make_call(self, amount_to_call):
        """Makes a call"""
        if amount_to_call <= 0:
            return (consts.CHECK, 0)
        self.chips -= amount_to_call
        self.committed += amount_to_call
        self.pot_committed += amount_to_call
        return (consts.CALL, amount_to_call)

    def make_fold(self):
        """Folds the hand"""
        self.folded = True
        return (consts.FOLD, 0)

    def make_all_in(self):
        """Makes an all-in bet"""
        raise_amount = self.chips
        self.chips = 0
        self.committed += raise_amount
        self.pot_committed += raise_amount
        return (consts.RAISE, raise_amount)