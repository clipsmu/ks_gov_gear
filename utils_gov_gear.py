from copy import deepcopy

# gear order
PIECES = ["cap", "watch", "coat", "pants", "belt", "weapon"]

LEVEL_ORDER = [
    "Green", "Green*",
    "Blue", "Blue*", "Blue**", "Blue***",
    "Purple", "Purple*", "Purple**", "Purple***",
    "Purple T1", "Purple T1*", "Purple T1**", "Purple T1***",
    "Gold", "Gold*", "Gold**", "Gold***",
    "Gold T1", "Gold T1*", "Gold T1**", "Gold T1***"
]

TROOP_MAP = {
    "cap": "cavalry",
    "watch": "cavalry",
    "coat": "infantry",
    "pants": "infantry",
    "belt": "archer",
    "weapon": "archer"
}

# ----------------------------
# 🔹 SET BONUS
# ----------------------------
def compute_set_bonus(levels_list, levels, level_index):
    bonus = 0
    level_keys = list(levels.keys())

    for lvl in level_keys:
        idx = level_index[lvl]
        count = sum(1 for l in levels_list if level_index[l] >= idx)

        if count >= 3:
            bonus += 0.5 * 3  # DEF for 3 types
        if count >= 6:
            bonus += 0.5 * 3  # ATK for 3 types

    return bonus

def compute_set_bonus_detailed(levels_list, level_index):
    atk = 0
    deff = 0

    level_keys = list(level_index.keys())

    for lvl in level_keys:
        idx = level_index[lvl]
        count = sum(1 for l in levels_list if level_index[l] >= idx)

        if count >= 3:
            deff += 0.5 * 3  # DEF uniquement
        if count >= 6:
            atk += 0.5 * 3   # ATK uniquement

    return atk, deff

def compute_detailed_stats(sol, gear, level_index):
    stats = {
        "infantry": {"atk": 0, "def": 0},
        "archer": {"atk": 0, "def": 0},
        "cavalry": {"atk": 0, "def": 0},
    }

    # 🔹 Gain équipement
    for c in sol["combo"]:
        troop = TROOP_MAP[c["piece"]]
        gain = c["gain_items"]

        stats[troop]["atk"] += gain
        stats[troop]["def"] += gain

    # 🔹 Gain set (recalculé proprement)
    final_levels = [c["to"] for c in sol["combo"]]
    atk_set, def_set = compute_set_bonus_detailed(final_levels, level_index)

    # appliquer à toutes les troupes
    for troop in stats:
        stats[troop]["atk"] += atk_set
        stats[troop]["def"] += def_set

    return stats
# ----------------------------
#  OPTIMAL PARETO
# ----------------------------
def pareto_front_fast(solutions):
    solutions_sorted = sorted(solutions, key=lambda x: (-x["gain"], -x["kvk"]))

    pareto = []
    best_kvk = -1

    for s in solutions_sorted:
        if s["kvk"] >= best_kvk:
            pareto.append(s)
            best_kvk = s["kvk"]

    return pareto


def get_next_level(levels_piece, current_level_index):
    """
    levels_piece : liste des niveaux pour UNE pièce
    current_level_index : index actuel

    Retourne le niveau suivant ou None
    """
    if current_level_index + 1 < len(levels_piece):
        return levels_piece[current_level_index + 1]
    return None

def can_still_upgrade(combo, satin, threads, artisans, levels, level_keys, level_index):
    for c in combo:
        current_level = c["to"]
        idx = level_index[current_level]

        if idx + 1 >= len(level_keys):
            continue

        next_level = level_keys[idx + 1]
        cost = levels[next_level]

        if (cost["satin"] <= satin and
            cost["threads"] <= threads and
            cost["artisans"] <= artisans):
            return True

    return False

