import json
import random
import sys


names_files = ("male-names.txt", "female-names.txt")

def to_chr(i):
    return chr(i + ord('A'))

def init(data):
    with open("setup.json", "r") as f:
        state = json.load(f)
    names_file = random.choice(names_files)
    with open(names_file, "r") as f:
        nameset = f.read().splitlines()
    names = random.choices(nameset, k=2)
    state["name"] = random.choice([names[0], names[1], "{}-{}".format(*names)])
    print(json.dumps(state), flush=True)

def status(data):
    if status == "game_over":
        exit(0)

def shoot(data):
    board = data["opponent_board"]["board"]
    for row in range(len(board)):
        for col in range(len(board[row])):
            if board[row][col] == " ":
                print("{} {}".format(to_chr(row), col), flush=True)
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
