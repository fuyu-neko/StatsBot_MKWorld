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
from common.plotting import create_plot
from common.calculation import calc_mmr_deltas

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

        timestamp_d2 = datetime.fromisoformat(table_details["verifiedOn"])
        unix_time2 = int(timestamp_d2.timestamp())

        embed.add_field(
            name="Verified On", value=f"Changed On <t:{unix_time2}:s>", inline=False
        )

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

        timestamp_d2 = datetime.fromisoformat(table_details["verifiedOn"])
        unix_time2 = int(timestamp_d2.timestamp())

        embed.add_field(
            name="Created On", value=f"Changed On <t:{unix_time1}:s>", inline=False
        )
        embed.add_field(
            name="Verified On", value=f"Changed On <t:{unix_time2}:s>", inline=False
        )

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

        embed.add_field(name="MMR Changes ", value=mmr_message, inline=True)
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


async def setup(bot):
    await bot.add_cog(Stats(bot))
