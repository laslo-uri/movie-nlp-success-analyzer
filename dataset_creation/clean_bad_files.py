import pandas as pd
from pathlib import Path

# Define the locations of our audit report and the actual subtitle files
AUDIT_FILE = Path("data/processed/audit_report.csv")
SUBTITLES_DIR = Path("data/raw/subtitles")

def main():
    print("Starting cleanup process...")

    # Step 1: Make sure the audit report actually exists before we try to read it
    if not AUDIT_FILE.exists():
        print(f"Audit report not found at {AUDIT_FILE}")
        print("Please run the audit script first.")
        return

    # Load the report into a pandas DataFrame
    df = pd.read_csv(AUDIT_FILE)

    # Step 2: Identify the garbage files
    # We filter the dataset to only include rows where the status is something other than "OK"
    bad_files = df[df['status'] != "OK"]

    if bad_files.empty:
        print("No bad files found in the report. Your data is clean!")
        return

    print(f"WARNING: Found {len(bad_files)} files marked as bad.")
    print("These include files that are too small or contain web server errors.")
    
    # Step 3: Safety Check
    # Deleting files is permanent, so we force the user to type exactly "DELETE" to proceed.
    # This prevents accidental data loss if someone runs the script by mistake.
    user_input = input(f"Are you sure you want to PERMANENTLY DELETE these {len(bad_files)} files? (Type 'DELETE' to confirm): ")

    if user_input.strip() != "DELETE":
        print("Aborted. No files were touched.")
        return

    # Step 4: Execute Deletion
    deleted_count = 0
    missing_count = 0
    error_count = 0

    print("\nDeleting files...")
    
    # Go through each bad file one by one
    for index, row in bad_files.iterrows():
        tmdb_id = row['tmdb_id']
        file_path = SUBTITLES_DIR / f"{tmdb_id}.txt"
        
        try:
            # We check if the file still exists physically on the hard drive before deleting
            if file_path.exists():
                file_path.unlink() # This command actually removes the file from the disk
                print(f"Deleted: {file_path.name} ({row['status']})")
                deleted_count += 1
            else:
                missing_count += 1
        except Exception as e:
            print(f"Error deleting {file_path.name}: {e}")
            error_count += 1

    # Step 5: Final Summary
    # Print a quick report so the user knows exactly what just happened
    print("-" * 30)
    print("Cleanup Complete.")
    print(f"Deleted: {deleted_count}")
    print(f"Missing: {missing_count} (Already gone)")
    print(f"Errors:  {error_count}")
    print("-" * 30)

if __name__ == "__main__":
    main()