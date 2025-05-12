import evolve
import config

# TODO:
# [ ] handle all ins (skip players who are all in, and make side pots)
# [ ] change the evaluation function for a) the fitness function or b) the end of training function
#     to check for hand winrate instead of just win/loss
# [ ] add vpip and pfr tracking to the players

# generate a new game with n players using gm.Game(n), or input a list of names
# deal cards to each player with .deal_player_cards
# print which cards each player has with .print_players()
# return all cards to the deck, shuffle it and start again with .new_hand() then 

def main():

    target_winrate = config.target_winrate
    max_repeats = config.max_repeats
    initial_generations = config.initial_generations
    generation_increment = config.generation_increment

    mutation_rate = config.mutation_rate
    mutation_strength = config.mutation_strength

    test_num_tables = config.test_num_tables
    # set to 0 to play until 1 winner at the table
    test_num_hands = config.test_num_hands

    # TODO add more values here / create a config file
    # add ways to modify the training parameters - number of hands per generation etc.

    i = 0
    chip_trained_winrate = 0
    winrate_trained_winrate = 0
    while (chip_trained_winrate <= target_winrate or winrate_trained_winrate <= target_winrate) and i < max_repeats:
        print(f"Epoch {i + 1} of {max_repeats}")
        
        winrate_trained_bot = evolve.train_player(num_generations=initial_generations + i * generation_increment, 
                                                                    mutation_rate=mutation_rate, mutation_strength=mutation_strength, bot_type = "rate")
        
        
        winrate_trained_winrate = evolve.test_player(winrate_trained_bot, num_tables=test_num_tables, num_hands=test_num_hands, bot_type="rate")
        print(f"Winrate Trained bot winrate: {winrate_trained_winrate}")

        # TODO make this a config variable
        # chip_trained_bot = evolve.train_player(num_generations=initial_generations + i * generation_increment, 
        #                                                             mutation_rate=mutation_rate, mutation_strength=mutation_strength, bot_type = "chip")
        # chip_trained_winrate = evolve.test_player(chip_trained_bot, num_tables=test_num_tables, num_hands=test_num_hands, bot_type="chip")
        # print(f"Chip Trained bot winrate: {chip_trained_winrate}")
        i+= 1

    # change this depending on the bot type
    # TODO make this a config variable
    if winrate_trained_winrate > target_winrate:
        print(f"Winrate Trained bot winrate: {winrate_trained_winrate} is greater than target winrate: {target_winrate}")
        filename = "winrate_trained_bot.txt"
        write_to_file(filename=filename, bot =winrate_trained_bot, winrate=winrate_trained_winrate, bot_type="winrate")

    # if chip_trained_winrate > winrate_trained_winrate:
    #     print("Chip trained bot is better")
    #     filename = "chip_trained_bot.txt"
    #     write_to_file(filename=filename, bot =chip_trained_bot, winrate=chip_trained_winrate, bot_type="chip")
    # elif winrate_trained_winrate > chip_trained_winrate:
    #     print("Winrate trained bot is better")
    #     filename = "winrate_trained_bot.txt"
    #     write_to_file(filename=filename, bot =winrate_trained_bot, winrate=winrate_trained_winrate, bot_type="winrate")
    # elif chip_trained_winrate == winrate_trained_winrate:
        print("Both bots are equally good")
        filename = "chip_trained_bot.txt"
        write_to_file(filename=filename, bot =chip_trained_bot, winrate=chip_trained_winrate, bot_type="chip")
        filename = "winrate_trained_bot.txt"
        write_to_file(filename=filename, bot =winrate_trained_bot, winrate=winrate_trained_winrate, bot_type="winrate")

def write_to_file(filename, bot, winrate, bot_type):
    with open(filename, 'w') as f:
        f.write(f"Bot type: {bot_type}, Winrate: {winrate}\n")
        f.write("# weights\n")
        for i, layer in enumerate(bot.brain.weights):
            f.write(f"# layer {i}:\n")
            for row in layer:
                f.write(' '.join(map(str, row)) + '\n')
            f.write("\n")
        f.write("# biases\n")
        for i, layer in enumerate(bot.brain.biases):
            f.write(f"# layer {i}:\n")
            for row in layer:
                f.write(' '.join(map(str, row)) + '\n')
            f.write("\n")


if __name__ == "__main__":
    main()