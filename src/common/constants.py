# contains the emoji ID and role ID for each rank in the server;
# rank names should match up with getRank function below
def get_rank_data(season: int):
    if season >= 0:
        ranks = {
            "Grandmaster": {
                "color": "#A3022C",
                "url": "https://i.imgur.com/EWXzu2U.png",
            },
            "Master": {"color": "#D9E1F2", "url": "https://i.imgur.com/3yBab63.png"},
            "Diamond 2": {"color": "#BDD7EE", "url": "https://i.imgur.com/RDlvdvA.png"},
            "Diamond 1": {"color": "#BDD7EE", "url": "https://i.imgur.com/RDlvdvA.png"},
            "Diamond": {"color": "#BDD7EE", "url": "https://i.imgur.com/RDlvdvA.png"},
            "Ruby 2": {"color": "#d51c5e", "url": "https://i.imgur.com/WU2NlJQ.png"},
            "Ruby 1": {"color": "#d51c5e", "url": "https://i.imgur.com/WU2NlJQ.png"},
            "Ruby": {"color": "#d51c5e", "url": "https://i.imgur.com/WU2NlJQ.png"},
            "Sapphire 2": {
                "color": "#286CD3",
                "url": "https://i.imgur.com/bXEfUSV.png",
            },
            "Sapphire 1": {
                "color": "#286CD3",
                "url": "https://i.imgur.com/bXEfUSV.png",
            },
            "Sapphire": {"color": "#286CD3", "url": "https://i.imgur.com/bXEfUSV.png"},
            "Platinum 2": {
                "color": "#3FABB8",
                "url": "https://i.imgur.com/8v8IjHE.png",
            },
            "Platinum 1": {
                "color": "#3FABB8",
                "url": "https://i.imgur.com/8v8IjHE.png",
            },
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

    return ranks


def get_rank(mmr: int, season: int, game_mode: str):
    if game_mode == "12p":
        if season == 0:
            return "Placement"

        if season == 1:
            if mmr < 2000:
                return "Iron"
            elif mmr < 3500:
                return "Bronze"
            elif mmr < 5000:
                return "Silver"
            elif mmr < 6500:
                return "Gold"
            elif mmr < 8000:
                return "Platinum"
            elif mmr < 9500:
                return "Sapphire"
            elif mmr < 11000:
                return "Ruby"
            elif mmr < 12500:
                return "Diamond"
            elif mmr < 13500:
                return "Master"
            else:
                return "Grandmaster"

        if season == 2:
            if mmr < 2000:
                return "Iron"
            elif mmr < 4000:
                return "Bronze"
            elif mmr < 6000:
                return "Silver"
            elif mmr < 7500:
                return "Gold"
            elif mmr < 9000:
                return "Platinum"
            elif mmr < 10500:
                return "Sapphire"
            elif mmr < 12000:
                return "Ruby"
            elif mmr < 13500:
                return "Diamond"
            elif mmr < 14500:
                return "Master"
            else:
                return "Grandmaster"

        if season >= 3:
            if mmr < 2000:
                return "Iron"
            elif mmr < 4000:
                return "Bronze"
            elif mmr < 6000:
                return "Silver"
            elif mmr < 8000:
                return "Gold"
            elif mmr < 9500:
                return "Platinum"
            elif mmr < 11000:
                return "Sapphire"
            elif mmr < 12500:
                return "Ruby"
            elif mmr < 14000:
                return "Diamond"
            elif mmr < 15000:
                return "Master"
            else:
                return "Grandmaster"

    elif game_mode == "24p":
        if season == 0:
            return "Placement"

        if season == 1:
            if mmr < 2000:
                return "Iron"
            elif mmr < 3500:
                return "Bronze"
            elif mmr < 5000:
                return "Silver"
            elif mmr < 6500:
                return "Gold"
            elif mmr < 8000:
                return "Platinum"
            elif mmr < 9500:
                return "Sapphire"
            elif mmr < 11000:
                return "Ruby"
            elif mmr < 12500:
                return "Diamond"
            elif mmr < 13500:
                return "Master"
            else:
                return "Grandmaster"

        if season >= 2:
            if mmr < 2000:
                return "Iron"
            elif mmr < 4000:
                return "Bronze"
            elif mmr < 6000:
                return "Silver"
            elif mmr < 8000:
                return "Gold"
            elif mmr < 10000:
                return "Platinum"
            elif mmr < 11500:
                return "Sapphire"
            elif mmr < 13000:
                return "Ruby"
            elif mmr < 14500:
                return "Diamond"
            elif mmr < 15500:
                return "Master"
            else:
                return "Grandmaster"

    else:
        return "Placement"


def get_country_flag(code: str) -> str:
    """Convert an ISO 3166-1 alpha-2 country code to a Unicode flag emoji."""
    if not code or len(code) != 2:
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def format_mmr_delta(delta: int) -> str:
    return f"+{delta}" if delta >= 0 else str(delta)


def get_mmr_definition(season: int, game_mode: str) -> list[int]:
    if game_mode == "12p":
        if season == 1:
            mmr_definition = [
                0,
                2000,
                3500,
                5000,
                6500,
                8000,
                9500,
                11000,
                12500,
                13500,
            ]
        elif season == 2:
            mmr_definition = [
                0,
                2000,
                4000,
                6000,
                7500,
                9000,
                10500,
                12000,
                13500,
                14500,
            ]

        elif season >= 3:
            mmr_definition = [
                0,
                2000,
                4000,
                6000,
                8000,
                9500,
                11000,
                12500,
                14000,
                15000,
            ]

    elif game_mode == "24p":
        if season == 1:
            mmr_definition = [
                0,
                2000,
                3500,
                5000,
                6500,
                8000,
                9500,
                11000,
                12500,
                13500,
            ]
        elif season >= 2:
            mmr_definition = [
                0,
                2000,
                4000,
                6000,
                8000,
                10000,
                11500,
                13000,
                14500,
                15500,
            ]

    return mmr_definition


# Rank order for determining "promotion" (higher index = higher rank)
_RANK_ORDER = [
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


def rank_index(rank_name):
    """Return rank order index, stripping tier suffixes like '1'/'2'."""
    base = rank_name.split()[0] if rank_name else ""
    try:
        return _RANK_ORDER.index(base)
    except ValueError:
        return -1
