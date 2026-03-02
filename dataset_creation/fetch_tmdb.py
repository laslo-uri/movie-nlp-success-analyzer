import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (specifically our TMDB API key)
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

# Project configurations based on our SIAP proposal
START_YEAR = 1950
END_YEAR = 2025
MOVIES_PER_YEAR = 500
OUTPUT_DIR = Path("data/raw/tmdb_metadata")

def fetch_movies_by_year(year):
    # TMDB returns 20 movies per page. We calculate how many pages we need to hit our target.
    movies = []
    page = 1
    max_pages = (MOVIES_PER_YEAR // 20) + 1
    
    print(f"Fetching movies for the year: {year}...")

    while page <= max_pages:
        try:
            url = f"{BASE_URL}/discover/movie"
            
            # Set up the query parameters.
            # We sort by revenue to prioritize financially relevant movies for our ROI analysis.
            # We also restrict to English to ensure the subtitles match our NLP tools later.
            params = {
                "api_key": API_KEY,
                "primary_release_year": year,
                "sort_by": "revenue.desc",  
                "include_adult": "false",
                "include_video": "false",
                "page": page,
                "with_original_language": "en" 
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                # Break the loop early if TMDB runs out of results for this specific year
                if not results:
                    break 
                
                movies.extend(results)
                
                # Stop paginating if we've reached our target number of movies
                if len(movies) >= MOVIES_PER_YEAR:
                    break
                
                page += 1
                
                # Small delay to respect TMDB API rate limits and avoid getting blocked
                time.sleep(0.2) 
            else:
                print(f"API Error {response.status_code}: {response.text}")
                time.sleep(1)
                
        except Exception as e:
            print(f"Network or parsing exception: {e}")
            time.sleep(1)

    # Return exactly the number requested, slicing the list in case we slightly overshot
    return movies[:MOVIES_PER_YEAR]


def main():
    # Safety check before starting the heavy lifting
    if not API_KEY:
        raise ValueError("TMDB_API_KEY is missing! Please check your .env file.")

    # Ensure our output directory exists before trying to save files
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_movies = []

    for year in range(START_YEAR, END_YEAR + 1):
        year_movies = fetch_movies_by_year(year)
        
        # Tagging each movie with the fetched year in case the official 'release_date' is messy or missing
        for movie in year_movies:
            movie['fetched_year'] = year
            
        all_movies.extend(year_movies)
        
        # Save a checkpoint CSV for each year. 
        # This prevents us from losing all data if the script crashes halfway through.
        df_year = pd.DataFrame(year_movies)
        file_path = OUTPUT_DIR / f"movies_{year}.csv"
        df_year.to_csv(file_path, index=False)
        
        print(f"Saved {len(year_movies)} movies for {year} to {file_path}")

    # Once the loop is done, combine everything into one massive dataset for the next pipeline step
    print("-" * 40)
    print("Consolidating all yearly data into a single CSV...")
    
    final_df = pd.DataFrame(all_movies)
    final_path = Path("data/processed/tmdb_all_raw.csv")
    
    # Make sure the processed folder exists
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(final_path, index=False)
    
    print(f"Done! Total movies fetched: {len(final_df)}")
    print(f"Final dataset saved to: {final_path}")


if __name__ == "__main__":
    main()