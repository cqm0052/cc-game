# -*- coding: utf-8 -*-
"""中国象棋规则引擎：棋盘、走法生成与胜负判定。"""

from copy import deepcopy
from typing import List, Tuple, Optional

# 棋子类型
PIECE_TYPES = ['king', 'advisor', 'elephant', 'horse', 'rook', 'cannon', 'pawn']
# 红方/黑方
RED, BLACK = 'red', 'black'

# 红方九宫 (帅/仕/相活动范围)
RED_PALACE_ROWS = (7, 8, 9)
RED_PALACE_COLS = (3, 4, 5)
# 黑方九宫
BLACK_PALACE_ROWS = (0, 1, 2)
BLACK_PALACE_COLS = (3, 4, 5)
# 河界：象/相不能过河，红方象 row>=5, 黑方象 row<=4
RIVER_RED_SIDE = 5   # 红方象活动行 >= 5
RIVER_BLACK_SIDE = 4  # 黑方象活动行 <= 4


def initial_board() -> List[List[Optional[dict]]]:
    """步骤1：创建 9x10 空棋盘。步骤2：摆放初始棋子。"""
    board = [[None for _ in range(9)] for _ in range(10)]
    # 黑方 (row 0-3)
    for col, piece_type in [(0, 'rook'), (1, 'horse'), (2, 'elephant'), (3, 'advisor'),
                            (4, 'king'), (5, 'advisor'), (6, 'elephant'), (7, 'horse'), (8, 'rook')]:
        board[0][col] = {'type': piece_type, 'color': BLACK}
    board[2][1] = {'type': 'cannon', 'color': BLACK}
    board[2][7] = {'type': 'cannon', 'color': BLACK}
    for col in (0, 2, 4, 6, 8):
        board[3][col] = {'type': 'pawn', 'color': BLACK}
    # 红方 (row 6-9)
    for col, piece_type in [(0, 'rook'), (1, 'horse'), (2, 'elephant'), (3, 'advisor'),
                            (4, 'king'), (5, 'advisor'), (6, 'elephant'), (7, 'horse'), (8, 'rook')]:
        board[9][col] = {'type': piece_type, 'color': RED}
    board[7][1] = {'type': 'cannon', 'color': RED}
    board[7][7] = {'type': 'cannon', 'color': RED}
    for col in (0, 2, 4, 6, 8):
        board[6][col] = {'type': 'pawn', 'color': RED}
    return board


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 10 and 0 <= c < 9


def get_king_pos(board: List[List], color: str) -> Optional[Tuple[int, int]]:
    """获取指定方将/帅的位置。"""
    for r in range(10):
        for c in range(9):
            p = board[r][c]
            if p and p['type'] == 'king' and p['color'] == color:
                return (r, c)
    return None


def kings_face_each_other(board: List[List], exclude_from: Tuple[int, int] = None) -> bool:
    """步骤1：找红帅、黑将列。步骤2：若同列，检查中间是否无子（飞将）。"""
    red_pos = get_king_pos(board, RED)
    black_pos = get_king_pos(board, BLACK)
    if not red_pos or not black_pos or red_pos[1] != black_pos[1]:
        return False
    c = red_pos[1]
    low, high = min(red_pos[0], black_pos[0]), max(red_pos[0], black_pos[0])
    count = 0
    for r in range(low + 1, high):
        if board[r][c]:
            if (r, c) == exclude_from:
                continue
            count += 1
    return count == 0


def is_in_palace(r: int, c: int, color: str) -> bool:
    if color == RED:
        return r in RED_PALACE_ROWS and c in RED_PALACE_COLS
    return r in BLACK_PALACE_ROWS and c in BLACK_PALACE_COLS


def generate_king_moves(board: List[List], r: int, c: int, color: str) -> List[Tuple[int, int]]:
    moves = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc) or not is_in_palace(nr, nc, color):
            continue
        piece = board[nr][nc]
        if piece is None or piece['color'] != color:
            moves.append((nr, nc))
    return moves


def generate_advisor_moves(board: List[List], r: int, c: int, color: str) -> List[Tuple[int, int]]:
    moves = []
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc) or not is_in_palace(nr, nc, color):
            continue
        piece = board[nr][nc]
        if piece is None or piece['color'] != color:
            moves.append((nr, nc))
    return moves


def generate_elephant_moves(board: List[List], r: int, c: int, color: str) -> List[Tuple[int, int]]:
    moves = []
    for dr, dc in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        if color == RED and nr < RIVER_RED_SIDE:
            continue
        if color == BLACK and nr > RIVER_BLACK_SIDE:
            continue
        # 象眼
        er, ec = r + dr // 2, c + dc // 2
        if board[er][ec]:
            continue
        piece = board[nr][nc]
        if piece is None or piece['color'] != color:
            moves.append((nr, nc))
    return moves


