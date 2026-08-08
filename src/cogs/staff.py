import datetime as dt
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import common.data_handler as data_handler
from common import game_config as cfg
from common.checks import is_mod

load_dotenv()


class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="data", description="Display player data")
    @app_commands.describe(name="Player name, discord id, or mkc id (optional)")
    @is_mod()
    async def data(self, interaction: discord.Interaction, name: str | None = None):
        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player(
            name, season=os.getenv("CURRENT_SEASON"), game_mode=cfg.DEFAULT_GAME_MODE
        )

        if player is None:
            await interaction.response.send_message(
                f"Player '{name}' not found.", ephemeral=True
            )
            return

        mkc_url = (
            os.getenv("MKCentral_Site_URL")
            + f"/registry/players/profile?id={player['mkcId']}"
        )
        mkc_field = f"[{player['mkcId']}]({mkc_url})"

        embed = discord.Embed(
            title="Player Data",
            url=cfg.player_url(player["id"]),
            description=player["name"],
            timestamp=dt.datetime.now(dt.UTC),
        )

        embed.add_field(name="MKC ID", value=mkc_field, inline=False)

        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )

        try:
            discordid = player["discordId"]
        except KeyError:
            discordid = "Null"
        embed.add_field(name="Discord ID", value=discordid, inline=False)
        embed.add_field(name="Mention", value=f"<@!{discordid}>", inline=False)
        try:
            country_code = player["countryCode"]
        except KeyError:
            country_code = "Null"
        embed.add_field(name="Country Code", value=country_code, inline=False)
        embed.add_field(name="Hidden", value=player["isHidden"], inline=False)
        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Staff(bot))
