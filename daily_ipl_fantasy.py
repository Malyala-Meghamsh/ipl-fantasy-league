"""
Daily IPL Fantasy Stats Pipeline
---------------------------------
1. Scrapes player stats from fantasy.iplt20.com/classic/stats (manual OTP login)
2. Maps players to 2026 auction squads
3. Calculates role-constrained Best XI per team
4. Saves daily snapshot and historical ranking
"""

import time
import csv
import os
from datetime import date, datetime, timedelta
from itertools import combinations
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# If before 2 AM, treat it as the previous day (late-night runs)
_now = datetime.now()
MATCH_DAY = (_now - timedelta(days=1)).date() if _now.hour < 2 else _now.date()
TODAY = MATCH_DAY.strftime("%Y-%m-%d")
DAILY_CSV = os.path.join(BASE_DIR, f"ipl_fantasy_stats_{TODAY}.csv")
LATEST_CSV = os.path.join(BASE_DIR, "ipl_fantasy_stats.csv")
HISTORY_CSV = os.path.join(BASE_DIR, "ranking_history.csv")

# ═══════════════════════════════════════════════════════════════════
# STEP 1 — SCRAPE FANTASY STATS
# ═══════════════════════════════════════════════════════════════════

def scrape_stats():
    print("\n" + "=" * 60)
    print("STEP 1: SCRAPING FANTASY STATS")
    print("=" * 60)

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://fantasy.iplt20.com/classic/stats")
    input("\n👉 Log in manually in the browser, then press ENTER here...")
    time.sleep(5)

    driver.get("https://fantasy.iplt20.com/classic/stats")
    time.sleep(8)

    # Scroll to load all players
    scrollable = driver.find_elements(By.CSS_SELECTOR, ".m11c-plyrSel__list")
    if scrollable:
        last_count = 0
        for _ in range(50):
            rows = driver.find_elements(By.CSS_SELECTOR, ".m11c-plyrSel__list li")
            if len(rows) == last_count:
                break
            last_count = len(rows)
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable[0]
            )
            time.sleep(1)

    # Extract data
    rows = driver.find_elements(By.CSS_SELECTOR, ".m11c-plyrSel__list li")
    data = []
    for row in rows:
        try:
            name = row.find_element(By.CSS_SELECTOR, ".m11c-plyrSel__name span").text
            team = row.find_element(By.CSS_SELECTOR, ".m11c-plyrSel__team span").text
            credits_val = row.find_element(By.CSS_SELECTOR, ".m11c-tbl__cell--pts span").text
            total_points = row.find_element(By.CSS_SELECTOR, ".m11c-tbl__cell--amt span").text
            data.append([name, team, credits_val, total_points])
        except Exception:
            continue

    driver.quit()

    # Save date-stamped CSV
    for path in [DAILY_CSV, LATEST_CSV]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Player", "Team", "Credits", "Total Points"])
            writer.writerows(data)

    print(f"✅ Scraped {len(data)} players → {DAILY_CSV}")
    return data


# ═══════════════════════════════════════════════════════════════════
# STEP 2 — DATA: SQUADS, ROLES, NAME MAP
# ═══════════════════════════════════════════════════════════════════

name_map = {
    "T. Natarajan": "T Natarajan",
    "Smaran Ravichandaran": "Ravichandran Smaran",
    "R. Sai Kishore": "Sai Kishore",
    "Vyshak Vijaykumar": "Vijaykumar Vyshak",
    "Varun Chakravarthy": "Varun Chakaravarthy",
    "Abhishek Porel": "Abishek Porel",
    "Vaibhav Suryavanshi": "Vaibhav Sooryavanshi",
    "Lhuan-Dre Pretorious": "Lhuan-dre Pretorius",
    "Quinton De Kock": "Quinton de Kock",
    "Digvesh Rathi": "Digvesh Singh",
    "Mohammad Siraj": "Mohammed Siraj",
    "Auqib Dar": "Auqib Nabi",
}

