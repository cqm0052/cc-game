/**
 * 中国象棋前端：棋盘渲染、走子、难度与历史
 */
(function () {
  const API_BASE = '';
  const RED = 'red';
  const BLACK = 'black';

  const PIECE_CHAR = {
    red: { king: '帅', advisor: '仕', elephant: '相', horse: '马', rook: '车', cannon: '炮', pawn: '兵' },
    black: { king: '将', advisor: '士', elephant: '象', horse: '马', rook: '车', cannon: '炮', pawn: '卒' },
  };

  let state = {
    gameId: null,
    board: null,
    turn: RED,
    difficulty: 'normal',
    redIsAi: false,
    selected: null,
    legalMoves: [],
    gameOver: false,
    winner: null,
  };

  function playMoveSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 520;
      osc.type = 'sine';
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.08);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.08);
    } catch (_) {}
  }

  const boardEl = document.getElementById('board');
  const statusEl = document.getElementById('status');
  const difficultyEl = document.getElementById('difficulty');
  const blackIsAiEl = document.getElementById('blackIsAi');
  const btnNewGame = document.getElementById('btnNewGame');
  const btnHistory = document.getElementById('btnHistory');
  const historyPanel = document.getElementById('historyPanel');
  const historyList = document.getElementById('historyList');
  const btnCloseHistory = document.getElementById('btnCloseHistory');

  function getLegalMovesFromServer() {
    if (!state.gameId || !state.board || state.gameOver) return [];
    const side = state.turn;
    const moves = [];
    for (let r = 0; r < 10; r++) {
      for (let c = 0; c < 9; c++) {
        const p = state.board[r][c];
        if (!p || p.color !== side) continue;
        const cellMoves = getMovesForPiece(state.board, r, c);
        for (const [nr, nc] of cellMoves) {
          moves.push({ from: [r, c], to: [nr, nc] });
        }
      }
    }
    return moves;
  }

  function getMovesForPiece(board, r, c) {
    const piece = board[r][c];
    if (!piece) return [];
    const color = piece.color;
    const moves = [];
    const inBounds = (nr, nc) => nr >= 0 && nr < 10 && nc >= 0 && nc < 9;
    const emptyOrEnemy = (nr, nc) => {
      if (!inBounds(nr, nc)) return false;
      const q = board[nr][nc];
      return !q || q.color !== color;
    };

    switch (piece.type) {
      case 'king': {
        const palaceRows = color === RED ? [7, 8, 9] : [0, 1, 2];
        const palaceCols = [3, 4, 5];
        for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
          const nr = r + dr, nc = c + dc;
          if (palaceRows.includes(nr) && palaceCols.includes(nc) && emptyOrEnemy(nr, nc))
            moves.push([nr, nc]);
        }
        break;
      }
      case 'advisor': {
        const palaceRows = color === RED ? [7, 8, 9] : [0, 1, 2];
        const palaceCols = [3, 4, 5];
        for (const [dr, dc] of [[-1, -1], [-1, 1], [1, -1], [1, 1]]) {
          const nr = r + dr, nc = c + dc;
          if (palaceRows.includes(nr) && palaceCols.includes(nc) && emptyOrEnemy(nr, nc))
            moves.push([nr, nc]);
        }
        break;
      }
      case 'elephant': {
        const canGo = color === RED ? (nr) => nr >= 5 : (nr) => nr <= 4;
        for (const [dr, dc] of [[-2, -2], [-2, 2], [2, -2], [2, 2]]) {
          const nr = r + dr, nc = c + dc;
          if (!inBounds(nr, nc) || !canGo(nr)) continue;
          const er = r + (dr > 0 ? 1 : -1), ec = c + (dc > 0 ? 1 : -1);
          if (board[er][ec]) continue;
          if (emptyOrEnemy(nr, nc)) moves.push([nr, nc]);
        }
        break;
      }
      case 'horse': {
        const legs = [[-2, -1, -1, 0], [-2, 1, -1, 0], [2, -1, 1, 0], [2, 1, 1, 0],
          [-1, -2, 0, -1], [-1, 2, 0, 1], [1, -2, 0, -1], [1, 2, 0, 1]];
        for (const [dr, dc, lr, lc] of legs) {
          const lr0 = r + lr, lc0 = c + lc;
          if (!inBounds(lr0, lc0) || board[lr0][lc0]) continue;
          const nr = r + dr, nc = c + dc;
          if (inBounds(nr, nc) && emptyOrEnemy(nr, nc)) moves.push([nr, nc]);
        }
        break;
      }
      case 'rook':
        for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
          let nr = r + dr, nc = c + dc;
          while (inBounds(nr, nc)) {
            if (!board[nr][nc]) moves.push([nr, nc]);
            else { if (board[nr][nc].color !== color) moves.push([nr, nc]); break; }
            nr += dr; nc += dc;
          }
        }
        break;
      case 'cannon':
        for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
          let nr = r + dr, nc = c + dc;
          let jumped = false;
          while (inBounds(nr, nc)) {
            if (!jumped) {
              if (!board[nr][nc]) moves.push([nr, nc]);
              else jumped = true;
            } else {
              if (board[nr][nc]) {
                if (board[nr][nc].color !== color) moves.push([nr, nc]);
                break;
              }
            }
            nr += dr; nc += dc;
          }
        }
        break;
      case 'pawn':
        if (color === RED) {
          if (r > 0 && emptyOrEnemy(r - 1, c)) moves.push([r - 1, c]);
          if (r <= 4) {
            if (emptyOrEnemy(r, c - 1)) moves.push([r, c - 1]);
            if (emptyOrEnemy(r, c + 1)) moves.push([r, c + 1]);
          }
        } else {
          if (r < 9 && emptyOrEnemy(r + 1, c)) moves.push([r + 1, c]);
          if (r >= 5) {
            if (emptyOrEnemy(r, c - 1)) moves.push([r, c - 1]);
            if (emptyOrEnemy(r, c + 1)) moves.push([r, c + 1]);
          }
        }
        break;
    }
    return moves;
  }

  function renderBoard() {
    boardEl.innerHTML = '';
    if (!state.board) return;
    const grid = document.createElement('div');
    grid.className = 'board-grid';
    for (let r = 0; r < 10; r++) {
      for (let c = 0; c < 9; c++) {
        const cell = document.createElement('div');
        cell.className = 'cell';
        cell.dataset.row = r;
        cell.dataset.col = c;
        const piece = state.board[r][c];
        if (piece) {
          const span = document.createElement('span');
          span.className = 'piece ' + piece.color;
          span.textContent = PIECE_CHAR[piece.color][piece.type];
          cell.appendChild(span);
        }
        if (state.selected && state.selected[0] === r && state.selected[1] === c) {
          cell.classList.add('selected');
        }
        if (state.legalMoves.some(m => m[0] === r && m[1] === c)) {
          cell.classList.add('highlight');
        }
        cell.addEventListener('click', () => onCellClick(r, c));
        grid.appendChild(cell);
      }
    }
    boardEl.appendChild(grid);
    const overlay = document.createElement('div');
    overlay.className = 'board-river-overlay';
    overlay.setAttribute('aria-hidden', 'true');
    const riverTop = document.createElement('span');
    riverTop.className = 'river-label top';
    riverTop.textContent = '楚 河';
    const riverBottom = document.createElement('span');
    riverBottom.className = 'river-label bottom';
    riverBottom.textContent = '汉 界';
    overlay.appendChild(riverTop);
    overlay.appendChild(riverBottom);
    boardEl.appendChild(overlay);
    updateStatus();
  }

  function updateStatus() {
    if (state.gameOver) {
      if (state.winner === 'draw') statusEl.textContent = '和棋';
      else if (state.winner === RED) statusEl.textContent = '红方胜';
      else statusEl.textContent = '黑方胜';
      statusEl.classList.add('winner');
      return;
    }
    statusEl.classList.remove('winner');
    const turnText = state.turn === RED ? '红方' : '黑方';
    const aiNote = (state.turn === RED && state.redIsAi) || (state.turn === BLACK && !state.redIsAi) ? ' (AI 思考中…)' : '';
    statusEl.textContent = turnText + '走棋' + aiNote;
  }

  function onCellClick(r, c) {
    if (state.gameOver) return;
    const isAiTurn = (state.turn === RED && state.redIsAi) || (state.turn === BLACK && !state.redIsAi);
    if (isAiTurn) return;

    const piece = state.board[r][c];
    if (state.selected) {
      const [sr, sc] = state.selected;
      const moveTo = state.legalMoves.find(m => m[0] === r && m[1] === c);
      if (moveTo) {
        submitMove(sr, sc, r, c);
        return;
      }
      if (piece && piece.color === state.turn) {
        state.selected = [r, c];
        state.legalMoves = getMovesForPiece(state.board, r, c);
      } else {
        state.selected = null;
        state.legalMoves = [];
      }
    } else {
      if (piece && piece.color === state.turn) {
        state.selected = [r, c];
        state.legalMoves = getMovesForPiece(state.board, r, c);
      }
    }
    renderBoard();
  }

  function submitMove(fromR, fromC, toR, toC) {
    fetch(API_BASE + '/api/game/' + state.gameId + '/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: [fromR, fromC], to: [toR, toC] }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          statusEl.textContent = data.error;
          return;
        }
        playMoveSound();
        state.board = data.board;
        state.turn = data.turn;
        state.selected = null;
        state.legalMoves = [];
        if (data.game_over) {
          state.gameOver = true;
          state.winner = data.winner;
        }
        if (data.ai_move) {
          state.board = data.board;
          state.turn = data.turn;
          if (data.game_over) {
            state.gameOver = true;
            state.winner = data.winner;
          }
          playMoveSound();
        }
        renderBoard();
      })
      .catch(() => {
        statusEl.textContent = '请求失败';
      });
  }

  function startNewGame() {
    const difficulty = difficultyEl.value;
    const blackIsAi = blackIsAiEl.checked;
    const redIsAi = !blackIsAi;
    fetch(API_BASE + '/api/game/new', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ difficulty, red_is_ai: redIsAi }),
    })
      .then(res => res.json())
      .then(data => {
        state.gameId = data.game_id;
        state.board = data.board;
        state.turn = data.turn;
        state.difficulty = data.difficulty;
        state.redIsAi = data.red_is_ai;
        state.selected = null;
        state.legalMoves = [];
        state.gameOver = false;
        state.winner = null;
        renderBoard();
        if (state.redIsAi && state.turn === RED) {
          fetch(API_BASE + '/api/game/' + state.gameId + '/ai_move', { method: 'POST' })
            .then(r => r.json())
            .then(d => {
              if (d.board) {
                playMoveSound();
                state.board = d.board;
                state.turn = d.turn;
                if (d.game_over) { state.gameOver = true; state.winner = d.winner; }
                renderBoard();
              }
            })
            .catch(() => {});
        }
      })
      .catch(() => {
        statusEl.textContent = '创建对局失败';
      });
  }

  function openHistory() {
    historyPanel.classList.remove('hidden');
    fetch(API_BASE + '/api/history')
      .then(res => res.json())
      .then(data => {
        historyList.innerHTML = '';
        (data.records || []).forEach(rec => {
          const li = document.createElement('li');
          const resultText = rec.winner === 'red' ? '红胜' : rec.winner === 'black' ? '黑胜' : '和棋';
          const resultClass = rec.winner === 'red' ? 'red' : rec.winner === 'black' ? 'black' : 'draw';
          const diffText = { normal: '普通', hard: '困难', hell: '地狱' }[rec.difficulty] || rec.difficulty;
          li.innerHTML = '<span class="result ' + resultClass + '">' + resultText + '</span>' +
            '<span class="meta">' + diffText + ' · ' + (rec.moves_count || 0) + ' 步</span>';
          li.addEventListener('click', () => showHistoryDetail(rec.id));
          historyList.appendChild(li);
        });
      })
      .catch(() => {});
  }

  function showHistoryDetail(id) {
    fetch(API_BASE + '/api/history/' + id)
      .then(res => res.json())
      .then(data => {
        if (data.error) return;
        const snapshots = data.board_snapshots || [];
        state.board = snapshots.length ? snapshots[snapshots.length - 1] : null;
        state.gameId = null;
        state.gameOver = true;
        state.winner = data.winner || null;
        state.selected = null;
        state.legalMoves = [];
        renderBoard();
        historyPanel.classList.add('hidden');
      })
      .catch(() => {});
  }

  btnNewGame.addEventListener('click', startNewGame);
  btnHistory.addEventListener('click', openHistory);
  btnCloseHistory.addEventListener('click', () => historyPanel.classList.add('hidden'));

  startNewGame();
})();
