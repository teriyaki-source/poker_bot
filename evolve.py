import consts
import config
import numpy as np
import game as gm
import player as pl

def test_player(player, num_tables=10, num_hands=0, bot_type = "chip"):

    # time to test if the winner is actually the best player
    # consts.VERBOSITY = [5]

    total = 0
    test_winners = []
    test_tables = [gm.Game(config.players_per_table) for _ in range(num_tables)]
    for table in test_tables:
        table.players[0].brain.set_weights_biases(player.brain.weights, player.brain.biases)
        table.play_game(num_hands)
        chip_winner, bb_winner = table.get_winner()
        total += table.players[0].get_bb_return()
        if bot_type == "chip":
            test_winners.append(chip_winner)
        elif bot_type == "rate":
            test_winners.append(bb_winner)
        # test_winners.append(table.get_winner())

    average_trained_bb_return = total / num_tables

    # TODO: Update this. its not quite right
    trained_bot_wins = sum(1 for player in test_winners if player.name == "Player 1")
    # consts.log(f"{bot_type} Trained bot wins: {trained_bot_wins} out of {num_tables} tables", consts.GENERATION_MESSAGES)
    consts.log(f"Trained Big Blind Return bot had the best returns in {trained_bot_wins} out of {num_tables} tables and average {average_trained_bb_return:.2f}BB / 100 Hands.", consts.GENERATION_MESSAGES)
    return average_trained_bb_return, trained_bot_wins / num_tables, 
    return trained_bot_wins / num_tables

def train_player(num_generations=10, mutation_rate=0.05, mutation_strength=0.1, bot_type = "rate"):
    #TODO 
    # there are n number of tables, each with m players
    # each table plays until there is a winner
    # the winners of each table are then used to generate new players
    # the new players are then used to create new tables
    # this is repeated x times to improve the player model
    
    tables = [gm.Game(config.players_per_table) for _ in range(config.num_training_tables)]
    winners = []
    consts.log(f"Generation 1 - with all randomised players", consts.GENERATION_MESSAGES)
    for table in tables:
        table.play_game(config.training_hand_limit)
        chip_winner, bb_winner = table.get_winner()
        if bot_type == "chip":
            winners.append(chip_winner)
        elif bot_type == "rate":
            consts.log(f"Winrate trained bot Big Blind Return / 100 Hands: {bb_winner.get_bb_return():.2f}", consts.TRAINING_MESSAGES)
            winners.append(bb_winner)
        consts.log(f"Winner: {(bb_winner.name if bot_type == "rate" else chip_winner.name)} of type {bot_type}.", consts.TRAINING_MESSAGES)
    new_players = generate_children(winners, mutation_rate=mutation_rate, mutation_strength=mutation_strength)
    winners = []
    # evolve 10 times
    # consts.VERBOSITY = [0,1,2]
    # generations with same size are first generation
    for i in range(num_generations - 2):
        # create new tables with the new players
        consts.log(f"Generation {i+2} - with {config.random_player_pct * 100}% randomised players", consts.GENERATION_MESSAGES)
        for j in range(0, len(new_players), config.players_per_table):
            table = gm.Game(config.players_per_table)
            for k,player in enumerate(table.players):
                player.brain.set_weights_biases(new_players[j+k].brain.weights, new_players[j+k].brain.biases)
            table.play_game(config.training_hand_limit)
            chip_winner, bb_winner = table.get_winner()
            if bot_type == "chip":
                winners.append(chip_winner)
            elif bot_type == "rate":
                consts.log(f"Winrate trained bot Big Blind Return / 100 Hands: {bb_winner.get_bb_return():.2f}", consts.TRAINING_MESSAGES)
                winners.append(bb_winner)
            consts.log(f"Winner: {(bb_winner.name if bot_type == "rate" else chip_winner.name)} of type {bot_type}.", consts.TRAINING_MESSAGES)
        new_players = generate_children(winners, mutation_rate=mutation_rate, mutation_strength=mutation_strength)
        winners = []

    # these generations will be gradually smaller until there are only config.players_per_table players
    # no random children are generated here.
    # assumes a large number of previous generations to minimise the change of overfitting
    while len(new_players) > config.players_per_table:
        consts.log(f"Generation {i+3} - with no randomised players", consts.GENERATION_MESSAGES)
        for j in range(0, len(new_players), config.players_per_table):
            table = gm.Game(config.players_per_table)
            for k,player in enumerate(table.players):
                player.brain.set_weights_biases(new_players[j+k].brain.weights, new_players[j+k].brain.biases)
            table.play_game(config.training_hand_limit)
            chip_winner, bb_winner = table.get_winner()
            if bot_type == "chip":
                winners.append(chip_winner)
            elif bot_type == "rate":
                consts.log(f"Winrate trained bot Big Blind Return / 100 Hands: {bb_winner.get_bb_return():.2f}", consts.TRAINING_MESSAGES)
                winners.append(bb_winner)
            consts.log(f"Winner: {(bb_winner.name if bot_type == "rate" else chip_winner.name)} of type {bot_type}.", consts.TRAINING_MESSAGES)
        new_players = generate_children(winners, num_children=int(config.players_per_table/2), mutation_rate=mutation_rate, mutation_strength=mutation_strength)
        winners = []
        i += 1

    # there should only be config.players_per_table players left here.

    consts.log(f"Final Table", consts.GENERATION_MESSAGES)
    table = gm.Game(config.players_per_table)
    for i ,player in enumerate(table.players):
        player.brain.set_weights_biases(new_players[i].brain.weights, new_players[i].brain.biases)
    table.play_game(config.training_hand_limit)
    chip_winner, bb_winner = table.get_winner()
    if bot_type == "chip":
        return chip_winner
    elif bot_type == "rate":
        consts.log(f"Best BB Return / 100 hands for trained bot: {bb_winner.get_bb_return():.2f} (against other trained bots)", consts.GENERATION_MESSAGES)
        return bb_winner
    else:
        return None

