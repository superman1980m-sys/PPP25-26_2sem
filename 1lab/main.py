"""
Шахматный симулятор (ООП-версия)
С дополнительными заданиями: откат ходов, подсказка допустимых ходов,
подсветка угрожаемых фигур, сложные правила пешек.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Set, Dict
from enum import Enum
from dataclasses import dataclass, field
import copy


class Color(Enum):
    """Цвет фигуры."""
    WHITE = "white"
    BLACK = "black"
    
    def __str__(self):
        return "Белые" if self == Color.WHITE else "Черные"
    
    @property
    def opposite(self):
        return Color.BLACK if self == Color.WHITE else Color.WHITE


@dataclass(frozen=True)
class Position:
    """Позиция на доске."""
    row: int
    col: int
    
    def __post_init__(self):
        if not (0 <= self.row < 8 and 0 <= self.col < 8):
            raise ValueError(f"Неверная позиция: ({self.row}, {self.col})")
    
    def __str__(self):
        files = 'abcdefgh'
        return f"{files[self.col]}{8 - self.row}"
    
    @classmethod
    def from_string(cls, s: str) -> 'Position':
        """Создание позиции из строки типа 'e2'."""
        s = s.strip().lower()
        if len(s) != 2:
            raise ValueError(f"Неверный формат позиции: {s}")
        col = ord(s[0]) - ord('a')
        row = 8 - int(s[1])
        if not (0 <= col < 8 and 0 <= row < 8):
            raise ValueError(f"Позиция вне доски: {s}")
        return cls(row, col)


@dataclass
class Move:
    """Класс для хранения информации о ходе."""
    piece: 'Piece'
    from_pos: Position
    to_pos: Position
    capture: Optional['Piece'] = None
    promotion: Optional[str] = None  # 'queen', 'rook', 'bishop', 'knight'
    en_passant_capture: Optional[Position] = None
    castle: Optional[str] = None  # 'king_side' или 'queen_side'
    
    def __str__(self):
        """Строковое представление хода."""
        capture_str = "x" if self.capture else ""
        piece_char = self.piece.symbol.upper() if self.piece.symbol != 'p' else ''
        move_str = f"{piece_char}{capture_str}{self.to_pos}"
        if self.promotion:
            promo_map = {'queen': 'Ф', 'rook': 'Л', 'bishop': 'С', 'knight': 'К'}
            move_str += f"={promo_map.get(self.promotion, '')}"
        return move_str


class Piece(ABC):
    """Абстрактный базовый класс для всех шахматных фигур."""
    
    def __init__(self, color: Color, position: Position):
        self._color = color
        self._position = position
        self._has_moved = False
    
    @property
    def color(self) -> Color:
        return self._color
    
    @property
    def position(self) -> Position:
        return self._position
    
    @position.setter
    def position(self, pos: Position):
        self._position = pos
        self._has_moved = True
    
    @property
    def has_moved(self) -> bool:
        return self._has_moved
    
    @property
    @abstractmethod
    def symbol(self) -> str:
        """Символ фигуры (для отображения)."""
        pass
    
    @property
    @abstractmethod
    def value(self) -> int:
        """Ценность фигуры (для оценки)."""
        pass
    
    @abstractmethod
    def get_possible_moves(self, board: 'Board') -> List[Position]:
        """Получение всех возможных ходов без учета шаха."""
        pass
    
    def get_attack_moves(self, board: 'Board') -> List[Position]:
        """Получение всех полей, которые атакует фигура (включая взятия)."""
        return self.get_possible_moves(board)
    
    def can_move_to(self, board: 'Board', pos: Position) -> bool:
        """Проверка, может ли фигура пойти на указанную позицию (без учета шаха)."""
        return pos in self.get_possible_moves(board)
    
    def __str__(self):
        color_char = 'Б' if self.color == Color.WHITE else 'Ч'
        return f"{color_char}{self.symbol.upper()}{self.position}"


class Pawn(Piece):
    """Пешка."""
    
    @property
    def symbol(self) -> str:
        return 'p'
    
    @property
    def value(self) -> int:
        return 1
    
    def get_possible_moves(self, board: 'Board') -> List[Position]:
        moves = []
        direction = -1 if self.color == Color.WHITE else 1
        start_row = 6 if self.color == Color.WHITE else 1
        
        # Ход вперед на одну клетку
        one_step = Position(self.position.row + direction, self.position.col)
        if board.is_empty(one_step):
            moves.append(one_step)
            
            # Ход вперед на две клетки из начальной позиции
            two_step = Position(self.position.row + 2 * direction, self.position.col)
            if self.position.row == start_row and board.is_empty(two_step) and board.is_empty(one_step):
                moves.append(two_step)
        
        # Взятия по диагонали
        for col_offset in [-1, 1]:
            if 0 <= self.position.col + col_offset < 8:
                target = Position(self.position.row + direction, self.position.col + col_offset)
                if target.row in range(8):
                    # Обычное взятие
                    piece = board.get_piece_at(target)
                    if piece and piece.color != self.color:
                        moves.append(target)
                    
                    # Взятие на проходе
                    en_passant_target = board.en_passant_target
                    if en_passant_target and en_passant_target == target:
                        moves.append(target)
        
        return moves
    
    def get_attack_moves(self, board: 'Board') -> List[Position]:
        """Поля, которые атакует пешка (диагонали вперед)."""
        attacks = []
        direction = -1 if self.color == Color.WHITE else 1
        
        for col_offset in [-1, 1]:
            if 0 <= self.position.col + col_offset < 8:
                target = Position(self.position.row + direction, self.position.col + col_offset)
                if target.row in range(8):
                    attacks.append(target)
        return attacks


class Rook(Piece):
    """Ладья."""
    
    @property
    def symbol(self) -> str:
        return 'r'
    
    @property
    def value(self) -> int:
        return 5
    
    def get_possible_moves(self, board: 'Board') -> List[Position]:
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dr, dc in directions:
            for step in range(1, 8):
                new_row = self.position.row + dr * step
                new_col = self.position.col + dc * step
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                    
                target = Position(new_row, new_col)
                piece = board.get_piece_at(target)
                
                if piece is None:
                    moves.append(target)
                elif piece.color != self.color:
                    moves.append(target)
                    break
                else:
                    break
        return moves


class Knight(Piece):
    """Конь."""
    
    @property
    def symbol(self) -> str:
        return 'n'
    
    @property
    def value(self) -> int:
        return 3
    
    def get_possible_moves(self, board: 'Board') -> List[Position]:
        moves = []
        offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for dr, dc in offsets:
            new_row = self.position.row + dr
            new_col = self.position.col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = Position(new_row, new_col)
                piece = board.get_piece_at(target)
                if piece is None or piece.color != self.color:
                    moves.append(target)
        return moves


class Bishop(Piece):
    """Слон."""
    
    @property
    def symbol(self) -> str:
        return 'b'
    
    @property
    def value(self) -> int:
        return 3
    
    def get_possible_moves(self, board: 'Board') -> List[Position]:
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for dr, dc in directions:
            for step in range(1, 8):
                new_row = self.position.row + dr * step
                new_col = self.position.col + dc * step
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                    
                target = Position(new_row, new_col)
                piece = board.get_piece_at(target)
                
                if piece is None:
                    moves.append(target)
                elif piece.color != self.color:
                    moves.append(target)
                    break
                else:
                    break
        return moves


class Queen(Piece):
    """Ферзь."""
    
    @property
    def symbol(self) -> str:
        return 'q'
    
    @property
    def value(self) -> int:
        return 9
    
    def get_possible_moves(self, board: 'Board') -> List[Position]:
        moves = []
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        for dr, dc in directions:
            for step in range(1, 8):
                new_row = self.position.row + dr * step
                new_col = self.position.col + dc * step
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                    
                target = Position(new_row, new_col)
                piece = board.get_piece_at(target)
                
                if piece is None:
                    moves.append(target)
                elif piece.color != self.color:
                    moves.append(target)
                    break
                else:
                    break
        return moves


class King(Piece):
    """Король."""
    
    @property
    def symbol(self) -> str:
        return 'k'
    
    @property
    def value(self) -> int:
        return 1000  # Бесконечная ценность
    
    def get_possible_moves(self, board: 'Board') -> List[Position]:
        moves = []
        offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1),  (1, 0), (1, 1)
        ]
        
        for dr, dc in offsets:
            new_row = self.position.row + dr
            new_col = self.position.col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = Position(new_row, new_col)
                piece = board.get_piece_at(target)
                if piece is None or piece.color != self.color:
                    moves.append(target)
        
        # Рокировка
        if not self.has_moved:
            # Короткая рокировка
            rook_pos = Position(self.position.row, 7)
            rook = board.get_piece_at(rook_pos)
            if (rook and isinstance(rook, Rook) and not rook.has_moved and
                board.is_empty(Position(self.position.row, 5)) and
                board.is_empty(Position(self.position.row, 6))):
                moves.append(Position(self.position.row, 6))
            
            # Длинная рокировка
            rook_pos = Position(self.position.row, 0)
            rook = board.get_piece_at(rook_pos)
            if (rook and isinstance(rook, Rook) and not rook.has_moved and
                board.is_empty(Position(self.position.row, 1)) and
                board.is_empty(Position(self.position.row, 2)) and
                board.is_empty(Position(self.position.row, 3))):
                moves.append(Position(self.position.row, 2))
        
        return moves


class Board:
    """Шахматная доска."""
    
    def __init__(self):
        self._board: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self._en_passant_target: Optional[Position] = None
        self._halfmove_clock: int = 0
        self._fullmove_number: int = 1
        self._setup_board()
    
    def _setup_board(self):
        """Начальная расстановка фигур."""
        # Пешки
        for col in range(8):
            self._board[6][col] = Pawn(Color.WHITE, Position(6, col))
            self._board[1][col] = Pawn(Color.BLACK, Position(1, col))
        
        # Основные фигуры
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, piece_class in enumerate(piece_order):
            self._board[7][col] = piece_class(Color.WHITE, Position(7, col))
            self._board[0][col] = piece_class(Color.BLACK, Position(0, col))
    
    def get_piece_at(self, pos: Position) -> Optional[Piece]:
        """Получение фигуры в позиции."""
        if 0 <= pos.row < 8 and 0 <= pos.col < 8:
            return self._board[pos.row][pos.col]
        return None
    
    def set_piece_at(self, pos: Position, piece: Optional[Piece]):
        """Установка фигуры в позицию."""
        if 0 <= pos.row < 8 and 0 <= pos.col < 8:
            self._board[pos.row][pos.col] = piece
            if piece:
                piece.position = pos
    
    def is_empty(self, pos: Position) -> bool:
        """Проверка, пуста ли клетка."""
        return self.get_piece_at(pos) is None
    
    def is_attacked(self, pos: Position, color: Color) -> bool:
        """Проверка, атакована ли клетка фигурой указанного цвета."""
        for row in range(8):
            for col in range(8):
                piece = self._board[row][col]
                if piece and piece.color == color:
                    if pos in piece.get_attack_moves(self):
                        return True
        return False
    
    def is_check(self, color: Color) -> bool:
        """Проверка, находится ли король под шахом."""
        # Находим короля
        king_pos = None
        for row in range(8):
            for col in range(8):
                piece = self._board[row][col]
                if piece and isinstance(piece, King) and piece.color == color:
                    king_pos = Position(row, col)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False
        
        # Проверяем, атакована ли позиция короля
        return self.is_attacked(king_pos, color.opposite)
    
    def is_checkmate(self, color: Color) -> bool:
        """Проверка мата."""
        if not self.is_check(color):
            return False
        
        # Проверяем, есть ли легальные ходы
        for row in range(8):
            for col in range(8):
                piece = self._board[row][col]
                if piece and piece.color == color:
                    for move_pos in piece.get_possible_moves(self):
                        if self.is_legal_move(piece, move_pos):
                            return False
        return True
    
    def is_stalemate(self, color: Color) -> bool:
        """Проверка пата."""
        if self.is_check(color):
            return False
        
        # Проверяем, есть ли легальные ходы
        for row in range(8):
            for col in range(8):
                piece = self._board[row][col]
                if piece and piece.color == color:
                    for move_pos in piece.get_possible_moves(self):
                        if self.is_legal_move(piece, move_pos):
                            return False
        return True
    
    def is_legal_move(self, piece: Piece, to_pos: Position) -> bool:
        """Проверка легальности хода (включая проверку шаха)."""
        # Сохраняем текущее состояние
        from_pos = piece.position
        captured_piece = self.get_piece_at(to_pos)
        en_passant_capture = None
        
        # Взятие на проходе
        if isinstance(piece, Pawn) and to_pos == self._en_passant_target:
            direction = -1 if piece.color == Color.WHITE else 1
            en_passant_capture = Position(to_pos.row - direction, to_pos.col)
            captured_piece = self.get_piece_at(en_passant_capture)
        
        # Выполняем ход
        self.set_piece_at(to_pos, piece)
        self.set_piece_at(from_pos, None)
        
        # Рокировка - перемещаем ладью
        if isinstance(piece, King) and abs(to_pos.col - from_pos.col) == 2:
            rook_from_col = 7 if to_pos.col > from_pos.col else 0
            rook_to_col = 5 if to_pos.col > from_pos.col else 3
            rook = self.get_piece_at(Position(from_pos.row, rook_from_col))
            if rook:
                self.set_piece_at(Position(from_pos.row, rook_to_col), rook)
                self.set_piece_at(Position(from_pos.row, rook_from_col), None)
        
        # Проверяем, не под шахом ли король
        king_color = piece.color
        in_check = self.is_check(king_color)
        
        # Откатываем изменения
        self.set_piece_at(from_pos, piece)
        self.set_piece_at(to_pos, captured_piece)
        
        if en_passant_capture:
            self.set_piece_at(en_passant_capture, captured_piece)
        
        # Откатываем рокировку
        if isinstance(piece, King) and abs(to_pos.col - from_pos.col) == 2:
            rook_from_col = 7 if to_pos.col > from_pos.col else 0
            rook_to_col = 5 if to_pos.col > from_pos.col else 3
            rook = self.get_piece_at(Position(from_pos.row, rook_to_col))
            if rook:
                self.set_piece_at(Position(from_pos.row, rook_from_col), rook)
                self.set_piece_at(Position(from_pos.row, rook_to_col), None)
        
        return not in_check
    
    def make_move(self, move: Move) -> bool:
        """Выполнение хода."""
        piece = move.piece
        from_pos = move.from_pos
        to_pos = move.to_pos
        
        if not self.is_legal_move(piece, to_pos):
            return False
        
        # Сохраняем информацию о взятии на проходе
        captured = self.get_piece_at(to_pos)
        
        # Обычное взятие
        if captured:
            move.capture = captured
        
        # Взятие на проходе
        if isinstance(piece, Pawn) and to_pos == self._en_passant_target:
            direction = -1 if piece.color == Color.WHITE else 1
            en_passant_capture_pos = Position(to_pos.row - direction, to_pos.col)
            move.en_passant_capture = en_passant_capture_pos
            move.capture = self.get_piece_at(en_passant_capture_pos)
            self.set_piece_at(en_passant_capture_pos, None)
        
        # Выполняем ход
        self.set_piece_at(to_pos, piece)
        self.set_piece_at(from_pos, None)
        
        # Рокировка
        if isinstance(piece, King) and abs(to_pos.col - from_pos.col) == 2:
            rook_from_col = 7 if to_pos.col > from_pos.col else 0
            rook_to_col = 5 if to_pos.col > from_pos.col else 3
            rook = self.get_piece_at(Position(from_pos.row, rook_from_col))
            if rook:
                self.set_piece_at(Position(from_pos.row, rook_to_col), rook)
                self.set_piece_at(Position(from_pos.row, rook_from_col), None)
                move.castle = 'king_side' if to_pos.col > from_pos.col else 'queen_side'
        
        # Обновляем счетчик полуходов
        if isinstance(piece, Pawn) or captured:
            self._halfmove_clock = 0
        else:
            self._halfmove_clock += 1
        
        # Обновляем счетчик полных ходов
        if piece.color == Color.BLACK:
            self._fullmove_number += 1
        
        # Обновляем en passant target
        self._en_passant_target = None
        if isinstance(piece, Pawn) and abs(to_pos.row - from_pos.row) == 2:
            direction = -1 if piece.color == Color.WHITE else 1
            self._en_passant_target = Position(from_pos.row + direction, from_pos.col)
        
        # Превращение пешки
        if isinstance(piece, Pawn):
            promotion_row = 0 if piece.color == Color.WHITE else 7
            if to_pos.row == promotion_row:
                if move.promotion:
                    self.promote_pawn(to_pos, move.promotion)
                else:
                    # По умолчанию превращаем в ферзя
                    self.promote_pawn(to_pos, 'queen')
        
        return True
    
    def promote_pawn(self, pos: Position, piece_type: str):
        """Превращение пешки."""
        pawn = self.get_piece_at(pos)
        if not isinstance(pawn, Pawn):
            return
        
        color = pawn.color
        piece_map = {
            'queen': Queen,
            'rook': Rook,
            'bishop': Bishop,
            'knight': Knight
        }
        
        piece_class = piece_map.get(piece_type.lower())
        if piece_class:
            self.set_piece_at(pos, piece_class(color, pos))
    
    def get_king_position(self, color: Color) -> Optional[Position]:
        """Получение позиции короля."""
        for row in range(8):
            for col in range(8):
                piece = self._board[row][col]
                if piece and isinstance(piece, King) and piece.color == color:
                    return Position(row, col)
        return None
    
    def get_all_pieces(self, color: Optional[Color] = None) -> List[Piece]:
        """Получение всех фигур (опционально по цвету)."""
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self._board[row][col]
                if piece and (color is None or piece.color == color):
                    pieces.append(piece)
        return pieces
    
    def get_attacked_positions(self, color: Color) -> Set[Position]:
        """Получение всех позиций, атакуемых фигурами цвета."""
        attacked = set()
        for piece in self.get_all_pieces(color):
            for pos in piece.get_attack_moves(self):
                attacked.add(pos)
        return attacked
    
    @property
    def en_passant_target(self) -> Optional[Position]:
        return self._en_passant_target
    
    def display(self, highlight_moves: Optional[List[Position]] = None,
                highlight_attacked: Optional[List[Position]] = None):
        """Отображение доски с подсветкой."""
        print("  a b c d e f g h")
        for row in range(8):
            print(f"{8 - row} ", end="")
            for col in range(8):
                piece = self._board[row][col]
                pos = Position(row, col)
                
                # Определяем цвет подсветки
                bg_color = ""
                reset = "\033[0m"
                
                if highlight_moves and pos in highlight_moves:
                    bg_color = "\033[48;5;46m"  # Зеленый
                elif highlight_attacked and pos in highlight_attacked:
                    bg_color = "\033[48;5;196m"  # Красный
                elif (row + col) % 2 == 0:
                    bg_color = "\033[48;5;255m"  # Светлый
                else:
                    bg_color = "\033[48;5;240m"  # Темный
                
                if piece:
                    color_char = "\033[38;5;231m" if piece.color == Color.WHITE else "\033[38;5;16m"
                    symbol = piece.symbol.upper() if piece.color == Color.WHITE else piece.symbol
                    print(f"{bg_color}{color_char} {symbol} {reset}", end="")
                else:
                    print(f"{bg_color}   {reset}", end="")
            print(f" {8 - row}")
        print("  a b c d e f g h")


class Game:
    """Управление игрой."""
    
    def __init__(self):
        self.board = Board()
        self.current_turn = Color.WHITE
        self.move_history: List[Move] = []
        self.game_over = False
        self.winner: Optional[Color] = None
    
    def get_possible_moves_for_piece(self, piece: Piece) -> List[Position]:
        """Получение легальных ходов для фигуры."""
        moves = []
        for pos in piece.get_possible_moves(self.board):
            if self.board.is_legal_move(piece, pos):
                moves.append(pos)
        return moves
    
    def get_all_legal_moves(self, color: Color) -> List[Tuple[Piece, Position]]:
        """Получение всех легальных ходов для цвета."""
        moves = []
        for piece in self.board.get_all_pieces(color):
            for pos in self.get_possible_moves_for_piece(piece):
                moves.append((piece, pos))
        return moves
    
    def make_move(self, from_pos: Position, to_pos: Position, promotion: Optional[str] = None) -> bool:
        """Сделать ход."""
        piece = self.board.get_piece_at(from_pos)
        
        if not piece or piece.color != self.current_turn:
            print("Неверная фигура!")
            return False
        
        if not self.board.is_legal_move(piece, to_pos):
            print("Неверный ход!")
            return False
        
        # Создаем объект хода
        move = Move(piece, from_pos, to_pos, promotion=promotion)
        
        # Сохраняем копию доски для отката
        # (здесь можно сохранить состояние)
        
        # Выполняем ход
        if self.board.make_move(move):
            self.move_history.append(move)
            
            # Проверяем окончание игры
            if self.board.is_checkmate(self.current_turn.opposite):
                self.game_over = True
                self.winner = self.current_turn
                print(f"Мат! Победили {self.current_turn}")
            elif self.board.is_stalemate(self.current_turn.opposite):
                self.game_over = True
                print("Пат! Ничья")
            else:
                self.current_turn = self.current_turn.opposite
                
                # Проверка шаха
                if self.board.is_check(self.current_turn):
                    print(f"Шах {self.current_turn}!")
            
            return True
        
        return False
    
    def undo_move(self) -> bool:
        """Откат последнего хода (доп. задание №5)."""
        if not self.move_history:
            print("Нет ходов для отката")
            return False
        
        # TODO: Полная реализация отката требует сохранения состояния доски
        print("Функция отката ходов требует сохранения полного состояния доски")
        return False
    
    def get_threatened_pieces(self, color: Color) -> List[Piece]:
        """Получение фигур, находящихся под боем (доп. задание №7)."""
        threatened = []
        attacked_positions = self.board.get_attacked_positions(color.opposite)
        
        for piece in self.board.get_all_pieces(color):
            if piece.position in attacked_positions:
                threatened.append(piece)
        
        return threatened
    
    def display(self, selected_piece: Optional[Piece] = None):
        """Отображение доски с подсветкой."""
        highlight_moves = None
        highlight_attacked = None
        
        if selected_piece:
            highlight_moves = self.get_possible_moves_for_piece(selected_piece)
        
        # Подсветка фигур под боем
        if self.current_turn:
            threatened = self.get_threatened_pieces(self.current_turn)
            highlight_attacked = [p.position for p in threatened]
        
        self.board.display(highlight_moves, highlight_attacked)
        
        # Вывод информации
        if self.board.is_check(self.current_turn):
            print(f"⚠️ ШАХ {self.current_turn}! ⚠️")
        
        print(f"\nХод: {self.current_turn}")
        print("Введите ход в формате 'e2 e4' или 'exit' для выхода")
        print("Для подсказки ходов: 'h'")
    
    def parse_move(self, move_str: str) -> Tuple[Optional[Position], Optional[Position], Optional[str]]:
        """Парсинг ввода пользователя."""
        parts = move_str.strip().lower().split()
        if len(parts) < 2:
            return None, None, None
        
        try:
            from_pos = Position.from_string(parts[0])
            to_pos = Position.from_string(parts[1])
            
            promotion = None
            if len(parts) >= 3:
                promotion = parts[2]
            
            return from_pos, to_pos, promotion
        except ValueError as e:
            print(e)
            return None, None, None
    
    def run(self):
        """Запуск игрового цикла."""
        print("=" * 50)
        print("Шахматный симулятор")
        print("=" * 50)
        
        selected_piece = None
        
        while not self.game_over:
            self.display(selected_piece)
            
            user_input = input("> ").strip()
            
            if user_input.lower() == 'exit':
                print("Игра завершена")
                break
            
            if user_input.lower() == 'h':
                # Подсказка: показываем фигуру, которую можно выбрать
                print("\nДоступные фигуры:")
                for piece in self.board.get_all_pieces(self.current_turn):
                    moves = self.get_possible_moves_for_piece(piece)
                    if moves:
                        print(f"  {piece} → {', '.join(str(m) for m in moves)}")
                continue
            
            if user_input.lower() == 'u' or user_input.lower() == 'undo':
                self.undo_move()
                continue
            
            # Попытка выбрать фигуру (ввод одной координаты)
            try:
                pos = Position.from_string(user_input)
                piece = self.board.get_piece_at(pos)
                if piece and piece.color == self.current_turn:
                    selected_piece = piece
                    print(f"Выбрана фигура: {piece}")
                else:
                    print("Неверная фигура")
                continue
            except ValueError:
                pass
            
            # Попытка сделать ход
            from_pos, to_pos, promotion = self.parse_move(user_input)
            if from_pos and to_pos:
                if self.make_move(from_pos, to_pos, promotion):
                    selected_piece = None
                else:
                    print("Неверный ход!")
            else:
                print("Неверный формат. Используйте 'e2 e4' или 'h' для подсказки")
        
        if self.game_over and self.winner:
            print(f"\n🏆 Победили {self.winner}! 🏆")
        elif self.game_over:
            print("\n🤝 Ничья! 🤝")


def main():
    """Точка входа."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
