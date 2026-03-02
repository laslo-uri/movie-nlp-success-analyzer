import re
import time
import urllib.parse
import pandas as pd
import requests
from io import StringIO
from pathlib import Path

# Define where we want to save our final scraped data
OUTPUT_DIR = Path("data/raw/awards")
OUTPUT_FILE = Path("data/processed/awards_master.csv")

# We use the official Wikipedia API instead of just scraping the raw webpage
# This is generally more reliable and gives us cleaner HTML
API_ENDPOINT = "https://en.wikipedia.org/w/api.php"

# Dictionary containing the "Big 5" major film awards we want to track
# We map our custom category names to the specific Wikipedia article URLs
AWARDS_CONFIG = {
    "Oscar": {
        "Best Picture": "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Picture",
        "Original Screenplay": "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Original_Screenplay",
        "Adapted Screenplay": "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Adapted_Screenplay",
        "Best Actor": "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actor",
        "Best Actress": "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actress",
        "Supporting Actor": "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Supporting_Actor",
        "Supporting Actress": "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Supporting_Actress"
    },
    "BAFTA": {
        "Best Film": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Film",
        "Original Screenplay": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Original_Screenplay",
        "Adapted Screenplay": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Adapted_Screenplay",
        "Best Actor": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Actor_in_a_Leading_Role",
        "Best Actress": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Actress_in_a_Leading_Role"
    },
    "Golden Globe": {
        "Best Motion Picture - Drama": "https://en.wikipedia.org/wiki/Golden_Globe_Award_for_Best_Motion_Picture_%E2%80%93_Drama",
        "Best Motion Picture - Musical/Comedy": "https://en.wikipedia.org/wiki/Golden_Globe_Award_for_Best_Motion_Picture_%E2%80%93_Musical_or_Comedy",
        "Screenplay": "https://en.wikipedia.org/wiki/Golden_Globe_Award_for_Best_Screenplay",
        "Best Actor - Drama": "https://en.wikipedia.org/wiki/Golden_Globe_Award_for_Best_Actor_in_a_Motion_Picture_%E2%80%93_Drama",
        "Best Actress - Drama": "https://en.wikipedia.org/wiki/Golden_Globe_Award_for_Best_Actress_in_a_Motion_Picture_%E2%80%93_Drama"
    },
    "WGA": {
        "Original Screenplay": "https://en.wikipedia.org/wiki/Writers_Guild_of_America_Award_for_Best_Original_Screenplay",
        "Adapted Screenplay": "https://en.wikipedia.org/wiki/Writers_Guild_of_America_Award_for_Best_Adapted_Screenplay"
    },
    "SAG": {
        "Ensemble Cast": "https://en.wikipedia.org/wiki/Screen_Actors_Guild_Award_for_Outstanding_Performance_by_a_Cast_in_a_Motion_Picture",
        "Male Actor": "https://en.wikipedia.org/wiki/Screen_Actors_Guild_Award_for_Outstanding_Performance_by_a_Male_Actor_in_a_Leading_Role",
        "Female Actor": "https://en.wikipedia.org/wiki/Screen_Actors_Guild_Award_for_Outstanding_Performance_by_a_Female_Actor_in_a_Leading_Role"
    }
}

# Standard headers to tell Wikipedia who is making the requests 
# It's good practice for scraping so they don't block us
HEADERS = {
    "User-Agent": "SIAP_Student_Project/1.0 (Student Research; contact@example.com) requests/2.0"
}

def get_page_title_from_url(url):
    # Extracts the specific article title from the URL path
    # Crucially, it unquotes special characters (like turning %E2%80%93 back into a dash) 
    # so the API can actually find the page
    path = urllib.parse.urlparse(url).path
    raw_title = path.split("/")[-1]
    return urllib.parse.unquote(raw_title)

def clean_film_title(title):
    # Cleans up the text we pull from the tables
    if not isinstance(title, str):
        return ""
        
    # Wikipedia tables often have citation footnotes like "[1]" or "[a]"
    # This regex removes anything inside square brackets
    title = re.sub(r'\[.*?\]', '', title)
    title = title.replace("\n", " ")
    
    return title.strip()

