n_teams_dict = {2: 100, 3: 80, 4: 60, 6: 40, 8: 30, 12: 20, 24: 10}

n_players_dict = {
    1: 2746.116,
    2: 1589.856,
    3: 1474.230,
    4: 1387.511,
    6: 1344.151,
    8: 1315.245,
    12: 1300.792,
}


def calc_mmr_deltas(mmr_data: dict) -> dict:

    n_players = mmr_data["numPlayers"] / mmr_data["numTeams"]
    n_teams = mmr_data["numTeams"]
    cap = n_teams_dict[n_teams] * 3

    def calc_mmr_delta_for_winner(winner_mmr: float, loser_mmr: float) -> float:
        return cap / (
            1 + 2 ** (1 - ((loser_mmr - winner_mmr) / n_players_dict[n_players]))
        )

    def calc_mmr_delta_for_tie(mmr1: float, mmr2: float) -> float:
        gap = abs(mmr1 - mmr2)
        return (
            cap / (1 + 2 ** (1 - (gap / n_players_dict[n_players])))
            - n_teams_dict[n_teams]
        )

    def calc_mmr_delta(team: int) -> float:
        average_mmr = (
            sum(player["prevMmr"] for player in mmr_data["teams"][team]["scores"])
            / n_players
        )
        rank = mmr_data["teams"][team]["rank"]
        mmr_delta = 0.0

        for other_team in range(n_teams):
            if team == other_team:
                continue

            other_average_mmr = (
                sum(
                    player["prevMmr"]
                    for player in mmr_data["teams"][other_team]["scores"]
                )
                / n_players
            )
            other_rank = mmr_data["teams"][other_team]["rank"]

            if rank == other_rank:
                sign = 1 if average_mmr < other_average_mmr else -1
                mmr_delta += sign * calc_mmr_delta_for_tie(
                    average_mmr, other_average_mmr
                )
            elif rank < other_rank:
                mmr_delta += calc_mmr_delta_for_winner(average_mmr, other_average_mmr)
            else:
                mmr_delta -= calc_mmr_delta_for_winner(other_average_mmr, average_mmr)

        return round(mmr_delta)

    deltas = [calc_mmr_delta(team) for team in range(n_teams)]
    return deltas
