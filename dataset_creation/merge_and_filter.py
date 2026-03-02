import pandas as pd
from pathlib import Path

# Define our input sources. We need to combine raw TMDB data, our enriched financial data, 
# and the scraped list of award-winning movies.
RAW_FILE = Path("data/processed/tmdb_all_raw.csv")
ENRICHED_FILE = Path("data/processed/tmdb_enriched.csv")
AWARDS_FILE = Path("data/processed/awards_master_partly.csv")

# The final, clean dataset that will act as our "Source of Truth" moving forward
OUTPUT_FILE = Path("data/processed/final_movie_list.csv")

def normalize_title(title):
    # Helper function to standardize movie titles so we can match them across different datasets.
    # eg. "Spider-Man: No Way Home" becomes "spidermannowayhome".
    if not isinstance(title, str):
        return ""
    return title.lower().strip().replace(":", "").replace("-", "").replace(" ", "")

def main():
    print("Loading datasets for merging...")
    
    # 1. Load Data
    # We only need specific columns from the raw file to avoid clutter
    df_raw = pd.read_csv(RAW_FILE, usecols=['id', 'title', 'original_title', 'vote_count'])
    df_enriched = pd.read_csv(ENRICHED_FILE) 
    
    print("Cleaning IDs and removing corrupt rows...")
    
    # CRITICAL FIX: Because our previous script appended to the CSV in batches, 
    # sometimes extra header rows get written into the middle of the file. 
    # Forcing the 'id' column to numeric turns those rogue text headers into NaNs, 
    # which we can then safely drop.
    df_raw['id'] = pd.to_numeric(df_raw['id'], errors='coerce')
    df_enriched['id'] = pd.to_numeric(df_enriched['id'], errors='coerce')
    
    df_raw = df_raw.dropna(subset=['id'])
    df_enriched = df_enriched.dropna(subset=['id'])
    
    # Cast back to standard integers for clean merging
    df_raw['id'] = df_raw['id'].astype(int)
    df_enriched['id'] = df_enriched['id'].astype(int)
    
    print(f"Cleaned Raw Rows: {len(df_raw)}")
    print(f"Cleaned Enriched Rows: {len(df_enriched)}")

    # Load the awards dataset to see which movies have critical acclaim
    if AWARDS_FILE.exists():
        df_awards = pd.read_csv(AWARDS_FILE)
        # Create a fast-lookup set of normalized award titles
        award_titles = set(df_awards['Film'].apply(normalize_title))
        print(f"Loaded {len(award_titles)} unique award-winning titles.")
    else:
        print("Warning: Awards file not found. Skipping the awards cross-reference step.")
        award_titles = set()

    # 2. Merge Data
    print("Merging financial data with titles and vote counts...")
    df_merged = pd.merge(df_enriched, df_raw, on='id', how='left')
    
    original_count = len(df_merged)
    
    # If a movie has no IMDb ID, we won't be able to scrape its transcript later.
    # It's dead weight for our NLP goals, so we drop it here.
    df_merged = df_merged.dropna(subset=['imdb_id'])
    print(f"Dropped {original_count - len(df_merged)} rows missing IMDb IDs.")

    # 3. Apply The "Great Filter"
    print("Applying quality control filters...")
    
    # First, ensure financial columns are purely numeric
    df_merged['budget'] = pd.to_numeric(df_merged['budget'], errors='coerce').fillna(0)
    df_merged['revenue'] = pd.to_numeric(df_merged['revenue'], errors='coerce').fillna(0)
    
    # Filter A: Financial Data
    # We keep the movie if it has meaningful financial data (> $1,000) for our ROI prediction.
    mask_financial = (df_merged['budget'] > 1000) | (df_merged['revenue'] > 1000)
    
    # Filter B: Critical Success
    # We keep the movie if it was nominated for an award, regardless of budget/revenue.
    mask_critical = df_merged['title'].apply(normalize_title).isin(award_titles)
    
    # Filter C: Popularity
    # We keep the movie if at least 50 people voted on it. 
    # This weeds out obscure student films or junk entries in TMDB.
    mask_popular = df_merged['vote_count'] >= 50
    
    # Combine the masks. A movie only needs to pass ONE of these tests to be kept.
    final_df = df_merged[mask_financial | mask_critical | mask_popular].copy()
    
    # 4. Add Flags for Analysis
    # These boolean flags will make our Exploratory Data Analysis (EDA) much easier later.
    final_df['is_commercial'] = mask_financial
    final_df['is_award_winner'] = mask_critical
    final_df['is_popular'] = mask_popular
    
    # 5. Print a final summary report for our project documentation
    print("-" * 48)
    print("Filtering Report:")
    print(f"   Original Rows:     {original_count}")
    print("-" * 48)
    print(f"   Kept by Finance:   {sum(mask_financial)}")
    print(f"   Kept by Awards:    {sum(mask_critical)}")
    print(f"   Kept by Votes:     {sum(mask_popular)}")
    print("-" * 48)
    print(f"   FINAL DATASET:     {len(final_df)} unique movies")
    print(f"   (Rejected {original_count - len(final_df)} junk entries)")
    
    # Ensure output directory exists and save the final, pristine dataset
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Successfully saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()