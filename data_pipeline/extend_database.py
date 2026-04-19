"""
Extend the movie database with new data from the Projekat folder.

Sources:
  - 25y_movie_subs/  (4,887 subtitle files, recent-era ~1998-2023)
  - golden_globes/   (580 subtitle files, Golden Globe winners/nominees)
  - downloaded_movies_25y.csv  (metadata for the 25y batch)
  - golden_globes_enriched.csv (metadata for the GG batch)
  - audit_report_25y.csv       (audit results for the 25y batch)

This script:
  1. Copies new subtitle files into data/raw/subtitles/
  2. Extends final_movie_list.csv with movies not already present
  3. Merges Golden Globe award titles into the awards master file
  4. Re-runs the subtitle audit on the full expanded directory
  5. Re-creates downloaded_movies.csv from the expanded data
  6. Validates consistency across all outputs
"""

import shutil
import time
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — source (Projekat) and destination (project)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROJEKAT_ROOT = PROJECT_ROOT.parent / "Projekat-20260419T044219Z-3-001" / "Projekat"

SRC_25Y_SUBS = PROJEKAT_ROOT / "data" / "raw" / "subtitles" / "25y_movie_subs"
SRC_GG_SUBS = PROJEKAT_ROOT / "data" / "raw" / "subtitles" / "golden_globes"
SRC_DM25 = PROJEKAT_ROOT / "data" / "processed" / "downloaded_movies_25y.csv"
SRC_GG_ENRICHED = PROJEKAT_ROOT / "data" / "processed" / "golden_globes_enriched.csv"
SRC_AUDIT_25Y = PROJEKAT_ROOT / "data" / "processed" / "audit_report_25y.csv"

DST_SUBS = PROJECT_ROOT / "data" / "raw" / "subtitles"
DST_FINAL = PROJECT_ROOT / "data" / "processed" / "final_movie_list.csv"
DST_FINAL_BACKUP = PROJECT_ROOT / "data" / "processed" / "final_movie_list_backup.csv"
DST_DOWNLOADED = PROJECT_ROOT / "data" / "processed" / "downloaded_movies.csv"
DST_AUDIT = PROJECT_ROOT / "data" / "processed" / "audit_report.csv"
DST_AWARDS_PARTIAL = PROJECT_ROOT / "data" / "processed" / "awards_master_partial.csv"

BAD_KEYWORDS = [
    "404 Not Found",
    "Page not found",
    "Internal Server Error",
    "Access Denied",
    "Cloudflare",
    "<html",
]


def copy_subtitle_files():
    """Copy subtitle .txt files from both Projekat sub-folders into the
    project's flat subtitles directory.  Existing files are overwritten."""

    DST_SUBS.mkdir(parents=True, exist_ok=True)

    before_count = len(list(DST_SUBS.glob("*.txt")))
    print(f"\n{'='*60}")
    print("STEP 1 — Copy subtitle files")
    print(f"{'='*60}")
    print(f"Destination: {DST_SUBS}")
    print(f"Files before copy: {before_count}")

    copied = 0
    for src_dir, label in [(SRC_25Y_SUBS, "25y_movie_subs"), (SRC_GG_SUBS, "golden_globes")]:
        if not src_dir.exists():
            print(f"  WARNING: {src_dir} not found, skipping.")
            continue
        files = list(src_dir.glob("*.txt"))
        total = len(files)
        print(f"  Copying {total:,} files from {label}...")
        t0 = time.time()
        for i, f in enumerate(files):
            shutil.copy2(f, DST_SUBS / f.name)
            copied += 1
            done = i + 1
            if done % 500 == 0 or done == total:
                elapsed = time.time() - t0
                pct = done / total * 100
                rate = done / elapsed if elapsed > 0 else 0
                eta = (total - done) / rate if rate > 0 else 0
                eta_str = f"{eta:.0f}s" if eta < 60 else f"{eta / 60:.1f}m"
                print(f"    {done:,}/{total:,}  ({pct:.1f}%)  ETA {eta_str}")
                sys.stdout.flush()

    after_count = len(list(DST_SUBS.glob("*.txt")))
    print(f"Copied {copied} files total.")
    print(f"Files after copy:  {after_count}  (net new: {after_count - before_count})")
    return before_count, after_count


