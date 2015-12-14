from itertools import permutations

coin_vals = [2,3,5,7,9] #corresponds to: red, corroded, shiny, concave, blue

for a,b,c,d,e in permutations(coin_vals):
    if a + b * c**2 + d**3 - e == 399:
        print a,b,c,d,e #9 2 5 7 3 is solution: blue, red, shiny, concave, corroded