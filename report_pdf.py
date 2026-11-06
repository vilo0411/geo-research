#!/usr/bin/env python3
"""Render a GEO insights markdown report to PDF with charts.

Usage:
  python report_pdf.py --month 2026-11 [--md reports/geo_insights_2026-11_tong-hop.md] [--source codex]

Charts are computed from data/<month>/<source>/ and inserted where the markdown has
`<!-- chart:NAME -->` markers (hero, named, heatmap, funnel, destination, brand_pages, format).

Unlike geo.py this script needs matplotlib and reportlab (pip install matplotlib reportlab).
Markdown support is a small subset: headings, paragraphs, bullets, numbered lists,
tables, blockquotes, horizontal rules, **bold**, *italic*, `code`.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (HRFlowable, Image, KeepTogether, ListFlowable, ListItem,  # noqa: E402
                                PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

import geo  # noqa: E402

# ---------------------------------------------------------------- design tokens (dataviz reference palette, light)
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_3 = "#8a8983"
GRID = "#e6e5e0"
SURFACE = "#ffffff"
ACCENT = "#2a78d6"          # the brand (highlight)
OTHER = "#c3c2b7"           # every other firm (recessive)
CAT = ["#2a78d6", "#eb6834", "#1baf7a"]                 # validated: first 3 slots, all pairs
ORDINAL = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]  # validated ordinal ramp (funnel stages)
SEQ = ["#f4f3ef", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

FONT_DIR = Path("C:/Windows/Fonts")


def setup_fonts():
    for f in ("arial.ttf", "arialbd.ttf"):
        if (FONT_DIR / f).exists():
            font_manager.fontManager.addfont(str(FONT_DIR / f))
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 9, "text.color": INK, "axes.labelcolor": INK_2,
        "xtick.color": INK_2, "ytick.color": INK, "axes.edgecolor": GRID, "axes.linewidth": 0.8,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.spines.top": False, "axes.spines.right": False,
    })
    pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_DIR / "arialbd.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Italic", str(FONT_DIR / "ariali.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(FONT_DIR / "arialbi.ttf")))
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-BoldItalic")


def style_axes(ax, grid_axis="x"):
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    for side in ("left", "top", "right"):
        ax.spines[side].set_visible(False)


def title(fig, text, sub=None):
    fig.text(0.01, 0.98, text, ha="left", va="top", fontsize=11, fontweight="bold", color=INK)
    if sub:
        fig.text(0.01, 0.915, sub, ha="left", va="top", fontsize=8.5, color=INK_2)


# ---------------------------------------------------------------- data


class Data:
    def __init__(self, month, source):
        self.month, self.source = month, source
        t = geo.load_month(month, source)
        if t is None:
            sys.exit(f"Không có dữ liệu {month}/{source}")
        self.t = t
        brand = geo.load_brand()
        self.brand = brand["BRAND"]
        self.short = brand.get("BRAND_ALIASES", [self.brand])[0]
        self.clf = geo.Classifier(geo.load_entities(brand), geo.load_source_types(), geo.load_page_types())
        raw = {r["prompt_id"]: r["question"] for r in geo.read_csv(geo.CONFIG / "prompts.csv")}
        self.questions = {pid: p["question"] for pid, p in geo.load_prompts(brand).items()}
        self.branded = {p for p, q in raw.items() if "{BRAND}" in q}
        key = self.key
        self.ub = {key(r) for r in t["runs"] if r["prompt_id"] not in self.branded}
        self.br = {key(r) for r in t["runs"] if r["prompt_id"] in self.branded}

    @staticmethod
    def key(r):
        return (r["prompt_id"], r["run"])

    def label(self, e):
        return self.short if e == self.brand else e

    def funnel(self):
        site, ret, cit, named = (defaultdict(set) for _ in range(4))
        for q in self.t["queries"]:
            if self.key(q) in self.ub:
                for h in geo.SITE_Q_RE.findall(q["query"]):
                    ent = self.clf.entity_for(h.lower().removeprefix("www."))
                    if ent:
                        site[ent["entity"]].add(self.key(q))
        for r in self.t["retrieved"]:
            if self.key(r) in self.ub and r["entity"]:
                ret[r["entity"]].add(self.key(r))
                if r["cited"] == "1":
                    cit[r["entity"]].add(self.key(r))
        for m in self.t["mentions"]:
            if self.key(m) in self.ub:
                named[m["entity"]].add(self.key(m))
        return site, ret, cit, named


# ---------------------------------------------------------------- charts


def save(fig, out: Path):
    fig.savefig(out, dpi=220)
    plt.close(fig)
    return out


def chart_named(d: Data, out: Path, top=10):
    _, _, _, named = d.funnel()
    ents = sorted(named, key=lambda e: -len(named[e]))[:top]
    if d.brand not in ents:
        ents.append(d.brand)
    vals = [len(named[e]) for e in ents]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    fig.subplots_adjust(left=0.16, right=0.95, top=0.80, bottom=0.08)
    y = range(len(ents))[::-1]
    ax.barh(list(y), vals, height=0.62, color=[ACCENT if e == d.brand else OTHER for e in ents])
    ax.set_yticks(list(y), [d.label(e) for e in ents])
    for yi, v, e in zip(y, vals, ents):
        ax.text(v + 1, yi, f"{v}", va="center", fontsize=8.5,
                color=INK if e == d.brand else INK_2, fontweight="bold" if e == d.brand else "normal")
    style_axes(ax)
    ax.set_xlim(0, max(vals) * 1.12)
    title(fig, "Số lượt được nhắc tên khi câu hỏi không nêu tên CTCK",
          f"{len(d.ub)} lượt, 42 câu hỏi. {d.short} tô màu, các CTCK khác màu xám.")
    return save(fig, out)


def chart_heatmap(d: Data, out: Path):
    pids = sorted({r["prompt_id"] for r in d.t["runs"] if r["group"] == "2_chon_ctck" and r["prompt_id"] not in d.branded})
    runs = Counter(r["prompt_id"] for r in d.t["runs"])
    cnt = defaultdict(Counter)
    for m in d.t["mentions"]:
        if m["prompt_id"] in pids:
            cnt[m["prompt_id"]][m["entity"]] += 1
    tot = Counter()
    for c in cnt.values():
        tot.update(c)
    ents = [e for e, _ in tot.most_common(9) if e != d.brand] + [d.brand]
    grid = [[cnt[p][e] / runs[p] for e in ents] for p in pids]
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    fig.subplots_adjust(left=0.40, right=0.96, top=0.76, bottom=0.04)
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(ents)), [d.label(e) for e in ents], rotation=35, fontsize=8, ha="left",
                  rotation_mode="anchor")
    ax.xaxis.tick_top()
    labels = [f"{p}  {d.questions[p][:42]}{'…' if len(d.questions[p]) > 42 else ''}" for p in pids]
    ax.set_yticks(range(len(pids)), labels, fontsize=8)
    for i, p in enumerate(pids):
        for j, e in enumerate(ents):
            n = cnt[p][e]
            if n or e == d.brand:
                ax.text(j, i, f"{n}/{runs[p]}", ha="center", va="center", fontsize=7.5,
                        color="#ffffff" if grid[i][j] >= 0.6 else INK)
    j = len(ents) - 1
    ax.add_patch(plt.Rectangle((j - 0.5, -0.5), 1, len(pids), fill=False, edgecolor=INK, linewidth=1.4))
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([x - 0.5 for x in range(1, len(ents))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(pids))], minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    title(fig, "Nhóm \"chọn CTCK\": số lượt mỗi CTCK được nhắc / số lượt hỏi",
          f"Màu càng đậm thì CTCK được nhắc càng đều. Cột viền đen: {d.short}.")
    return save(fig, out)


def chart_funnel(d: Data, out: Path):
    site, ret, cit, named = d.funnel()
    ents = [e for e in ("SSI", "TCBS", "VNDIRECT", "VPS", "DNSE", "Phú Hưng") if e in ret or e in named] + [d.brand]
    stages = [("Nhận lệnh site:", site), ("Được đọc", ret), ("Được trích dẫn", cit), ("Được nhắc tên", named)]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    fig.subplots_adjust(left=0.13, right=0.97, top=0.76, bottom=0.08)
    h = 0.19
    n = len(ents)
    for si, (lab, data) in enumerate(stages):
        ys = [(n - 1 - i) + (1.5 - si) * h for i in range(n)]
        vals = [len(data[e]) for e in ents]
        ax.barh(ys, vals, height=h * 0.9, color=ORDINAL[si], label=lab, edgecolor=SURFACE, linewidth=0.6)
    # one combined label for the brand instead of four crowded numbers
    vals = [len(s[d.brand]) for _, s in stages]
    ax.text(max(vals) + 2, 0, f"site: {vals[0]} · đọc {vals[1]} · trích dẫn {vals[2]} · nhắc tên {vals[3]}",
            va="center", fontsize=8, color=INK, fontweight="bold")
    ax.set_yticks(range(n)[::-1], [d.label(e) for e in ents])
    for lbl in ax.get_yticklabels():
        if lbl.get_text() == d.short:
            lbl.set_fontweight("bold")
    style_axes(ax)
    ax.legend(ncol=4, loc="upper left", bbox_to_anchor=(-0.13, 1.13), frameon=False, fontsize=8,
              handlelength=1.2, columnspacing=1.2)
    title(fig, "Phễu hiển thị theo CTCK (câu hỏi không nêu tên, đơn vị: lượt)",
          f"{d.short} rơi khỏi phễu ngay ở bước đầu: gần như không được nhắm tới bằng lệnh site:.")
    return save(fig, out)


def chart_destination(d: Data, out: Path):
    groups = sorted({c["group"] for c in d.t["citations"]})
    segs = [("Website " + d.short, lambda c: c["source_type"] == "chinh_chu"),
            ("Website CTCK khác", lambda c: c["source_type"] == "doi_thu_ctck"),
            ("Nguồn trung gian", lambda c: c["source_type"] not in ("chinh_chu", "doi_thu_ctck"))]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    fig.subplots_adjust(left=0.17, right=0.97, top=0.74, bottom=0.08)
    y = list(range(len(groups)))[::-1]
    left = [0.0] * len(groups)
    for si, (lab, fn) in enumerate(segs):
        vals = []
        for g in groups:
            cs = [c for c in d.t["citations"] if c["group"] == g]
            vals.append(sum(fn(c) for c in cs) / len(cs) * 100 if cs else 0)
        ax.barh(y, vals, left=left, height=0.62, color=CAT[si], label=lab, edgecolor=SURFACE, linewidth=1.5)
        for yi, lft, v in zip(y, left, vals):
            if v >= 8:  # relief rule: direct labels (aqua is below 3:1 contrast)
                ax.text(lft + v / 2, yi, f"{v:.0f}%", ha="center", va="center", fontsize=7.5, color="#ffffff",
                        fontweight="bold")
        left = [a + b for a, b in zip(left, vals)]
    ax.set_yticks(y, groups, fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    style_axes(ax)
    ax.legend(ncol=3, loc="upper left", bbox_to_anchor=(-0.17, 1.17), frameon=False, fontsize=8, handlelength=1.2)
    title(fig, "Link trích dẫn trỏ về đâu, theo nhóm câu hỏi", None)
    return save(fig, out)


def short_url(u: str) -> str:
    u = re.sub(r"^https?://", "", u).split("?")[0]
    host, _, path = u.partition("/")
    if host.startswith("extgw."):
        name = path.rsplit("/", 1)[-1]
        return "PDF: " + (name[:34] + "…" if len(name) > 35 else name)
    path = "/" + path
    if host.startswith("elearn."):
        path = "elearn" + path
    return path if len(path) <= 44 else path[:43] + "…"


def chart_brand_pages(d: Data, out: Path, top=14):
    rr, rc = defaultdict(set), defaultdict(set)
    for r in d.t["retrieved"]:
        if r["is_brand"] == "1":
            u = r["url"].split("?")[0]
            rr[u].add(d.key(r))
            if r["cited"] == "1":
                rc[u].add(d.key(r))
    urls = sorted(rr, key=lambda u: -len(rr[u]))[:top]
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    fig.subplots_adjust(left=0.42, right=0.95, top=0.80, bottom=0.06)
    y = list(range(len(urls)))[::-1]
    ax.barh(y, [len(rr[u]) for u in urls], height=0.66, color=ORDINAL[0], label="Được đọc")
    ax.barh(y, [len(rc[u]) for u in urls], height=0.36, color=ORDINAL[3], label="Được trích dẫn")
    ax.set_yticks(y, [short_url(u) for u in urls], fontsize=7.8)
    for yi, u in zip(y, urls):
        r = len(rc[u]) / len(rr[u])
        ax.text(len(rr[u]) + 0.4, yi, f"{r:.0%}", va="center", fontsize=7.5,
                color=INK if r >= 0.5 else INK_2, fontweight="bold" if r >= 0.5 else "normal")
    style_axes(ax)
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(-0.72, 1.0), frameon=False, fontsize=8, handlelength=1.2)
    title(fig, f"Trang {d.short}: được đọc so với được trích dẫn (số lượt)",
          "Số % bên phải là tỷ lệ trích dẫn. Trang PDF và /en/ gần như không được chọn.")
    return save(fig, out)


def chart_format(d: Data, out: Path):
    ret, cit = Counter(), Counter()
    for r in d.t["retrieved"]:
        if r["source_type"] in ("chinh_chu", "doi_thu_ctck"):
            u = r["url"].lower().split("?")[0]
            f = "PDF" if u.endswith(".pdf") else ("Bản tiếng Anh /en/" if "/en/" in u else "HTML tiếng Việt")
            ret[f] += 1
            cit[f] += r["cited"] == "1"
    fmts = ["HTML tiếng Việt", "PDF", "Bản tiếng Anh /en/"]
    rates = [cit[f] / ret[f] * 100 if ret[f] else 0 for f in fmts]
    fig, ax = plt.subplots(figsize=(7.2, 2.1))
    fig.subplots_adjust(left=0.2, right=0.95, top=0.70, bottom=0.12)
    y = [2, 1, 0]
    ax.barh(y, rates, height=0.55, color=[ACCENT, OTHER, OTHER])
    ax.set_yticks(y, fmts)
    for yi, f, r in zip(y, fmts, rates):
        ax.text(r + 0.5, yi, f"{r:.0f}%  ({cit[f]}/{ret[f]:,} lượt đọc)".replace(",", "."), va="center", fontsize=8,
                color=INK_2)
    ax.set_xlim(0, max(rates) * 1.6)
    ax.set_xticks([])
    style_axes(ax)
    ax.spines["bottom"].set_visible(False)
    title(fig, "Tỷ lệ được trích dẫn theo định dạng trang (website mọi CTCK)", None)
    return save(fig, out)


MIX_TYPES = ["chinh_chu", "doi_thu_ctck", "co_quan_nha_nuoc", "co_quan_nuoc_ngoai", "quy_dau_tu", "bao_chi",
             "toplist", "blog_kien_thuc", "phap_ly", "ngan_hang_fintech", "du_lieu_tai_chinh"]
GROUP_LABEL = {"1_kien_thuc": "1. Kiến thức", "2_chon_ctck": "2. Chọn CTCK", "3_phi_margin": "3. Phí, margin",
               "4_mo_tai_khoan": "4. Mở tài khoản", "5_san_pham": "5. Sản phẩm", "6_xac_minh": "6. Xác minh",
               "7_van_hanh": "7. Vận hành"}


def chart_source_mix(d: Data, out: Path):
    groups = sorted({r["group"] for r in d.t["runs"]})
    short = {"chinh_chu": f"Web {d.short}", "doi_thu_ctck": "Web CTCK khác", "co_quan_nha_nuoc": "Nhà nước VN",
             "co_quan_nuoc_ngoai": "Nước ngoài", "quy_dau_tu": "Quỹ", "bao_chi": "Báo chí", "toplist": "Toplist",
             "blog_kien_thuc": "Blog", "phap_ly": "Luật", "ngan_hang_fintech": "Ngân hàng", "du_lieu_tai_chinh": "Dữ liệu TC"}
    labels = [short[k] for k in MIX_TYPES]
    panels = [("% trang được đọc", d.t["retrieved"]), ("% link được trích dẫn", d.t["citations"])]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.6), sharey=True)
    fig.subplots_adjust(left=0.15, right=0.955, top=0.71, bottom=0.08, wspace=0.06)
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    for ax, (ptitle, rows) in zip(axes, panels):
        grid = []
        for g in groups:
            rs = [r for r in rows if r["group"] == g]
            c = Counter(r["source_type"] for r in rs)
            grid.append([c[k] / len(rs) if rs else 0 for k in MIX_TYPES])
        ax.imshow(grid, cmap=cmap, vmin=0, vmax=0.6, aspect="auto")
        for i in range(len(groups)):
            for j in range(len(MIX_TYPES)):
                v = grid[i][j]
                if v >= 0.005:
                    ax.text(j, i, f"{v * 100:.0f}", ha="center", va="center", fontsize=6.5,
                            color="#ffffff" if v >= 0.3 else INK)
        ax.set_xticks(range(len(MIX_TYPES)), labels, rotation=50, ha="left", rotation_mode="anchor", fontsize=7.5)
        ax.xaxis.tick_top()
        ax.set_yticks(range(len(groups)), [GROUP_LABEL.get(g, g) for g in groups], fontsize=8)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xticks([x - 0.5 for x in range(1, len(MIX_TYPES))], minor=True)
        ax.set_yticks([y - 0.5 for y in range(1, len(groups))], minor=True)
        ax.grid(which="minor", color=SURFACE, linewidth=1.5)
        ax.tick_params(which="minor", length=0)
        ax.set_xlabel(ptitle, fontsize=8.5, fontweight="bold", color=INK, labelpad=6)
    title(fig, "Mỗi nhóm câu hỏi đọc nguồn gì và tin nguồn gì (%)",
          "Ô đậm bên phải mà nhạt bên trái = nguồn được tin. Ngược lại = được đọc nhưng bị bỏ qua.")
    return save(fig, out)


def chart_helpcenter(d: Data, out: Path):
    sites = [("help.tcbs.com.vn", "help.tcbs.com.vn (hỗ trợ)", True), ("support.vndirect.com.vn", "support.vndirect.com.vn (hỗ trợ)", True),
             ("ssi.com.vn", "ssi.com.vn", False), ("vndirect.com.vn", "vndirect.com.vn (trang chính)", False),
             ("tcbs.com.vn", "tcbs.com.vn (trang chính)", False)]
    rows = []
    for dom, lab, is_help in sites:
        rs = [r for r in d.t["retrieved"] if r["domain"] == dom]
        if rs:
            rows.append((lab, sum(r["cited"] == "1" for r in rs), len(rs), is_help))
    hd = [r for r in d.t["retrieved"] if r["is_brand"] == "1" and "/huong-dan" in r["url"]
          and d.key(r) in d.br]
    if hd:
        rows.append((f"{d.short} /huong-dan/*", sum(r["cited"] == "1" for r in hd), len(hd), None))
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    fig.subplots_adjust(left=0.34, right=0.95, top=0.72, bottom=0.06)
    y = list(range(len(rows)))[::-1]
    col = {True: ACCENT, False: OTHER, None: CAT[1]}
    ax.barh(y, [c / n * 100 for _, c, n, _ in rows], height=0.6, color=[col[h] for *_, h in rows])
    ax.set_yticks(y, [r[0] for r in rows], fontsize=8)
    for yi, (_, c, n, _) in zip(y, rows):
        ax.text(c / n * 100 + 0.8, yi, f"{c / n:.0%}  ({c}/{n})", va="center", fontsize=8, color=INK_2)
    ax.set_xlim(0, 60)
    ax.set_xticks([])
    style_axes(ax)
    ax.spines["bottom"].set_visible(False)
    title(fig, "Tỷ lệ chọn: số trang được trích dẫn / số trang được đọc",
          f"Xanh: trung tâm hỗ trợ của đối thủ. Xám: trang chính. Cam: trang hướng dẫn {d.short}.")
    return save(fig, out)


CHARTS = {"named": chart_named, "heatmap": chart_heatmap, "funnel": chart_funnel,
          "destination": chart_destination, "brand_pages": chart_brand_pages, "format": chart_format,
          "source_mix": chart_source_mix, "helpcenter": chart_helpcenter}


# ---------------------------------------------------------------- markdown -> reportlab


def styles():
    base = dict(fontName="Arial", textColor=colors.HexColor(INK), leading=13.5, fontSize=9.6, alignment=TA_LEFT)
    return {
        "h1": ParagraphStyle("h1", **{**base, "fontName": "Arial-Bold", "fontSize": 17, "leading": 21, "spaceAfter": 6}),
        "h2": ParagraphStyle("h2", **{**base, "fontName": "Arial-Bold", "fontSize": 12.5, "leading": 16,
                                      "spaceBefore": 10, "spaceAfter": 4}),
        "h3": ParagraphStyle("h3", **{**base, "fontName": "Arial-Bold", "fontSize": 10.5, "spaceBefore": 6}),
        "p": ParagraphStyle("p", **{**base, "spaceAfter": 5}),
        "quote": ParagraphStyle("q", **{**base, "fontSize": 8.8, "leading": 12.5, "textColor": colors.HexColor(INK_2),
                                        "leftIndent": 8, "borderPadding": (5, 6, 5, 6),
                                        "backColor": colors.HexColor("#f4f3ef"), "spaceBefore": 4, "spaceAfter": 8}),
        "cell": ParagraphStyle("c", **{**base, "fontSize": 8.2, "leading": 10.5}),
        "cellh": ParagraphStyle("ch", **{**base, "fontName": "Arial-Bold", "fontSize": 8.2, "leading": 10.5,
                                         "textColor": colors.HexColor(INK_2)}),
        "tile_v": ParagraphStyle("tv", **{**base, "fontName": "Arial-Bold", "fontSize": 24, "leading": 28}),
        "tile_l": ParagraphStyle("tl", **{**base, "fontSize": 8.5, "leading": 11, "textColor": colors.HexColor(INK_2)}),
    }


def inline(s: str) -> str:
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"`([^`]+)`", r'<font color="#52514e">\1</font>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", s)
    return s


def md_table(lines, st, width):
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines]
    rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    lens = [max(min(len(r[i]), 60) for r in rows) + 4 for i in range(ncol)]
    widths = [width * x / sum(lens) for x in lens]
    data = [[Paragraph(inline(c), st["cellh"] if i == 0 else st["cell"]) for c in r] for i, r in enumerate(rows)]
    tb = Table(data, colWidths=widths, repeatRows=1)
    tb.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(INK_3)),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor(GRID)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tb


def hero(d: Data, st, width):
    _, _, _, named = d.funnel()
    ub_n = len(named[d.brand])
    br_runs = [r for r in d.t["runs"] if d.key(r) in d.br]
    br_n = sum(r["brand_mentioned"] == "1" for r in br_runs)
    site, _, _, _ = d.funnel()
    top = max(site, key=lambda e: len(site[e]))
    tiles = [
        (f"{ub_n}/{len(d.ub)}", f"lượt nhắc {d.short} khi khách <b>không nêu tên</b> ({ub_n / len(d.ub):.1%})"),
        (f"{br_n}/{len(br_runs)}", f"lượt nhắc {d.short} khi khách <b>có nêu tên</b> ({br_n / len(br_runs):.0%})"),
        (f"{len(site[d.brand])}", f"lệnh tìm <b>site:</b> nhắm vào {d.short} (so với {top}: {len(site[top])})"),
    ]
    cells = [[Paragraph(v, st["tile_v"]), Paragraph(lbl, st["tile_l"])] for v, lbl in tiles]
    tb = Table([[c for c in cells]], colWidths=[width / 3] * 3)
    inner = [Table([[c[0]], [c[1]]], colWidths=[width / 3 - 12]) for c in cells]
    tb = Table([inner], colWidths=[width / 3] * 3)
    tb.setStyle(TableStyle([
        ("BOX", (0, 0), (0, 0), 0.6, colors.HexColor(GRID)), ("BOX", (1, 0), (1, 0), 0.6, colors.HexColor(GRID)),
        ("BOX", (2, 0), (2, 0), 0.6, colors.HexColor(GRID)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tb


def build(md_path: Path, d: Data, out_pdf: Path, chart_dir: Path):
    st = styles()
    doc = SimpleDocTemplate(str(out_pdf), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title=f"GEO insights {d.month}", author="GEO tracker")
    width = A4[0] - 36 * mm
    story = []
    lines = md_path.read_text(encoding="utf-8").splitlines()
    i = 0
    para = []

    def flush():
        if para:
            story.append(Paragraph(inline(" ".join(para)), st["p"]))
            para.clear()

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        m = re.match(r"<!--\s*chart:(\w+)\s*-->", s)
        if m:
            flush()
            name = m.group(1)
            if name == "hero":
                story += [Spacer(1, 4), hero(d, st, width), Spacer(1, 8)]
            elif name in CHARTS:
                png = CHARTS[name](d, chart_dir / f"{name}.png")
                img = Image(str(png), width=width, height=width * plt.imread(png).shape[0] / plt.imread(png).shape[1])
                story += [Spacer(1, 4), img, Spacer(1, 6)]
            i += 1
            continue
        if not s:
            flush()
        elif s.startswith("# "):
            flush()
            story.append(Paragraph(inline(s[2:]), st["h1"]))
        elif s.startswith("## "):
            flush()
            story.append(Paragraph(inline(s[3:]), st["h2"]))
        elif s.startswith("### "):
            flush()
            story.append(Paragraph(inline(s[4:]), st["h3"]))
        elif s == "---":
            flush()
            story.append(HRFlowable(width="100%", color=colors.HexColor(GRID), thickness=0.8, spaceBefore=4, spaceAfter=4))
        elif s.startswith(">"):
            flush()
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip().lstrip(">").strip())
                i += 1
            story.append(Paragraph(inline(" ".join(q)), st["quote"]))
            continue
        elif s.startswith("|"):
            flush()
            tl = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tl.append(lines[i])
                i += 1
            story += [md_table(tl, st, width), Spacer(1, 6)]
            continue
        elif re.match(r"^(- |\d+\. )", s):
            flush()
            numbered = bool(re.match(r"^\d+\. ", s))
            items = []
            while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i].strip()):
                items.append(re.sub(r"^(- |\d+\. )", "", lines[i].strip()))
                i += 1
                while i < len(lines) and lines[i].startswith("   ") and lines[i].strip() and \
                        not re.match(r"^(- |\d+\. )", lines[i].strip()):
                    items[-1] += " " + lines[i].strip()
                    i += 1
            lst = ListFlowable([ListItem(Paragraph(inline(t), st["p"]), leftIndent=12) for t in items],
                               bulletType="1" if numbered else "bullet", start="1" if numbered else None,
                               bulletFontName="Arial", bulletFontSize=8.5, leftIndent=14,
                               bulletColor=colors.HexColor(INK_2))
            story.append(lst)
            continue
        else:
            para.append(s)
        i += 1
    flush()

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Arial", 7.5)
        canvas.setFillColor(colors.HexColor(INK_3))
        canvas.drawString(18 * mm, 9 * mm, f"GEO tracker · {d.brand} · tháng {d.month} · nguồn: {geo.SOURCE_LABEL[d.source]}")
        canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Trang {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    ap.add_argument("--source", default="codex", choices=geo.SOURCES)
    ap.add_argument("--md", help="markdown file (default reports/geo_insights_<month>_tong-hop.md)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    setup_fonts()
    md = Path(args.md) if args.md else geo.REPORTS / f"geo_insights_{args.month}_tong-hop.md"
    chart_dir = geo.REPORTS / f"charts_{args.month}"
    chart_dir.mkdir(parents=True, exist_ok=True)
    out = md.with_suffix(".pdf")
    try:
        with open(out, "ab"):
            pass
    except PermissionError:  # the PDF is open in a viewer on Windows
        out = md.with_name(md.stem + "_moi.pdf")
        print(f"File PDF cũ đang mở nên không ghi đè được. Ghi sang {out.name}")
    build(md, Data(args.month, args.source), out, chart_dir)
    print(f"Đã ghi {out}\nBiểu đồ PNG: {chart_dir}")


if __name__ == "__main__":
    main()
