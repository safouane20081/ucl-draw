import pandas as pd
import random
import copy
import sys
import os

# ============================================================
#  UCL 2024/25 LEAGUE PHASE DRAW SIMULATOR
#
#  Official Rules:
#  - 36 teams in 4 pots of 9
#  - Each team gets EXACTLY 8 opponents (2 from EACH of the 4 pots)
#  - This includes 2 opponents from within their OWN pot
#  - 4 home games, 4 away games
#  - No same-country matchups
#  - Max 2 opponents from any single country
# ============================================================

def load_teams(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()
    required = {"team", "country", "pot"}
    if not required.issubset(df.columns):
        raise ValueError(f"Need columns: {required}")
    teams = {}
    for _, row in df.iterrows():
        name = row["team"].strip()
        teams[name] = {
            "name": name,
            "country": row["country"].strip(),
            "pot": int(row["pot"]),
            "opponents": set(),
            "home_games": [],
            "away_games": [],
            "pot_count": {1: 0, 2: 0, 3: 0, 4: 0},
        }
    return teams


def can_pair(teams, a, b):
    if a == b: return False
    if b in teams[a]["opponents"]: return False
    if teams[a]["country"] == teams[b]["country"]: return False
    cb = teams[b]["country"]
    if sum(1 for o in teams[a]["opponents"] if teams[o]["country"] == cb) >= 2: return False
    ca = teams[a]["country"]
    if sum(1 for o in teams[b]["opponents"] if teams[o]["country"] == ca) >= 2: return False
    return True


def do_assign(teams, a, b):
    opts = []
    if len(teams[a]["home_games"]) < 4 and len(teams[b]["away_games"]) < 4: opts.append(0)
    if len(teams[a]["away_games"]) < 4 and len(teams[b]["home_games"]) < 4: opts.append(1)
    if not opts: return False
    if random.choice(opts) == 0:
        teams[a]["home_games"].append(b); teams[b]["away_games"].append(a)
    else:
        teams[a]["away_games"].append(b); teams[b]["home_games"].append(a)
    return True


def confirm(teams, a, b, pot_a, pot_b):
    if not do_assign(teams, a, b): return False
    teams[a]["opponents"].add(b); teams[b]["opponents"].add(a)
    teams[a]["pot_count"][pot_b] += 1; teams[b]["pot_count"][pot_a] += 1
    return True


def draw_pot_pair(teams, pot_a, pot_b, retries=3000):
    """
    Match teams from pot_a against teams from pot_b.
    Each team in pot_a needs 2 from pot_b, and vice versa.
    When pot_a == pot_b, teams pair within their own pot.
    """
    pool_a = [t for t in teams if teams[t]["pot"] == pot_a]
    pool_b = [t for t in teams if teams[t]["pot"] == pot_b]
    same_pot = (pot_a == pot_b)

    for _ in range(retries):
        saved = {t: {
            "opponents": copy.copy(teams[t]["opponents"]),
            "home_games": copy.copy(teams[t]["home_games"]),
            "away_games": copy.copy(teams[t]["away_games"]),
            "pot_count": copy.copy(teams[t]["pot_count"]),
        } for t in set(pool_a + pool_b)}

        random.shuffle(pool_a)
        ok = True

        for team in pool_a:
            needed = 2 - teams[team]["pot_count"][pot_b]
            if needed <= 0: continue

            if same_pot:
                candidates = [t for t in pool_b
                              if t != team
                              and teams[t]["pot_count"][pot_a] < 2
                              and can_pair(teams, team, t)]
            else:
                candidates = [t for t in pool_b
                              if teams[t]["pot_count"][pot_a] < 2
                              and can_pair(teams, team, t)]

            # Most constrained first
            candidates.sort(key=lambda t: sum(
                1 for x in (pool_a if same_pot else pool_b)
                if x != t and teams[x]["pot_count"][pot_b if same_pot else pot_a] < 2
                and can_pair(teams, t, x)
            ))

            assigned = 0
            for opp in candidates:
                if assigned >= needed: break
                if same_pot and teams[opp]["pot_count"][pot_a] >= 2: continue
                if not same_pot and teams[opp]["pot_count"][pot_a] >= 2: continue
                if not can_pair(teams, team, opp): continue
                if confirm(teams, team, opp, pot_a, pot_b):
                    assigned += 1

            if assigned < needed:
                ok = False
                break

        if ok:
            if same_pot:
                done = all(teams[t]["pot_count"][pot_a] == 2 for t in pool_a)
            else:
                done = (all(teams[t]["pot_count"][pot_b] == 2 for t in pool_a) and
                        all(teams[t]["pot_count"][pot_a] == 2 for t in pool_b))
            if done:
                return True

        for t in set(pool_a + pool_b):
            teams[t]["opponents"] = saved[t]["opponents"]
            teams[t]["home_games"] = saved[t]["home_games"]
            teams[t]["away_games"] = saved[t]["away_games"]
            teams[t]["pot_count"] = saved[t]["pot_count"]

    return False


def run_full_draw(teams_orig, max_attempts=300):
    # All pot pairings including same-pot pairings
    # Each team needs 2 from each pot (including own)
    all_pairs = [(1,1),(2,2),(3,3),(4,4),(1,2),(1,3),(1,4),(2,3),(2,4),(3,4)]

    for attempt in range(1, max_attempts + 1):
        teams = copy.deepcopy(teams_orig)
        pairs = all_pairs[:]
        random.shuffle(pairs)
        ok = True

        for pa, pb in pairs:
            label = f"Pot {pa} vs Pot {pa} (within)" if pa == pb else f"Pot {pa} vs Pot {pb}"
            print(f"   {label}...", end=" ", flush=True)
            if draw_pot_pair(teams, pa, pb):
                print("✅")
            else:
                print("❌  → restarting")
                ok = False
                break

        if ok:
            return teams, attempt

    return None, max_attempts


def validate(teams):
    errors = []
    for name, t in teams.items():
        opps = list(t["opponents"])
        if len(opps) != 8: errors.append(f"{name}: {len(opps)} opponents (need 8)")
        if len(t["home_games"]) != 4: errors.append(f"{name}: {len(t['home_games'])} home (need 4)")
        if len(t["away_games"]) != 4: errors.append(f"{name}: {len(t['away_games'])} away (need 4)")
        for pot in range(1, 5):
            c = sum(1 for o in opps if teams[o]["pot"] == pot)
            if c != 2: errors.append(f"{name}: {c} from pot {pot} (need 2)")
        for opp in opps:
            if teams[opp]["country"] == t["country"]:
                errors.append(f"SAME COUNTRY: {name} vs {opp}!")
        cc = {}
        for opp in opps:
            c = teams[opp]["country"]
            cc[c] = cc.get(c, 0) + 1
        for c, n in cc.items():
            if n > 2: errors.append(f"{name}: {n} from {c} (max 2)")
    return errors


def show(teams):
    print("\n" + "=" * 68)
    print("           🏆  UCL 2024/25 DRAW RESULTS  🏆")
    print("=" * 68)
    for pot in range(1, 5):
        print(f"\n{'─'*68}\n  POT {pot}\n{'─'*68}")
        for team in sorted([t for t in teams.values() if t["pot"] == pot], key=lambda x: x["name"]):
            print(f"\n  🔵 {team['name']} ({team['country']})")
            for opp in sorted(team["opponents"], key=lambda o: (teams[o]["pot"], o)):
                v = "🏠 HOME" if opp in team["home_games"] else "✈️  AWAY"
                print(f"       {v}  vs  {opp} ({teams[opp]['country']}) [Pot {teams[opp]['pot']}]")
            print(f"     📊 {len(team['home_games'])} Home  |  {len(team['away_games'])} Away")
    print("\n" + "=" * 68)
    print("  ✅ All UCL rules verified — Draw complete!")
    print("=" * 68 + "\n")


def make_sample():
    data = [
        ("Real Madrid","Spain",1),("Manchester City","England",1),
        ("Bayern Munich","Germany",1),("Paris Saint-Germain","France",1),
        ("Liverpool","England",1),("Inter Milan","Italy",1),
        ("Borussia Dortmund","Germany",1),("RB Leipzig","Germany",1),
        ("Barcelona","Spain",1),
        ("Bayer Leverkusen","Germany",2),("Atletico Madrid","Spain",2),
        ("Atalanta","Italy",2),("Juventus","Italy",2),
        ("Benfica","Portugal",2),("Arsenal","England",2),
        ("Club Brugge","Belgium",2),("Shakhtar Donetsk","Ukraine",2),
        ("AC Milan","Italy",2),
        ("Feyenoord","Netherlands",3),("Sporting CP","Portugal",3),
        ("PSV Eindhoven","Netherlands",3),("GNK Dinamo Zagreb","Croatia",3),
        ("Red Star Belgrade","Serbia",3),("Young Boys","Switzerland",3),
        ("Celtic","Scotland",3),("Monaco","France",3),("Aston Villa","England",3),
        ("Bologna","Italy",4),("Girona","Spain",4),
        ("Stuttgart","Germany",4),("Sturm Graz","Austria",4),
        ("Brest","France",4),("Sparta Prague","Czechia",4),
        ("Slovan Bratislava","Slovakia",4),("Red Bull Salzburg","Austria",4),
        ("Lille","France",4),
    ]
    pd.DataFrame(data, columns=["team","country","pot"]).to_csv("ucl_teams.csv", index=False)
    print("✅ Sample ucl_teams.csv created!\n")


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "ucl_teams.csv"
    if not os.path.exists(csv_path):
        print(f"\n❌ File not found: {csv_path}")
        print("Usage: python ucl_draw.py your_file.csv\n")
        print("CSV columns needed: team, country, pot\n")
        print("Creating sample CSV...")
        make_sample()
        csv_path = "ucl_teams.csv"

    print(f"\n📂 Loading: {csv_path}")
    teams = load_teams(csv_path)
    print(f"✅ {len(teams)} teams | ", end="")
    for p in range(1,5): print(f"Pot {p}: {sum(1 for t in teams.values() if t['pot']==p)}", end="  ")
    print()

    print(f"\n🎲 Running Draw...\n")
    result, attempts = run_full_draw(teams)

    if result is None:
        print("\n❌ Draw failed after all attempts.")
        return

    errs = validate(result)
    if errs:
        print("\n⚠️ Issues:")
        for e in errs: print(f"  - {e}")
    else:
        print(f"\n✅ Validated! Completed in {attempts} attempt(s).")
        show(result)


if __name__ == "__main__":
    main()
