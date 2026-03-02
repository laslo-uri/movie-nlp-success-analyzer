import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load our hidden API key from the .env file
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

# Define where we are reading from and saving to.
# We use the raw list of movies from the first script as our starting point.
INPUT_FILE = Path("data/processed/tmdb_all_raw.csv")
OUTPUT_FILE = Path("data/processed/tmdb_enriched.csv")

def get_movie_details(movie_id):
    # This function asks the TMDB database for extra details about a single movie.
    # We specifically need budget and revenue to calculate the ROI (Return on Investment) for our labels.
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": API_KEY}
    
    try:
        response = requests.get(url, params=params)
        
        # Status code 200 means the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Pull out only the exact pieces of information we need for our analysis.
            # The imdb_id is especially important because we need it to find subtitles later.
            return {
                "id": movie_id,
                "budget": data.get("budget", 0),
                "revenue": data.get("revenue", 0),
                "imdb_id": data.get("imdb_id"), 
                "runtime": data.get("runtime"),
                "release_date": data.get("release_date"),
                # The API gives us a list of genre dictionaries, but we just want a simple list of genre names.
                "genres": [genre['name'] for genre in data.get('genres', [])] 
            }
            
        # Status code 429 means we are asking for data too fast.
        elif response.status_code == 429:
            print("We asked for data too fast. Waiting 5 seconds before trying again...")
            time.sleep(5)
            # Try fetching this exact same movie again after the wait
            return get_movie_details(movie_id)
            
    except Exception as e:
        print(f"Something went wrong while fetching movie ID {movie_id}: {e}")
    
    # If the request completely fails, return nothing so the main loop can just skip it
    return None

def main():
    # Make sure we actually have the raw data before trying to enrich it
    if not INPUT_FILE.exists():
        print(f"Could not find {INPUT_FILE}. Make sure to run the fetch_tmdb script first.")
        return

    print(f"Loading our list of movies from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    
    # This block handles crash recovery. 
    # If the script stopped halfway through yesterday, we don't want to start all over.
    if OUTPUT_FILE.exists():
        df_existing = pd.read_csv(OUTPUT_FILE)
        # Make a quick lookup list of movie IDs we have already processed
        processed_ids = set(df_existing['id'])
        print(f"Found existing data. We already enriched {len(processed_ids)} movies.")
    else:
        # If this is our first time running the script, start completely fresh
        processed_ids = set()

    # Filter our main list to only include movies we haven't fetched yet.
    movies_to_process = df[~df['id'].isin(processed_ids)]['id'].unique()
    total_movies = len(movies_to_process)
    print(f"We have {total_movies} movies left to process...")

    batch_data = []
    
    for i, movie_id in enumerate(movies_to_process):
        details = get_movie_details(movie_id)
        
        if details:
            batch_data.append(details)
        
        # We save our progress in chunks of 100 movies.
        # This way, if our internet drops, we don't need to restart the process.
        # We also trigger a save if we are on the very last movie in the list.
        if (i + 1) % 100 == 0 or (i + 1) == total_movies:
            new_df = pd.DataFrame(batch_data)
            
            # If our save file already exists, we just add the new rows to the bottom (append mode).
            # If it doesn't exist yet, we create it and write the column names at the top.
            if OUTPUT_FILE.exists():
                new_df.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
            else:
                new_df.to_csv(OUTPUT_FILE, mode='w', header=True, index=False)
            
            print(f"Saved a chunk of data. Progress so far: {i + 1} out of {total_movies}")
            
            # Empty the list so it's ready for the next chunk of 100 movies
            batch_data = [] 
            
            # Add a tiny pause so TMDB doesn't block us for making too many requests
            time.sleep(0.2) 

    print("Finished grabbing all extra movie details!")

if __name__ == "__main__":
    main()