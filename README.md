# StatsBot_MKWorld

[English](#english) | [日本語](#日本語)

---

## English

### Overview

A Discord bot that provides player statistics and Mogi data for **Mario Kart World** via the [MKCentral Lounge API](https://github.com/VikeMK/Lounge-API).

#### Features

- `/mmr` — Display MMR (Matchmaking Rating) for one or more players
- `/stats` — Show detailed statistics with an MMR history chart
- `/lastmatch` — View a player's most recent match
- `/table` — Look up a specific match by Table ID
- `/fc` — Retrieve a player's Nintendo Switch Friend Code
- `/namelog` — View a player's name change history
- `/calc` — Calculate expected MMR changes for a specific match by Table ID

Players can be looked up by name, MKC ID, Discord ID, or Friend Code.

#### Prerequisites

- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))

#### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/StatsBot_MKWorld.git
cd StatsBot_MKWorld

# Install dependencies
uv sync

# Create .env file
cp .env.example .env
# Edit .env and set your values (see below)

# Run the bot
uv run src/main.py
```

#### Environment Variables

Create a `.env` file in the project root with the following:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
CURRENT_SEASON=2
WEBSITE_URL=https://lounge.mkcentral.com
MKCentral_Site_URL=https://mkcentral.com
DEBUG_MODE=True
Mods_Server_ID=your_server_id
Mods_Role_ID=your_mod_role_id
```

| Variable | Description |
|---|---|
| `DISCORD_BOT_TOKEN` | Your Discord bot token |
| `CURRENT_SEASON` | Current MKWorld Lounge season number |
| `WEBSITE_URL` | MKCentral Lounge API base URL |
| `MKCentral_Site_URL` | MKCentral website URL |
| `DEBUG_MODE` | Enable debug logging (`True`/`False`) |
| `Mods_Server_ID` | Discord server ID for staff commands |
| `Mods_Role_ID` | Discord role ID for staff permissions |

### Development

```bash
# Run linter
uv run ruff check src/

# Run tests
uv run pytest

# Run pre-commit hooks
uv run pre-commit run --all-files
```

### License

This project is licensed under the [MIT License](LICENSE).

---

## 日本語

### 概要

[MKCentral Lounge API](https://github.com/VikeMK/Lounge-API) を利用して、
**マリオカートワールド** のプレイヤー統計情報や模擬データを提供する Discord Bot です。

#### 機能

- `/mmr` — 1人または複数プレイヤーの MMR（マッチメイキングレート）を表示
- `/stats` — MMR 推移グラフ付きの詳細な統計情報を表示
- `/lastmatch` — プレイヤーの直近の試合を表示
- `/table` — テーブル ID で特定の試合を検索
- `/fc` — プレイヤーの Nintendo Switch フレンドコードを取得
- `/namelog` — プレイヤーの名前変更履歴を表示
- `/calc` — テーブル ID を指定して、予想される MMR 変動を計算

プレイヤーは名前、MKC ID、Discord ID、フレンドコードで検索できます。

#### 前提条件

- Python 3.13 以上
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Discord Bot トークン（[Discord Developer Portal](https://discord.com/developers/applications)）

#### インストール

```bash
# リポジトリをクローン
git clone https://github.com/<your-username>/StatsBot_MKWorld.git
cd StatsBot_MKWorld

# 依存パッケージをインストール
uv sync

# .env ファイルを作成
cp .env.example .env
# .env を編集して値を設定（下記参照）

# Bot を起動
uv run src/main.py
```

#### 環境変数

プロジェクトルートに `.env` ファイルを作成し、以下の値を設定してください。

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
CURRENT_SEASON=2
WEBSITE_URL=https://lounge.mkcentral.com
MKCentral_Site_URL=https://mkcentral.com
DEBUG_MODE=True
Mods_Server_ID=your_server_id
Mods_Role_ID=your_mod_role_id
```

| 変数名 | 説明 |
|---|---|
| `DISCORD_BOT_TOKEN` | Discord Bot トークン |
| `CURRENT_SEASON` | 現在の MKWorld Lounge シーズン番号 |
| `WEBSITE_URL` | MKCentral Lounge API のベース URL |
| `MKCentral_Site_URL` | MKCentral ウェブサイトの URL |
| `DEBUG_MODE` | デバッグログの有効化（`True`/`False`） |
| `Mods_Server_ID` | スタッフコマンド用の Discord サーバー ID |
| `Mods_Role_ID` | スタッフ権限用の Discord ロール ID |

### 開発

```bash
# リンターの実行
uv run ruff check src/

# テストの実行
uv run pytest

# pre-commit フックの実行
uv run pre-commit run --all-files
```

### ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。