# Map squad player names → player_roles.csv names (for name mismatches)
_role_name_map = {
    "Suryakumar Yadav": "Surya Kumar Yadav",
    "Tilak Varma": "N. Tilak Varma",
    "Shahbaz Ahmed": "Shahbaz Ahamad",
    "Mohammad Siraj": "Mohammed Siraj",
    "Smaran Ravichandaran": "Smaran Ravichandran",
    "Varun Chakravarthy": "Varun Chakaravarthy",
    "Abhishek Porel": "Abishek Porel",
    "Vaibhav Suryavanshi": "Vaibhav Sooryavanshi",
    "Lhuan-Dre Pretorious": "Lhuan-dre Pretorious",
    "Quinton De Kock": "Quinton de Kock",
    "R. Sai Kishore": "Sai Kishore",
    "Digvesh Rathi": "Digvesh Singh",
    "Auqib Dar": "Auqib Nabi",
    "Lungi Ngidi": "Lungisani Ngidi",
}

# Fallback roles for players missing from player_roles.csv
_fallback_roles = {
    "Sam Curran": "AR", "K.S. Bharat": "WK", "Vijay Shankar": "AR",
    "Harshit Rana": "BOWL", "Deepak Hooda": "AR", "Abhinav Manohar": "BAT",
    "Aarya Desai": "BOWL", "Kamlesh Nagarkoti": "BOWL",
    "Jake Fraser-McGurk": "BAT", "Fazalhaq Farooqi": "BOWL",
    "Anmolpreet Singh": "BAT", "Akash Madhwal": "BOWL",
    "Manan Vohra": "BAT", "Ankit Kumar": "AR",
    "Rahmanullah Gurbaz": "WK", "Daniel Sams": "AR",
    "Karn Sharma": "BOWL", "Rajvardhan Hangargekar": "AR",
    "Kusal Perera": "WK", "Chetan Sakariya": "BOWL",
    "Mayank Agarawal": "BAT",
}

# Fallback foreign status for players missing from player_roles.csv
_fallback_foreign = {
    "Sam Curran": True, "K.S. Bharat": False, "Vijay Shankar": False,
    "Harshit Rana": False, "Deepak Hooda": False, "Abhinav Manohar": False,
    "Aarya Desai": False, "Kamlesh Nagarkoti": False,
    "Jake Fraser-McGurk": True, "Fazalhaq Farooqi": True,
    "Anmolpreet Singh": False, "Akash Madhwal": False,
    "Manan Vohra": False, "Ankit Kumar": False,
    "Rahmanullah Gurbaz": True, "Daniel Sams": True,
    "Karn Sharma": False, "Rajvardhan Hangargekar": False,
    "Kusal Perera": True, "Chetan Sakariya": False,
    "Mayank Agarawal": False,
}

# Load player roles from player_roles.csv
_ROLE_STR_MAP = {"Batsman": "BAT", "Bowler": "BOWL", "WK": "WK", "AR": "AR"}
_ROLES_CSV = os.path.join(BASE_DIR, "player_roles.csv")

roles = dict(_fallback_roles)
foreign = dict(_fallback_foreign)
if os.path.isfile(_ROLES_CSV):
    with open(_ROLES_CSV, "r", encoding="utf-8") as f:
        _reader = csv.DictReader(f)
        for _row in _reader:
            _csv_name = _row["Player"].strip()
            _role = _ROLE_STR_MAP.get(_row["Role"].strip(), _row["Role"].strip())
            roles[_csv_name] = _role
            # Load foreign status if column exists
            if "Foreign" in _row:
                foreign[_csv_name] = _row["Foreign"].strip().lower() == "yes"
    # Add entries for squad names that differ from CSV names
    for _squad_name, _csv_name in _role_name_map.items():
        if _csv_name in roles:
            roles[_squad_name] = roles[_csv_name]
        if _csv_name in foreign:
            foreign[_squad_name] = foreign[_csv_name]