def extend_final_movie_list():
    """Append movies from downloaded_movies_25y.csv and golden_globes_enriched.csv
    that are not already in final_movie_list.csv."""

    print(f"\n{'='*60}")
    print("STEP 2 — Extend final_movie_list.csv")
    print(f"{'='*60}")

    df_fml = pd.read_csv(DST_FINAL)
    before_count = len(df_fml)
    existing_ids = set(df_fml["id"])
    print(f"Current final_movie_list rows: {before_count}")

    # Back up the original
    df_fml.to_csv(DST_FINAL_BACKUP, index=False)
    print(f"Backup saved to {DST_FINAL_BACKUP.name}")

    new_rows = []

    # --- 25y batch (same schema) ---
    if SRC_DM25.exists():
        df_25y = pd.read_csv(SRC_DM25)
        df_25y_new = df_25y[~df_25y["id"].isin(existing_ids)]
        print(f"  25y batch: {len(df_25y)} total, {len(df_25y_new)} new")
        new_rows.append(df_25y_new)
        existing_ids.update(df_25y_new["id"])
    else:
        print(f"  WARNING: {SRC_DM25} not found.")

    # --- Golden Globes batch (partial schema — needs alignment) ---
    if SRC_GG_ENRICHED.exists():
        df_gg = pd.read_csv(SRC_GG_ENRICHED)
        df_gg_new = df_gg[~df_gg["tmdb_id"].isin(existing_ids)].copy()
        # De-duplicate by tmdb_id (same movie may appear for multiple awards)
        df_gg_new = df_gg_new.drop_duplicates(subset=["tmdb_id"])
        print(f"  GG batch:  {len(df_gg)} total, {len(df_gg_new)} new (unique)")

        if not df_gg_new.empty:
            aligned = pd.DataFrame()
            aligned["id"] = df_gg_new["tmdb_id"].values
            aligned["budget"] = pd.to_numeric(df_gg_new["budget"].values, errors="coerce").astype(float)
            aligned["revenue"] = pd.to_numeric(df_gg_new["revenue"].values, errors="coerce").astype(float)
            aligned["imdb_id"] = df_gg_new["imdb_id"].values
            aligned["runtime"] = np.nan
            aligned["release_date"] = np.nan
            aligned["genres"] = df_gg_new["genres"].values
            aligned["original_title"] = df_gg_new["Film"].values
            aligned["title"] = df_gg_new["Film"].values
            aligned["vote_count"] = 0
            aligned["is_commercial"] = (aligned["budget"] > 1000) | (aligned["revenue"] > 1000)
            aligned["is_award_winner"] = True
            aligned["is_popular"] = False
            new_rows.append(aligned)
            existing_ids.update(aligned["id"])
    else:
        print(f"  WARNING: {SRC_GG_ENRICHED} not found.")

    if new_rows:
        df_new = pd.concat(new_rows, ignore_index=True)
        df_extended = pd.concat([df_fml, df_new], ignore_index=True)
        df_extended.to_csv(DST_FINAL, index=False)
        after_count = len(df_extended)
        print(f"Appended {len(df_new)} new rows.")
        print(f"final_movie_list now has {after_count} rows (was {before_count}).")
    else:
        after_count = before_count
        print("No new rows to append.")

    return before_count, after_count


def update_awards():
    """Merge Golden Globe titles into the awards master file so
    is_award_winner flags stay accurate for future merge_and_filter runs."""

    print(f"\n{'='*60}")
    print("STEP 3 — Update awards data")
    print(f"{'='*60}")

    if not SRC_GG_ENRICHED.exists():
        print("  WARNING: golden_globes_enriched.csv not found. Skipping.")
        return

    df_gg = pd.read_csv(SRC_GG_ENRICHED)
    gg_awards = pd.DataFrame({
        "Film": df_gg["Film"],
        "Award_Body": "Golden Globe",
        "Category": df_gg["Award"],
    }).drop_duplicates()

    if DST_AWARDS_PARTIAL.exists():
        df_awards = pd.read_csv(DST_AWARDS_PARTIAL)
        before = len(df_awards)
        df_combined = pd.concat([df_awards, gg_awards], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=["Film", "Award_Body", "Category"])
        df_combined.to_csv(DST_AWARDS_PARTIAL, index=False)
        print(f"Awards master: {before} -> {len(df_combined)} rows  (+{len(df_combined)-before} new)")
    else:
        gg_awards.to_csv(DST_AWARDS_PARTIAL, index=False)
        print(f"Created awards_master_partial.csv with {len(gg_awards)} rows.")


