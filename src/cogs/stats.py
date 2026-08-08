import datetime as dt
import os
import statistics
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import API.get_lounge as api
import common.constants as constants
import common.data_handler as data_handler
from common import game_config as cfg
from common.calculation import calc_mmr_deltas
from common.command_options import game_mode_option, reject_unsupported_season
from common.plotting import (
    create_formats_plot,
    create_h2h_plot,
    create_partner_plot,
    create_plot,
    create_scores_plot,
    create_streak_plot,
    create_tiers_plot,
)
from common.predict import parse_room, predict_deltas

# Common timezone abbreviations routed to IANA zones so DST is automatic.
# Ambiguous picks: CST -> US Central, IST -> India.
ABBREV_TO_IANA = {
    "UTC": "UTC",
    "GMT": "Etc/GMT",
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "AST": "America/Halifax",
    "ADT": "America/Halifax",
    "NST": "America/St_Johns",
    "NDT": "America/St_Johns",
    "AKST": "America/Anchorage",
    "AKDT": "America/Anchorage",
    "HST": "Pacific/Honolulu",
    "HDT": "Pacific/Honolulu",
    "CLT": "America/Santiago",
    "CLST": "America/Santiago",
    "BST": "Europe/London",
    "CET": "Europe/Paris",
    "CEST": "Europe/Paris",
    "IST": "Asia/Kolkata",
    "JST": "Asia/Tokyo",
    "KST": "Asia/Seoul",
    "AEST": "Australia/Sydney",
    "AEDT": "Australia/Sydney",
    "ACST": "Australia/Adelaide",
    "ACDT": "Australia/Adelaide",
    "AWST": "Australia/Perth",
    "AWDT": "Australia/Perth",
}


def _resolve_timezone(tz_str: str | None) -> tuple[str, ZoneInfo] | None:
    if not tz_str:
        return "UTC", ZoneInfo("UTC")
    upper = tz_str.upper()
    iana = ABBREV_TO_IANA.get(upper)
    if iana is None:
        return None
    try:
        return upper, ZoneInfo(iana)
    except ZoneInfoNotFoundError:
        return None


TIER_ORDER = [
    "SQ",
    "X",
    "S",
    "AB",
    "A",
    "B",
    "BC",
    "C",
    "CD",
    "D",
    "DE",
    "E",
    "EF",
    "F",
]

_FORMAT_TO_TEAM_SIZE = {
    "FFA": 1,
    "2v2": 2,
    "3v3": 3,
    "4v4": 4,
    "6v6": 6,
    "8v8": 8,
    "12v12": 12,
}

_TEAM_SIZE_TO_FORMAT = {size: name for name, size in _FORMAT_TO_TEAM_SIZE.items()}

# 8v8 and 12v12 need 24 players, so they never occur in a 12p-only lounge.
_MAX_PLAYERS = 24 if "24p" in cfg.GAME_MODES else 12
FORMAT_ORDER = [
    name
    for name, size in _FORMAT_TO_TEAM_SIZE.items()
    if _MAX_PLAYERS % size == 0 and _MAX_PLAYERS // size >= 2
]


