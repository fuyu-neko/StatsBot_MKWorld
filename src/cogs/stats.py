import asyncio
import datetime as dt
import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import API.get_mkworld as api
import common.constants as constants
import common.data_handler as data_handler
from common.calculation import calc_mmr_deltas
from common.plotting import create_plot, create_tiers_plot
from common.predict import calc_predicted_deltas

# load environment variables from .env file
load_dotenv()


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mmr", description="Show MKWorld Player MMR")
    @app_commands.describe(
        names="comma-separated list of player names, discord ids, mkc ids (optional)",
        season="Season number (default: current season)",
        game_mode="Game mode (default: 24p)",
    )
    @app_commands.choices(
        game_mode=[
            app_commands.Choice(name="24p", value="24p"),
            app_commands.Choice(name="12p", value="12p"),
        ]
    )
    async def mmr(
        self,
        interaction: discord.Interaction,
        names: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = "24p",
    ):
        # if multiple names are provided,
        # split them into a list and fetch MMR data for each player

        # If no names are provided, default to the user's ID
        if names is None:
            names = str(interaction.user.id)
        if len(names.split(",")) == 1:
            # Call API to fetch players MMR data
            player = await data_handler.fetch_player_info(names, season, game_mode)

            # return error message if player is not found
            if player is None:
                await interaction.response.send_message(
                    f"Player '{names}' not found.",
                    ephemeral=True,
                )
                return

            # return error message if player has no MMR data
            if "mmr" not in player:
                await interaction.response.send_message(
                    "You have to play at least 1 match to check your MMR.",
                    ephemeral=True,
                )
                return

            rank_data = constants.get_rank_data(season)[player["rank"]]
            embed = discord.Embed(
                title=f"S{season} MMR - MKWorld{game_mode.upper()}",
                url=f"https://lounge.mkcentral.com/mkworld/PlayerDetails/{player['playerId']}?p={game_mode[0:1]}",
                colour=int(f"0x{rank_data['color'][1:]}", 16),
                timestamp=dt.datetime.now(dt.UTC),
            )

            embed.add_field(
                name=player["name"], value=f"```\n{player['mmr']}\n```", inline=False
            )
            embed.set_footer(
                text="MKCentral Lounge",
                icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
            )
            await interaction.response.send_message(embed=embed)

        else:
            embed = discord.Embed(
                title=f"S{season} MMR - MKWorld{game_mode.upper()}",
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
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stats", description="Show MKWorld Player Stats")
    @app_commands.describe(
        name="Lounge name, discord ids, mkc ids (optional)",
        season="Season number (default: current season)",
        game_mode="Game mode (default: 24p)",
    )
    @app_commands.choices(
        game_mode=[
            app_commands.Choice(name="24p", value="24p"),
            app_commands.Choice(name="12p", value="12p"),
        ]
    )
    async def stats(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = "24p",
    ):
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

        rank_data = constants.get_rank_data(season)[player["rank"]]

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
            title=f"S{season} Stats - MKWorld{game_mode.upper()}",
            url=f"https://lounge.mkcentral.com/mkworld/PlayerDetails/{player['playerId']}?p={game_mode[0:1]}",
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
        name="lastmatch", description="Show MKWorld Player Last Verified Match"
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        game_mode="Game mode (default: most recent across both 12p and 24p)",
    )
    @app_commands.choices(
        game_mode=[
            app_commands.Choice(name="24p", value="24p"),
            app_commands.Choice(name="12p", value="12p"),
        ]
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
        modes = [game_mode] if game_mode is not None else ["24p", "12p"]

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

    @app_commands.command(name="table", description="Show MKWorld Match Details")
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
                value="Unverified — MMR changes shown are expected values and may differ from the final result.",
                inline=False,
            )
        calced_deltas = (
            None if is_verified else calc_mmr_deltas(table_details)
        )

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

    @app_commands.command(name="namelog", description="View a player's name change history")
    @app_commands.describe(name="Player name, discord id, or mkc id (optional)")
    async def namelog(self, interaction: discord.Interaction, name: str | None = None):
        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player_info(
            name, season=os.getenv("CURRENT_SEASON"), game_mode="24p"
        )

        if player is None:
            await interaction.response.send_message(
                f"Player '{name}' not found.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Namelog for {player['name']}",
            url=f"https://lounge.mkcentral.com/mkworld/PlayerDetails/{player['playerId']}",
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

    @app_commands.command(name="fc", description="Show MKWorld Player Friend Code")
    @app_commands.describe(name="Player name, discord id, or mkc id (optional)")
    async def fc(self, interaction: discord.Interaction, name: str | None = None):
        if name is None:
            name = str(interaction.user.id)
        player = await data_handler.fetch_player(
            name, season=os.getenv("CURRENT_SEASON"), game_mode="24p"
        )

        if player is None:
            await interaction.response.send_message(
                f"Player '{name}' not found.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Friend Code for {player['name']}",
            url=f"https://lounge.mkcentral.com/mkworld/PlayerDetails/{player['id']}",
            timestamp=dt.datetime.now(dt.UTC),
        )

        embed.add_field(name="Friend Code", value=player["switchFc"], inline=False)
        embed.set_footer(
            text="MKCentral Lounge",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="tiers", description="Show MKWorld Player Performance by Tier"
    )
    @app_commands.describe(
        name="Lounge name, discord id, mkc id (optional)",
        season="Season number (default: current season)",
        game_mode="Game mode (default: 24p)",
    )
    @app_commands.choices(
        game_mode=[
            app_commands.Choice(name="24p", value="24p"),
            app_commands.Choice(name="12p", value="12p"),
        ]
    )
    async def tiers(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        season: int | None = int(os.getenv("CURRENT_SEASON")),
        game_mode: str | None = "24p",
    ):
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

        tier_order = [
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

        rank_data = constants.get_rank_data(season)[player["rank"]]
        embed = discord.Embed(
            title=f"S{season} Tiers - MKWorld{game_mode.upper()}",
            url=f"https://lounge.mkcentral.com/mkworld/PlayerDetails/{player['playerId']}?p={game_mode[0:1]}",
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
            value=f"{best_tier[0]} ({best_tier[1]['delta_sum'] / best_tier[1]['events']:+.0f} avg)",
            inline=True,
        )
        embed.add_field(
            name="Worst Tier",
            value=f"{worst_tier[0]} ({worst_tier[1]['delta_sum'] / worst_tier[1]['events']:+.0f} avg)",
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
            url=os.getenv("WEBSITE_URL") + f"/mkworld/TableDetails/{table_id}",
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


    _PLAYERS_PER_TEAM = {"ffa": 1, "2v2": 2, "3v3": 3}

    @app_commands.command(
        name="predict", description="Estimate MMR changes before a table is submitted"
    )
    @app_commands.describe(
        format="Mogi format",
        players="Copy-paste the player names from the scoreboard command in the mogi thread, separated by commas",
        seed="Your seed (team number) in the mogi",
    )
    @app_commands.choices(
        format=[
            app_commands.Choice(name="FFA", value="ffa"),
            app_commands.Choice(name="2v2", value="2v2"),
            app_commands.Choice(name="3v3", value="3v3"),
        ]
    )
    async def predict(
        self,
        interaction: discord.Interaction,
        format: str,
        players: str,
        seed: int,
    ):
        await interaction.response.defer()

        players_per_team = self._PLAYERS_PER_TEAM[format]
        player_names = [n.strip() for n in players.split(",") if n.strip()]
        total_players = len(player_names)

        if total_players not in (12, 24):
            await interaction.followup.send(
                f"Expected 12 or 24 players, got {total_players}. "
                "Please paste all player names from the mogi.",
                ephemeral=True,
            )
            return

        if total_players % players_per_team != 0:
            await interaction.followup.send(
                f"{total_players} players is not divisible by {players_per_team} "
                f"for {format.upper()} format.",
                ephemeral=True,
            )
            return

        num_teams = total_players // players_per_team
        game_mode = "24p" if total_players == 24 else "12p"

        if not (1 <= seed <= num_teams):
            await interaction.followup.send(
                f"Seed must be between 1 and {num_teams} for {format.upper()} "
                f"with {total_players} players.",
                ephemeral=True,
            )
            return

        season = os.getenv("CURRENT_SEASON")
        results = []
        for name in player_names:
            results.append(await data_handler.fetch_player(name, season, game_mode))
            await asyncio.sleep(0.1)

        failed = [
            name
            for name, result in zip(player_names, results)
            if result is None or "mmr" not in result
        ]
        if failed:
            failed_list = ", ".join(f"`{n}`" for n in failed)
            await interaction.followup.send(
                f"Could not find MMR for: {failed_list}\n"
                "Please check the names and try again.",
                ephemeral=True,
            )
            return

        mmr_by_name = {
            name: result["mmr"] for name, result in zip(player_names, results)
        }

        teams = [
            {
                "seed": i + 1,
                "names": player_names[i * players_per_team : (i + 1) * players_per_team],
                "mmr": sum(
                    mmr_by_name[n]
                    for n in player_names[i * players_per_team : (i + 1) * players_per_team]
                )
                / players_per_team,
            }
            for i in range(num_teams)
        ]

        my_team = teams[seed - 1]
        my_mmr = my_team["mmr"]
        avg_opp_mmr = sum(t["mmr"] for t in teams if t["seed"] != seed) / (num_teams - 1)

        deltas = calc_predicted_deltas(my_mmr, avg_opp_mmr, num_teams, players_per_team)

        rows = [
            f"{rank}. {'+' if delta >= 0 else ''}{delta}"
            for rank, delta in enumerate(deltas, 1)
        ]
        half = (len(rows) + 1) // 2
        code = "```\n"
        for i in range(half):
            left = rows[i]
            right = rows[half + i] if half + i < len(rows) else ""
            code += f"{left.ljust(12)} {right}\n"
        code += "```"

        if players_per_team == 1:
            label = my_team["names"][0]
            if len(label) > 30:
                label = label[:27] + "..."
        else:
            label = f"Team {seed}"

        embed = discord.Embed(
            title=f"Estimated MMR Changes for {label}",
            colour=0x1DA3DD,
            timestamp=dt.datetime.now(dt.UTC),
        )
        embed.add_field(name=label, value=code, inline=False)
        embed.set_footer(
            text="Actual results may vary. Use /calc once a table is submitted.",
            icon_url="https://raw.githubusercontent.com/VikeMK/Lounge-API/refs/heads/main/src/Lounge.Web/wwwroot/favicon.ico",
        )
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))
