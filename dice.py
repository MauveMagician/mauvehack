import random
import datetime

def roll(dice_string):
    generator = random.Random()
    generator.seed(datetime.datetime.timestamp(datetime.datetime.now()))
    number_of_dice, faces = dice_string.split('d')
    accumulator = 0
    for _ in range(int(number_of_dice)):
        accumulator += generator.randint(1,int(faces))
    return accumulator