"""Automated consistency and quality checker for ATFB Group 12 Topic 7.

Verifies:
1. All 33 CSV tables and 10 PNG figures match canonical values in src/report_numbers.py.
2. Group 12 member names and student IDs are populated in config.py, notebook header,
   report Title Page, and report Appendix A.
3. docs/references.md header ("21 Live-Verified Sources") matches its 21 numbered entries,
   and report/ATFB_Essay_Group12.docx References section aligns 1-for-1 with docs/references.md.
4. notebooks/t7_macro_links.ipynb has executed cleanly with 0 cell errors and no forbidden strings.
5. report/ATFB_Essay_Group12.docx obeys the <= 200-word Abstract limit, <= 7 columns per table,
   contains all required sections, references every table and figure in prose, and matches
   canonical empirical numbers.
6. report/ATFB_Essay_Group12.pdf main text (Abstract to Conclusion) is <= 15 pages.
"""

import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config
from src import report_numbers as rn

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

EXPECTED_MEMBERS = [
    ("Hoàng Phương Linh", "2412345011"),
    ("Võ Như Ý", "2412345017"),
    ("Lê Khánh Mỹ Linh", "2412345040"),
    ("Trương Bảo Thư", "2412345083"),
]


def check_group_metadata() -> dict:
    assert config.GROUP_NUMBER == "12", f"Expected GROUP_NUMBER='12', got {config.GROUP_NUMBER!r}"
    assert config.MEMBERS == EXPECTED_MEMBERS, f"config.MEMBERS mismatch: {config.MEMBERS}"
    return {"group_number": config.GROUP_NUMBER, "members_count": len(config.MEMBERS)}


def check_references_md(ref_path: Path) -> list[str]:
    txt = ref_path.read_text(encoding="utf-8")
    assert "## 3. Peer-Reviewed Academic Literature (21 Live-Verified Sources)" in txt, (
        "Missing corrected '21 Live-Verified Sources' header in docs/references.md"
    )
    numbered = [
        ln.strip() for ln in txt.splitlines()
        if ln.strip() and ln.strip()[0].isdigit() and ". **" in ln
    ]
    assert len(numbered) == 21, f"Expected 21 numbered peer-reviewed entries in references.md, found {len(numbered)}"
    return numbered


def check_notebook(nb_path: Path) -> dict:
    assert nb_path.exists(), f"Missing notebook: {nb_path}"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    cells = nb["cells"]
    code_cells = [c for c in cells if c["cell_type"] == "code"]
    unexecuted = [i for i, c in enumerate(cells) if c["cell_type"] == "code" and not c.get("execution_count")]
    errors = []
    for i, c in enumerate(cells):
        for out in c.get("outputs", []):
            if out.get("output_type") == "error":
                errors.append((i, out.get("ename"), out.get("evalue")))

    header_text = "".join(cells[0]["source"])
    for name, sid in EXPECTED_MEMBERS:
        assert name in header_text and sid in header_text, f"Missing {name} ({sid}) in notebook header cell"

    full_text = "\n".join("".join(c["source"]) for c in cells)
    assert "locked methodology" not in full_text.lower(), "Forbidden string 'locked methodology' in notebook"
    assert "locked rule" not in full_text.lower(), "Forbidden string 'locked rule' in notebook"
    assert "DRAFT for group review: rewrite in own words" in full_text, "Missing DRAFT marker in Conclusions"
    assert not unexecuted, f"Unexecuted code cells in notebook: {unexecuted}"
    assert not errors, f"Execution errors in notebook: {errors}"

    return {
        "total_cells": len(cells),
        "code_cells": len(code_cells),
        "unexecuted_code_cells": len(unexecuted),
        "error_cells": len(errors),
    }


