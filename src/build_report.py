"""Build report/ATFB_Essay_Group12.docx from report/report_template.docx.

Preserves A4 page setup, 2.5 cm margins, 12 pt Times New Roman body font, 1.5 line spacing,
and template styles (Heading1, Heading2, Normal, TableGrid), while populating all sections,
8 formatted summary tables, and 6 embedded figures using canonical numbers from results/tables/.
"""

import io
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config
from src import report_numbers as rn

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
           align: str = "", space_after: int = 120, space_before: int = 0,
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
               font_size_half_pt: int = 19) -> ET.Element:
    """Create a compact, clean academic Word table (9.5 pt cells, 1.15 spacing)."""
    total_w = 9072
    ncols = len(headers)
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
                space_after=6,
                space_before=6,
                line_spacing=205,
                font_size_half_pt=font_size_half_pt,
            )
            tc.append(p)

    _add_row(headers, is_header=True)
    for r in rows:
        _add_row(r, is_header=False)
    return tbl


def make_figure_p(rel_id: str, doc_pr_id: int, img_name: str,
                  cx_emu: int, cy_emu: int) -> ET.Element:
    """Create a centered paragraph containing an inline DrawingML picture."""
    xml_str = f"""
    <w:p xmlns:w="{W_NS}" xmlns:r="{R_NS}" xmlns:wp="{WP_NS}" xmlns:a="{A_NS}" xmlns:pic="{PIC_NS}">
      <w:pPr>
        <w:spacing w:before="60" w:after="40" w:line="240" w:lineRule="auto"/>
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


def prepare_composite_figures() -> dict[str, tuple[bytes, int, int]]:
    """Load figures and build compact side-by-side panels to fit the <= 15-page main-text cap."""
    fig_dir = config.FIG_DIR

    def _stack_horizontal(p1: Path, p2: Path, target_h_px: int = 620) -> bytes:
        im1 = Image.open(p1).convert("RGB")
        im2 = Image.open(p2).convert("RGB")
        w1 = int(im1.width * (target_h_px / im1.height))
        w2 = int(im2.width * (target_h_px / im2.height))
        im1_r = im1.resize((w1, target_h_px), Image.Resampling.LANCZOS)
        im2_r = im2.resize((w2, target_h_px), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (w1 + w2 + 24, target_h_px), (255, 255, 255))
        canvas.paste(im1_r, (0, 0))
        canvas.paste(im2_r, (w1 + 24, 0))
        buf = io.BytesIO()
        canvas.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    fig_specs = [
        ("image1.png", (fig_dir / "fig01_composite_construction.png").read_bytes(), 3900000),
        ("image2.png", (fig_dir / "fig02_levels_and_returns.png").read_bytes(), 3700000),
        ("image3.png", _stack_horizontal(fig_dir / "fig03_qq_plots.png", fig_dir / "fig04_acf_returns_squared.png"), 5200000),
        ("image4.png", (fig_dir / "fig09_var_irf_ordering_girf.png").read_bytes(), 4100000),
        ("image5.png", (fig_dir / "fig07_vecm_error_correction_term.png").read_bytes(), 4000000),
        ("image6.png", _stack_horizontal(fig_dir / "fig08_forecast_comparison.png", fig_dir / "fig10_subsample_irf_stability.png"), 5200000),
    ]

    out = {}
    for name, png_bytes, target_cx in fig_specs:
        im = Image.open(io.BytesIO(png_bytes))
        w_px, h_px = im.size
        cy = int(target_cx * (h_px / w_px))
        out[name] = (png_bytes, target_cx, cy)
    return out


def build_report_docx() -> Path:
    template_path = ROOT / "report" / "report_template.docx"
    out_path = ROOT / "report" / "ATFB_Essay_Group12.docx"
    assert template_path.exists(), f"Missing template: {template_path}"

    figs = prepare_composite_figures()

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
              align: str = "both", space_after: int = 35, space_before: int = 0,
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
        add_p(text=text, style="Heading1", align="left", space_before=80, space_after=30, line_spacing=260, keep_next=True)

    def add_h2(text: str):
        add_p(text=text, style="Heading2", align="left", space_before=60, space_after=20, line_spacing=250, keep_next=True)

    def add_caption(text: str, space_before: int = 20, space_after: int = 15, keep_next: bool = True):
        add_p(text=text, bold=True, italic=False, align="left",
              space_before=space_before, space_after=space_after,
              line_spacing=220, font_size_half_pt=19, keep_next=keep_next)

    def add_fig(idx: int, caption: str):
        img_name = f"image{idx}.png"
        _, cx, cy = figs[img_name]
        body.append(make_figure_p(f"rId{9 + idx}", 100 + idx, img_name, cx, cy))
        add_caption(caption, space_before=10, space_after=30, keep_next=False)

    # =========================================================================
    # TITLE PAGE (Excluded from the 15-page main-text count)
    # =========================================================================
    add_p("FOREIGN TRADE UNIVERSITY – HO CHI MINH CITY CAMPUS", bold=True, align="center", space_after=120, font_size_half_pt=24)
    add_p("Applied Technology in Finance and Banking (NHAE408)", bold=False, align="center", space_after=900, font_size_half_pt=24)
    add_p("MIDTERM GROUP ESSAY", bold=True, align="center", space_after=160, font_size_half_pt=28)
    add_p(
        "Macro-Financial Links in Vietnam: Dynamic Transmission, Cointegration, and Out-of-Sample Predictability of Stock Returns with USD/VND, US Interest Rates, and Brent Crude Oil",
        bold=True, align="center", space_after=480, font_size_half_pt=30,
    )
    add_p("Topic: T7 (Macro-financial links)   ·   Group: 12 (confirm/replace)", bold=False, align="center", space_after=480, font_size_half_pt=24)

    body.append(make_table(
        headers=["No.", "Full name", "Student ID"],
        rows=[
            ["1", "[TODO: Fill in manually before submission]", "[TODO]"],
            ["2", "[TODO: Fill in manually before submission]", "[TODO]"],
            ["3", "[TODO: Fill in manually before submission]", "[TODO]"],
            ["4", "[TODO: Fill in manually before submission]", "[TODO]"],
            ["5", "[TODO: Fill in manually before submission]", "[TODO]"],
        ],
        col_widths_dxa=[1200, 4672, 3200],
        font_size_half_pt=22,
    ))
    add_p("", space_after=360)
    add_p("Instructors: Dr. Lê Trung Thành, Dr. Nguyễn Thị Hoàng Anh", align="center", space_after=120, font_size_half_pt=24)
    add_p("Ho Chi Minh City, November 2026", align="center", space_after=120, font_size_half_pt=24)
    body.append(make_page_break())

    # =========================================================================
    # ABSTRACT (Strictly <= 200 words; target ~165 words)
    # =========================================================================
    add_h1("Abstract")
    abstract_text = (
        "This essay investigates how daily Vietnamese equity returns interact with the USD/VND exchange rate, "
        "the US 10-year Treasury yield (DGS10), and Brent crude oil prices (BZ=F) across N = 1,527 aligned "
        "trading days from June 2020 to October 2026, supplemented by a 10-year VN-Index check from November "
        "2016 (N = 2,384). We construct a start-of-sample market-capitalisation-weighted composite of HOSE "
        "(93.78%) and HNX (6.22%) and estimate a five-lag vector autoregression (VAR(5)) on returns/differences "
        "alongside Engle–Granger and Johansen cointegration tests and a rank-1 vector error-correction model "
        "(VECM) on log levels. Short-run changes in the US 10-year yield significantly Granger-cause Vietnamese "
        "equity returns (F = 3.30, p = 0.0056) and USD/VND movements (F = 3.85, p = 0.0018), depressing equities "
        "by -0.0666% at h = 1 and -0.0938% at h = 5 per one-standard-deviation shock, whereas direct oil and "
        "FX lags are insignificant and macro shocks explain 1.81% of 20-day equity variance. Joint cointegration "
        "is weak (trace = 51.99, max-eigenvalue = 26.29) with zero equity error-correction adjustment "
        "(alpha = -0.0008, p = 0.728). Over a 500-day rolling out-of-sample window, Diebold–Mariano tests find "
        "no significant accuracy gain for the VAR over an AR(1) or random walk."
    )
    add_p(abstract_text)
    add_p(
        runs=[
            ("Keywords: ", True, False),
            ("Vietnamese stock market; VAR; cointegration; VECM; Generalized IRF; Diebold–Mariano test.", False, True),
        ],
        space_after=120,
    )

    # =========================================================================
    # 1. INTRODUCTION
    # =========================================================================
    add_h1("1. Introduction")
    add_p(
        "As a rapidly growing, trade-intensive small open economy, Vietnam's equity market is exposed to global "
        "monetary conditions, exchange-rate fluctuations, and international energy prices. Understanding the "
        "direction, timing, and magnitude of these macro-financial linkages is central to three practical tasks: "
        "(i) commercial bank treasury and asset-liability management (ALM) desks calibrating joint stress tests "
        "across foreign-exchange (FX) liquidity and equity-backed margin lending; (ii) domestic and foreign fund "
        "managers deciding whether to overlay USD/VND or commodity hedges onto Vietnamese equity portfolios; and "
        "(iii) quantitative analysts evaluating whether macroeconomic indicators improve daily equity return "
        "forecasts out of sample. This study answers Topic 7 of the ATFB (NHAE408) Midterm Essay: How are "
        "Vietnamese stock returns related to the USD/VND exchange rate, US interest rates (10-year Treasury "
        "yield), and Brent crude oil prices in both the short run and the long run, and do these linkages "
        "translate into superior out-of-sample return forecasts?"
    )
    add_p(
        "Theoretical and empirical literature identifies three primary transmission channels. First, the "
        "exchange-rate and trade competitiveness channel (Dornbusch & Fischer, 1980; Phylaktis & Ravazzolo, 2005) "
        "links currency depreciation to export revenues and foreign-currency balance-sheet liabilities, while the "
        "stock-oriented portfolio-balance channel (Branson, 1983) predicts reverse causality from domestic equity "
        "returns to FX rates via foreign capital flows. Second, the Global Financial Cycle and discount-rate "
        "channel (Rey, 2015; Bernanke & Kuttner, 2005; Cushman & Zha, 1997) posits that US Treasury yield shocks "
        "tighten global dollar funding, raise risk premia, and compress emerging-market equity valuations, while "
        "simultaneously pressuring managed exchange rates such as the State Bank of Vietnam's (SBV) crawling "
        "USD/VND band. Third, the energy-cost and aggregate-demand channel (Jones & Kaul, 1996; Kilian & Park, "
        "2009) distinguishes cost-push oil supply shocks from global demand-driven oil rallies. Prior Vietnamese "
        "studies (Narayan & Narayan, 2010; Nguyen & Bhatti, 2012; Sui & Sun, 2016; Batten, Kinateder, Szilagyi, "
        "& Wagner, 2019; Vo, 2017) document time-varying comovement among oil, USD/VND, and the Ho Chi Minh Stock "
        "Exchange (HOSE) VN-Index, but typically focus on pre-2020 samples, omit the Hanoi Stock Exchange (HNX), "
        "or rely solely on in-sample homoskedastic tests without out-of-sample forecast validation."
    )
    add_p(
        "We advance this empirical literature in four ways. First, anticipating the regulatory consolidation of "
        "HOSE and HNX equities under Circular 69/2023/TT-BTC by December 2026, we construct a fixed start-of-sample "
        "market-capitalisation-weighted composite index combining VN-Index (93.78%) and HNX-Index (6.22%) over "
        "N = 1,527 aligned trading days from 2 June 2020 to 30 October 2026, and verify our results against a "
        "full 10-year VN-Index-only sample from November 2016 (N = 2,384). Second, we pair a five-lag vector "
        "autoregression (VAR(5)) with White HC3, Newey–West HAC, Rademacher Wild Bootstrap (Gonçalves & Kilian, "
        "2004), and Holm (1979) multiple-testing corrections, alongside Pesaran & Shin (1998) order-invariant "
        "Generalized Impulse Response Functions (GIRFs) and a Student-t GARCH(1,1) / GJR-GARCH(1,1) residual "
        "filter. Third, we test long-run equilibrium via pairwise Engle–Granger (1987) and system Johansen (1991) "
        "trace and maximum-eigenvalue tests and estimate a rank-1 Vector Error-Correction Model (VECM). Fourth, "
        "following Welch & Goyal (2008), Campbell & Thompson (2008), and Giacomini & White (2006), we evaluate "
        "500 one-step-ahead rolling out-of-sample forecasts against univariate AR(1) and random-walk benchmarks "
        "using Diebold & Mariano (1995) tests with the Harvey, Leybourne, & Newbold (1997) finite-sample adjustment."
    )

    # =========================================================================
    # 2. DATA
    # =========================================================================
    add_h1("2. Data")
    add_p(
        "All data series are retrieved programmatically via src/data.py into data/raw/ with SHA-256 integrity "
        "hashes recorded in Appendix C. Vietnamese equity indices—the HOSE VN-Index (symbol VNINDEX) and the "
        "HNX-Index (symbol HNX)—are sourced from the vnstock Python library (DNSE Entrade endpoint, pinned at "
        "commit e8339514; Yahoo Finance is excluded because it lacks a verified VN-Index feed). Daily spot "
        "exchange rates (USDVND=X, VND per USD) and front-month Brent crude futures (BZ=F, USD per barrel) are "
        "pulled from Yahoo Finance via yfinance. Brent crude misses only 1.98% of weekdays over the sample—well "
        "below our 5.0% completeness threshold—so no WTI (CL=F) fallback is triggered. The US 10-year Treasury "
        "constant-maturity yield (DGS10, % per annum) is retrieved from Federal Reserve Economic Data (FRED)."
    )
    add_p(
        "Although our target window spans 1 November 2016 to 31 October 2026, the upstream vnstock DNSE feed "
        "provides HNX-Index daily history starting on 11 May 2020 (while VN-Index is available across the full "
        "decade). Following the longest common window principle across all five series, our baseline sample "
        "begins on 1 June 2020 ( yielding N = 1,527 aligned daily return observations from 2 June 2020 to "
        "30 October 2026, more than six years of daily data and well above the course minimum of three years). "
        "Section 5.5 then re-estimates the system on the 10-year VN-Index-only panel (2016-11-02 to 2026-10-30, "
        "N = 2,384). To avoid look-ahead bias, we weight the composite return r_composite,t = w_HOSE * r_VNINDEX,t "
        "+ w_HNX * r_HNXINDEX,t using official end-May 2020 domestic market capitalisations published by HOSE "
        "(3,010,000 billion VND, w_HOSE = 93.78%) and HNX (199,800 billion VND, w_HNX = 6.22%). As shown in "
        "Figure 1, the composite and VN-Index series exhibit a daily return correlation of 0.9993 (and log-level "
        "correlation of 0.9997) with a mean absolute daily return difference of just 0.038 percentage points."
    )
    add_fig(1, "Figure 1: Market-Cap-Weighted VN Composite vs. HOSE VN-Index and HNX-Index (Rebased to 100 on 2020-06-02) and Daily Return Difference.")
    add_p(
        "Table 1 summarises source coverage, calendar alignment, and data-cleaning decisions. The reference "
        "calendar is the intersection of trading days on which both VN-Index and HNX-Index trade (1,576 common "
        "days out of 1,675 calendar weekdays). Cross-checking the 99 missing weekdays against State Securities "
        "Commission (SSC) and HOSE schedules identifies 71 statutory Vietnamese public holidays (primarily five-day "
        "Tết Nguyên Đán closures, Reunification/Labour Day on 30 April–1 May, and National Day on 2 September) "
        "and 28 unscheduled vnstock (DNSE) provider gaps concentrated in three early clusters between July 2020 "
        "and July 2021 (10 multi-day return intervals, zero gaps after July 2021). Traded asset prices (USDVND=X "
        "and BZ=F) are aligned to the Vietnamese calendar via an inner join without forward-filling to prevent "
        "artificial zero-return streaks followed by catch-up jumps; this drops 48 VN trading days (47 US/UK "
        "holidays without Brent quotes, 3 days without USD/VND quotes, 2 overlapping), leaving 1,528 aligned "
        "level dates and N = 1,527 synchronised return rows. Only DGS10—a policy/reference yield—is forward-filled "
        "across 59 US bond-market holidays (e.g., Juneteenth, Columbus Day, Veterans Day). Log returns "
        "r_t = 100 * ln(P_t / P_{t-1}) and yield changes dUS10Y_t = DGS10_t - DGS10_{t-1} (in percentage points) "
        "are computed strictly after alignment so that every row spans the exact same calendar interval across "
        "all four variables."
    )
    add_p(
        "Because VN-Index and HNX-Index are aggregate capital-appreciation indices, individual stock splits are "
        "absorbed by exchange divisor adjustments, and zero-volume days do not occur at the index level. Inspection "
        "of daily simple returns exceeding HOSE's +-7% daily price limit (HNX limit +-10%) flags two HNX dates: "
        "18 January 2022 (-9.80%, a two-day return spanning a dropped Martin Luther King Jr. Day) and 22 April "
        "2025 (+8.08%, a genuine broad rebound within HNX's +-10% band). Both are retained. Finally, cross-checking "
        "vnstock closes against 10 independently published year-end and milestone market reports (2020–2025) "
        "confirms a 0.00-point discrepancy across all 20 index checkpoints (Table 1, Panel B)."
    )
    add_caption("Table 1: Data Sources, Calendar Alignment, Series Quality Diagnostics, and Cross-Validation Summary")
    body.append(make_table(
        headers=["Series / Metric", "Source & Symbol", "Raw Obs (Window)", "Alignment Rule & Losses", "Aligned Obs (N)", "Zero-Move Days (%)", "Min / Max Daily Move"],
        rows=[
            ["VN-Index (HOSE)", "vnstock (VNINDEX)", "1,576", "Reference calendar (71 VN holidays + 28 provider gaps)", "1,527", "2 (0.13%)", "-6.95% / +6.44%"],
            ["HNX-Index (HNX)", "vnstock (HNX)", "1,576", "Reference calendar (starts 2020-05-11)", "1,527", "5 (0.33%)", "-10.31% / +7.77%"],
            ["VN Composite", "0.9378*HOSE + 0.0622*HNX", "1,576", "Fixed May-2020 mcap weights (3,010,000 & 199,800 bn VND)", "1,527", "0 (0.00%)", "-6.95% / +6.63%"],
            ["USD/VND Spot", "yfinance (USDVND=X)", "1,671", "Inner join (3 VN days dropped; 17 spike-reversals noted)", "1,527", "158 (10.35%)", "-2.11% / +2.10%"],
            ["Brent Crude Oil", "yfinance (BZ=F)", "1,615", "Inner join (47 US/UK holidays dropped; gap = 1.98% < 5%)", "1,527", "4 (0.26%)", "-15.69% / +9.16%"],
            ["US 10Y Yield", "FRED (DGS10)", "1,600", "Forward-filled on 59 US holidays only (d_DGS10 in pp)", "1,527", "105 (6.88%)", "-0.30 pp / +0.28 pp"],
            ["Panel B: Validation", "10 Published Checkpoints", "2020–2025", "HOSE/HNX/VNA/Vietstock/BVSC official closes", "20 / 20", "Max diff: 0.00 pts", "Status: 100% Verified"],
        ],
        col_widths_dxa=[1300, 1450, 950, 2222, 850, 1050, 1250],
    ))
    add_p("", space_after=60)

    # =========================================================================
    # 3. EXPLORATORY DATA ANALYSIS
    # =========================================================================
    add_h1("3. Exploratory data analysis")
    add_p(
        "Figure 2 displays the log-level trajectories and daily return/difference series across the 2020–2026 "
        "sample, while Table 2 reports distributional statistics, Jarque–Bera (JB) normality tests, Ljung–Box "
        "serial-correlation tests on returns Q(10) and squared returns Q^2(10), and Engle's (1982) ARCH-LM(10) "
        "tests. Over the sample, the Vietnamese composite index delivered a mean daily log return of 0.0457% "
        "(11.53% annualised) with an annualised volatility of 19.84% (daily standard deviation 1.2497%). Brent "
        "crude exhibited nearly double the volatility (39.44% annualised; daily standard deviation 2.4843%, "
        "ranging from -15.69% on 1 April 2026 to +9.16% on 13 July 2026), whereas USD/VND moved within a "
        "tightly managed volatility of 4.52% annualised (daily standard deviation 0.2850%, annualised drift "
        "+1.70%). The US 10-year Treasury yield rose from 0.66% in June 2020 to above 4.20% by 2024–2026, with "
        "a daily standard deviation of 0.0594 percentage points (5.94 bps)."
    )
    add_fig(2, "Figure 2: Daily Levels and Log Returns / First Differences of VN Composite, USD/VND, Brent Crude, and US 10Y Yield (2020–2026).")
    add_caption("Table 2: Summary Statistics, Normality, Autocorrelation, and Conditional Heteroskedasticity Tests (N = 1,527)")
    body.append(make_table(
        headers=["Series", "Mean (Daily)", "Std (Daily)", "Ann. Mean / Vol", "Skewness", "Excess Kurt.", "Min / Max", "Jarque–Bera (p)", "LB Q(10) [p]", "LB Q^2(10) [p]", "ARCH-LM(10) [p]"],
        rows=[
            ["r_composite (%)", "0.0457", "1.2497", "11.53% / 19.84%", "-0.959", "4.619", "-6.95 / +6.63", "1,580.0 (<.001)", "7.98 [.630]", "233.90 [<.001]", "158.31 [<.001]"],
            ["r_VNINDEX (%)", "0.0455", "1.2463", "11.46% / 19.78%", "-0.942", "4.597", "-6.95 / +6.44", "1,554.7 (<.001)", "7.76 [.652]", "226.44 [<.001]", "154.10 [<.001]"],
            ["r_HNXINDEX (%)", "0.0497", "1.5223", "12.52% / 24.17%", "-0.869", "4.892", "-10.31 / +7.77", "1,705.2 (<.001)", "18.88 [.042]", "262.13 [<.001]", "165.41 [<.001]"],
            ["r_USDVND (%)", "0.0067", "0.2850", "1.70% / 4.52%", "-0.097", "20.561", "-2.11 / +2.10", "26,713.6 (<.001)", "141.48 [<.001]", "521.48 [<.001]", "430.49 [<.001]"],
            ["r_OIL (%)", "0.0735", "2.4843", "18.51% / 39.44%", "-0.822", "4.336", "-15.69 / +9.16", "1,357.9 (<.001)", "19.66 [.033]", "247.37 [<.001]", "183.95 [<.001]"],
            ["d_DGS10 (pp)", "0.0028", "0.0594", "+0.70 / 0.94 pp", "-0.051", "1.406", "-0.30 / +0.28", "124.87 (<.001)", "15.56 [.113]", "101.66 [<.001]", "75.83 [<.001]"],
        ],
        col_widths_dxa=[1100, 720, 720, 1050, 680, 720, 920, 920, 740, 760, 742],
        font_size_half_pt=17,
    ))
    add_p(
        "The EDA confirms four classic financial stylized facts (Cont, 2001) that directly govern our Stage 3 "
        "model specification. First, heavy tails and negative skewness: Jarque–Bera tests strongly reject "
        "normality for every series (all p < 0.0001), with significant negative skewness in Vietnamese equities "
        "(-0.959) and Brent (-0.822) and extreme leptokurtosis in USD/VND (excess kurtosis 20.561, reflecting "
        "stepwise band adjustments and occasional Yahoo spot quote bounce-backs). The Q-Q plots in Figure 3 "
        "(upper panel) show pronounced S-shaped departures from the Gaussian reference line. Second, absence of "
        "linear return autocorrelation vs. strong FX persistence: Ljung–Box Q(10) fails to reject white noise "
        "for composite equity returns (Q(10) = 7.98, p = 0.630) and US yield changes (Q(10) = 15.56, p = 0.113), "
        "whereas USD/VND exhibits strong linear autocorrelation (Q(10) = 141.48, p < 0.0001) due to central-bank "
        "smoothing and quotes reversion. Third, volatility clustering: as shown in Figure 3 (lower panel) and "
        "Table 2, squared returns display highly significant autocorrelation (Q^2(10) ranging from 101.66 to "
        "521.48, all p < 0.0001) and ARCH-LM(10) rejects conditional homoskedasticity in every series (158.31 "
        "for r_composite). Fourth, I(1) levels and I(0) differences: Table 3 reports Augmented Dickey–Fuller "
        "(ADF, H0: unit root) and Kwiatkowski–Phillips–Schmidt–Shin (KPSS, H0: level stationarity) tests. For "
        "all four level series, ADF fails to reject a unit root (p >= 0.129) while KPSS rejects stationarity at "
        "the 1% level (p = 0.010). For all first differences and log returns, ADF rejects a unit root at "
        "p < 0.0001 and KPSS fails to reject stationarity (p = 0.100). Consequently, short-run dynamics must be "
        "modelled via a stationary VAR on returns/differences with heteroskedasticity-robust inference, while "
        "long-run equilibrium among the I(1) levels requires cointegration testing and a VECM."
    )
    add_fig(3, "Figure 3: Normal Q-Q Plots (Top) and Sample Autocorrelation Functions of Returns and Squared Returns to Lag 20 (Bottom).")
    add_caption("Table 3: Augmented Dickey–Fuller (ADF) and KPSS Unit-Root Tests on Levels and Returns/Differences")
    body.append(make_table(
        headers=["Variable", "Level Series", "ADF Stat (Level)", "ADF p", "KPSS Stat (Level)", "KPSS p", "Diff / Return Series", "ADF Stat (Diff)", "ADF p", "KPSS Stat (Diff)", "KPSS p", "Order"],
        rows=[
            ["VN Composite", "log_composite", "-1.999", "0.287", "2.185", "0.010", "r_composite", "-38.613", "<0.001", "0.130", "0.100", "I(1)"],
            ["VN-Index", "log_VNINDEX", "-1.954", "0.307", "2.126", "0.010", "r_VNINDEX", "-38.587", "<0.001", "0.136", "0.100", "I(1)"],
            ["HNX-Index", "log_HNXINDEX", "-2.447", "0.129", "1.464", "0.010", "r_HNXINDEX", "-16.519", "<0.001", "0.214", "0.100", "I(1)"],
            ["USD/VND", "log_USDVND", "-0.088", "0.951", "5.374", "0.010", "r_USDVND", "-14.791", "<0.001", "0.172", "0.100", "I(1)"],
            ["Brent Crude", "log_OIL", "-2.266", "0.183", "1.520", "0.010", "r_OIL", "-39.048", "<0.001", "0.228", "0.100", "I(1)"],
            ["US 10Y Yield", "DGS10", "-1.367", "0.598", "4.888", "0.010", "d_DGS10", "-17.653", "<0.001", "0.163", "0.100", "I(1)"],
        ],
        col_widths_dxa=[950, 920, 800, 620, 820, 620, 1020, 800, 620, 820, 620, 462],
        font_size_half_pt=17,
    ))
    add_p("", space_after=60)

    # =========================================================================
    # 4. METHODOLOGY
    # =========================================================================
    add_h1("4. Methodology")
    add_p(
        "Short-run dynamic interactions are modelled via a p-lag Vector Autoregression, VAR(p), on the "
        "stationary 4 x 1 vector y_t = [dUS10Y_t, r_OIL,t, r_USDVND,t, r_VN,t]': "
        "y_t = c + A_1 y_{t-1} + ... + A_p y_{t-p} + u_t, where c is a 4 x 1 intercept vector, A_k are 4 x 4 "
        "autoregressive coefficient matrices, and u_t is a 4 x 1 innovation vector with covariance matrix Sigma_u "
        "(Sims, 1980; Lütkepohl, 2005). Candidate lag orders p in {0, 1, ..., 10} are evaluated on a common "
        "estimation sample using the Akaike (AIC), Hannan–Quinn (HQIC), and Schwarz Bayesian (BIC) criteria. "
        "For variable j to Granger-cause variable i, we test H0: a_{ij,1} = ... = a_{ij,p} = 0. Because Table 2 "
        "revealed strong ARCH effects, we supplement standard homoskedastic F-tests with three robust inference "
        "procedures: (i) White HC3 heteroskedasticity-consistent Wald tests; (ii) Newey & West (1987) HAC Wald "
        "tests with bandwidth q = p; and (iii) the Rademacher Wild Bootstrap (B = 2,000 replications, seed = 42; "
        "Gonçalves & Kilian, 2004), which multiplies restricted null residuals by w_t in {-1, +1} with equal "
        "probability to preserve the exact conditional heteroskedasticity timing. Across all 4 x 3 = 12 off-diagonal "
        "pairs, family-wise error rates are controlled via Bonferroni and Holm (1979) step-down adjustments."
    )
    add_p(
        "To orthogonalise innovations Sigma_u = P P' for Impulse Response Functions (IRFs) and Forecast-Error "
        "Variance Decompositions (FEVDs), our baseline Cholesky ordering places variables in decreasing order of "
        "global exogeneity: dUS10Y -> r_OIL -> r_USDVND -> r_VN (Cushman & Zha, 1997; Kilian & Park, 2009). US "
        "Treasury yields are determined in the deepest global bond market; Brent crude responds within the day "
        "to US macro news; the SBV sets USD/VND reference rates against global dollar and rate conditions; and "
        "Vietnamese equities respond endogenously. However, because HOSE and HNX close at 15:00 ICT (08:00 UTC) "
        "before the London afternoon and New York sessions, same-calendar-date US yield and Brent closes occur "
        "chronologically after the Hanoi close. We therefore cross-check our baseline Cholesky decomposition "
        "against (a) the reversed ordering (r_VN -> r_USDVND -> r_OIL -> dUS10Y) and (b) order-invariant "
        "Generalized Impulse Response Functions (GIRFs; Koop, Pesaran, & Potter, 1996; Pesaran & Shin, 1998), "
        "where the response to a one-standard-deviation shock in variable j is Theta^g_i(h) = sigma_{jj}^{-1/2} "
        "Phi_h Sigma_u e_j. To verify that conditional heteroskedasticity does not distort the VAR dynamics, we "
        "also estimate Student-t GARCH(1,1) (Bollerslev, 1986) and asymmetric GJR-GARCH(1,1)-t (Glosten, "
        "Jagannathan, & Runkle, 1993) models on the VAR(5) equity residuals."
    )
    add_p(
        "For long-run equilibrium analysis on the I(1) level vector X_t = [log_composite_t, log_USDVND_t, "
        "log_OIL_t, DGS10_t]', we run two complementary tests: (i) pairwise Engle & Granger (1987) residual-based "
        "ADF tests regressing log_composite_t on each macro variable individually, and (ii) system Johansen "
        "(1991) reduced-rank trace (lambda_trace) and maximum-eigenvalue (lambda_max) tests with a constant "
        "restricted to the cointegrating space (det_order = 0) and lag order k_{ar,diff} = p - 1 = 4. When rank "
        "r = 1 is supported by the trace test (preferred under skewness and excess kurtosis per Lütkepohl, "
        "Saikkonen, & Trenkler, 2001), we estimate the VECM: Delta X_t = alpha (beta' X_{t-1} + c_0) + "
        "Sum_{m=1}^{k} Gamma_m Delta X_{t-m} + varepsilon_t, normalising beta_1 = 1 on log_composite_t. The "
        "loading vector alpha measures each variable's daily adjustment speed toward equilibrium, with implied "
        "mean-reversion half-life ln(0.5) / ln(1 - |alpha|) compared against the empirical AR(1) half-life of "
        "the error-correction term ect_{t-1} = beta' X_{t-1} + c_0."
    )
    add_p(
        "Finally, Stage 5 evaluates one-step-ahead out-of-sample forecasts over the last N_test = 500 trading "
        "days (25 September 2024 to 30 October 2026) using a fixed-length rolling window of W = 750 trading days "
        "(~3 years), re-estimated every 20 trading days with strict zero look-ahead. We compare the AIC-selected "
        "VAR, fixed-lag VAR(1), VAR(2), and VAR(5) models, a univariate AR(1), and a zero-return random walk "
        "(RW, r_hat_{t+1|t} = 0) using Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), Campbell & "
        "Thompson (2008) out-of-sample R^2_OOS = 1 - MSE_model / MSE_RW, directional accuracy (DA %), and "
        "Diebold & Mariano (1995) tests with the Harvey et al. (1997) finite-sample modification. Although VAR, "
        "AR(1), and RW are nested, Giacomini & White (2006, Theorem 1) prove that under a finite rolling window "
        "W = 750, parameter estimation error remains non-vanishing under the null, so the Diebold–Mariano "
        "statistic retains its standard normal asymptotic distribution."
    )

    # =========================================================================
    # 5. RESULTS
    # =========================================================================
    add_h1("5. Results")
    add_h2("5.1 VAR Lag Selection, Granger Causality, and Robustness Battery")
    add_p(
        "On the common estimation sample, AIC selects p = 5 lags (AIC = -6.0442, one full five-day trading week), "
        "HQIC selects p = 2 (-5.9956), and BIC selects p = 1 (-5.9469). We adopt VAR(5) (N_eff = 1,522) as the "
        "baseline model because five daily lags capture full weekly cross-market transmission across asynchronous "
        "time zones and eliminate residual serial correlation at lag 10 in all four equations. Table 4 (Panel A) "
        "reports all significant and policy-relevant Granger-causality pairs in the baseline VAR(5) across four "
        "inference methods plus 12-pair Holm (1979) step-down adjustments, while Panel B tests dUS10Y -> r_VN "
        "across lag orders p in {1, 2, 3, 5, 10} both on the full sample and after excluding all 10 multi-day "
        "return rows following unscheduled 2020–2021 vnstock provider gaps."
    )
    add_caption("Table 4: VAR(5) Granger Causality Tests, Heteroskedasticity/Bootstrap/Holm Adjustments, and Lag/Provider-Gap Sensitivity")
    body.append(make_table(
        headers=["Panel / Directed Pair or Specification", "Lag p", "T_eff", "F (Homo)", "p (Homo)", "p (HC3)", "p (HAC)", "p (Wild Boot)", "p (Holm 12-pair)", "Finding"],
        rows=[
            ["Panel A: Baseline VAR(5) Key Pairs", "", "", "", "", "", "", "", "", ""],
            ["dUS10Y -> r_VN (US Yield -> VN Equity)", "5", "1,522", "3.2991", "0.0056**", "0.0317*", "0.0717", "0.0230*", "0.0574 (boot .253)", "Significant at 1% (homo), 5% (HC3/boot)"],
            ["dUS10Y -> r_USDVND (US Yield -> FX)", "5", "1,522", "3.8480", "0.0018**", "0.0026**", "0.0072**", "0.0005**", "0.0218* (boot .006**)", "Survives all 12-pair FWER corrections"],
            ["r_VN -> r_USDVND (VN Equity -> FX)", "5", "1,522", "3.3624", "0.0049**", "0.0688", "0.1109", "0.0465*", "0.0540 (boot .465)", "Portfolio-flow feedback to FX"],
            ["r_USDVND -> r_OIL (FX -> Brent)", "5", "1,522", "2.6452", "0.0214*", "0.0126*", "0.0920", "0.0045**", "0.1965 (boot .050*)", "Reflects global USD common factor"],
            ["r_OIL -> r_VN (Brent -> VN Equity)", "5", "1,522", "1.0577", "0.3822", "0.5206", "0.5433", "0.5317", "1.0000", "No direct daily oil causality"],
            ["r_USDVND -> r_VN (FX -> VN Equity)", "5", "1,522", "0.4567", "0.8086", "0.8342", "0.8180", "0.8316", "1.0000", "No direct daily FX causality"],
            ["Panel B: dUS10Y -> r_VN Lag & Gap Sensitivity", "", "", "", "", "", "", "", "", ""],
            ["Full sample (BIC optimal lag)", "1", "1,526", "5.2174", "0.0225*", "0.0383*", "0.0349*", "0.0350*", "—", "Significant <5% across ALL 4 methods"],
            ["Excl. provider gaps (BIC lag)", "1", "1,506", "4.7459", "0.0295*", "0.0485*", "0.0446*", "0.0500*", "—", "Robust to dropping provider gaps"],
            ["Full sample (HQIC optimal lag)", "2", "1,525", "2.7484", "0.0643", "0.1103", "0.0996", "0.1259", "—", "Borderline at 10%"],
            ["Full sample (3-day lag)", "3", "1,524", "2.8027", "0.0387*", "0.0885", "0.1079", "0.0975", "—", "Significant at 5% (homo)"],
            ["Excl. provider gaps (AIC baseline lag)", "5", "1,472", "3.7836", "0.0021**", "0.0189*", "0.0421*", "0.0160*", "—", "Excluding gaps strengthens causality"],
            ["Full sample (2-week lag)", "10", "1,517", "2.0080", "0.0292*", "0.0853", "0.1095", "0.0950", "—", "Significant at 5% (homo)"],
        ],
        col_widths_dxa=[2150, 480, 580, 720, 720, 700, 700, 760, 960, 1302],
        font_size_half_pt=16,
    ))
    add_p(
        "Three empirical findings stand out from Table 4. First, changes in the US 10-year Treasury yield "
        "(dUS10Y) are the dominant external driver of Vietnamese equity returns: in the baseline VAR(5), "
        "dUS10Y -> r_VN rejects non-causality at p = 0.0056 (F = 3.30), remaining significant at the 5% level "
        "under White HC3 (p = 0.0317) and the Rademacher Wild Bootstrap (p = 0.0230), and at the 10% level "
        "under Newey–West HAC (p = 0.0717) and 12-pair Holm correction (p = 0.0574). Second, excluding the 10 "
        "return rows that follow the 2020–2021 vnstock provider gaps strengthens dUS10Y -> r_VN at p = 5 to "
        "F = 3.7836 (p_homo = 0.0021, p_HC3 = 0.0189, p_HAC = 0.0421, p_boot = 0.0160), proving that our primary "
        "finding is not an artifact of multi-day provider gaps. Moreover, at the BIC-selected lag p = 1, "
        "dUS10Y -> r_VN is statistically significant at the 5% level across all four inference procedures "
        "(p_homo = 0.0225, p_HC3 = 0.0383, p_HAC = 0.0349, p_boot = 0.0350). Third, US yield changes strongly "
        "Granger-cause USD/VND movements (F = 3.8480, p_homo = 0.0018, p_boot = 0.0005), surviving strict "
        "12-pair Bonferroni and Holm corrections (p_Holm = 0.0218; bootstrap p_Holm = 0.0060), while Vietnamese "
        "equity returns Granger-cause USD/VND (F = 3.3624, p_homo = 0.0049, p_boot = 0.0465), supporting the "
        "portfolio-balance channel (Branson, 1983). Neither Brent crude (p = 0.382) nor USD/VND (p = 0.809) "
        "exhibits significant direct linear Granger causality onto Vietnamese stock returns."
    )

    add_h2("5.2 Impulse Responses, Variance Decomposition, and Residual Diagnostics")
    add_p(
        "Figure 4 and Table 5 (Panels A–B) trace the dynamic response and forecast-error variance decomposition "
        "of composite Vietnamese equity returns across our three identification schemes: baseline Cholesky "
        "(dUS10Y first), reversed Cholesky (r_VN first, motivated by Hanoi's 08:00 UTC market close), and "
        "order-invariant Pesaran–Shin (1998) GIRFs. Because same-calendar-date US yield innovations occur after "
        "the Hanoi close, the contemporaneous (h = 0) response of r_VN to a one-standard-deviation (5.94 bps) "
        "dUS10Y shock is near zero (-0.0130%, or 0.0000% by construction under reversed ordering). The main "
        "impact arrives on the next trading day (h = 1), where a 1-s.d. US yield increase depresses Vietnamese "
        "equities by -0.0666% under baseline Cholesky, -0.0704% under reversed Cholesky, and -0.0666% under "
        "GIRF, followed by a second significant negative wave at h = 5 (-0.0938% baseline/GIRF, -0.0842% "
        "reversed). By horizon h = 20 (Table 5, Panel B), own equity shocks account for 98.19% of forecast-error "
        "variance (98.25% reversed), while dUS10Y explains 1.29% (1.11% reversed), Brent explains 0.33% (0.49% "
        "reversed), and USD/VND explains 0.19% (0.15% reversed)."
    )
    add_fig(4, "Figure 4: Dynamic Response of Composite VN Equity Returns (r_VN) to One-Standard-Deviation Macro Shocks: Baseline Cholesky, Reversed Cholesky, and Pesaran–Shin (1998) GIRF.")
    add_caption("Table 5: Impulse Responses, FEVD Ordering Sensitivity, and VAR(5) Residual Diagnostics with Student-t GARCH(1,1) Filter")
    body.append(make_table(
        headers=["Panel / Metric", "h=0 / Eq.", "h=1 / Lag 10", "h=2 / JB", "h=3 / ARCH", "h=5 / alpha+beta", "h=10 / nu_hat", "h=20 / Note"],
        rows=[
            ["Panel A: r_VN Response to 1-s.d. Shock (%)", "h = 0", "h = 1", "h = 2", "h = 3", "h = 5", "h = 10", "Cumulative (0..5)"],
            ["Shock: dUS10Y (Baseline Cholesky)", "-0.0130%", "-0.0666%", "-0.0187%", "+0.0365%", "-0.0938%", "-0.0014%", "-0.1756%"],
            ["Shock: dUS10Y (Reversed Cholesky: VN first)", "0.0000%", "-0.0704%", "-0.0230%", "+0.0376%", "-0.0842%", "-0.0016%", "-0.1636%"],
            ["Shock: dUS10Y (Pesaran–Shin GIRF)", "-0.0130%", "-0.0666%", "-0.0191%", "+0.0364%", "-0.0938%", "-0.0014%", "-0.1760%"],
            ["Shock: r_OIL (Baseline / GIRF)", "+0.0168%", "+0.0398%", "-0.0493%", "+0.0056%", "+0.0282%", "+0.0016%", "+0.0192%"],
            ["Shock: r_USDVND (Baseline / GIRF)", "-0.0370%", "-0.0006%", "+0.0138%", "+0.0273%", "-0.0221%", "+0.0054%", "-0.0006%"],
            ["Panel B: FEVD of r_VN (% Variance)", "h = 1", "h = 2", "h = 5", "h = 10", "h = 20 (Base)", "h = 20 (Rev)", "Invariance Check"],
            ["Share: Own Shock (r_VN)", "99.90%", "99.46%", "99.13%", "98.20%", "98.19%", "98.25%", "Diff = 0.06 pp"],
            ["Share: US 10Y Yield (dUS10Y)", "0.01%", "0.29%", "0.40%", "1.28%", "1.29%", "1.11%", "Primary macro driver"],
            ["Share: Brent Crude (r_OIL)", "0.02%", "0.12%", "0.29%", "0.33%", "0.33%", "0.49%", "Minor variance share"],
            ["Share: Exchange Rate (r_USDVND)", "0.09%", "0.09%", "0.15%", "0.19%", "0.19%", "0.15%", "Minor variance share"],
            ["Panel C: Residual & GARCH Diagnostics", "Equation", "LB Q(10) [p]", "JB Stat [p]", "LB Q^2(10) [p]", "Persistence", "DoF / Asym.", "Diagnostic Result"],
            ["Raw VAR(5) Residuals (r_VN eq.)", "r_VN", "0.24 [1.000]", "1393.1 [<.001]", "235.12 [<.001]", "ARCH-LM=153.3", "Max root=0.695", "Mean clean; ARCH present"],
            ["Student-t GARCH(1,1) on r_VN Resid.", "r_VN", "7.45 [.682]", "—", "4.21 [.937]", "0.9368 (.15+.79)", "nu = 4.25", "ARCH completely removed"],
            ["Student-t GJR-GARCH(1,1) on r_VN Resid.", "r_VN", "6.26 [.793]", "—", "4.85 [.901]", "0.9462", "gamma = 0.3496**", "Strong leverage effect"],
        ],
        col_widths_dxa=[2150, 950, 980, 980, 1020, 980, 950, 1062],
        font_size_half_pt=16,
    ))
    add_p(
        "Table 5 (Panel C) confirms that the VAR(5) is dynamically stable (all 20 companion-matrix eigenvalues "
        "lie strictly inside the unit circle, largest modulus = 0.695) and free of residual autocorrelation in "
        "every equation at lag 10 (Ljung–Box Q(10) = 0.24, p = 1.000 for r_VN). Because squared VAR(5) residuals "
        "retain strong volatility clustering (Q^2(10) = 235.12, p < 0.0001; ARCH-LM(10) = 153.26), we fit a "
        "Student-t GARCH(1,1) filter (alpha_1 = 0.1456, beta_1 = 0.7912, alpha_1 + beta_1 = 0.9368, degrees of "
        "freedom nu_hat = 4.25) and an asymmetric Student-t GJR-GARCH(1,1) model (leverage parameter gamma_1 = "
        "0.3496, p < 0.0001) to the equity residuals. Standardized squared residuals have Q^2(10) = 4.21 "
        "(p = 0.9374) and ARCH-LM(10) = 4.19 (p = 0.9385), confirming that a fat-tailed GARCH variance equation "
        "completely absorbs the conditional heteroskedasticity."
    )

    add_h2("5.3 Long-Run Equilibrium: Cointegration and VECM")
    add_p(
        "Table 6 summarises the Engle–Granger (1987) pairwise tests, the four-variable Johansen (1991) system "
        "tests (k_{ar,diff} = 4), and the resulting rank-1 VECM estimates. Pairwise Engle–Granger tests find no "
        "cointegration between the log composite index and any single macro variable (ADF t = -1.994, p = 0.532 "
        "for log_USDVND; t = -1.778, p = 0.640 for log_OIL; t = -1.644, p = 0.702 for DGS10). In the joint "
        "four-variable system, the Johansen trace test rejects r = 0 at the 5% level (lambda_trace = 51.9936 > "
        "47.8545) and does not reject r <= 1 (25.7032 < 29.7961), indicating one cointegrating relation (r = 1), "
        "whereas the maximum-eigenvalue statistic falls narrowly below its 5% critical value (lambda_max = "
        "26.2905 < 27.5858). Following Lütkepohl et al. (2001), we estimate the rank-1 VECM. Normalised on "
        "log_composite_t = 1.000, the cointegrating vector is beta = [1.000, -5.6806 (p < 0.001), -1.0452 "
        "(p < 0.001), +0.1915 (p = 0.023)]', implying that in the long-run relation log equity levels co-move "
        "positively with nominal USD/VND and Brent prices (reflecting shared nominal growth and inflation trends "
        "over 2020–2026) and negatively with US 10-year yields. Crucially, however, the equity error-correction "
        "speed is statistically indistinguishable from zero (alpha_VN = -0.00082, t = -0.348, p = 0.728, "
        "implied partial half-life = 842.8 trading days), whereas Brent crude adjusts significantly "
        "(alpha_OIL = +0.0236, t = 5.079, p < 0.001; AR(1) half-life of the error-correction term in Figure 5 "
        "is 24.12 trading days). Hence, the weak four-variable equilibrium is restored through global commodity "
        "repricing rather than domestic stock-price mean reversion."
    )
    add_fig(5, "Figure 5: Estimated VECM Error-Correction Term (ect_{t-1} = beta' X_{t-1} + c_0, Standardized) Over 2020–2026.")
    add_caption("Table 6: Pairwise Engle–Granger Tests, Johansen System Cointegration Tests, and Rank-1 VECM Estimates")
    body.append(make_table(
        headers=["Panel / Test or Variable", "Hypothesis / Role", "Statistic / Coef.", "5% CV / SE", "p-value / t-stat", "Decision / Economic Interpretation"],
        rows=[
            ["Panel A: Engle–Granger Pairwise", "Dep: log_composite", "ADF t-stat", "MacKinnon p", "Lag (AIC)", "Result"],
            ["Regressor: log_USDVND", "H0: No cointegration", "-1.9935", "—", "p = 0.5315 (k=0)", "Fail to reject H0 (no pairwise coint.)"],
            ["Regressor: log_OIL", "H0: No cointegration", "-1.7782", "—", "p = 0.6403 (k=0)", "Fail to reject H0 (no pairwise coint.)"],
            ["Regressor: DGS10", "H0: No cointegration", "-1.6442", "—", "p = 0.7024 (k=0)", "Fail to reject H0 (no pairwise coint.)"],
            ["Panel B: Johansen 4-Variable System", "Null Hypothesis", "Trace / Max-Eig", "5% Crit. Val.", "1% Crit. Val.", "Result (k_ar_diff = 4, det_order = 0)"],
            ["Trace Test (r <= 0)", "H0: rank = 0", "51.9936*", "47.8545", "54.6815", "Reject r = 0 at 5% -> Rank r = 1"],
            ["Trace Test (r <= 1)", "H0: rank <= 1", "25.7032", "29.7961", "35.4628", "Fail to reject r <= 1"],
            ["Max-Eigenvalue Test (r <= 0)", "H0: rank = 0", "26.2905", "27.5858", "32.7172", "Narrowly below 5% CV (weak joint coint.)"],
            ["Panel C: Rank-1 VECM Estimates", "Parameter Role", "Estimate", "Std. Error", "t-stat [p-val]", "Adjustment / Long-Run Implication"],
            ["log_composite (beta_1, alpha_VN)", "Normalised Dep. Var.", "beta = 1.0000", "alpha = -0.00082", "t = -0.348 [.728]", "Zero equity adjustment (HL_alpha = 842.8d)"],
            ["log_USDVND (beta_2, alpha_FX)", "Exchange Rate", "beta = -5.6806**", "alpha = +0.00037", "t = 0.696 [.486]", "FX weakly exogenous to long-run ECT"],
            ["log_OIL (beta_3, alpha_OIL)", "Brent Crude Oil", "beta = -1.0452**", "alpha = +0.02359**", "t = 5.079 [<.001]", "Oil adjusts strongly (ECT AR(1) HL = 24.1d)"],
            ["DGS10 (beta_4, alpha_US10Y)", "US 10Y Yield", "beta = +0.1915*", "alpha = -0.00005", "t = -0.453 [.650]", "US yield strictly exogenous (alpha ~ 0)"],
        ],
        col_widths_dxa=[1950, 1300, 1150, 1100, 1150, 2422],
        font_size_half_pt=16,
    ))
    add_p("", space_after=60)

    add_h2("5.4 Out-of-Sample Forecast Comparison")
    add_p(
        "Table 7 and Figure 6 (top panel) report the 500-day rolling out-of-sample evaluation (25 September 2024 "
        "to 30 October 2026). The AIC-selected rolling VAR (which selects p = 1 in 21 of 25 refits and p = 2 in "
        "4 refits) achieves an RMSE of 1.2448% and MAE of 0.8368%, trailing the zero-return random walk (RMSE = "
        "1.2349%, MAE = 0.8349%) with R^2_OOS = -1.60% and directional accuracy DA = 54.2% (vs. 55.6% for RW). "
        "The univariate AR(1) achieves the lowest RMSE (1.2290%, R^2_OOS = +0.96%, DA = 54.6%). However, "
        "comparing fixed-lag VAR(1), VAR(2), and VAR(5) models in Table 7 reveals why: a 4-variable VAR(5) "
        "estimates 21 parameters per equation, injecting estimation variance on a 750-day window (R^2_OOS = "
        "-1.60%), whereas restricting the system to a parsimonious fixed-lag VAR(1) (5 parameters per equation) "
        "reduces RMSE to 1.2328% (MAE = 0.8299%), achieving a positive R^2_OOS = +0.34% and tying the random "
        "walk on directional accuracy (55.6%). Across all loss functions, Diebold–Mariano tests fail to reject "
        "equal predictive accuracy at the 5% level (MSE DM = 1.7077, p = 0.0883 vs. AR(1); DM = 0.9355, "
        "p = 0.3500 vs. RW), confirming that the modest 1.29% macro variance share is too small to dominate "
        "daily equity noise out of sample (Welch & Goyal, 2008)."
    )
    add_caption("Table 7: Out-of-Sample Forecast Evaluation (N_test = 500, 2024-09-25 to 2026-10-30, Rolling Window W = 750)")
    body.append(make_table(
        headers=["Model / Benchmark", "RMSE (%)", "MAE (%)", "RMSE / RW", "OOS R^2 vs RW (%)", "Dir. Acc. (%)", "DM (MSE) vs VAR [p]", "DM (MAE) vs VAR [p]"],
        rows=[
            ["VAR (AIC rolling lag)", "1.2448", "0.8368", "1.0080", "-1.60%", "54.2%", "Baseline VAR", "Baseline VAR"],
            ["VAR(5) fixed lag (21 params)", "1.2448", "0.8407", "1.0080", "-1.60%", "52.4%", "—", "—"],
            ["VAR(2) fixed lag (9 params)", "1.2393", "0.8339", "1.0036", "-0.71%", "54.6%", "—", "—"],
            ["VAR(1) fixed lag (5 params)", "1.2328", "0.8299", "0.9983", "+0.34%", "55.6%", "Beats RW on RMSE & MAE", "Ties best MAE & DA"],
            ["Univariate AR(1) (2 params)", "1.2290", "0.8299", "0.9952", "+0.96%", "54.6%", "DM = 1.7077 [p = .0883]", "DM = 1.2456 [p = .2135]"],
            ["Random Walk (zero-drift, 0 params)", "1.2349", "0.8349", "1.0000", "0.00%", "55.6%", "DM = 0.9355 [p = .3500]", "DM = 0.2882 [p = .7733]"],
        ],
        col_widths_dxa=[1850, 820, 820, 850, 1100, 900, 1366, 1366],
        font_size_half_pt=16,
    ))
    add_fig(6, "Figure 6: Out-of-Sample Cumulative Squared Forecast Errors (Top) and Subsample IRF Stability Across Monetary and SBV FX-Band Regimes (Bottom).")

    add_h2("5.5 Robustness: VN-Index Alone, Extended 2016–2026 Sample, and Subsample Stability")
    add_p(
        "Table 8 synthesises three structural robustness checks. First, replacing the composite index with "
        "HOSE's VN-Index alone over 2020–2026 (N = 1,527) yields virtually identical results: AIC selects p = 5, "
        "dUS10Y Granger-causes r_VNINDEX with F = 3.2804 (p = 0.0059 vs. 0.0056 composite), 20-day FEVD shares "
        "differ by <= 0.03 percentage points (98.22% own, 1.28% dUS10Y), and Johansen trace statistics match "
        "closely (52.00 vs. 51.99). Second, extending the VN-Index-only system back to November 2016 "
        "(2016-11-02 to 2026-10-30, N = 2,384) strengthens long-run cointegration: both the Johansen trace "
        "test (67.9915 > 47.8545) and maximum-eigenvalue test (40.3399 > 27.5858) reject r = 0 at the 5% level "
        "(confirming Hakkio & Rush, 1991, that cointegration power rises with total time span). Splitting out "
        "the pre-pandemic subsample (2016-11 to 2020-05, N = 856) reveals why full-decade short-run Granger "
        "causality is more moderate (F = 2.1129, p = 0.0767): before 2020, US yield increases reflected global "
        "growth optimism and co-moved positively with VN-Index (+0.1075% at h = 1), whereas in 2020–2026 US rate "
        "shocks reflected inflation/Fed tightening and depressed Vietnamese equities (-0.0666% at h = 1). Third, "
        "splitting the 2020–2026 sample by monetary regime (2020–2022 vs. 2023–2026) and by the SBV's 17 October "
        "2022 widening of the USD/VND trading band from +-3% to +-5% (Figure 6, bottom panel; Table 8) shows that "
        "while the h = 1 negative impact of dUS10Y is stable across every subsample (-0.068% to -0.075%), "
        "multi-day Granger causality is concentrated during the 2020–2022 tightening cycle (F = 4.8163, "
        "p_homo = 0.00025, p_HAC = 0.0064; 5-day cumulative IRF = -0.3061%) and under the tighter +-3% FX band "
        "(F = 3.0919, p_homo = 0.0092, p_HAC = 0.0485). Under the wider +-5% FX band after October 2022, the "
        "spot exchange rate absorbed greater external pressure, buffering domestic equities beyond lag 1 "
        "(1-lag F = 3.7619, p = 0.0527; 5-lag F = 1.2076, p = 0.3035)."
    )
    add_caption("Table 8: Robustness Across Equity Benchmark, Extended 10-Year Sample (2016–2026), and Monetary / SBV FX-Band Regimes")
    body.append(make_table(
        headers=["Specification / Subsample", "Sample Window", "N_obs", "dUS10Y -> r_VN F (p_homo)", "p_HAC / p_boot", "1-Lag F (p)", "IRF h=1 (%)", "IRF h=5 / Cum5d", "Johansen Trace / MaxEig [Rank]"],
        rows=[
            ["1. Baseline Composite (HOSE+HNX)", "2020-06..2026-10", "1,527", "3.2991 (0.0056**)", "0.0717 / 0.0230*", "5.217 (0.0225*)", "-0.0666%", "-0.0938% / -0.176%", "51.99* / 26.29 [r = 1]"],
            ["2. VN-Index Only (HOSE)", "2020-06..2026-10", "1,527", "3.2804 (0.0059**)", "0.0748 / 0.0245*", "5.148 (0.0234*)", "-0.0666%", "-0.0928% / -0.175%", "52.00* / 26.23 [r = 1]"],
            ["3. VN-Index Extended (10-Year)", "2016-11..2026-10", "2,384", "2.1129 (0.0767)", "0.1851 / 0.1419", "1.464 (0.2264)", "-0.0229%", "-0.0398% / -0.059%", "67.99* / 40.34* [r = 1]"],
            ["4. VN-Index Pre-Pandemic", "2016-11..2020-05", "856", "2.4879 (0.0593)", "0.2647 / 0.1949", "2.429 (0.1195)", "+0.1075%", "+0.0010% / +0.344%", "35.70 / 21.84 [r = 0]"],
            ["5. Subsample 1A: Tightening Cycle", "2020-06..2022-12", "605", "4.8163 (0.0003**)", "0.0064** / 0.0030**", "1.999 (0.1579)", "-0.0679%", "-0.1980% / -0.306%", "Strongest rate spillover"],
            ["6. Subsample 1B: Post-2022 Norm.", "2023-01..2026-10", "922", "0.2586 (0.9355)", "0.9389 / 0.9270", "3.427 (0.0645)", "-0.0680%", "-0.0110% / -0.130%", "Fast 1-day absorption"],
            ["7. Subsample 2A: SBV +-3% FX Band", "2020-06..2022-10-14", "552", "3.0919 (0.0092**)", "0.0485* / 0.0330*", "1.829 (0.1768)", "-0.0684%", "-0.1381% / -0.258%", "Rigid FX -> equity hit"],
            ["8. Subsample 2B: SBV +-5% FX Band", "2022-10-17..2026-10", "975", "1.2076 (0.3035)", "0.4534 / 0.4318", "3.762 (0.0527)", "-0.0751%", "-0.0365% / -0.145%", "Wider FX band buffers lags"],
        ],
        col_widths_dxa=[1650, 1020, 520, 1100, 950, 920, 720, 950, 1242],
        font_size_half_pt=16,
    ))
    add_p("", space_after=60)

    # =========================================================================
    # 6. CONCLUSION
    # =========================================================================
    add_h1("6. Conclusion")
    add_p(
        "This study examined the short-run dynamic transmission, long-run equilibrium, and out-of-sample "
        "predictability linking Vietnamese stock returns to USD/VND, US 10-year Treasury yields, and Brent crude "
        "oil. In the short run, US 10-year yield changes significantly Granger-cause both Vietnamese equity "
        "returns (F = 3.30, p = 0.0056) and USD/VND depreciation (F = 3.85, p = 0.0018), with a one-standard-deviation "
        "(5.94 bps) US rate shock depressing Vietnamese equities by -0.0666% at h = 1 and -0.0938% at h = 5 "
        "(robust across reversed Cholesky ordering, Pesaran–Shin GIRFs, provider-gap exclusion, and lag lengths). "
        "Domestic equity returns also Granger-cause USD/VND (F = 3.36, p = 0.0049), whereas direct oil and FX "
        "lags have negligible predictive power for equities, and all three macro variables jointly explain 1.81% "
        "of 20-day equity variance. In the long run, cointegration exists over the full 2016–2026 decade "
        "(trace = 67.99, max-eig = 40.34) and marginally over 2020–2026 (trace = 51.99), but the equity "
        "adjustment speed is statistically zero (alpha_VN = -0.0008, p = 0.728), indicating that equilibrium is "
        "restored through global oil repricing rather than domestic stock-market error correction. Out of sample, "
        "a parsimonious VAR(1) achieves a positive R^2_OOS (+0.34%) over the random walk, but Diebold–Mariano "
        "tests confirm no statistically significant gain over an AR(1) or random walk."
    )
    add_p(
        "For commercial bank risk managers and ALM committees, our findings imply that overnight US Treasury "
        "yield spikes act as a simultaneous stress driver for USD/VND liquidity and domestic equity collateral "
        "values—especially when the exchange rate approaches the edge of the SBV's crawling band—so market and "
        "margin-lending stress tests should model US rate shocks and domestic equity-to-FX spillovers jointly. "
        "For equity portfolio managers, static linear FX or Brent futures hedges offer virtually no daily "
        "variance reduction (<0.6% FEVD share); instead, tactical risk management should focus on the 1-to-5-day "
        "window following US monetary policy shocks. Six limitations qualify our analysis and point to clear "
        "extensions: (1) HNX history truncation prior to May 2020 (addressed via our 2016–2026 VN-Index check); "
        "(2) 28 unscheduled 2020–2021 vnstock provider gaps (shown not to drive causality when excluded); "
        "(3) strong ARCH effects in VAR residuals (successfully absorbed by our Student-t GARCH(1,1) and "
        "GJR-GARCH(1,1) filters, motivating a full multivariate DCC-GARCH-in-mean extension); (4) linear VAR/VECM "
        "approximations of the SBV's bounded USD/VND regime (motivating a threshold VECM around the +-5% band); "
        "(5) asynchronous Hanoi (08:00 UTC) vs. US closing times (motivating overnight vs. intraday return "
        "decomposition); and (6) time-varying parameter regimes across global tightening vs. easing cycles."
    )

    # =========================================================================
    # PAGE BREAK BEFORE REFERENCES & APPENDICES (Excluded from <= 15-page cap)
    # =========================================================================
    body.append(make_page_break())
    add_h1("References")
    refs = [
        "[TODO: Insert assigned ATFB (NHAE408) course textbook citation manually before submission — verify against official course syllabus; do not guess.]",
        "ATFB (NHAE408) Teaching Team. (2026). Midterm Essay Brief, Template Notebook (midterm_template.ipynb), and Report Template (report_template.docx). Foreign Trade University – Ho Chi Minh City Campus.",
        "Batten, J. A., Kinateder, H., Szilagyi, P. G., & Wagner, N. F. (2019). Time-varying energy and stock market integration in Asia. Energy Economics, 80, 777–792. https://doi.org/10.1016/j.eneco.2019.01.008",
        "Bernanke, B. S., & Kuttner, K. N. (2005). What explains the stock market's reaction to Federal Reserve policy? The Journal of Finance, 60(3), 1221–1257. https://doi.org/10.1111/j.1540-6261.2005.00760.x",
        "Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. Journal of Econometrics, 31(3), 307–327. https://doi.org/10.1016/0304-4076(86)90063-1",
        "Branson, W. H. (1983). Macroeconomic determinants of real exchange risk. In R. J. Herring (Ed.), Managing Foreign Exchange Risk (pp. 33–74). Cambridge University Press.",
        "Campbell, J. Y., & Thompson, S. B. (2008). Predicting excess stock returns out of sample: Can anything beat the historical average? The Review of Financial Studies, 21(4), 1509–1531. https://doi.org/10.1093/rfs/hhm055",
        "Christoffersen, P. F. (2012). Elements of Financial Risk Management (2nd ed.). Academic Press. https://doi.org/10.1016/C2009-0-64134-9 [Supplementary econometrics reference]",
        "Clark, T. E., & McCracken, M. W. (2001). Tests of equal forecast accuracy and encompassing for nested models. Journal of Econometrics, 105(1), 85–110. https://doi.org/10.1016/S0304-4076(01)00071-9",
        "Cont, R. (2001). Empirical properties of asset returns: Stylized facts and statistical issues. Quantitative Finance, 1(2), 223–236. https://doi.org/10.1080/713665670",
        "Cushman, D. O., & Zha, T. (1997). Identifying monetary policy in a small open economy under flexible exchange rates. Journal of Monetary Economics, 39(3), 433–448. https://doi.org/10.1016/S0304-3932(97)00029-9",
        "Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. Journal of Business & Economic Statistics, 13(3), 253–263. https://doi.org/10.1080/07350015.1995.10524599",
        "Dornbusch, R., & Fischer, S. (1980). Exchange rates and the current account. American Economic Review, 70(5), 960–971. https://www.jstor.org/stable/1805775",
        "Engle, R. F. (1982). Autoregressive conditional heteroscedasticity with estimates of the variance of United Kingdom inflation. Econometrica, 50(4), 987–1007. https://doi.org/10.2307/1912773",
        "Engle, R. F., & Granger, C. W. J. (1987). Co-integration and error correction: Representation, estimation, and testing. Econometrica, 55(2), 251–276. https://doi.org/10.2307/1913236",
        "Giacomini, R., & White, H. (2006). Tests of conditional predictive ability. Econometrica, 74(6), 1545–1578. https://doi.org/10.1111/j.1468-0262.2006.00718.x",
        "Glosten, L. R., Jagannathan, R., & Runkle, D. E. (1993). On the relation between the expected value and the volatility of the nominal excess return on stocks. The Journal of Finance, 48(5), 1779–1801. https://doi.org/10.1111/j.1540-6261.1993.tb05128.x",
        "Gonçalves, S., & Kilian, L. (2004). Bootstrapping autoregressions with conditional heteroskedasticity of unknown form. Journal of Econometrics, 123(1), 89–120. https://doi.org/10.1016/j.jeconom.2003.10.030",
        "Hakkio, C. S., & Rush, M. (1991). Cointegration: How short is the long run? Journal of International Money and Finance, 10(4), 571–581. https://doi.org/10.1016/0261-5606(91)90008-8",
        "Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction mean squared errors. International Journal of Forecasting, 13(2), 281–291. https://doi.org/10.1016/S0169-2070(96)00719-4",
        "Holm, S. (1979). A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, 6(2), 65–70. https://www.jstor.org/stable/4615733",
        "Johansen, S. (1991). Estimation and hypothesis testing of cointegration vectors in Gaussian vector autoregressive models. Econometrica, 59(6), 1551–1580. https://doi.org/10.2307/2938278",
        "Jones, C. M., & Kaul, G. (1996). Oil and the stock markets. The Journal of Finance, 51(2), 463–491. https://doi.org/10.1111/j.1540-6261.1996.tb02691.x",
        "Kilian, L., & Park, C. (2009). The impact of oil price shocks on the U.S. stock market. International Economic Review, 50(4), 1267–1287. https://doi.org/10.1111/j.1468-2354.2009.00568.x",
        "Koop, G., Pesaran, M. H., & Potter, S. M. (1996). Impulse response analysis in nonlinear multivariate models. Journal of Econometrics, 74(1), 119–147. https://doi.org/10.1016/0304-4076(95)01753-4",
        "Lütkepohl, H. (2005). New Introduction to Multiple Time Series Analysis. Springer. https://doi.org/10.1007/978-3-540-27752-1",
        "Lütkepohl, H., Saikkonen, P., & Trenkler, C. (2001). Maximum eigenvalue versus trace tests for the cointegrating rank of a VAR process. The Econometrics Journal, 4(2), 287–310. https://doi.org/10.1111/1368-423X.00068",
        "Narayan, P. K., & Narayan, S. (2010). Modelling the impact of oil prices on Vietnam's stock prices. Applied Energy, 87(1), 356–361. https://doi.org/10.1016/j.apenergy.2009.05.037",
        "Newey, W. K., & West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. Econometrica, 55(3), 703–708. https://doi.org/10.2307/1913610",
        "Nguyen, C. C., & Bhatti, M. I. (2012). Copula model dependency between oil prices and stock markets: Evidence from China and Vietnam. Journal of International Financial Markets, Institutions and Money, 22(4), 758–773. https://doi.org/10.1016/j.intfin.2012.03.004",
        "Pesaran, H. H., & Shin, Y. (1998). Generalized impulse response analysis in linear multivariate models. Economics Letters, 58(1), 17–29. https://doi.org/10.1016/S0165-1765(97)00214-0",
        "Phylaktis, K., & Ravazzolo, F. (2005). Stock prices and exchange rate dynamics. Journal of International Money and Finance, 24(7), 1031–1053. https://doi.org/10.1016/j.jimonfin.2005.08.001",
        "Rey, H. (2015). Dilemma not trilemma: The global financial cycle and monetary policy independence (NBER Working Paper No. 21162). National Bureau of Economic Research. https://doi.org/10.3386/w21162",
        "Sims, C. A. (1980). Macroeconomics and reality. Econometrica, 48(1), 1–48. https://doi.org/10.2307/1912017",
        "Sui, L., & Sun, L. (2016). Spillover effects between exchange rates and stock prices: Evidence from BRICS around the recent global financial crisis. Research in International Business and Finance, 36, 459–471. https://doi.org/10.1016/j.ribaf.2015.10.011",
        "Vo, X. V. (2017). Does the exchange rate matter for stock returns in an emerging market? Evidence from Vietnam. Afro-Asian Journal of Finance and Accounting, 7(4), 392–406. [See docs/references.md for full list of 10 verified HOSE/HNX/VNA/BVSC checkpoint bulletins and data sources.]",
        "Vu, T. (2024). vnstock: Vietnamese stock market data toolkit for Python (legacy branch v0.2.9.2.3, commit e8339514). GitHub. https://github.com/thinh-vu/vnstock",
        "Welch, I., & Goyal, A. (2008). A comprehensive look at the empirical performance of equity premium prediction. The Review of Financial Studies, 21(4), 1455–1508. https://doi.org/10.1093/rfs/hhm014",
    ]
    for r_str in refs:
        add_p(r_str, align="left", space_after=60, line_spacing=270, font_size_half_pt=21)

    body.append(make_page_break())
    add_h1("Appendix A. Contribution of each member")
    add_p(
        "Note: Group member names, student IDs, task allocations, and percentage shares (summing to 100%) are left "
        "as explicit placeholders below for manual completion by the group prior to submission. Each member also "
        "completes the individual peer-review form on Microsoft Teams."
    )
    body.append(make_table(
        headers=["Full name", "Student ID", "Tasks", "Share of the work (%)"],
        rows=[
            ["[TODO: Fill in manually]", "[TODO]", "[TODO: e.g., Data pipeline, holiday audit, EDA]", "[TODO: %]"],
            ["[TODO: Fill in manually]", "[TODO]", "[TODO: e.g., VAR(5), GIRFs, GARCH diagnostics]", "[TODO: %]"],
            ["[TODO: Fill in manually]", "[TODO]", "[TODO: e.g., Cointegration, VECM, subsamples]", "[TODO: %]"],
            ["[TODO: Fill in manually]", "[TODO]", "[TODO: e.g., Rolling OOS forecasts, DM tests]", "[TODO: %]"],
            ["[TODO: Fill in manually]", "[TODO]", "[TODO: e.g., Literature review, report editing]", "[TODO: %]"],
            ["Total", "—", "All stages verified by all members", "100%"],
        ],
        col_widths_dxa=[2268, 1600, 3604, 1600],
        font_size_half_pt=20,
    ))

    add_h1("Appendix B. Use of generative AI")
    add_p(
        "In accordance with Section 8 of the ATFB (NHAE408) Midterm Essay Brief, the table below discloses how "
        "generative AI tools were used during the preparation of this project and how every output was verified "
        "by the group."
    )
    body.append(make_table(
        headers=["Tool (Name & Version)", "Used for", "How the output was checked and verified"],
        rows=[
            [
                "Google DeepMind Antigravity Agent (2026)",
                "Structuring modular Python scripts in src/ (data.py, eda.py, var_model.py, cointegration.py, forecast_eval.py, plots.py), implementing wild bootstrap & GIRF routines, and formatting tables.",
                "Every mathematical formula and econometric output was verified against statsmodels/arch documentation and tested with 10 automated unit tests in tests/test_pipeline.py (synthetic data with known analytical solutions).",
            ],
            [
                "Google DeepMind Antigravity Agent (2026)",
                "Cross-checking bibliographic metadata (DOIs, volume/issue/page numbers) and drafting prose structure for group review.",
                "Every citation in References and docs/references.md was verified via live DOI resolver / publisher lookup; 10 vnstock index dates were verified against official VNA/HOSE/HNX/BVSC market reports (0.00 pt error); src/check_report_numbers.py verified every report number against results/tables/*.csv.",
            ],
        ],
        col_widths_dxa=[2100, 3200, 3772],
        font_size_half_pt=19,
    ))

    add_h1("Appendix C. Reproducibility and data manifest")
    add_p(
        "Note on Appendix Ordering: Per Section 4 of the ATFB Midterm Essay Brief, Appendix A is the Member "
        "Contribution Table and Appendix B is the Generative-AI Disclosure Statement; reproducibility and "
        "data-manifest documentation is therefore placed here in Appendix C (and in README.md and "
        "docs/data_manifest.md). The full pipeline runs start-to-finish on Python 3.13.3 via python run_all.py "
        "(or Restart & Run All in notebooks/t7_macro_links.ipynb), using fixed random seed 42 for all bootstrap "
        "procedures. When online, src/data.py pulls fresh raw series from vnstock (pinned commit e8339514), "
        "yfinance, and FRED; when offline, it automatically rebuilds data/processed/ from the verified raw CSVs "
        "included in the Microsoft Teams submission archive (ATFB_Essay_Group12_code.zip). Per vnstock license "
        "terms, raw and processed data files are excluded from the public git repository via .gitignore."
    )
    body.append(make_table(
        headers=["Raw Data File (data/raw/)", "Source & Identifier", "Rows", "Date Span", "SHA-256 Prefix (First 24 Hex Chars)"],
        rows=[
            ["vnindex_raw.csv", "vnstock DNSE (VNINDEX)", "1,576", "2020-06-01 .. 2026-10-30", "ee9de5a5e440fa9cc20e2cb7"],
            ["hnxindex_raw.csv", "vnstock DNSE (HNX)", "1,577", "2020-06-01 .. 2026-10-30", "17a860f4aa087c079335e4f5"],
            ["usdvnd_raw.csv", "yfinance (USDVND=X)", "1,671", "2020-06-01 .. 2026-10-30", "c730a86a87f24be775cf1c46"],
            ["oil_raw.csv", "yfinance (BZ=F)", "1,615", "2020-06-01 .. 2026-10-30", "461586c1f19a91ec3ab83333"],
            ["dgs10_raw.csv", "FRED (DGS10)", "1,685", "2020-05-18 .. 2026-10-30", "25ba476347380f28b06ca593"],
            ["vnindex_ext2016_raw.csv", "vnstock DNSE (VNINDEX 10Y)", "2,473", "2016-11-01 .. 2026-10-30", "51071e46872d78c181d5c2b9"],
        ],
        col_widths_dxa=[2100, 2100, 750, 1922, 2200],
        font_size_half_pt=18,
    ))

    if sect_pr is not None:
        body.append(sect_pr)

    # Write output .docx
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