squads = {
    "PBKS": [
        "Hardik Pandya", "Ruturaj Gaikwad", "Arshdeep Singh", "Sam Curran",
        "Ishan Kishan", "Harshal Patel", "Azmatullah Omarzai", "Shardul Thakur",
        "Dewald Brevis", "Devdutt Padikkal", "Prabhsimran Singh", "Sameer Rizvi",
        "Ramandeep Singh", "Sarfaraz Khan", "K.S. Bharat", "Matheesha Pathirana",
        "Vijay Shankar"
    ],
    "SRH": [
        "Mitchell Marsh", "Shubman Gill", "Rohit Sharma", "KL Rahul",
        "Mohammad Siraj", "Aiden Markram", "Virat Kohli", "Riyan Parag",
        "Rajat Patidar", "Jaydev Unadkat", "Yash Dayal", "Harshit Rana",
        "Nitish Kumar Reddy", "Umran Malik", "Musheer Khan", "Abdul Samad",
        "Zeeshan Ansari", "Anuj Rawat", "Swapnil Singh", "Rachin Ravindra",
        "Wanindu Hasaranga", "Deepak Hooda", "Abhinav Manohar", "Aarya Desai",
        "Kamlesh Nagarkoti"
    ],
    "KKR": [
        "MS Dhoni", "Sunil Narine", "Lockie Ferguson", "Suryakumar Yadav",
        "Mitchell Starc", "Josh Hazlewood", "Bhuvneshwar Kumar",
        "Sherfane Rutherford", "Nandre Burger", "Ryan Rickelton",
        "Shahrukh Khan", "Karun Nair", "R. Sai Kishore", "Mukesh Choudhary",
        "Nehal Wadhera", "Priyansh Arya", "Vaibhav Arora", "Mohsin Khan",
        "Angkrish Raghuvanshi", "Jake Fraser-McGurk", "Ravi Bishnoi"
    ],
    "GT": [
        "Jos Buttler", "Yashasvi Jaiswal", "Heinrich Klaasen", "Kuldeep Yadav",
        "Mohammad Shami", "Avesh Khan", "Tristan Stubbs", "Sai Sudharsan",
        "Khaleel Ahmed", "Mitchell Santner", "Dhruv Jurel", "Jamie Overton",
        "Kamindu Mendis", "Harpreet Brar", "Urvil Patel", "Vishnu Vinod",
        "Gurjapneet Singh", "Anshul Kamboj", "Ashutosh Sharma",
        "Fazalhaq Farooqi", "Shivam Mavi", "Anmolpreet Singh", "Akash Madhwal"
    ],
    "DC": [
        "Kagiso Rabada", "Marcus Stoinis", "Phil Salt", "Shreyas Iyer",
        "Marco Jansen", "Will Jacks", "Mayank Yadav", "Washington Sundar",
        "Rahul Tewatia", "Nitish Rana", "Vyshak Vijaykumar", "Digvesh Rathi",
        "Naman Dhir", "Mayank Markande", "Ayush Badoni", "Pathum Nissanka",
        "Tom Banton", "Kyle Jamieson", "Manan Vohra", "Ankit Kumar"
    ],
    "MI": [
        "Nicholas Pooran", "Jofra Archer", "Shivam Dube", "Axar Patel",
        "Sanju Samson", "Rovman Powell", "Prasidh Krishna", "Romario Shepherd",
        "Deepak Chahar", "Glenn Phillips", "Mukesh Kumar", "Shashank Singh",
        "Prithvi Shaw", "Rahmanullah Gurbaz", "Finn Allen", "Tim Seifert"
    ],
    "RR": [
        "Rinku Singh", "Trent Boult", "Yuzvendra Chahal", "Rishabh Pant",
        "Varun Chakravarthy", "Shimron Hetmyer", "Travis Head",
        "Abhishek Sharma", "Sandeep Sharma", "Abhishek Porel",
        "Liam Livingstone", "Jacob Duffy", "Rahul Chahar",
        "Rajvardhan Hangargekar", "Karn Sharma", "Rahul Tripathi", "Daniel Sams"
    ],
    "CSK": [
        "Rashid Khan", "Jasprit Bumrah", "Krunal Pandya", "Ajinkya Rahane",
        "Vaibhav Suryavanshi", "Ayush Mhatre", "Lhuan-Dre Pretorious",
        "David Miller", "Quinton De Kock", "Matt Henry", "Kartik Sharma",
        "Prashant Solanki", "Jason Holder", "Kusal Perera", "Adam Milne",
        "Chetan Sakariya"
    ],
    "RCB": [
        "Tim David", "Noor Ahmad", "Pat Cummins", "Ravindra Jadeja",
        "Tilak Varma", "T. Natarajan", "Jacob Bethell", "Shahbaz Ahmed",
        "Jitesh Sharma", "Smaran Ravichandaran", "Suyash Sharma",
        "Aniket Verma", "Robin Minz", "Eshan Malinga", "Cameron Green",
        "Venkatesh Iyer", "Prashant Veer", "Auqib Dar", "Ashok Sharma",
        "Kartik Tyagi", "Vignesh Puthur", "Mayank Agarawal", "Josh Inglis"
    ],
}

