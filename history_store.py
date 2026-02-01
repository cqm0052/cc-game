# -*- coding: utf-8 -*-
"""对战历史存储：JSON 文件持久化。"""

import json
import os
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'data', 'game_history.json')


def _ensure_data_dir():
    d = os.path.dirname(HISTORY_FILE)
    if d and not os.path.isdir(d):
        os.makedirs(d)


def _load_all() -> List[dict]:
    _ensure_data_dir()
    if not os.path.isfile(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_all(records: List[dict]):
    _ensure_data_dir()
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def add_record(
    winner: Optional[str],
    difficulty: str,
    moves_count: int,
    board_snapshots: List[List],
    red_is_ai: bool,
) -> str:
    """步骤1：生成 id 与时间。步骤2：追加记录并保存。"""
    record_id = str(uuid4())
    records = _load_all()
    records.append({
        'id': record_id,
        'winner': winner,
        'difficulty': difficulty,
        'moves_count': moves_count,
        'board_snapshots': board_snapshots,
        'red_is_ai': red_is_ai,
        'created_at': datetime.utcnow().isoformat() + 'Z',
    })
    _save_all(records)
    return record_id


def list_records(limit: int = 50) -> List[dict]:
    """返回最近 limit 条记录（不含完整棋盘快照以减小体积）。"""
    records = _load_all()
    result = []
    for r in reversed(records[-limit:]):
        result.append({
            'id': r['id'],
            'winner': r.get('winner'),
            'difficulty': r.get('difficulty', 'normal'),
            'moves_count': r.get('moves_count', 0),
            'red_is_ai': r.get('red_is_ai', False),
            'created_at': r.get('created_at', ''),
        })
    return result


def get_record(record_id: str) -> Optional[dict]:
    """根据 id 获取单条记录（含棋盘快照）。"""
    records = _load_all()
    for r in records:
        if r.get('id') == record_id:
            return r
    return None
