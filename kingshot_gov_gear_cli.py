import json
import argparse
from utils_gov_gear import get_best_upgrades, pareto_front_fast
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# ----------------------------
# 🔹 ARGUMENTS CLI
# ----------------------------
parser = argparse.ArgumentParser(description="Calculateur Kingshot upgrades")
parser.add_argument("--satin", type=int, required=True)
parser.add_argument("--threads", type=int, required=True)
parser.add_argument("--artisans", type=int, required=True)
parser.add_argument("--no_pareto", action="store_true", help="Afficher toutes les solutions (pas de pareto optimal)")
parser.add_argument("--weight_gain", type=float, default=0.5, help="Poids du gain dans le score combiné (0-1)")
parser.add_argument("--weight_kvk", type=float, default=0.5, help="Poids du KvK dans le score combiné (0-1)")
args = parser.parse_args()

# ----------------------------
# 🔹 LOAD DATA
# ----------------------------
with open("gear.json") as f:
    current_gear = json.load(f)

with open("data/gear_levels.json") as f:
    levels = json.load(f)

materials = {"satin": args.satin, "threads": args.threads, "artisans": args.artisans}

# ----------------------------
# 🔹 COMPUTE BEST UPGRADE
# ----------------------------
solutions = get_best_upgrades(current_gear, levels, materials)

if not solutions:
    console.print("[bold red]Aucune solution trouvée[/bold red]")
    exit()

# ----------------------------
# 🔹 NORMALIZING AND SCORE 
# ----------------------------
gain_max = max(s["gain"] for s in solutions)
kvk_max  = max(s["kvk"] for s in solutions)

for s in solutions:
    s["gain_ratio"] = s["gain"] / gain_max if gain_max > 0 else 0
    s["kvk_ratio"] = s["kvk"] / kvk_max if kvk_max > 0 else 0
    s["score"] = args.weight_gain * s["gain_ratio"] + args.weight_kvk * s["kvk_ratio"]

score_max = max(solutions, key=lambda x: x["score"])["score"]

# ----------------------------
# 🔹 MAX VALUES (for color)
# ----------------------------
max_gain_value = gain_max
max_kvk_value = kvk_max
max_score_value = score_max

# ----------------------------
# 🔹 PARETO (optionnal)
# ----------------------------
if not args.no_pareto:
    pareto_solutions = pareto_front_fast(solutions)

    # Ajouter toutes les solutions gain max et kvk max si elles ne sont pas déjà présentes
    all_max_gain_sols = [s for s in solutions if s["gain"] == max_gain_value]
    all_max_kvk_sols = [s for s in solutions if s["kvk"] == max_kvk_value]

    for s in all_max_gain_sols + all_max_kvk_sols:
        if s not in pareto_solutions:
            pareto_solutions.append(s)

    solutions = pareto_solutions

# Trier par score combiné
solutions.sort(key=lambda x: x["score"], reverse=True)

# ----------------------------
# 🔹 TABLE
# ----------------------------
pieces = ["cap", "watch", "coat", "pants", "belt", "weapon"]
table = Table(title="Best Gear upgrades", box=box.SIMPLE_HEAVY)

# Colonnes équipements
for p in pieces:
    table.add_column(p.capitalize(), justify="center")

# Colonnes stats
table.add_column("Gain", justify="right")
table.add_column("Gain %", justify="right")
table.add_column("KvK", justify="right")
table.add_column("KvK %", justify="right")
table.add_column("Score", justify="right")
table.add_column("Satin", justify="right")
table.add_column("threads", justify="right")
table.add_column("artisans", justify="right")

# ----------------------------
# 🔹 DISPLAY
# ----------------------------
for sol in solutions:
    # Color if one max value
    style_parts = []
    if sol["gain"] == max_gain_value:
        style_parts.append("green")
    if sol["kvk"] == max_kvk_value:
        style_parts.append("cyan")
    if sol["score"] == max_score_value:
        style_parts.append("magenta")

    style = "bold " + " ".join(style_parts) if style_parts else ""

    piece_display = {c["piece"]: f"{c['to']}(+{c['num_upgrades']})" for c in sol["combo"]}
    row = [piece_display.get(p, "-") for p in pieces]

    row += [
        f"{sol['gain']:.2f}",
        f"{sol['gain_ratio']*100:.1f}%",
        str(sol["kvk"]),
        f"{sol['kvk_ratio']*100:.1f}%",
        f"{sol['score']:.3f}",
        str(sol["satin"]),
        str(sol["threads"]),
        str(sol["artisans"])
    ]

    table.add_row(*row, style=style)

console.print(table)

console.print(f"\n[bold yellow]{len(solutions)} solutions affichées[/bold yellow]")
console.print("[green]Max Gain[/green] | [cyan]Max KvK[/cyan] | [magenta]Max Score[/magenta]")