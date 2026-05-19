#!/usr/bin/env python3
"""
Main orchestrator for RFEA ranking scraper.
Coordinates download -> import -> scoring -> export -> cleanup.
"""

import sys
import shutil
from pathlib import Path
import config
import scraper
import importer
import scorer


def cleanup_excel_files():
    """Delete downloaded Excel files after processing."""
    excel_dir = config.EXCEL_DOWNLOAD_DIR / "2026"
    if excel_dir.exists():
        try:
            shutil.rmtree(excel_dir)
            print("✅ Cleaned up Excel files")
            return True
        except Exception as e:
            print(f"⚠️  Could not clean up Excel files: {str(e)}")
            return False
    return True


def main():
    """Run complete pipeline: download -> import -> score -> compile -> cleanup."""
    print("\n" + "="*60)
    print("🏃 RFEA RANKING SCRAPER - FULL PIPELINE")
    print("="*60 + "\n")

    try:
        # Step 1: Download current year rankings
        print("STEP 1: Downloading from RFEA...\n")
        downloaded = scraper.download_year(2026, headless=True)
        if not downloaded:
            print("⚠️  No files downloaded. Continuing with existing data...")
        else:
            print(f"✅ Downloaded {len(downloaded)} files\n")

        # Step 2: Import Excel files to JSON
        print("STEP 2: Importing Excel files to JSON...\n")
        records = importer.import_and_export(
            input_dir=str(config.EXCEL_PROCESSING_DIR / "2026"),
            output_file=str(config.OUTPUT_FILE_2026_POINTS),
            club_name=config.CLUB_NAME,
            mode="2026"
        )

        # Step 3: Add IAAF points (update the points file with scoring)
        print("STEP 3: Adding IAAF points...\n")
        scorer.score_rankings(
            input_file=str(config.OUTPUT_FILE_2026_POINTS),
            output_file=str(config.OUTPUT_FILE_2026_POINTS)
        )

        # Step 4: Compile all years into single JSON
        print("STEP 4: Compiling historical + current year data...\n")
        total_records = importer.compile_all_years(
            data2026_file=str(config.OUTPUT_FILE_2026_POINTS),
            historical_file=str(config.OUTPUT_FILE_HISTORICAL),
            output_file=str(config.OUTPUT_FILE_COMPILED)
        )

        # Step 5: Cleanup Excel files
        print("STEP 5: Cleaning up Excel files...\n")
        cleanup_excel_files()

        # Summary
        print("="*60)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"\n📊 Results:")
        print(f"   - Records processed: {records}")
        print(f"   - With IAAF points: {config.OUTPUT_FILE_2026_POINTS}")
        print(f"   - Total compiled: {total_records}")
        print(f"   - Output: {config.OUTPUT_FILE_COMPILED}")
        print(f"\n💾 Files ready for GitHub commit.\n")

        return 0

    except Exception as e:
        print("\n" + "="*60)
        print("❌ PIPELINE FAILED")
        print("="*60)
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