def generate_children(players, mutation_rate=0.05, mutation_strength=0.1, num_children=config.players_per_table):
    """Takes a list of players and generates config.players_per_table children per player with a crossover of their genes"""
    # TODO there is an issue with this - its combining chip and rate players together which isnt necessarily right
    # change this to only combine players of the same type / adjust the usage above to only train one type of player
    
    np.random.shuffle(players)
    children = []
    for i in range(0, len(players), 2):
        player1 = players[i]
        player2 = players[i+1]
        # crossover genes  
        child1_weights = []
        child2_weights = []
        child1_biases = []
        child2_biases = []

        # Crossover weights
        for w1, w2 in zip(player1.brain.weights, player2.brain.weights):
            # Generate random mask
            mask = np.random.rand(*w1.shape) > 0.5
            # Select elements from each parent
            c1 = np.where(mask, w1, w2)
            c2 = np.where(mask, w2, w1)
            child1_weights.append(c1)
            child2_weights.append(c2)

        # Crossover biases
        for b1, b2 in zip(player1.brain.biases, player2.brain.biases):
            mask = np.random.rand(*b1.shape) > 0.5
            c1 = np.where(mask, b1, b2)
            c2 = np.where(mask, b2, b1)
            child1_biases.append(c1)
            child2_biases.append(c2)

        child1 = pl.Neural_AI(f"Child{i}")
        child2 = pl.Neural_AI(f"Child{i+1}")
        child1.brain.set_weights_biases(child1_weights, child1_biases)
        child2.brain.set_weights_biases(child2_weights, child2_biases)
        child1.reset()
        child2.reset()

        

        # adding some random players to see if this changes / prevents overfitting
        # # half of the new players will be random, half will be children
        # maybe this should be a config variable, or just less random players    

        if num_children == config.players_per_table:
            # m, n. 2*m + n = 2 * players per table
            m = int((1 - config.random_player_pct) * config.players_per_table)
            n = 2 * config.players_per_table - 2 * m
            for _ in range(m):                      
                children.append(child1)
                children.append(child2)
            for _ in range(n):
                random_player = pl.Neural_AI(f"Random Child{i}")
                random_player.reset()
                children.append(random_player)
        else:
            for _ in range(num_children):
                children.append(child1)
                children.append(child2)

    # mutate children
    # what a terrible out of context comment
    # im an awful parent
    for child in children:
        for i in range(len(child.brain.weights)):
            mutation = np.random.rand(*child.brain.weights[i].shape) < mutation_rate
            noise = np.random.randn(*child.brain.weights[i].shape) * mutation_strength
            child.brain.weights[i] += mutation * noise  
        for i in range(len(child.brain.biases)):
            mutation = np.random.rand(*child.brain.biases[i].shape) < mutation_rate
            noise = np.random.randn(*child.brain.biases[i].shape) * mutation_strength
            child.brain.biases[i] += mutation * noise
    
    np.random.shuffle(children)
    for i in range(0, len(children), config.players_per_table):
        for j in range(num_children):
            children[i+j].name = f"Player {j+1}"

    return children