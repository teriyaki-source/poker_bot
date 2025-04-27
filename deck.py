import random

class Card:
    def __init__(self, value, suit):
        self.value = value
        self.suit = suit

    def __repr__(self):
        return f"{self.value}{self.suit}"

class Deck:
    """The deck of cards."""
    def __init__(self):
        self.values = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        self.suits = ['c', 'd', 'h', 's']
        self.cards = list()
        # create the deck here by creating an instance of a card for each pair of values and suits
        self.refresh_deck()

    def refresh_deck(self):
        self.cards.clear()
        for suit in self.suits:
            for value in self.values:
                self.cards.append(Card(value, suit))
        self.shuffle_deck()

    def return_card(self, card):
        if card not in self.cards:
            self.cards.append(card)

    def shuffle_deck(self):
        """Shuffles the deck"""
        random.shuffle(self.cards)
        # shuffle the deck - randomise the order of the cards
    
    def report_deck(self):
        """Prints how many cards are currently in the deck"""
        print("There are " , len(self.cards) , " cards in the deck")

    def print_deck(self):
        """Prints the deck"""
        for card in self.cards:
            print(card.value, card.suit)