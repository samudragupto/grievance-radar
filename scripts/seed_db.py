# Database initialization and sample data seeding script.

from pathlib import Path
import sys
from scripts.run_pipeline import run

if __name__ == "__main__":
    sample_file = Path(__file__).resolve().parent.parent / "data" / "sample_complaints.json"
    if not sample_file.exists():
        print(f"Generating sample data first at {sample_file}...")
        from scripts.generate_sample_data import main as gen_main
        gen_main()

    print(f"Seeding database and running pipeline from {sample_file}...")
    run(str(sample_file))
    print("Database seeding and initial anomaly detection complete.")
