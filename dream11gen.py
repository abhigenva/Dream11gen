import argparse
import json
import random
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

TEAM_ALIASES = {
    "CSK": "CSK", "CHENNAI SUPER KINGS": "CSK",
    "DC": "DC", "DELHI CAPITALS": "DC",
    "GT": "GT", "GUJARAT TITANS": "GT",
    "KKR": "KKR", "KOLKATA KNIGHT RIDERS": "KKR",
    "LSG": "LSG", "LUCKNOW SUPER GIANTS": "LSG",
    "MI": "MI", "MUMBAI INDIANS": "MI",
    "PBKS": "PBKS", "PUNJAB KINGS": "PBKS",
    "RR": "RR", "RAJASTHAN ROYALS": "RR",
    "RCB": "RCB", "ROYAL CHALLENGERS BENGALURU": "RCB",
    "SRH": "SRH", "SUNRISERS HYDERABAD": "SRH",
}

LIVE_SQUAD_URLS = {
    "MI": [
        "https://www.espncricinfo.com/series/ipl-2026-1510719/mumbai-indians-squad-1511109/series-squads",
        "https://www.iplt20.com/teams/mumbai-indians",
    ],
    "LSG": [
        "https://www.espncricinfo.com/series/ipl-2026-1510719/lucknow-super-giants-squad-1511110/series-squads",
        "https://www.iplt20.com/teams/lucknow-super-giants",
    ],
    "CSK": ["https://www.iplt20.com/teams/chennai-super-kings"],
    "DC": ["https://www.iplt20.com/teams/delhi-capitals"],
    "GT": ["https://www.iplt20.com/teams/gujarat-titans"],
    "KKR": ["https://www.iplt20.com/teams/kolkata-knight-riders"],
    "PBKS": ["https://www.iplt20.com/teams/punjab-kings"],
    "RR": ["https://www.iplt20.com/teams/rajasthan-royals"],
    "RCB": ["https://www.iplt20.com/teams/royal-challengers-bengaluru"],
    "SRH": ["https://www.iplt20.com/teams/sunrisers-hyderabad"],
}

