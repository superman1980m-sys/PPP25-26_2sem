class Move:
    def __init__(self, from_pos, to_pos):
        self.from_pos = from_pos
        self.to_pos = to_pos


class Piece:
    def __init__(self, color, position):
        self.color = color
        self.position = position

    def get_moves(self, board):
        raise NotImplementedError

    def enemy(self, other):
        return other is not None and other.color != self.color


class Pawn(Piece):
    def get_moves(self, board):
        moves = []
        x, y = self.position
        direction = -1 if self.color == 'white' else 1

        if board.is_empty((x + direction, y)):
            moves.append((x + direction, y))

        for dy in [-1, 1]:
            target = (x + direction, y + dy)
            if board.in_bounds(target):
                piece = board.get_piece(target)
                if self.enemy(piece):
                    moves.append(target)

        return moves


class Rook(Piece):
    def get_moves(self, board):
        return self._linear_moves(board, [(1,0), (-1,0), (0,1), (0,-1)])

    def _linear_moves(self, board, directions):
        moves = []
        for dx, dy in directions:
            x, y = self.position
            while True:
                x += dx
                y += dy
                if not board.in_bounds((x, y)):
                    break
                piece = board.get_piece((x, y))
                if piece is None:
                    moves.append((x, y))
                elif self.enemy(piece):
                    moves.append((x, y))
                    break
                else:
                    break
        return moves


class Knight(Piece):
    def get_moves(self, board):
        moves = []
        x, y = self.position
        steps = [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]

        for dx, dy in steps:
            target = (x + dx, y + dy)
            if board.in_bounds(target):
                piece = board.get_piece(target)
                if piece is None or self.enemy(piece):
                    moves.append(target)
        return moves


class Bishop(Rook):
    def get_moves(self, board):
        return self._linear_moves(board, [(1,1),(1,-1),(-1,1),(-1,-1)])


class Queen(Rook):
    def get_moves(self, board):
        return self._linear_moves(board, [
            (1,0),(-1,0),(0,1),(0,-1),
            (1,1),(1,-1),(-1,1),(-1,-1)
        ])


class King(Piece):
    def get_moves(self, board):
        moves = []
        x, y = self.position

        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx == 0 and dy == 0:
                    continue
                target = (x + dx, y + dy)
                if board.in_bounds(target):
                    piece = board.get_piece(target)
                    if piece is None or self.enemy(piece):
                        moves.append(target)
        return moves


class Board:
    UNICODE_PIECES = {
        ('white', 'Pawn'): '♙',
        ('white', 'Rook'): '♖',
        ('white', 'Knight'): '♘',
        ('white', 'Bishop'): '♗',
        ('white', 'Queen'): '♕',
        ('white', 'King'): '♔',

        ('black', 'Pawn'): '♟',
        ('black', 'Rook'): '♜',
        ('black', 'Knight'): '♞',
        ('black', 'Bishop'): '♝',
        ('black', 'Queen'): '♛',
        ('black', 'King'): '♚',
    }

    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]

    def in_bounds(self, pos):
        x, y = pos
        return 0 <= x < 8 and 0 <= y < 8

    def get_piece(self, pos):
        x, y = pos
        return self.grid[x][y]

    def set_piece(self, pos, piece):
        x, y = pos
        self.grid[x][y] = piece
        if piece:
            piece.position = pos

    def is_empty(self, pos):
        return self.in_bounds(pos) and self.get_piece(pos) is None

    def move_piece(self, move):
        piece = self.get_piece(move.from_pos)
        self.set_piece(move.to_pos, piece)
        self.set_piece(move.from_pos, None)

    def setup(self):
        for i in range(8):
            self.set_piece((1, i), Pawn('black', (1, i)))
            self.set_piece((6, i), Pawn('white', (6, i)))

        self.set_piece((0,0), Rook('black',(0,0)))
        self.set_piece((0,7), Rook('black',(0,7)))
        self.set_piece((7,0), Rook('white',(7,0)))
        self.set_piece((7,7), Rook('white',(7,7)))

        self.set_piece((0,1), Knight('black',(0,1)))
        self.set_piece((0,6), Knight('black',(0,6)))
        self.set_piece((7,1), Knight('white',(7,1)))
        self.set_piece((7,6), Knight('white',(7,6)))

        self.set_piece((0,2), Bishop('black',(0,2)))
        self.set_piece((0,5), Bishop('black',(0,5)))
        self.set_piece((7,2), Bishop('white',(7,2)))
        self.set_piece((7,5), Bishop('white',(7,5)))

        self.set_piece((0,3), Queen('black',(0,3)))
        self.set_piece((7,3), Queen('white',(7,3)))

        self.set_piece((0,4), King('black',(0,4)))
        self.set_piece((7,4), King('white',(7,4)))

    def display(self):
        print("  0 1 2 3 4 5 6 7")
        for i, row in enumerate(self.grid):
            line = []
            for cell in row:
                if cell is None:
                    line.append('·')
                else:
                    symbol = self.UNICODE_PIECES[(cell.color, cell.__class__.__name__)]
                    line.append(symbol)
            print(f"{i} " + ' '.join(line))
        print()


class Game:
    def __init__(self):
        self.board = Board()
        self.board.setup()
        self.turn = 'white'

    def play(self):
        while True:
            self.board.display()
            print(f"Ход: {self.turn}")

            try:
                x1, y1 = map(int, input("Откуда (x y): ").split())
                x2, y2 = map(int, input("Куда (x y): ").split())
            except:
                print("Ошибка ввода")
                continue

            piece = self.board.get_piece((x1, y1))

            if piece is None or piece.color != self.turn:
                print("Неверная фигура")
                continue

            moves = piece.get_moves(self.board)

            if (x2, y2) not in moves:
                print("Недопустимый ход")
                continue

            move = Move((x1, y1), (x2, y2))
            self.board.move_piece(move)

            self.turn = 'black' if self.turn == 'white' else 'white'


if __name__ == "__main__":
    game = Game()
    game.play()
