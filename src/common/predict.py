import re

from common.calculation import calc_mmr_deltas, n_players_dict, n_teams_dict

_ENTRY_RE = re.compile(r"(\d+)\.\s+(.+?)\s+\((\d+)\s*MMR\)", re.DOTALL)


def parse_room(text: str) -> list[dict]:
    """Extract teams from a room post.

    Each returned entry: {"seed": int, "names": list[str], "mmr": int}.
    Matches are pulled from anywhere in the text, so headers, mentions, and
    footers are ignored — and inputs that arrive on a single line (Discord
    slash command params strip newlines) still work.
    """
    # Strip Discord inline-code backticks; the bot wraps seeds and commands
    # in them (e.g. "`1.` amity, ...") which would otherwise break the regex.
    text = text.replace("`", "")

    teams: list[dict] = []
    seen_seeds: set[int] = set()
    for seed_str, names_str, mmr_str in _ENTRY_RE.findall(text):
        seed = int(seed_str)
        if seed in seen_seeds:
            continue
        seen_seeds.add(seed)
        names = [n.strip() for n in names_str.split(",") if n.strip()]
        teams.append({"seed": seed, "names": names, "mmr": int(mmr_str)})

    if not teams:
        raise ValueError(
            "Could not find any '<seed>. names (NNNN MMR)' entries in the input."
        )

    teams.sort(key=lambda t: t["seed"])
    if [t["seed"] for t in teams] != list(range(1, len(teams) + 1)):
        raise ValueError("Seed numbers must be contiguous starting from 1.")

    sizes = {len(t["names"]) for t in teams}
    if len(sizes) != 1:
        raise ValueError("All teams must have the same number of players.")

    return teams


def predict_deltas(teams: list[dict]) -> list[list[int]]:
    """Build a grid of predicted MMR deltas.

    grid[t][p - 1] = predicted delta for the team at index ``t`` if it
    finishes at position ``p``. The other teams are assumed to fill the
    remaining positions in seed order — i.e., the chosen team is shuffled
    to position ``p`` and everyone else stays in their original ordering.
    """
    num_teams = len(teams)
    players_per_team = len(teams[0]["names"])
    if num_teams not in n_teams_dict or players_per_team not in n_players_dict:
        raise ValueError(
            f"Unsupported format: {num_teams} teams of {players_per_team}."
        )

    num_players = num_teams * players_per_team
    grid: list[list[int]] = []
    for t in range(num_teams):
        row: list[int] = []
        others = [i for i in range(num_teams) if i != t]
        for p in range(1, num_teams + 1):
            other_ranks = [r for r in range(1, num_teams + 1) if r != p]
            rank_for = {t: p}
            for j, idx in enumerate(others):
                rank_for[idx] = other_ranks[j]
            table = {
                "numPlayers": num_players,
                "numTeams": num_teams,
                "teams": [
                    {
                        "rank": rank_for[i],
                        "scores": [{"prevMmr": teams[i]["mmr"]}] * players_per_team,
                    }
                    for i in range(num_teams)
                ],
            }
            row.append(calc_mmr_deltas(table)[t])
        grid.append(row)
    return grid