FALLBACK_SQUADS = {
    "MI": [
        ("Ryan Rickelton", "WK"), ("Rohit Sharma", "BAT"), ("Suryakumar Yadav", "BAT"),
        ("Tilak Varma", "BAT"), ("Naman Dhir", "AR"), ("Hardik Pandya", "AR"),
        ("Will Jacks", "AR"), ("Mitchell Santner", "AR"), ("Raj Angad Bawa", "AR"),
        ("Deepak Chahar", "BOWL"), ("Jasprit Bumrah", "BOWL"), ("Trent Boult", "BOWL"),
        ("Ashwani Kumar", "BOWL"), ("Reece Topley", "BOWL"), ("Satyanarayana Raju", "BOWL"),
        ("Mujeeb Ur Rahman", "BOWL"), ("Robin Minz", "WK"), ("Shrijith Krishnan", "WK")
    ],
    "LSG": [
        ("Rishabh Pant", "WK"), ("Nicholas Pooran", "WK"), ("Aiden Markram", "AR"),
        ("Mitchell Marsh", "AR"), ("Ayush Badoni", "BAT"), ("David Miller", "BAT"),
        ("Abdul Samad", "AR"), ("Shahbaz Ahmed", "AR"), ("Shardul Thakur", "AR"),
        ("Digvesh Singh Rathi", "BOWL"), ("Avesh Khan", "BOWL"), ("Akash Deep", "BOWL"),
        ("Prince Yadav", "BOWL"), ("Ravi Bishnoi", "BOWL"), ("Mayank Yadav", "BOWL"),
        ("Mohsin Khan", "BOWL"), ("Himmat Singh", "BAT"), ("Aryan Juyal", "WK")
    ],
    "CSK": [
        ("Ruturaj Gaikwad", "BAT"), ("Devon Conway", "WK"), ("Rahul Tripathi", "BAT"),
        ("Shivam Dube", "AR"), ("Deepak Hooda", "AR"), ("Ravindra Jadeja", "AR"),
        ("MS Dhoni", "WK"), ("Rachin Ravindra", "AR"), ("Sam Curran", "AR"),
        ("Noor Ahmad", "BOWL"), ("Khaleel Ahmed", "BOWL"), ("Matheesha Pathirana", "BOWL"),
        ("Mukesh Choudhary", "BOWL"), ("Nathan Ellis", "BOWL"), ("R Ashwin", "AR")
    ],
    "DC": [
        ("KL Rahul", "WK"), ("Faf Du Plessis", "BAT"), ("Jake Fraser-McGurk", "BAT"),
        ("Tristan Stubbs", "BAT"), ("Karun Nair", "BAT"), ("Axar Patel", "AR"),
        ("Ashutosh Sharma", "AR"), ("Vipraj Nigam", "AR"), ("Mitchell Starc", "BOWL"),
        ("Kuldeep Yadav", "BOWL"), ("Mukesh Kumar", "BOWL"), ("T Natarajan", "BOWL"),
        ("Mohit Sharma", "BOWL"), ("Abishek Porel", "WK"), ("Donovan Ferreira", "WK")
    ],
    "GT": [
        ("Shubman Gill", "BAT"), ("Jos Buttler", "WK"), ("Sai Sudharsan", "BAT"),
        ("Shahrukh Khan", "AR"), ("Rahul Tewatia", "AR"), ("Rashid Khan", "AR"),
        ("Washington Sundar", "AR"), ("Sai Kishore", "BOWL"), ("Mohammed Siraj", "BOWL"),
        ("Prasidh Krishna", "BOWL"), ("Ishant Sharma", "BOWL"), ("Gerald Coetzee", "BOWL"),
        ("Sherfane Rutherford", "BAT"), ("Glenn Phillips", "AR"), ("Kagiso Rabada", "BOWL")
    ],
    "KKR": [
        ("Quinton De Kock", "WK"), ("Sunil Narine", "AR"), ("Ajinkya Rahane", "BAT"),
        ("Venkatesh Iyer", "AR"), ("Rinku Singh", "BAT"), ("Andre Russell", "AR"),
        ("Ramandeep Singh", "AR"), ("Harshit Rana", "BOWL"), ("Vaibhav Arora", "BOWL"),
        ("Varun Chakaravarthy", "BOWL"), ("Spencer Johnson", "BOWL"), ("Anrich Nortje", "BOWL"),
        ("Moeen Ali", "AR"), ("Rahmanullah Gurbaz", "WK"), ("Angkrish Raghuvanshi", "BAT")
    ],
    "PBKS": [
        ("Prabhsimran Singh", "WK"), ("Shreyas Iyer", "BAT"), ("Marcus Stoinis", "AR"),
        ("Nehal Wadhera", "BAT"), ("Shashank Singh", "BAT"), ("Glenn Maxwell", "AR"),
        ("Marco Jansen", "AR"), ("Azmatullah Omarzai", "AR"), ("Arshdeep Singh", "BOWL"),
        ("Yuzvendra Chahal", "BOWL"), ("Lockie Ferguson", "BOWL"), ("Harpreet Brar", "AR"),
        ("Priyansh Arya", "BAT"), ("Josh Inglis", "WK"), ("Vijaykumar Vyshak", "BOWL")
    ],
    "RR": [
        ("Sanju Samson", "WK"), ("Yashasvi Jaiswal", "BAT"), ("Nitish Rana", "BAT"),
        ("Riyan Parag", "AR"), ("Dhruv Jurel", "WK"), ("Shimron Hetmyer", "BAT"),
        ("Wanindu Hasaranga", "AR"), ("Jofra Archer", "BOWL"), ("Maheesh Theekshana", "BOWL"),
        ("Sandeep Sharma", "BOWL"), ("Tushar Deshpande", "BOWL"), ("Yudhvir Singh", "BOWL"),
        ("Shubham Dubey", "BAT"), ("Kunal Rathore", "WK"), ("Fazalhaq Farooqi", "BOWL")
    ],
    "RCB": [
        ("Phil Salt", "WK"), ("Virat Kohli", "BAT"), ("Rajat Patidar", "BAT"),
        ("Liam Livingstone", "AR"), ("Jitesh Sharma", "WK"), ("Tim David", "AR"),
        ("Krunal Pandya", "AR"), ("Romario Shepherd", "AR"), ("Bhuvneshwar Kumar", "BOWL"),
        ("Josh Hazlewood", "BOWL"), ("Yash Dayal", "BOWL"), ("Suyash Sharma", "BOWL"),
        ("Devdutt Padikkal", "BAT"), ("Jacob Bethell", "AR"), ("Rasikh Dar", "BOWL")
    ],
    "SRH": [
        ("Travis Head", "BAT"), ("Abhishek Sharma", "AR"), ("Ishan Kishan", "WK"),
        ("Nitish Kumar Reddy", "AR"), ("Heinrich Klaasen", "WK"), ("Aniket Verma", "BAT"),
        ("Abhinav Manohar", "BAT"), ("Pat Cummins", "BOWL"), ("Harshal Patel", "BOWL"),
        ("Mohammed Shami", "BOWL"), ("Rahul Chahar", "BOWL"), ("Adam Zampa", "BOWL"),
        ("Wiaan Mulder", "AR"), ("Kamindu Mendis", "AR"), ("Simarjeet Singh", "BOWL")
    ],
}