def fetch_via_api(title):
    # Uses the Wikipedia API to grab the parsed HTML of the page
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text",
        "redirects": 1
    }
    
    try:
        # A short pause to be polite to Wikipedia's servers
        time.sleep(1) 
        response = requests.get(API_ENDPOINT, params=params, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"API Error: {data['error'].get('info')}")
                return None
            
            # The actual HTML body content is deeply nested in the JSON response
            return data['parse']['text']['*']
            
        elif response.status_code == 429:
            print("Hitting the API rate limit. Waiting 5 seconds before retrying...")
            time.sleep(5)
            return fetch_via_api(title)
            
    except Exception as e:
        print(f"Network exception while fetching {title}: {e}")
        
    return None

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_awards = []

    print("Starting award harvest via Wikipedia API...")

    for award_body, categories in AWARDS_CONFIG.items():
        print(f"\n--- Processing {award_body} ---")
        
        for category, url in categories.items():
            page_title = get_page_title_from_url(url)
            print(f"Fetching: {category}...")
            
            html_content = fetch_via_api(page_title)
            
            if html_content:
                try:
                    # pd.read_html is a lifesaver. It automatically finds all <table> 
                    # tags in the HTML and converts them into a list of DataFrames.
                    tables = pd.read_html(StringIO(html_content))
                    
                    found_data = False
                    for table in tables:
                        # Normalize all column names to lowercase so we can search them easily
                        cols_lower = [str(c).lower() for c in table.columns]
                        
                        # Hunt for the column that contains the movie names. 
                        # Wikipedia formatting is wildly inconsistent, so we check a few variations.
                        target_col = None
                        if "film" in cols_lower:
                            target_col = table.columns[cols_lower.index("film")]
                        elif "motion picture" in cols_lower:
                            target_col = table.columns[cols_lower.index("motion picture")]
                        elif "title" in cols_lower:
                            target_col = table.columns[cols_lower.index("title")]
                        
                        if target_col:
                            df = table.copy()
                            
                            # Standardize the column names for our master dataset
                            df = df.rename(columns={target_col: 'Film'})
                            df['Film'] = df['Film'].apply(clean_film_title)
                            df['Award_Body'] = award_body
                            df['Category'] = category
                            
                            # If the first column isn't 'Film', it's usually the 'Year' column.
                            # We make a rough heuristic guess here to grab it.
                            if len(df.columns) > 0 and df.columns[0] != 'Film':
                                 df = df.rename(columns={df.columns[0]: 'Year_Raw'})

                            # Keep only the columns we actually care about
                            clean_df = df[['Film', 'Award_Body', 'Category']].copy()
                            clean_df = clean_df.dropna(subset=['Film'])
                            
                            # Ensure the film name is longer than 1 character to weed out garbage rows
                            clean_df = clean_df[clean_df['Film'].astype(str).str.len() > 1]
                            
                            all_awards.append(clean_df)
                            found_data = True
                    
                    if not found_data:
                        print(f"  -> Could not find a 'Film' column in any table for {category}")

                except Exception as e:
                    # Sometimes pandas read_html chokes on bad formatting (like strings in integer columns).
                    # We catch it here so it skips the bad table instead of crashing the whole script.
                    print(f"  -> Parsing Error (skipping bad table): {e}")

    # Combine everything into one big master DataFrame
    if all_awards:
        print("\nConsolidating all harvested data...")
        master_df = pd.concat(all_awards)
        
        # Drop duplicates in case multiple tables contained the same movie
        master_df = master_df.drop_duplicates(subset=['Film', 'Award_Body', 'Category'])
        
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        master_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Success! Harvested {len(master_df)} unique award records.")
        print(f"Saved to: {OUTPUT_FILE}")
    else:
        print("Failed to collect any award data. Check the API or internet connection.")

if __name__ == "__main__":
    main()