def run_audit():
    """Re-run the subtitle file audit on the full (expanded) subtitles directory."""

    print(f"\n{'='*60}")
    print("STEP 4 — Re-run subtitle audit")
    print(f"{'='*60}")

    files = list(DST_SUBS.glob("*.txt"))
    if not files:
        print("No subtitle files found to audit.")
        return

    total = len(files)
    print(f"Scanning {total:,} files...")
    audit_data = []
    t0 = time.time()

    for i, fp in enumerate(files):
        try:
            size_kb = fp.stat().st_size / 1024
            status = "OK"
            if size_kb < 2:
                status = "TOO_SMALL"
            if status == "OK":
                with open(fp, "r", encoding="utf-8", errors="ignore") as fobj:
                    content = fobj.read(1000)
                    for kw in BAD_KEYWORDS:
                        if kw.lower() in content.lower():
                            status = f"BAD_CONTENT ({kw})"
                            break
            audit_data.append({"tmdb_id": fp.stem, "size_kb": round(size_kb, 2), "status": status})
        except Exception as e:
            audit_data.append({"tmdb_id": fp.stem, "size_kb": None, "status": "ERROR"})

        done = i + 1
        if done % 500 == 0 or done == total:
            elapsed = time.time() - t0
            pct = done / total * 100
            rate = done / elapsed if elapsed > 0 else 0
            eta = (total - done) / rate if rate > 0 else 0
            eta_str = f"{eta:.0f}s" if eta < 60 else f"{eta / 60:.1f}m"
            print(f"  {done:,}/{total:,}  ({pct:.1f}%)  ETA {eta_str}")
            sys.stdout.flush()

    df = pd.DataFrame(audit_data)
    df.to_csv(DST_AUDIT, index=False)

    print("\nAudit Summary:")
    print(df["status"].value_counts().to_string())
    print(f"\nSaved to {DST_AUDIT}  ({len(df)} rows)")


def recreate_downloaded_manifest():
    """Re-create downloaded_movies.csv by intersecting final_movie_list with
    subtitle files physically on disk."""

    print(f"\n{'='*60}")
    print("STEP 5 — Re-create downloaded_movies.csv")
    print(f"{'='*60}")

    df_master = pd.read_csv(DST_FINAL)
    existing_files = list(DST_SUBS.glob("*.txt"))
    downloaded_ids = {int(fp.stem) for fp in existing_files if fp.stem.isdigit()}

    print(f"Master list rows:       {len(df_master)}")
    print(f"Subtitle files on disk: {len(downloaded_ids)}")

    df_downloaded = df_master[df_master["id"].isin(downloaded_ids)].copy()
    df_downloaded.to_csv(DST_DOWNLOADED, index=False)

    print(f"downloaded_movies.csv:  {len(df_downloaded)} rows")
    return len(df_downloaded)


def validate(sub_before, sub_after, fml_before, fml_after, dm_count):
    """Print a final validation summary."""

    print(f"\n{'='*60}")
    print("STEP 6 — Validation")
    print(f"{'='*60}")

    df_fml = pd.read_csv(DST_FINAL)
    df_dm = pd.read_csv(DST_DOWNLOADED)
    df_audit = pd.read_csv(DST_AUDIT)
    sub_files = len(list(DST_SUBS.glob("*.txt")))

    ok_audit = len(df_audit[df_audit["status"] == "OK"])
    all_dm_in_fml = df_dm["id"].isin(df_fml["id"]).all()

    print(f"\n  {'Metric':<40} {'Before':>10} {'After':>10} {'Delta':>10}")
    print(f"  {'-'*70}")
    print(f"  {'Subtitle files on disk':<40} {sub_before:>10,} {sub_after:>10,} {sub_after-sub_before:>+10,}")
    print(f"  {'final_movie_list.csv rows':<40} {fml_before:>10,} {fml_after:>10,} {fml_after-fml_before:>+10,}")
    print(f"  {'downloaded_movies.csv rows':<40} {'7,423':>10} {len(df_dm):>10,} {len(df_dm)-7423:>+10,}")
    print(f"  {'audit_report.csv rows':<40} {'7,476':>10} {len(df_audit):>10,} {len(df_audit)-7476:>+10,}")
    print(f"  {'audit OK files':<40} {'':>10} {ok_audit:>10,}")
    print()

    checks = []

    checks.append(("All downloaded IDs exist in final_movie_list", all_dm_in_fml))
    checks.append(("Subtitle file count == audit rows", sub_files == len(df_audit)))
    checks.append(("No duplicate IDs in final_movie_list", df_fml["id"].is_unique))
    checks.append(("No duplicate IDs in downloaded_movies", df_dm["id"].is_unique))

    all_ok = True
    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_ok = False
        print(f"  [{status}] {label}")

    print()
    if all_ok:
        print("  All validation checks PASSED.")
    else:
        print("  WARNING: Some checks FAILED — review above.")

    return all_ok


def main():
    print("=" * 60)
    print("  EXTEND MOVIE DATABASE")
    print("=" * 60)

    sub_before, sub_after = copy_subtitle_files()
    fml_before, fml_after = extend_final_movie_list()
    update_awards()
    run_audit()
    dm_count = recreate_downloaded_manifest()
    validate(sub_before, sub_after, fml_before, fml_after, dm_count)

    print(f"\n{'='*60}")
    print("DONE. Remember to re-run 02_nlp_features.ipynb to regenerate")
    print("nlp_features.csv for the expanded subtitle set.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
