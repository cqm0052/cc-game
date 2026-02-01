# cc-game

中国象棋小游戏（Python 后端 + JavaScript 前端）

## 功能

- 人机对战，红方/黑方可选谁为 AI
- **对战难度**：普通、困难、地狱（对应 AI 搜索深度 1/2/3）
- **对战历史**：自动记录每局结果与步数，可查看历史对局终盘

## 运行

```bash
pip install -r requirements.txt
python app.py
```

浏览器访问 http://localhost:5000

## 项目结构

- `app.py` - Flask API（新对局、走子、AI 应答、历史）
- `chess_engine.py` - 规则引擎（棋盘、走法、胜负）
- `ai_engine.py` - AI（普通/困难/地狱）
- `history_store.py` - 对战历史存储（JSON 文件，存于 `data/`）
- `static/` - 前端（HTML/CSS/JS）
