from random import random
x = {}

def populate(y: dict[float, int]):
    x[random()] = 3

for i in range(10):
    populate(x)

print(x)