# ═══════════════════════════════════════════════════════════════════
# STEP 3 — BEST XI OPTIMIZER
# ═══════════════════════════════════════════════════════════════════

# Pre-compute valid compositions (wk, bat, ar, bowl) summing to 11
# Constraints: at least 1 WK (WK counts as batsman), AR+BOWL >= 5
valid_combos = []
for wk in range(1, 7):          # at least 1 WK, up to 6 (since AR+BOWL >= 5)
    for bat in range(0, 7):      # BAT can be 0 if enough WKs
        remaining = 11 - wk - bat
        if remaining < 5:        # can't satisfy AR+BOWL >= 5
            continue
        for ar in range(0, remaining + 1):
            bowl = remaining - ar
            if bowl >= 0 and (ar + bowl) >= 5:
                valid_combos.append((wk, bat, ar, bowl))


def get_points(name, fantasy_points):
    mapped = name_map.get(name, name)
    return fantasy_points.get(mapped, 0)


def get_role(name):
    return roles.get(name, "UNKNOWN")


def is_foreign(name):
    return foreign.get(name, False)


MAX_OVERSEAS = 4


def find_best_xi(team_name, squad, fantasy_points):
    """Find the best XI for a team under role composition constraints."""
    pool = {"WK": [], "BAT": [], "AR": [], "BOWL": []}
    for name in squad:
        pts = get_points(name, fantasy_points)
        role = get_role(name)
        if role in pool:
            pool[role].append((name, pts))
    for r in pool:
        pool[r].sort(key=lambda x: x[1], reverse=True)

    best_team = None
    best_pts = -1

    for wk_c, bat_c, ar_c, bowl_c in valid_combos:
        counts = {"WK": wk_c, "BAT": bat_c, "AR": ar_c, "BOWL": bowl_c}
        if any(len(pool[r]) < counts[r] for r in counts if counts[r] > 0):
            continue

        best_for_combo_pts = -1
        best_for_combo = None

        for wk_pick in combinations(pool["WK"], wk_c):
            wk_pts = sum(p[1] for p in wk_pick)
            wk_os = sum(1 for p in wk_pick if is_foreign(p[0]))
            if wk_os > MAX_OVERSEAS:
                continue
            for bat_pick in combinations(pool["BAT"], bat_c):
                bat_pts = sum(p[1] for p in bat_pick)
                bat_os = sum(1 for p in bat_pick if is_foreign(p[0]))
                if wk_os + bat_os > MAX_OVERSEAS:
                    continue
                for ar_pick in combinations(pool["AR"], ar_c):
                    ar_pts = sum(p[1] for p in ar_pick)
                    ar_os = sum(1 for p in ar_pick if is_foreign(p[0]))
                    os_so_far = wk_os + bat_os + ar_os
                    if os_so_far > MAX_OVERSEAS:
                        continue
                    partial = wk_pts + bat_pts + ar_pts
                    bowl_upper = sum(p[1] for p in pool["BOWL"][:bowl_c])
                    if partial + bowl_upper <= best_for_combo_pts:
                        continue
                    for bowl_pick in combinations(pool["BOWL"], bowl_c):
                        bowl_os = sum(1 for p in bowl_pick if is_foreign(p[0]))
                        if os_so_far + bowl_os > MAX_OVERSEAS:
                            continue
                        bowl_pts = sum(p[1] for p in bowl_pick)
                        total = partial + bowl_pts
                        if total > best_for_combo_pts:
                            best_for_combo_pts = total
                            best_for_combo = (
                                list(wk_pick) + list(bat_pick)
                                + list(ar_pick) + list(bowl_pick)
                            )

        if best_for_combo_pts > best_pts:
            best_pts = best_for_combo_pts
            best_team = best_for_combo

    return best_team, best_pts


# ═══════════════════════════════════════════════════════════════════
# STEP 4 — RUN PIPELINE
# ═══════════════════════════════════════════════════════════════════

