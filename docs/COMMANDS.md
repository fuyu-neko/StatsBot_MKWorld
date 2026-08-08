# Commands Reference

[English](#english) | [日本語](#日本語)

---

## English

All commands are Discord slash commands. Players can be looked up by **lounge name**, **Discord ID**, **MKC ID**, or **Friend Code**. When a name parameter is omitted, the caller's Discord ID is used.

One bot process serves one lounge, selected by `GAME` in `.env`. MK8DX has a single 12p ladder, so the `game_mode` parameter is not offered there, and stats are available from **season 4** onwards.

### Public Commands

#### `/mmr`
Show MKWorld Player MMR.

| Parameter | Required | Description |
|---|---|---|
| `names` | No | Comma-separated list of player names, Discord IDs, or MKC IDs |
| `season` | No | Season number (default: current season) |
| `game_mode` | No | `24p` or `12p` (default: `24p`). MKWorld only — not shown when `GAME=mk8dx` |

#### `/stats`
Show detailed player statistics with an MMR history chart.

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Lounge name, Discord ID, or MKC ID |
| `season` | No | Season number (default: current season) |
| `game_mode` | No | `24p` or `12p` (default: `24p`). MKWorld only — not shown when `GAME=mk8dx` |

#### `/lastmatch`
Show a player's most recent verified match.

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Lounge name, Discord ID, or MKC ID |
| `game_mode` | No | `24p` or `12p` (default: the most recent match across both). MKWorld only — not shown when `GAME=mk8dx` |

#### `/table`
Show details for a specific match.

| Parameter | Required | Description |
|---|---|---|
| `table_id` | Yes | Table ID |

#### `/namelog`
View a player's name change history.

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Player name, Discord ID, or MKC ID |

#### `/fc`
Show a player's Nintendo Switch Friend Code.

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Player name, Discord ID, or MKC ID |

#### `/tiers`
Show a player's performance broken down by tier.

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Lounge name, Discord ID, or MKC ID |
| `season` | No | Season number (default: current season) |
| `game_mode` | No | `24p` or `12p` (default: `24p`). MKWorld only — not shown when `GAME=mk8dx` |

#### `/fs`
Show a player's performance broken down by format (FFA, 2v2, 3v3, 4v4, 6v6, 8v8, 12v12).

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Lounge name, Discord ID, or MKC ID |
| `season` | No | Season number (default: current season) |
| `game_mode` | No | `24p` or `12p` (default: `24p`). MKWorld only — not shown when `GAME=mk8dx` |

#### `/h2h`
Compare two players' shared matches (head-to-head).

| Parameter | Required | Description |
|---|---|---|
| `name1` | Yes | First player (lounge name, Discord ID, or MKC ID) |
| `name2` | No | Second player (defaults to you) |
| `season` | No | Season number (default: current season) |
| `game_mode` | No | `24p` or `12p` (default: `24p`). MKWorld only — not shown when `GAME=mk8dx` |

#### `/scores`
Show a player's score breakdown.

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Lounge name, Discord ID, or MKC ID |
| `season` | No | Season number (default: current season) |
| `game_mode` | No | `24p` or `12p` (default: `24p`). MKWorld only — not shown when `GAME=mk8dx` |
| `tier` | No | Filter by tier (default: all tiers) |
| `last` | No | Limit to the last N matches (default: all) |
| `show_partner_scores` | No | Overlay partner scores on the plot (`Yes`/`No`, default: `No`) |

#### `/calc`
Calculate expected MMR changes for a specific match.

| Parameter | Required | Description |
|---|---|---|
| `table_id` | Yes | Table ID for the match |

#### `/streak`
Show a player's win/loss streaks.

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Lounge name, Discord ID, or MKC ID |
| `season` | No | Season number (default: current season) |
| `game_mode` | No | `24p` or `12p` (default: `24p`). MKWorld only — not shown when `GAME=mk8dx` |

#### `/dd`
Show events played and net MMR per day over the last 14 days.

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Lounge name, Discord ID, or MKC ID |
| `season` | No | Season number (default: current season) |
| `game_mode` | No | `24p` or `12p` (default: `24p`). MKWorld only — not shown when `GAME=mk8dx` |
| `timezone` | No | Timezone abbreviation, e.g. `EST`, `JST` (default: `UTC`) |

#### `/wd`
Show events played and net MMR per week (Mon–Sun) for the season.

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Lounge name, Discord ID, or MKC ID |
| `season` | No | Season number (default: current season) |
| `game_mode` | No | `24p` or `12p` (default: `24p`). MKWorld only — not shown when `GAME=mk8dx` |
| `timezone` | No | Timezone abbreviation, e.g. `EST`, `JST` (default: `UTC`) |

#### `/md`
Show events played and net MMR per month for the season.

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Lounge name, Discord ID, or MKC ID |
| `season` | No | Season number (default: current season) |
| `game_mode` | No | `24p` or `12p` (default: `24p`). MKWorld only — not shown when `GAME=mk8dx` |
| `timezone` | No | Timezone abbreviation, e.g. `EST`, `JST` (default: `UTC`) |

### Staff Commands

These commands require the role specified by `Mods_Role_ID` in `.env`.

#### `/data`
Display raw player data (MKC ID, Discord ID, country code, hidden flag).

| Parameter | Required | Description |
|---|---|---|
| `name` | No | Player name, Discord ID, or MKC ID |

---

## 日本語

すべて Discord スラッシュコマンドです。プレイヤーは **ラウンジ名**、**Discord ID**、**MKC ID**、**フレンドコード** で検索できます。`name` 系パラメータを省略した場合、コマンド実行者の Discord ID が使用されます。

1 つの Bot プロセスは 1 つのラウンジのみを担当し、`.env` の `GAME` で選択します。MK8DX は 12p の単一ラダーのため `game_mode` パラメータは表示されず、対応シーズンは **シーズン 4 以降** です。

### 一般コマンド

#### `/mmr`
プレイヤーの MMR を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `names` | No | プレイヤー名・Discord ID・MKC ID のカンマ区切りリスト |
| `season` | No | シーズン番号（デフォルト: 現在のシーズン） |
| `game_mode` | No | `24p` または `12p`（デフォルト: `24p`）。MKWorld 専用で、`GAME=mk8dx` では表示されません |

#### `/stats`
MMR 推移グラフ付きの詳細なプレイヤー統計情報を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | ラウンジ名・Discord ID・MKC ID |
| `season` | No | シーズン番号（デフォルト: 現在のシーズン） |
| `game_mode` | No | `24p` または `12p`（デフォルト: `24p`）。MKWorld 専用で、`GAME=mk8dx` では表示されません |

#### `/lastmatch`
プレイヤーの直近のアップデート済み試合を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | ラウンジ名・Discord ID・MKC ID |
| `game_mode` | No | `24p` または `12p`（デフォルト: 両モードのうち最も新しい試合）。MKWorld 専用で、`GAME=mk8dx` では表示されません |

#### `/table`
特定の試合の詳細を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `table_id` | Yes | テーブル ID |

#### `/namelog`
プレイヤーの名前変更履歴を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | プレイヤー名・Discord ID・MKC ID |

#### `/fc`
プレイヤーの Nintendo Switch フレンドコードを表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | プレイヤー名・Discord ID・MKC ID |

#### `/tiers`
プレイヤーのティア別パフォーマンスを表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | ラウンジ名・Discord ID・MKC ID |
| `season` | No | シーズン番号（デフォルト: 現在のシーズン） |
| `game_mode` | No | `24p` または `12p`（デフォルト: `24p`）。MKWorld 専用で、`GAME=mk8dx` では表示されません |

#### `/fs`
プレイヤーのフォーマット別（FFA・2v2・3v3・4v4・6v6・8v8・12v12）パフォーマンスを表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | ラウンジ名・Discord ID・MKC ID |
| `season` | No | シーズン番号（デフォルト: 現在のシーズン） |
| `game_mode` | No | `24p` または `12p`（デフォルト: `24p`）。MKWorld 専用で、`GAME=mk8dx` では表示されません |

#### `/h2h`
2 人のプレイヤーが同席した試合を比較。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name1` | Yes | 1 人目のプレイヤー（ラウンジ名・Discord ID・MKC ID） |
| `name2` | No | 2 人目のプレイヤー（省略時は実行者） |
| `season` | No | シーズン番号（デフォルト: 現在のシーズン） |
| `game_mode` | No | `24p` または `12p`（デフォルト: `24p`）。MKWorld 専用で、`GAME=mk8dx` では表示されません |

#### `/scores`
プレイヤーのスコア内訳を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | ラウンジ名・Discord ID・MKC ID |
| `season` | No | シーズン番号（デフォルト: 現在のシーズン） |
| `game_mode` | No | `24p` または `12p`（デフォルト: `24p`）。MKWorld 専用で、`GAME=mk8dx` では表示されません |
| `tier` | No | 特定ティアでフィルタ（デフォルト: 全ティア） |
| `last` | No | 直近 N 試合に限定（デフォルト: 全試合） |
| `show_partner_scores` | No | パートナーのスコアをグラフに重ねて表示（`Yes`/`No`、デフォルト: `No`） |

#### `/calc`
特定の試合における予想 MMR 変動を計算。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `table_id` | Yes | 試合のテーブル ID |

#### `/streak`
プレイヤーの連勝・連敗を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | ラウンジ名・Discord ID・MKC ID |
| `season` | No | シーズン番号（デフォルト: 現在のシーズン） |
| `game_mode` | No | `24p` または `12p`（デフォルト: `24p`）。MKWorld 専用で、`GAME=mk8dx` では表示されません |

#### `/dd`
直近 14 日間の日ごとの試合数と MMR 増減を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | ラウンジ名・Discord ID・MKC ID |
| `season` | No | シーズン番号（デフォルト: 現在のシーズン） |
| `game_mode` | No | `24p` または `12p`（デフォルト: `24p`）。MKWorld 専用で、`GAME=mk8dx` では表示されません |
| `timezone` | No | タイムゾーン略称（例: `EST`, `JST`、デフォルト: `UTC`） |

#### `/wd`
シーズン中の週（月〜日）ごとの試合数と MMR 増減を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | ラウンジ名・Discord ID・MKC ID |
| `season` | No | シーズン番号（デフォルト: 現在のシーズン） |
| `game_mode` | No | `24p` または `12p`（デフォルト: `24p`）。MKWorld 専用で、`GAME=mk8dx` では表示されません |
| `timezone` | No | タイムゾーン略称（例: `EST`, `JST`、デフォルト: `UTC`） |

#### `/md`
シーズン中の月ごとの試合数と MMR 増減を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | No | ラウンジ名・Discord ID・MKC ID |
| `season` | No | シーズン番号（デフォルト: 現在のシーズン） |
| `game_mode` | No | `24p` または `12p`（デフォルト: `24p`）。MKWorld 専用で、`GAME=mk8dx` では表示されません |
| `timezone` | No | タイムゾーン略称（例: `EST`, `JST`、デフォルト: `UTC`） |

### スタッフコマンド

`.env` の `Mods_Role_ID` で指定したロールが必要です。

#### `/data`
プレイヤーの生データ（MKC ID、Discord ID、国コード、Hidden フラグなど）を表示。

| パラメータ | 必須 | 説明 |
|---|---|---|
| `name` | いいえ | プレイヤー名・Discord ID・MKC ID |