# ----------------------------
# 🔹 MAIN ENGINE
# ----------------------------
def get_best_upgrades(current_gear, levels, materials):
    level_keys = list(levels.keys())
    level_index = {lvl: i for i, lvl in enumerate(level_keys)}

    set_bonus_before = compute_set_bonus(
        [current_gear[p] for p in PIECES],
        levels,
        level_index
    )

    solutions = []

    def backtrack(index, combo, satin, threads, artisans):
        # if all pieces done, final solution
        if index == len(PIECES):
            final_levels = [c["to"] for c in combo]

            gain_set = compute_set_bonus(final_levels, levels, level_index) - set_bonus_before
            gain_items = sum(c["gain_items"] for c in combo)
            total_gain = gain_items + gain_set
            kvk_total = sum(c["kvk"] for c in combo)

            solution = {
                "combo": deepcopy(combo),
                "gain_items": gain_items,
                "gain_set": gain_set,
                "gain": total_gain,
                "kvk": kvk_total,
                "satin": sum(c["satin"] for c in combo),
                "threads": sum(c["threads"] for c in combo),
                "artisans": sum(c["artisans"] for c in combo),
            }

            if not can_still_upgrade(combo, satin, threads, artisans, levels, level_keys, level_index):
                solutions.append(solution)

            return

        piece = PIECES[index]
        start_level = current_gear[piece]
        start_idx = level_index[start_level]

        upgrade_possible = False

        # Explore all reachable levels
        for end_idx in range(start_idx, len(level_keys)):
            upgrades_path = level_keys[start_idx+1:end_idx+1]

            total_satin = sum(levels[l]["satin"] for l in upgrades_path)
            total_threads = sum(levels[l]["threads"] for l in upgrades_path)
            total_artisans = sum(levels[l]["artisans"] for l in upgrades_path)

            if total_satin <= satin and total_threads <= threads and total_artisans <= artisans:
                upgrade_possible = True

                # KvK = previous level (N-1)
                kvk_total = 0
                for l in upgrades_path:
                    idx_l = level_index[l]
                    prev_level = level_keys[idx_l - 1]
                    kvk_total += levels[prev_level]["kvk"]

                gain_items = levels[level_keys[end_idx]]["bonus"] - levels[start_level]["bonus"]

                combo.append({
                    "piece": piece,
                    "to": level_keys[end_idx],
                    "gain_items": gain_items,
                    "kvk": kvk_total,
                    "satin": total_satin,
                    "threads": total_threads,
                    "artisans": total_artisans,
                    "num_upgrades": len(upgrades_path)
                })

                backtrack(
                    index + 1,
                    combo,
                    satin - total_satin,
                    threads - total_threads,
                    artisans - total_artisans
                )

                combo.pop()

        # if no possible upgrad, keep current level
        if not upgrade_possible:
            combo.append({
                "piece": piece,
                "to": start_level,
                "gain_items": 0,
                "kvk": 0,
                "satin": 0,
                "threads": 0,
                "artisans": 0,
                "num_upgrades": 0
            })

            backtrack(index + 1, combo, satin, threads, artisans)
            combo.pop()

    backtrack(0, [], materials["satin"], materials["threads"], materials["artisans"])

    return solutions


# ----------------------------
# 🔹 NORMALISATION + SCORE
# ----------------------------
def add_normalized_scores(solutions):
    gain_max_sol = max(solutions, key=lambda x: x["gain"])
    kvk_max_sol = max(solutions, key=lambda x: x["kvk"])

    gain_max = gain_max_sol["gain"]
    gain_min = kvk_max_sol["gain"]

    kvk_max = kvk_max_sol["kvk"]
    kvk_min = gain_max_sol["kvk"]

    for s in solutions:
        if gain_max != gain_min:
            s["gain_ratio"] = (s["gain"] - gain_min) / (gain_max - gain_min)
        else:
            s["gain_ratio"] = 1

        if kvk_max != kvk_min:
            s["kvk_ratio"] = (s["kvk"] - kvk_min) / (kvk_max - kvk_min)
        else:
            s["kvk_ratio"] = 1

        # Score combiné (modifiable)
        s["score"] = 0.5 * s["gain_ratio"] + 0.5 * s["kvk_ratio"]

    return solutions
