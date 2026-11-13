"""Master end-to-end runner for ATFB (NHAE408) Midterm Essay — Group 12, Topic 7.

Usage:
    python run_all.py            # Live pull if online, automatic raw CSV fallback if offline
    python run_all.py --offline  # Force offline rebuild from data/raw/*.csv
"""

import os
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    t0 = time.time()
    if "--offline" in sys.argv:
        os.environ["ATFB_OFFLINE"] = "1"
        print("[run_all] Running in explicit offline mode (ATFB_OFFLINE=1).")

    print("=" * 76)
    print("STEP 1/5: Running data pipeline (src/data.py)...")
    print("=" * 76)
    from src import data as dat
    dat.run_pipeline()
    dat.pull_extended_2016()

    print("\n" + "=" * 76)
    print("STEP 2/5: Updating & executing notebook (notebooks/t7_macro_links.ipynb)...")
    print("=" * 76)
    from src import update_notebook as unb
    nb_path = unb.build_updated_notebook()
    unb.execute_notebook_inprocess(nb_path)

    print("\n" + "=" * 76)
    print("STEP 3/5: Building Word report (report/ATFB_Essay_Group12.docx)...")
    print("=" * 76)
    from src import build_report as br
    br.build_report_docx()

    print("\n" + "=" * 76)
    print("STEP 4/5: Running automated unit test suite (tests/test_pipeline.py)...")
    print("=" * 76)
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(ROOT / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    if not res.wasSuccessful():
        raise RuntimeError("Unit test suite failed!")

    print("\n" + "=" * 76)
    print("STEP 5/5: Running cross-artifact consistency check (src/check_report_numbers.py)...")
    print("=" * 76)
    from src import check_report_numbers as crn
    crn.main()

    elapsed = time.time() - t0
    print("\n" + "=" * 76)
    print(f"PIPELINE COMPLETED SUCCESSFULLY in {elapsed:.1f}s.")
    print("=" * 76)


if __name__ == "__main__":
    main()