@dataclass
class Player:
    name: str
    team: str
    role: str
    score: float
    tags: List[str]

def normalize_team(s: str) -> str:
    key = s.strip().upper()
    if key not in TEAM_ALIASES:
        raise ValueError(f"Unknown team: {s}")
    return TEAM_ALIASES[key]

def try_live_squad(team_code: str) -> List[Player]:
    urls = LIVE_SQUAD_URLS.get(team_code, [])
    bad_tokens = {"news", "videos", "fixtures", "results", "squad", "overview", "schedule"}
    names = []

    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            text_items = [t.strip() for t in soup.stripped_strings]

            for item in text_items:
                if len(item.split()) < 2 or len(item.split()) > 4:
                    continue
                if any(ch.isdigit() for ch in item):
                    continue
                if item.lower() in bad_tokens:
                    continue
                if any(tok in item.lower() for tok in ["partner", "ticket", "follow", "shop", "official"]):
                    continue
                if re.fullmatch(r"[A-Za-z .'-]+", item):
                    names.append(item)
        except Exception:
            continue

    dedup = []
    seen = set()
    for n in names:
        k = n.lower()
        if k not in seen:
            seen.add(k)
            dedup.append(n)

    fallback_names = {name for name, _ in FALLBACK_SQUADS[team_code]}
    matched = [n for n in dedup if n in fallback_names]
    role_map = {name: role for name, role in FALLBACK_SQUADS[team_code]}

    if len(matched) >= 8:
        return [Player(name=n, team=team_code, role=role_map.get(n, "BAT"), score=0.0, tags=[]) for n in matched]

    return []

def fetch_team_squad(team_code: str) -> List[Player]:
    live = try_live_squad(team_code)
    if len(live) >= 11:
        return live
    return [Player(name=n, team=team_code, role=r, score=0.0, tags=[]) for n, r in FALLBACK_SQUADS[team_code]]

def role_weight(role: str) -> float:
    return {"WK": 1.05, "BAT": 1.0, "AR": 1.18, "BOWL": 1.03}.get(role, 1.0)

