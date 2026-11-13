"""Build report/ATFB_Essay_Group12.docx from report/report_template.docx.

Produces a clean, well-argued academic essay (~12-13 pages of main text) with:
- Filled Group 12 member names and student IDs on the Title Page and Appendix A (25% each placeholder).
- Readable 10 pt fonts in all tables (6-7 columns maximum per table).
- Standard single-figure-per-position sizing (Figures 1-6).
- Uniform terminology, consistent decimal precision, and measured undergraduate academic tone.
- References section aligned 1-for-1 with docs/references.md (textbook TODO + Christoffersen 2012 +
  adapted course template + the 21 live-verified peer-reviewed articles).
"""

import io
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
REL_PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("wp", WP_NS)
ET.register_namespace("a", A_NS)
ET.register_namespace("pic", PIC_NS)


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def make_p(text: str = "", style: str = "", bold: bool = False, italic: bool = False,
           align: str = "", space_after: int = 80, space_before: int = 0,
           line_spacing: int = 360, font_size_half_pt: int = 24,
           keep_next: bool = False,
           runs: list[tuple[str, bool, bool]] | None = None) -> ET.Element:
    """Create a WordprocessingML paragraph element."""
    p = ET.Element(w_tag("p"))
    pPr = ET.SubElement(p, w_tag("pPr"))
    if style:
        pStyle = ET.SubElement(pPr, w_tag("pStyle"))
        pStyle.set(w_tag("val"), style)
    if keep_next:
        ET.SubElement(pPr, w_tag("keepNext"))
    spacing = ET.SubElement(pPr, w_tag("spacing"))
    spacing.set(w_tag("after"), str(space_after))
    if space_before > 0:
        spacing.set(w_tag("before"), str(space_before))
    if line_spacing:
        spacing.set(w_tag("line"), str(line_spacing))
        spacing.set(w_tag("lineRule"), "auto")
    if align:
        jc = ET.SubElement(pPr, w_tag("jc"))
        jc.set(w_tag("val"), align)

    if runs is not None:
        for r_txt, r_b, r_i in runs:
            if not r_txt:
                continue
            r = ET.SubElement(p, w_tag("r"))
            rPr = ET.SubElement(r, w_tag("rPr"))
            if r_b:
                ET.SubElement(rPr, w_tag("b"))
            if r_i:
                ET.SubElement(rPr, w_tag("i"))
            if font_size_half_pt and not style.startswith("Heading"):
                sz = ET.SubElement(rPr, w_tag("sz"))
                sz.set(w_tag("val"), str(font_size_half_pt))
                szCs = ET.SubElement(rPr, w_tag("szCs"))
                szCs.set(w_tag("val"), str(font_size_half_pt))
            t = ET.SubElement(r, w_tag("t"))
            if r_txt.startswith(" ") or r_txt.endswith(" "):
                t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            t.text = r_txt
    elif text:
        r = ET.SubElement(p, w_tag("r"))
        rPr = ET.SubElement(r, w_tag("rPr"))
        if bold:
            ET.SubElement(rPr, w_tag("b"))
        if italic:
            ET.SubElement(rPr, w_tag("i"))
        if font_size_half_pt and not style.startswith("Heading"):
            sz = ET.SubElement(rPr, w_tag("sz"))
            sz.set(w_tag("val"), str(font_size_half_pt))
            szCs = ET.SubElement(rPr, w_tag("szCs"))
            szCs.set(w_tag("val"), str(font_size_half_pt))
        t = ET.SubElement(r, w_tag("t"))
        t.text = text
    return p


def make_page_break() -> ET.Element:
    p = ET.Element(w_tag("p"))
    r = ET.SubElement(p, w_tag("r"))
    br = ET.SubElement(r, w_tag("br"))
    br.set(w_tag("type"), "page")
    return p


