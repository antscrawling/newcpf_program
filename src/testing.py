

import multiprocessing
import os

def run_program():
    os.system('python3 src/run_cpf_simulation_v7.py')

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_program)
    p2 = multiprocessing.Process(target=run_program)

    p1.start()
    p2.start()

    p1.join()
    p2.join()