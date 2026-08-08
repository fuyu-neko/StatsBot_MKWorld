from common.ranks import BAND_COLORS, RANK_ORDER

MIN_SEASON = 1

_MMR_DEFINITIONS = {
    "12p": {
        1: [0, 2000, 3500, 5000, 6500, 8000, 9500, 11000, 12500, 13500],
        2: [0, 2000, 4000, 6000, 7500, 9000, 10500, 12000, 13500, 14500],
        3: [0, 2000, 4000, 6000, 8000, 9500, 11000, 12500, 14000, 15000],
    },
    "24p": {
        1: [0, 2000, 3500, 5000, 6500, 8000, 9500, 11000, 12500, 13500],
        2: [0, 2000, 4000, 6000, 8000, 10000, 11500, 13000, 14500, 15500],
    },
}

_COLORS = [BAND_COLORS[name] for name in RANK_ORDER]


def get_mmr_definition(season: int, game_mode: str) -> list[int]:
    definitions = _MMR_DEFINITIONS.get(game_mode, _MMR_DEFINITIONS["24p"])
    latest = max(definitions)
    return definitions[min(max(season, MIN_SEASON), latest)]


def get_rank(mmr: int, season: int, game_mode: str) -> str:
    if season == 0 or game_mode not in _MMR_DEFINITIONS:
        return "Placement"

    thresholds = get_mmr_definition(season, game_mode)
    for name, lower_bound in zip(reversed(RANK_ORDER), reversed(thresholds)):
        if mmr >= lower_bound:
            return name
    return RANK_ORDER[0]


def get_mmr_colors(season: int, game_mode: str) -> list[str]:
    return _COLORS


def get_subrank_lines(season: int, game_mode: str) -> list[int]:
    return []
