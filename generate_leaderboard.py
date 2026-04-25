"""
Generate a mobile-friendly HTML leaderboard from IPL Fantasy ranking data.
Reads ipl_fantasy_stats.csv + ranking_history.csv and produces index.html
"""

import csv
import os
from datetime import date, datetime, timedelta
from itertools import combinations

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LATEST_CSV = os.path.join(BASE_DIR, "ipl_fantasy_stats.csv")
HISTORY_CSV = os.path.join(BASE_DIR, "ranking_history.csv")
OUTPUT_HTML = os.path.join(BASE_DIR, "docs", "index.html")

# If before 2 AM, treat it as the previous day (late-night viewing)
_now = datetime.now()
MATCH_DAY = (_now - timedelta(days=1)).date() if _now.hour < 2 else _now.date()
TODAY = MATCH_DAY.strftime("%Y-%m-%d")

# ═══════════════════════════════════════════════════════════════════
# IPL 2026 FIXTURES (date → list of (home_team_code, away_team_code))
# ═══════════════════════════════════════════════════════════════════
IPL_FIXTURES = {
    "2026-04-08": [("DC", "GT")],
    "2026-04-09": [("KKR", "LSG")],
    "2026-04-10": [("RR", "RCB")],
    "2026-04-11": [("PBKS", "SRH"), ("CSK", "DC")],
    "2026-04-12": [("LSG", "GT"), ("MI", "RCB")],
    "2026-04-13": [("SRH", "RR")],
    "2026-04-14": [("CSK", "KKR")],
    "2026-04-15": [("RCB", "LSG")],
    "2026-04-16": [("MI", "PBKS")],
    "2026-04-17": [("GT", "KKR")],
    "2026-04-18": [("RCB", "DC"), ("SRH", "CSK")],
    "2026-04-19": [("KKR", "RR"), ("PBKS", "LSG")],
    "2026-04-20": [("GT", "MI")],
    "2026-04-21": [("SRH", "DC")],
    "2026-04-22": [("LSG", "RR")],
    "2026-04-23": [("MI", "CSK")],
    "2026-04-24": [("RCB", "GT")],
    "2026-04-25": [("DC", "PBKS"), ("RR", "SRH")],
    "2026-04-26": [("GT", "CSK"), ("LSG", "KKR")],
    "2026-04-27": [("DC", "RCB")],
    "2026-04-28": [("PBKS", "RR")],
    "2026-04-29": [("MI", "SRH")],
    "2026-04-30": [("GT", "RCB")],
    "2026-05-01": [("RR", "DC")],
    "2026-05-02": [("CSK", "MI")],
    "2026-05-03": [("SRH", "KKR"), ("GT", "PBKS")],
    "2026-05-04": [("MI", "LSG")],
    "2026-05-05": [("DC", "CSK")],
    "2026-05-06": [("SRH", "PBKS")],
    "2026-05-07": [("LSG", "RCB")],
    "2026-05-08": [("DC", "KKR")],
    "2026-05-09": [("RR", "GT")],
    "2026-05-10": [("CSK", "LSG"), ("RCB", "MI")],
    "2026-05-11": [("PBKS", "DC")],
    "2026-05-12": [("GT", "SRH")],
    "2026-05-13": [("RCB", "KKR")],
    "2026-05-14": [("PBKS", "MI")],
    "2026-05-15": [("LSG", "CSK")],
    "2026-05-16": [("KKR", "GT")],
    "2026-05-17": [("PBKS", "RCB"), ("DC", "RR")],
    "2026-05-18": [("CSK", "SRH")],
    "2026-05-19": [("RR", "LSG")],
    "2026-05-20": [("KKR", "MI")],
    "2026-05-21": [("CSK", "GT")],
    "2026-05-22": [("SRH", "RCB")],
    "2026-05-23": [("LSG", "PBKS")],
    "2026-05-24": [("MI", "RR"), ("KKR", "DC")],
}

# Map original IPL team codes used in ipl_fantasy_stats.csv
# Note: "LSG" does not exist in original IPL teams — Lucknow Super Giants is LSG
ORIGINAL_TEAM_FULL = {
    "DC": "Delhi Capitals", "GT": "Gujarat Titans", "KKR": "Kolkata Knight Riders",
    "LSG": "Lucknow Super Giants", "MI": "Mumbai Indians", "PBKS": "Punjab Kings",
    "RR": "Rajasthan Royals", "RCB": "Royal Challengers Bengaluru",
    "CSK": "Chennai Super Kings", "SRH": "Sunrisers Hyderabad",
}


def get_todays_matches():
    """Return list of (home, away) tuples for today's IPL matches."""
    return IPL_FIXTURES.get(TODAY, [])


