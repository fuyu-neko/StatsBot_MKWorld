# StatsBot_MKWorld

[English](#english) | [日本語](#日本語)

---

## English

A Discord bot that provides player statistics and Mogi data for **Mario Kart World** via the [MKCentral Lounge API](https://github.com/VikeMK/Lounge-API).

### Features

Players can be looked up by **lounge name**, **Discord ID**, **MKC ID**, or **Friend Code**.

**Public commands**

| Command | Description |
|---|---|
| `/mmr` | Display MMR for one or more players |
| `/stats` | Show detailed statistics with an MMR history chart |
| `/lastmatch` | View a player's most recent match |
| `/table` | Look up a specific match by Table ID |
| `/fc` | Retrieve a player's Nintendo Switch Friend Code |
| `/namelog` | View a player's name change history |
| `/tiers` | Show performance broken down by tier |
| `/h2h` | Compare two players' shared matches (head-to-head) |
| `/scores` | Show a player's score breakdown |
| `/calc` | Calculate expected MMR changes for a specific match |
| `/streak` | Show a player's win/loss streaks |

**Staff commands** (require the role configured by `Mods_Role_ID`)

| Command | Description |
|---|---|
| `/data` | Display raw player data |

See [docs/COMMANDS.md](./docs/COMMANDS.md) for full parameter details.

### Documentation

- **[docs/COMMANDS.md](./docs/COMMANDS.md)** — full command reference with all parameters
- **[docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)** — server deployment workflow (initial setup, routine deploy, rollback)

### Prerequisites

- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))

### Quick Start

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

### Environment Variables

Create a `.env` file in the project root with the following:

```env
ENVIRONMENT=staging
DISCORD_BOT_TOKEN_STAGING=your_discord_bot_token_for_staging
DISCORD_BOT_TOKEN_PRODUCTION=your_discord_bot_token_for_production
CURRENT_SEASON=2
WEBSITE_URL=https://lounge.mkcentral.com
MKCentral_Site_URL=https://mkcentral.com
DEBUG_MODE=True
Mods_Server_ID=your_server_id
Mods_Role_ID=your_mod_role_id
```

| Variable | Description |
|---|---|
| `GAME` | Which lounge this process serves: `mkworld` or `mk8dx` (default: `mkworld`) |
| `ENVIRONMENT` | Selects which token to use: `staging` or `production` |
| `DISCORD_BOT_TOKEN_STAGING` | Discord bot token used when `ENVIRONMENT=staging` |
| `DISCORD_BOT_TOKEN_PRODUCTION` | Discord bot token used when `ENVIRONMENT=production` |
| `CURRENT_SEASON` | Current season number of the selected lounge (MK8DX is supported from season 4) |
| `WEBSITE_URL` | MKCentral Lounge API base URL |
| `MKCentral_Site_URL` | MKCentral website URL |
| `DEBUG_MODE` | Enable debug logging (`True`/`False`) |
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

### Disclaimer

This is an unofficial tool. "Mario Kart" is a trademark of Nintendo. This project is **not affiliated with, endorsed by, or sponsored by Nintendo**. The bot relies on the public [MKCentral Lounge API](https://github.com/VikeMK/Lounge-API). Use this software at your own risk.

### License

This project is licensed under the [MIT License](LICENSE).

---

## 日本語

[MKCentral Lounge API](https://github.com/VikeMK/Lounge-API) を利用して、**マリオカートワールド** のプレイヤー統計情報や模擬データを提供する Discord Bot です。

### 機能

プレイヤーは **ラウンジ名**、**Discord ID**、**MKC ID**、**フレンドコード** で検索できます。

**一般コマンド**

| コマンド | 説明 |
|---|---|
| `/mmr` | 1 人または複数プレイヤーの MMR を表示 |
| `/stats` | MMR 推移グラフ付きの詳細な統計情報を表示 |
| `/lastmatch` | プレイヤーの直近の試合を表示 |
| `/table` | テーブル ID で特定の試合を検索 |
| `/fc` | プレイヤーの Nintendo Switch フレンドコードを取得 |
| `/namelog` | プレイヤーの名前変更履歴を表示 |
| `/tiers` | ティア別のパフォーマンスを表示 |
| `/h2h` | 指定したプレイヤー間の戦績を表示 |
| `/scores` | プレイヤーのスコア内訳を表示 |
| `/calc` | テーブル ID を指定して、予想される MMR 変動を計算 |
| `/streak` | プレイヤーの連勝・連敗を表示 |

**スタッフコマンド**（`Mods_Role_ID` で指定したロールが必要）

| コマンド | 説明 |
|---|---|
| `/data` | プレイヤーの生データを表示 |

各コマンドのパラメータ詳細は [docs/COMMANDS.md](./docs/COMMANDS.md) を参照してください。

### ドキュメント

- **[docs/COMMANDS.md](./docs/COMMANDS.md)** — 全コマンドのパラメータを含む詳細リファレンス
- **[docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)** — サーバーデプロイ運用（初期セットアップ、通常デプロイ、ロールバック）

### 前提条件

- Python 3.13 以上
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Discord Bot トークン（[Discord Developer Portal](https://discord.com/developers/applications)）

### クイックスタート

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

### 環境変数

プロジェクトルートに `.env` ファイルを作成し、以下の値を設定してください。

```env
ENVIRONMENT=staging
DISCORD_BOT_TOKEN_STAGING=your_discord_bot_token_for_staging
DISCORD_BOT_TOKEN_PRODUCTION=your_discord_bot_token_for_production
CURRENT_SEASON=2
WEBSITE_URL=https://lounge.mkcentral.com
MKCentral_Site_URL=https://mkcentral.com
DEBUG_MODE=True
Mods_Role_ID=your_mod_role_id
```

| 変数名 | 説明 |
|---|---|
| `GAME` | このプロセスが担当するラウンジ: `mkworld` または `mk8dx`（デフォルト: `mkworld`） |
| `ENVIRONMENT` | 使用するトークンを選択（`staging` または `production`） |
| `DISCORD_BOT_TOKEN_STAGING` | `ENVIRONMENT=staging` のときに使用される Discord Bot トークン |
| `DISCORD_BOT_TOKEN_PRODUCTION` | `ENVIRONMENT=production` のときに使用される Discord Bot トークン |
| `CURRENT_SEASON` | 選択したラウンジの現在のシーズン番号（MK8DX はシーズン 4 以降に対応） |
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

### 免責事項

これは非公式のツールです。「マリオカート」は Nintendo の商標です。本プロジェクトは **Nintendo と提携しておらず、Nintendo から推奨・後援も受けていません**。本 Bot は公開されている [MKCentral Lounge API](https://github.com/VikeMK/Lounge-API) を利用しています。本ソフトウェアは自己責任でご利用ください。

### ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。
