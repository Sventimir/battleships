import sys
import json


def letter_coord(letter):
    return ord(letter.upper()) - ord('A')

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
        if d == 'left':
            return self.left(distance)
        elif d == 'right':
            return self.right(distance)
        elif d == 'up':
            return self.up(distance)
        elif d == 'down':
            return self.down(distance)

    def show(self, show_ships):
        if self.ship is None:
            return '.' if self.hit else ' '
        elif self.ship.sunk:
            return '-'
        else:
            return 'x' if self.hit else \
                str(self.ship.ident) if show_ships else ' '

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
        if d == 'r':
            squares = self.grid[y][x : x + size]
        else:
            assert d == 'd'
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
        labels = [chr(ord('A') + i) for i in range(self.size)]
        print('|' + ('---+' * self.size) + '---|')
        print('|   | ' + ' | '.join(labels) + ' |')
        for row in range(self.size):
            print('|' + ('---+' * self.size) + '---|')
            print('| {} | '.format(row) + ' | '.join(sq.show(show_ships) for sq in self.grid[row]) + ' | ')
        print('|' + ('---+' * self.size) + '---|')

    def shoot(self, x, y):
        sq = self.grid[y][x]
        sq.hit = True
        try:
            return 'hit' if sq.ship.hp > 0 else 'sunk'
        except AttributeError:
            return 'miss'

    def to_json(self):
        return json.dumps({
            "board": [[sq.show(False) for sq in row] for row in self.grid],
            "remaining_ships": { n: sum(1 for s in self.ships if s.size == n and not s.sunk) for n in range(1, 6) },
        

class Ship:
    def __init__(self, ident, squares):
        self.ident = chr(ident + ord('a'))
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
        self.name = ''
        self.board = Board(board_size)

    def shoot(self, x, y):
        return self.board.shoot(x, y)

    def has_lost(self):
        return all(s.sunk for s in self.board.ships)

class ConsolePlayer(Player):

    def __init__(self, board_size, filename):
        super().__init__(board_size)
        self.filename = filename
    
    def setup(self):
        with open(self.filename, "r") as f:
            data = json.load(f)
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
        self.board.show()

    def make_shot(self, board):
        while True:
            try:
                x, y = input('{}, make your shot: '.format(self.name)).split()
                break
            except ValueError:
                print("Invalid square!")
        return (letter_coord(x), int(y))


def main(args):
    try:
        board_size = args[1]
    except IndexError:
        board_size = 10
    current_player = ConsolePlayer(board_size, "lis.json")
    other_player = ConsolePlayer(board_size, "kot.json")
    current_player.setup()
    other_player.setup()
    
    while True:
        other_player.board.show(show_ships=False)
        x, y = current_player.make_shot(other_player.board)
        result = other_player.shoot(x, y)
        if result == 'miss':
            current_player, other_player = other_player, current_player
        elif other_player.has_lost():
            print('{} has won!'.format(players[current_player].name))
            break
        else:
            continue
    
    
if __name__ == '__main__':
    main(sys.argv)
