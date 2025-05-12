CHECK = 0
RAISE = 1
CALL = 2
FOLD = 3
ALL_IN = 4


VERBOSITY = [0, 6]
# if below variable is in VERBOSITY then its printed
INFO_MESSAGES = 0           # messages declaring a winner. Keep this in verbosity by default
GAMEPLAY_MESSAGES = 2       # messages detailing actions in the game (check, fold, raise etc.)
PLAYER_CHECKS = 1           # messages printing the players hand and stack size, and the board at the end of the hand
DEBUG = 3
TRAINING_MESSAGES = 4                # messages regarding the training of the bot
EXTRAS = 5          
GENERATION_MESSAGES = 6     # messages regarding the generation of the bot         
DECISION_MAKING = 99        # messages outlining the bots decision making choices

def log(message, level=0):
    if level in VERBOSITY:
        print(message)