def _derive_format(num_teams: int, game_mode: str) -> str:
    total = 24 if game_mode == "24p" else 12
    if not num_teams or total % num_teams != 0:
        return "?"
    return _TEAM_SIZE_TO_FORMAT.get(total // num_teams, "?")


# load environment variables from .env file
load_dotenv()


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mmr", description=f"Show {cfg.DISPLAY_NAME} Player MMR")
    @app_commands.describe(
        names="comma-separated list of player names, discord ids, mkc ids (optional)",
        season="Season number (default: current season)",
    )
    @game_mode_option
    async def mmr(
        self,
        interaction: discord.Interaction,
        names: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
    ):
        if await reject_unsupported_season(interaction, season):
            return
        # if multiple names are provided,
        # split them into a list and fetch MMR data for each player

        # If no names are provided, default to the user's ID
        if names is None:
            names = str(interaction.user.id)
        if len(names.split(",")) == 1:
            await self._show_mmr(interaction, names, season, game_mode, "current")

        else:
            await interaction.response.defer()
            embed = discord.Embed(
                title=f"S{season} MMR - {cfg.label(game_mode)}",
                timestamp=dt.datetime.now(dt.UTC),
            )

            total_mmr = 0
            total_players = 0

            for name in names.split(","):
                player = await data_handler.fetch_player_info(
                    name.strip(), season, game_mode
                )

                # return error message if player is not found
                if player is None:
                    embed.add_field(
                        name=name.strip(),
                        value="```\nPlayer Not Found\n```",
                        inline=False,
                    )
                    continue

                # return error message if player has no MMR data
                if "mmr" not in player:
                    embed.add_field(
                        name=name.strip(), value="```\nPlacement\n```", inline=False
                    )
                    continue

                embed.add_field(
                    name=player["name"],
                    value=f"```\n{player['mmr']}\n```",
                    inline=False,
                )
                total_mmr += player["mmr"]
                total_players += 1
                continue

            average_mmr = total_mmr / total_players if total_players > 0 else 0
            embed.add_field(
                name="Average MMR",
                value=f"```\n{average_mmr:.2f}\n```",
                inline=False,
            )

            embed.set_footer(
                text="MKCentral Lounge",
                icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="stats", description=f"Show {cfg.DISPLAY_NAME} Player Stats"
    )
    @app_commands.describe(
        name="Lounge name, discord ids, mkc ids (optional)",
        season="Season number (default: current season)",
    )
    @game_mode_option
    async def stats(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
    ):
        if await reject_unsupported_season(interaction, season):
            return
        await interaction.response.defer()

        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player_info(name, season, game_mode)

        # check if player exists
        if player is None:
            await interaction.followup.send(
                f"Player '{name}' not found.",
                ephemeral=True,
            )
            return

        # check if player has event history
        if len(player["mmrChanges"]) <= 1:
            await interaction.followup.send(
                "You have to play at least 1 match to check your stats.",
                ephemeral=True,
            )
            return

        rank_data = constants.get_rank_info(player["rank"])

        # Generate MMR history plot
        mmr_changes = list(reversed(player["mmrChanges"]))
        mmr_history = [change["newMmr"] for change in mmr_changes]
        plot_image = create_plot(
            mmr_history,
            season=season,
            player_name=player["name"],
            game_mode=game_mode,
        )
        file = discord.File(plot_image, filename="mmr_chart.png")

        # create embed with player stats
        embed = discord.Embed(
            title=f"S{season} Stats - {cfg.label(game_mode)}",
            url=cfg.player_url(player["playerId"], game_mode),
            description=f"### {player['name']} [{player['countryCode']}]",
            colour=int(f"0x{rank_data['color'][1:]}", 16),
            timestamp=dt.datetime.now(dt.UTC),
        )

        embed.set_image(url="attachment://mmr_chart.png")
        embed.add_field(name="MMR", value=f"{player['mmr']}", inline=True)
        try:
            embed.add_field(name="Peak MMR", value=f"{player['maxMmr']}", inline=True)
        except KeyError:
            embed.add_field(name="Peak MMR", value="N/A", inline=True)
        embed.add_field(
            name="Events Played", value=f"{player['eventsPlayed']}", inline=True
        )

        # Row 2: Win rate and last 10
        embed.add_field(
            name="Win Rate", value=f"{player['winRate'] * 100:.1f}%", inline=True
        )
        embed.add_field(
            name="Last 10 Matches",
            value=f"{player['winLossLastTen']}（{player['gainLossLastTen']}）",
            inline=True,
        )
        # Empty field to keep grid aligned (Discord embeds use 3-column layout)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Row 3: Score stats
        embed.add_field(
            name="Avg. Score", value=f"{player['averageScore']:.1f}", inline=True
        )
        embed.add_field(
            name="Avg. Score Last10",
            value=f"{player['averageLastTen']:.1f}",
            inline=True,
        )
        try:
            embed.add_field(
                name="Largest Gain", value=player["largestGain"], inline=True
            )
        except KeyError:
            embed.add_field(name="Largest Gain", value="N/A", inline=True)

        # Row 4: Score stats of No SQ
        embed.add_field(
            name="Avg. Score (No SQ)",
            value=f"{player['noSQAverageScore']:.1f}",
            inline=True,
        )
        embed.add_field(
            name="Avg. Score Last10 (No SQ)",
            value=f"{player['noSQAverageLastTen']:.1f}",
            inline=True,
        )

        try:
            embed.add_field(
                name="Partner Avg.",
                value=f"{player['partnerAverage']:.1f}",
                inline=True,
            )
        except KeyError:
            embed.add_field(name="Partner Avg.", value="N/A", inline=True)

        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        embed.set_thumbnail(url=rank_data["url"])

        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command(
        name="lastmatch",
        description=f"Show {cfg.DISPLAY_NAME} Player Last Verified Match",
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
    )
    @game_mode_option(
        description="Game mode (default: most recent across both 12p and 24p)"
    )
    async def lastmatch(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        game_mode: str | None = None,
    ):
        if name is None:
            name = str(interaction.user.id)

        season = os.getenv("CURRENT_SEASON")
        modes = [game_mode] if game_mode is not None else list(cfg.GAME_MODES)

        candidates = []
        player_name_for_error = name
        for mode in modes:
            mode_player = await data_handler.fetch_player_info(
                name, season=season, game_mode=mode
            )
            if mode_player is None:
                continue
            player_name_for_error = mode_player["name"]
            for event in mode_player["mmrChanges"]:
                if event["reason"] != "Table":
                    continue
                details = await api.fetch_table(table_id=event["changeId"])
                if details is None or "verifiedOn" not in details:
                    continue
                candidates.append((mode_player, event, details))
                break

        if not candidates:
            await interaction.response.send_message(
                f"No verified matches found for {player_name_for_error}.",
                ephemeral=True,
            )
            return

        player, last_event, table_details = max(
            candidates,
            key=lambda c: datetime.fromisoformat(c[2]["createdOn"]),
        )

        page_url = os.getenv("WEBSITE_URL") + f"/TableDetails/{last_event['changeId']}"

        embed = discord.Embed(
            title=f"Table ID: {last_event['changeId']}", url=page_url, colour=0x1DA3DD
        )
        embed.add_field(name="Table ID", value=table_details["id"], inline=True)
        embed.add_field(name="Format", value=table_details["format"], inline=True)
        embed.add_field(name="Tier", value=table_details["tier"], inline=True)

        timestamp_d1 = datetime.fromisoformat(table_details["createdOn"])
        unix_time1 = int(timestamp_d1.timestamp())

        embed.add_field(
            name="Created On", value=f"Changed On <t:{unix_time1}:s>", inline=False
        )

        if "verifiedOn" in table_details:
            timestamp_d2 = datetime.fromisoformat(table_details["verifiedOn"])
            unix_time2 = int(timestamp_d2.timestamp())

            embed.add_field(
                name="Verified On", value=f"Changed On <t:{unix_time2}:s>", inline=False
            )
        else:
            embed.add_field(name="Verified On", value="Unverified", inline=False)

        mmr_message = "```\n"
        names = []
        old_mmrs = []
        new_mmrs = []
        deltas = []
        for team in table_details["teams"]:
            for player in team["scores"]:
                names.append(player["playerName"])
                old_mmrs.append(player["prevMmr"])
                new_mmrs.append(player["newMmr"])
                deltas.append(player["delta"])
        len_names = max(map(len, names))
        len_old_mmrs = len(str(max(old_mmrs)))
        len_new_mmrs = len(str(max(new_mmrs)))
        len_deltas = len(str(max(deltas)))
        for i in range(len(names)):
            mmr_message += f"{names[i].ljust(len_names)}: {str(old_mmrs[i]).ljust(len_old_mmrs)} --> {str(new_mmrs[i]).ljust(len_new_mmrs)} ({str(deltas[i]).rjust(len_deltas)})\n"  # noqa: E501
        mmr_message += "```"

        embed.add_field(name="MMR Changes", value=mmr_message, inline=True)

        embed.set_image(
            url=os.getenv("WEBSITE_URL") + f"/TableImage/{last_event['changeId']}.png"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="table", description=f"Show {cfg.DISPLAY_NAME} Match Details"
    )
    @app_commands.describe(table_id="Table ID")
    async def table(self, interaction: discord.Interaction, table_id: str):
        table_details = await api.fetch_table(table_id=table_id)
        if table_details is None:
            await interaction.response.send_message("Table not found!", ephemeral=True)
            return

        page_url = os.getenv("WEBSITE_URL") + f"/TableDetails/{table_id}"
        embed = discord.Embed(
            title=f"Table ID: {table_id}", url=page_url, colour=0x1DA3DD
        )
        embed.add_field(name="Table ID", value=table_details["id"], inline=True)
        embed.add_field(name="Format", value=table_details["format"], inline=True)
        embed.add_field(name="Tier", value=table_details["tier"], inline=True)

        timestamp_d1 = datetime.fromisoformat(table_details["createdOn"])
        unix_time1 = int(timestamp_d1.timestamp())

        embed.add_field(
            name="Created On", value=f"Changed On <t:{unix_time1}:s>", inline=False
        )

        is_verified = "verifiedOn" in table_details

        if is_verified:
            timestamp_d2 = datetime.fromisoformat(table_details["verifiedOn"])
            unix_time2 = int(timestamp_d2.timestamp())

            embed.add_field(
                name="Verified On", value=f"Changed On <t:{unix_time2}:s>", inline=False
            )
        else:
            embed.add_field(
                name="Verified On",
                value="Unverified — MMR changes shown are expected values and may differ from the final result.",  # noqa: E501
                inline=False,
            )
        calced_deltas = None if is_verified else calc_mmr_deltas(table_details)

        mmr_message = "```\n"
        names = []
        old_mmrs = []
        new_mmrs = []
        deltas = []
        for i, team in enumerate(table_details["teams"]):
            for player in team["scores"]:
                names.append(player["playerName"])
                old_mmrs.append(player["prevMmr"])
                if is_verified:
                    new_mmrs.append(player["newMmr"])
                    deltas.append(player["delta"])
                else:
                    new_mmrs.append(player["prevMmr"] + calced_deltas[i])
                    deltas.append(calced_deltas[i])
        len_names = max(map(len, names))
        len_old_mmrs = len(str(max(old_mmrs)))
        len_new_mmrs = len(str(max(new_mmrs)))
        len_deltas = len(str(max(deltas)))
        for i in range(len(names)):
            mmr_message += f"{names[i].ljust(len_names)}: {str(old_mmrs[i]).ljust(len_old_mmrs)} --> {str(new_mmrs[i]).ljust(len_new_mmrs)} ({str(deltas[i]).rjust(len_deltas)})\n"  # noqa: E501
        mmr_message += "```"

        embed.add_field(
            name="MMR Changes" if is_verified else "Expected MMR Changes",
            value=mmr_message,
            inline=True,
        )
        embed.set_image(
            url=(os.getenv("WEBSITE_URL") + f"/TableImage/{table_details['id']}.png")
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="namelog", description="View a player's name change history"
    )
    @app_commands.describe(name="Player name, discord id, or mkc id (optional)")
    async def namelog(self, interaction: discord.Interaction, name: str | None = None):
        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player_info(
            name, season=os.getenv("CURRENT_SEASON"), game_mode=cfg.DEFAULT_GAME_MODE
        )

        if player is None:
            await interaction.response.send_message(
                f"Player '{name}' not found.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Namelog for {player['name']}",
            url=cfg.player_url(player["playerId"]),
            timestamp=dt.datetime.now(dt.UTC),
        )

        for entry in player["nameHistory"]:
            timestamp_d = datetime.fromisoformat(entry["changedOn"])
            unix_time = int(timestamp_d.timestamp())

            embed.add_field(
                name=entry["name"],
                value=f"Changed On <t:{unix_time}:s>",
                inline=False,
            )
        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="fc", description=f"Show {cfg.DISPLAY_NAME} Player Friend Code"
    )
    @app_commands.describe(name="Player name, discord id, or mkc id (optional)")
    async def fc(self, interaction: discord.Interaction, name: str | None = None):
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

        embed = discord.Embed(
            title=f"Friend Code for {player['name']}",
            url=cfg.player_url(player["id"]),
            timestamp=dt.datetime.now(dt.UTC),
        )

        embed.add_field(name="Friend Code", value=player["switchFc"], inline=False)
        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="tiers", description=f"Show {cfg.DISPLAY_NAME} Player Performance by Tier"
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        season="Season number (default: current season)",
    )
    @game_mode_option
    async def tiers(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
    ):
        if await reject_unsupported_season(interaction, season):
            return
        await interaction.response.defer()

        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player_info(name, season, game_mode)

        if player is None:
            await interaction.followup.send(
                f"Player '{name}' not found.", ephemeral=True
            )
            return

        table_events = [
            e for e in player.get("mmrChanges", []) if e.get("reason") == "Table"
        ]
        if not table_events:
            await interaction.followup.send(
                "You have to play at least 1 match to check your tier stats.",
                ephemeral=True,
            )
            return

        tier_order = TIER_ORDER

        buckets = {}
        for e in table_events:
            t = e.get("tier", "?")
            b = buckets.setdefault(
                t,
                {
                    "events": 0,
                    "delta_sum": 0,
                    "rank_sum": 0,
                    "score_sum": 0,
                    "wins": 0,
                    "win_delta_sum": 0,
                    "loss_delta_sum": 0,
                    "losses": 0,
                    "firsts": 0,
                    "tops": 0,
                    "bottoms": 0,
                },
            )
            b["events"] += 1
            delta = e.get("mmrDelta", 0)
            rank = e.get("rank", 0)
            num_teams = e.get("numTeams", 1) or 1
            b["delta_sum"] += delta
            b["rank_sum"] += rank
            b["score_sum"] += e.get("score", 0)
            if delta > 0:
                b["wins"] += 1
                b["win_delta_sum"] += delta
            elif delta < 0:
                b["losses"] += 1
                b["loss_delta_sum"] += delta
            if rank == 1:
                b["firsts"] += 1
            if rank <= num_teams * 0.25:
                b["tops"] += 1
            if rank > num_teams * 0.75:
                b["bottoms"] += 1

        sorted_tiers = sorted(
            buckets.items(),
            key=lambda kv: (
                tier_order.index(kv[0]) if kv[0] in tier_order else len(tier_order)
            ),
        )

        tier_rows = []
        for tier_name, b in sorted_tiers:
            n = b["events"]
            tier_rows.append(
                {
                    "tier": tier_name,
                    "n": n,
                    "win_rate": b["wins"] / n * 100,
                    "avg_delta": b["delta_sum"] / n,
                    "total": b["delta_sum"],
                    "avg_rank": b["rank_sum"] / n,
                    "avg_score": b["score_sum"] / n,
                    "firsts": b["firsts"],
                    "tops": b["tops"],
                    "bottoms": b["bottoms"],
                }
            )

        plot_image = create_tiers_plot(
            tier_rows=tier_rows,
            season=season,
            player_name=player["name"],
            country_code=player.get("countryCode", ""),
            game_mode=game_mode,
        )
        file = discord.File(plot_image, filename="tiers.png")

        rank_data = constants.get_rank_info(player["rank"])
        embed = discord.Embed(
            title=f"S{season} Tiers - {cfg.label(game_mode)}",
            url=cfg.player_url(player["playerId"], game_mode),
            description=f"### {player['name']} [{player['countryCode']}]",
            colour=int(f"0x{rank_data['color'][1:]}", 16),
            timestamp=dt.datetime.now(dt.UTC),
        )
        embed.set_image(url="attachment://tiers.png")

        best_tier = max(
            sorted_tiers, key=lambda kv: kv[1]["delta_sum"] / kv[1]["events"]
        )
        worst_tier = min(
            sorted_tiers, key=lambda kv: kv[1]["delta_sum"] / kv[1]["events"]
        )
        most_played = max(sorted_tiers, key=lambda kv: kv[1]["events"])
        embed.add_field(
            name="Best Tier",
            value=f"{best_tier[0]} ({best_tier[1]['delta_sum'] / best_tier[1]['events']:+.0f} avg)",  # noqa: E501
            inline=True,
        )
        embed.add_field(
            name="Worst Tier",
            value=f"{worst_tier[0]} ({worst_tier[1]['delta_sum'] / worst_tier[1]['events']:+.0f} avg)",  # noqa: E501
            inline=True,
        )
        embed.add_field(
            name="Most Played",
            value=f"{most_played[0]} ({most_played[1]['events']} events)",
            inline=True,
        )

        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        embed.set_thumbnail(url=rank_data["url"])

        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command(
        name="fs", description=f"Show {cfg.DISPLAY_NAME} Player Performance by Format"
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        season="Season number (default: current season)",
    )
    @game_mode_option
    async def fs(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
    ):
        if await reject_unsupported_season(interaction, season):
            return
        await interaction.response.defer()

        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player_info(name, season, game_mode)

        if player is None:
            await interaction.followup.send(
                f"Player '{name}' not found.", ephemeral=True
            )
            return

        table_events = [
            e for e in player.get("mmrChanges", []) if e.get("reason") == "Table"
        ]
        if not table_events:
            await interaction.followup.send(
                "You have to play at least 1 match to check your format stats.",
                ephemeral=True,
            )
            return

        buckets = {}
        for e in table_events:
            f = _derive_format(e.get("numTeams", 0) or 0, game_mode)
            b = buckets.setdefault(
                f,
                {
                    "events": 0,
                    "delta_sum": 0,
                    "rank_sum": 0,
                    "score_sum": 0,
                    "wins": 0,
                    "win_delta_sum": 0,
                    "loss_delta_sum": 0,
                    "losses": 0,
                    "firsts": 0,
                    "tops": 0,
                    "bottoms": 0,
                },
            )
            b["events"] += 1
            delta = e.get("mmrDelta", 0)
            rank = e.get("rank", 0)
            num_teams = e.get("numTeams", 1) or 1
            b["delta_sum"] += delta
            b["rank_sum"] += rank
            b["score_sum"] += e.get("score", 0)
            if delta > 0:
                b["wins"] += 1
                b["win_delta_sum"] += delta
            elif delta < 0:
                b["losses"] += 1
                b["loss_delta_sum"] += delta
            if rank == 1:
                b["firsts"] += 1
            if rank <= num_teams * 0.25:
                b["tops"] += 1
            if rank > num_teams * 0.75:
                b["bottoms"] += 1

        sorted_formats = sorted(
            buckets.items(),
            key=lambda kv: (
                FORMAT_ORDER.index(kv[0])
                if kv[0] in FORMAT_ORDER
                else len(FORMAT_ORDER)
            ),
        )

        format_rows = []
        for format_name, b in sorted_formats:
            n = b["events"]
            format_rows.append(
                {
                    "format": format_name,
                    "n": n,
                    "win_rate": b["wins"] / n * 100,
                    "avg_delta": b["delta_sum"] / n,
                    "total": b["delta_sum"],
                    "avg_rank": b["rank_sum"] / n,
                    "avg_score": b["score_sum"] / n,
                    "firsts": b["firsts"],
                    "tops": b["tops"],
                    "bottoms": b["bottoms"],
                }
            )

        plot_image = create_formats_plot(
            format_rows=format_rows,
            season=season,
            player_name=player["name"],
            country_code=player.get("countryCode", ""),
            game_mode=game_mode,
        )
        file = discord.File(plot_image, filename="formats.png")

        rank_data = constants.get_rank_info(player["rank"])
        embed = discord.Embed(
            title=f"S{season} Formats - {cfg.label(game_mode)}",
            url=cfg.player_url(player["playerId"], game_mode),
            description=f"### {player['name']} [{player['countryCode']}]",
            colour=int(f"0x{rank_data['color'][1:]}", 16),
            timestamp=dt.datetime.now(dt.UTC),
        )
        embed.set_image(url="attachment://formats.png")

        best_format = max(
            sorted_formats, key=lambda kv: kv[1]["delta_sum"] / kv[1]["events"]
        )
        worst_format = min(
            sorted_formats, key=lambda kv: kv[1]["delta_sum"] / kv[1]["events"]
        )
        most_played = max(sorted_formats, key=lambda kv: kv[1]["events"])
        embed.add_field(
            name="Best Format",
            value=f"{best_format[0]} ({best_format[1]['delta_sum'] / best_format[1]['events']:+.0f} avg)",  # noqa: E501
            inline=True,
        )
        embed.add_field(
            name="Worst Format",
            value=f"{worst_format[0]} ({worst_format[1]['delta_sum'] / worst_format[1]['events']:+.0f} avg)",  # noqa: E501
            inline=True,
        )
        embed.add_field(
            name="Most Played",
            value=f"{most_played[0]} ({most_played[1]['events']} events)",
            inline=True,
        )

        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        embed.set_thumbnail(url=rank_data["url"])

        await interaction.followup.send(embed=embed, file=file)

    async def _show_mmr(
        self,
        interaction: discord.Interaction,
        name: str | None,
        season: int | None,
        game_mode: str | None,
        type: str,
    ):
        if await reject_unsupported_season(interaction, season):
            return
        await interaction.response.defer()

        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player_info(name, season, game_mode)

        if player is None:
            await interaction.followup.send(
                f"Player '{name}' not found.", ephemeral=True
            )
            return

        table_events = [
            e for e in player.get("mmrChanges", []) if e.get("reason") == "Table"
        ]
        if not table_events:
            await interaction.followup.send(
                "You have to play at least 1 match to check your mmr.",
                ephemeral=True,
            )
            return

        if type == "current":
            type_name = "MMR"
            show_mmr = player.get("mmr")
            rank_name = player.get("rank")
        elif type == "average":
            type_name = "Average MMR"
            mmr_sum = 0
            for e in table_events:
                mmr_sum += e.get("newMmr", 0)
            avg_mmr = mmr_sum / player.get("eventsPlayed")
            rank_name = constants.get_rank(avg_mmr, season, game_mode)
            show_mmr = f"{avg_mmr:.1f}"
        elif type == "peak":
            type_name = "Peak MMR"
            show_mmr = player.get("maxMmr")
            if show_mmr is None:
                await interaction.followup.send(
                    "You have to play at least 5 match to check your Peak mmr."
                )
                return
            rank_name = constants.get_rank(show_mmr, season, game_mode)

        rank_data = constants.get_rank_info(rank_name)
        embed = discord.Embed(
            title=f"S{season} {type_name} - {cfg.label(game_mode)}",
            url=cfg.player_url(player["playerId"], game_mode),
            colour=int(f"0x{rank_data['color'][1:]}", 16),
            timestamp=dt.datetime.now(dt.UTC),
        )

        embed.add_field(
            name=player["name"], value=f"```\n{show_mmr}\n```", inline=False
        )
        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="averagemmr",
        description=f"Show {cfg.DISPLAY_NAME} Player Average MMR",
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        season="Season number (default: current season)",
    )
    @game_mode_option
    async def averagemmr(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
    ):
        await self._show_mmr(interaction, name, season, game_mode, "average")

    @app_commands.command(
        name="peakmmr",
        description=f"Show {cfg.DISPLAY_NAME} Player Peak MMR",
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        season="Season number (default: current season)",
    )
    @game_mode_option
    async def peakmmr(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
    ):
        await self._show_mmr(interaction, name, season, game_mode, "peak")

    @app_commands.command(
        name="h2h",
        description="Compare two players' shared matches (head-to-head)",
    )
    @app_commands.describe(
        name1="First player (lounge name, discord id, or mkc id)",
        name2="Second player (defaults to you)",
        season="Season number (default: current season)",
    )
    @game_mode_option
    async def h2h(
        self,
        interaction: discord.Interaction,
        name1: str,
        name2: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
    ):
        if await reject_unsupported_season(interaction, season):
            return
        await interaction.response.defer()

        if name2 is None:
            # caller is the implicit second player; put them on the left
            name2 = name1
            name1 = str(interaction.user.id)

        p1 = await data_handler.fetch_player_info(name1, season, game_mode)
        if p1 is None:
            await interaction.followup.send(
                f"Player '{name1}' not found.", ephemeral=True
            )
            return
        p2 = await data_handler.fetch_player_info(name2, season, game_mode)
        if p2 is None:
            await interaction.followup.send(
                f"Player '{name2}' not found.", ephemeral=True
            )
            return

        if p1.get("playerId") == p2.get("playerId"):
            await interaction.followup.send(
                "You can't compare a player to themselves.", ephemeral=True
            )
            return

        c1 = {
            e["changeId"]: e
            for e in p1.get("mmrChanges", [])
            if e.get("reason") == "Table" and "changeId" in e
        }
        c2 = {
            e["changeId"]: e
            for e in p2.get("mmrChanges", [])
            if e.get("reason") == "Table" and "changeId" in e
        }
        shared_ids = sorted(
            set(c1) & set(c2), key=lambda k: c1[k]["time"], reverse=True
        )

        if not shared_ids:
            await interaction.followup.send(
                f"No shared {game_mode} matches found between "
                f"{p1['name']} and {p2['name']}.",
                ephemeral=True,
            )
            return

        pid1, pid2 = p1["playerId"], p2["playerId"]
        opponent_ids = []
        for cid in shared_ids:
            partners1 = c1[cid].get("partnerIds") or []
            partners2 = c2[cid].get("partnerIds") or []
            if pid2 not in partners1 and pid1 not in partners2:
                opponent_ids.append(cid)

        if not opponent_ids:
            await interaction.followup.send(
                f"{p1['name']} and {p2['name']} have only played {game_mode} "
                "matches as teammates — no head-to-head matches to compare.",
                ephemeral=True,
            )
            return

        p1_beats_p2 = sum(
            1 for cid in opponent_ids if c1[cid]["rank"] < c2[cid]["rank"]
        )
        p2_beats_p1 = sum(
            1 for cid in opponent_ids if c2[cid]["rank"] < c1[cid]["rank"]
        )
        ties = len(opponent_ids) - p1_beats_p2 - p2_beats_p1

        n = len(opponent_ids)
        scores1 = [c1[cid].get("score", 0) for cid in opponent_ids]
        scores2 = [c2[cid].get("score", 0) for cid in opponent_ids]
        ranks1 = [c1[cid].get("rank", 0) for cid in opponent_ids]
        ranks2 = [c2[cid].get("rank", 0) for cid in opponent_ids]
        p1_avg = sum(scores1) / n
        p2_avg = sum(scores2) / n
        p1_avg_rank = sum(ranks1) / n
        p2_avg_rank = sum(ranks2) / n
        p1_outscored = sum(1 for a, b in zip(scores1, scores2) if a > b)
        p2_outscored = sum(1 for a, b in zip(scores1, scores2) if b > a)

        p1_total_delta = sum(c1[cid].get("mmrDelta", 0) for cid in opponent_ids)
        p2_total_delta = sum(c2[cid].get("mmrDelta", 0) for cid in opponent_ids)

        def _biggest_win(my, other):
            best_cid = None
            best_margin = 0
            for cid in opponent_ids:
                margin = my[cid].get("score", 0) - other[cid].get("score", 0)
                if margin > best_margin:
                    best_margin = margin
                    best_cid = cid
            if best_cid is None:
                return None
            return {
                "date": my[best_cid]["time"][:10],
                "tier": my[best_cid].get("tier", "?"),
                "table_id": best_cid,
                "my_score": my[best_cid].get("score", 0),
                "other_score": other[best_cid].get("score", 0),
                "diff": best_margin,
            }

        p1_biggest_win = _biggest_win(c1, c2)
        p2_biggest_win = _biggest_win(c2, c1)

        recent = []
        for cid in opponent_ids[:10]:
            r1, r2 = c1[cid], c2[cid]
            recent.append(
                {
                    "date": r1["time"][:10],
                    "tier": r1.get("tier", "?"),
                    "p1_score": r1.get("score", 0),
                    "p1_delta": r1.get("mmrDelta", 0),
                    "p2_score": r2.get("score", 0),
                    "p2_delta": r2.get("mmrDelta", 0),
                    "p1_rank": r1.get("rank", "?"),
                    "p2_rank": r2.get("rank", "?"),
                }
            )

        stats = {
            "p1_name": p1["name"],
            "p2_name": p2["name"],
            "p1_country": p1.get("countryCode", ""),
            "p2_country": p2.get("countryCode", ""),
            "p1_mmr": p1.get("mmr"),
            "p2_mmr": p2.get("mmr"),
            "shared": n,
            "p1_beats_p2": p1_beats_p2,
            "p2_beats_p1": p2_beats_p1,
            "ties": ties,
            "p1_avg_score": p1_avg,
            "p2_avg_score": p2_avg,
            "p1_avg_rank": p1_avg_rank,
            "p2_avg_rank": p2_avg_rank,
            "p1_outscored": p1_outscored,
            "p2_outscored": p2_outscored,
            "p1_mmr_delta": p1_total_delta,
            "p2_mmr_delta": p2_total_delta,
            "p1_biggest_win": p1_biggest_win,
            "p2_biggest_win": p2_biggest_win,
            "recent": recent,
        }

        plot_image = create_h2h_plot(stats=stats, season=season, game_mode=game_mode)
        file = discord.File(plot_image, filename="h2h.png")

        embed = discord.Embed(
            title=f"S{season} Head-to-Head - {cfg.label(game_mode)}",
            description=f"### {p1['name']} vs {p2['name']}",
            colour=0x1DA3DD,
            timestamp=dt.datetime.now(dt.UTC),
        )
        embed.set_image(url="attachment://h2h.png")
        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command(
        name="partner",
        description="Compare two players' shared matches as partners",
    )
    @app_commands.describe(
        name1="First player (lounge name, discord id, or mkc id)",
        name2="Second player (defaults to you)",
        season="Season number (default: current season)",
    )
    @game_mode_option
    async def partner(
        self,
        interaction: discord.Interaction,
        name1: str,
        name2: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
    ):
        if await reject_unsupported_season(interaction, season):
            return
        await interaction.response.defer()

        if name2 is None:
            name2 = name1
            name1 = str(interaction.user.id)

        p1 = await data_handler.fetch_player_info(name1, season, game_mode)
        if p1 is None:
            await interaction.followup.send(
                f"Player '{name1}' not found.", ephemeral=True
            )
            return
        p2 = await data_handler.fetch_player_info(name2, season, game_mode)
        if p2 is None:
            await interaction.followup.send(
                f"Player '{name2}' not found.", ephemeral=True
            )
            return

        if p1.get("playerId") == p2.get("playerId"):
            await interaction.followup.send(
                "You can't compare a player to themselves.", ephemeral=True
            )
            return

        c1 = {
            e["changeId"]: e
            for e in p1.get("mmrChanges", [])
            if e.get("reason") == "Table" and "changeId" in e
        }
        c2 = {
            e["changeId"]: e
            for e in p2.get("mmrChanges", [])
            if e.get("reason") == "Table" and "changeId" in e
        }
        shared = set(c1) & set(c2)

        pid1, pid2 = p1["playerId"], p2["playerId"]
        partner_ids = sorted(
            [
                cid
                for cid in shared
                if pid2 in (c1[cid].get("partnerIds") or [])
                or pid1 in (c2[cid].get("partnerIds") or [])
            ],
            key=lambda k: c1[k]["time"],
            reverse=True,
        )

        if not partner_ids:
            await interaction.followup.send(
                f"{p1['name']} and {p2['name']} have not played as partners "
                f"in {game_mode} S{season}.",
                ephemeral=True,
            )
            return

        n = len(partner_ids)
        deltas = [c1[cid].get("mmrDelta", 0) for cid in partner_ids]
        wins = sum(1 for d in deltas if d > 0)
        losses = sum(1 for d in deltas if d < 0)
        total_delta = sum(deltas)

        scores1 = [c1[cid].get("score", 0) for cid in partner_ids]
        scores2 = [c2[cid].get("score", 0) for cid in partner_ids]
        ranks = [c1[cid].get("rank", 0) for cid in partner_ids]

        p1_avg = sum(scores1) / n
        p2_avg = sum(scores2) / n
        avg_rank = sum(ranks) / n
        win_rate = wins / n
        p1_best = max(scores1)
        p2_best = max(scores2)

        def _best_performance(scorer_changes, other_changes):
            best_cid = max(partner_ids, key=lambda k: scorer_changes[k].get("score", 0))
            e_self = scorer_changes[best_cid]
            e_other = other_changes[best_cid]
            return {
                "date": e_self["time"][:10],
                "tier": e_self.get("tier", "?"),
                "table_id": best_cid,
                "self_score": e_self.get("score", 0),
                "other_score": e_other.get("score", 0),
                "rank": e_self.get("rank", 0),
                "num_teams": e_self.get("numTeams", 0),
                "delta": e_self.get("mmrDelta", 0),
            }

        p1_best_match = _best_performance(c1, c2)
        p2_best_match = _best_performance(c2, c1)

        recent = []
        for cid in partner_ids[:10]:
            e1 = c1[cid]
            e2 = c2[cid]
            recent.append(
                {
                    "date": e1["time"][:10],
                    "tier": e1.get("tier", "?"),
                    "p1_score": e1.get("score", 0),
                    "p2_score": e2.get("score", 0),
                    "rank": e1.get("rank", 0),
                    "num_teams": e1.get("numTeams", 0),
                    "delta": e1.get("mmrDelta", 0),
                }
            )

        stats = {
            "p1_name": p1["name"],
            "p2_name": p2["name"],
            "p1_country": p1.get("countryCode", ""),
            "p2_country": p2.get("countryCode", ""),
            "p1_mmr": p1.get("mmr"),
            "p2_mmr": p2.get("mmr"),
            "shared": n,
            "wins": wins,
            "losses": losses,
            "total_delta": total_delta,
            "p1_avg_score": p1_avg,
            "p2_avg_score": p2_avg,
            "p1_best_score": p1_best,
            "p2_best_score": p2_best,
            # avg_rank is computed and exposed for future use but not
            # currently rendered in the partner plot.
            "avg_rank": avg_rank,
            "win_rate": win_rate,
            "p1_best_match": p1_best_match,
            "p2_best_match": p2_best_match,
            "recent": recent,
        }

        plot_image = create_partner_plot(
            stats=stats, season=season, game_mode=game_mode
        )
        file = discord.File(plot_image, filename="partner.png")

        embed = discord.Embed(
            title=f"S{season} Partner - {cfg.label(game_mode)}",
            description=f"### {p1['name']} & {p2['name']}",
            colour=0x1DA3DD,
            timestamp=dt.datetime.now(dt.UTC),
        )
        embed.set_image(url="attachment://partner.png")
        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command(
        name="scores", description=f"Show {cfg.DISPLAY_NAME} Player Score Breakdown"
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        season="Season number (default: current season)",
        tier="Filter by tier (default: all tiers)",
        last="Limit to the last N matches (default: all matches)",
        show_partner_scores="Overlay partner scores on the plot (default: No)",
    )
    @app_commands.choices(
        tier=[app_commands.Choice(name=t, value=t) for t in TIER_ORDER],
        show_partner_scores=[
            app_commands.Choice(name="Yes", value="yes"),
            app_commands.Choice(name="No", value="no"),
        ],
    )
    @game_mode_option
    async def scores(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
        tier: str | None = None,
        last: int | None = None,
        show_partner_scores: str | None = "no",
    ):
        if await reject_unsupported_season(interaction, season):
            return
        await interaction.response.defer()

        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player_info(name, season, game_mode)

        if player is None:
            await interaction.followup.send(
                f"Player '{name}' not found.", ephemeral=True
            )
            return

        table_events = [
            e for e in player.get("mmrChanges", []) if e.get("reason") == "Table"
        ]
        # API returns most recent first; reverse so x-axis is oldest -> newest
        table_events.reverse()

        if tier is not None:
            table_events = [e for e in table_events if e.get("tier") == tier]

        if last is not None and last > 0:
            table_events = table_events[-last:]

        scores_list = [e.get("score", 0) for e in table_events]

        if len(scores_list) < 2:
            tier_msg = f" in tier {tier}" if tier else ""
            await interaction.followup.send(
                f"Not enough {game_mode} matches{tier_msg} to build a score breakdown.",
                ephemeral=True,
            )
            return

        avg_score = statistics.mean(scores_list)
        median_score = statistics.median(scores_list)
        top_score = max(scores_list)
        std_dev = statistics.stdev(scores_list)

        if last is not None and last > 0:
            label = f"Last {len(scores_list)} Matches"
        else:
            label = f"In the Last {len(scores_list)} Matches"

        show_partners = show_partner_scores == "yes"
        partner_scores_per_match = None
        partner_avg = None
        if show_partners:
            partner_scores_per_match = [
                e.get("partnerScores", []) or [] for e in table_events
            ]
            flat_partner_scores = [
                p for partners in partner_scores_per_match for p in partners
            ]
            partner_avg = (
                statistics.mean(flat_partner_scores) if flat_partner_scores else None
            )

        plot_image = create_scores_plot(
            scores=scores_list,
            average=avg_score,
            season=season,
            player_name=player["name"],
            country_code=player.get("countryCode", ""),
            game_mode=game_mode,
            tier=tier,
            label=label,
            partner_scores=partner_scores_per_match,
            partner_average=partner_avg,
        )
        file = discord.File(plot_image, filename="scores.png")

        rank_data = constants.get_rank_info(player["rank"])
        title_tier = f" | Tier: {tier}" if tier else ""
        embed = discord.Embed(
            title=f"S{season} Scores{title_tier} | {label}",
            url=cfg.player_url(player["playerId"], game_mode),
            description=f"### {player['name']} [{player['countryCode']}]",
            colour=int(f"0x{rank_data['color'][1:]}", 16),
            timestamp=dt.datetime.now(dt.UTC),
        )

        embed.add_field(name="Average Score", value=f"{avg_score:.1f}", inline=True)
        embed.add_field(name="Top Score", value=f"{top_score}", inline=True)
        embed.add_field(name="​", value="​", inline=True)

        embed.add_field(name="Median Score", value=f"{median_score:g}", inline=True)
        embed.add_field(name="Standard Deviation", value=f"{std_dev:.1f}", inline=True)
        embed.add_field(name="​", value="​", inline=True)

        embed.set_image(url="attachment://scores.png")
        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        embed.set_thumbnail(url=rank_data["url"])

        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command(name="calc", description="Calculate Expected MMR changes")
    @app_commands.describe(table_id="Table ID for the match")
    async def calc(self, interaction: discord.Interaction, table_id: str):
        table_details = await api.fetch_table(table_id=table_id)
        if table_details is None:
            await interaction.response.send_message("Table not found!", ephemeral=True)
            return

        calced_deltas = calc_mmr_deltas(table_details)

        mmr_message = "```\n"
        names = []
        old_mmrs = []
        new_mmrs = []
        deltas = []
        for i, team in enumerate(table_details["teams"]):
            for player in team["scores"]:
                names.append(player["playerName"])
                old_mmrs.append(player["prevMmr"])
                new_mmrs.append(player["prevMmr"] + calced_deltas[i])
                deltas.append(calced_deltas[i])
        len_names = max(map(len, names))
        len_old_mmrs = len(str(max(old_mmrs)))
        len_new_mmrs = len(str(max(new_mmrs)))
        len_deltas = len(str(max(deltas)))
        for i in range(len(names)):
            if (
                i % (table_details["numPlayers"] / table_details["numTeams"]) == 0
                and table_details["numPlayers"] != table_details["numTeams"]
                and i != 0
            ):
                mmr_message += "\n"
            mmr_message += f"{names[i].ljust(len_names)}: {str(old_mmrs[i]).ljust(len_old_mmrs)} --> {str(new_mmrs[i]).ljust(len_new_mmrs)} ({str(deltas[i]).rjust(len_deltas)})\n"  # noqa: E501
        mmr_message += "```"

        embed = discord.Embed(
            title=f"Expected MMR Changes for Table ID: {table_id}",
            url=cfg.table_url(table_id),
            colour=0x1DA3DD,
            timestamp=dt.datetime.now(dt.UTC),
        )
        embed.add_field(name="Expected MMR Changes", value=mmr_message, inline=False)
        embed.set_image(
            url=(os.getenv("WEBSITE_URL") + f"/TableImage/{table_details['id']}.png")
        )
        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="streak", description=f"Show {cfg.DISPLAY_NAME} Player Win/Loss Streaks"
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        season="Season number (default: current season)",
    )
    @game_mode_option
    async def streak(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
    ):
        if await reject_unsupported_season(interaction, season):
            return
        await interaction.response.defer()

        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player_info(name, season, game_mode)

        if player is None:
            await interaction.followup.send(
                f"Player '{name}' not found.", ephemeral=True
            )
            return

        table_events = [
            e for e in player.get("mmrChanges", []) if e.get("reason") == "Table"
        ]
        if not table_events:
            await interaction.followup.send(
                f"{player['name']} has no {game_mode} matches in S{season}.",
                ephemeral=True,
            )
            return

        # API returns newest-first; we want oldest-first for streak walks
        chronological = sorted(table_events, key=lambda e: e["time"])

        def sign(d: int) -> int:
            return 1 if d > 0 else (-1 if d < 0 else 0)

        # Current streak: walk newest -> oldest while the sign holds
        latest_sign = sign(chronological[-1].get("mmrDelta", 0))
        cur_count = 0
        cur_delta = 0
        if latest_sign != 0:
            for e in reversed(chronological):
                if sign(e.get("mmrDelta", 0)) != latest_sign:
                    break
                cur_count += 1
                cur_delta += e.get("mmrDelta", 0)

        # Longest run for a given sign across the whole season
        def longest_run(target: int) -> dict:
            best = {"count": 0, "delta": 0, "start": None, "end": None}
            run_count = 0
            run_delta = 0
            run_start = None
            run_end = None
            for e in chronological:
                d = e.get("mmrDelta", 0)
                if sign(d) == target:
                    if run_count == 0:
                        run_start = e.get("time")
                    run_count += 1
                    run_delta += d
                    run_end = e.get("time")
                else:
                    if run_count > best["count"]:
                        best = {
                            "count": run_count,
                            "delta": run_delta,
                            "start": run_start,
                            "end": run_end,
                        }
                    run_count = 0
                    run_delta = 0
                    run_start = None
                    run_end = None
            if run_count > best["count"]:
                best = {
                    "count": run_count,
                    "delta": run_delta,
                    "start": run_start,
                    "end": run_end,
                }
            return best

        longest_win = longest_run(1)
        longest_loss = longest_run(-1)

        # The current run is part of the season, so longest_*['count'] already
        # includes it. Equality means the active run *is* the season longest.
        win_active = (
            cur_count > 0 and latest_sign == 1 and cur_count >= longest_win["count"]
        )
        loss_active = (
            cur_count > 0 and latest_sign == -1 and cur_count >= longest_loss["count"]
        )

        def fmt_date_range(
            start: str | None, end: str | None, active: bool = False
        ) -> str:
            if start is None:
                return ""
            s = int(datetime.fromisoformat(start).timestamp())
            if active:
                return f"<t:{s}:d> – active"
            if end is None:
                return ""
            e = int(datetime.fromisoformat(end).timestamp())
            if s == e:
                return f"<t:{s}:d>"
            return f"<t:{s}:d> – <t:{e}:d>"

        if cur_count == 0:
            cur_label = "No active streak"
            cur_value = "Last match was a tie."
        else:
            kind = "Win" if latest_sign == 1 else "Loss"
            cur_label = f"Current {kind} Streak"
            cur_noun = "match" if cur_count == 1 else "matches"
            cur_value = f"```\n{cur_count} {cur_noun} ({cur_delta:+d} MMR)\n```"

        win_noun = "match" if longest_win["count"] == 1 else "matches"
        win_value = (
            f"```\n{longest_win['count']} {win_noun} ({longest_win['delta']:+d} MMR)\n```"
            if longest_win["count"] > 0
            else "```\nNone\n```"
        )
        win_range = fmt_date_range(
            longest_win["start"], longest_win["end"], active=win_active
        )

        loss_noun = "match" if longest_loss["count"] == 1 else "matches"
        loss_value = (
            f"```\n{longest_loss['count']} {loss_noun} ({longest_loss['delta']:+d} MMR)\n```"  # noqa: E501
            if longest_loss["count"] > 0
            else "```\nNone\n```"
        )
        loss_range = fmt_date_range(
            longest_loss["start"], longest_loss["end"], active=loss_active
        )

        # Last-N strip: newest on the right, oldest on the left
        last_n = chronological[-10:]
        # Cells in the visual strip that belong to the active streak
        strip_streak_count = min(cur_count, len(last_n))

        plot_image = create_streak_plot(
            events=last_n,
            current_streak_count=strip_streak_count,
            season=season,
            player_name=player["name"],
            country_code=player.get("countryCode", ""),
            game_mode=game_mode,
            mmr=player.get("mmr"),
        )
        file = discord.File(plot_image, filename="streak.png")

        rank_data = constants.get_rank_info(player["rank"])
        mmr_suffix = f" · {player['mmr']} MMR" if player.get("mmr") is not None else ""
        embed = discord.Embed(
            title=f"S{season} Streaks - {cfg.label(game_mode)}",
            url=cfg.player_url(player["playerId"], game_mode),
            description=f"### {player['name']}{mmr_suffix} [{player['countryCode']}]",
            colour=int(f"0x{rank_data['color'][1:]}", 16),
            timestamp=dt.datetime.now(dt.UTC),
        )
        embed.set_image(url="attachment://streak.png")
        embed.add_field(name=cur_label, value=cur_value, inline=False)
        embed.add_field(
            name="Longest Win Streak",
            value=win_value + (win_range if win_range else ""),
            inline=True,
        )
        embed.add_field(
            name="Longest Loss Streak",
            value=loss_value + (loss_range if loss_range else ""),
            inline=True,
        )
        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        embed.set_thumbnail(url=rank_data["url"])

        await interaction.followup.send(embed=embed, file=file)

    async def _activity_histogram(
        self,
        interaction: discord.Interaction,
        name: str | None,
        season: int | None,
        game_mode: str | None,
        timezone: str | None,
        period: str,
    ):
        if await reject_unsupported_season(interaction, season):
            return
        await interaction.response.defer()

        resolved = _resolve_timezone(timezone)
        if resolved is None:
            supported = ", ".join(sorted(ABBREV_TO_IANA))
            await interaction.followup.send(
                f"Unknown timezone '{timezone}'. Supported: {supported}.",
                ephemeral=True,
            )
            return
        tz_label, tz = resolved

        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player_info(name, season, game_mode)

        if player is None:
            await interaction.followup.send(
                f"Player '{name}' not found.", ephemeral=True
            )
            return

        table_events = [
            e for e in player.get("mmrChanges", []) if e.get("reason") == "Table"
        ]

        if period == "daily":
            cutoff_date = dt.datetime.now(tz).date() - dt.timedelta(days=14)
            buckets: dict = {}
            for e in table_events:
                local_dt = datetime.fromisoformat(e["time"]).astimezone(tz)
                d = local_dt.date()
                if d >= cutoff_date:
                    b = buckets.setdefault(d, {"count": 0, "delta": 0})
                    b["count"] += 1
                    b["delta"] += e.get("mmrDelta", 0)
            ordered = sorted(buckets.items())
            lines = []
            for d, b in ordered:
                ts = int(dt.datetime.combine(d, dt.time(0, 0), tzinfo=tz).timestamp())
                lines.append(f"<t:{ts}:d> : {b['count']} ({b['delta']:+d} MMR)")
            field_value = "\n".join(lines) if lines else ""
            empty_msg = (
                f"{player['name']} has no {game_mode} matches in the last 14 days."
            )
            title = f"S{season} Daily Data - {cfg.label(game_mode)}"
        elif period == "weekly":
            buckets = {}
            for e in table_events:
                local_dt = datetime.fromisoformat(e["time"]).astimezone(tz)
                d = local_dt.date()
                monday = d - dt.timedelta(days=d.weekday())
                sunday = monday + dt.timedelta(days=6)
                key = (monday, sunday)
                b = buckets.setdefault(key, {"count": 0, "delta": 0})
                b["count"] += 1
                b["delta"] += e.get("mmrDelta", 0)
            ordered = sorted(buckets.items(), key=lambda kv: kv[0][0])
            lines = [
                f"{monday.isoformat()}/{sunday.isoformat()}: "
                f"{b['count']} ({b['delta']:+d} MMR)"
                for (monday, sunday), b in ordered
            ]
            field_value = "```\n" + "\n".join(lines) + "\n```" if lines else ""
            empty_msg = f"{player['name']} has no {game_mode} matches this season."
            title = f"S{season} Weekly Data - {cfg.label(game_mode)}"
        else:  # monthly
            buckets = {}
            for e in table_events:
                local_dt = datetime.fromisoformat(e["time"]).astimezone(tz)
                key = local_dt.strftime("%Y-%m")
                b = buckets.setdefault(key, {"count": 0, "delta": 0})
                b["count"] += 1
                b["delta"] += e.get("mmrDelta", 0)
            ordered = sorted(buckets.items())
            lines = [f"{ym}: {b['count']} ({b['delta']:+d} MMR)" for ym, b in ordered]
            field_value = "\n".join(lines) if lines else ""
            empty_msg = f"{player['name']} has no {game_mode} matches this season."
            title = f"S{season} Monthly Data - {cfg.label(game_mode)}"

        if not lines:
            await interaction.followup.send(empty_msg, ephemeral=True)
            return

        total = sum(b["count"] for _, b in ordered)
        total_delta = sum(b["delta"] for _, b in ordered)

        mmr = player.get("mmr")
        mmr_part = f" - {mmr} MMR" if mmr is not None else ""

        rank_data = constants.get_rank_info(player["rank"])
        embed = discord.Embed(
            title=title,
            url=cfg.player_url(player["playerId"], game_mode),
            description=f"### {player['name']} [{player['countryCode']}]{mmr_part}",
            colour=int(f"0x{rank_data['color'][1:]}", 16),
            timestamp=dt.datetime.now(dt.UTC),
        )
        embed.add_field(
            name=f"Events Played: {total} ({total_delta:+d} MMR)",
            value=field_value,
            inline=False,
        )
        embed.set_footer(text=f"Timezone: {tz_label} · MKCentral Lounge")
        embed.set_thumbnail(url=rank_data["url"])

        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="dd",
        description=f"Show {cfg.DISPLAY_NAME} events played per day (last 14 days)",
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        season="Season number (default: current season)",
        timezone="Timezone abbreviation, e.g. EST, JST (default: UTC)",
    )
    @game_mode_option
    async def dd(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
        timezone: str | None = "UTC",
    ):
        await self._activity_histogram(
            interaction, name, season, game_mode, timezone, "daily"
        )

    @app_commands.command(
        name="wd",
        description=f"Show {cfg.DISPLAY_NAME} events played per week (this season)",
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        season="Season number (default: current season)",
        timezone="Timezone abbreviation, e.g. EST, JST (default: UTC)",
    )
    @game_mode_option
    async def wd(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
        timezone: str | None = "UTC",
    ):
        await self._activity_histogram(
            interaction, name, season, game_mode, timezone, "weekly"
        )

    @app_commands.command(
        name="md",
        description=f"Show {cfg.DISPLAY_NAME} events played per month (this season)",
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        season="Season number (default: current season)",
        timezone="Timezone abbreviation, e.g. EST, JST (default: UTC)",
    )
    @game_mode_option
    async def md(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = cfg.DEFAULT_GAME_MODE,
        timezone: str | None = "UTC",
    ):
        await self._activity_histogram(
            interaction, name, season, game_mode, timezone, "monthly"
        )

    @app_commands.command(
        name="predict",
        description="Predict MMR changes for each finish position from a room post",
    )
    @app_commands.describe(
        text="Paste the room post (lines like '1. name (5831 MMR)' or "
        "'1. a, b, c (5630 MMR)')",
        seed="Your seed (defaults to the team containing your lounge name)",
    )
    async def predict(
        self,
        interaction: discord.Interaction,
        text: str,
        seed: int | None = None,
    ):
        await interaction.response.defer()

        try:
            teams = parse_room(text)
        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral=True)
            return

        num_teams = len(teams)
        players_per_team = len(teams[0]["names"])
        num_players = num_teams * players_per_team

        supported_sizes = (12, 24) if _MAX_PLAYERS == 24 else (12,)
        if num_players not in supported_sizes:
            expected = "- or ".join(str(size) for size in supported_sizes)
            await interaction.followup.send(
                f"Only {expected}-player rooms are supported (parsed "
                f"{num_players} players in {num_teams} teams).",
                ephemeral=True,
            )
            return

        if seed is None:
            game_mode = "24p" if num_players == 24 else "12p"
            season = os.getenv("CURRENT_SEASON")
            player = await data_handler.fetch_player(
                str(interaction.user.id), season, game_mode
            )
            if player is None or "name" not in player:
                await interaction.followup.send(
                    "Couldn't find your lounge profile from your Discord ID. "
                    "Pass `seed` manually.",
                    ephemeral=True,
                )
                return
            target = player["name"].casefold()
            matches = [
                t["seed"]
                for t in teams
                if any(n.casefold() == target for n in t["names"])
            ]
            if not matches:
                await interaction.followup.send(
                    f"Couldn't find **{player['name']}** in the room. "
                    "Pass `seed` manually.",
                    ephemeral=True,
                )
                return
            if len(matches) > 1:
                await interaction.followup.send(
                    f"Found **{player['name']}** in multiple teams "
                    f"(seeds {matches}). Pass `seed` manually.",
                    ephemeral=True,
                )
                return
            seed = matches[0]

        if not 1 <= seed <= num_teams:
            await interaction.followup.send(
                f"Seed must be between 1 and {num_teams}.", ephemeral=True
            )
            return

        try:
            deltas = predict_deltas(teams)[seed - 1]
        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral=True)
            return

        team = teams[seed - 1]
        if players_per_team == 1:
            label = team["names"][0]
        else:
            label = f"Team {seed}: " + ", ".join(team["names"])

        def ord_suffix(n: int) -> str:
            if 10 <= n % 100 <= 20:
                return "th"
            return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

        cells = [
            f"{p}{ord_suffix(p)}: {deltas[p - 1]:+d}" for p in range(1, num_teams + 1)
        ]
        cell_w = max(len(c) for c in cells)
        # Cap at 2 columns so rows stay narrow enough for mobile Discord.
        cols = 2 if num_teams >= 8 else 1
        rows_per_col = (num_teams + cols - 1) // cols
        lines: list[str] = []
        for r in range(rows_per_col):
            parts = []
            for c in range(cols):
                idx = c * rows_per_col + r
                if idx < num_teams:
                    parts.append(cells[idx].ljust(cell_w))
            lines.append("   ".join(parts).rstrip())
        block = "```\n" + "\n".join(lines) + "\n```"

        embed = discord.Embed(
            title=f"Predicted MMR Changes for {label}",
            colour=0x1DA3DD,
            timestamp=dt.datetime.now(dt.UTC),
        )
        embed.add_field(
            name=f"Δ MMR by finish position (seed {seed}, {team['mmr']} MMR)",
            value=block,
            inline=False,
        )
        embed.set_footer(
            text="These numbers are just an estimate — your actual MMR change will be different.",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))
