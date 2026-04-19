import time
import sys
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# Define paths to our subtitle folder and where we want to save the final report
SUBTITLES_DIR = Path("data/raw/subtitles")
OUTPUT_REPORT = Path("data/processed/audit_report.csv")

# These are common error messages that web servers return. 
# If a transcript file contains these, it means our scraper failed to get the actual text
# and saved an error page instead.
BAD_KEYWORDS = [
    "404 Not Found",
    "Page not found",
    "Internal Server Error",
    "Access Denied",
    "Cloudflare",
    "<html"  # This catches cases where we accidentally saved raw webpage code
]

def main():
    print("Starting the file audit process...")
    
    # Grab a list of all text files in our subtitles directory
    files = list(SUBTITLES_DIR.glob("*.txt"))
    if not files:
        print("No files found to audit.")
        return

    audit_data = []
    total = len(files)
    
    print(f"Scanning {total:,} files...")
    t_start = time.time()
    
    for i, file_path in enumerate(files):
        try:
            # Calculate file size in Kilobytes
            size_kb = file_path.stat().st_size / 1024
            status = "OK"
            
            # Check 1: File Size
            # A real movie script is thousands of words long. 
            # If the file is less than 2KB, it's almost certainly broken or empty.
            if size_kb < 2: 
                status = "TOO_SMALL"
            
            # Check 2: File Content
            # We only perform this check if the file size seems normal.
            if status == "OK":
                # Open the file and read just the first 1000 characters to save memory
                # If there is a server error, it will almost always be at the very top of the file
                with open(file_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                    content = file_obj.read(1000) 
                    
                    # Check if any of our known error messages appear in the text
                    for keyword in BAD_KEYWORDS:
                        if keyword.lower() in content.lower():
                            status = f"BAD_CONTENT ({keyword})"
                            break
                            
            # Record the findings for this specific file
            audit_data.append({
                "tmdb_id": file_path.stem,
                "size_kb": round(size_kb, 2),
                "status": status
            })
            
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")
            audit_data.append({
                "tmdb_id": file_path.stem,
                "size_kb": None,
                "status": "ERROR"
            })

        done = i + 1
        if done % 500 == 0 or done == total:
            elapsed = time.time() - t_start
            pct = done / total * 100
            rate = done / elapsed if elapsed > 0 else 0
            eta = (total - done) / rate if rate > 0 else 0
            eta_str = f"{eta:.0f}s" if eta < 60 else f"{eta/60:.1f}m"
            print(f"  {done:,}/{total:,}  ({pct:.1f}%)  ETA {eta_str}")
            sys.stdout.flush()

    # Convert our list of dictionaries into a pandas DataFrame for easy analysis
    df = pd.DataFrame(audit_data)
    
    # Print a quick summary to the console so we can see how many files are broken
    print("\nAudit Summary:")
    print(df['status'].value_counts())
    
    # Create a visual histogram of the file sizes.
    # This helps us see the general length of our valid scripts (usually 20KB to 100KB).
    print("\nGenerating a size distribution histogram...")
    plt.figure(figsize=(10, 5))
    
    # We only plot the 'OK' files so the broken ones don't mess up our graph
    df[df['status'] == "OK"]['size_kb'].hist(bins=50, color='skyblue', edgecolor='black')
    plt.title("Distribution of Script File Sizes (KB)")
    plt.xlabel("Size (KB)")
    plt.ylabel("Count")
    
    # Save the graph as an image for our final project report
    plt.savefig("data/processed/size_distribution.png")
    print("Histogram saved to data/processed/size_distribution.png")
    
    # Save the full detailed report to a CSV file
    df.to_csv(OUTPUT_REPORT, index=False)
    print(f"Detailed report saved to {OUTPUT_REPORT}")
    
    # Alert the user if any bad files were detected
    bad_files = df[df['status'] != "OK"]
    if not bad_files.empty:
        print(f"\nWARNING: Found {len(bad_files)} bad files.")
        print("Run the cleanup script to delete them.")

if __name__ == "__main__":
    main()