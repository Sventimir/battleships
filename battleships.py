import argparse
import sys
import json
import random
import subprocess


def letter_coord(letter):
    return ord(letter.upper()) - ord("A")

class Square:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hit = False
        self.ship = None

    def left(self, distance=1):
        return Square(self.x - distance, self.y)

    def right(self, distance=1):
        return Square(self.x + distance, self.y)

    def up(self, distance=1):
        return Square(self.x, self.y + distance)

    def down(self, distance=1):
        return Square(self.x, self.y - distance)

    def dir(self, d, distance=1):
        if d == "left":
            return self.left(distance)
        elif d == "right":
            return self.right(distance)
        elif d == "up":
            return self.up(distance)
        elif d == "down":
            return self.down(distance)

    def show(self, show_ships):
        if self.ship is None:
            return "." if self.hit else " "
        elif self.ship.sunk:
            return "-"
        else:
            return "x" if self.hit else \
                str(self.ship.ident) if show_ships else " "

class Board:
    def __init__(self, size):
        self.next_ship_id = 0
        self.grid = [[Square(x, y) for x in range(size)] for y in range(size)]
        self.ships = []

    @property
    def size(self):
        return len(self.grid)

    def square(self, x, y):
        return self.grid[y][x]

    def add_ship(self, size, x, y, d):
        if d == "r":
            squares = self.grid[y][x : x + size]
        else:
            assert d == "d"
            squares = [self.grid[i][x] for i in range(y, y + size)]
        assert len(squares) == size
        ship = Ship(self.next_ship_id, squares)
        self.next_ship_id += 1
        self.ships.append(ship)
        for s in squares:
            assert s.ship == None
            s.ship = ship
        return ship

    def show(self, show_ships=True):
        labels = [chr(ord("A") + i) for i in range(self.size)]
        print("|" + ("---+" * self.size) + "---|")
        print("|   | " + " | ".join(labels) + " |")
        for row in range(self.size):
            print("|" + ("---+" * self.size) + "---|")
            print("| {} | ".format(row) + " | ".join(sq.show(show_ships) for sq in self.grid[row]) + " | ")
        print("|" + ("---+" * self.size) + "---|")

    def shoot(self, x, y):
        try:
            sq = self.grid[y][x]
            sq.hit = True
            return "hit" if sq.ship.hp > 0 else "sunk"
        except AttributeError:
            return "miss"
        except IndexError:
            return "miss"

    def to_json(self):
        return json.dumps({
            "board": [[sq.show(False) for sq in row] for row in self.grid],
            "remaining_ships": { n: sum(1 for s in self.ships if s.size == n and not s.sunk) for n in range(1, 6) }})
        

class Ship:
    def __init__(self, ident, squares):
        self.ident = chr(ident + ord("a"))
        self.squares = squares

    @property
    def hp(self):
        return sum(1 for sq in self.squares if not sq.hit)

    @property
    def size(self):
        return len(self.squares)

    @property
    def sunk(self):
        return self.hp == 0

class Player:
    def __init__(self, board_size=10):
        self.name = ""
        self.board = Board(board_size)

    def shoot(self, x, y):
        return self.board.shoot(x, y)

    def has_lost(self):
        return all(s.sunk for s in self.board.ships)

    def setup(self, data):
        self.name = data["name"]
        for ship in data["ships"]:
            try:
                self.board.add_ship(
                    ship["size"],
                    letter_coord(ship["x"]),
                    ship["y"],
                    ship["dir"]
                )
            except AssertionError:
                print(json.dumps(ship))
                self.board.show()
                raise

    def status(self, status):
        pass

class ConsolePlayer(Player):

    def __init__(self, board_size, filename):
        super().__init__(board_size)
        self.filename = filename

    def setup(self):
        with open(self.filename, "r") as f:
            data = json.load(f)
        super().setup(data)
        self.board.show()

    def make_shot(self, board):
        board.show(show_ships=False)
        while True:
            try:
                x, y = input("{}, make your shot: ".format(self.name)).split()
                break
            except ValueError:
                print("Invalid square!")
        return (letter_coord(x), int(y))

class SubprocessPlayer(Player):
    def __init__(self, board_size, executable, args=()):
        super().__init__(board_size)
        try:
            args = json.loads(args[0])
        except RuntimeError:
            pass
        self.process = self.process = subprocess.Popen(
            args,
            executable=executable,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=False
        )

    def setup(self):
       data = json.loads(self.process.stdout.readline())
       super().setup(data)

    def make_shot(self, board):
        self.send_command({
            "event": "shoot",
            "own_board": board.to_json(),
            "opponent_board": board.to_json()
        })
        x, y = self.process.stdout.readline().split()
        return (letter_coord(x), int(y))

    def status(self, status):
        self.send_command({
            "event": "status",
            "status": status
        })

    def send_command(self, cmd):
        self.process.stdin.write(json.dumps(cmd) + "\n")
        self.process.stdin.flush()


def setup(player1, player2):
    players = [ player1, player2 ]
    random.shuffle(players)
    for player in players:
        player.setup()
        yield player

def parse_arguments(args):
    p = argparse.ArgumentParser()
    p.add_argument("-t", "--type", choices=["console", "subprocess", "mixed"], default="console")
    p.add_argument("-s", "--size", type=int, default=10)
    p.add_argument("player1")
    p.add_argument("player2")
    p.add_argument("-1", nargs=1)
    p.add_argument("-2", nargs=1)
    return p.parse_args(args)

def main(args):
    args=parse_arguments(args)
    if args.type == "console":
        current_player, other_player = setup(
            ConsolePlayer(args.size, args.player1),
            ConsolePlayer(args.size, args.player2)
        )
    elif args.type == "subprocess":
        current_player, other_player = setup(
            SubprocessPlayer(args.size, args.player1, args=args._1),
            SubprocessPlayer(args.size, args.player2, args=args._2)
        )
    elif args.type == "mixed":
        current_player, other_player = setup(
            ConsolePlayer(args.size, args.player1),
            SubprocessPlayer(args.size, args.player2, args=args._2)
        )
    else:
        print("Unknown game type: {}".format(game_type), file=sys.stderr)
        exit(1)
    
    while True:
        x, y = current_player.make_shot(other_player.board)
        result = other_player.shoot(x, y)
        current_player.status(result)
        if result == "miss":
            current_player, other_player = other_player, current_player
        elif other_player.has_lost():
            print("{} has won!".format(players[current_player].name))
            break
        else:
            continue
    
    
if __name__ == "__main__":
    main(args=sys.argv[1:])
