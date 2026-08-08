import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from common import game_config as cfg

load_dotenv()

if os.getenv("DEBUG_MODE", "False").lower() == "true":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
logging.getLogger("discord").setLevel(logging.INFO)
logging.getLogger("matplotlib").setLevel(logging.INFO)

cogs = ["cogs.stats", "cogs.staff"]


class StatsBot(commands.AutoShardedBot):
    def __init__(self):
        # command_prefix is required by commands.Bot; unused since all commands are slash commands.
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
        )

    async def on_ready(self):
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logging.info("------")

    async def setup_hook(self) -> None:
        await self.tree.sync()


bot = StatsBot()


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    if isinstance(error, app_commands.MissingAnyRole):
        msg = "You don't have the required role to execute this command."
    elif isinstance(error, app_commands.NoPrivateMessage):
        msg = "This command cannot be used in private messages."
    elif isinstance(error, app_commands.CheckFailure):
        msg = "You don't meet the requirements to execute this command."
    else:
        cmd_name = interaction.command.name if interaction.command else "?"
        logging.error(
            f"App command error in /{cmd_name} "
            f"by {interaction.user} (id={interaction.user.id}) "
            f"in guild={interaction.guild_id}",
            exc_info=error,
        )
        msg = "An unexpected error occurred. Please try again later."
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, app_commands.CommandNotFound):
        await ctx.send("Command not found. Use `^help` to see available commands.")
    elif isinstance(error, app_commands.BotMissingPermissions):
        await ctx.send(
            "I don't have the necessary permissions to execute this command."
        )
    elif isinstance(error, app_commands.MissingPermissions):
        await ctx.send(
            "You don't have the necessary permissions to execute this command."
        )
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"This command is on cooldown. \
                        Try again in {error.retry_after:.2f} seconds."
        )
    elif isinstance(error, app_commands.MissingAnyRole):
        await ctx.send("You don't have the required role to execute this command.")
    elif isinstance(error, app_commands.NoPrivateMessage):
        await ctx.send("This command cannot be used in private messages.")
    elif isinstance(error, app_commands.CheckFailure):
        await ctx.send("You don't meet the requirements to execute this command.")
    else:
        logging.error(f"An error occurred: {error}")
        await ctx.send("An unexpected error occurred. Please try again later.")


def get_bot_token() -> str:
    env = os.getenv("ENVIRONMENT", "staging").lower()
    if env not in ("staging", "production"):
        raise RuntimeError(
            f"ENVIRONMENT must be 'staging' or 'production', got '{env}'"
        )
    token_key = f"DISCORD_BOT_TOKEN_{env.upper()}"
    token = os.getenv(token_key)
    if not token:
        raise RuntimeError(f"{token_key} is not set in environment")
    logging.info(f"Starting {cfg.DISPLAY_NAME} bot in {env.upper()} mode")
    return token


async def main():
    async with bot:
        for extension in cogs:
            await bot.load_extension(extension)
        await bot.start(get_bot_token())


asyncio.run(main())
