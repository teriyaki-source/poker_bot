import game as gm

# TODO:
# [x] Action rounds per game stage
# [x] Turn based action - alternating who is dealer
# [x] Chip stack tracking - the board needs a pot size attribute
# [x] Different action order preflop - utg to act first
# [x] Big blinds
# [ ] handle all ins (skip players who are all in, and make side pots)
# [ ] Variable bet size - can be random for now
# [ ] tidy up betting rules for the player to make them easier to use by the bot
# [ ] Basic automatic decision making for each player - change initialisation to include ways to vary the heuristics


# generate a new game with n players using gm.Game(n), or input a list of names
# deal cards to each player with .deal_player_cards
# print which cards each player has with .print_players()
# return all cards to the deck, shuffle it and start again with .new_hand() then 

def main():
    game1 = gm.Game(8)
    # game1 = gm.Game((("Luke","Human"), ("Bot1", ""), ("Bot2", "")))
    game1.play_game(100)


if __name__ == "__main__":
    main()

