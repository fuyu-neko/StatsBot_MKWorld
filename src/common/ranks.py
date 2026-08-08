"""Rank names and display data shared by every game.

MKCentral uses the same rank ladder and artwork for both lounges, so only the
MMR thresholds differ per game (see ``constants_mkworld`` / ``constants_mk8dx``).
"""

# Lowest to highest. Sub-rank suffixes ("Iron 1") are stripped before lookup.
RANK_ORDER = [
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

# Keyed by the rank name the API reports, including sub-rank variants.
RANK_DATA = {
    "Grandmaster": {"color": "#A3022C", "url": "https://i.imgur.com/EWXzu2U.png"},
    "Master": {"color": "#D9E1F2", "url": "https://i.imgur.com/3yBab63.png"},
    "Diamond 2": {"color": "#BDD7EE", "url": "https://i.imgur.com/RDlvdvA.png"},
    "Diamond 1": {"color": "#BDD7EE", "url": "https://i.imgur.com/RDlvdvA.png"},
    "Diamond": {"color": "#BDD7EE", "url": "https://i.imgur.com/RDlvdvA.png"},
    "Ruby 2": {"color": "#d51c5e", "url": "https://i.imgur.com/WU2NlJQ.png"},
    "Ruby 1": {"color": "#d51c5e", "url": "https://i.imgur.com/WU2NlJQ.png"},
    "Ruby": {"color": "#d51c5e", "url": "https://i.imgur.com/WU2NlJQ.png"},
    "Sapphire 2": {"color": "#286CD3", "url": "https://i.imgur.com/bXEfUSV.png"},
    "Sapphire 1": {"color": "#286CD3", "url": "https://i.imgur.com/bXEfUSV.png"},
    "Sapphire": {"color": "#286CD3", "url": "https://i.imgur.com/bXEfUSV.png"},
    "Platinum 2": {"color": "#3FABB8", "url": "https://i.imgur.com/8v8IjHE.png"},
    "Platinum 1": {"color": "#3FABB8", "url": "https://i.imgur.com/8v8IjHE.png"},
    "Platinum": {"color": "#3FABB8", "url": "https://i.imgur.com/8v8IjHE.png"},
    "Gold 2": {"color": "#FFD966", "url": "https://i.imgur.com/6yAatOq.png"},
    "Gold 1": {"color": "#FFD966", "url": "https://i.imgur.com/6yAatOq.png"},
    "Gold": {"color": "#FFD966", "url": "https://i.imgur.com/6yAatOq.png"},
    "Silver 2": {"color": "#D9D9D9", "url": "https://i.imgur.com/xgFyiYa.png"},
    "Silver 1": {"color": "#D9D9D9", "url": "https://i.imgur.com/xgFyiYa.png"},
    "Silver": {"color": "#D9D9D9", "url": "https://i.imgur.com/xgFyiYa.png"},
    "Bronze 2": {"color": "#C65911", "url": "https://i.imgur.com/DxFLvtO.png"},
    "Bronze 1": {"color": "#C65911", "url": "https://i.imgur.com/DxFLvtO.png"},
    "Bronze": {"color": "#C65911", "url": "https://i.imgur.com/DxFLvtO.png"},
    "Iron 2": {"color": "#817876", "url": "https://i.imgur.com/AYRMVEu.png"},
    "Iron 1": {"color": "#817876", "url": "https://i.imgur.com/AYRMVEu.png"},
    "Iron": {"color": "#817876", "url": "https://i.imgur.com/AYRMVEu.png"},
    "Placement": {"color": "#000000", "url": ""},
    "Ranked": {"color": "#000000", "url": ""},
}

UNKNOWN_RANK = {"color": "#000000", "url": ""}

# Fill colours for the MMR bands drawn behind a plot. Deliberately a different
# palette from RANK_DATA, which colours embeds.
BAND_COLORS = {
    "Iron": "#817876",
    "Bronze": "#E67E22",
    "Silver": "#7D8396",
    "Gold": "#F1C40F",
    "Platinum": "#3FABB8",
    "Sapphire": "#286CD3",
    "Ruby": "#d51c5e",
    "Diamond": "#9CCBD6",
    "Master": "#0E0B0B",
    "Grandmaster": "#A3022C",
}


def rank_index(rank_name: str) -> int:
    """Return rank order index, stripping sub-rank suffixes like '1'/'2'."""
    base = rank_name.split()[0] if rank_name else ""
    try:
        return RANK_ORDER.index(base)
    except ValueError:
        return -1


def get_rank_info(rank_name: str) -> dict:
    """Display data for an API-reported rank, tolerating unknown names."""
    if rank_name in RANK_DATA:
        return RANK_DATA[rank_name]
    base = rank_name.split()[0] if rank_name else ""
    return RANK_DATA.get(base, UNKNOWN_RANK)
