import re
import csv
import time
import random
import argparse
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION & PATHS
# ==========================================
INPUT_FILE = Path("data/processed/final_movie_list.csv")
OUTPUT_DIR = Path("data/raw/subtitles")
LOG_FILE = Path("data/processed/download_log.csv")
BASE_URL = "https://subslikescript.com"

# A list of real browser User-Agents. 
# We randomly rotate through these so the target server thinks our script 
# is just a bunch of regular people browsing from different computers.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5.2 Safari/605.1.15"
]

def get_random_header():
    # Constructs a fake HTTP header for our requests
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/"
    }

def similarity(string_a, string_b):
    # Compares two strings and returns a similarity score from 0.0 to 1.0.
    # We need this because movie titles in our database might slightly differ 
    # from how they are written on the transcript website.
    return SequenceMatcher(None, string_a.lower(), string_b.lower()).ratio()

def scrape_script(movie_title, movie_year):
    # This function handles the actual search, match, and download process for a single movie
    search_url = f"{BASE_URL}/search"
    params = {"q": movie_title}
    
    try:
        # STEP 1: Search the website
        response = requests.get(search_url, params=params, headers=get_random_header())
        
        # HTTP 429 means we are making too many requests and the server is timing us out
        if response.status_code == 429:
            return "RATE_LIMIT"
        if response.status_code != 200:
            return "CONNECTION_ERROR"
        
        # Parse the HTML to find the search results list
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find("ul", class_="scripts-list")
        if not results:
            return "NOT_FOUND"
        
        # STEP 2: Find the best match from the search results
        best_link = None
        highest_score = 0.0
        
        for item in results.find_all("a"):
            text = item.get_text() # This usually looks like "The Godfather (1972)"
            link = item['href']
            
            # Extract the year from the parenthesis using a Regular Expression
            match = re.search(r'\((\d{4})\)', text)
            result_year = int(match.group(1)) if match else 0
            
            # Strip the year out so we can compare just the clean titles
            clean_result_name = re.sub(r'\(\d{4}\)', '', text).strip()
            
            sim_score = similarity(movie_title, clean_result_name)
            year_diff = abs(int(movie_year) - result_year)
            
            # Our custom matching logic: 
            # The release year must be within 3 years (to account for international release delays),
            # and the title similarity must be at least 65%.
            if year_diff <= 3 and sim_score > 0.65:
                if sim_score > highest_score:
                    highest_score = sim_score
                    best_link = link
        
        if not best_link:
            return "NO_MATCH"
            
        # STEP 3: Download the actual transcript
        script_url = f"{BASE_URL}{best_link}"
        
        # Wait a random amount of time before fetching the page so we look human
        time.sleep(random.uniform(1.0, 2.5)) 
        
        script_resp = requests.get(script_url, headers=get_random_header())
        if script_resp.status_code == 429:
            return "RATE_LIMIT"
            
        script_soup = BeautifulSoup(script_resp.text, "html.parser")
        script_div = script_soup.find("div", class_="full-script")
        
        if not script_div:
            return "NO_TEXT"
            
        return script_div.get_text(separator="\n", strip=True)

    except Exception as e:
        print(f"Encountered an error while scraping: {e}")
        return "ERROR"

def initialize_log():
    # Creates an empty CSV to track our progress if one doesn't exist yet
    if not LOG_FILE.exists():
        with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['tmdb_id', 'status', 'timestamp'])

def log_attempt(tmdb_id, status):
    # Appends the result of a download attempt to our tracking log
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([tmdb_id, status, time.strftime("%Y-%m-%d %H:%M:%S")])

def main():
    # Set up command line arguments. This allows us to manually force the script 
    # to start from a specific row if we need to.
    parser = argparse.ArgumentParser(description="Scrape movie transcripts.")
    parser.add_argument("--start_index", type=int, default=0, help="Row index to start from (ignoring log history).")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    initialize_log()
    
    # Load our filtered "Source of Truth" dataset
    df = pd.read_csv(INPUT_FILE)
    print(f"Master List loaded: {len(df)} movies.")
    
    # Figure out which movies we actually need to download
    if args.start_index > 0:
        print(f"Manual Override: Starting strictly from row {args.start_index}...")
        pending_df = df.iloc[args.start_index:]
    else:
        print("Smart Mode: Resuming based on logs and files already on disk...")
        # Check what files physically exist in the folder
        existing_files = list(OUTPUT_DIR.glob("*.txt"))
        physical_ids = {int(f.stem) for f in existing_files if f.stem.isdigit()}
        
        # Check what we already attempted in previous runs
        logged_ids = set()
        if LOG_FILE.exists():
            try:
                log_df = pd.read_csv(LOG_FILE)
                logged_ids = set(log_df['tmdb_id'].unique())
            except Exception:
                pass # If the log is corrupt, we just rely on physical files
        
        all_done = physical_ids.union(logged_ids)
        
        # Filter the dataframe to only include movies we haven't touched yet
        pending_df = df[~df['id'].isin(all_done)]
    
    total_pending = len(pending_df)
    print(f"Processing {total_pending:,} remaining movies...")
    
    success_count = 0
    fail_count = 0
    t_start = time.time()
    
    for seq, (index, row) in enumerate(pending_df.iterrows(), 1):
        title = row['title']
        tmdb_id = row['id']
        
        # Safely extract the release year
        try:
            year = int(str(row['release_date'])[:4])
        except Exception:
            year = 0

        pct = seq / total_pending * 100
        print(f"[{seq}/{total_pending} ({pct:.1f}%)] {title} ({year})...", end=" ")
        
        # Final safety check to avoid overwriting files
        if (OUTPUT_DIR / f"{tmdb_id}.txt").exists():
            print("Already on disk. Skipping.")
            continue

        result = scrape_script(title, year)
        status = ""
        
        if result == "RATE_LIMIT":
            print("Rate limit hit (HTTP 429). Sleeping for 60 seconds...")
            # We pause script execution to let our IP "cool down"
            time.sleep(60)
            status = "RATE_LIMIT"
        elif result in ["CONNECTION_ERROR", "NOT_FOUND", "NO_MATCH", "NO_TEXT", "ERROR"]:
            print(f"Failed: {result}")
            status = result
            fail_count += 1
        else:
            save_path = OUTPUT_DIR / f"{tmdb_id}.txt"
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(result)
            print("Successfully saved.")
            status = "DOWNLOADED"
            success_count += 1
            
        log_attempt(tmdb_id, status)
        
        # Random sleep between requests is CRITICAL to avoid being permanently blocked
        time.sleep(random.uniform(2.0, 5.0))
        
        # Print a mini status report every 10 attempts
        attempts = success_count + fail_count
        if attempts > 0 and attempts % 10 == 0:
            elapsed = time.time() - t_start
            rate = attempts / elapsed if elapsed > 0 else 0
            remaining = total_pending - seq
            eta = remaining / rate if rate > 0 else 0
            if eta < 60:
                eta_str = f"{eta:.0f}s"
            elif eta < 3600:
                eta_str = f"{eta / 60:.1f}m"
            else:
                eta_str = f"{eta / 3600:.1f}h"
            print(f"--- Stats: {success_count} OK | {fail_count} Failed | "
                  f"{rate:.2f} movies/s | ETA {eta_str} ---")

if __name__ == "__main__":
    main()