def generate_horse_moves(board: List[List], r: int, c: int, color: str) -> List[Tuple[int, int]]:
    # 8 个方向：马走日，先 2 再 1，检查马腿
    steps = [
        (-2, -1, -1, 0), (-2, 1, -1, 0), (2, -1, 1, 0), (2, 1, 1, 0),
        (-1, -2, 0, -1), (-1, 2, 0, 1), (1, -2, 0, -1), (1, 2, 0, 1),
    ]
    moves = []
    for dr, dc, leg_dr, leg_dc in steps:
        lr, lc = r + leg_dr, c + leg_dc
        if not in_bounds(lr, lc) or board[lr][lc]:
            continue
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        piece = board[nr][nc]
        if piece is None or piece['color'] != color:
            moves.append((nr, nc))
    return moves


def generate_rook_moves(board: List[List], r: int, c: int, color: str) -> List[Tuple[int, int]]:
    moves = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            piece = board[nr][nc]
            if piece is None:
                moves.append((nr, nc))
            else:
                if piece['color'] != color:
                    moves.append((nr, nc))
                break
            nr, nc = nr + dr, nc + dc
    return moves


def generate_cannon_moves(board: List[List], r: int, c: int, color: str) -> List[Tuple[int, int]]:
    moves = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        jumped = False
        while in_bounds(nr, nc):
            piece = board[nr][nc]
            if not jumped:
                if piece is None:
                    moves.append((nr, nc))
                else:
                    jumped = True
            else:
                if piece is not None:
                    if piece['color'] != color:
                        moves.append((nr, nc))
                    break
            nr, nc = nr + dr, nc + dc
    return moves


def generate_pawn_moves(board: List[List], r: int, c: int, color: str) -> List[Tuple[int, int]]:
    moves = []
    if color == RED:
        # 红方向上（行减小）
        if r > 0:
            nr = r - 1
            piece = board[nr][c]
            if piece is None or piece['color'] != color:
                moves.append((nr, c))
        if r <= 4:  # 过河后可横走
            for nc in (c - 1, c + 1):
                if 0 <= nc < 9:
                    piece = board[r][nc]
                    if piece is None or piece['color'] != color:
                        moves.append((r, nc))
    else:
        if r < 9:
            nr = r + 1
            piece = board[nr][c]
            if piece is None or piece['color'] != color:
                moves.append((nr, c))
        if r >= 5:
            for nc in (c - 1, c + 1):
                if 0 <= nc < 9:
                    piece = board[r][nc]
                    if piece is None or piece['color'] != color:
                        moves.append((r, nc))
    return moves


GENERATORS = {
    'king': generate_king_moves,
    'advisor': generate_advisor_moves,
    'elephant': generate_elephant_moves,
    'horse': generate_horse_moves,
    'rook': generate_rook_moves,
    'cannon': generate_cannon_moves,
    'pawn': generate_pawn_moves,
}


def generate_moves_for_piece(board: List[List], r: int, c: int) -> List[Tuple[int, int]]:
    piece = board[r][c]
    if not piece:
        return []
    gen = GENERATORS.get(piece['type'])
    if not gen:
        return []
    return gen(board, r, c, piece['color'])


def all_legal_moves(board: List[List], side: str) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """生成一方所有合法着法（移动后不造成己方被将、不造成飞将）。"""
    result = []
    for r in range(10):
        for c in range(9):
            piece = board[r][c]
            if not piece or piece['color'] != side:
                continue
            for (nr, nc) in generate_moves_for_piece(board, r, c):
                new_board = make_move(board, (r, c), (nr, nc))
                if is_king_attacked(new_board, side):
                    continue
                if kings_face_each_other(new_board):
                    continue
                result.append(((r, c), (nr, nc)))
    return result


def make_move(board: List[List], from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> List[List]:
    """执行一步（不检查合法性），返回新棋盘。"""
    new_board = deepcopy(board)
    r0, c0 = from_pos
    r1, c1 = to_pos
    new_board[r1][c1] = new_board[r0][c0]
    new_board[r0][c0] = None
    return new_board


def is_king_attacked(board: List[List], king_color: str) -> bool:
    """判断 king_color 方的将/帅是否被将军。"""
    kpos = get_king_pos(board, king_color)
    if not kpos:
        return True
    kr, kc = kpos
    opponent = BLACK if king_color == RED else RED
    for r in range(10):
        for c in range(9):
            piece = board[r][c]
            if not piece or piece['color'] != opponent:
                continue
            moves = generate_moves_for_piece(board, r, c)
            if (kr, kc) in moves:
                return True
    return False


def is_checkmate_or_stalemate(board: List[List], side: str) -> str:
    """
    步骤1：若当前被将军且无合法着法，则将死。
    步骤2：若未被将军且无合法着法，则困毙。
    步骤3：否则返回空字符串。
    """
    moves = all_legal_moves(board, side)
    if not moves:
        if is_king_attacked(board, side):
            return 'checkmate'
        return 'stalemate'
    return ''


def board_to_json_serializable(board: List[List]) -> List[List]:
    """将棋盘转为可 JSON 序列化的结构。"""
    out = []
    for row in board:
        out.append([p.copy() if p else None for p in row])
    return out