def captain_bias(name: str) -> float:
    anchors = {
        "Virat Kohli", "Shubman Gill", "Yashasvi Jaiswal", "Ruturaj Gaikwad", "Suryakumar Yadav",
        "Shreyas Iyer", "KL Rahul", "Sanju Samson", "Travis Head", "Abhishek Sharma", "Jos Buttler",
        "Rashid Khan", "Jasprit Bumrah", "Sunil Narine", "Andre Russell", "Hardik Pandya",
        "Rishabh Pant", "Nicholas Pooran", "Rohit Sharma"
    }
    return 1.18 if name in anchors else 1.0

def name_signal(name: str, role: str) -> Tuple[float, List[str]]:
    score = 50.0
    tags = []

    high_ceiling = {
        "Virat Kohli", "Phil Salt", "Liam Livingstone", "Jitesh Sharma", "Sanju Samson",
        "Yashasvi Jaiswal", "Riyan Parag", "Shubman Gill", "Jos Buttler", "Sai Sudharsan",
        "Rashid Khan", "Shreyas Iyer", "Marcus Stoinis", "Marco Jansen", "Arshdeep Singh",
        "Yuzvendra Chahal", "Ruturaj Gaikwad", "MS Dhoni", "Ravindra Jadeja", "Shivam Dube",
        "Suryakumar Yadav", "Rohit Sharma", "Hardik Pandya", "Jasprit Bumrah", "Tilak Varma",
        "Sunil Narine", "Andre Russell", "Rinku Singh", "Varun Chakaravarthy", "KL Rahul",
        "Nicholas Pooran", "Aiden Markram", "Mitchell Marsh", "Ravi Bishnoi", "Travis Head",
        "Abhishek Sharma", "Heinrich Klaasen", "Pat Cummins", "Mohammed Shami", "Axar Patel",
        "Kuldeep Yadav", "Rishabh Pant", "Ryan Rickelton", "David Miller"
    }

    reliable = {
        "Virat Kohli", "Shubman Gill", "Sai Sudharsan", "Shreyas Iyer", "Ruturaj Gaikwad",
        "Sanju Samson", "Suryakumar Yadav", "KL Rahul", "Travis Head", "Abhishek Sharma",
        "Rashid Khan", "Jasprit Bumrah", "Arshdeep Singh", "Kuldeep Yadav", "Varun Chakaravarthy",
        "Rishabh Pant", "Nicholas Pooran", "Rohit Sharma"
    }

    all_rounder_elite = {
        "Hardik Pandya", "Andre Russell", "Sunil Narine", "Ravindra Jadeja", "Marcus Stoinis",
        "Marco Jansen", "Axar Patel", "Washington Sundar", "Riyan Parag", "Rashid Khan",
        "Mitchell Marsh", "Aiden Markram", "Abhishek Sharma"
    }

    if name in high_ceiling:
        score += 18
        tags.append("high_ceiling")
    if name in reliable:
        score += 14
        tags.append("reliable")
    if name in all_rounder_elite:
        score += 15
        tags.append("dual_skill")

    score *= role_weight(role)
    score *= captain_bias(name)
    return round(score, 2), tags

def assign_scores(players: List[Player]) -> List[Player]:
    out = []
    for p in players:
        score, tags = name_signal(p.name, p.role)
        out.append(Player(p.name, p.team, p.role, score, tags))
    return sorted(out, key=lambda x: x.score, reverse=True)

def valid_team(combo: List[Player]) -> bool:
    roles = {"WK": 0, "BAT": 0, "AR": 0, "BOWL": 0}
    teams = {}
    for p in combo:
        roles[p.role] += 1
        teams[p.team] = teams.get(p.team, 0) + 1
    return (
        len(combo) == 11 and
        1 <= roles["WK"] <= 4 and
        3 <= roles["BAT"] <= 6 and
        1 <= roles["AR"] <= 4 and
        3 <= roles["BOWL"] <= 6 and
        len(teams) == 2 and
        max(teams.values()) <= 7
    )

