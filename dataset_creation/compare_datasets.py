import ast
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# Input and Output Paths
TARGET_FILE = Path("data/processed/final_movie_list.csv")
COLLECTED_FILE = Path("data/processed/downloaded_movies.csv")
OUTPUT_DIR = Path("reports/figures")

def parse_genres(genre_str):
    # Safely converts a string representation of a list (like "['Action', 'Drama']") 
    # back into an actual Python list object.
    try:
        return ast.literal_eval(genre_str)
    except Exception:
        return []

def extract_year(date_str):
    # Extracts just the 4-digit year from a YYYY-MM-DD date string.
    # We use this to check for chronological bias in our scraping success.
    try:
        return int(str(date_str)[:4])
    except Exception:
        return None

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Loading datasets to generate comparison visualizations...")
    
    if not COLLECTED_FILE.exists():
        print("Error: Please run 'create_downloaded_manifest.py' first.")
        return
        
    df_target = pd.read_csv(TARGET_FILE)
    df_collected = pd.read_csv(COLLECTED_FILE)
    
    # Standardize the year columns for clean plotting
    df_target['year'] = df_target['release_date'].apply(extract_year)
    df_collected['year'] = df_collected['release_date'].apply(extract_year)
    
    # Filter out bad chronological outliers (like missing dates defaulting to 0 or future unreleased movies)
    df_target = df_target[(df_target['year'] > 1920) & (df_target['year'] < 2026)]
    df_collected = df_collected[(df_collected['year'] > 1920) & (df_collected['year'] < 2026)]

    # --- PLOT 1: Chronological Gap Analysis ---
    # Goal: See if our scraper struggled disproportionately with older or newer movies.
    print("Generating Chronological Gap Analysis...")
    plt.figure(figsize=(14, 7))
    
    # Plot the full target list as a light gray background outline
    sns.histplot(data=df_target, x='year', bins=range(1930, 2026), 
                 color='lightgray', label='Target List (Missing)', element="step")
    
    # Overlay the actually downloaded files in solid blue
    sns.histplot(data=df_collected, x='year', bins=range(1930, 2026), 
                 color='royalblue', label='Successfully Downloaded', element="step")
    
    plt.title("Data Collection Success Rate by Release Year")
    plt.xlabel("Release Year")
    plt.ylabel("Number of Movies")
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    save_path = OUTPUT_DIR / "comparison_years.png"
    plt.savefig(save_path)
    print(f"Saved: {save_path}")

    # --- PLOT 2: Genre Distribution ---
    # Goal: Check for genre bias (e.g., did we only successfully scrape 'Action' movies?)
    print("Generating Genre Distribution Bar Chart...")
    
    # Because genres are stored as lists in a single column, we use explode() 
    # to create a new row for every single genre tag a movie has.
    df_collected['genres_list'] = df_collected['genres'].apply(parse_genres)
    df_exploded = df_collected.explode('genres_list')
    
    genre_counts = df_exploded['genres_list'].value_counts().head(20)
    
    plt.figure(figsize=(12, 8))
    
    # We map 'y' to 'hue' and set legend=False to comply with modern Seaborn updates
    sns.barplot(x=genre_counts.values, y=genre_counts.index, hue=genre_counts.index, palette='viridis', legend=False)
    
    plt.title("Top 20 Genres in Final Downloaded Dataset")
    plt.xlabel("Total Count of Scripts")
    plt.ylabel("Genre")
    
    save_path = OUTPUT_DIR / "comparison_genres.png"
    plt.savefig(save_path)
    print(f"Saved: {save_path}")

    # --- PLOT 3: Overall Success Rate ---
    # Goal: A simple, high-level pie chart summarizing our data engineering effort.
    print("Generating Success Rate Pie Chart...")
    
    total = len(df_target)
    collected = len(df_collected)
    missing = total - collected
    
    plt.figure(figsize=(7, 7))
    plt.pie([collected, missing], labels=[f'Collected ({collected})', f'Missing ({missing})'], 
            autopct='%1.1f%%', colors=['#66b3ff', '#ff9999'], startangle=90)
    plt.title("Overall Transcript Collection Completion")
    
    save_path = OUTPUT_DIR / "completion_rate.png"
    plt.savefig(save_path)
    print(f"Saved: {save_path}")

if __name__ == "__main__":
    main()