import pandas as pd
from pathlib import Path

# Define paths for the master list and the audit report
MASTER_FILE = Path("data/processed/final_movie_list.csv")
AUDIT_FILE = Path("data/processed/audit_report.csv")

def main():
    print("Checking dataset balance for Machine Learning suitability...")
    
    # Load Master List
    df_master = pd.read_csv(MASTER_FILE)
    
    # Load the Audit Report to see which files passed our quality control checks
    if not AUDIT_FILE.exists():
        print("Error: Run the audit tool before checking balance.")
        return
        
    df_audit = pd.read_csv(AUDIT_FILE)
    
    # Filter the audit to only grab IDs of files marked strictly as "OK"
    valid_ids = df_audit[df_audit['status'] == "OK"]['tmdb_id'].astype(int)
    
    # Create a boolean mask indicating if a movie has a valid script
    df_master['has_script'] = df_master['id'].isin(valid_ids)
    
    # Filter the master list to create our final, usable dataset for modeling
    df_usable = df_master[df_master['has_script']].copy()
    
    print(f"\nTotal Movies Initially Targeted: {len(df_master)}")
    print(f"Movies with Valid Scripts: {len(df_usable)} ({len(df_usable)/len(df_master):.1%})")
    
    print("\n--- Bias & Class Imbalance Check (Usable Data Only) ---")
    
    # 1. Critical Success (Award Winners)
    # This is our target variable for the Critical Success classification model.
    # If this is below 10%, we will likely need to use SMOTE or class weighting during training.
    winners = df_usable['is_award_winner'].sum()
    print(f"Award Winners: {winners} ({winners/len(df_usable):.1%})")
    print("   (Note for ML: A target of >10% is preferred for stable training)")
    
    # 2. Commercial Success (Financial Data Available)
    # This checks how much data we have to calculate our ROI target variable.
    commercial = df_usable['is_commercial'].sum()
    print(f"Financial Data Available: {commercial} ({commercial/len(df_usable):.1%})")
    
    # 3. Popularity Bias
    # Ensures our dataset isn't overwhelmingly skewed toward obscure indie films
    popular = df_usable['is_popular'].sum()
    print(f"Popular (>50 votes): {popular} ({popular/len(df_usable):.1%})")
    
    # General rule of thumb: NLP models require a decent amount of samples to learn vocabularies effectively
    if len(df_usable) < 1000:
        print("\nCRITICAL WARNING: Dataset may be too small for robust NLP deep learning.")
        print("Consider using pre-trained embeddings (Word2Vec/BERT) or simple ML models (Random Forest).")
    else:
        print("\nDataset size is sufficient to proceed to the Exploratory Data Analysis (EDA) phase.")

if __name__ == "__main__":
    main()