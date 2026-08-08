import logging
import os
from datetime import datetime, timedelta, timezone

import aiohttp
from dotenv import load_dotenv

from common import game_config as cfg

load_dotenv()

headers = {"Content-Type": "application/json"}
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=10)


async def fetch_strikes(player_name: str, season: int, game_mode: str):
    from_date = datetime.now(timezone.utc) - timedelta(days=30)
    url = f"{os.getenv('WEBSITE_URL')}/api/penalty/list?name={player_name}&isStrike=true&from={from_date.isoformat()}&season={season}&game={cfg.api_game(game_mode)}"  # noqa: E501
    logging.debug(f"Fetching strikes for {player_name} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(f"Received strikes data for {player_name}: {data}")
                return data
            else:
                return None


async def fetch_all_strikes(name: str, season: int, game_mode: str):
    url = f"{os.getenv('WEBSITE_URL')}/api/penalty/list?name={name}&isStrike=true&season={season}&game={cfg.api_game(game_mode)}"  # noqa: E501
    logging.debug(f"Fetching all strikes for {name} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(f"Received all strikes data for {name}: {data}")
                return data
            else:
                return None


async def fetch_player_by_name(player_name: str, season: int, game_mode: str):
    url = f"{os.getenv('WEBSITE_URL')}/api/player?name={player_name}&season={season}&game={cfg.api_game(game_mode)}"
    logging.debug(f"Fetching player data for {player_name} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(f"Received player data for {player_name}: {data}")
                return data
            else:
                return None


async def fetch_player_by_mkcid(mkcid: int, season: int, game_mode: str):
    url = f"{os.getenv('WEBSITE_URL')}/api/player?mkcid={mkcid}&season={season}&game={cfg.api_game(game_mode)}"  # noqa: E501
    logging.debug(f"Fetching player data for MKCID {mkcid} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(f"Received player data for MKCID {mkcid}: {data}")
                return data
            else:
                return None


async def fetch_player_by_discord(discord_id: str, season: int, game_mode: str):
    url = f"{os.getenv('WEBSITE_URL')}/api/player?discordId={discord_id}&season={season}&game={cfg.api_game(game_mode)}"  # noqa: E501
    logging.debug(f"Fetching player data for Discord ID {discord_id} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(
                    f"Received player data for Discord ID {discord_id}: {data}"
                )
                return data
            else:
                return None


async def fetch_player_by_fc(fc: str, season: int, game_mode: str):
    url = f"{os.getenv('WEBSITE_URL')}/api/player?fc={fc}&season={season}&game={cfg.api_game(game_mode)}"  # noqa: E501
    logging.debug(f"Fetching player data for FC {fc} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(f"Received player data for FC {fc}: {data}")
                return data
            else:
                return None


async def fetch_player_info_by_name(name: str, season: int, game_mode: str):
    url = f"{os.getenv('WEBSITE_URL')}/api/player/details?name={name}&season={season}&game={cfg.api_game(game_mode)}"  # noqa: E501
    logging.debug(f"Fetching player details for {name} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(f"Received player details for {name}: {data}")
                return data
            else:
                return None


async def fetch_player_info_by_mkcid(mkcid: int, season: int, game_mode: str):
    url = f"{os.getenv('WEBSITE_URL')}/api/player/details?mkcid={mkcid}&season={season}&game={cfg.api_game(game_mode)}"
    logging.debug(f"Fetching player details for MKCID {mkcid} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(f"Received player details for MKCID {mkcid}: {data}")
                return data
            else:
                return None


async def fetch_player_info_by_discord(discord_id: str, season: int, game_mode: str):
    url = f"{os.getenv('WEBSITE_URL')}/api/player/details?discordId={discord_id}&season={season}&game={cfg.api_game(game_mode)}"  # noqa: E501
    logging.debug(f"Fetching player details for Discord ID {discord_id} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(
                    f"Received player details for Discord ID {discord_id}: {data}"
                )
                return data
            else:
                return None


async def fetch_player_info_by_fc(fc: str, season: int, game_mode: str):
    url = f"{os.getenv('WEBSITE_URL')}/api/player/details?fc={fc}&season={season}&game={cfg.api_game(game_mode)}"  # noqa: E501
    logging.debug(f"Fetching player details for FC {fc} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(f"Received player details for FC {fc}: {data}")
                return data
            else:
                return None


async def fetch_table(table_id: int):
    url = f"{os.getenv('WEBSITE_URL')}/api/table?tableId={table_id}"  # noqa: E501
    logging.debug(f"Fetching table data for table ID {table_id} from {url}")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logging.debug(f"Received table data for table ID {table_id}: {data}")
                return data
            else:
                return None
