"""Package the Microsoft Teams submission archive outside the git repository.

Creates:
  1. D:\\ANTIGRAVITY\\GROUP\\ATFB_Essay_Group12_code.zip
     (containing code, notebooks, docs, report .docx, data/raw/*.csv, data/processed/*.csv,
      and results/{tables,figures}/* so the archive runs start-to-finish offline or online)
  2. D:\\ANTIGRAVITY\\GROUP\\ATFB_Essay_Group12.pdf
     (copied from report/ATFB_Essay_Group12.pdf)
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

    include_patterns = [
        "README.md",
        "requirements.txt",
        "config.py",
        "run_all.py",
        "make_submission.py",
        ".gitignore",
        "src/*.py",
        "tests/*.py",
        "notebooks/t7_macro_links.ipynb",
        "docs/*.md",
        "report/report_template.docx",
        "report/ATFB_Essay_Group12.docx",
        "data/raw/*.csv",
        "data/processed/*.csv",
        "results/tables/*.csv",
        "results/figures/*.png",
    ]

    files_to_pack: list[Path] = []
    for pat in include_patterns:
        matched = sorted(ROOT.glob(pat))
        for p in matched:
            if p.is_file() and "__pycache__" not in p.parts:
                files_to_pack.append(p)

    assert len(files_to_pack) >= 70, f"Expected >= 70 files to pack, found {len(files_to_pack)}"

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

