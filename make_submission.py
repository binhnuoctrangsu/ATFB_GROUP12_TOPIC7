"""Package the Microsoft Teams submission archive outside the git repository.

Creates:
  1. D:\\ANTIGRAVITY\\GROUP\\ATFB_Essay_Group12_code.zip
     Contains the consolidated single-notebook submission package:
       - README.md
       - requirements.txt
       - config.py
       - notebooks/t7_macro_links.ipynb
       - docs/references.md
       - report/ATFB_Essay_Group12.docx
       - data/raw/{vnindex_raw,hnxindex_raw,usdvnd_raw,oil_raw,dgs10_raw}.csv
       - data/processed/{panel,log_levels,alignment_report}.csv
  2. D:\\ANTIGRAVITY\\GROUP\\ATFB_Essay_Group12.pdf
     (Copied from report/ATFB_Essay_Group12.pdf for the separate PDF upload on Teams)
"""

import hashlib
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT.parent.parent  # D:\ANTIGRAVITY\GROUP


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_submission_package() -> dict:
    zip_path = OUT_DIR / "ATFB_Essay_Group12_code.zip"
    pdf_src = ROOT / "report" / "ATFB_Essay_Group12.pdf"
    pdf_dst = OUT_DIR / "ATFB_Essay_Group12.pdf"

    explicit_files = [
        "README.md",
        "requirements.txt",
        "config.py",
        "notebooks/t7_macro_links.ipynb",
        "docs/references.md",
        "report/ATFB_Essay_Group12.docx",
        "data/raw/vnindex_raw.csv",
        "data/raw/hnxindex_raw.csv",
        "data/raw/usdvnd_raw.csv",
        "data/raw/oil_raw.csv",
        "data/raw/dgs10_raw.csv",
        "data/processed/panel.csv",
        "data/processed/log_levels.csv",
        "data/processed/alignment_report.csv",
    ]

    files_to_pack: list[Path] = []
    for rel_str in explicit_files:
        p = ROOT / rel_str
        assert p.is_file(), f"Missing required submission file: {p}"
        files_to_pack.append(p)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fpath in files_to_pack:
            rel = fpath.relative_to(ROOT).as_posix()
            zf.write(fpath, arcname=f"ATFB_GROUP12_TOPIC7/{rel}")

    if pdf_src.exists():
        shutil.copy2(pdf_src, pdf_dst)

    zip_hash = sha256_file(zip_path)
    pdf_hash = sha256_file(pdf_dst) if pdf_dst.exists() else None

    print(f"[make_submission] Created {zip_path} ({zip_path.stat().st_size:,} bytes, {len(files_to_pack)} files)")
    print(f"                  SHA-256: {zip_hash}")
    if pdf_dst.exists():
        print(f"[make_submission] Copied  {pdf_dst} ({pdf_dst.stat().st_size:,} bytes)")
        print(f"                  SHA-256: {pdf_hash}")

    return {
        "zip_path": str(zip_path),
        "zip_files": len(files_to_pack),
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": zip_hash,
        "pdf_path": str(pdf_dst) if pdf_dst.exists() else None,
        "pdf_sha256": pdf_hash,
    }


if __name__ == "__main__":
    build_submission_package()
