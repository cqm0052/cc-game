# -*- coding: utf-8 -*-
"""中国象棋 AI：三种难度（普通、困难、地狱）。"""

import random
from typing import List, Tuple, Optional

from chess_engine import (
    board_to_json_serializable,
    all_legal_moves,
    make_move,
    is_king_attacked,
    kings_face_each_other,
    get_king_pos,
    RED,
    BLACK,
)

# 棋子价值（粗略）
PIECE_VALUES = {
    'king': 10000,
    'advisor': 20,
    'elephant': 20,
    'horse': 40,
    'rook': 90,
    'cannon': 45,
    'pawn': 10,
}

# 难度对应搜索深度
DEPTH_BY_DIFFICULTY = {
    'normal': 1,
    'hard': 2,
    'hell': 3,
}


def evaluate_board(board: List[List], side: str) -> float:
    """
    步骤1：己方棋子价值之和减去对方棋子价值之和。
    步骤2：己方将/帅被将军则大幅罚分。
    """
    score = 0.0
    opp = BLACK if side == RED else RED
    for r in range(10):
        for c in range(9):
            p = board[r][c]
            if not p:
                continue
            v = PIECE_VALUES.get(p['type'], 0)
            if p['color'] == side:
                score += v
            else:
                score -= v
    if is_king_attacked(board, side):
        score -= 500
    if is_king_attacked(board, opp):
        score += 300
    return score


def minimax(
    board: List[List],
    depth: int,
    side: str,
    alpha: float,
    beta: float,
    is_max: bool,
) -> Tuple[float, Optional[Tuple[Tuple[int, int], Tuple[int, int]]]]:
    """
    步骤1：深度为 0 时返回当前局面评估。
    步骤2：生成当前轮走棋方的所有合法着法。
    步骤3：若无可走则按将死/困毙返回极值，否则递归并 alpha-beta 剪枝。
    """
    if depth <= 0:
        return evaluate_board(board, side), None
    current_side = side if is_max else (BLACK if side == RED else RED)
    moves = all_legal_moves(board, current_side)
    if not moves:
        if is_king_attacked(board, current_side):
            return (-10000 if is_max else 10000), None
        return evaluate_board(board, side), None
    best_move = moves[0]
    if is_max:
        best_val = -1e9
        for (fr, fc), (tr, tc) in moves:
            new_board = make_move(board, (fr, fc), (tr, tc))
            val, _ = minimax(new_board, depth - 1, side, alpha, beta, False)
            if val > best_val:
                best_val = val
                best_move = ((fr, fc), (tr, tc))
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break
        return best_val, best_move
    else:
        best_val = 1e9
        for (fr, fc), (tr, tc) in moves:
            new_board = make_move(board, (fr, fc), (tr, tc))
            val, _ = minimax(new_board, depth - 1, side, alpha, beta, True)
            if val < best_val:
                best_val = val
                best_move = ((fr, fc), (tr, tc))
            beta = min(beta, best_val)
            if beta <= alpha:
                break
        return best_val, best_move


def ai_choose_move(
    board: List[List],
    ai_color: str,
    difficulty: str,
) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    步骤1：根据难度取搜索深度。
    步骤2：用 minimax 找最优着法；若无则随机合法着法。
    """
    depth = DEPTH_BY_DIFFICULTY.get(difficulty, 1)
    moves = all_legal_moves(board, ai_color)
    if not moves:
        return None
    if difficulty == 'normal':
        # 普通难度：随机加一点评估，增加变化
        scored = []
        for m in moves:
            new_b = make_move(board, m[0], m[1])
            scored.append((evaluate_board(new_b, ai_color), m))
        scored.sort(key=lambda x: -x[0])
        top = [m for v, m in scored if v == scored[0][0]]
        return random.choice(top)
    _, best = minimax(board, depth, ai_color, -1e9, 1e9, True)
    if best is not None:
        return best
    return random.choice(moves)
