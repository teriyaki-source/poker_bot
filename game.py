import deck as dk
import player as pl
import player2 as pl2
import consts
from enum import Enum
import numpy as np
import random

class Game_Stage(Enum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3

class Board:
    """Has the burns, flop, turn and river"""
    def __init__(self):
        self.burn = [None, None, None]
        self.cards = [None, None, None, None, None]

    def add_card(self, card, index):
        self.cards[index] = card

    def add_burn(self, card):
        self.burn.append(card)

    def return_cards(self):
        self.cards = [None for card in self.cards]
        self.burn = [None for card in self.burn]

    def print_board(self):
        all_cards = [card for card in self.cards if card is not None]
        if len(all_cards) > 0:
            consts.log(all_cards, consts.PLAYER_CHECKS)

class Game:
    # game has x players
    # game has a deck 'game_deck' which it can shuffle, deal to players etc.
    # players is either an int or a list of names
    def __init__(self, players):
        # random.seed(2)
        # np.random.seed(2)
        # the game has a deck
        self.game_deck = dk.Deck()
        self.small_blind = 10
        self.big_blind = 20
        self.pot = 0
        self.hands_played = 0
        # the game has a board
        self.game_board = Board()
        self.count_folded_players = 0
        self.stage = Game_Stage.PREFLOP
        self.players = []
        self.eliminated_players = []
        if isinstance(players, int):
            self.num_players = players
            self.players = [pl.Neural_AI(f"Player {i + 1}") for i in range(players)]
            for player in self.players:
                player.add_board(self.game_board)
                player.add_game(self)
                player.update_bot(self)
            # self.players = [random.choice([pl.Smart_AI(f"Player {i+1} Smart", self.game_board), pl.Basic_AI(f"Player {i+1} Basic", self.game_board)]) for i in range(players)]
        elif isinstance(players, list):
            for player in players:
                self.players.append(player)
                player.add_board(self.game_board)
                player.add_game(self)
            for player in self.players:
                player.update_bot(self)
            self.num_players = len(players)
        else:
            print(type(players))
            raise ValueError("Game must be initialized with an integer or a list of player names.")
        
        for i in range(len(self.players)):
            if i == 0:
                self.players[i].prev = self.players[-1]
                self.players[i].next = self.players[i+1]
            elif i == len(self.players) - 1:
                self.players[i].prev = self.players[i-1]
                self.players[i].next = self.players[0]
            else:
                self.players[i].prev = self.players[i-1]
                self.players[i].next = self.players[i+1]

        self.dealer = self.players[0]

    # Controlling the flow of the game

    def game_flow(self):
        self.hands_played += 1
        for player in self.players:
                if player.chips == 0 and player.committed > 0:
                    consts.log(f"{player.name} has 0 chips but still has {player.committed} committed!", consts.DEBUG)

                if len(self.players) <= 1:
                    break;
                self.new_hand()
                self.deal_player_cards()
                self.print_players()
                consts.log(f"Dealer: {self.dealer.name}", consts.GAMEPLAY_MESSAGES)
                consts.log("--------- PRE-FLOP ----------", consts.GAMEPLAY_MESSAGES)
                self.action_round(self.stage, self.small_blind, self.big_blind)

                if (len(self.players) - 1) > self.count_folded_players:
                    self.deal_hand(self.stage)
                    consts.log("--------- FLOP ----------", consts.GAMEPLAY_MESSAGES)
                    self.print_board()
                    self.action_round(self.stage, self.small_blind, self.big_blind)

                    if (len(self.players) - 1) > self.count_folded_players:
                        self.deal_hand(self.stage)
                        consts.log("--------- TURN ----------", consts.GAMEPLAY_MESSAGES)
                        self.print_board()
                        self.action_round(self.stage, self.small_blind, self.big_blind)

                        if (len(self.players) - 1) > self.count_folded_players:
                            self.deal_hand(self.stage)
                            consts.log("--------- RIVER ----------", consts.GAMEPLAY_MESSAGES)
                            self.print_board()
                            self.action_round(self.stage, self.small_blind, self.big_blind)

                self.rotate_seats()

                self.print_board()
                self.evaluate_winner()
                # need to eliminate players who are out
                for player in self.players:
                    if player.chips <= 0:
                        self.remove_player(player)
                

    def play_game(self, num_hands = 0):
        """Play the entire sequence of the game"""
        # MODIFY THIS TO EDIT HOW THE GAME FLOWS
        
        # tidy this up
        i = 0
        # for i in range(num_hands):
        if num_hands == 0:
            while len(self.players) > 1:
                self.game_flow()
                i += 1
        else:
            for i in range(num_hands):
                self.game_flow()
        consts.log(f"{i + 1} hands played", consts.TRAINING_MESSAGES)
        self.final_check_balances()

    def verify_chip_totals(self):
        """Verify that the total chips in play matches the expected total"""
        total_chips = sum(player.chips for player in self.players) + max(sum(player.committed for player in self.players), self.pot)
        expected_total = self.num_players * 1000  # Each player starts with 1000

        if total_chips != expected_total:
            consts.log(f"Chip total mismatch! Expected {expected_total}, got {total_chips}", consts.DEBUG)
            consts.log(f"Chips: {total_chips}, Committed: {sum(player.pot_committed for player in self.players)}, Pot: {self.pot}", consts.DEBUG)
            for player in self.players:
                consts.log(f"{player.name}: Chips={player.chips}, Committed={player.committed}", consts.DEBUG)
            for player in self.eliminated_players:
                consts.log(f"{player.name} (eliminated): Chips={player.chips}, Committed={player.committed}", consts.DEBUG)

    def action_round(self, stage, small, big):      
        action = True
        last_raiser = None
        current_bet = 0
        small_blind_amount = small
        min_raise = big

        for player in self.players:
            player.committed = 0
            player.last_action = None

        if stage == Game_Stage.PREFLOP:
            current_player = ((self.dealer.next).next).next
            small_blind = current_player.prev.prev
            amt_paid = small_blind.pay_blind(small_blind_amount)
            self.pot += amt_paid
            consts.log(f"{small_blind.name} paid {amt_paid} chips for the small blind", consts.GAMEPLAY_MESSAGES)

            big_blind = current_player.prev
            amt_paid = big_blind.pay_blind(min_raise)
            consts.log(f"{big_blind.name} paid {amt_paid} chips for the big blind", consts.GAMEPLAY_MESSAGES)
            self.pot += amt_paid
            current_bet = min_raise
            # self.verify_chip_totals()  # Verify after blinds

        else:
            current_player = self.dealer.next

        # need to track who the most recent raiser was is to determine when to finish
        # if recent_raiser is current player then break
        # do this check before their action and it should work?
        while action:
            # checks if all players have folded or checked - automatically ending the round with no action
            if all((player.folded or player.last_action == consts.CHECK or player.last_action == consts.CALL or player.all_in) for player in self.players):
                action = False
                break

            # for player in self.players:
            if self.count_folded_players >= (len(self.players) - 1):
                action = False
                break
            # pass over a player in an action rounded if they are folded
            if current_player.folded: # TODO add a skip if its all in as well
                current_player = current_player.next
                continue

            if current_player.all_in:
                current_player = current_player.next
                continue
            # if the last raiser is the current player, all other players must have called or folded, hence the action is over
            if last_raiser == current_player:
                action = False
                break

            # player makes a decision here - fold, call, or raise with amount x
            decision, bet_amount = current_player.decision(current_bet, min_raise)

            current_player.last_action = decision
            if decision == consts.CHECK:
                current_player.last_action = consts.CHECK
                consts.log(f"{current_player.name} CHECKS", consts.GAMEPLAY_MESSAGES)
            elif decision == consts.FOLD:
                self.count_folded_players += 1
                current_player.folded = True
                consts.log(f"{current_player.name} FOLDS", consts.GAMEPLAY_MESSAGES)
            elif decision == consts.CALL:
                amount_to_add = bet_amount # - current_player.committed
                self.pot += amount_to_add
                consts.log(f"{current_player.name} CALLS {bet_amount} chips", consts.GAMEPLAY_MESSAGES)
            elif decision == consts.RAISE:
                last_raiser = current_player
                min_raise = bet_amount - current_bet
                current_bet = bet_amount

                amount_to_add = bet_amount - current_player.committed

                # First, update the player's state
                current_player.chips -= amount_to_add
                current_player.committed += amount_to_add
                current_player.pot_committed += amount_to_add
                current_player.last_action = consts.RAISE
                current_player.last_action_amount = bet_amount

                # Then update pot
                self.pot += amount_to_add

                
                # if self.stage == Game_Stage.RIVER and current_player.name == "Player 3":
                #     print(f"current pot after adding = {self.pot}")
                #     print(f"current player chips after adding = {current_player.chips}\n\n\n\n\n\n")

                consts.log(f"{current_player.name} RAISES to {bet_amount} chips", consts.GAMEPLAY_MESSAGES)
            elif decision == consts.ALL_IN:
                last_raiser = current_player
                amount_to_add = bet_amount
                min_raise = bet_amount - current_bet
                self.pot += amount_to_add
            consts.log(f"The current pot is: {self.pot} chips.", consts.GAMEPLAY_MESSAGES)
            # self.verify_chip_totals()  # Verify after each action

            if self.stage == Game_Stage.PREFLOP and current_player.in_hand == False and current_player.last_action != consts.FOLD:
                current_player.in_hand = True

            current_player = current_player.next

            for player in self.players:
                consts.log(player.next.name, consts.GAMEPLAY_MESSAGES)

        if stage == Game_Stage.PREFLOP:
            self.stage = Game_Stage.FLOP
        elif stage == Game_Stage.FLOP:
            self.stage = Game_Stage.TURN
        elif stage == Game_Stage.TURN:
            self.stage = Game_Stage.RIVER
        return None

    # sub - actions within the flow of the game

    def deal_player_cards(self):
        for i in range(2):
            for player in self.players:
                player.receive_card(self.game_deck.cards.pop(), i)

    def new_hand(self):
        self.stage = Game_Stage.PREFLOP
        self.count_folded_players = 0
        self.pot = 0
        for player in self.players:
            player.reset()
        self.game_board.return_cards()
        self.game_deck.refresh_deck()
        consts.log(f"Deck refreshed. Total cards in deck: {len(self.game_deck.cards)}", consts.DEBUG)

    def print_players(self):
        for player in self.players:
            if isinstance(player, pl.Human) or all(isinstance(player, pl.Neural_AI) for player in self.players) :
                consts.log(f"Name: {player.name}", consts.PLAYER_CHECKS)
                consts.log(f"Cards: {player.get_cards()}", consts.PLAYER_CHECKS)
                consts.log(f"Chip balance: {player.chips}", consts.PLAYER_CHECKS)

    def final_check_balances(self):
        sum = 0
        consts.log("\n", consts.EXTRAS)
        winner, _ = self.get_winner()
        consts.log(f"The winner is {winner.name}", consts.EXTRAS)
        for player in self.players:
            consts.log(f"{player.name} has {player.chips} chips", consts.EXTRAS)
            sum += player.chips
        consts.log(f"Total chips in play = {sum}", consts.EXTRAS)
        for player in self.eliminated_players:
            consts.log(f"{player.name} was eliminated", consts.EXTRAS)

    def rotate_seats(self):
        self.dealer = self.dealer.next

    def remove_player(self, player):
        consts.log(f"{player.name} has been eliminated from the game.", consts.GAMEPLAY_MESSAGES)
        if player.next == player:
            raise ValueError("Can't remove the last player.")
        
        player.next.prev = player.prev
        player.prev.next = player.next

        if self.dealer == player:
            self.dealer = player.next

        self.players.remove(player)
        self.eliminated_players.append(player)
    
    # handling the board

    def print_board(self):
        self.game_board.print_board()

    def deal_hand(self, stage):
        if stage == Game_Stage.FLOP:
            self.game_board.add_burn(self.game_deck.cards.pop())
            for i in range(3):
                self.game_board.add_card(self.game_deck.cards.pop(), i)
        elif stage == Game_Stage.TURN:
            self.game_board.add_burn(self.game_deck.cards.pop())
            self.game_board.add_card(self.game_deck.cards.pop(), 3)
        elif stage == Game_Stage.RIVER:
            self.game_board.add_burn(self.game_deck.cards.pop())
            self.game_board.add_card(self.game_deck.cards.pop(), 4)

    def evaluate_winner(self):
        remaining_players = [player for player in self.players if not player.folded]
        
        best_score = 7462  # Max Treys score (worst possible hand)
        winners = []
        if len(remaining_players) == 1:
            consts.log(f"{remaining_players[0].name} wins the hand!", consts.GAMEPLAY_MESSAGES)
            remaining_players[0].hands_won += 1
            remaining_players[0].chips += self.pot
            remaining_players[0].committed = 0
            self.pot = 0
            self.verify_chip_totals()
        else:
            for player in remaining_players:
                score = player.get_hand_score()
                if score < best_score:
                    best_score = score
                    winners = [player]
                elif score == best_score:
                    winners.append(player)

            if len(winners) == 1:
                consts.log(f"{winners[0].name} wins the hand!", consts.GAMEPLAY_MESSAGES)
                # winners[0].chips += self.pot - winners[0].committed
                winners[0].hands_won += 1
                winners[0].committed = 0
                winners[0].chips += self.pot
                self.pot = 0
                self.verify_chip_totals()
            elif len(winners) > 1:
                names = ', '.join(player.name for player in winners)
                consts.log(f"Tie! {names} split the pot.", consts.GAMEPLAY_MESSAGES)
                split_amount = self.pot // len(winners)
                remainder = self.pot % len(winners)
                for player in winners:
                    player.hands_won += 1
                    player.chips += split_amount
                    # player.chips += split_amount - player.committed  # Subtract their committed amount
                    player.committed = 0  # Reset their committed amount
                if remainder > 0:
                    random.choice(winners).chips += remainder
                self.pot = 0
                self.verify_chip_totals()

    def get_average_stack(self):
        sum = 0
        for player in self.players:
            sum += player.chips
        avg = sum / len(self.players)
        return avg
    
    def get_winner(self):
        """Return chip_winner, winrate_winner.
        \nReturns the player with the most chips, and the player with the best win rate. Will return the same player twice if they are the same"""
        chips_winner = None
        if len(self.players) == 1:
            chips_winner = self.players[0]
        else:
            max = self.players[0]
            for player in self.players:
                if player.chips > max.chips:
                    max = player
            chips_winner = max
        
        winrate_winner = None
        all_players = self.players + self.eliminated_players
        max = all_players[0]
        for player in all_players:
            if player.hands_won > max.hands_won:
                max = player
        winrate_winner = max
        return chips_winner, winrate_winner