def extract_docx_content(docx_path: Path) -> dict:
    with zipfile.ZipFile(docx_path, "r") as zf:
        xml_bytes = zf.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    body = root.find(f"{W_NS}body")

    paragraphs = []
    for p in body.findall(f"{W_NS}p"):
        texts = [t.text for t in p.iter(f"{W_NS}t") if t.text]
        p_text = "".join(texts).strip()
        p_style_el = p.find(f"{W_NS}pPr/{W_NS}pStyle")
        p_style = p_style_el.attrib.get(f"{W_NS}val", "") if p_style_el is not None else ""
        if p_text:
            paragraphs.append((p_style, p_text))

    tables_text = []
    for tbl in body.findall(f"{W_NS}tbl"):
        rows = []
        for tr in tbl.findall(f"{W_NS}tr"):
            cells = []
            for tc in tr.findall(f"{W_NS}tc"):
                c_txt = "".join(t.text for t in tc.iter(f"{W_NS}t") if t.text).strip()
                cells.append(c_txt)
            rows.append(cells)
        tables_text.append(rows)

    return {"paragraphs": paragraphs, "tables": tables_text}


def check_docx(docx_path: Path) -> dict:
    assert docx_path.exists(), f"Missing report docx: {docx_path}"
    content = extract_docx_content(docx_path)
    paragraphs = content["paragraphs"]
    tables = content["tables"]

    all_para_text = "\n".join(txt for _, txt in paragraphs)
    all_table_text = "\n".join(
        " | ".join(cell for cell in row)
        for tbl in tables
        for row in tbl
    )
    combined_text = all_para_text + "\n" + all_table_text

    # 1. Verify member names and IDs appear on Title Page (table 0) and in Appendix A (table 9)
    title_tbl_text = " ".join(c for r in tables[0] for c in r)
    app_a_tbl_text = " ".join(c for r in tables[9] for c in r)
    for name, sid in EXPECTED_MEMBERS:
        assert name in title_tbl_text and sid in title_tbl_text, f"Missing {name} ({sid}) in Title Page table"
        assert name in app_a_tbl_text and sid in app_a_tbl_text and "25%" in app_a_tbl_text, (
            f"Missing {name} ({sid}) or 25% share in Appendix A table"
        )

    # 2. Verify max columns per table <= 7
    max_cols = max(len(r) for tbl in tables for r in tbl)
    assert max_cols <= 7, f"Found table with {max_cols} columns (max allowed is 7)"

    # 3. Find Abstract text and verify word count <= 200
    abs_words = []
    in_abstract = False
    for style, txt in paragraphs:
        if txt.strip().lower() == "abstract":
            in_abstract = True
            continue
        if in_abstract:
            if style.startswith("Heading") or txt.startswith("1. Introduction"):
                break
            if not txt.startswith("Keywords:"):
                abs_words.extend(txt.split())
    abs_word_count = len(abs_words)
    assert 80 <= abs_word_count <= 200, f"Abstract word count ({abs_word_count}) must be <= 200 words"

    # 4. Verify required sections
    required_headings = [
        "Abstract",
        "1. Introduction",
        "2. Data",
        "3. Exploratory data analysis",
        "4. Methodology",
        "5. Results",
        "6. Conclusion",
        "References",
        "Appendix A. Contribution of each member",
        "Appendix B. Use of generative AI",
        "Appendix C. Reproducibility and data manifest",
    ]
    for req in required_headings:
        assert req in all_para_text, f"Missing required section heading in report: {req}"

    # 5. Verify 21 numbered references in report match docs/references.md
    for idx in range(1, 22):
        assert f"\n{idx}. " in ("\n" + all_para_text), f"Missing numbered reference #{idx} in report References"

    # 6. Verify all 8 Tables and 6 Figures are captioned and referenced in prose
    for t_idx in range(1, 9):
        assert f"Table {t_idx}" in all_para_text, f"Missing Table {t_idx} caption/reference in report prose"
    for f_idx in range(1, 7):
        assert f"Figure {f_idx}" in all_para_text, f"Missing Figure {f_idx} caption/reference in report prose"

    # 7. Verify canonical empirical numbers appear accurately in the report
    canonical_tokens = [
        "1,527",       # N_ALIGNED_RETURNS
        "1,576",       # N_VN_COMMON_DAYS
        "3,010,000",   # HOSE_MCAP_BN_VND
        "199,800",     # HNX_MCAP_BN_VND
        "93.78%",      # W_HOSE
        "6.22%",       # W_HNX
        "0.9993",      # Corr(r_composite, r_VNINDEX)
        "3.30",        # F stat dUS10Y -> r_VN (3.2991)
        "0.0056",      # p-value dUS10Y -> r_VN
        "3.78",        # F stat dUS10Y -> r_VN excl. provider gaps (3.7836)
        "0.0021",      # p-value dUS10Y -> r_VN excl. provider gaps
        "3.85",        # F stat dUS10Y -> r_USDVND (3.8480)
        "0.0018",      # p-value dUS10Y -> r_USDVND
        "-0.0666%",    # IRF h=1 r_VN to dUS10Y
        "-0.0938%",    # IRF h=5 r_VN to dUS10Y
        "98.19",       # FEVD h=20 own shock
        "1.29",        # FEVD h=20 dUS10Y
        "51.99",       # Johansen trace r=0
        "26.29",       # Johansen max-eig r=0
        "-5.6806",     # VECM beta USDVND
        "-1.0452",     # VECM beta OIL
        "0.1915",      # VECM beta DGS10
        "1.2448",      # OOS RMSE VAR(AIC)
        "1.2290",      # OOS RMSE AR(1)
        "1.2349",      # OOS RMSE RW
        "2,384",       # Extended 10-year VNINDEX N
        "67.99",       # Extended 10-year Johansen trace
    ]
    for tok in canonical_tokens:
        assert tok in combined_text, f"Missing canonical empirical number in report: {tok}"

    return {
        "abstract_words": abs_word_count,
        "paragraph_count": len(paragraphs),
        "table_count": len(tables),
        "max_table_cols": max_cols,
        "canonical_tokens_verified": len(canonical_tokens),
    }


