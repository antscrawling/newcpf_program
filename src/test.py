
from itertools import count
import os

start_ref = 100000000
counter : count = count(1)
transaction_reference = start_ref + next(counter)


print(transaction_reference)
print(transaction_reference)


