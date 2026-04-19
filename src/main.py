import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

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


async def main():
    async with bot:
        for extension in cogs:
            await bot.load_extension(extension)
        await bot.start(os.getenv("DISCORD_BOT_TOKEN"))


asyncio.run(main())
