import os

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

mods_role_ids = set(
    int(role_id) for role_id in os.getenv("Mods_Role_ID", "").split(",") if role_id
)


def is_mod():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise app_commands.NoPrivateMessage()
        user_role_ids = {role.id for role in interaction.user.roles}
        if mods_role_ids.isdisjoint(user_role_ids):
            raise app_commands.MissingAnyRole(list(mods_role_ids))
        return True

    return app_commands.check(predicate)
