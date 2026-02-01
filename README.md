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

## 推送到 GitHub

本地已提交，只需在本机终端完成认证后执行 `git push`。

**方式一：SSH（推荐）**

1. 若尚未配置 SSH 公钥：`ssh-keygen -t ed25519 -C "你的邮箱" -f ~/.ssh/id_ed25519 -N ""`
2. 查看公钥：`cat ~/.ssh/id_ed25519.pub`
3. 在 GitHub：**Settings → SSH and GPG keys → New SSH key**，粘贴公钥并保存
4. 在项目目录执行：`git push -u origin main`

**方式二：HTTPS + Personal Access Token**

1. 在 GitHub：**Settings → Developer settings → Personal access tokens** 生成一个 token（勾选 `repo`）
2. 在项目目录执行：`git remote set-url origin https://github.com/cqm0052/cc-game.git`，再执行 `git push -u origin main`
3. 用户名填 GitHub 用户名，密码处粘贴上述 token

## 部署到 Railway

项目已配置 `Procfile` 与 `gunicorn`，可按以下步骤部署。

**若控制台显示 “No service”**：说明还没有部署过，需要先在终端执行第 3 步 `railway up`，部署成功后控制台里会出现服务。

1. **登录**（会打开浏览器）：  
   `railway login`

2. **初始化并关联项目**（首次选 “Create new project”）：  
   `railway init`

3. **部署**（这一步会创建服务并上传代码，必须执行）：  
   `railway up`

4. **生成公网域名**：  
   Railway 控制台 https://railway.app → 你的项目 → 出现的服务 → Settings → Networking → Generate Domain

部署完成后用生成的域名访问即可（对战历史在 Railway 上为内存/临时存储，重启会清空）。
