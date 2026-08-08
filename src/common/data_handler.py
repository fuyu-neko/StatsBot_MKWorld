import re

from API import get_lounge as api_lounge


async def fetch_player(search_value: str | int, season: int, game_mode: str):
    # FC形式: XXXX-XXXX-XXXX (4桁-4桁-4桁, 計12桁)
    if re.fullmatch(r"\d{4}-\d{4}-\d{4}", search_value):
        return await api_lounge.fetch_player_by_fc(search_value, season, game_mode)

    # 数字のみの場合
    if search_value.isdigit():
        if len(search_value) >= 17:
            return await api_lounge.fetch_player_by_discord(
                search_value, season, game_mode
            )
        else:
            return await api_lounge.fetch_player_by_mkcid(
                int(search_value), season, game_mode
            )

    # 文字列の場合
    return await api_lounge.fetch_player_by_name(search_value, season, game_mode)


async def fetch_player_info(search_value: str | int, season: int, game_mode: str):
    # FC形式: XXXX-XXXX-XXXX (4桁-4桁-4桁, 計12桁)
    if re.fullmatch(r"\d{4}-\d{4}-\d{4}", search_value):
        return await api_lounge.fetch_player_info_by_fc(search_value, season, game_mode)

    # 数字のみの場合
    if search_value.isdigit():
        if len(search_value) >= 17:
            return await api_lounge.fetch_player_info_by_discord(
                search_value, season, game_mode
            )
        else:
            return await api_lounge.fetch_player_info_by_mkcid(
                int(search_value), season, game_mode
            )

    # 文字列の場合
    return await api_lounge.fetch_player_info_by_name(search_value, season, game_mode)
