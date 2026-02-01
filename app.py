# -*- coding: utf-8 -*-
"""中国象棋后端 API：新局、走子、AI 应答、历史记录。"""

from flask import Flask, request, jsonify
from flask_cors import CORS

from chess_engine import (
    initial_board,
    all_legal_moves,
    make_move,
    is_checkmate_or_stalemate,
    get_king_pos,
    board_to_json_serializable,
    RED,
    BLACK,
)
from ai_engine import ai_choose_move
from history_store import add_record, list_records, get_record

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# 内存中的对局：game_id -> { board, turn, difficulty, red_is_ai, moves_count, board_history }
games = {}


def new_game_id():
    import uuid
    return str(uuid.uuid4())


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/api/game/new', methods=['POST'])
def api_new_game():
    """步骤1：解析难度与是否红方为 AI。步骤2：创建新棋盘并写入 games。"""
    data = request.get_json() or {}
    difficulty = data.get('difficulty', 'normal')
    red_is_ai = data.get('red_is_ai', False)
    board = initial_board()
    gid = new_game_id()
    board_history = [board_to_json_serializable(board)]
    games[gid] = {
        'board': board,
        'turn': RED,
        'difficulty': difficulty,
        'red_is_ai': red_is_ai,
        'moves_count': 0,
        'board_history': board_history,
    }
    return jsonify({
        'game_id': gid,
        'board': board_to_json_serializable(board),
        'turn': RED,
        'red_is_ai': red_is_ai,
        'difficulty': difficulty,
    })


@app.route('/api/game/<game_id>', methods=['GET'])
def api_get_game(game_id):
    g = games.get(game_id)
    if not g:
        return jsonify({'error': 'game not found'}), 404
    return jsonify({
        'board': board_to_json_serializable(g['board']),
        'turn': g['turn'],
        'difficulty': g['difficulty'],
        'red_is_ai': g['red_is_ai'],
        'moves_count': g['moves_count'],
    })


@app.route('/api/game/<game_id>/ai_move', methods=['POST'])
def api_ai_move(game_id):
    """步骤1：若当前轮为 AI，则计算并执行一步。步骤2：返回新棋盘与胜负。"""
    g = games.get(game_id)
    if not g:
        return jsonify({'error': 'game not found'}), 404
    ai_color = RED if g['red_is_ai'] else BLACK
    if g['turn'] != ai_color:
        return jsonify({'error': 'not ai turn'}), 400
    board = g['board']
    ai_move = ai_choose_move(board, ai_color, g['difficulty'])
    if not ai_move:
        return jsonify({'error': 'no move'}), 400
    from_a, to_a = ai_move
    board = make_move(board, from_a, to_a)
    g['board'] = board
    g['moves_count'] += 1
    g['board_history'].append(board_to_json_serializable(board))
    g['turn'] = RED if g['turn'] == BLACK else BLACK
    result = is_checkmate_or_stalemate(board, g['turn'])
    winner = None
    if result == 'checkmate':
        winner = ai_color
    elif result == 'stalemate':
        winner = 'draw'
    if winner:
        add_record(
            winner=winner,
            difficulty=g['difficulty'],
            moves_count=g['moves_count'],
            board_snapshots=g['board_history'],
            red_is_ai=g['red_is_ai'],
        )
        return jsonify({
            'board': board_to_json_serializable(board),
            'turn': g['turn'],
            'ai_move': {'from': list(from_a), 'to': list(to_a)},
            'winner': winner,
            'game_over': True,
        })
    return jsonify({
        'board': board_to_json_serializable(board),
        'turn': g['turn'],
        'ai_move': {'from': list(from_a), 'to': list(to_a)},
    })


@app.route('/api/game/<game_id>/move', methods=['POST'])
def api_move(game_id):
    """步骤1：解析 from/to。步骤2：校验轮次与合法性。步骤3：执行走子并更新胜负。步骤4：若轮到 AI 则计算并执行 AI 着法。"""
    g = games.get(game_id)
    if not g:
        return jsonify({'error': 'game not found'}), 404
    data = request.get_json() or {}
    from_pos = tuple(data.get('from', []))
    to_pos = tuple(data.get('to', []))
    if len(from_pos) != 2 or len(to_pos) != 2:
        return jsonify({'error': 'invalid from/to'}), 400
    board = g['board']
    turn = g['turn']
    moves = all_legal_moves(board, turn)
    if (from_pos, to_pos) not in moves:
        return jsonify({'error': 'illegal move'}), 400
    board = make_move(board, from_pos, to_pos)
    g['board'] = board
    g['moves_count'] += 1
    g['board_history'].append(board_to_json_serializable(board))
    g['turn'] = BLACK if turn == RED else RED
    result = is_checkmate_or_stalemate(board, g['turn'])
    winner = None
    if result == 'checkmate':
        winner = turn
    elif result == 'stalemate':
        winner = 'draw'
    if winner:
        add_record(
            winner=winner,
            difficulty=g['difficulty'],
            moves_count=g['moves_count'],
            board_snapshots=g['board_history'],
            red_is_ai=g['red_is_ai'],
        )
        return jsonify({
            'board': board_to_json_serializable(board),
            'turn': g['turn'],
            'winner': winner,
            'game_over': True,
        })
    # 若轮到 AI，计算并执行 AI 着法
    ai_color = RED if g['red_is_ai'] else BLACK
    if g['turn'] == ai_color:
        ai_move = ai_choose_move(board, ai_color, g['difficulty'])
        if ai_move:
            from_a, to_a = ai_move
            board = make_move(board, from_a, to_a)
            g['board'] = board
            g['moves_count'] += 1
            g['board_history'].append(board_to_json_serializable(board))
            g['turn'] = RED if g['turn'] == BLACK else BLACK
            result = is_checkmate_or_stalemate(board, g['turn'])
            winner = None
            if result == 'checkmate':
                winner = ai_color
            elif result == 'stalemate':
                winner = 'draw'
            if winner:
                add_record(
                    winner=winner,
                    difficulty=g['difficulty'],
                    moves_count=g['moves_count'],
                    board_snapshots=g['board_history'],
                    red_is_ai=g['red_is_ai'],
                )
                return jsonify({
                    'board': board_to_json_serializable(board),
                    'turn': g['turn'],
                    'ai_move': {'from': list(from_a), 'to': list(to_a)},
                    'winner': winner,
                    'game_over': True,
                })
            return jsonify({
                'board': board_to_json_serializable(board),
                'turn': g['turn'],
                'ai_move': {'from': list(from_a), 'to': list(to_a)},
            })
    return jsonify({
        'board': board_to_json_serializable(board),
        'turn': g['turn'],
    })


@app.route('/api/history', methods=['GET'])
def api_history():
    limit = request.args.get('limit', 50, type=int)
    return jsonify({'records': list_records(limit=limit)})


@app.route('/api/history/<record_id>', methods=['GET'])
def api_history_detail(record_id):
    r = get_record(record_id)
    if not r:
        return jsonify({'error': 'not found'}), 404
    return jsonify(r)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