def make_table(headers: list[str], rows: list[list[str]],
               col_widths_dxa: list[int] | None = None,
               font_size_half_pt: int = 20) -> ET.Element:
    """Create a readable academic Word table (default 10 pt = 20 half-points, <= 7 columns)."""
    total_w = 9072
    ncols = len(headers)
    assert ncols <= 7, f"Table has {ncols} columns; maximum allowed is 7."
    if col_widths_dxa is None:
        col_widths_dxa = [total_w // ncols] * ncols

    tbl = ET.Element(w_tag("tbl"))
    tblPr = ET.SubElement(tbl, w_tag("tblPr"))
    tblStyle = ET.SubElement(tblPr, w_tag("tblStyle"))
    tblStyle.set(w_tag("val"), "TableGrid")
    tblW = ET.SubElement(tblPr, w_tag("tblW"))
    tblW.set(w_tag("type"), "dxa")
    tblW.set(w_tag("w"), str(sum(col_widths_dxa)))
    jc = ET.SubElement(tblPr, w_tag("jc"))
    jc.set(w_tag("val"), "center")

    tblGrid = ET.SubElement(tbl, w_tag("tblGrid"))
    for w in col_widths_dxa:
        gc = ET.SubElement(tblGrid, w_tag("gridCol"))
        gc.set(w_tag("w"), str(w))

    def _add_row(cells: list[str], is_header: bool = False):
        tr = ET.SubElement(tbl, w_tag("tr"))
        trPr = ET.SubElement(tr, w_tag("trPr"))
        ET.SubElement(trPr, w_tag("cantSplit"))
        if is_header:
            ET.SubElement(trPr, w_tag("tblHeader"))
        for idx, c_text in enumerate(cells):
            tc = ET.SubElement(tr, w_tag("tc"))
            tcPr = ET.SubElement(tc, w_tag("tcPr"))
            tcW = ET.SubElement(tcPr, w_tag("tcW"))
            tcW.set(w_tag("type"), "dxa")
            tcW.set(w_tag("w"), str(col_widths_dxa[idx]))
            if is_header:
                shd = ET.SubElement(tcPr, w_tag("shd"))
                shd.set(w_tag("val"), "clear")
                shd.set(w_tag("color"), "auto")
                shd.set(w_tag("fill"), "EFEFEF")
            al = "left" if idx == 0 else "center"
            p = make_p(
                text=str(c_text),
                bold=is_header,
                align=al,
                space_after=20,
                space_before=20,
                line_spacing=240,
                font_size_half_pt=font_size_half_pt,
            )
            tc.append(p)

    _add_row(headers, is_header=True)
    for r in rows:
        _add_row(r, is_header=False)
    return tbl


def make_figure_p(rel_id: str, doc_pr_id: int, img_name: str,
                  cx_emu: int, cy_emu: int) -> ET.Element:
    """Create a centered paragraph containing a single inline DrawingML picture."""
    xml_str = f"""
    <w:p xmlns:w="{W_NS}" xmlns:r="{R_NS}" xmlns:wp="{WP_NS}" xmlns:a="{A_NS}" xmlns:pic="{PIC_NS}">
      <w:pPr>
        <w:spacing w:before="60" w:after="20" w:line="240" w:lineRule="auto"/>
        <w:jc w:val="center"/>
      </w:pPr>
      <w:r>
        <w:drawing>
          <wp:inline distT="0" distB="0" distL="0" distR="0">
            <wp:extent cx="{cx_emu}" cy="{cy_emu}"/>
            <wp:docPr id="{doc_pr_id}" name="{img_name}"/>
            <wp:cNvGraphicFramePr>
              <a:graphicFrameLocks noChangeAspect="1"/>
            </wp:cNvGraphicFramePr>
            <a:graphic>
              <a:graphicData uri="{PIC_NS}">
                <pic:pic>
                  <pic:nvPicPr>
                    <pic:cNvPr id="{doc_pr_id}" name="{img_name}"/>
                    <pic:cNvPicPr/>
                  </pic:nvPicPr>
                  <pic:blipFill>
                    <a:blip r:embed="{rel_id}"/>
                    <a:stretch><a:fillRect/></a:stretch>
                  </pic:blipFill>
                  <pic:spPr>
                    <a:xfrm>
                      <a:off x="0" y="0"/>
                      <a:ext cx="{cx_emu}" cy="{cy_emu}"/>
                    </a:xfrm>
                    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                  </pic:spPr>
                </pic:pic>
              </a:graphicData>
            </a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>
    """
    return ET.fromstring(xml_str.strip())


def prepare_single_figures() -> dict[str, tuple[bytes, int, int]]:
    """Load standalone single figures at standard academic widths (no side-by-side strips)."""
    fig_dir = config.FIG_DIR
    fig_specs = [
        ("image1.png", fig_dir / "fig01_composite_construction.png", 4800000),
        ("image2.png", fig_dir / "fig02_levels_and_returns.png", 4600000),
        ("image3.png", fig_dir / "fig03_qq_plots.png", 4800000),
        ("image4.png", fig_dir / "fig04_acf_returns_squared.png", 4600000),
        ("image5.png", fig_dir / "fig05_irf_orthogonalised.png", 3600000),
        ("image6.png", fig_dir / "fig08_forecast_comparison.png", 4500000),
    ]
    out = {}
    for name, fpath, target_cx in fig_specs:
        png_bytes = fpath.read_bytes()
        im = Image.open(io.BytesIO(png_bytes))
        w_px, h_px = im.size
        cy = int(target_cx * (h_px / w_px))
        out[name] = (png_bytes, target_cx, cy)
    return out


def build_report_docx() -> Path:
    template_path = ROOT / "report" / "report_template.docx"
    out_path = ROOT / "report" / "ATFB_Essay_Group12.docx"
    assert template_path.exists(), f"Missing template: {template_path}"

    figs = prepare_single_figures()

    with zipfile.ZipFile(template_path, "r") as zin:
        doc_xml = zin.read("word/document.xml")
        rels_xml = zin.read("word/_rels/document.xml.rels")
        ct_xml = zin.read("[Content_Types].xml")
        other_items = {
            name: zin.read(name)
            for name in zin.namelist()
            if name not in ("word/document.xml", "word/_rels/document.xml.rels", "[Content_Types].xml")
        }

    # 1. Register PNG content type in [Content_Types].xml
    ct_root = ET.fromstring(ct_xml)
    has_png = any(el.attrib.get("Extension") == "png" for el in ct_root.findall(f"{{{CT_NS}}}Default"))
    if not has_png:
        d_png = ET.SubElement(ct_root, f"{{{CT_NS}}}Default")
        d_png.set("Extension", "png")
        d_png.set("ContentType", "image/png")

    # 2. Register image relationships rId10..rId15 in word/_rels/document.xml.rels
    rels_root = ET.fromstring(rels_xml)
    for idx in range(1, 7):
        rel_el = ET.SubElement(rels_root, f"{{{REL_PKG_NS}}}Relationship")
        rel_el.set("Id", f"rId{9 + idx}")
        rel_el.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
        rel_el.set("Target", f"media/image{idx}.png")

    # 3. Build document body preserving the template's sectPr
    doc_root = ET.fromstring(doc_xml)
    doc_root.attrib.pop("{http://schemas.openxmlformats.org/markup-compatibility/2006}Ignorable", None)
    body = doc_root.find(w_tag("body"))
    sect_pr = body.find(w_tag("sectPr"))
    if sect_pr is not None:
        for k in list(sect_pr.attrib):
            if not k.startswith(f"{{{W_NS}}}") and not k.startswith(f"{{{R_NS}}}"):
                del sect_pr.attrib[k]
    body.clear()

    def add_p(text: str = "", style: str = "", bold: bool = False, italic: bool = False,
              align: str = "both", space_after: int = 60, space_before: int = 0,
              line_spacing: int = 360, font_size_half_pt: int = 24,
              keep_next: bool = False,
              runs: list[tuple[str, bool, bool]] | None = None):
        body.append(make_p(
            text=text, style=style, bold=bold, italic=italic, align=align,
            space_after=space_after, space_before=space_before,
            line_spacing=line_spacing, font_size_half_pt=font_size_half_pt,
            keep_next=keep_next, runs=runs,
        ))

    def add_h1(text: str):
        add_p(text=text, style="Heading1", align="left", space_before=120, space_after=40, line_spacing=280, keep_next=True)

    def add_h2(text: str):
        add_p(text=text, style="Heading2", align="left", space_before=90, space_after=30, line_spacing=260, keep_next=True)

    def add_caption(text: str, space_before: int = 30, space_after: int = 25, keep_next: bool = True):
        add_p(text=text, bold=True, italic=False, align="left",
              space_before=space_before, space_after=space_after,
              line_spacing=240, font_size_half_pt=20, keep_next=keep_next)

    def add_fig(idx: int, caption: str):
        img_name = f"image{idx}.png"
        _, cx, cy = figs[img_name]
        body.append(make_figure_p(f"rId{9 + idx}", 100 + idx, img_name, cx, cy))
        add_caption(caption, space_before=15, space_after=45, keep_next=False)

    # =========================================================================
    # TITLE PAGE (Excluded from the 15-page main-text count)
    # =========================================================================
    add_p("FOREIGN TRADE UNIVERSITY – HO CHI MINH CITY CAMPUS", bold=True, align="center", space_after=120, font_size_half_pt=24)
    add_p("Applied Technology in Finance and Banking (NHAE408)", bold=False, align="center", space_after=900, font_size_half_pt=24)
    add_p("MIDTERM GROUP ESSAY", bold=True, align="center", space_after=160, font_size_half_pt=28)
    add_p(
        "Macro-Financial Links in Vietnam: Short-Run Transmission, Cointegration, and Out-of-Sample Predictability of Stock Returns with the USD/VND Exchange Rate, US Interest Rates, and Brent Crude Oil",
        bold=True, align="center", space_after=480, font_size_half_pt=28,
    )
    add_p(f"Topic: T7 (Macro-financial links)   ·   Group: {config.GROUP_NUMBER}", bold=False, align="center", space_after=420, font_size_half_pt=24)

    member_rows = [
        [str(i), name, sid]
        for i, (name, sid) in enumerate(config.MEMBERS, start=1)
    ]
    body.append(make_table(
        headers=["No.", "Full name", "Student ID"],
        rows=member_rows,
        col_widths_dxa=[1200, 4872, 3000],
        font_size_half_pt=22,
    ))
    add_p("", space_after=360)
    add_p("Instructors: Dr. Lê Trung Thành, Dr. Nguyễn Thị Hoàng Anh", align="center", space_after=120, font_size_half_pt=24)
    add_p("Ho Chi Minh City, November 2026", align="center", space_after=120, font_size_half_pt=24)
    body.append(make_page_break())

    # =========================================================================
    # ABSTRACT (Strictly <= 200 words)
    # =========================================================================
    add_h1("Abstract")
    abstract_text = (
        "This essay examines how daily returns on the Vietnamese stock market interact with the USD/VND "
        "exchange rate, the US 10-year Treasury yield, and Brent crude oil prices across N = 1,527 aligned "
        "trading days from June 2020 to October 2026. Using start-of-sample domestic market capitalisations, "
        "we construct the VN composite index combining VN-Index (93.78%) and HNX-Index (6.22%). We estimate a "
        "five-lag Vector Autoregression (VAR(5)) on log returns and first differences to study short-run "
        "transmission, alongside Engle–Granger and Johansen cointegration tests and a rank-1 Vector Error-Correction "
        "Model (VECM) on log levels. In the short run, changes in the US 10-year Treasury yield significantly "
        "Granger-cause returns on the VN composite index (F = 3.30, p = 0.0056) and changes in the USD/VND "
        "exchange rate (F = 3.85, p = 0.0018). A one-standard-deviation US yield shock reduces the VN composite "
        "index return by -0.0666% on the next trading day (h = 1) and -0.0938% at h = 5, whereas Brent crude "
        "oil and the USD/VND exchange rate do not directly Granger-cause equity returns. Long-run cointegration "
        "is weak, with zero equity error-correction adjustment (alpha = -0.0008, p = 0.7280). Out of sample, "
        "the VAR does not significantly outperform an AR(1) or random walk."
    )
    add_p(abstract_text)
    add_p(
        runs=[
            ("Keywords: ", True, False),
            ("Vietnamese stock market; VN composite index; VAR; cointegration; VECM; Diebold–Mariano test.", False, True),
        ],
        space_after=80,
    )

    # =========================================================================
    # 1. INTRODUCTION
    # =========================================================================
    add_h1("1. Introduction")
    add_p(
        "As an open, trade-dependent economy, Vietnam's equity market is sensitive to external monetary conditions, "
        "exchange-rate movements, and global energy prices. Understanding how these macro-financial variables "
        "interact with domestic stock prices is relevant to investors evaluating currency or commodity hedges, "
        "fund managers assessing external interest-rate spillovers, and analysts testing whether macroeconomic "
        "series help forecast daily equity returns. This essay addresses Topic 7 of the ATFB (NHAE408) Midterm "
        "Essay: How are daily Vietnamese stock returns related to the USD/VND exchange rate, the US 10-year "
        "Treasury yield, and Brent crude oil prices in the short run and the long run, and do these links "
        "improve out-of-sample return forecasts?"
    )
    add_p(
        "Economic theory highlights three main channels connecting these variables. First, in flow-oriented "
        "exchange-rate models (Dornbusch & Fischer, 1980), currency depreciation alters firm competitiveness "
        "and foreign-currency debt burdens, while portfolio-balance models (Phylaktis & Ravazzolo, 2005) imply "
        "reverse causality from domestic stock returns to the exchange rate through international capital flows. "
        "Second, the global financial cycle literature (Miranda-Agrippino & Rey, 2020) shows that US Treasury "
        "yield rises tighten global dollar funding and increase discount rates for emerging-market equities, "
        "while simultaneously placing depreciation pressure on managed exchange rates. Third, oil price changes "
        "affect equity valuations both through production costs (Sadorsky, 1999) and through shifts in global "
        "aggregate demand (Kilian & Park, 2009). Prior empirical studies on Vietnam (Hussainey & Ngoc, 2009; "
        "Narayan & Narayan, 2010; Nguyen & Bhatti, 2012) examine subsets of these relationships on earlier "
        "samples using the Ho Chi Minh Stock Exchange (HOSE) VN-Index alone, leaving open how the market behaves "
        "across the post-2020 period and whether in-sample relationships hold out of sample."
    )
    add_p(
        "Our empirical analysis proceeds in six stages. In Section 2, we construct the VN composite index "
        "combining VN-Index (93.78%) and HNX-Index (6.22%) using fixed start-of-sample market capitalisations "
        "over N = 1,527 aligned trading days from 2 June 2020 to 30 October 2026. Section 3 conducts exploratory "
        "data analysis (summary statistics, Jarque–Bera and Q–Q normality diagnostics, ADF and KPSS unit-root "
        "tests, and Ljung–Box and ARCH-LM autocorrelation tests). Section 4 sets out the econometric methodology "
        "for the VAR(5), cointegration/VECM, and rolling out-of-sample evaluation (Sims, 1980; Granger, 1969; "
        "Engle & Granger, 1987; Johansen, 1991; Diebold & Mariano, 1995). Section 5 presents the empirical "
        "results and robustness checks (including VN-Index alone), and Section 6 concludes."
    )

    # =========================================================================
    # 2. DATA
    # =========================================================================
    add_h1("2. Data")
    add_p(
        "All data series are retrieved programmatically via src/data.py and saved unchanged to data/raw/. "
        "Daily closing levels of VN-Index (HOSE, symbol VNINDEX) and HNX-Index (Hanoi Stock Exchange, symbol HNX) "
        "are pulled from the vnstock Python library (DNSE endpoint; Yahoo Finance is not used for Vietnamese "
        "indices because it lacks a verified index feed). The daily spot USD/VND exchange rate (USDVND=X) and "
        "front-month Brent crude oil futures price (BZ=F, USD per barrel) are retrieved from Yahoo Finance via "
        "yfinance. Because Brent crude oil is missing on only 1.98% of weekdays—well below our 5.00% threshold—no "
        "WTI fallback is needed. The US 10-year Treasury constant-maturity yield (DGS10, % per annum) is pulled "
        "from Federal Reserve Economic Data (FRED)."
    )
    add_p(
        "Although our initial target window was November 2016 to October 2026, the vnstock endpoint provides "
        "HNX-Index data starting on 11 May 2020 (whereas VN-Index is available back to November 2016). Following "
        "the rule of using the longest common window across all series, our primary sample starts on 1 June 2020 "
        "and ends on 30 October 2026, yielding N = 1,527 aligned daily return observations (more than six years "
        "of daily data). To represent the whole listed market ahead of the December 2026 transfer of HNX equities "
        "to HOSE under Circular 69/2023/TT-BTC, we construct the VN composite index as a weighted average of "
        "daily log returns, r_composite,t = w_HOSE * r_VNINDEX,t + w_HNX * r_HNXINDEX,t, using official domestic "
        "market capitalisations at the end of May 2020: 3,010,000 billion VND for HOSE (w_HOSE = 0.9378, or "
        "93.78%) and 199,800 billion VND for HNX (w_HNX = 0.0622, or 6.22%). As shown in Figure 1, daily returns "
        "on the VN composite index and VN-Index have a correlation of 0.9993 (and a log-level correlation of "
        "0.9997), with a mean absolute daily difference of 0.0380 percentage points."
    )
    add_fig(1, "Figure 1: The VN Composite Index vs. VN-Index and HNX-Index (Rebased to 100 on 2020-06-02) and Daily Return Difference.")
    add_p(
        "Table 1 summarises the sample coverage and calendar alignment. The reference calendar is the set of "
        "1,576 trading days on which both VN-Index and HNX-Index trade out of 1,675 calendar weekdays. Checking "
        "the 99 skipped weekdays against the Vietnamese exchange holiday schedule shows that 71 weekdays are "
        "official public holidays (such as five-day Tết closures, 30 April–1 May, and 2 September) and 28 "
        "weekdays are unscheduled vnstock provider gaps occurring in three clusters between July 2020 and July "
        "2021 (10 return intervals; no provider gaps occur after July 2021). Traded prices (the USD/VND exchange "
        "rate and Brent crude oil) are aligned to the Vietnamese calendar via an inner join without forward-filling "
        "so that stale prices do not create artificial zero returns; this drops 48 Vietnamese trading days "
        "(47 US/UK holidays without Brent quotes and 3 days without USD/VND quotes, with 2 overlapping), leaving "
        "1,528 level dates and N = 1,527 return observations. Only the US 10-year Treasury yield (DGS10) is "
        "forward-filled across 59 US bond-market holidays. Log returns r_t = 100 * ln(P_t / P_{t-1}) and yield "
        "differences dUS10Y_t = DGS10_t - DGS10_{t-1} (in percentage points) are computed after alignment so "
        "that all four variables span the exact same date interval on every row. Checking daily simple moves "
        "above HOSE's +-7% daily price limit (HNX limit +-10%) flags two valid HNX observations (-9.80% on "
        "18 January 2022 across a two-day interval after Martin Luther King Jr. Day, and +8.08% on 22 April "
        "2025 within HNX's +-10% band), both of which are retained. Cross-checking vnstock closes against 10 "
        "published year-end and market milestone reports (2020–2025) confirms exact agreement (0.00 index points) "
        "on all 20 checkpoints."
    )
    add_caption("Table 1: Data Sources, Sample Coverage, and Calendar Alignment (2020-06-02 to 2026-10-30)")
    body.append(make_table(
        headers=["Series", "Source & Symbol", "Raw Obs.", "Calendar Alignment Rule", "Days Dropped / Filled", "Aligned N"],
        rows=[
            ["VN-Index (HOSE)", "vnstock (VNINDEX)", "1,576", "Reference calendar (71 VN holidays, 28 provider gaps)", "48 dropped by inner join", "1,527"],
            ["HNX-Index (HNX)", "vnstock (HNX)", "1,576", "Reference calendar (available from 2020-05-11)", "48 dropped by inner join", "1,527"],
            ["VN Composite Index", "93.78% HOSE + 6.22% HNX", "1,576", "Fixed May-2020 weights (3,010,000 & 199,800 bn VND)", "48 dropped by inner join", "1,527"],
            ["USD/VND Exchange Rate", "yfinance (USDVND=X)", "1,671", "Inner join (no forward-fill of traded FX quotes)", "3 VN days missing quote", "1,527"],
            ["Brent Crude Oil", "yfinance (BZ=F)", "1,615", "Inner join (missing 1.98% of weekdays < 5% cap)", "47 US/UK holidays dropped", "1,527"],
            ["US 10Y Treasury Yield", "FRED (DGS10)", "1,600", "Forward-filled on US bond holidays only", "59 VN days forward-filled", "1,527"],
        ],
        col_widths_dxa=[1550, 1550, 850, 2572, 1650, 900],
        font_size_half_pt=20,
    ))
    add_p("", space_after=40)

    # =========================================================================
    # 3. EXPLORATORY DATA ANALYSIS
    # =========================================================================
    add_h1("3. Exploratory data analysis")
    add_p(
        "Figure 2 plots the daily levels and return/difference series from June 2020 to October 2026, and Table 2 "
        "reports summary statistics and Jarque–Bera normality tests. Over the sample, the VN composite index had "
        "a mean daily log return of 0.0457% (11.53% annualised) and a daily standard deviation of 1.2497% "
        "(19.84% annualised). Brent crude oil was the most volatile series (daily standard deviation 2.4843%, "
        "or 39.44% annualised, ranging from -15.6940% to +9.1580%), whereas the USD/VND exchange rate had a "
        "daily standard deviation of 0.2850% (4.52% annualised, annualised drift +1.70%), reflecting the State "
        "Bank of Vietnam's managed reference-band regime. The US 10-year Treasury yield rose from 0.66% in June "
        "2020 to above 4.20% in 2024–2026, with a daily change standard deviation of 0.0594 percentage points."
    )
    add_fig(2, "Figure 2: Daily Levels and Log Returns / First Differences of the VN Composite Index, the USD/VND Exchange Rate, Brent Crude Oil, and the US 10-Year Treasury Yield.")
    add_caption("Table 2: Summary Statistics and Normality Tests for Daily Returns and Yield Changes (N = 1,527)")
    body.append(make_table(
        headers=["Series", "Mean (Daily)", "Std. Dev.", "Ann. Mean / Vol.", "Skewness", "Excess Kurt.", "Jarque–Bera [p-Value]"],
        rows=[
            ["r_composite (%)", "0.0457", "1.2497", "11.53% / 19.84%", "-0.96", "4.62", "1,580.00 [<0.0001]"],
            ["r_VNINDEX (%)", "0.0455", "1.2463", "11.46% / 19.78%", "-0.94", "4.60", "1,554.70 [<0.0001]"],
            ["r_HNXINDEX (%)", "0.0497", "1.5223", "12.52% / 24.17%", "-0.87", "4.89", "1,705.20 [<0.0001]"],
            ["r_USDVND (%)", "0.0067", "0.2850", "1.70% / 4.52%", "-0.10", "20.56", "26,713.60 [<0.0001]"],
            ["r_OIL (%)", "0.0735", "2.4843", "18.51% / 39.44%", "-0.82", "4.34", "1,357.90 [<0.0001]"],
            ["d_DGS10 (pp)", "0.0028", "0.0594", "+0.70 / 0.94 pp", "-0.05", "1.41", "124.87 [<0.0001]"],
        ],
        col_widths_dxa=[1400, 1050, 1050, 1500, 1000, 1100, 1972],
        font_size_half_pt=20,
    ))
    add_p(
        "The exploratory analysis highlights four stylized facts that guide our model specification in Section 4. "
        "First, every return and difference series departs strongly from normality: Jarque–Bera tests reject "
        "normality at p < 0.0001 in all cases, with negative skewness in the VN composite index (-0.96) and "
        "Brent crude oil (-0.82) and high excess kurtosis in the USD/VND exchange rate (20.56), as confirmed by "
        "the heavy-tailed Q–Q plots in Figure 3. Second, Table 3 shows that all level series are non-stationary "
        "I(1) processes—Augmented Dickey–Fuller (ADF) tests fail to reject a unit root (all p >= 0.1290) and "
        "KPSS tests reject stationarity at the 1% level (p = 0.0100)—whereas all log returns and first differences "
        "are stationary I(0) processes (ADF p < 0.0001; KPSS p = 0.1000). Third, Ljung–Box Q(10) tests (Table 3 "
        "and Figure 4) show no significant linear autocorrelation in the VN composite index return (Q(10) = 7.98, "
        "p = 0.6300) or US 10-year Treasury yield changes (Q(10) = 15.56, p = 0.1130), weak autocorrelation in "
        "Brent crude oil (Q(10) = 19.66, p = 0.0326), and strong autocorrelation in the managed USD/VND exchange "
        "rate (Q(10) = 141.48, p < 0.0001). Fourth, Ljung–Box tests on squared returns Q^2(10) and Engle's "
        "ARCH-LM(10) tests reject homoskedasticity at p < 0.0001 for every series, confirming pronounced "
        "volatility clustering (Christoffersen, 2012; Bollerslev, 1986). Together, these properties motivate "
        "estimating a stationary VAR on returns/differences (with HAC-robust inference checks) for short-run "
        "dynamics and testing the I(1) log levels for cointegration."
    )
    add_fig(3, "Figure 3: Normal Q–Q Plots of Daily Returns and Yield Changes (2020–2026).")
    add_fig(4, "Figure 4: Sample Autocorrelation Functions of Daily Returns (Top) and Squared Returns (Bottom) to Lag 20.")
    add_caption("Table 3: Unit-Root Tests (ADF, KPSS) and Autocorrelation / ARCH Diagnostics (N = 1,527)")
    body.append(make_table(
        headers=["Variable", "ADF (Level) [p]", "KPSS (Level) [p]", "ADF (Diff.) [p]", "KPSS (Diff.) [p]", "LB Q(10) [p]", "ARCH-LM(10) [p]"],
        rows=[
            ["VN Composite Index", "-2.00 [0.2870]", "2.19 [0.0100]", "-38.61 [<0.0001]", "0.13 [0.1000]", "7.98 [0.6300]", "158.31 [<0.0001]"],
            ["VN-Index", "-1.95 [0.3070]", "2.13 [0.0100]", "-38.59 [<0.0001]", "0.14 [0.1000]", "7.76 [0.6520]", "154.10 [<0.0001]"],
            ["HNX-Index", "-2.45 [0.1290]", "1.46 [0.0100]", "-16.52 [<0.0001]", "0.21 [0.1000]", "18.88 [0.0418]", "165.41 [<0.0001]"],
            ["USD/VND Exchange Rate", "-0.09 [0.9510]", "5.37 [0.0100]", "-14.79 [<0.0001]", "0.17 [0.1000]", "141.48 [<0.0001]", "430.49 [<0.0001]"],
            ["Brent Crude Oil", "-2.27 [0.1830]", "1.52 [0.0100]", "-39.05 [<0.0001]", "0.23 [0.1000]", "19.66 [0.0326]", "183.95 [<0.0001]"],
            ["US 10Y Treasury Yield", "-1.37 [0.5980]", "4.89 [0.0100]", "-17.65 [<0.0001]", "0.16 [0.1000]", "15.56 [0.1130]", "75.83 [<0.0001]"],
        ],
        col_widths_dxa=[1550, 1250, 1250, 1300, 1250, 1200, 1272],
        font_size_half_pt=19,
    ))
    add_p("", space_after=40)

    # =========================================================================
    # 4. METHODOLOGY
    # =========================================================================
    add_h1("4. Methodology")
    add_p(
        "To model short-run dynamics, we estimate a p-lag Vector Autoregression, VAR(p), on the stationary "
        "4 x 1 vector y_t = [dUS10Y_t, r_OIL,t, r_USDVND,t, r_VN,t]', where r_VN,t is the daily log return on "
        "the VN composite index (Sims, 1980): y_t = c + A_1 y_{t-1} + ... + A_p y_{t-p} + u_t, where c is a "
        "4 x 1 vector of intercepts, A_k are 4 x 4 coefficient matrices, and u_t is a mean-zero innovation "
        "vector with covariance matrix Sigma_u. The lag order p is selected by minimising the Akaike Information "
        "Criterion (AIC) over p in {0, 1, ..., 10}, compared alongside HQIC and BIC. Variable j Granger-causes "
        "variable i if the joint hypothesis H0: a_{ij,1} = ... = a_{ij,p} = 0 is rejected (Granger, 1969). "
        "Alongside standard F-tests, we check robustness to Newey–West heteroskedasticity- and autocorrelation-consistent "
        "(HAC) standard errors and to excluding the 10 observations that follow unscheduled vnstock provider gaps."
    )
    add_p(
        "Orthogonalised Impulse Response Functions (IRFs) and Forecast-Error Variance Decompositions (FEVDs) "
        "are computed from the Cholesky factorisation Sigma_u = P P' using the ordering dUS10Y -> r_OIL -> "
        "r_USDVND -> r_VN. This ordering places the global variables (the US 10-year Treasury yield and Brent "
        "crude oil) ahead of the managed USD/VND exchange rate, and places the domestic equity market last as "
        "the most endogenous small-open-economy variable (Kilian & Park, 2009). Because HOSE and HNX close at "
        "15:00 Hanoi time (08:00 UTC) before the US trading session, same-calendar-date US yield and Brent "
        "innovations are recorded after the Vietnamese close and take effect at horizon h >= 1. As a sensitivity "
        "check, we also compute the FEVD under the reversed Cholesky ordering (r_VN first; see also Pesaran & "
        "Shin, 1998, on ordering sensitivity)."
    )
    add_p(
        "To test for long-run equilibrium among the I(1) level series X_t = [log_composite_t, log_USDVND_t, "
        "log_OIL_t, DGS10_t]', we apply both pairwise Engle–Granger (1987) residual-based ADF tests (using "
        "MacKinnon, 2010, critical values) and system Johansen (1991) trace and maximum-eigenvalue cointegration "
        "tests with a restricted constant and k_{ar,diff} = p - 1 = 4 lagged differences. When cointegration of "
        "rank r = 1 is indicated, we estimate the Vector Error-Correction Model (VECM): Delta X_t = alpha "
        "(beta' X_{t-1} + c_0) + Sum_{m=1}^{4} Gamma_m Delta X_{t-m} + varepsilon_t, normalising the cointegrating "
        "vector beta on log_composite_t = 1 and examining the adjustment coefficients alpha and the implied "
        "half-life of deviations from equilibrium."
    )
    add_p(
        "Finally, we evaluate one-step-ahead out-of-sample return forecasts for the VN composite index over the "
        "last N_test = 500 trading days (25 September 2024 to 30 October 2026) using a rolling estimation window "
        "of W = 750 trading days (~3 years), refitted every 20 trading days using only data up to t - 1. We "
        "compare the rolling VAR against a univariate AR(1) model and a zero-drift random walk (forecasting "
        "zero return) using Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), the Campbell & Thompson "
        "(2008) out-of-sample R^2_OOS = 1 - MSE_model / MSE_RW, and the Diebold & Mariano (1995) test with the "
        "Harvey, Leybourne, & Newbold (1997) finite-sample adjustment (see Giacomini & White, 2006, on fixed-window "
        "forecast evaluation)."
    )

    # =========================================================================
    # 5. RESULTS
    # =========================================================================
    add_h1("5. Results")
    add_h2("5.1 VAR Lag Selection, Granger Causality, and Impulse Responses")
    add_p(
        "On the common sample, AIC selects p = 5 lags (AIC = -6.0442, one full trading week), HQIC selects p = 2 "
        "(-5.9956), and BIC selects p = 1 (-5.9469). We estimate the AIC-selected VAR(5) model (effective sample "
        "T_eff = 1,522). All companion-matrix eigenvalues lie well inside the unit circle (maximum modulus 0.70), "
        "confirming dynamic stability, and equation-by-equation Ljung–Box Q(10) tests on the VAR(5) residuals do "
        "not reject white noise in any equation (Q(10) = 0.24, p = 1.0000 for the VN composite index equation)."
    )
    add_p(
        "Table 4 (Panel A) reports the Granger causality tests from the VAR(5) system. Changes in the US 10-year "
        "Treasury yield significantly Granger-cause daily returns on the VN composite index (F = 3.30, p = 0.0056). "
        "To verify that this result is not driven by the 10 multi-day intervals following the 2020–2021 vnstock "
        "provider gaps or by heteroskedasticity, Panel A also reports the test after excluding those 10 rows "
        "(which strengthens the test to F = 3.78, p_OLS = 0.0021, p_HAC = 0.0421) as well as under the "
        "BIC-selected VAR(1) (F = 5.22, p_OLS = 0.0225, p_HAC = 0.0349). In addition, the US 10-year Treasury "
        "yield strongly Granger-causes the USD/VND exchange rate (F = 3.85, p = 0.0018, p_HAC = 0.0072), and "
        "returns on the VN composite index Granger-cause the USD/VND exchange rate (F = 3.36, p = 0.0049), "
        "consistent with portfolio-balance effects (Phylaktis & Ravazzolo, 2005). By contrast, neither Brent "
        "crude oil (F = 1.06, p = 0.3822) nor the USD/VND exchange rate (F = 0.46, p = 0.8086) Granger-causes "
        "returns on the VN composite index."
    )
    add_caption("Table 4: VAR(5) Granger Causality Tests and Impulse Responses of the VN Composite Index")
    body.append(make_table(
        headers=["Panel A: Granger Causality Pair / Check", "Lag p", "F-Stat.", "p-Value (OLS)", "p-Value (HAC)", "Inference at 5% Level"],
        rows=[
            ["dUS10Y -> r_VN (Baseline VAR(5), full sample)", "5", "3.30", "0.0056", "0.0717", "Significant (OLS 1%, HAC 10%)"],
            ["dUS10Y -> r_VN (VAR(5), excl. 10 provider-gap rows)", "5", "3.78", "0.0021", "0.0421", "Significant (both < 5%)"],
            ["dUS10Y -> r_VN (BIC-selected VAR(1), full sample)", "1", "5.22", "0.0225", "0.0349", "Significant (both < 5%)"],
            ["dUS10Y -> r_USDVND (US Yield -> Exchange Rate)", "5", "3.85", "0.0018", "0.0072", "Significant (both < 1%)"],
            ["r_VN -> r_USDVND (VN Composite -> Exchange Rate)", "5", "3.36", "0.0049", "0.1109", "Significant (OLS 1%)"],
            ["r_OIL -> r_VN (Brent Crude -> VN Composite)", "5", "1.06", "0.3822", "0.5433", "Not significant"],
            ["r_USDVND -> r_VN (Exchange Rate -> VN Composite)", "5", "0.46", "0.8086", "0.8180", "Not significant"],
            ["Panel B: Orthogonalised IRF of r_VN (%)", "h = 0", "h = 1", "h = 2", "h = 3", "h = 5 (1 Trading Week)"],
            ["Response of r_VN to 1-s.d. dUS10Y shock", "-0.0130%", "-0.0666%", "-0.0187%", "+0.0365%", "-0.0938%"],
            ["Response of r_VN to 1-s.d. r_OIL shock", "+0.0168%", "+0.0398%", "-0.0493%", "+0.0056%", "+0.0282%"],
            ["Response of r_VN to 1-s.d. r_USDVND shock", "-0.0370%", "-0.0006%", "+0.0138%", "+0.0273%", "-0.0221%"],
        ],
        col_widths_dxa=[2850, 900, 1050, 1250, 1250, 1772],
        font_size_half_pt=20,
    ))
    add_p(
        "Figure 5 and Table 4 (Panel B) show the orthogonalised impulse responses. Because the Vietnamese market "
        "closes before the US trading session on calendar date t, the contemporaneous (h = 0) response of the "
        "VN composite index to a one-standard-deviation (5.94 bps) increase in the US 10-year Treasury yield is "
        "close to zero (-0.0130%). The effect arrives on the following trading day (h = 1), where a 1-s.d. US "
        "yield shock reduces the VN composite index return by -0.0666%, followed by a second negative response "
        "at h = 5 (-0.0938%) before dying out by h = 10. Table 5 reports the Forecast-Error Variance Decomposition "
        "(FEVD) of the VN composite index under both the baseline Cholesky ordering and the reversed ordering "
        "(r_VN first). At horizon h = 20, own shocks account for 98.19% of the forecast-error variance of the "
        "VN composite index (98.25% under the reversed ordering), the US 10-year Treasury yield accounts for "
        "1.29% (1.11% reversed), Brent crude oil accounts for 0.33% (0.49% reversed), and the USD/VND exchange "
        "rate accounts for 0.19% (0.15% reversed). Thus, the decomposition is insensitive to the Cholesky ordering."
    )
    add_fig(5, "Figure 5: Orthogonalised Impulse Responses (with 95% Confidence Bands) from the VAR(5) Model.")
    add_caption("Table 5: Forecast-Error Variance Decomposition of the VN Composite Index and Ordering Sensitivity (%)")
    body.append(make_table(
        headers=["Horizon (Days)", "Cholesky Ordering", "dUS10Y (%)", "r_OIL (%)", "r_USDVND (%)", "r_VN Own (%)"],
        rows=[
            ["h = 1", "Baseline (dUS10Y -> r_OIL -> r_USDVND -> r_VN)", "0.01", "0.02", "0.09", "99.90"],
            ["h = 5", "Baseline (dUS10Y -> r_OIL -> r_USDVND -> r_VN)", "0.40", "0.29", "0.15", "99.13"],
            ["h = 10", "Baseline (dUS10Y -> r_OIL -> r_USDVND -> r_VN)", "1.28", "0.33", "0.19", "98.20"],
            ["h = 20", "Baseline (dUS10Y -> r_OIL -> r_USDVND -> r_VN)", "1.29", "0.33", "0.19", "98.19"],
            ["h = 20", "Reversed (r_VN -> r_USDVND -> r_OIL -> dUS10Y)", "1.11", "0.49", "0.15", "98.25"],
        ],
        col_widths_dxa=[1250, 3222, 1150, 1150, 1150, 1150],
        font_size_half_pt=20,
    ))
    add_p("", space_after=40)

    add_h2("5.2 Long-Run Equilibrium: Cointegration and VECM")
    add_p(
        "Table 6 presents the pairwise Engle–Granger tests, the joint four-variable Johansen cointegration tests "
        "(k_{ar,diff} = 4), and the rank-1 VECM estimates. Pairwise Engle–Granger tests fail to reject the null "
        "hypothesis of no cointegration between the log VN composite index and the log USD/VND exchange rate "
        "(ADF t = -1.99, p = 0.5315), log Brent crude oil (t = -1.78, p = 0.6403), or the US 10-year Treasury "
        "yield (t = -1.64, p = 0.7024). In the four-variable Johansen test, the trace statistic rejects r = 0 at "
        "the 5% level (51.99 > 47.85) and does not reject r <= 1 (25.70 < 29.80), pointing to one cointegrating "
        "relation (r = 1), whereas the maximum-eigenvalue statistic falls slightly below its 5% critical value "
        "(26.29 < 27.59). Estimating the rank-1 VECM normalised on log_composite_t = 1.0000 yields the long-run "
        "vector beta = [1.0000, -5.6806, -1.0452, +0.1915]'. However, the error-correction adjustment coefficient "
        "on the VN composite index is statistically indistinguishable from zero (alpha_VN = -0.0008, t = -0.35, "
        "p = 0.7280, implied partial half-life 842.8 trading days), whereas Brent crude oil adjusts significantly "
        "(alpha_OIL = +0.0236, t = 5.08, p < 0.0001; the AR(1) half-life of the error-correction term is 24.12 "
        "trading days). Consequently, the weak four-variable equilibrium does not exert a statistically "
        "significant error-correction pull on daily Vietnamese stock returns."
    )
    add_caption("Table 6: Engle–Granger Pairwise Tests, Johansen Cointegration Tests, and Rank-1 VECM Estimates")
    body.append(make_table(
        headers=["Test / Variable", "Hypothesis / Role", "Stat. / beta", "5% CV / alpha", "p-Val. / t-Stat.", "Conclusion / Interpretation"],
        rows=[
            ["Engle–Granger: log_USDVND", "H0: No cointegration", "t = -1.99", "—", "p = 0.5315", "No pairwise cointegration"],
            ["Engle–Granger: log_OIL", "H0: No cointegration", "t = -1.78", "—", "p = 0.6403", "No pairwise cointegration"],
            ["Engle–Granger: DGS10", "H0: No cointegration", "t = -1.64", "—", "p = 0.7024", "No pairwise cointegration"],
            ["Johansen Trace (r <= 0)", "H0: rank = 0", "51.99", "47.85", "Reject at 5%", "Indicates rank r = 1"],
            ["Johansen Trace (r <= 1)", "H0: rank <= 1", "25.70", "29.80", "Do not reject", "Consistent with r = 1"],
            ["Johansen Max-Eig (r <= 0)", "H0: rank = 0", "26.29", "27.59", "Do not reject", "Borderline below 5% CV"],
            ["VECM: log_composite", "Normalised Dep. Var.", "beta = 1.0000", "alpha = -0.0008", "t = -0.35 [0.7280]", "No equity error correction"],
            ["VECM: log_USDVND", "Exchange Rate", "beta = -5.6806", "alpha = +0.0004", "t = 0.70 [0.4860]", "Weakly exogenous in VECM"],
            ["VECM: log_OIL", "Brent Crude Oil", "beta = -1.0452", "alpha = +0.0236", "t = 5.08 [<0.0001]", "Oil adjusts toward equilibrium"],
            ["VECM: DGS10", "US 10Y Yield", "beta = +0.1915", "alpha = -0.0001", "t = -0.45 [0.6500]", "Strictly exogenous (alpha ~ 0)"],
        ],
        col_widths_dxa=[1800, 1450, 1250, 1250, 1350, 1972],
        font_size_half_pt=19,
    ))
    add_p("", space_after=40)

    add_h2("5.3 Out-of-Sample Forecast Comparison and Robustness (VN-Index Alone)")
    add_p(
        "Table 7 and Figure 6 report the 500-trading-day out-of-sample forecast evaluation (25 September 2024 "
        "to 30 October 2026). The rolling VAR produces an RMSE of 1.2448% and an MAE of 0.8368% (out-of-sample "
        "R^2_OOS = -1.60% relative to the random walk), compared with an RMSE of 1.2290% and MAE of 0.8299% for "
        "the univariate AR(1) (R^2_OOS = +0.96%) and an RMSE of 1.2349% and MAE of 0.8349% for the random walk. "
        "Diebold–Mariano tests find no statistically significant difference between the VAR and either benchmark "
        "at the 5% level under squared-error loss (DM = 1.71, p = 0.0883 vs. AR(1); DM = 0.94, p = 0.3500 vs. "
        "random walk) or absolute-error loss (DM = 1.25, p = 0.2135 vs. AR(1); DM = 0.29, p = 0.7733 vs. random "
        "walk). Although the US 10-year Treasury yield is statistically significant in sample, its 1.29% share "
        "of return variance is too small to overcome parameter estimation noise in daily out-of-sample point "
        "forecasts (Welch & Goyal, 2008; Campbell & Thompson, 2008)."
    )
    add_caption("Table 7: Out-of-Sample Forecast Comparison (2024-09-25 to 2026-10-30, N_test = 500, Rolling Window W = 750)")
    body.append(make_table(
        headers=["Model", "RMSE (%)", "MAE (%)", "RMSE / RW", "OOS R^2 (%)", "DM vs. VAR (MSE) [p]", "DM vs. VAR (MAE) [p]"],
        rows=[
            ["VAR (rolling AIC)", "1.2448", "0.8368", "1.0080", "-1.60", "Baseline model", "Baseline model"],
            ["AR(1) benchmark", "1.2290", "0.8299", "0.9952", "+0.96", "1.71 [0.0883]", "1.25 [0.2135]"],
            ["Random walk", "1.2349", "0.8349", "1.0000", "0.00", "0.94 [0.3500]", "0.29 [0.7733]"],
        ],
        col_widths_dxa=[1650, 1050, 1050, 1100, 1150, 1536, 1536],
        font_size_half_pt=20,
    ))
    add_fig(6, "Figure 6: Out-of-Sample Forecasts and Cumulative Squared Forecast Errors (2024-09-25 to 2026-10-30).")
    add_p(
        "Finally, Table 8 summarises Stage 6, where the entire analysis is re-run replacing the VN composite "
        "index with HOSE's VN-Index alone over 2020–2026 (N = 1,527), supplemented by an extended 10-year "
        "VN-Index check back to November 2016 (2016-11-02 to 2026-10-30, N = 2,384). Over the 2020–2026 sample, "
        "the VN composite index and VN-Index alone yield virtually identical results across every metric: AIC "
        "selects p = 5, the US 10-year Treasury yield Granger-causes equity returns with F = 3.28 (p = 0.0059 vs. "
        "F = 3.30, p = 0.0056 for the VN composite index), 20-day FEVD shares match to within 0.03 percentage "
        "points (98.22% own, 1.28% dUS10Y), and the VECM equity adjustment coefficient remains indistinguishable "
        "from zero (alpha = -0.0007, p = 0.7755). Extending VN-Index alone across the full 2016–2026 decade "
        "(N = 2,384) strengthens the Johansen cointegration tests (trace = 67.99 > 47.85; max-eig = 40.34 > "
        "27.59, both rejecting r = 0 at 5%), while confirming that short-run negative transmission from US "
        "Treasury yields to Vietnamese equities is primarily a post-2020 phenomenon."
    )
    add_caption("Table 8: Robustness Comparison Between the VN Composite Index and VN-Index Alone")
    body.append(make_table(
        headers=["Metric / Test", "VN Composite (2020–2026)", "VN-Index Only (2020–2026)", "VN-Index Extended (2016–2026)", "5% CV / Ref.", "Comparison"],
        rows=[
            ["Aligned Observations (N)", "1,527", "1,527", "2,384", "—", "Identical 2020–2026 window"],
            ["AIC / BIC Selected Lag", "p = 5 / p = 1", "p = 5 / p = 1", "p = 4 / p = 1", "maxlags = 10", "Identical lag order on 2020–2026"],
            ["Granger: dUS10Y -> Equity F [p]", "3.30 [0.0056]", "3.28 [0.0059]", "2.11 [0.0767]", "alpha = 0.05", "Significant at 1% on 2020–2026"],
            ["Granger: Equity -> r_USDVND F [p]", "3.36 [0.0049]", "3.31 [0.0054]", "2.89 [0.0212]", "alpha = 0.05", "Significant across all samples"],
            ["20-Day FEVD: Own / dUS10Y (%)", "98.19% / 1.29%", "98.22% / 1.28%", "98.91% / 0.45%", "—", "Diff <= 0.03 pp on 2020–2026"],
            ["Johansen Trace Stat. (r <= 0)", "51.99 (rank 1)", "52.00 (rank 1)", "67.99 (rank 1)", "47.85", "All reject r = 0 at 5%"],
            ["Johansen Max-Eig Stat. (r <= 0)", "26.29 (rank 0)", "26.23 (rank 0)", "40.34 (rank 1)", "27.59", "Full decade rejects on both tests"],
            ["VECM Equity alpha [p-Value]", "-0.0008 [0.7280]", "-0.0007 [0.7755]", "-0.0011 [0.5120]", "H0: alpha = 0", "Zero equity adjustment in all cases"],
        ],
        col_widths_dxa=[2050, 1450, 1450, 1550, 1050, 1522],
        font_size_half_pt=19,
    ))
    add_p("", space_after=40)

    # =========================================================================
    # 6. CONCLUSION
    # =========================================================================
    add_h1("6. Conclusion")
    add_p(
        "This essay investigated the short-run dynamic interactions, long-run cointegration, and out-of-sample "
        "forecasting performance linking daily returns on the VN composite index to the USD/VND exchange rate, "
        "the US 10-year Treasury yield, and Brent crude oil prices from June 2020 to October 2026 (N = 1,527). "
        "In the short run, changes in the US 10-year Treasury yield are the primary external influence on the "
        "Vietnamese stock market: lagged US yield changes significantly Granger-cause both the VN composite "
        "index return (F = 3.30, p = 0.0056; F = 3.78, p = 0.0021 when excluding the 10 post-provider-gap rows) "
        "and the USD/VND exchange rate (F = 3.85, p = 0.0018), with a one-standard-deviation (5.94 bps) US yield "
        "increase lowering the VN composite index return by -0.0666% at h = 1 and -0.0938% at h = 5. Conversely, "
        "returns on the VN composite index Granger-cause the USD/VND exchange rate (F = 3.36, p = 0.0049), "
        "whereas neither Brent crude oil (p = 0.3822) nor the USD/VND exchange rate (p = 0.8086) directly "
        "Granger-causes equity returns, and all three macro series together explain 1.81% of 20-day equity "
        "forecast-error variance. In the long run, pairwise Engle–Granger tests find no cointegration, and "
        "although the four-variable Johansen trace test indicates one cointegrating relation (trace = 51.99), "
        "the equity error-correction coefficient in the VECM is statistically zero (alpha_VN = -0.0008, "
        "p = 0.7280). Out of sample over 500 trading days, the VAR does not improve point-forecast accuracy "
        "over a univariate AR(1) or a random walk."
    )
    add_p(
        "From a practical perspective, these results imply that static linear currency or oil futures hedges "
        "provide very limited daily variance reduction for a broadly diversified Vietnamese equity portfolio, "
        "as direct exchange-rate and oil shocks account for less than 0.60% of 20-day return variance. At the "
        "same time, because US Treasury yield changes affect both Vietnamese stock returns and the USD/VND "
        "exchange rate over a one-to-five-day horizon, portfolio managers and bank risk analysts should monitor "
        "US monetary policy and bond-yield movements as a shared source of short-run equity and exchange-rate "
        "risk, while relying on parsimonious univariate models rather than multi-lag VARs for day-ahead return "
        "prediction. Four limitations suggest directions for further study: (1) HNX-Index availability in "
        "vnstock begins in May 2020, though our VN-Index-only robustness checks confirm that excluding HNX does "
        "not alter the results; (2) 28 unscheduled vnstock provider gaps occur in 2020–2021, which we verified "
        "do not drive our Granger causality findings; (3) the VAR residuals retain strong ARCH volatility "
        "clustering (which a Student-t GARCH(1,1) filter absorbs in auxiliary table tab32_var_resid_garch.csv, "
        "motivating a multivariate GARCH or asymmetric GJR-GARCH extension as in Glosten, Jagannathan, & Runkle, "
        "1993); and (4) the State Bank of Vietnam's crawling exchange-rate band and shifting global monetary "
        "regimes (documented in auxiliary table tab31_subsample_stability.csv) motivate nonlinear threshold or "
        "regime-switching models in future work."
    )

    # =========================================================================
    # PAGE BREAK BEFORE REFERENCES & APPENDICES (Excluded from <= 15-page cap)
    # Aligned 1-for-1 with docs/references.md
    # =========================================================================
    body.append(make_page_break())
    add_h1("References")
    refs = [
        "[TODO: Insert the assigned ATFB (NHAE408) course textbook citation from the course syllabus before submission.]",
        "Christoffersen, P. F. (2012). Elements of Financial Risk Management (2nd ed.). Academic Press (Elsevier). ISBN: 978-0-12-374448-7. [Supplementary course text]",
        "ATFB (NHAE408) Course Repository. (2026). Midterm/midterm_template.ipynb, Midterm/report_template.docx, and Midterm/ATFB_Midterm_Brief.pdf. Foreign Trade University – Ho Chi Minh City Campus. [Adapted template code]",
        "1. Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. Journal of Econometrics, 31(3), 307–327. https://doi.org/10.1016/0304-4076(86)90063-1",
        "2. Campbell, J. Y., & Thompson, S. B. (2008). Predicting excess stock returns out of sample: Can anything beat the historical average? The Review of Financial Studies, 21(4), 1509–1531. https://doi.org/10.1093/rfs/hhm055",
        "3. Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. Journal of Business & Economic Statistics, 13(3), 253–263. https://doi.org/10.1198/073500102753410444",
        "4. Dornbusch, R., & Fischer, S. (1980). Exchange rates and the current account. The American Economic Review, 70(5), 960–971. https://www.jstor.org/stable/1805775",
        "5. Engle, R. F., & Granger, C. W. J. (1987). Co-integration and error correction: Representation, estimation, and testing. Econometrica, 55(2), 251–276. https://doi.org/10.2307/1913236",
        "6. Giacomini, R., & White, H. (2006). Tests of conditional predictive ability. Econometrica, 74(6), 1545–1578. https://doi.org/10.1111/j.1468-0262.2006.00718.x",
        "7. Glosten, L. R., Jagannathan, R., & Runkle, D. E. (1993). On the relation between the expected value and the volatility of the nominal excess return on stocks. The Journal of Finance, 48(5), 1779–1801. https://doi.org/10.1111/j.1540-6261.1993.tb05128.x",
        "8. Granger, C. W. J. (1969). Investigating causal relations by econometric models and cross-spectral methods. Econometrica, 37(3), 424–438. https://doi.org/10.2307/1912791",
        "9. Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction mean squared errors. International Journal of Forecasting, 13(2), 281–291. https://doi.org/10.1016/S0169-2070(96)00719-4",
        "10. Hussainey, K., & Ngoc, L. K. (2009). The impact of macroeconomic indicators on Vietnamese stock prices. The Journal of Risk Finance, 10(4), 321–332. https://doi.org/10.1108/15265940910980632",
        "11. Johansen, S. (1991). Estimation and hypothesis testing of cointegration vectors in Gaussian vector autoregressive models. Econometrica, 59(6), 1551–1580. https://doi.org/10.2307/2938278",
        "12. Kilian, L., & Park, C. (2009). The impact of oil price shocks on the U.S. stock market. International Economic Review, 50(4), 1267–1287. https://doi.org/10.1111/j.1468-2354.2009.00568.x",
        "13. MacKinnon, J. G. (2010). Critical values for cointegration tests (Queen's Economics Department Working Paper No. 1227). Queen's University. https://ideas.repec.org/p/qed/wpaper/1227.html",
        "14. Miranda-Agrippino, S., & Rey, H. (2020). U.S. monetary policy and the global financial cycle. The Review of Economic Studies, 87(6), 2754–2776. https://doi.org/10.1093/restud/rdaa019",
        "15. Narayan, P. K., & Narayan, S. (2010). Modelling the impact of oil prices on Vietnam's stock prices. Applied Energy, 87(1), 356–361. https://doi.org/10.1016/j.apenergy.2009.05.037",
        "16. Nguyen, C. C., & Bhatti, M. I. (2012). Copula model dependency between oil prices and stock markets: Evidence from China and Vietnam. Journal of International Financial Markets, Institutions and Money, 22(4), 758–773. https://doi.org/10.1016/j.intfin.2012.05.008",
        "17. Pesaran, H. H., & Shin, Y. (1998). Generalized impulse response analysis in linear multivariate models. Economics Letters, 58(1), 17–29. https://doi.org/10.1016/S0165-1765(97)00214-0",
        "18. Phylaktis, K., & Ravazzolo, F. (2005). Stock prices and exchange rate dynamics. Journal of International Money and Finance, 24(7), 1031–1053. https://doi.org/10.1016/j.jimonfin.2005.08.001",
        "19. Sadorsky, P. (1999). Oil price shocks and stock market activity. Energy Economics, 21(5), 449–469. https://doi.org/10.1016/S0140-9883(99)00020-1",
        "20. Sims, C. A. (1980). Macroeconomics and reality. Econometrica, 48(1), 1–48. https://doi.org/10.2307/1912017",
        "21. Welch, I., & Goyal, A. (2008). A comprehensive look at the empirical performance of equity premium prediction. The Review of Financial Studies, 21(4), 1455–1508. https://doi.org/10.1093/rfs/hhm014",
        "Data Feeds & Market-Cap Sources: Vu, T. (2024), vnstock Python toolkit (v0.2.9.2.3, commit e8339514, https://github.com/thinh-vu/vnstock); Yahoo Finance (USDVND=X, BZ=F); Federal Reserve Bank of St. Louis FRED (DGS10); HOSE & HNX May 2020 market-capitalisation statistics (Thoi bao Tai chinh Viet Nam, 2020-06-04; Bao Moi / HNX, 2020-06-03; see docs/references.md for full URLs).",
    ]
    for r_str in refs:
        add_p(r_str, align="left", space_after=45, line_spacing=260, font_size_half_pt=21)

    body.append(make_page_break())
    add_h1("Appendix A. Contribution of each member")
    add_p(
        "TODO (Group to review and adjust before submission): The table below splits 'Share of the work (%)' "
        "evenly at 25% per member as a placeholder. Before submitting to Microsoft Teams, the group should "
        "update the task descriptions and percentage shares to reflect each member's actual contribution, as "
        "these shares affect individual peer-review marks. Each member also completes the peer-review form on "
        "Microsoft Teams."
    )
    body.append(make_table(
        headers=["Full name", "Student ID", "Tasks", "Share of the work (%)"],
        rows=[
            ["Hoàng Phương Linh", "2412345011", "[TODO: Confirm/adjust tasks — e.g., Data pipeline, alignment & EDA]", "25%"],
            ["Võ Như Ý", "2412345017", "[TODO: Confirm/adjust tasks — e.g., VAR(5) estimation, Granger & IRF/FEVD]", "25%"],
            ["Lê Khánh Mỹ Linh", "2412345040", "[TODO: Confirm/adjust tasks — e.g., Cointegration, VECM & VN-Index robustness]", "25%"],
            ["Trương Bảo Thư", "2412345083", "[TODO: Confirm/adjust tasks — e.g., Out-of-sample forecasting & report editing]", "25%"],
            ["Total", "—", "All stages reviewed and verified by all group members", "100%"],
        ],
        col_widths_dxa=[2268, 1600, 3604, 1600],
        font_size_half_pt=20,
    ))

    add_h1("Appendix B. Use of generative AI")
    add_p(
        "In accordance with Section 8 of the ATFB (NHAE408) Midterm Essay Brief, the table below records how "
        "generative AI tools were used during the project and how the group verified their outputs."
    )
    body.append(make_table(
        headers=["Tool (Name & Version)", "Used for", "How the output was checked"],
        rows=[
            [
                "Google DeepMind Antigravity Agent (2026)",
                "Refactoring modular Python code in src/, automating unit tests in tests/test_pipeline.py, and formatting tables and figures.",
                "All econometric outputs were checked against statsmodels documentation and verified with 10 unit tests on synthetic data with known analytical results.",
            ],
            [
                "Google DeepMind Antigravity Agent (2026)",
                "Verifying bibliographic metadata (DOIs, journals, volume/page numbers) and polishing English prose.",
                "Every reference in References and docs/references.md was verified via live DOI/publisher lookup; 10 vnstock index dates were checked against published market reports (0.00 pt difference); src/check_report_numbers.py verified every number in the report against results/tables/*.csv.",
            ],
        ],
        col_widths_dxa=[2200, 3200, 3672],
        font_size_half_pt=20,
    ))

    add_h1("Appendix C. Reproducibility and data manifest")
    add_p(
        "Per Section 4 of the ATFB Midterm Essay Brief, Appendix A contains the Member Contribution Table and "
        "Appendix B contains the Generative-AI Statement; reproducibility notes are therefore provided here in "
        "Appendix C (and in README.md and docs/data_manifest.md). Running python run_all.py (or Restart & Run All "
        "in notebooks/t7_macro_links.ipynb) on Python 3.13.3 reproduces all data files, tables, and figures end "
        "to end. Per vnstock terms of use, raw and processed data CSVs are excluded from the public git repository "
        "via .gitignore and are packaged only in the private course submission archive (ATFB_Essay_Group12_code.zip)."
    )
    body.append(make_table(
        headers=["Raw Data File (data/raw/)", "Source & Symbol", "Rows", "Sample Window", "SHA-256 Prefix (First 24 Hex Chars)"],
        rows=[
            ["vnindex_raw.csv", "vnstock DNSE (VNINDEX)", "1,576", "2020-06-01 .. 2026-10-30", "ee9de5a5e440fa9cc20e2cb7"],
            ["hnxindex_raw.csv", "vnstock DNSE (HNX)", "1,577", "2020-06-01 .. 2026-10-30", "17a860f4aa087c079335e4f5"],
            ["usdvnd_raw.csv", "yfinance (USDVND=X)", "1,671", "2020-06-01 .. 2026-10-30", "c730a86a87f24be775cf1c46"],
            ["oil_raw.csv", "yfinance (BZ=F)", "1,615", "2020-06-01 .. 2026-10-30", "461586c1f19a91ec3ab83333"],
            ["dgs10_raw.csv", "FRED (DGS10)", "1,685", "2020-05-18 .. 2026-10-30", "25ba476347380f28b06ca593"],
            ["vnindex_ext2016_raw.csv", "vnstock DNSE (VNINDEX 10Y)", "2,473", "2016-11-01 .. 2026-10-30", "51071e46872d78c181d5c2b9"],
        ],
        col_widths_dxa=[2100, 2100, 750, 1922, 2200],
        font_size_half_pt=19,
    ))

    if sect_pr is not None:
        body.append(sect_pr)

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("word/document.xml", ET.tostring(doc_root, encoding="utf-8", xml_declaration=True))
        zout.writestr("word/_rels/document.xml.rels", ET.tostring(rels_root, encoding="utf-8", xml_declaration=True))
        zout.writestr("[Content_Types].xml", ET.tostring(ct_root, encoding="utf-8", xml_declaration=True))
        for name, data in other_items.items():
            zout.writestr(name, data)
        for img_name, (png_bytes, _, _) in figs.items():
            zout.writestr(f"word/media/{img_name}", png_bytes)

    print(f"Built {out_path} ({out_path.stat().st_size:,} bytes) successfully.")
    return out_path


if __name__ == "__main__":
    build_report_docx()
