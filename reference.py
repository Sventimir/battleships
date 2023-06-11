import json
import random
import sys


names_files = ("male-names.txt", "female-names.txt")

def init(data):
    with open("setup.json", "r") as f:
        state = json.load(f)
    names_file = random.choice(names_files)
    with open(names_file, "r") as f:
        nameset = f.read().splitlines()
    names = random.choices(nameset, k=2)
    state["name"] = random.choice([names[0], names[1], "{}-{}".format(*names)])
    print(json.dumps(state))

def status(data):
    if status == "game_over":
        exit(0)

def shoot(data):
    for row in range(len(data["opponent_board"])):
        for col in range(len(data["opponent_board"][row])):
            if data["opponent_board"][row][col] == " ":
                print("{} {}".format(row, col))
                return
    exit(1)

def main():
    while True:
        input_line = sys.stdin.readline()
        if not input_line:
            exit(0)
        data = json.loads(input_line.strip())
        globals()[data["event"]](data)


if __name__ == "__main__":
    main()
