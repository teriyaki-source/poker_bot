target_winrate = 0.25
max_repeats = 3
# this is how many generations the bot will train against itself and randomised players for
# the remaining generations depend on the number of training tables to begin with. 
initial_generations = 10
generation_increment = 10
# this needs to be 8 for now, TODO: but later can be changed to a multiple of 8, or any number, tbc
# can be any multiple of 8. 
# will impact number of generations
# there will be a total of (initial_generations + i * generation_increment) + (num_training_tables/8) + 4
num_training_tables = 8
# set to 0 to play until 1 winner at the table
training_hand_limit = 0

# this controls the mutation rate and strength of the children
# mutation rate is the probability of a mutation occuring
# mutation strength is the size of the mutation
mutation_rate = 0.2
mutation_strength = 0.1



test_num_tables = 30
# set to 0 to play until 1 winner at the table
test_num_hands = 0

num_neural_layers = 3
neural_hidden_layer_size = 15