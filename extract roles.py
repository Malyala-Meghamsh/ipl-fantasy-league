from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time

TEAM_URLS = [
    "https://www.iplt20.com/teams/kolkata-knight-riders",
    "https://www.iplt20.com/teams/gujarat-titans",
    "https://www.iplt20.com/teams/delhi-capitals",
    "https://www.iplt20.com/teams/chennai-super-kings",
    "https://www.iplt20.com/teams/sunrisers-hyderabad",
    "https://www.iplt20.com/teams/royal-challengers-bengaluru",
    "https://www.iplt20.com/teams/rajasthan-royals",
    "https://www.iplt20.com/teams/punjab-kings",
    "https://www.iplt20.com/teams/mumbai-indians",
    "https://www.iplt20.com/teams/lucknow-super-giants",
]

ROLE_MAP = {
    "batter": "Batsman",
    "wk-batter": "WK",
    "wicketkeeper batter": "WK",
    "all-rounder": "AR",
    "all rounder": "AR",
    "bowler": "Bowler",
}


def normalize_role(raw_role):
    key = raw_role.strip().lower()
    return ROLE_MAP.get(key, raw_role.strip())


def extract_roles():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)

    all_players = []

    try:
        for url in TEAM_URLS:
            team_slug = url.split("/teams/")[-1]
            print(f"Scraping: {team_slug} ...")
            driver.get(url)

            # Wait for page to fully load
            time.sleep(5)

            # Scroll down to trigger lazy-loaded content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            # Try multiple selectors
            player_cards = driver.find_elements(By.CSS_SELECTOR, "li.ih-pcard1")

            if not player_cards:
                # Fallback: try finding via data-player_name attribute
                player_cards = driver.find_elements(By.CSS_SELECTOR, "a[data-player_name]")
                print(f"  Found {len(player_cards)} players (via fallback selector)")
                for link in player_cards:
                    try:
                        player_name = link.get_attribute("data-player_name")
                        # Role span is inside the link
                        role_span = link.find_element(
                            By.CSS_SELECTOR, "span.d-block.w-100.text-center"
                        )
                        raw_role = role_span.text
                        role = normalize_role(raw_role)
                        # Check for foreign player icon
                        foreign_icons = link.find_elements(
                            By.CSS_SELECTOR, "img[src*='teams-foreign-player-icon']"
                        )
                        is_foreign = "Yes" if foreign_icons else "No"
                        all_players.append({"Player": player_name, "Role": role, "Foreign": is_foreign})
                    except Exception as e:
                        print(f"  Error: {e}")
            else:
                print(f"  Found {len(player_cards)} players")
                for card in player_cards:
                    try:
                        link = card.find_element(By.CSS_SELECTOR, "a[data-player_name]")
                        player_name = link.get_attribute("data-player_name")
                        role_span = card.find_element(
                            By.CSS_SELECTOR, "div.ih-p-img > span.d-block"
                        )
                        raw_role = role_span.text
                        role = normalize_role(raw_role)
                        # Check for foreign player icon
                        foreign_icons = card.find_elements(
                            By.CSS_SELECTOR, "img[src*='teams-foreign-player-icon']"
                        )
                        is_foreign = "Yes" if foreign_icons else "No"
                        all_players.append({"Player": player_name, "Role": role, "Foreign": is_foreign})
                    except Exception as e:
                        print(f"  Error: {e}")

    finally:
        driver.quit()

    # Save to CSV
    output_file = "player_roles.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Player", "Role", "Foreign"])
        writer.writeheader()
        writer.writerows(all_players)

    print(f"\nSaved {len(all_players)} players to {output_file}")
    for p in all_players:
        foreign_tag = " [OVERSEAS]" if p["Foreign"] == "Yes" else ""
        print(f"  {p['Player']:30s} | {p['Role']:10s}{foreign_tag}")


if __name__ == "__main__":
    extract_roles()
