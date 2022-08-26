import random
random.seed(0)
lb = 10
sampled_number = random.uniform(0,150)
if (sampled_number < lb):
    print(sampled_number + lb)
else:
    print(sampled_number)
