import functools
import inspect

import discord
from discord import app_commands

from common import constants
from common import game_config as cfg


def game_mode_option(func=None, *, description: str | None = None):
    def decorator(inner):
        if cfg.HAS_GAME_MODE_CHOICE:
            inner = app_commands.describe(
                game_mode=description or f"Game mode (default: {cfg.DEFAULT_GAME_MODE})"
            )(inner)
            return app_commands.choices(
                game_mode=[
                    app_commands.Choice(name=mode, value=mode)
                    for mode in cfg.GAME_MODES
                ]
            )(inner)

        @functools.wraps(inner)
        async def wrapper(*args, **kwargs):
            kwargs.setdefault("game_mode", cfg.DEFAULT_GAME_MODE)
            return await inner(*args, **kwargs)

        signature = inspect.signature(inner)
        wrapper.__signature__ = signature.replace(
            parameters=[
                param
                for name, param in signature.parameters.items()
                if name != "game_mode"
            ]
        )
        wrapper.__annotations__ = {
            name: annotation
            for name, annotation in inner.__annotations__.items()
            if name != "game_mode"
        }
        return wrapper

    return decorator(func) if func is not None else decorator


async def reject_unsupported_season(
    interaction: discord.Interaction, season: int | None
) -> bool:
    if season is None or int(season) >= constants.MIN_SEASON:
        return False

    message = (
        f"{cfg.DISPLAY_NAME} stats are only available from "
        f"Season {constants.MIN_SEASON} onwards."
    )
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)
    return True
