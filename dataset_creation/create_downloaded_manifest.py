import pandas as pd
from pathlib import Path

# Define the paths for our master list and our raw subtitle files
MASTER_FILE = Path("data/processed/final_movie_list.csv")
SUBTITLES_DIR = Path("data/raw/subtitles")

# This will be our new "Source of Truth" dataset containing ONLY movies 
# where we successfully downloaded the transcript.
OUTPUT_FILE = Path("data/processed/downloaded_movies.csv")

def main():
    print("Inventorying successfully downloaded scripts...")

    # Step 1: Load the Master Target List
    if not MASTER_FILE.exists():
        print("Error: Master list not found. Please run the merge_and_filter script first.")
        return
        
    df_master = pd.read_csv(MASTER_FILE)

    # Step 2: Scan the Hard Drive
    # We only care about files that physically exist right now. 
    # This acts as a final safety net after the cleanup script.
    existing_files = list(SUBTITLES_DIR.glob("*.txt"))
    
    # Extract the TMDB IDs from the filenames (e.g., "12345.txt" -> 12345)
    downloaded_ids = {int(file_path.stem) for file_path in existing_files if file_path.stem.isdigit()}
    
    print(f"Found {len(downloaded_ids)} valid script files on disk.")

    # Step 3: Filter the Master List
    # We do an inner join conceptually: keep only the rows from our master list 
    # where the ID exists in our set of successfully downloaded files.
    df_downloaded = df_master[df_master['id'].isin(downloaded_ids)].copy()

    # Step 4: Save the manifest to a new CSV
    df_downloaded.to_csv(OUTPUT_FILE, index=False)
    
    print("-" * 40)
    print(f"Success! Created manifest: {OUTPUT_FILE}")
    print(f"Final usable dataset contains: {len(df_downloaded)} rows")
    print("-" * 40)

if __name__ == "__main__":
    main()