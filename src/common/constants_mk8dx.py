from common.ranks import BAND_COLORS

MIN_SEASON = 4

# Lower bound of every rank the API can report, lowest first.
_S4_RANKS = [
    (0, "Iron"),
    (4000, "Bronze"),
    (5500, "Silver"),
    (7000, "Gold"),
    (8500, "Platinum"),
    (10000, "Sapphire"),
    (11500, "Diamond"),
    (13000, "Master"),
    (14500, "Grandmaster"),
]

_S5_RANKS = [
    (0, "Iron 1"),
    (1000, "Iron 2"),
    (2000, "Bronze 1"),
    (3000, "Bronze 2"),
    (4000, "Silver 1"),
    (5000, "Silver 2"),
    (6000, "Gold 1"),
    (7000, "Gold 2"),
    (8000, "Platinum 1"),
    (9000, "Platinum 2"),
    (10000, "Sapphire"),
    (11000, "Diamond 1"),
    (12000, "Diamond 2"),
    (13000, "Master"),
    (14000, "Grandmaster"),
]

_S6_RANKS = [
    (0, "Iron 1"),
    (1000, "Iron 2"),
    (2000, "Bronze 1"),
    (3000, "Bronze 2"),
    (4000, "Silver 1"),
    (5000, "Silver 2"),
    (6000, "Gold 1"),
    (7000, "Gold 2"),
    (8000, "Platinum 1"),
    (9000, "Platinum 2"),
    (10000, "Sapphire 1"),
    (11000, "Sapphire 2"),
    (12000, "Diamond 1"),
    (13000, "Diamond 2"),
    (14000, "Master"),
    (15000, "Grandmaster"),
]

_S8_RANKS = [
    (0, "Iron 1"),
    (1000, "Iron 2"),
    (2000, "Bronze 1"),
    (3000, "Bronze 2"),
    (4000, "Silver 1"),
    (5000, "Silver 2"),
    (6000, "Gold 1"),
    (7000, "Gold 2"),
    (8000, "Platinum 1"),
    (9000, "Platinum 2"),
    (10000, "Sapphire 1"),
    (11000, "Sapphire 2"),
    (12000, "Ruby 1"),
    (13000, "Ruby 2"),
    (14000, "Diamond 1"),
    (15000, "Diamond 2"),
    (16000, "Master"),
    (17000, "Grandmaster"),
]

_S4_BANDS = [
    "Iron",
    "Bronze",
    "Silver",
    "Gold",
    "Platinum",
    "Sapphire",
    "Diamond",
    "Master",
    "Grandmaster",
]
_S8_BANDS = [
    "Iron",
    "Bronze",
    "Silver",
    "Gold",
    "Platinum",
    "Sapphire",
    "Ruby",
    "Diamond",
    "Master",
    "Grandmaster",
]

_SEASONS = {
    4: {"ranks": _S4_RANKS, "bands": _S4_BANDS},
    5: {"ranks": _S5_RANKS, "bands": _S4_BANDS},
    6: {"ranks": _S6_RANKS, "bands": _S4_BANDS},
    8: {"ranks": _S8_RANKS, "bands": _S8_BANDS},
}


def _season_data(season: int) -> dict:
    season = max(season, MIN_SEASON)
    key = max(k for k in _SEASONS if k <= season)
    return _SEASONS[key]


def _base_rank(rank_name: str) -> str:
    return rank_name.split()[0]


def get_mmr_definition(season: int, game_mode: str) -> list[int]:
    """Lower bound of each coloured band, lowest first."""
    data = _season_data(season)
    lowest = {}
    for lower_bound, name in data["ranks"]:
        lowest.setdefault(_base_rank(name), lower_bound)
    return [lowest[name] for name in data["bands"]]


def get_rank(mmr: int, season: int, game_mode: str) -> str:
    if season < MIN_SEASON:
        return "Placement"

    ranks = _season_data(season)["ranks"]
    for lower_bound, name in reversed(ranks):
        if mmr >= lower_bound:
            return name
    return ranks[0][1]


def get_mmr_colors(season: int, game_mode: str) -> list[str]:
    return [BAND_COLORS[name] for name in _season_data(season)["bands"]]


def get_subrank_lines(season: int, game_mode: str) -> list[int]:
    """MMR values where a band is split into sub-ranks, e.g. Iron 1 / Iron 2."""
    data = _season_data(season)
    seen = set()
    lines = []
    for lower_bound, name in data["ranks"]:
        base = _base_rank(name)
        if base in seen:
            lines.append(lower_bound)
        seen.add(base)
    return lines
