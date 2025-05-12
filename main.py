import evolve
import config

# TODO:
# [ ] handle all ins (skip players who are all in, and make side pots)
# [ ] change the evaluation function for a) the fitness function or b) the end of training function
#     to check for hand winrate instead of just win/loss
# [ ] add vpip and pfr tracking to the players

# TODO make it only track winrate, dont care about best chip stack.
# TODO bias children generation towards better players ?? 
# TODO add some random bots into the mix too? for during training

# generate a new game with n players using gm.Game(n), or input a list of names
# deal cards to each player with .deal_player_cards
# print which cards each player has with .print_players()
# return all cards to the deck, shuffle it and start again with .new_hand() then 

def main():
    print(f"Starting training with config:")
    print(f"target_winrate: {config.target_winrate}")
    print(f"target_bb_return: {config.target_bb_return}")
    print(f"max_repeats: {config.max_repeats}")
    print(f"initial_generations: {config.initial_generations}")
    print(f"generation_increment: {config.generation_increment}")
    print(f"num_training_tables: {config.num_training_tables}")
    print(f"players_per_table: {config.players_per_table}")
    print(f"training_hand_limit: {config.training_hand_limit}")
    print(f"mutation_rate: {config.mutation_rate}")
    print(f"mutation_strength: {config.mutation_strength}")
    print(f"test_num_tables: {config.test_num_tables}")
    print(f"test_num_hands: {config.test_num_hands}")
    print(f"num_neural_layers: {config.num_neural_layers}")
    print(f"hidden_layer_size: {config.neural_hidden_layer_size}")


    # can probably remove this and just replace the below with the direct config references
    target_winrate = config.target_winrate
    max_repeats = config.max_repeats
    initial_generations = config.initial_generations
    generation_increment = config.generation_increment

    mutation_rate = config.mutation_rate
    mutation_strength = config.mutation_strength

    test_num_tables = config.test_num_tables
    # set to 0 to play until 1 winner at the table
    test_num_hands = config.test_num_hands

    i = 0
    chip_trained_winrate = 0
    bb_trained_winrate = 0
    while (chip_trained_winrate <= target_winrate or bb_trained_winrate <= target_winrate) and i < max_repeats:
        print(f"Epoch {i + 1} of {max_repeats}")
        
        bb_trained_bot = evolve.train_player(num_generations=initial_generations + i * generation_increment, 
                                                                    mutation_rate=mutation_rate, mutation_strength=mutation_strength, bot_type = "rate")
        
        
        bb_return, bb_trained_winrate = evolve.test_player(bb_trained_bot, num_tables=test_num_tables, num_hands=test_num_hands, bot_type="rate")
        print(f"Winrate Trained bot winrate: {bb_trained_winrate:.2f}")

        # TODO make this a config variable
        # chip_trained_bot = evolve.train_player(num_generations=initial_generations + i * generation_increment, 
        #                                                             mutation_rate=mutation_rate, mutation_strength=mutation_strength, bot_type = "chip")
        # chip_trained_winrate = evolve.test_player(chip_trained_bot, num_tables=test_num_tables, num_hands=test_num_hands, bot_type="chip")
        # print(f"Chip Trained bot winrate: {chip_trained_winrate}")
        i+= 1

    # change this depending on the bot type
    # TODO make this a config variable
    # if bb_trained_winrate >= target_winrate or bb_return >= config.target_bb_return:
    
    # TODO add a better data header to the file, with training params included and other stats etc.
    print(f"Winrate against random bots: {bb_trained_winrate} | Target winrate: {target_winrate}")
    print(f"Big Blind Return: {bb_return} | Target Big Blind Return: {config.target_bb_return}")
    filename = f"bb_trained_bot_{bb_trained_winrate:.2f}_{bb_return:.2f}.txt"
    write_to_file(filename=filename, bot =bb_trained_bot, winrate=bb_trained_winrate, bot_type="winrate")

    # if chip_trained_winrate > winrate_trained_winrate:
    #     print("Chip trained bot is better")
    #     filename = "chip_trained_bot.txt"
    #     write_to_file(filename=filename, bot =chip_trained_bot, winrate=chip_trained_winrate, bot_type="chip")
    # elif winrate_trained_winrate > chip_trained_winrate:
    #     print("Winrate trained bot is better")
    #     filename = "winrate_trained_bot.txt"
    #     write_to_file(filename=filename, bot =winrate_trained_bot, winrate=winrate_trained_winrate, bot_type="winrate")
    # elif chip_trained_winrate == winrate_trained_winrate:
        # print("Both bots are equally good")
        # filename = "chip_trained_bot.txt"
        # write_to_file(filename=filename, bot =chip_trained_bot, winrate=chip_trained_winrate, bot_type="chip")
        # filename = "winrate_trained_bot.txt"
        # write_to_file(filename=filename, bot =winrate_trained_bot, winrate=winrate_trained_winrate, bot_type="winrate")

def write_to_file(filename, bot, winrate, bot_type):
    with open(filename, 'w') as f:
        f.write(f"Bot type: {bot_type}, Random winrate: {winrate}, vs Trained winrate: {bot.get_win_pct():.2f}\n")
        f.write(f"BB Return: {bot.get_bb_return():.2f}\n")
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