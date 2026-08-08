from common import game_config as cfg
from common.ranks import RANK_DATA, RANK_ORDER, get_rank_info, rank_index

if cfg.GAME == cfg.MK8DX:
    from common import constants_mk8dx as _game
else:
    from common import constants_mkworld as _game

MIN_SEASON: int = _game.MIN_SEASON

get_rank = _game.get_rank
get_mmr_definition = _game.get_mmr_definition
get_mmr_colors = _game.get_mmr_colors
get_subrank_lines = _game.get_subrank_lines

__all__ = [
    "MIN_SEASON",
    "RANK_DATA",
    "RANK_ORDER",
    "format_mmr_delta",
    "get_country_flag",
    "get_mmr_colors",
    "get_mmr_definition",
    "get_rank",
    "get_rank_data",
    "get_rank_info",
    "get_subrank_lines",
    "rank_index",
]


def get_rank_data(season: int | None = None) -> dict:
    return RANK_DATA


def get_country_flag(code: str) -> str:
    if not code or len(code) != 2:
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def format_mmr_delta(delta: int) -> str:
    return f"+{delta}" if delta >= 0 else str(delta)
