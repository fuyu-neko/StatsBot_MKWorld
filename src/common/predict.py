import math

from common.calculation import n_players_dict, n_teams_dict


def calc_predicted_deltas(
    my_mmr: float,
    avg_opp_mmr: float,
    num_teams: int,
    players_per_team: int,
) -> list[int]:
    cap = n_teams_dict[num_teams] * 3
    gap = n_players_dict[players_per_team]
    win_sig = cap / (1 + math.pow(2, 1 - ((avg_opp_mmr - my_mmr) / gap)))
    loss_sig = cap / (1 + math.pow(2, 1 - ((my_mmr - avg_opp_mmr) / gap)))
    return [
        round((num_teams - rank) * win_sig - (rank - 1) * loss_sig)
        for rank in range(1, num_teams + 1)
    ]