def load_fantasy_points():
    """Load fantasy points from the latest CSV."""
    fp = {}
    with open(LATEST_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fp[row["Player"].strip()] = int(row["Total Points"])
    return fp


def run_pipeline():
    # --- Scrape ---
    scrape_stats()

    # --- Load points ---
    fantasy_points = load_fantasy_points()

    # --- Best XI per team ---
    print("\n" + "=" * 70)
    print(f"{'BEST XI PER TEAM (1-4 WK, 3-6 BAT, AR+BOWL >= 5)':^70}")
    print(f"{'Date: ' + TODAY:^70}")
    print("=" * 70)

    role_order = {"WK": 1, "BAT": 2, "AR": 3, "BOWL": 4}
    team_totals = {}

    for team, squad in squads.items():
        best_team, best_pts = find_best_xi(team, squad, fantasy_points)
        team_totals[team] = best_pts

        print(f"\n{'━' * 70}")
        print(f"  {team} — BEST XI ({best_pts} pts)")
        print(f"{'━' * 70}")

        if best_team:
            best_team.sort(key=lambda p: (role_order.get(get_role(p[0]), 9), -p[1]))
            print(f"  {'#':<4} {'Player':<30} {'Role':<6} {'Points':>8}")
            print(f"  {'─' * 52}")
            for i, (name, pts) in enumerate(best_team, 1):
                print(f"  {i:<4} {name:<30} {get_role(name):<6} {pts:>8}")
            print(f"  {'─' * 52}")
            print(f"  {'':4} {'TOTAL':<30} {'':6} {best_pts:>8}")
            comp = {"WK": 0, "BAT": 0, "AR": 0, "BOWL": 0}
            for name, _ in best_team:
                comp[get_role(name)] += 1
            print(f"  Composition: {comp['WK']} WK, {comp['BAT']} BAT, {comp['AR']} AR, {comp['BOWL']} BOWL")
        else:
            print("  ⚠️  Could not form a valid XI (not enough players per role)")

    # --- Rankings ---
    sorted_teams = sorted(team_totals.items(), key=lambda x: x[1], reverse=True)

    print(f"\n\n{'=' * 55}")
    print(f"{'TEAM RANKINGS — BEST XI TOTAL FANTASY POINTS':^55}")
    print(f"{'Date: ' + TODAY:^55}")
    print(f"{'=' * 55}")
    print(f"  {'Rank':<6} {'Team':<12} {'Best XI Pts':>12} {'Avg/Player':>12}")
    print(f"  {'─' * 45}")
    for rank, (team, total) in enumerate(sorted_teams, 1):
        avg = total / 11 if total > 0 else 0
        print(f"  {rank:<6} {team:<12} {total:>12} {avg:>12.1f}")
    print(f"  {'─' * 45}")
    grand = sum(t for _, t in sorted_teams)
    print(f"  {'':6} {'TOTAL':<12} {grand:>12} {grand / (11 * len(sorted_teams)):>12.1f}")
    print()

    # --- Save to history (replace today's data if exists) ---
    existing_rows = []
    if os.path.isfile(HISTORY_CSV):
        with open(HISTORY_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if row and row[0] != TODAY:
                    existing_rows.append(row)

    with open(HISTORY_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Rank", "Team", "Best XI Points", "Avg Per Player"])
        writer.writerows(existing_rows)
        for rank, (team, total) in enumerate(sorted_teams, 1):
            avg = round(total / 11, 1) if total > 0 else 0
            writer.writerow([TODAY, rank, team, total, avg])

    print(f"✅ Rankings appended to {HISTORY_CSV}")
    print(f"✅ Daily stats saved to {DAILY_CSV}")
    print(f"✅ Latest stats updated in {LATEST_CSV}")

    # --- Generate HTML leaderboard ---
    try:
        from generate_leaderboard import main as generate_html
        generate_html()
    except Exception as e:
        print(f"⚠️  HTML generation skipped: {e}")

    # --- Auto deploy to GitHub Pages ---
    import subprocess
    try:
        print("\n" + "=" * 60)
        print("DEPLOYING TO GITHUB PAGES")
        print("=" * 60)
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Daily update {TODAY}"],
            cwd=BASE_DIR, check=True,
        )
        subprocess.run(["git", "push"], cwd=BASE_DIR, check=True)
        print("✅ Pushed to GitHub Pages")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git deploy failed: {e}")
    except FileNotFoundError:
        print("⚠️  Git not found. Install git and set up the repo first.")

if __name__ == "__main__":
    run_pipeline()
