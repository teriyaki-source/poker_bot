import consts
import config
import numpy as np
import game as gm
import player as pl

def test_player(player, num_tables=10, num_hands=0, bot_type = "chip"):

    # time to test if the winner is actually the best player
    # consts.VERBOSITY = [5]
    test_winners = []
    test_tables = [gm.Game(8) for _ in range(num_tables)]
    for table in test_tables:
        table.players[0].brain.set_weights_biases(player.brain.weights, player.brain.biases)
        table.play_game(num_hands)
        chip_winner, winrate_winner = table.get_winner()
        if bot_type == "chip":
            test_winners.append(chip_winner)
        elif bot_type == "rate":
            test_winners.append(winrate_winner)
        # test_winners.append(table.get_winner())

    # TODO: Update this. its not quite right
    trained_bot_wins = sum(1 for player in test_winners if player.name == "Player 1")
    consts.log(f"{bot_type} Trained bot wins: {trained_bot_wins} out of {num_tables} tables", consts.GENERATION_MESSAGES)
    return trained_bot_wins / num_tables

def train_player(num_generations=10, mutation_rate=0.05, mutation_strength=0.1, bot_type = "rate"):
    #TODO 
    # there are n number of tables, each with 8 players
    # each table plays until there is a winner
    # the winners of each table are then used to generate new players
    # the new players are then used to create new tables
    # this is repeated x times to improve the player model
    
    tables = [gm.Game(8) for _ in range(config.num_training_tables)]
    winners = []
    consts.log(f"Generation 1", consts.GENERATION_MESSAGES)
    for table in tables:
        table.play_game()
        chip_winner, winrate_winner = table.get_winner()
        if bot_type == "chip":
            winners.append(chip_winner)
        elif bot_type == "rate":
            winners.append(winrate_winner)
        consts.log(f"Winner: {(winrate_winner.name if bot_type == "rate" else chip_winner.name)} of type {bot_type}.", consts.TRAINING_MESSAGES)
    new_players = generate_children(winners, mutation_rate=mutation_rate, mutation_strength=mutation_strength)
    winners = []
    # evolve 10 times
    # consts.VERBOSITY = [0,1,2]
    for i in range(num_generations - 2):
        # create new tables with the new players
        consts.log(f"Generation {i+2}", consts.GENERATION_MESSAGES)
        for j in range(0, len(new_players), 8):
            table = gm.Game(8)
            for k,player in enumerate(table.players):
                player.brain.set_weights_biases(new_players[j+k].brain.weights, new_players[j+k].brain.biases)
            table.play_game()
            chip_winner, winrate_winner = table.get_winner()
            if bot_type == "chip":
                winners.append(chip_winner)
            elif bot_type == "rate":
                winners.append(winrate_winner)
            consts.log(f"Winner: {(winrate_winner.name if bot_type == "rate" else chip_winner.name)} of type {bot_type}.", consts.TRAINING_MESSAGES)
        new_players = generate_children(winners, mutation_rate=mutation_rate, mutation_strength=mutation_strength)
        winners = []

    consts.log(f"Generation {i+3}", consts.GENERATION_MESSAGES)
    for j in range(0, len(new_players), 8):
        table = gm.Game(8)
        for k,player in enumerate(table.players):
            player.brain.set_weights_biases(new_players[j+k].brain.weights, new_players[j+k].brain.biases)
        table.play_game()
        chip_winner, winrate_winner = table.get_winner()
        if bot_type == "chip":
            winners.append(chip_winner)
        elif bot_type == "rate":
            winners.append(winrate_winner)
        consts.log(f"Winner: {(winrate_winner.name if bot_type == "rate" else chip_winner.name)} of type {bot_type}.", consts.TRAINING_MESSAGES)
    new_players = generate_children(winners, num_children=1, mutation_rate=mutation_rate, mutation_strength=mutation_strength)
    winners = []

    # TODO make a way to have this repeat until there are >= 8 and <16 players remaining
    # i.e. if there are more players there are more players, so there will be more than 8 players after this step
    # repeat the process, generating less children each time until there are 8 players left and then play a final game
    # this is a bit of a hack, but it works for now

    consts.log(f"Final Table", consts.GENERATION_MESSAGES)
    table = gm.Game(8)
    for i ,player in enumerate(table.players):
        player.brain.set_weights_biases(new_players[i].brain.weights, new_players[i].brain.biases)
    table.play_game()
    chip_winner, winrate_winner = table.get_winner()
    if bot_type == "chip":
        return chip_winner
    elif bot_type == "rate":
        return winrate_winner
    else:
        return None

def generate_children(players, mutation_rate=0.05, mutation_strength=0.1, num_children=8):
    """Takes a list of players and generates 8 children per player with a crossover of their genes"""
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

        for _ in range(num_children):
            children.append(child1)
            children.append(child2)

    # mutate children
    # what a terrible out of context comment
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
    for i in range(0, len(children), 8):
        for j in range(num_children):
            children[i+j].name = f"Player {j+1}"

    return children