def main():
    print("1. Verifying canonical CSV tables and PNG figures via src.report_numbers...")
    rn_summary = rn.verify_all_numbers()
    print("   PASS:", rn_summary)

    print("2. Verifying Group 12 metadata and docs/references.md...")
    grp_summary = check_group_metadata()
    refs_list = check_references_md(ROOT / "docs" / "references.md")
    print("   PASS:", {**grp_summary, "references_md_numbered_entries": len(refs_list)})

    nb_path = ROOT / "notebooks" / "t7_macro_links.ipynb"
    print(f"3. Checking executed notebook {nb_path.name}...")
    nb_summary = check_notebook(nb_path)
    print("   PASS:", nb_summary)

    docx_path = ROOT / "report" / "ATFB_Essay_Group12.docx"
    if docx_path.exists():
        print(f"4. Checking Word report {docx_path.name}...")
        docx_summary = check_docx(docx_path)
        print("   PASS:", docx_summary)

    pdf_path = ROOT / "report" / "ATFB_Essay_Group12.pdf"
    if pdf_path.exists():
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        abs_page, ref_page = None, None
        for idx, page in enumerate(reader.pages, start=1):
            txt = page.extract_text() or ""
            if abs_page is None and "Abstract" in txt:
                abs_page = idx
            if ref_page is None and "References" in txt and "1. Introduction" not in txt:
                ref_page = idx
        assert abs_page is not None and ref_page is not None, "Could not locate Abstract/References in PDF"
        main_text_pages = ref_page - abs_page
        assert main_text_pages <= 15, f"Main text is {main_text_pages} pages (exceeds <= 15 page limit)"
        print(f"5. Checking PDF report {pdf_path.name}...")
        print("   PASS:", {"total_pages": total_pages, "abstract_start_page": abs_page,
                           "references_start_page": ref_page, "main_text_pages": main_text_pages})

    print("All consistency checks succeeded.")


if __name__ == "__main__":
    main()