def choose_c_vc(team: List[Player]) -> Tuple[str, str]:
    ordered = sorted(team, key=lambda p: (p.score, 1 if p.role == "AR" else 0), reverse=True)
    return ordered[0].name, ordered[1].name

def top_backups(pool: List[Player], selected: List[Player], count: int = 4) -> List[Dict]:
    selected_names = {p.name for p in selected}
    backups = [p for p in pool if p.name not in selected_names]
    backups = sorted(backups, key=lambda p: p.score, reverse=True)[:count]
    return [asdict(p) for p in backups]

def generate_teams(team1: str, team2: str, n: int, seed: int | None = None) -> Dict:
    if seed is not None:
        random.seed(seed)

    squads = {
        team1: fetch_team_squad(team1),
        team2: fetch_team_squad(team2),
    }

    if len(squads[team1]) < 11 or len(squads[team2]) < 11:
        raise ValueError(f"Not enough players found for {team1} or {team2}")

    pool = assign_scores(squads[team1] + squads[team2])
    by_role = {r: [p for p in pool if p.role == r] for r in ["WK", "BAT", "AR", "BOWL"]}

    teams = []
    seen = set()
    attempts = 0
    max_attempts = max(15000, n * 1000)

    while len(teams) < n and attempts < max_attempts:
        attempts += 1
        wk_n = random.choice([1, 1, 2])
        bat_n = random.choice([3, 4, 4, 5])
        ar_n = random.choice([1, 2, 2, 3])
        bowl_n = 11 - wk_n - bat_n - ar_n

        if not (3 <= bowl_n <= 5):
            continue
        if len(by_role["WK"]) < wk_n or len(by_role["BAT"]) < bat_n or len(by_role["AR"]) < ar_n or len(by_role["BOWL"]) < bowl_n:
            continue

        combo = []
        combo += random.sample(by_role["WK"], wk_n)
        combo += random.sample(by_role["BAT"], bat_n)
        combo += random.sample(by_role["AR"], ar_n)
        combo += random.sample(by_role["BOWL"], bowl_n)
        combo = list({(p.name, p.team): p for p in combo}.values())

        if len(combo) != 11 or not valid_team(combo):
            continue

        signature = tuple(sorted((p.name, p.team) for p in combo))
        if signature in seen:
            continue
        seen.add(signature)

        captain, vice_captain = choose_c_vc(combo)
        teams.append({
            "players": [asdict(p) for p in sorted(combo, key=lambda p: (p.role, -p.score, p.team, p.name))],
            "captain": captain,
            "vice_captain": vice_captain,
            "backups": top_backups(pool, combo, 4),
        })

    return {
        "match": f"{team1} vs {team2}",
        "requested_teams": n,
        "generated_teams": len(teams),
        "teams": teams,
        "squad_sizes": {team1: len(squads[team1]), team2: len(squads[team2])},
        "sources": LIVE_SQUAD_URLS.get(team1, []) + LIVE_SQUAD_URLS.get(team2, []),
        "note": "Uses live web fetch where possible and falls back to built-in current-season squads if scraping fails.",
    }

def main():
    parser = argparse.ArgumentParser(description="Dream11 team generator")
    parser.add_argument("match", help='Format: "MI vs LSG"')
    parser.add_argument("count", type=int, help="Number of teams to generate")
    parser.add_argument("--output", default="teams.json", help="Output JSON file")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed")
    args = parser.parse_args()

    m = re.match(r"\s*([A-Za-z]+)\s+vs\s+([A-Za-z]+)\s*$", args.match, flags=re.I)
    if not m:
        raise SystemExit("Match format must be like 'MI vs LSG'")

    team1 = normalize_team(m.group(1))
    team2 = normalize_team(m.group(2))

    result = generate_teams(team1, team2, args.count, args.seed)

    if result["generated_teams"] == 0:
        raise SystemExit(f"No valid teams generated for {team1} vs {team2}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Generated {result['generated_teams']} teams in {args.output}")

if __name__ == "__main__":
    main()