def get_today_players(fantasy_points_csv_path):
    """Return players from today's match teams, sorted by points desc."""
    matches = get_todays_matches()
    if not matches:
        return [], []

    # Collect all team codes playing today
    playing_teams = set()
    for home, away in matches:
        playing_teams.add(home)
        playing_teams.add(away)

    # Load yesterday's points for daily diff
    yesterday = (MATCH_DAY - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_csv = os.path.join(BASE_DIR, f"ipl_fantasy_stats_{yesterday}.csv")
    yesterday_pts = {}
    if os.path.isfile(yesterday_csv):
        with open(yesterday_csv, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pts_str = row["Total Points"].strip()
                if pts_str:
                    yesterday_pts[row["Player"].strip()] = int(pts_str)

    # Read CSV and filter by original team
    players = []
    with open(fantasy_points_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Team"].strip() in playing_teams:
                pts_str = row["Total Points"].strip()
                if not pts_str:
                    continue
                total = int(pts_str)
                prev = yesterday_pts.get(row["Player"].strip(), 0)
                players.append({
                    "name": row["Player"].strip(),
                    "original_team": row["Team"].strip(),
                    "credits": float(row["Credits"]),
                    "points": total,
                    "today_pts": total - prev,
                })

    players.sort(key=lambda x: x["points"], reverse=True)
    return matches, players

# ── Import data from daily script ──
from daily_ipl_fantasy import (
    squads, roles, name_map, valid_combos,
    get_role, get_points, find_best_xi, is_foreign,
)

# Team colors (IPL brand colors)
TEAM_COLORS = {
    "PBKS": {"bg": "#D71920", "text": "#FFFFFF"},
    "SRH": {"bg": "#FF822A", "text": "#FFFFFF"},
    "KKR": {"bg": "#3A225D", "text": "#FFC425"},
    "GT":  {"bg": "#1C1C2B", "text": "#B8D8E8"},
    "DC":  {"bg": "#004C93", "text": "#FFFFFF"},
    "MI":  {"bg": "#004BA0", "text": "#D4A537"},
    "RR":  {"bg": "#EA1A85", "text": "#FFFFFF"},
    "CSK": {"bg": "#FFCB05", "text": "#0051A2"},
    "RCB": {"bg": "#D4213D", "text": "#FFFFFF"},
}

TEAM_FULL_NAMES = {
    "PBKS": "Punjab Kings",
    "SRH": "Sunrisers Hyderabad",
    "KKR": "Kolkata Knight Riders",
    "GT": "Gujarat Titans",
    "DC": "Delhi Capitals",
    "MI": "Mumbai Indians",
    "RR": "Rajasthan Royals",
    "CSK": "Chennai Super Kings",
    "RCB": "Royal Challengers Bengaluru",
}

# Owner data
OWNERS = {
    "GT":  {"name": "Pranav",      "nick": "Daff"},
    "DC":  {"name": "Nithin",      "nick": "Aids"},
    "CSK": {"name": "Sai Ram",     "nick": "Chillar"},
    "PBKS":{"name": "Meghamsh",    "nick": "Megha"},
    "SRH": {"name": "Aman",        "nick": "Thal"},
    "RCB": {"name": "Sahil",       "nick": "Micromax Sahil"},
    "RR":  {"name": "Santosh",     "nick": "Santhoo"},
    "MI":  {"name": "Nandeeshwar", "nick": "Nandi"},
    "KKR": {"name": "Tejash",      "nick": "Oorav"},
}

import random

# Fun titles assigned by rank position
RANK_TITLES = {
    1: ("&#128081; KING OF LEAGUE", "Best team. Best owner."),
    2: ("&#129352; Close But Not Close", "Close to first but still far away."),
    3: ("&#129353; Third Place Winner", "You made it to top 3. That is good."),
    4: ("&#128545; Just Average", "Not good. Not bad. Just middle."),
    5: ("&#128747; Middle Player", "You are forgotten."),
    6: ("&#129313; Bad Team", "What happened in auction?"),
    7: ("&#128128; Very Bad", "Almost last place. Not good."),
    8: ("&#127869; Almost Last", "Last place is coming."),
    9: ("&#128049; LAST PLACE", "Make tea for everyone."),
}

# Trash talk lines per rank
TRASH_TALK = {
    1: [
        "Number 1 sir. Everyone else is trying for second.",
        "You picked a team like a smart person. Others picked shit.",
        "I never saw picks this good before.",
        "You are the king of this league.",
        "Your team is on another level. Everyone else is playing trash.",
        "In auction you were like god.",
        "Best team best owner. The trophy is yours."
    ],
    2: [
        "Number 2. Very close. But still far.",
        "One person beat you. Who is it?",
        "Such a good team but you lost to one person?",
        "Silver medal. Take it and go.",
        "Next time pick better team.",
        "Good. At least you are on podium."
    ],
    3: [
        "You are on podium. Good. Now be quiet.",
        "Third place. Not good. Not bad. Just okay.",
        "At least you have a medal. Take screenshot.",
        "Third is okay okay. Could be better.",
        "You are on podium. That is something."
    ],
    4: [
        "Fourth place? This is an achievement?",
        "Fourth place. Nobody will know.",
        "What happened in auction? Nothing good?",
        "You died in the middle.",
        "Not first. Not last. Just middle."
    ],
    5: [
        "Fifth place. Average team average owner.",
        "Fifth place. Just forget it.",
        "Not so bad. Not so good.",
        "You are standing in middle. That is all.",
        "One more place down and you are not in top 4."
    ],
    6: [
        "Sixth place. What was this?",
        "Auction time what happened? You slept?",
        "You are in bottom half now.",
        "6 out of 9. That is very bad.",
        "Now the loser section starts."
    ],
    7: [
        "Seventh place. Very very bad.",
        "You are in bottom. Almost last.",
        "Two more places and you are last.",
        "Seventh. That is it.",
        "How far you fell back!"
    ],
    8: [
        "Eighth place! One more place and last.",
        "Almost you will be wooden spoon champion.",
        "Last place is just one spot below. Watch out.",
        "Who is playing with your team now?",
        "One bad day and you are last."
    ],
    9: [
        "LAST PLACE. Go make tea for everyone.",
        "You are number 1. In losing.",
        "What happened in auction day?",
        "What team is this? You closed your eyes and picked?",
        "I never saw such bad team before.",
        "Money wasted. Total waste.",
        "Last place. Go drink tea and relax.",
        "Wooden spoon. This is your gift.",
        "What light was on in auction room?",
        "Even small children would pick better team.",
        "Last place. Only one position for you."
    ],
}

# Dark horse alert threshold (% of points gap)
DARK_HORSE_THRESHOLD = 0.05  # Flag if gap to team above is within 5%

# Auction prices in Cr for each player (L = lakhs, 30L = 0.30 Cr)
squad_prices = {
    # PBKS (Megha)
    "Hardik Pandya": 16.5, "Ruturaj Gaikwad": 16.5, "Arshdeep Singh": 12.3,
    "Sam Curran": 2.6, "Ishan Kishan": 14.3, "Harshal Patel": 7.5,
    "Azmatullah Omarzai": 3.0, "Shardul Thakur": 4.6, "Dewald Brevis": 16.5,
    "Devdutt Padikkal": 6.0, "Prabhsimran Singh": 7.0, "Sameer Rizvi": 1.6,
    "Ramandeep Singh": 2.6, "Sarfaraz Khan": 1.1, "K.S. Bharat": 0.75,
    "Matheesha Pathirana": 6.3, "Vijay Shankar": 0.35,
    # SRH (Thal)
    "Mitchell Marsh": 6.5, "Shubman Gill": 10.3, "Rohit Sharma": 11.3,
    "KL Rahul": 15.8, "Mohammad Siraj": 7.8, "Aiden Markram": 9.8,
    "Virat Kohli": 20.5, "Riyan Parag": 7.8, "Rajat Patidar": 6.3,
    "Jaydev Unadkat": 4.2, "Yash Dayal": 0.50, "Harshit Rana": 0.60,
    "Nitish Kumar Reddy": 7.0, "Umran Malik": 0.55, "Musheer Khan": 0.30,
    "Abdul Samad": 1.1, "Zeeshan Ansari": 0.35, "Anuj Rawat": 0.30,
    "Swapnil Singh": 0.30, "Rachin Ravindra": 2.0, "Wanindu Hasaranga": 2.0,
    "Deepak Hooda": 0.75, "Abhinav Manohar": 0.30, "Aarya Desai": 0.30,
    "Kamlesh Nagarkoti": 1.0,
    # KKR (Oorav)
    "MS Dhoni": 7.8, "Sunil Narine": 6.0, "Lockie Ferguson": 3.0,
    "Suryakumar Yadav": 11.3, "Mitchell Starc": 6.3, "Josh Hazlewood": 14.5,
    "Bhuvneshwar Kumar": 8.3, "Sherfane Rutherford": 1.0, "Nandre Burger": 0.95,
    "Ryan Rickelton": 1.2, "Shahrukh Khan": 3.2, "Karun Nair": 0.50,
    "R. Sai Kishore": 5.5, "Mukesh Choudhary": 0.70, "Nehal Wadhera": 3.6,
    "Priyansh Arya": 13.3, "Vaibhav Arora": 0.30, "Mohsin Khan": 0.30,
    "Angkrish Raghuvanshi": 10.0, "Jake Fraser-McGurk": 6.5, "Ravi Bishnoi": 4.8,
    # GT (Daff)
    "Jos Buttler": 8.3, "Yashasvi Jaiswal": 16.3, "Heinrich Klaasen": 14.5,
    "Kuldeep Yadav": 5.5, "Mohammad Shami": 2.4, "Avesh Khan": 3.0,
    "Tristan Stubbs": 5.8, "Sai Sudharsan": 12.3, "Khaleel Ahmed": 7.5,
    "Mitchell Santner": 8.3, "Dhruv Jurel": 5.3, "Jamie Overton": 0.90,
    "Kamindu Mendis": 1.5, "Harpreet Brar": 1.5, "Urvil Patel": 4.2,
    "Vishnu Vinod": 0.30, "Gurjapneet Singh": 0.30, "Anshul Kamboj": 4.6,
    "Ashutosh Sharma": 9.0, "Fazalhaq Farooqi": 1.0, "Shivam Mavi": 1.3,
    "Anmolpreet Singh": 0.50, "Akash Madhwal": 5.5,
    # DC (Aids)
    "Kagiso Rabada": 8.3, "Marcus Stoinis": 9.5, "Phil Salt": 9.0,
    "Shreyas Iyer": 18.5, "Marco Jansen": 9.0, "Will Jacks": 13.3,
    "Mayank Yadav": 3.0, "Washington Sundar": 4.4, "Rahul Tewatia": 1.7,
    "Nitish Rana": 4.2, "Vyshak Vijaykumar": 2.2, "Digvesh Rathi": 6.3,
    "Naman Dhir": 8.3, "Mayank Markande": 0.30, "Ayush Badoni": 7.3,
    "Pathum Nissanka": 4.6, "Tom Banton": 2.0, "Kyle Jamieson": 2.0,
    "Manan Vohra": 0.50, "Ankit Kumar": 1.5,
    # MI (Nandi)
    "Nicholas Pooran": 15.8, "Jofra Archer": 4.6, "Shivam Dube": 10.5,
    "Axar Patel": 10.3, "Sanju Samson": 13.8, "Rovman Powell": 2.0,
    "Prasidh Krishna": 5.0, "Romario Shepherd": 3.8, "Deepak Chahar": 6.8,
    "Glenn Phillips": 2.2, "Mukesh Kumar": 0.75, "Shashank Singh": 9.5,
    "Prithvi Shaw": 3.0, "Rahmanullah Gurbaz": 1.6, "Finn Allen": 8.8,
    "Tim Seifert": 12.0,
    # RR (Santhoo)
    "Rinku Singh": 5.8, "Trent Boult": 11.3, "Yuzvendra Chahal": 9.3,
    "Rishabh Pant": 11.0, "Varun Chakravarthy": 8.3, "Shimron Hetmyer": 11.8,
    "Travis Head": 13.8, "Abhishek Sharma": 15.5, "Sandeep Sharma": 9.3,
    "Abhishek Porel": 6.3, "Liam Livingstone": 8.3, "Jacob Duffy": 2.2,
    "Rahul Chahar": 1.5, "Rajvardhan Hangargekar": 0.65, "Karn Sharma": 3.6,
    "Rahul Tripathi": 0.75, "Daniel Sams": 1.0,
    # CSK (Chillar)
    "Rashid Khan": 8.0, "Jasprit Bumrah": 18.0, "Krunal Pandya": 6.0,
    "Ajinkya Rahane": 6.8, "Vaibhav Suryavanshi": 16.5, "Ayush Mhatre": 19.3,
    "Lhuan-Dre Pretorious": 0.30, "David Miller": 12.0, "Quinton De Kock": 8.0,
    "Matt Henry": 5.0, "Kartik Sharma": 4.2, "Prashant Solanki": 0.30,
    "Jason Holder": 2.4, "Kusal Perera": 1.0, "Adam Milne": 2.0,
    "Chetan Sakariya": 2.0,
    # RCB (Micromax Sahil)
    "Tim David": 7.8, "Noor Ahmad": 10.3, "Pat Cummins": 9.0,
    "Ravindra Jadeja": 5.0, "Tilak Varma": 8.3, "T. Natarajan": 1.0,
    "Jacob Bethell": 4.4, "Shahbaz Ahmed": 0.55, "Jitesh Sharma": 5.8,
    "Smaran Ravichandaran": 0.30, "Suyash Sharma": 1.1, "Aniket Verma": 4.4,
    "Robin Minz": 0.30, "Eshan Malinga": 0.75, "Cameron Green": 20.5,
    "Venkatesh Iyer": 9.8, "Prashant Veer": 10.3, "Auqib Dar": 0.45,
    "Ashok Sharma": 0.30, "Kartik Tyagi": 0.95, "Vignesh Puthur": 0.30,
    "Mayank Agarawal": 5.0, "Josh Inglis": 12.3,
}


def compute_auction_awards(rankings, fantasy_points):
    """Dynamically compute auction awards based on fantasy points and prices."""
    # Build flat list of (player, team, pts, price, pts_per_cr)
    all_players = []
    for team, squad in squads.items():
        owner_nick = OWNERS.get(team, {}).get("nick", team)
        for name in squad:
            pts = get_points(name, fantasy_points)
            price = squad_prices.get(name, 0)
            if price > 0:
                all_players.append({
                    "name": name, "team": team, "owner": owner_nick,
                    "pts": pts, "price": price,
                    "pts_per_cr": pts / price,
                })

    # Visionary Pick: best pts/cr among players in the top 30% by points
    sorted_pts = sorted([p["pts"] for p in all_players if p["pts"] > 0])
    top30_threshold = sorted_pts[int(len(sorted_pts) * 0.7)] if sorted_pts else 0
    eligible_value = [p for p in all_players if p["pts"] >= top30_threshold]
    best_value = max(eligible_value, key=lambda p: p["pts_per_cr"]) if eligible_value else None

    # Shittiest Pick: worst pts/cr among expensive players (>= 5 Cr), exclude 0 pts
    expensive = [p for p in all_players if p["price"] >= 5.0 and p["pts"] > 0]
    worst_value = min(expensive, key=lambda p: p["pts_per_cr"]) if expensive else None

    # Best Squad Selector: team with highest Best XI points (rankings[0])
    best_squad = rankings[0]
    best_squad_owner = OWNERS.get(best_squad["team"], {}).get("nick", best_squad["team"])
    best_squad_xi_pts = best_squad["points"]
    best_squad_total = best_squad["total_squad_pts"]

    # Worst Squad Selector: team with lowest Best XI points (rankings[-1])
    worst_squad = rankings[-1]
    worst_squad_owner = OWNERS.get(worst_squad["team"], {}).get("nick", worst_squad["team"])
    worst_squad_xi_pts = worst_squad["points"]

    awards = []

    if best_value:
        price_str = f"{best_value['price']} Cr"
        awards.append({
            "emoji": "&#129351;",
            "title": "Visionary Pick",
            "subtitle": "Best value for money",
            "player": best_value["name"],
            "price": price_str,
            "owner": best_value["owner"],
            "team": best_value["team"],
            "color": "#ffd200",
            "pts": best_value["pts"],
            "reason": f"{best_value['name']} cost just {price_str} and scored {best_value['pts']} fantasy points. "
                      f"That's {best_value['pts_per_cr']:.1f} pts per crore. "
                      f"While others were throwing crores at big names, {best_value['owner']} quietly robbed the auction.",
        })

    if worst_value:
        price_str = f"{worst_value['price']} Cr"
        awards.append({
            "emoji": "&#128169;",
            "title": "Shittiest Pick",
            "subtitle": "Worst money wasted",
            "player": worst_value["name"],
            "price": price_str,
            "owner": worst_value["owner"],
            "team": worst_value["team"],
            "color": "#ff4444",
            "pts": worst_value["pts"],
            "reason": f"{worst_value['name']} cost {price_str} and has only {worst_value['pts']} fantasy points to show for it. "
                      f"That is {worst_value['pts_per_cr']:.1f} pts per crore. "
                      f"{worst_value['owner']} basically set {price_str} on fire at the auction.",
        })

    awards.append({
        "emoji": "&#127942;",
        "title": "Best Squad Selector",
        "subtitle": "Came. Drafted. Destroyed.",
        "player": None,
        "price": None,
        "owner": best_squad_owner,
        "team": best_squad["team"],
        "color": "#4caf50",
        "pts": best_squad_xi_pts,
        "reason": f"{best_squad_owner}'s {best_squad['team']} leads the league with {best_squad_xi_pts} Best XI points "
                  f"out of {best_squad_total} total squad points. "
                  f"Built like a pro. Everyone else is just watching.",
    })

    awards.append({
        "emoji": "&#129313;",
        "title": "Went Auction for Snacks Award",
        "subtitle": "Was he even paying attention?",
        "player": None,
        "price": None,
        "owner": worst_squad_owner,
        "team": worst_squad["team"],
        "color": "#ff6b6b",
        "pts": worst_squad_xi_pts,
        "reason": f"{worst_squad_owner}'s {worst_squad['team']} sits last with only {worst_squad_xi_pts} Best XI points. "
                  f"Squad has {worst_squad['squad_size']} players scoring {worst_squad['total_squad_pts']} total pts. "
                  f"Went to the auction looking for samosas and accidentally raised the paddle.",
    })

    return awards


def load_fantasy_points():
    fp = {}
    with open(LATEST_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pts = row["Total Points"].strip()
            if pts:
                fp[row["Player"].strip()] = int(pts)
    return fp


def load_original_teams():
    """Load player -> original IPL team mapping from the stats CSV."""
    ot = {}
    with open(LATEST_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ot[row["Player"].strip()] = row["Team"].strip()
    return ot


def load_history():
    """Load ranking history for trend display."""
    history = {}
    if not os.path.isfile(HISTORY_CSV):
        return history
    with open(HISTORY_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = row["Date"]
            team = row["Team"]
            if d not in history:
                history[d] = {}
            history[d][team] = {
                "rank": int(row["Rank"]),
                "points": int(row["Best XI Points"]),
            }
    return history


def compute_rankings(fantasy_points, original_teams=None):
    """Return sorted list of (team, best_pts, best_xi_players, full_squad)."""
    if original_teams is None:
        original_teams = {}
    results = []
    for team, squad in squads.items():
        best_team, best_pts = find_best_xi(team, squad, fantasy_points)
        players = []
        best_xi_names = set()
        if best_team:
            role_order = {"WK": 1, "BAT": 2, "AR": 3, "BOWL": 4}
            best_team.sort(key=lambda p: (role_order.get(get_role(p[0]), 9), -p[1]))
            for name, pts in best_team:
                players.append({"name": name, "role": get_role(name), "points": pts})
                best_xi_names.add(name)
        # Full squad with all players
        full_squad = []
        total_squad_pts = 0
        for name in squad:
            p = get_points(name, fantasy_points)
            total_squad_pts += p
            csv_name = name_map.get(name, name)
            orig_team = original_teams.get(csv_name, "")
            full_squad.append({
                "name": name,
                "role": get_role(name),
                "points": p,
                "in_xi": name in best_xi_names,
                "original_team": orig_team,
            })
        full_squad.sort(key=lambda x: x["points"], reverse=True)
        results.append({
            "team": team, "points": best_pts, "players": players,
            "full_squad": full_squad, "total_squad_pts": total_squad_pts,
            "squad_size": len(squad),
        })
    results.sort(key=lambda x: x["points"], reverse=True)
    return results


def generate_html(rankings, history, fantasy_points):
    """Generate a complete standalone HTML file."""

    # Build today's players to watch HTML
    today_matches, today_players = get_today_players(LATEST_CSV)
    today_section_html = ""
    if today_matches:
        match_labels = []
        for home, away in today_matches:
            match_labels.append(f"{home} vs {away}")
        match_title = " &amp; ".join(match_labels)

        # Build player rows — show which fantasy owner has each player
        # Map: player name -> fantasy owner team
        player_to_owner = {}
        for team_code, squad in squads.items():
            for pname in squad:
                mapped = name_map.get(pname, pname)
                player_to_owner[mapped] = team_code

        # Sort: owned players first, then unowned. Within each group: today_pts desc, then total pts desc
        owned = [p for p in today_players if player_to_owner.get(p["name"], "")]
        unowned = [p for p in today_players if not player_to_owner.get(p["name"], "")]
        owned.sort(key=lambda x: (x.get("today_pts", 0), x["points"]), reverse=True)
        unowned.sort(key=lambda x: (x.get("today_pts", 0), x["points"]), reverse=True)
        today_players_sorted = owned + unowned

        # Compute dynamic thresholds based on percentiles of today's players
        all_total_pts = sorted([p["points"] for p in today_players_sorted if p["points"] > 0])
        all_daily_pts = sorted([p.get("today_pts", 0) for p in today_players_sorted if p.get("today_pts", 0) > 0])
        def _percentile(sorted_vals, pct):
            if not sorted_vals:
                return 0
            idx = int(len(sorted_vals) * pct / 100)
            return sorted_vals[min(idx, len(sorted_vals) - 1)]
        pts_hot_threshold = _percentile(all_total_pts, 75)   # top 25% = green
        pts_warm_threshold = _percentile(all_total_pts, 40)   # top 60% = orange
        day_hot_threshold = _percentile(all_daily_pts, 75)    # top 25% daily = green
        day_warm_threshold = max(_percentile(all_daily_pts, 40), 1)  # top 60% daily = orange

        today_rows = ""
        divider_added = False
        for i, p in enumerate(today_players_sorted, 1):
            owner_team = player_to_owner.get(p["name"], "")
            # Insert divider before first unowned player
            if not owner_team and not divider_added and owned:
                divider_added = True
                today_rows += f'<tr class="today-divider-row" data-owner="UNCLAIMED"><td colspan="6" class="today-divider">&#128683; Unclaimed Players</td></tr>'
            owner_nick = OWNERS.get(owner_team, {}).get("nick", "") if owner_team else ""
            owner_badge = f'<span class="today-owner-badge" style="background:{TEAM_COLORS.get(owner_team, {}).get("bg","#333")};color:{TEAM_COLORS.get(owner_team, {}).get("text","#fff")}">{owner_team}</span>' if owner_team else '<span class="today-owner-badge today-unclaimed">N/A</span>'
            pts_class = "today-pts-hot" if p["points"] >= pts_hot_threshold else "today-pts-warm" if p["points"] >= pts_warm_threshold else ""
            team_color = TEAM_COLORS.get(p["original_team"], {"bg": "#333", "text": "#fff"})
            # Reverse name_map (CSV name → squad name) for price lookup
            reverse_name = {v: k for k, v in name_map.items()}.get(p["name"], p["name"])
            price = squad_prices.get(p["name"], 0) or squad_prices.get(reverse_name, 0)
            price_str = f"{price} Cr" if price else "-"
            row_owner = owner_team if owner_team else "UNCLAIMED"
            today_pts = p.get("today_pts", 0)
            today_pts_display = f"+{today_pts}" if today_pts > 0 else str(today_pts) if today_pts < 0 else "0"
            today_pts_color = "today-day-hot" if today_pts >= day_hot_threshold else "today-day-warm" if today_pts >= day_warm_threshold else "today-day-zero"
            today_rows += f"""
                <tr class="today-row" data-owner="{row_owner}">
                    <td class="num">{i}</td>
                    <td class="player-name">
                        {p["name"]}
                        <span class="today-orig-team" style="background:{team_color['bg']};color:{team_color['text']}">{p["original_team"]}</span>
                    </td>
                    <td class="today-price">{price_str}</td>
                    <td class="pts {pts_class}">{p["points"]}</td>
                    <td class="today-day {today_pts_color}">{today_pts_display}</td>
                    <td class="today-owner">{owner_badge}<br><small>{owner_nick}</small></td>
                </tr>"""

        # Build owner filter buttons (only owners who have players in today's match)
        today_owners_set = set()
        for p in today_players_sorted:
            ot = player_to_owner.get(p["name"], "")
            if ot:
                today_owners_set.add(ot)
        filter_buttons = '<button class="today-filter-btn active" onclick="filterTodayOwner(\'ALL\')">All</button>'
        for tc in sorted(today_owners_set):
            nick = OWNERS.get(tc, {}).get("nick", tc)
            bg = TEAM_COLORS.get(tc, {}).get("bg", "#333")
            txt = TEAM_COLORS.get(tc, {}).get("text", "#fff")
            filter_buttons += f'<button class="today-filter-btn" style="--btn-bg:{bg};--btn-text:{txt}" onclick="filterTodayOwner(\'{tc}\')">{nick}</button>'
        filter_buttons += '<button class="today-filter-btn" style="--btn-bg:#333;--btn-text:#888" onclick="filterTodayOwner(\'UNCLAIMED\')">Unclaimed</button>'

        today_section_html = f"""
        <div class="today-section">
            <div class="today-header">
                <div class="today-live-dot"></div>
                <h2>Today's Players to Watch</h2>
            </div>
            <div class="today-match-info">{match_title}</div>
            <div class="today-subtitle">{len(today_players)} players in action</div>
            <div class="today-filter-bar">{filter_buttons}</div>
            <table class="today-table">
                <thead>
                    <tr><th>#</th><th>Player</th><th>Price</th><th>Pts</th><th>Today</th><th>Owner</th></tr>
                </thead>
                <tbody>
                    {today_rows}
                </tbody>
                <tfoot>
                    <tr class="today-total-row">
                        <td></td><td><strong>TOTAL</strong></td><td></td>
                        <td class="pts" id="today-total-pts"><strong>{sum(p['points'] for p in today_players_sorted)}</strong></td>
                        <td class="today-day" id="today-total-day"><strong>{'+' + str(sum(p.get('today_pts', 0) for p in today_players_sorted)) if sum(p.get('today_pts', 0) for p in today_players_sorted) > 0 else str(sum(p.get('today_pts', 0) for p in today_players_sorted))}</strong></td>
                        <td></td>
                    </tr>
                </tfoot>
            </table>
        </div>
        """

    # Build auction awards HTML
    auction_awards = compute_auction_awards(rankings, fantasy_points)
    awards_html = ""
    for award in auction_awards:
        color = award["color"]
        # Stats bar for player-level awards
        stats_bar = ""
        if award["player"]:
            pts_per_cr = award["pts"] / float(award["price"].replace(' Cr','')) if award["pts"] else 0
            stats_bar = f'''<div class="award-stats-bar">
                <div class="award-stat-item">
                    <div class="award-stat-label">Player</div>
                    <div class="award-stat-value" style="color:#e0e0e0">{award["player"]}</div>
                </div>
                <div class="award-stat-item">
                    <div class="award-stat-label">Price</div>
                    <div class="award-stat-value" style="color:{color}">{award["price"]}</div>
                </div>
                <div class="award-stat-item">
                    <div class="award-stat-label">Points</div>
                    <div class="award-stat-value" style="color:#ffd200">{award["pts"]}</div>
                </div>
                <div class="award-stat-item">
                    <div class="award-stat-label">Pts/Cr</div>
                    <div class="award-stat-value" style="color:{'#4caf50' if pts_per_cr > 50 else '#ff6b6b'}">{pts_per_cr:.1f}</div>
                </div>
            </div>'''
        else:
            # Team-level award stats
            stats_bar = f'''<div class="award-stats-bar">
                <div class="award-stat-item">
                    <div class="award-stat-label">Team</div>
                    <div class="award-stat-value" style="color:#e0e0e0">{award["team"]}</div>
                </div>
                <div class="award-stat-item">
                    <div class="award-stat-label">Best XI Pts</div>
                    <div class="award-stat-value" style="color:{color}">{award["pts"]}</div>
                </div>
            </div>'''
        awards_html += f"""
        <div class="award-card" style="border-left: 4px solid {color}">
            <div class="award-header">
                <div class="award-emoji">{award["emoji"]}</div>
                <div class="award-title-block">
                    <div class="award-title" style="color:{color}">{award["title"]}</div>
                    <div class="award-subtitle">{award["subtitle"]}</div>
                </div>
                <div class="award-winner">
                    <div class="award-winner-name" style="color:{color}">{award["owner"]}</div>
                    <div class="award-winner-team">{award["team"]}</div>
                </div>
            </div>
            {stats_bar}
            <div class="award-reason">{award["reason"]}</div>
        </div>"""

    # Build team cards HTML
    team_cards = ""
    total_teams = len(rankings)
    for rank, r in enumerate(rankings, 1):
        team = r["team"]
        pts = r["points"]
        colors = TEAM_COLORS.get(team, {"bg": "#333", "text": "#fff"})
        full_name = TEAM_FULL_NAMES.get(team, team)
        owner = OWNERS.get(team, {"name": "???", "nick": "???"})
        title, subtitle = RANK_TITLES.get(rank, ("&#128566; Survivor", "Still in the game... barely."))

        # Trash talk
        talk_lines = TRASH_TALK.get(rank, [])
        trash_line = random.choice(talk_lines) if talk_lines else ""

        # Dark horse detection
        dark_horse_html = ""
        if rank > 1:
            team_above = rankings[rank - 2]
            gap = team_above["points"] - pts
            above_pts = team_above["points"] if team_above["points"] > 0 else 1
            if 0 < gap <= above_pts * DARK_HORSE_THRESHOLD:
                above_nick = OWNERS.get(team_above['team'], {}).get('nick', team_above['team'])
                dark_horse_html = f'<div class="dark-horse">&#127943; DARK HORSE ALERT: Only {gap} pts behind {team_above["team"]} ({above_nick})! One big match and they\'re cooked &#128293;</div>'

        # Trend arrow from history
        dates = sorted(history.keys())
        trend_html = ""
        if len(dates) >= 2:
            prev_date = dates[-2]
            if team in history.get(prev_date, {}):
                prev_rank = history[prev_date][team]["rank"]
                prev_pts = history[prev_date][team]["points"]
                pt_diff = pts - prev_pts
                rank_diff = prev_rank - rank  # positive = improved
                if rank_diff > 0:
                    trend_html = f'<span class="trend trend-up">&#9650; +{rank_diff}</span>'
                elif rank_diff < 0:
                    trend_html = f'<span class="trend trend-down">&#9660; {rank_diff}</span>'
                else:
                    trend_html = '<span class="trend trend-same">&mdash;</span>'
                if pt_diff != 0:
                    sign = "+" if pt_diff > 0 else ""
                    trend_html += f' <span class="pt-diff">({sign}{pt_diff} pts)</span>'

        # Player rows
        player_rows = ""
        xi_overseas = 0
        for i, p in enumerate(r["players"], 1):
            role_class = p["role"].lower()
            os_badge = ' <span class="overseas-badge">OS</span>' if is_foreign(p["name"]) else ""
            if is_foreign(p["name"]):
                xi_overseas += 1
            player_rows += f"""
                <tr>
                    <td class="num">{i}</td>
                    <td class="player-name">{p["name"]}{os_badge}</td>
                    <td><span class="role-badge role-{role_class}">{p["role"]}</span></td>
                    <td class="pts">{p["points"]}</td>
                </tr>"""

        avg = round(pts / 11, 1) if pts > 0 else 0

        # Full squad rows
        full_squad = r["full_squad"]
        total_squad_pts = r["total_squad_pts"]
        squad_size = r["squad_size"]
        bench_pts = total_squad_pts - pts if pts > 0 else total_squad_pts
        playing = sum(1 for p in full_squad if p["in_xi"])
        on_bench = squad_size - playing

        squad_rows = ""
        total_squad_price = 0
        squad_overseas = 0
        for i, p in enumerate(full_squad, 1):
            role_class = p["role"].lower()
            row_class = "in-xi" if p["in_xi"] else "on-bench"
            xi_badge = "&#9989;" if p["in_xi"] else "&#10060;"
            price = squad_prices.get(p["name"], 0)
            total_squad_price += price
            price_str = f"{price} Cr" if price >= 1 else f"{int(price * 100)}L" if price > 0 else "-"
            os_badge = ' <span class="overseas-badge">OS</span>' if is_foreign(p["name"]) else ""
            if is_foreign(p["name"]):
                squad_overseas += 1
            orig_team = p.get("original_team", "")
            orig_team_badge = ""
            if orig_team:
                otc = TEAM_COLORS.get(orig_team, {"bg": "#333", "text": "#fff"})
                orig_team_badge = f' <span class="orig-team-badge" style="background:{otc["bg"]};color:{otc["text"]}">{orig_team}</span>'
            squad_rows += f"""
                <tr class="{row_class}">
                    <td class="num">{i}</td>
                    <td class="player-name">{p["name"]}{os_badge}{orig_team_badge}</td>
                    <td><span class="role-badge role-{role_class}">{p["role"]}</span></td>
                    <td class="price">{price_str}</td>
                    <td class="pts">{p["points"]}</td>
                    <td class="xi-status">{xi_badge}</td>
                </tr>"""

        # Role composition summary
        role_counts = {}
        for p in full_squad:
            role_counts[p["role"]] = role_counts.get(p["role"], 0) + 1
        role_summary = " &middot; ".join(f'{count} {role}' for role, count in
            sorted(role_counts.items(), key=lambda x: {"WK":1,"BAT":2,"AR":3,"BOWL":4}.get(x[0],9)))

        team_cards += f"""
        <div class="team-card{'  wooden-spoon' if rank == total_teams else ' champion' if rank == 1 else ''}" id="team-{team.lower()}">
            <div class="team-header" style="background:{colors['bg']}; color:{colors['text']}"
                 onclick="toggleTeam('{team.lower()}')">
                <div class="rank-badge">#{rank}</div>
                <div class="team-info">
                    <div class="team-abbr">{team}</div>
                    <div class="team-full">{full_name}</div>
                    <div class="owner-name">&#127918; {owner['nick']}</div>
                </div>
                <div class="team-pts">
                    <div class="pts-value">{pts}</div>
                    <div class="pts-label">pts</div>
                    {trend_html}
                </div>
                <div class="expand-icon">&#9660;</div>
            </div>
            <div class="team-body" id="body-{team.lower()}">
                <div class="fun-title-bar">
                    <span class="fun-title">{title}</span>
                    <span class="fun-subtitle">{subtitle}</span>
                    {'<div class="trash-talk">&ldquo;' + trash_line + '&rdquo;</div>' if trash_line else ''}
                    {dark_horse_html}
                </div>
                <div class="owner-detail">
                    <span>Owner: <strong>{owner['name']}</strong> aka <em>{owner['nick']}</em></span>
                </div>

                <!-- Tabs -->
                <div class="tab-bar">
                    <div class="tab active" onclick="switchTab('{team.lower()}', 'xi')">Best XI</div>
                    <div class="tab" onclick="switchTab('{team.lower()}', 'squad')">Full Squad</div>
                    <div class="tab" onclick="switchTab('{team.lower()}', 'stats')">Stats</div>
                </div>

                <!-- Tab: Best XI -->
                <div class="tab-content active" id="tab-xi-{team.lower()}">
                    <table class="xi-table">
                        <thead>
                            <tr><th>#</th><th>Player</th><th>Role</th><th>Pts</th></tr>
                        </thead>
                        <tbody>
                            {player_rows}
                        </tbody>
                        <tfoot>
                            <tr class="total-row">
                                <td></td><td><strong>TOTAL</strong></td><td></td><td class="pts"><strong>{pts}</strong></td>
                            </tr>
                            <tr class="avg-row">
                                <td></td><td>Avg per player</td><td></td><td class="pts">{avg}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>

                <!-- Tab: Full Squad -->
                <div class="tab-content" id="tab-squad-{team.lower()}">
                    <table class="xi-table squad-table">
                        <thead>
                            <tr><th>#</th><th>Player</th><th>Role</th><th>Price</th><th>Pts</th><th>XI?</th></tr>
                        </thead>
                        <tbody>
                            {squad_rows}
                        </tbody>
                        <tfoot>
                            <tr class="total-row">
                                <td></td><td><strong>SQUAD TOTAL</strong></td><td></td>
                                <td class="price"><strong>{round(total_squad_price, 2)} Cr</strong></td>
                                <td class="pts"><strong>{total_squad_pts}</strong></td><td></td>
                            </tr>
                        </tfoot>
                    </table>
                    <div class="squad-legend">
                        &#9989; = In Best XI &nbsp;&nbsp; &#10060; = On Bench
                    </div>
                </div>

                <!-- Tab: Stats -->
                <div class="tab-content" id="tab-stats-{team.lower()}">
                    <div class="team-stats">
                        <div class="stat-row">
                            <span>&#128203; Squad Size</span><span>{squad_size} players</span>
                        </div>
                        <div class="stat-row">
                            <span>&#127942; Best XI Points</span><span class="stat-highlight">{pts}</span>
                        </div>
                        <div class="stat-row">
                            <span>&#128202; Total Squad Points</span><span>{total_squad_pts}</span>
                        </div>
                        <div class="stat-row">
                            <span>&#129518; Bench Points (wasted)</span><span class="stat-dim">{bench_pts}</span>
                        </div>
                        <div class="stat-row">
                            <span>&#11088; Best XI Utilization</span><span>{round(pts / total_squad_pts * 100, 1) if total_squad_pts > 0 else 0}%</span>
                        </div>
                        <div class="stat-row">
                            <span>&#127919; Squad Composition</span><span>{role_summary}</span>
                        </div>
                        <div class="stat-row">
                            <span>&#128100; Playing / Bench</span><span>{playing} / {on_bench}</span>
                        </div>
                        <div class="stat-row">
                            <span>&#127758; Overseas in XI / Squad</span><span>{xi_overseas} / {squad_overseas}</span>
                        </div>
                    </div>
                </div>

            </div>
        </div>
        """

    # Build player search data (JSON for JS)
    import json
    player_search_data = []
    for r in rankings:
        team = r["team"]
        owner_nick = OWNERS.get(team, {}).get("nick", team)
        for p in r["full_squad"]:
            price = squad_prices.get(p["name"], 0)
            price_str = f"{price} Cr" if price >= 1 else f"{int(price * 100)}L" if price > 0 else "-"
            player_search_data.append({
                "name": p["name"],
                "team": team,
                "owner": owner_nick,
                "role": p["role"],
                "pts": p["points"],
                "price": price_str,
                "foreign": is_foreign(p["name"]),
                "in_xi": p["in_xi"],
            })
    player_search_json = json.dumps(player_search_data)

    # History chart data (last 10 days)
    dates = sorted(history.keys())[-10:]
    chart_data_js = "const chartData = " + str({
        "dates": dates,
        "teams": {
            team: [history.get(d, {}).get(team, {}).get("points", 0) for d in dates]
            for team in squads
        },
        "colors": {team: TEAM_COLORS.get(team, {"bg": "#333"})["bg"] for team in squads}
    }).replace("'", '"') + ";"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IPL 2026 Fantasy Leaderboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a1a;
            color: #e0e0e0;
            min-height: 100vh;
        }}

        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 16px;
        }}

        /* Header */
        .header {{
            text-align: center;
            padding: 24px 0 16px;
        }}
        .header h1 {{
            font-size: 1.6em;
            background: linear-gradient(135deg, #f7971e, #ffd200);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .header .subtitle {{
            color: #888;
            font-size: 0.85em;
            margin-top: 4px;
        }}
        .header .update-date {{
            color: #666;
            font-size: 0.75em;
            margin-top: 8px;
        }}

        /* Owner name in header */
        .owner-name {{
            font-size: 0.65em;
            opacity: 0.85;
            margin-top: 2px;
            font-style: italic;
        }}

        /* Fun title bar inside expanded card */
        .fun-title-bar {{
            padding: 10px 14px;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border-bottom: 1px solid #222;
            text-align: center;
        }}
        .fun-title {{
            font-size: 1em;
            font-weight: 700;
            display: block;
        }}
        .fun-subtitle {{
            font-size: 0.75em;
            color: #888;
            display: block;
            margin-top: 2px;
        }}
        .trash-talk {{
            font-size: 0.8em;
            color: #ff6b6b;
            font-style: italic;
            margin-top: 6px;
            padding: 4px 0;
        }}
        .owner-detail {{
            padding: 6px 14px;
            font-size: 0.78em;
            color: #aaa;
            background: #0f0f1f;
            border-bottom: 1px solid #1a1a2e;
        }}
        .podium-owner {{
            font-size: 0.7em;
            opacity: 0.85;
            font-style: italic;
        }}

        /* Champion glow */
        .team-card.champion {{
            box-shadow: 0 0 15px rgba(255, 210, 0, 0.4);
            border: 1px solid rgba(255, 210, 0, 0.3);
        }}
        /* Wooden spoon shame */
        .team-card.wooden-spoon {{
            opacity: 0.85;
            border: 1px dashed #ff4444;
        }}
        .team-card .team-header {{
            position: relative;
        }}

        /* WhatsApp share button */
        .share-btn {{
            display: block;
            margin: 20px auto;
            padding: 12px 24px;
            background: #25d366;
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 0.95em;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            max-width: 280px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .share-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);
        }}
        .share-btn:active {{ transform: scale(0.97); }}

        /* Confetti canvas */
        #confetti-canvas {{
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            z-index: 9999;
        }}

        /* Shame zone */
        .shame-zone {{
            margin-top: 24px;
            padding: 16px;
            background: linear-gradient(135deg, #1a0000, #0a0a1a);
            border: 1px dashed #ff4444;
            border-radius: 12px;
            text-align: center;
        }}
        .shame-zone h2 {{
            color: #ff4444;
            font-size: 1.1em;
            margin-bottom: 8px;
        }}
        .shame-zone .shame-text {{
            color: #ff6b6b;
            font-size: 0.85em;
            font-style: italic;
        }}
        .shame-zone .shame-owner {{
            font-size: 1.3em;
            margin-top: 8px;
        }}

        /* Dark horse alert */
        .dark-horse {{
            margin-top: 8px;
            padding: 8px 12px;
            background: linear-gradient(135deg, #1a3a00, #0a2a00);
            border: 1px solid #4caf50;
            border-radius: 8px;
            color: #76ff03;
            font-size: 0.8em;
            font-weight: 600;
            animation: pulse-glow 2s infinite;
        }}
        @keyframes pulse-glow {{
            0%, 100% {{ box-shadow: 0 0 5px rgba(76, 175, 80, 0.3); }}
            50% {{ box-shadow: 0 0 15px rgba(76, 175, 80, 0.6); }}
        }}

        /* Team Cards */
        .team-card {{
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
        .team-header {{
            display: flex;
            align-items: center;
            padding: 14px 16px;
            cursor: pointer;
            user-select: none;
            gap: 12px;
            transition: filter 0.2s;
        }}
        .team-header:hover {{ filter: brightness(1.1); }}
        .team-header:active {{ filter: brightness(0.95); }}

        .rank-badge {{
            font-size: 1.3em;
            font-weight: 800;
            min-width: 40px;
            opacity: 0.9;
        }}
        .team-info {{ flex: 1; }}
        .team-abbr {{ font-size: 1.2em; font-weight: 700; }}
        .team-full {{ font-size: 0.7em; opacity: 0.8; }}
        .team-pts {{ text-align: right; }}
        .pts-value {{ font-size: 1.5em; font-weight: 800; }}
        .pts-label {{ font-size: 0.65em; opacity: 0.7; text-transform: uppercase; }}
        .expand-icon {{
            font-size: 0.8em;
            opacity: 0.6;
            transition: transform 0.3s;
        }}
        .team-card.open .expand-icon {{ transform: rotate(180deg); }}

        /* Trend */
        .trend {{ font-size: 0.75em; font-weight: 600; }}
        .trend-up {{ color: #4caf50; }}
        .trend-down {{ color: #f44336; }}
        .trend-same {{ color: #888; }}
        .pt-diff {{ font-size: 0.7em; opacity: 0.7; }}

        /* Team Body (expandable) */
        .team-body {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.35s ease;
            background: #111122;
        }}
        .team-card.open .team-body {{
            max-height: 2000px;
        }}

        /* XI Table */
        .xi-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
        }}
        .xi-table th {{
            background: #1a1a2e;
            padding: 8px 10px;
            text-align: left;
            font-size: 0.8em;
            color: #888;
            text-transform: uppercase;
        }}
        .xi-table td {{
            padding: 7px 10px;
            border-bottom: 1px solid #1a1a2e;
        }}
        .xi-table .num {{ width: 30px; color: #666; }}
        .xi-table .pts {{ text-align: right; font-weight: 600; color: #ffd200; }}
        .xi-table th:last-child {{ text-align: right; }}
        .total-row td {{ border-top: 2px solid #333; padding-top: 10px; }}
        .avg-row td {{ color: #888; font-size: 0.9em; }}
        .player-name {{ font-weight: 500; }}

        /* Team Stats Summary */
        .team-stats {{
            padding: 12px 14px;
            background: #0d0d20;
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            font-size: 0.8em;
            border-bottom: 1px solid #151530;
        }}
        .stat-row:last-child {{ border-bottom: none; }}
        .stat-highlight {{ color: #ffd200; font-weight: 700; }}
        .stat-dim {{ color: #ff6b6b; }}

        /* Tab Bar */
        .tab-bar {{
            display: flex;
            background: #0d0d1f;
            border-top: 1px solid #1a1a2e;
            border-bottom: 1px solid #1a1a2e;
        }}
        .tab {{
            flex: 1;
            text-align: center;
            padding: 10px 0;
            font-size: 0.78em;
            font-weight: 600;
            color: #666;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            user-select: none;
        }}
        .tab:hover {{ color: #aaa; background: #111128; }}
        .tab.active {{
            color: #ffd200;
            border-bottom-color: #ffd200;
        }}

        /* Tab Content */
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}

        /* Full Squad styles */
        .squad-table .on-bench {{ opacity: 0.5; }}
        .squad-table .in-xi {{ background: rgba(255, 210, 0, 0.05); }}
        .xi-status {{ text-align: center; font-size: 0.85em; }}
        .xi-table .price {{ text-align: right; font-size: 0.82em; color: #aaa; }}
        .overseas-badge {{
            display: inline-block;
            padding: 1px 5px;
            border-radius: 6px;
            font-size: 0.6em;
            font-weight: 700;
            background: #1565c0;
            color: #fff;
            margin-left: 4px;
            vertical-align: middle;
            letter-spacing: 0.5px;
        }}
        .orig-team-badge {{
            display: inline-block;
            padding: 1px 5px;
            border-radius: 6px;
            font-size: 0.6em;
            font-weight: 700;
            margin-left: 4px;
            vertical-align: middle;
            letter-spacing: 0.5px;
            opacity: 0.85;
        }}
        .squad-legend {{
            padding: 8px 14px;
            font-size: 0.7em;
            color: #666;
            text-align: center;
        }}

        /* Role Badges */
        .role-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.7em;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .role-wk {{ background: #1565c0; color: #fff; }}
        .role-bat {{ background: #e65100; color: #fff; }}
        .role-ar {{ background: #2e7d32; color: #fff; }}
        .role-bowl {{ background: #6a1b9a; color: #fff; }}

        /* History Section */
        .history-section {{
            margin-top: 24px;
            padding: 16px;
            background: #111122;
            border-radius: 12px;
        }}
        .history-section h2 {{
            font-size: 1em;
            color: #888;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .history-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8em;
            overflow-x: auto;
        }}
        .history-table th, .history-table td {{
            padding: 8px 10px;
            text-align: center;
            border-bottom: 1px solid #1a1a2e;
        }}
        .history-table th {{ color: #666; font-size: 0.85em; }}
        .history-table td {{ color: #ccc; }}
        .history-table .team-col {{
            text-align: left;
            font-weight: 600;
            position: sticky;
            left: 0;
            background: #111122;
            z-index: 2;
            min-width: 120px;
            white-space: nowrap;
        }}
        .history-table thead th.team-col {{
            z-index: 3;
            background: #111122;
        }}
        .history-table tbody tr:nth-child(odd) {{
            background: #0e0e1e;
        }}
        .history-table tbody tr:nth-child(even) {{
            background: #161630;
        }}
        .history-table tbody tr:nth-child(odd) .team-col {{
            background: #0e0e1e;
        }}
        .history-table tbody tr:nth-child(even) .team-col {{
            background: #161630;
        }}
        .history-table tbody tr:hover {{
            background: #1e1e3a;
        }}
        .history-table tbody tr:hover .team-col {{
            background: #1e1e3a;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 20px;
            color: #444;
            font-size: 0.7em;
        }}

        /* Podium (top 3) */
        .podium {{
            display: flex;
            justify-content: center;
            align-items: flex-end;
            gap: 8px;
            margin: 20px 0;
            height: 200px;
        }}
        .podium-item {{
            text-align: center;
            border-radius: 10px 10px 0 0;
            padding: 14px 10px 10px;
            min-width: 100px;
            position: relative;
        }}
        .podium-item.first {{ height: 190px; }}
        .podium-item.second {{ height: 155px; }}
        .podium-item.third {{ height: 130px; }}
        .podium-rank {{
            font-size: 1.8em;
            font-weight: 900;
            opacity: 0.3;
        }}
        .podium-team {{
            font-size: 1.1em;
            font-weight: 700;
            margin: 4px 0;
        }}
        .podium-pts {{
            font-size: 0.8em;
            opacity: 0.8;
        }}

        /* Awards Section */
        .awards-section {{
            margin-top: 30px;
            padding: 20px 16px;
            background: linear-gradient(180deg, #0d0d20 0%, #0a0a1a 100%);
            border-radius: 16px;
            border: 1px solid #1a1a2e;
        }}
        .awards-section h2 {{
            font-size: 1.1em;
            color: #ffd200;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 16px;
            text-align: center;
            padding-bottom: 12px;
            border-bottom: 1px solid #1a1a2e;
        }}
        .award-card {{
            border-radius: 14px;
            overflow: hidden;
            margin-bottom: 14px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.4);
            background: linear-gradient(135deg, #111125, #0e0e22);
            transition: transform 0.2s, box-shadow 0.2s;
            position: relative;
        }}
        .award-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.5);
        }}
        .award-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            border-radius: 14px;
            pointer-events: none;
        }}
        .award-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px 12px;
        }}
        .award-emoji {{
            font-size: 2.2em;
            min-width: 50px;
            text-align: center;
            filter: drop-shadow(0 2px 6px rgba(0,0,0,0.4));
        }}
        .award-title-block {{ flex: 1; }}
        .award-title {{
            font-size: 1em;
            font-weight: 800;
            letter-spacing: 0.5px;
        }}
        .award-subtitle {{
            font-size: 0.7em;
            color: #666;
            margin-top: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .award-winner {{
            text-align: right;
        }}
        .award-winner-name {{
            font-size: 1.05em;
            font-weight: 900;
        }}
        .award-winner-team {{
            font-size: 0.68em;
            opacity: 0.6;
            margin-top: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .award-stats-bar {{
            display: flex;
            gap: 0;
            margin: 0 16px;
            background: #0a0a18;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #1a1a2e;
        }}
        .award-stat-item {{
            flex: 1;
            text-align: center;
            padding: 8px 6px;
            border-right: 1px solid #1a1a2e;
        }}
        .award-stat-item:last-child {{ border-right: none; }}
        .award-stat-label {{
            font-size: 0.6em;
            color: #555;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .award-stat-value {{
            font-size: 0.9em;
            font-weight: 800;
            margin-top: 2px;
        }}
        .award-reason {{
            padding: 12px 16px;
            font-size: 0.78em;
            color: #888;
            line-height: 1.6;
            font-style: italic;
            border-top: 1px solid #141428;
            margin-top: 10px;
        }}

        /* Player Search */
        .search-toggle {{
            position: absolute;
            top: 16px;
            right: 0;
            width: 34px;
            height: 34px;
            border-radius: 50%;
            background: #111122;
            border: 1px solid #1a1a2e;
            color: #888;
            font-size: 0.9em;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s, border-color 0.2s;
            z-index: 101;
        }}
        .search-toggle:hover {{ background: #1a1a2e; border-color: #ffd200; color: #ffd200; }}
        .search-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 200;
            padding: 60px 16px 16px;
        }}
        .search-overlay.active {{ display: block; }}
        .search-box {{
            max-width: 420px;
            margin: 0 auto;
            position: relative;
        }}
        .search-close {{
            position: absolute;
            top: -40px;
            right: 0;
            background: none;
            border: none;
            color: #888;
            font-size: 1.4em;
            cursor: pointer;
        }}
        .search-close:hover {{ color: #fff; }}
        .search-input {{
            width: 100%;
            padding: 12px 16px;
            background: #111122;
            border: 1px solid #1a1a2e;
            border-radius: 12px;
            color: #e0e0e0;
            font-size: 0.9em;
            outline: none;
            transition: border-color 0.2s;
        }}
        .search-input:focus {{
            border-color: #ffd200;
        }}
        .search-input::placeholder {{ color: #555; }}
        .search-results {{
            margin-top: 8px;
            max-height: calc(100vh - 180px);
            overflow-y: auto;
            display: none;
            background: #0d0d1f;
            border: 1px solid #1a1a2e;
            border-radius: 10px;
        }}
        .search-results.active {{ display: block; }}
        .search-result-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            cursor: pointer;
            border-bottom: 1px solid #141428;
            gap: 8px;
            transition: background 0.15s;
        }}
        .search-result-item:last-child {{ border-bottom: none; }}
        .search-result-item:hover {{ background: #151530; }}
        .search-result-item .sr-left {{
            flex: 1;
            min-width: 0;
        }}
        .search-result-item .sr-name {{
            font-weight: 600;
            font-size: 0.85em;
        }}
        .search-result-item .sr-meta {{
            font-size: 0.68em;
            color: #888;
            margin-top: 2px;
        }}
        .search-result-item .sr-right {{
            text-align: right;
            flex-shrink: 0;
        }}
        .search-result-item .sr-pts {{
            font-size: 0.9em;
            font-weight: 700;
            color: #ffd200;
        }}
        .search-result-item .sr-price {{
            font-size: 0.65em;
            color: #aaa;
        }}
        .search-no-results {{
            text-align: center;
            padding: 14px;
            color: #555;
            font-size: 0.8em;
        }}

        /* Today's Players to Watch */
        .today-section {{
            margin: 20px 0;
            padding: 0;
            background: linear-gradient(135deg, #0d1a2e, #0a0a1a);
            border-radius: 14px;
            border: 1px solid #1a3a5e;
            overflow: hidden;
        }}
        .today-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 16px 16px 6px;
        }}
        .today-header h2 {{
            font-size: 1.05em;
            color: #4fc3f7;
            margin: 0;
        }}
        .today-live-dot {{
            width: 10px; height: 10px;
            border-radius: 50%;
            background: #4caf50;
            animation: live-pulse 1.5s infinite;
        }}
        @keyframes live-pulse {{
            0%, 100% {{ opacity: 1; box-shadow: 0 0 4px #4caf50; }}
            50% {{ opacity: 0.4; box-shadow: 0 0 10px #4caf50; }}
        }}
        .today-match-info {{
            padding: 0 16px;
            font-size: 1.2em;
            font-weight: 800;
            color: #ffd200;
            letter-spacing: 1px;
        }}
        .today-subtitle {{
            padding: 4px 16px 10px;
            font-size: 0.72em;
            color: #666;
        }}
        .today-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82em;
        }}
        .today-table th {{
            background: #0a1525;
            padding: 8px 8px;
            text-align: left;
            font-size: 0.78em;
            color: #4fc3f7;
            text-transform: uppercase;
        }}
        .today-table th:last-child {{ text-align: center; }}
        .today-table td {{
            padding: 7px 8px;
            border-bottom: 1px solid #112240;
        }}
        .today-row:hover {{ background: rgba(79, 195, 247, 0.05); }}
        .today-table .num {{ width: 28px; color: #555; }}
        .today-table .pts {{ text-align: right; font-weight: 700; color: #ffd200; }}
        .today-pts-hot {{ color: #4caf50 !important; font-size: 1.05em; }}
        .today-pts-warm {{ color: #ffa726 !important; }}

        .today-owner {{ text-align: center; font-size: 0.8em; }}
        .today-price {{ text-align: center; color: #aaa; font-size: 0.85em; white-space: nowrap; }}
        .today-day {{ text-align: right; font-weight: 700; font-size: 0.85em; }}
        .today-day-hot {{ color: #4caf50; }}
        .today-day-warm {{ color: #ffa726; }}
        .today-day-zero {{ color: #555; }}
        .today-orig-team {{
            display: inline-block;
            padding: 1px 5px;
            border-radius: 6px;
            font-size: 0.6em;
            font-weight: 700;
            margin-left: 4px;
            vertical-align: middle;
        }}
        .today-owner-badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 6px;
            font-size: 0.7em;
            font-weight: 700;
        }}
        .today-unclaimed {{
            background: #333 !important;
            color: #888 !important;
        }}
        .today-divider {{
            text-align: center;
            padding: 8px 0;
            font-size: 0.72em;
            color: #555;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-top: 1px dashed #1a3a5e;
        }}
        .today-total-row {{
            background: #0a1525;
            border-top: 2px solid #1a3a5e;
        }}
        .today-total-row td {{
            padding: 10px 8px;
            font-size: 0.9em;
        }}
        .today-total-row .pts {{
            color: #ffd200;
        }}
        .today-total-row .today-day {{
            color: #4caf50;
        }}
        .today-filter-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            padding: 10px 0;
            justify-content: center;
        }}
        .today-filter-btn {{
            padding: 5px 12px;
            border-radius: 16px;
            border: 1px solid #222;
            background: #111;
            color: #888;
            font-size: 0.75em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .today-filter-btn:hover {{
            background: #1a1a2e;
            color: #ccc;
        }}
        .today-filter-btn.active {{
            background: var(--btn-bg, #ffd200);
            color: var(--btn-text, #000);
            border-color: var(--btn-bg, #ffd200);
        }}

        /* Page-level tab bar */
        .page-tab-bar {{
            display: flex;
            background: #0d0d1f;
            border-radius: 12px;
            margin: 16px 0;
            overflow: hidden;
            border: 1px solid #1a1a2e;
        }}
        .page-tab {{
            flex: 1;
            text-align: center;
            padding: 12px 0;
            font-size: 0.85em;
            font-weight: 700;
            color: #666;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
            user-select: none;
        }}
        .page-tab:hover {{ color: #aaa; background: #111128; }}
        .page-tab.active {{
            color: #ffd200;
            border-bottom-color: #ffd200;
            background: #111128;
        }}
        .page-tab-content {{
            display: none;
        }}
        .page-tab-content.active {{
            display: block;
        }}
        .page-tab .tab-badge {{
            display: inline-block;
            padding: 1px 7px;
            border-radius: 10px;
            font-size: 0.7em;
            margin-left: 5px;
            background: #4caf50;
            color: #fff;
            vertical-align: middle;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 4px; }}
        ::-webkit-scrollbar-track {{ background: #0a0a1a; }}
        ::-webkit-scrollbar-thumb {{ background: #333; border-radius: 2px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header" style="position:relative">
            <h1>IPL 2026 Fantasy Leaderboard</h1>
            <div class="subtitle">Friends Auction League</div>
            <div class="update-date">Last updated: {TODAY}</div>
            <button class="search-toggle" onclick="openSearch()" title="Search player">&#128269;</button>
        </div>

        <!-- Search Overlay -->
        <div class="search-overlay" id="search-overlay">
            <div class="search-box">
                <button class="search-close" onclick="closeSearch()">&#10005;</button>
                <input type="text" class="search-input" id="player-search"
                       placeholder="Type player name..."
                       autocomplete="off">
                <div class="search-results" id="search-results"></div>
            </div>
        </div>

        <!-- Page Tab Bar -->
        <div class="page-tab-bar">
            <div class="page-tab active" onclick="switchPageTab('leaderboard')">&#127942; Leaderboard</div>
            <div class="page-tab" onclick="switchPageTab('today')">{"&#9917; Today's " + ("Matches" if len(today_matches) > 1 else "Match") + (' <span class="tab-badge">LIVE</span>' if today_matches else '') if today_matches else "&#9917; Today's Match"}</div>
        </div>

        <!-- Page Tab: Leaderboard -->
        <div class="page-tab-content active" id="page-leaderboard">

        <!-- Podium -->
        <div class="podium">
            {"".join(f'''
            <div class="podium-item {'first' if i==0 else 'second' if i==1 else 'third'}"
                 style="background:{TEAM_COLORS.get(rankings[p]['team'], {}).get('bg','#333')};
                        color:{TEAM_COLORS.get(rankings[p]['team'], {}).get('text','#fff')}">
                <div class="podium-rank">{"🥇" if i==0 else "🥈" if i==1 else "🥉"}</div>
                <div class="podium-team">{rankings[p]['team']}</div>
                <div class="podium-owner">{OWNERS.get(rankings[p]['team'], {}).get('nick','')}</div>
                <div class="podium-pts">{rankings[p]['points']} pts</div>
            </div>
            ''' for i, p in enumerate([0, 1, 2]) if p < len(rankings))}
        </div>

        <!-- Team Cards -->
        {team_cards}

        <!-- History Table -->
        {"" if not history else f'''
        <div class="history-section">
            <h2>Ranking History</h2>
            <div style="overflow-x:auto">
            <table class="history-table">
                <thead>
                    <tr>
                        <th class="team-col">Team</th>
                        {"".join(f'<th>{d[5:]}</th>' for d in dates)}
                    </tr>
                </thead>
                <tbody>
                    {"".join(
                        '<tr><td class="team-col">' + team + ' <small>(' + OWNERS.get(team, {}).get('nick','') + ')</small></td>' +
                        "".join(
                            '<td>' + str(history.get(d, {}).get(team, {}).get("points", "-")) + '</td>'
                            for d in dates
                        ) + '</tr>'
                        for team in [r["team"] for r in rankings]
                    )}
                </tbody>
            </table>
            </div>
        </div>
        '''}

        <div class="footer">
            Auto-generated by IPL Fantasy Pipeline &middot; {TODAY}
        </div>

        </div><!-- end page-leaderboard -->

        <!-- Page Tab: Today's Match -->
        <div class="page-tab-content" id="page-today">
            {today_section_html if today_section_html else '<div style="text-align:center;padding:40px 16px;color:#555"><div style="font-size:2em;margin-bottom:10px">&#128164;</div>No match scheduled for today.</div>'}
        </div>

    </div>

    <!-- WhatsApp Share -->
    <a class="share-btn" id="wa-share" target="_blank" rel="noopener noreferrer">
        &#128172; Share on WhatsApp
    </a>

    <!-- Auction Awards -->
    <div class="container">
        <div class="awards-section">
            <h2>&#127942; Auction Awards &#127942;</h2>
            {awards_html}
        </div>
    </div>

    <!-- Shame Zone for last place -->
    <div class="container">
        <div class="shame-zone">
            <h2>&#127869; Wall of Shame &#127869;</h2>
            <div class="shame-owner">{OWNERS.get(rankings[-1]['team'], {}).get('nick','???')}</div>
            <div class="shame-text">
                Owner of {rankings[-1]['team']} ({rankings[-1]['points']} pts)<br>
                "Your auction strategy was basically: close eyes, raise paddle."<br>
                <br>
                &#9749; Chai duty: <strong>{OWNERS.get(rankings[-1]['team'], {}).get('nick','???')}</strong>
            </div>
        </div>
    </div>

    <!-- Confetti Canvas -->
    <canvas id="confetti-canvas"></canvas>

    <script>
        function toggleTeam(id) {{
            const card = document.getElementById('team-' + id);
            card.classList.toggle('open');
        }}
        function switchTab(teamId, tab) {{
            const body = document.getElementById('body-' + teamId);
            // Deactivate all tabs and content in this card
            body.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            body.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            // Activate clicked tab
            const tabs = body.querySelectorAll('.tab');
            const tabMap = {{'xi': 0, 'squad': 1, 'stats': 2}};
            tabs[tabMap[tab]]?.classList.add('active');
            document.getElementById('tab-' + tab + '-' + teamId)?.classList.add('active');
        }}
        document.querySelector('.team-card')?.classList.add('open');

        // Page-level tab switching
        function switchPageTab(tab) {{
            document.querySelectorAll('.page-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.page-tab-content').forEach(c => c.classList.remove('active'));
            const tabMap = {{'leaderboard': 0, 'today': 1}};
            document.querySelectorAll('.page-tab')[tabMap[tab]]?.classList.add('active');
            document.getElementById('page-' + tab)?.classList.add('active');
        }}

        // Today's Match owner filter
        function filterTodayOwner(owner) {{
            document.querySelectorAll('.today-filter-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            const rows = document.querySelectorAll('.today-table tbody tr');
            let visibleIdx = 0;
            let totalPts = 0;
            let totalDay = 0;
            rows.forEach(row => {{
                const rowOwner = row.getAttribute('data-owner');
                if (!rowOwner) return;
                if (owner === 'ALL') {{
                    row.style.display = '';
                    if (row.classList.contains('today-row')) {{
                        visibleIdx++;
                        row.querySelector('.num').textContent = visibleIdx;
                        totalPts += parseInt(row.querySelector('.pts')?.textContent) || 0;
                        const dayText = row.querySelector('.today-day')?.textContent?.replace('+','') || '0';
                        totalDay += parseInt(dayText) || 0;
                    }}
                }} else {{
                    const show = rowOwner === owner;
                    row.style.display = show ? '' : 'none';
                    if (show && row.classList.contains('today-row')) {{
                        visibleIdx++;
                        row.querySelector('.num').textContent = visibleIdx;
                        totalPts += parseInt(row.querySelector('.pts')?.textContent) || 0;
                        const dayText = row.querySelector('.today-day')?.textContent?.replace('+','') || '0';
                        totalDay += parseInt(dayText) || 0;
                    }}
                }}
            }});
            const totalPtsEl = document.getElementById('today-total-pts');
            const totalDayEl = document.getElementById('today-total-day');
            if (totalPtsEl) totalPtsEl.innerHTML = '<strong>' + totalPts + '</strong>';
            if (totalDayEl) totalDayEl.innerHTML = '<strong>' + (totalDay > 0 ? '+' + totalDay : totalDay) + '</strong>';
        }}

        // Player Search
        const allPlayers = {player_search_json};
        const searchInput = document.getElementById('player-search');
        const searchResults = document.getElementById('search-results');
        const searchOverlay = document.getElementById('search-overlay');
        function openSearch() {{
            searchOverlay.classList.add('active');
            setTimeout(() => searchInput.focus(), 100);
        }}
        function closeSearch() {{
            searchOverlay.classList.remove('active');
            searchInput.value = '';
            searchResults.classList.remove('active');
            searchResults.innerHTML = '';
        }}
        searchOverlay.addEventListener('click', function(e) {{
            if (e.target === searchOverlay) closeSearch();
        }});
        searchInput.addEventListener('input', function() {{
            const q = this.value.trim().toLowerCase();
            if (q.length < 2) {{ searchResults.classList.remove('active'); searchResults.innerHTML = ''; return; }}
            const matches = allPlayers.filter(p => p.name.toLowerCase().includes(q));
            searchResults.classList.add('active');
            if (matches.length === 0) {{
                searchResults.innerHTML = '<div class="search-no-results">No players found</div>';
                return;
            }}
            searchResults.innerHTML = matches.slice(0, 15).map(p => {{
                const osBadge = p.foreign ? ' <span class="overseas-badge">OS</span>' : '';
                const xiBadge = p.in_xi ? ' &#9989;' : '';
                return `<div class="search-result-item" onclick="scrollToTeam('${{p.team.toLowerCase()}}')">
                    <div class="sr-left">
                        <div class="sr-name">${{p.name}}${{osBadge}}</div>
                        <div class="sr-meta">${{p.team}} &middot; ${{p.owner}} &middot; ${{p.role}}${{xiBadge}}</div>
                    </div>
                    <div class="sr-right">
                        <div class="sr-pts">${{p.pts}} pts</div>
                        <div class="sr-price">${{p.price}}</div>
                    </div>
                </div>`;
            }}).join('');
        }});
        function scrollToTeam(teamId) {{
            closeSearch();
            switchPageTab('leaderboard');
            const card = document.getElementById('team-' + teamId);
            if (card) {{
                card.classList.add('open');
                card.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}

        // WhatsApp share
        const rankings = {str([{"rank": i+1, "team": r["team"], "nick": OWNERS.get(r["team"], {}).get("nick",""), "pts": r["points"]} for i, r in enumerate(rankings)]).replace("'", '"')};
        let msg = "&#127942; *IPL 2026 Fantasy Leaderboard*\\n";
        msg += "_Updated: {TODAY}_\\n\\n";
        rankings.forEach(r => {{
            const medal = r.rank === 1 ? "&#128081;" : r.rank === 2 ? "&#129352;" : r.rank === 3 ? "&#129353;" : r.rank === rankings.length ? "&#127869;" : "&#128200;";
            msg += medal + " #" + r.rank + " *" + r.team + "* (" + r.nick + ") — " + r.pts + " pts\\n";
        }});
        msg += "\\n&#128169; Chai duty: *" + rankings[rankings.length-1].nick + "* &#9749;";
        const waUrl = "https://api.whatsapp.com/send?text=" + encodeURIComponent(msg.replace(/&#\\d+;/g, ''));
        document.getElementById('wa-share').href = waUrl;

        // Confetti for #1 team
        (function() {{
            const canvas = document.getElementById('confetti-canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            const pieces = [];
            const colors = ['#ffd200', '#ff6b6b', '#4caf50', '#2196f3', '#ff9800', '#e91e63', '#9c27b0'];
            for (let i = 0; i < 120; i++) {{
                pieces.push({{
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height - canvas.height,
                    w: Math.random() * 8 + 4,
                    h: Math.random() * 6 + 2,
                    color: colors[Math.floor(Math.random() * colors.length)],
                    speed: Math.random() * 3 + 1,
                    angle: Math.random() * 360,
                    spin: (Math.random() - 0.5) * 4,
                    drift: (Math.random() - 0.5) * 1.5,
                }});
            }}
            let frame = 0;
            function draw() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                if (frame > 200) {{ canvas.style.display = 'none'; return; }}
                pieces.forEach(p => {{
                    ctx.save();
                    ctx.translate(p.x, p.y);
                    ctx.rotate(p.angle * Math.PI / 180);
                    ctx.fillStyle = p.color;
                    ctx.globalAlpha = Math.max(0, 1 - frame / 200);
                    ctx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
                    ctx.restore();
                    p.y += p.speed;
                    p.x += p.drift;
                    p.angle += p.spin;
                }});
                frame++;
                requestAnimationFrame(draw);
            }}
            draw();
        }})();
    </script>
</body>
</html>"""
    return html


def main():
    print("Loading fantasy data...")
    fantasy_points = load_fantasy_points()
    original_teams = load_original_teams()
    rankings = compute_rankings(fantasy_points, original_teams)
    history = load_history()

    html = generate_html(rankings, history, fantasy_points)

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Leaderboard generated → {OUTPUT_HTML}")
    print(f"   Open in browser or push docs/ folder to GitHub Pages")


if __name__ == "__main__":
    main()
