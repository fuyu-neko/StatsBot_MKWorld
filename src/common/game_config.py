import os

from dotenv import load_dotenv

load_dotenv()

MKWORLD = "mkworld"
MK8DX = "mk8dx"

_SETTINGS = {
    MKWORLD: {
        "display_name": "MKWorld",
        "site_segment": "mkworld",
        "game_modes": ("24p", "12p"),
    },
    MK8DX: {
        "display_name": "MK8DX",
        "site_segment": "mk8dx",
        "game_modes": ("12p",),
    },
}

_MODE_DISPLAY = {"12p": "12 player", "24p": "24 player"}


def _resolve_game() -> str:
    game = os.getenv("GAME", MKWORLD).strip().lower()
    if game not in _SETTINGS:
        raise RuntimeError(
            f"GAME must be one of {', '.join(sorted(_SETTINGS))}, got '{game}'"
        )
    return game


GAME = _resolve_game()

DISPLAY_NAME: str = _SETTINGS[GAME]["display_name"]
SITE_SEGMENT: str = _SETTINGS[GAME]["site_segment"]
GAME_MODES: tuple[str, ...] = _SETTINGS[GAME]["game_modes"]
DEFAULT_GAME_MODE: str = GAME_MODES[0]
HAS_GAME_MODE_CHOICE: bool = len(GAME_MODES) > 1

SITE_URL: str = os.getenv("WEBSITE_URL", "https://lounge.mkcentral.com").rstrip("/")


def api_game(game_mode: str | None = None) -> str:
    if GAME == MKWORLD:
        return f"{MKWORLD}{game_mode or DEFAULT_GAME_MODE}"
    return GAME


def player_url(player_id: int | str, game_mode: str | None = None) -> str:
    url = f"{SITE_URL}/{SITE_SEGMENT}/PlayerDetails/{player_id}"
    if HAS_GAME_MODE_CHOICE:
        url += f"?p={(game_mode or DEFAULT_GAME_MODE)[0:1]}"
    return url


def table_url(table_id: int | str) -> str:
    return f"{SITE_URL}/{SITE_SEGMENT}/TableDetails/{table_id}"


def label(game_mode: str | None = None) -> str:
    if HAS_GAME_MODE_CHOICE:
        return f"{DISPLAY_NAME}{(game_mode or DEFAULT_GAME_MODE).upper()}"
    return DISPLAY_NAME


def mode_display(game_mode: str | None) -> str | None:
    if not HAS_GAME_MODE_CHOICE:
        return None
    return _MODE_DISPLAY.get(game_mode)
