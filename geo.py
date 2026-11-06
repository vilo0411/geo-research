#!/usr/bin/env python3
"""GEO tracker: measure how ChatGPT mentions and cites a securities brand.

Two sources, kept in separate data folders (data/<month>/<source>/):
  codex   - automated. Every planned run is asked through `codex exec` in an isolated,
            ephemeral session. A proxy for ChatGPT web, NOT identical to it.
  chatgpt - small manual sample asked on chatgpt.com, read from the account data export.
            Used to calibrate how far the codex proxy is from the real web experience.

Monthly workflow (see README.md):
  python geo.py codex-run  --month 2026-12        -> exports/2026-12/codex/*.json, then parse
  python geo.py checklist  --month 2026-12        -> ~20 runs to ask by hand on chatgpt.com
  python geo.py parse      exports/2026-12/conversations.json --month 2026-12
  python geo.py report     --month 2026-12 [--source chatgpt]
  python geo.py calibrate  --month 2026-12        -> codex vs chatgpt gap on the same prompts

Standard library only. The ChatGPT export format is undocumented, so extraction is defensive
(recursive search for url/query fields) and `inspect` exists to verify it.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config"
# GEO_WORKDIR lets tests write outputs somewhere other than the real data folders
WORK = Path(os.environ.get("GEO_WORKDIR", ROOT))
DATA = WORK / "data"
EXPORTS = WORK / "exports"
REPORTS = WORK / "reports"
REVIEW = WORK / "review"
SOURCES = ("codex", "chatgpt")
SOURCE_LABEL = {"codex": "Codex CLI (tự động)", "chatgpt": "ChatGPT web (hỏi tay)"}


def data_dir(month: str, source: str) -> Path:
    return DATA / month / source

TITLE_RE = re.compile(r"^\s*(Q\d{3})\s*-\s*r(\d+)\b", re.IGNORECASE)
CITE_MARKER_RE = re.compile(r".*?", re.DOTALL)  # inline citation tokens
PUA_RE = re.compile(r"[-]")
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
URL_RE = re.compile(r"https?://[^\s)\]>\"']+")
QUERY_IN_TEXT_RE = re.compile(r'"q"\s*:\s*"((?:[^"\\]|\\.)+)"')
REF_TOKEN_RE = re.compile(r"turn\d+(?:search|news|view|fetch|image)\d+")  # codex/chatgpt source ids
REVIEW_GROUPS = {"3_phi_margin", "6_xac_minh", "7_van_hanh"}

# ---------------------------------------------------------------- config


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig so Excel opens Vietnamese text correctly
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def load_brand() -> dict:
    return json.loads((CONFIG / "brand.json").read_text(encoding="utf-8"))


def render(text: str, brand: dict) -> str:
    for k, v in brand.items():
        if isinstance(v, str):
            text = text.replace("{" + k + "}", v)
    return text


def load_prompts(brand: dict) -> dict[str, dict]:
    out = {}
    for r in read_csv(CONFIG / "prompts.csv"):
        r["question"] = render(r["question"], brand)
        r["runs_target"] = int(r.get("runs_target") or 3)
        out[r["prompt_id"].upper()] = r
    return out


def load_entities(brand: dict) -> list[dict]:
    ents = []
    for r in read_csv(CONFIG / "entities.csv"):
        name = render(r["entity"], brand)
        aliases = [render(a, brand).strip() for a in r["aliases"].split("|") if a.strip()]
        if r["is_brand"] == "1":
            aliases += brand.get("BRAND_ALIASES", [])
        # accept "https://www.x.vn/" as well as bare "x.vn"
        domains = [domain_of(d if "://" in d else "https://" + d)
                   for d in (render(d, brand).strip() for d in r["domains"].split("|")) if d]
        aliases = sorted(set(a for a in aliases if a and "{" not in a), key=len, reverse=True)
        ents.append({
            "entity": name,
            "is_brand": r["is_brand"] == "1",
            "patterns": [re.compile(r"(?<!\w)" + re.escape(a) + r"(?!\w)", re.IGNORECASE) for a in aliases],
            "domains": [d for d in domains if "{" not in d],
        })
    return ents


def load_source_types() -> list[tuple[str, str]]:
    return [(r["domain"].lower(), r["source_type"]) for r in read_csv(CONFIG / "source_types.csv")]


def load_page_types() -> list[tuple[str, list[str]]]:
    return [(r["page_type"], [k for k in r["url_keywords"].split("|") if k])
            for r in read_csv(CONFIG / "page_types.csv")]


# ---------------------------------------------------------------- url helpers


def normalize_url(url: str) -> str:
    url = url.strip().rstrip(".,;")
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_")]
    host = parts.netloc.lower()
    host = host[4:] if host.startswith("www.") else host  # same page with/without www
    path = parts.path.rstrip("/") or "/"
    return urlunsplit(("https", host, path, urlencode(query), ""))


def domain_of(url: str) -> str:
    host = urlsplit(url).netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def domain_match(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)


def suffix_type(host: str) -> str:
    """Fallback source type from the domain suffix when source_types.csv has no entry."""
    if host.endswith(".gov.vn"):
        return "co_quan_nha_nuoc"
    if host.endswith(".gov") or ".gov." in host or host.endswith(".europa.eu"):
        return "co_quan_nuoc_ngoai"
    if host.endswith((".edu", ".edu.vn")) or ".edu." in host or host.endswith(".ac.uk"):
        return "giao_duc"
    return "khac"


class Classifier:
    def __init__(self, entities, source_types, page_types):
        self.entities, self.source_types, self.page_types = entities, source_types, page_types

    def entity_for(self, host: str):
        for e in self.entities:
            if any(domain_match(host, d) for d in e["domains"]):
                return e
        return None

    def classify(self, url: str) -> dict:
        host = domain_of(url)
        ent = self.entity_for(host)
        if ent:
            stype = "chinh_chu" if ent["is_brand"] else "doi_thu_ctck"
        else:
            stype = next((t for d, t in self.source_types if domain_match(host, d)), None) or suffix_type(host)
        path = urlsplit(url).path.lower()
        if path.strip("/") == "":
            ptype = "trang_chu"
        else:
            ptype = next((p for p, kws in self.page_types if any(k in path for k in kws)), "khac")
        return {
            "url": url, "domain": host, "source_type": stype, "page_type": ptype,
            "entity": ent["entity"] if ent else "", "is_brand": int(bool(ent and ent["is_brand"])),
        }


# ---------------------------------------------------------------- export parsing


def load_export(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):  # some exports wrap the list
        data = data.get("conversations") or list(data.values())
    return data


def active_branch(conv: dict) -> list[dict]:
    """Messages on the branch the user last saw (current_node back to root)."""
    mapping = conv.get("mapping") or {}
    node_id = conv.get("current_node")
    if node_id not in mapping:  # fallback: deepest leaf
        leaves = [k for k, v in mapping.items() if not v.get("children")]
        node_id = leaves[-1] if leaves else None
    chain = []
    while node_id and node_id in mapping:
        node = mapping[node_id]
        if node.get("message"):
            chain.append(node["message"])
        node_id = node.get("parent")
    return list(reversed(chain))


def msg_text(msg: dict) -> str:
    content = msg.get("content") or {}
    parts = content.get("parts")
    if isinstance(parts, list):
        return "\n".join(p for p in parts if isinstance(p, str))
    if isinstance(content.get("text"), str):
        return content["text"]
    return ""


def role(msg: dict) -> str:
    return (msg.get("author") or {}).get("role", "")


def collect_urls(obj) -> list[str]:
    """Recursively collect values of url-like keys."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("url", "safe_url", "link") and isinstance(v, str) and v.startswith("http"):
                found.append(v)
            elif k in ("safe_urls", "urls") and isinstance(v, list):
                found += [u for u in v if isinstance(u, str) and u.startswith("http")]
            else:
                found += collect_urls(v)
    elif isinstance(obj, list):
        for v in obj:
            found += collect_urls(v)
    return found


def collect_queries(obj) -> list[str]:
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("q", "query") and isinstance(v, str):
                found.append(v)
            elif k == "queries" and isinstance(v, list):
                found += [q for q in v if isinstance(q, str)]
                found += collect_queries([q for q in v if not isinstance(q, str)])
            else:
                found += collect_queries(v)
    elif isinstance(obj, list):
        for v in obj:
            found += collect_queries(v)
    return found


def dedupe(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def extract_run(conv: dict) -> dict:
    msgs = active_branch(conv)
    question = next((msg_text(m) for m in msgs if role(m) == "user"), "")
    answers = [m for m in msgs if role(m) == "assistant" and m.get("recipient", "all") == "all"
               and (m.get("content") or {}).get("content_type", "text") == "text" and msg_text(m).strip()]
    final = answers[-1] if answers else None
    answer = msg_text(final) if final else ""
    meta = (final or {}).get("metadata") or {}

    # Cited = sources attached to the final answer (+ inline markdown links)
    cited = collect_urls(meta.get("content_references")) + collect_urls(meta.get("citations"))
    cited += [m.group(2) for m in MD_LINK_RE.finditer(answer)]
    cited = dedupe(normalize_url(u) for u in cited)

    # Retrieved = every search result seen on the branch
    retrieved, queries = [], []
    for m in msgs:
        md = m.get("metadata") or {}
        retrieved += collect_urls(md.get("search_result_groups"))
        for key in ("search_queries", "search_model_queries"):
            queries += collect_queries(md.get(key))
        if role(m) == "assistant" and m.get("recipient", "all") != "all":  # tool call
            for q in QUERY_IN_TEXT_RE.findall(msg_text(m)):
                try:
                    queries.append(json.loads('"' + q + '"'))  # undo JSON escaping
                except json.JSONDecodeError:
                    queries.append(q)
    retrieved = dedupe(normalize_url(u) for u in retrieved + cited)
    return {
        "question": question.strip(),
        "answer": answer,
        "cited": cited,
        "retrieved": retrieved,
        "queries": dedupe(q.strip() for q in queries if q.strip()),
        "has_search": int(bool(retrieved or queries)),
        "model": meta.get("model_slug") or meta.get("default_model_slug") or "",
    }


def clean_answer(text: str) -> str:
    """Answer text with citation tokens and URLs removed, for mention matching."""
    text = CITE_MARKER_RE.sub(" ", text)
    text = PUA_RE.sub(" ", text)
    text = REF_TOKEN_RE.sub(" ", text)
    text = MD_LINK_RE.sub(lambda m: m.group(1), text)
    return URL_RE.sub(" ", text)


def find_mentions(text: str, entities: list[dict]) -> list[tuple[dict, int]]:
    clean = clean_answer(text)
    hits = []
    for e in entities:
        positions = [m.start() for p in e["patterns"] for m in p.finditer(clean)]
        if positions:
            hits.append((e, min(positions)))
    hits.sort(key=lambda x: x[1])
    return hits


def month_of(conv: dict) -> str:
    ts = conv.get("create_time")
    if not ts:
        return "unknown"
    return dt.datetime.fromtimestamp(float(ts)).strftime("%Y-%m")


def norm_q(s: str) -> str:
    return re.sub(r"\W+", " ", s.lower()).strip()


# ---------------------------------------------------------------- competitor discovery

FIRM_PREFIX_RE = re.compile(r"chứng\s+khoán\s+", re.IGNORECASE)
SECURITIES_RE = re.compile(r"((?:[A-Z][\w&.\-]*\s+){1,3})Securities\b")
ACRONYM_RE = re.compile(r"(?<![\w/+.-])([A-Z][A-Z0-9]{1,5})(?![\w/+-])")
# words after "chứng khoán" that do not start a firm name
NOT_FIRM_START = {"việt", "nhà", "nam", "phái", "cơ", "quốc", "mỹ", "châu", "hà", "tp", "thành", "tại", "là",
                  "và", "hoặc", "của", "online", "trực", "top", "uy", "giá", "lớn", "nhỏ"}
# context before "chứng khoán" that marks an authority or market, not a broker
NOT_FIRM_CONTEXT = re.compile(r"(ủy ban|uỷ ban|sở giao dịch|lưu ký|luật|thị trường|mã|ngành|quỹ)\s*$", re.IGNORECASE)
# common upper-case tokens in Vietnamese finance answers that are not firms
NOT_FIRM_ACRONYM = {
    "ETF", "HOSE", "HNX", "UPCOM", "VSDC", "VSD", "UBCKNN", "VND", "USD", "CCQ", "CW", "API", "OTP", "KYC",
    "EKYC", "CMND", "CCCD", "AI", "CTCK", "NĐT", "NDT", "ROE", "ROA", "EPS", "IPO", "VN", "TP", "HCM", "HN",
    "FAQ", "PDF", "URL", "SMS", "QR", "ATM", "TK", "CK", "TTCK", "VNI", "VNINDEX", "VN30", "HNX30", "GTGT",
    "TNCN", "VAT", "NAV", "ROI", "PE", "PB", "SLA", "CSKH", "TPDN", "TPCP", "IB", "ID", "OK", "BCTC", "ĐHĐCĐ",
    "CEO", "CFO", "KRX", "ESG", "GDP", "FDI", "FED", "MSCI", "FTSE", "NHNN", "BCT", "TT", "NĐ", "QĐ", "LS",
}
SEC_DOMAIN_HINT = re.compile(r"(sec|securities|chungkhoan|ck|invest)", re.IGNORECASE)


def find_candidates(answer: str, entities: list[dict]) -> list[tuple[str, str, str]]:
    """(candidate, kind, context) for securities-firm names not yet in entities.csv."""
    text = clean_answer(answer).replace("*", " ").replace("|", "\n")

    def known(s: str) -> bool:
        return any(p.search(s) for e in entities for p in e["patterns"])

    out = []
    for m in FIRM_PREFIX_RE.finditer(text):
        if NOT_FIRM_CONTEXT.search(text[max(0, m.start() - 25):m.start()]):
            continue
        tokens = []
        for raw in text[m.end():m.end() + 60].split("\n")[0].split()[:4]:
            if raw[0] in "([\"'“":
                break
            tok = raw.strip(".,;:()\"'“”")
            if not tok or not (tok[0].isupper() or tok[0].isdigit()):
                break
            tokens.append(tok)
            if raw[-1] in ".,;:)!?":  # name ends at punctuation
                break
        if not tokens or tokens[0].lower() in NOT_FIRM_START:
            continue
        name = "Chứng khoán " + " ".join(tokens)
        if not known(name):
            out.append((name, "ten_day_du", text[max(0, m.start() - 30):m.end() + 50]))
    for m in SECURITIES_RE.finditer(text):
        name = m.group(0).strip()
        if not known(name):
            out.append((name, "ten_day_du", text[max(0, m.start() - 30):m.end() + 30]))
    for m in ACRONYM_RE.finditer(text):
        tok = m.group(1)
        before = text[max(0, m.start() - 12):m.start()].lower()
        if "gói" in before or "mã" in before:  # product package or ticker, not a firm
            continue
        if tok not in NOT_FIRM_ACRONYM and not tok.isdigit() and not known(tok):
            out.append((tok, "viet_tat", text[max(0, m.start() - 40):m.end() + 40]))
    return out


def write_candidates(month: str, source: str, rows: list[dict], domains: Counter) -> list[dict]:
    """Aggregate per-run candidates; acronyms need >=2 runs because they are noisy."""
    runs, kind, example = defaultdict(set), {}, {}
    for r in rows:
        runs[r["candidate"]].add(r["run_key"])
        kind[r["candidate"]] = r["kind"]
        example.setdefault(r["candidate"], r["context"].replace("\n", " ").strip())
    out = [{"candidate": c, "kind": kind[c], "n_runs": len(k), "example": example[c]}
           for c, k in runs.items() if kind[c] != "viet_tat" or len(k) >= 2]
    out += [{"candidate": d, "kind": "domain", "n_runs": n, "example": "domain chưa phân loại"}
            for d, n in domains.items() if SEC_DOMAIN_HINT.search(d)]
    out.sort(key=lambda r: -r["n_runs"])
    write_csv(data_dir(month, source) / "entity_candidates.csv", out, ["candidate", "kind", "n_runs", "example"])
    return out


# ---------------------------------------------------------------- codex runner


def load_codex_cfg() -> dict:
    cfg = {"model": "", "reasoning_effort": "", "workers": 3, "timeout_sec": 300, "codex_home": ""}
    path = CONFIG / "codex.json"
    if path.exists():
        cfg.update({k: v for k, v in json.loads(path.read_text(encoding="utf-8")).items()
                    if not k.startswith("_")})
    return cfg


def codex_home(cfg: dict) -> Path:
    # Dedicated CODEX_HOME: no user AGENTS.md, skills, plugins, memories or session history
    raw = os.environ.get("GEO_CODEX_HOME") or cfg.get("codex_home") or str(Path.home() / ".codex-geo")
    return Path(raw).expanduser()


def codex_command() -> list[str]:
    exe = shutil.which("codex")
    if not exe:
        raise SystemExit("Không tìm thấy lệnh `codex`. Cài Codex CLI trước.")
    if exe.lower().endswith((".cmd", ".bat", ".ps1")):
        # npm shim on Windows: call node directly so cmd.exe does not mangle quoted -c values
        js = Path(exe).parent / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
        node = shutil.which("node")
        if js.exists() and node:
            return [node, str(js)]
    return [exe]


def codex_args(cfg: dict, instructions: Path) -> list[str]:
    args = [
        "exec", "--ephemeral",            # no session/rollout written
        "--ignore-user-config",           # ignore config.toml (model, MCP servers, apps...)
        "--ignore-rules", "--skip-git-repo-check",
        "-s", "read-only", "--json",
        "-c", f"model_instructions_file='{instructions.as_posix()}'",  # replace the coding-agent prompt
        "-c", 'web_search="live"',        # live search, not the cached index
        "-c", "project_doc_max_bytes=0",  # never read AGENTS.md
        "--disable", "shell_tool", "--disable", "memories", "--disable", "apps", "--disable", "plugins",
    ]
    if cfg.get("model"):
        args += ["-m", cfg["model"]]
    if cfg.get("reasoning_effort"):
        args += ["-c", f'model_reasoning_effort="{cfg["reasoning_effort"]}"']
    return args + ["-"]  # question comes from stdin (safe for any characters)


def parse_jsonl(text: str) -> list[dict]:
    events = []
    for line in text.split("\n"):  # split on \n only: answers may contain \r
        line = line.strip()
        if line.startswith("{"):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def codex_answer(events: list[dict]) -> str:
    msgs = [(e.get("item") or {}).get("text", "") for e in events
            if e.get("type") == "item.completed" and (e.get("item") or {}).get("type") == "agent_message"]
    msgs = [m for m in msgs if m.strip()]
    return msgs[-1] if msgs else ""


def run_codex_once(cmd: list[str], cfg: dict, home: Path, instr_text: str, question: str) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "CODEX_API_KEY")}  # ChatGPT login only
    env["CODEX_HOME"] = str(home)
    with tempfile.TemporaryDirectory(prefix="geo-run-") as tmp:
        tmp = Path(tmp)
        cwd = tmp / "cwd"  # fresh empty working dir: no project files in context
        cwd.mkdir()
        instructions = tmp / "instructions.md"
        instructions.write_text(instr_text, encoding="utf-8")
        t0 = time.time()
        try:
            p = subprocess.run(cmd + codex_args(cfg, instructions), input=question.encode("utf-8"), cwd=cwd,
                               env=env, capture_output=True, timeout=cfg["timeout_sec"])
            rc, out, err = p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
        except subprocess.TimeoutExpired as e:
            rc, out, err = -1, (e.stdout or b"").decode("utf-8", "replace"), "timeout"
    events = parse_jsonl(out)
    ok = rc == 0 and any(e.get("type") == "turn.completed" for e in events) and bool(codex_answer(events))
    errors = [json.dumps(e, ensure_ascii=False) for e in events if e.get("type") in ("error", "turn.failed")]
    return {"ok": ok, "returncode": rc, "duration_sec": round(time.time() - t0, 1), "events": events,
            "thread_id": next((e.get("thread_id") for e in events if e.get("type") == "thread.started"), ""),
            "error": ("\n".join(errors) + "\n" + err)[-3000:] if not ok else ""}


LIMIT_RE = re.compile(r"usage limit|rate limit|quota|too many requests|429", re.IGNORECASE)


def count_files(d: Path) -> int:
    return sum(1 for _ in d.rglob("*") if _.is_file()) if d.exists() else 0


def cmd_codex_run(args):
    cfg = load_codex_cfg()
    if args.model:
        cfg["model"] = args.model
    if args.workers:
        cfg["workers"] = args.workers
    home = codex_home(cfg)
    if not (home / "auth.json").exists():
        print(f"Chưa đăng nhập Codex trong thư mục riêng {home}. Chạy một lần (PowerShell):\n"
              f'  $env:CODEX_HOME = "{home}"; codex login; Remove-Item Env:CODEX_HOME\n'
              "Chọn 'Sign in with ChatGPT' bằng tài khoản Plus.")
        return 1
    brand = load_brand()
    prompts = load_prompts(brand)
    only = {x.strip().upper() for x in args.only.split(",")} if args.only else None
    planned = [(pid, r) for pid, p in prompts.items() for r in range(1, p["runs_target"] + 1)
               if not only or pid in only]
    outdir = EXPORTS / args.month / "codex"
    outdir.mkdir(parents=True, exist_ok=True)

    def done(pid, r):
        f = outdir / f"{pid}-r{r}.json"
        return f.exists() and json.loads(f.read_text(encoding="utf-8")).get("ok")

    todo = [t for t in planned if args.force or not done(*t)]
    n_done = len(planned) - len(todo)
    if args.limit:
        todo = todo[: args.limit]
    bad = [pid for pid, _ in todo if "{" in prompts[pid]["question"]]
    if bad:
        print(f"Còn placeholder chưa thay trong config/brand.json: {sorted(set(bad))[:5]}")
        return 1
    instr_text = (CONFIG / "codex_instructions.md").read_text(encoding="utf-8")
    instr_text = instr_text.replace("{DATE}", dt.date.today().isoformat())
    (outdir / "_instructions_used.md").write_text(instr_text, encoding="utf-8")
    cmd = codex_command()
    model_label = cfg["model"] or "codex-default"
    print(f"Tháng {args.month}: chạy {len(todo)} lượt (đã có {n_done}/{len(planned)}), "
          f"{cfg['workers']} luồng, model={model_label}, CODEX_HOME={home}")
    sessions_before = count_files(home / "sessions")
    stop = threading.Event()

    def task(pid, r):
        if stop.is_set():
            return None
        q = prompts[pid]["question"]
        started = dt.datetime.now().isoformat(timespec="seconds")
        res = run_codex_once(cmd, cfg, home, instr_text, q)
        if not res["ok"] and not LIMIT_RE.search(res["error"]) and not stop.is_set():
            time.sleep(10)
            res = run_codex_once(cmd, cfg, home, instr_text, q)  # one retry for transient errors
        rec = {"source": "codex", "month": args.month, "title": f"{pid}-r{r}", "prompt_id": pid, "run": r,
               "question": q, "model": model_label, "reasoning_effort": cfg["reasoning_effort"] or "default",
               "started_at": started, **res}
        (outdir / f"{pid}-r{r}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        if not res["ok"] and LIMIT_RE.search(res["error"]):
            stop.set()
        return rec

    n_ok = n_fail = 0
    with ThreadPoolExecutor(max_workers=max(1, cfg["workers"])) as ex:
        futs = [ex.submit(task, pid, r) for pid, r in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            rec = fut.result()
            if rec is None:
                continue
            if rec["ok"]:
                n_ok += 1
                x = extract_codex(rec)
                print(f"[{i}/{len(todo)}] {rec['title']} ok {rec['duration_sec']}s | "
                      f"tìm {len(x['queries'])} lệnh | {len(x['cited'])} link trích dẫn")
            else:
                n_fail += 1
                print(f"[{i}/{len(todo)}] {rec['title']} LỖI: {rec['error'].strip().splitlines()[-1][:200]}")
    leaked = count_files(home / "sessions") - sessions_before
    print(f"Xong: {n_ok} ok, {n_fail} lỗi." + (" Dừng sớm vì chạm giới hạn sử dụng; chạy lại lệnh này sau để "
                                               "làm tiếp các lượt còn thiếu." if stop.is_set() else ""))
    if leaked:
        print(f"CẢNH BÁO: Codex đã ghi {leaked} file session vào {home / 'sessions'}.")
    return cmd_parse(argparse.Namespace(export=str(outdir), month=args.month, source="codex"))


def extract_codex(rec: dict) -> dict:
    events = rec.get("events") or []
    answer = codex_answer(events)
    queries, retrieved, ref_urls = [], [], {}
    for e in events:
        it = e.get("item") or {}
        if e.get("type") != "item.completed" or it.get("type") != "web_search":
            continue
        act = it.get("action") or {}
        if isinstance(act.get("queries"), list):
            queries += [q for q in act["queries"] if isinstance(q, str)]
        elif isinstance(act.get("query"), str):
            queries.append(act["query"])
        elif isinstance(it.get("query"), str) and not it["query"].endswith("..."):
            queries.append(it["query"])
        for res in it.get("results") or []:
            if isinstance(res, dict) and str(res.get("url", "")).startswith("http"):
                retrieved.append(res["url"])
                if res.get("ref_id"):
                    ref_urls[res["ref_id"]] = res["url"]
    cited = [m.group(2) for m in MD_LINK_RE.finditer(answer)]
    cited += URL_RE.findall(MD_LINK_RE.sub(" ", answer))  # bare URLs
    cited += [u for ref, u in ref_urls.items() if ref in answer]  # citation tokens
    cited = dedupe(normalize_url(u) for u in cited)
    retrieved = dedupe(normalize_url(u) for u in retrieved + cited)
    queries = dedupe(q.strip() for q in queries if q.strip())
    return {"question": rec.get("question", ""), "answer": answer, "cited": cited, "retrieved": retrieved,
            "queries": queries, "has_search": int(bool(queries or retrieved)), "model": rec.get("model", "")}


# ---------------------------------------------------------------- commands


CALIBRATION_PRIORITY = ["2_chon_ctck", "6_xac_minh", "3_phi_margin"]


def sample_prompts(prompts: dict, n_prompts: int, seed: str) -> list[str]:
    """Stratified sample: one prompt per group first, extra prompts go to the high-value groups."""
    rng = random.Random(seed)
    by_group = defaultdict(list)
    for pid, p in prompts.items():
        by_group[p["group"]].append(pid)
    for pids in by_group.values():
        rng.shuffle(pids)
    picked = [by_group[g].pop() for g in sorted(by_group) if by_group[g]][:n_prompts]
    order = [g for g in CALIBRATION_PRIORITY if g in by_group] + sorted(set(by_group) - set(CALIBRATION_PRIORITY))
    while len(picked) < n_prompts and any(by_group.values()):
        for g in order:
            if by_group[g] and len(picked) < n_prompts:
                picked.append(by_group[g].pop())
    return sorted(picked)


def cmd_checklist(args):
    brand = load_brand()
    prompts = load_prompts(brand)
    if args.sample:
        per_prompt = 2
        pids = sample_prompts(prompts, math.ceil(args.sample / per_prompt), args.month)
        plan = [(pid, r) for pid in pids for r in range(1, min(per_prompt, prompts[pid]["runs_target"]) + 1)]
    else:
        plan = [(pid, r) for pid, p in prompts.items() for r in range(1, p["runs_target"] + 1)]
    rows = [{"chat_title": f"{pid}-r{r}", "group": prompts[pid]["group"], "question": prompts[pid]["question"],
             "done": ""} for pid, r in plan]
    out = data_dir(args.month, "chatgpt") / "checklist.csv"
    write_csv(out, rows, ["chat_title", "group", "question", "done"])
    leftover = [r["chat_title"] for r in rows if "{" in r["question"]]
    print(f"{len(rows)} lượt chat cần hỏi tay trên chatgpt.com -> {out}")
    if leftover:
        print(f"CẢNH BÁO: còn placeholder chưa thay trong config/brand.json: {leftover[:5]}...")


def planned_runs(month: str, source: str, prompts: dict) -> set[tuple[str, int]]:
    checklist = data_dir(month, source) / "checklist.csv"
    if source == "chatgpt" and checklist.exists():
        return {(m.group(1).upper(), int(m.group(2))) for r in read_csv(checklist)
                if (m := TITLE_RE.match(r["chat_title"]))}
    return {(pid, i) for pid, p in prompts.items() for i in range(1, p["runs_target"] + 1)}


def cmd_inspect(args):
    convs = load_export(Path(args.export))
    tagged = [c for c in convs if TITLE_RE.match(c.get("title") or "")]
    print(f"Tổng số chat trong export: {len(convs)} | chat có tiêu đề Qxxx-rN: {len(tagged)}")
    key_counter: Counter = Counter()

    def walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                key_counter[path + "." + k] += 1
                walk(v, path + "." + k)
        elif isinstance(obj, list):
            for v in obj[:50]:
                walk(v, path + "[]")

    for c in tagged[: args.limit]:
        for m in active_branch(c):
            ctype = (m.get("content") or {}).get("content_type", "?")
            walk(m.get("metadata") or {}, f"{role(m)}/{ctype}:metadata")
    for k, n in sorted(key_counter.items()):
        if k.count(".") <= args.depth:
            print(f"{n:6d}  {k}")
    for c in tagged[:3]:
        r = extract_run(c)
        print(f"\n== {c.get('title')} | search={r['has_search']} | queries={len(r['queries'])} "
              f"| retrieved={len(r['retrieved'])} | cited={len(r['cited'])}")
        print("  queries:", r["queries"][:5])
        print("  cited  :", r["cited"][:5])


def iter_source(path: Path, source: str):
    """Yield (title, month, conv_id, lazy extractor) for every chat/run in an export."""
    if source == "codex":
        files = sorted(path.glob("Q*-r*.json")) if path.is_dir() else [path]
        for f in files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            if rec.get("ok"):
                yield rec["title"], rec.get("month", "unknown"), rec.get("thread_id", ""), \
                    (lambda rec=rec: extract_codex(rec))
    else:
        for conv in sorted(load_export(path), key=lambda c: c.get("create_time") or 0):
            yield conv.get("title") or "", month_of(conv), conv.get("id") or conv.get("conversation_id", ""), \
                (lambda conv=conv: extract_run(conv))


def cmd_parse(args):
    brand = load_brand()
    prompts = load_prompts(brand)
    entities = load_entities(brand)
    clf = Classifier(entities, load_source_types(), load_page_types())
    path = Path(args.export)
    source = getattr(args, "source", None) or ("codex" if path.is_dir() else "chatgpt")

    by_month: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    seen_runs: dict[str, set] = defaultdict(set)
    warnings = []

    for title, conv_month, conv_id, extract in iter_source(path, source):
        m = TITLE_RE.match(title)
        if not m:
            continue
        pid, run = m.group(1).upper(), int(m.group(2))
        month = args.month or conv_month
        if pid not in prompts:
            warnings.append(f"{title}: prompt_id không có trong prompts.csv")
            continue
        if (pid, run) in seen_runs[month]:
            warnings.append(f"{month} {pid}-r{run}: trùng tiêu đề, giữ bản mới nhất")
            for table in by_month[month].values():
                table[:] = [r for r in table if not (r["prompt_id"] == pid and r["run"] == run)]
        seen_runs[month].add((pid, run))
        p = prompts[pid]
        r = extract()
        if norm_q(p["question"]) not in norm_q(r["question"]):
            warnings.append(f"{pid}-r{run}: câu hỏi đã gõ khác prompts.csv -> '{r['question'][:60]}'")

        base = {"month": month, "prompt_id": pid, "group": p["group"], "run": run}
        mentions = find_mentions(r["answer"], entities)
        cited = [clf.classify(u) for u in r["cited"]]
        cited_set = set(r["cited"])
        tables = by_month[month]
        for cand, kind, ctx in find_candidates(r["answer"], entities):
            tables["candidates"].append({"candidate": cand, "kind": kind, "context": ctx, "run_key": (pid, run)})
        tables["runs"].append({
            **base, "conv_id": conv_id, "model": r["model"],
            "has_search": r["has_search"], "n_queries": len(r["queries"]),
            "n_retrieved": len(r["retrieved"]), "n_cited": len(cited),
            "brand_mentioned": int(any(e["is_brand"] for e, _ in mentions)),
            "brand_cited": int(any(c["is_brand"] for c in cited)),
            "n_entities_mentioned": len(mentions),
        })
        for rank, (e, _) in enumerate(mentions, 1):
            tables["mentions"].append({**base, "entity": e["entity"], "is_brand": int(e["is_brand"]),
                                       "rank_in_answer": rank})
        for c in cited:
            tables["citations"].append({**base, **c})
        for u in r["retrieved"]:
            tables["retrieved"].append({**base, **clf.classify(u), "cited": int(u in cited_set)})
        for q in r["queries"]:
            tables["queries"].append({**base, "query": q})
        tables["answers"].append({**base, "question": r["question"], "answer": r["answer"]})

    if not by_month:
        print("Không tìm thấy chat nào có tiêu đề dạng Q001-r1. Kiểm tra lại tên chat.")
        return 1

    cls_fields = ["url", "domain", "source_type", "page_type", "entity", "is_brand"]
    base_f = ["month", "prompt_id", "group", "run"]
    specs = {
        "runs": base_f + ["conv_id", "model", "has_search", "n_queries", "n_retrieved", "n_cited",
                          "brand_mentioned", "brand_cited", "n_entities_mentioned"],
        "mentions": base_f + ["entity", "is_brand", "rank_in_answer"],
        "citations": base_f + cls_fields,
        "retrieved": base_f + cls_fields + ["cited"],
        "queries": base_f + ["query"],
        "answers": base_f + ["question", "answer"],
    }
    for month, tables in sorted(by_month.items()):
        for name, fields in specs.items():
            write_csv(data_dir(month, source) / f"geo_{name}.csv", tables.get(name, []), fields)
        missing = sorted(planned_runs(month, source, prompts) - seen_runs[month])
        make_review_template(month, source, tables)
        unknown_domains = Counter(d for d, _, _ in {(r["domain"], r["prompt_id"], r["run"])
                                                    for r in tables["retrieved"] if r["source_type"] == "khac"})
        cands = write_candidates(month, source, tables["candidates"], unknown_domains)
        print(f"[{month} | {source}] {len(tables['runs'])} lượt | thiếu {len(missing)} lượt so với kế hoạch"
              + (f" (vd: {', '.join(f'{p}-r{i}' for p, i in missing[:8])})" if missing else ""))
        if cands:
            print(f"  {len(cands)} tên/domain có thể là CTCK chưa có trong entities.csv "
                  f"-> {data_dir(month, source) / 'entity_candidates.csv'}")
            print("  Nhiều nhất: " + ", ".join(f"{c['candidate']} ({c['n_runs']})" for c in cands[:10]))
    for w in warnings:
        print("CẢNH BÁO:", w)
    return 0


def make_review_template(month: str, source: str, tables: dict) -> None:
    """Runs where the brand is mentioned in fact-sensitive groups need a human accuracy check."""
    path = REVIEW / f"accuracy_{month}_{source}.csv"
    existing = {}
    if path.exists():
        existing = {(r["prompt_id"], r["run"]): r for r in read_csv(path)}
    rows = []
    for r in tables["runs"]:
        if r["brand_mentioned"] and (r["group"] in REVIEW_GROUPS or r["brand_cited"] == 0):
            key = (r["prompt_id"], str(r["run"]))
            old = existing.get(key, {})
            rows.append({"prompt_id": r["prompt_id"], "run": r["run"], "group": r["group"],
                         "is_accurate": old.get("is_accurate", ""), "wrong_fact": old.get("wrong_fact", ""),
                         "source_of_error": old.get("source_of_error", "")})
    write_csv(path, rows, ["prompt_id", "run", "group", "is_accurate", "wrong_fact", "source_of_error"])


# ---------------------------------------------------------------- report


def pct(a: float, b: float) -> str:
    return f"{a / b * 100:.0f}%" if b else "–"


def ratio(a: float, b: float):
    return a / b if b else None


def delta(cur, prev) -> str:
    if cur is None or prev is None:
        return "–"
    d = (cur - prev) * 100
    return f"{d:+.0f} điểm"


def load_month(month: str, source: str) -> dict[str, list[dict]] | None:
    d = data_dir(month, source)
    if not (d / "geo_runs.csv").exists():
        return None
    return {n: read_csv(d / f"geo_{n}.csv") for n in ("runs", "mentions", "citations", "retrieved", "queries")}


def core_metrics(t: dict, group: str | None = None) -> dict:
    runs = [r for r in t["runs"] if group is None or r["group"] == group]
    keys = {(r["prompt_id"], r["run"]) for r in runs}
    ments = [m for m in t["mentions"] if (m["prompt_id"], m["run"]) in keys]
    brand_runs = {(r["prompt_id"], r["run"]) for r in runs if r["brand_mentioned"] == "1"}
    cits_in_brand_runs = [c for c in t["citations"] if (c["prompt_id"], c["run"]) in brand_runs]
    n = len(runs)
    return {
        "runs": n,
        "mention_rate": ratio(sum(r["brand_mentioned"] == "1" for r in runs), n),
        "citation_rate": ratio(sum(r["brand_cited"] == "1" for r in runs), n),
        "owned_share": ratio(sum(c["is_brand"] == "1" for c in cits_in_brand_runs), len(cits_in_brand_runs)),
        "sov": ratio(sum(m["is_brand"] == "1" for m in ments), len(ments)),
        "search_rate": ratio(sum(r["has_search"] == "1" for r in runs), n),
    }


def fmt(v) -> str:
    return "–" if v is None else f"{v * 100:.0f}%"


def available_months(source: str) -> list[str]:
    if not DATA.exists():
        return []
    return sorted(p.name for p in DATA.iterdir() if (data_dir(p.name, source) / "geo_runs.csv").exists())


def cmd_report(args):
    source = args.source
    months = available_months(source)
    if not months:
        print(f"Chưa có dữ liệu nguồn {source}. Chạy `codex-run` hoặc `parse` trước.")
        return 1
    month = args.month or months[-1]
    cur = load_month(month, source)
    if cur is None:
        print(f"Không có dữ liệu tháng {month} (nguồn {source}). Có: {months}")
        return 1
    prev_months = [m for m in months if m < month]
    prev = load_month(prev_months[-1], source) if prev_months else None
    brand = load_brand()
    L = []
    add = L.append

    add(f"# Báo cáo GEO – {brand['BRAND']} – tháng {month} – {SOURCE_LABEL[source]}\n")
    if source == "codex":
        models = sorted({r["model"] for r in cur["runs"]})
        add(f"Nguồn: Codex CLI (`codex exec`), model {', '.join(models)}. Mỗi lượt là một phiên tạm, "
            "không memory, không context dự án, tìm web live. **Đây là số đo gần đúng cho ChatGPT web, "
            "không giống hệt**: xem độ lệch ở `reports/calibration_" + month + ".md`. "
            f"So sánh với: {prev_months[-1] if prev else 'không có tháng trước'}.\n")
    else:
        add(f"Nguồn: ChatGPT (giao diện web, tài khoản Plus), file export `conversations.json`. "
            f"So sánh với: {prev_months[-1] if prev else 'không có tháng trước'}.\n")

    # 1. Headline
    c, p = core_metrics(cur), core_metrics(prev) if prev else {}
    add("## 1. Chỉ số chính\n")
    add("| Chỉ số | Tháng này | Tháng trước | Thay đổi |\n|---|---|---|---|")
    labels = [("mention_rate", "Mention rate (lượt có nhắc tên thương hiệu)"),
              ("citation_rate", "Citation rate (lượt có link về website chính chủ)"),
              ("owned_share", "Owned citation share (link chính chủ / tổng link, trong các lượt có nhắc tên)"),
              ("sov", "Share of voice (lượt nhắc thương hiệu / tổng lượt nhắc mọi CTCK)"),
              ("search_rate", "Tỷ lệ lượt ChatGPT có tìm web")]
    for k, label in labels:
        add(f"| {label} | {fmt(c[k])} | {fmt(p.get(k))} | {delta(c[k], p.get(k))} |")
    add(f"\nTổng số lượt đo: {c['runs']}" + (f" (tháng trước: {p['runs']})" if prev else "") + "\n")

    # 1b. Unbranded vs branded questions: only unbranded ones show organic visibility
    branded = {r["prompt_id"] for r in read_csv(CONFIG / "prompts.csv") if "{BRAND}" in r["question"]}
    add("### Câu hỏi không nêu tên thương hiệu và câu hỏi có nêu tên\n")
    add("Câu hỏi đã chứa tên thương hiệu thì gần như luôn được nhắc tên. **Chỉ số phản ánh mức độ ChatGPT "
        "tự giới thiệu thương hiệu là ở dòng \"không nêu tên\".**\n")
    add("| Loại câu hỏi | Lượt | Mention | Δ | Citation | Δ | SoV |\n|---|---|---|---|---|---|---|")
    for label, keep in [("Không nêu tên thương hiệu", lambda pid: pid not in branded),
                        ("Có nêu tên thương hiệu", lambda pid: pid in branded)]:
        cs = core_metrics(subset(cur, {r["prompt_id"] for r in cur["runs"] if keep(r["prompt_id"])}))
        ps = core_metrics(subset(prev, {r["prompt_id"] for r in prev["runs"] if keep(r["prompt_id"])})) if prev else {}
        add(f"| {label} | {cs['runs']} | {fmt(cs['mention_rate'])} | {delta(cs['mention_rate'], ps.get('mention_rate'))} "
            f"| {fmt(cs['citation_rate'])} | {delta(cs['citation_rate'], ps.get('citation_rate'))} | {fmt(cs['sov'])} |")
    add("")

    # 2. By group
    add("## 2. Theo nhóm câu hỏi\n")
    add("| Nhóm | Lượt | Mention | Δ | Citation | Δ | SoV |\n|---|---|---|---|---|---|---|")
    for g in sorted({r["group"] for r in cur["runs"]}):
        cg = core_metrics(cur, g)
        pg = core_metrics(prev, g) if prev else {}
        add(f"| {g} | {cg['runs']} | {fmt(cg['mention_rate'])} | {delta(cg['mention_rate'], pg.get('mention_rate'))} "
            f"| {fmt(cg['citation_rate'])} | {delta(cg['citation_rate'], pg.get('citation_rate'))} | {fmt(cg['sov'])} |")

    # 3. Share of voice by entity
    add("\n## 3. Share of voice theo CTCK\n")
    n_runs = len(cur["runs"])
    ment_runs = defaultdict(set)
    first_rank = Counter()
    for m in cur["mentions"]:
        ment_runs[m["entity"]].add((m["prompt_id"], m["run"]))
        if m["rank_in_answer"] == "1":
            first_rank[m["entity"]] += 1
    cit_count = Counter(c["entity"] for c in cur["citations"] if c["entity"])
    add("| CTCK | Lượt được nhắc | % lượt | Lần đứng đầu câu trả lời | Link trích dẫn về website |\n|---|---|---|---|---|")
    for ent, runs_set in sorted(ment_runs.items(), key=lambda x: -len(x[1]))[:15]:
        add(f"| {ent} | {len(runs_set)} | {pct(len(runs_set), n_runs)} | {first_rank[ent]} | {cit_count[ent]} |")

    # 4. Top cited domains per group
    add("\n## 4. Domain được trích dẫn nhiều nhất\n")
    by_group = defaultdict(Counter)
    stype = {}
    for cdx in cur["citations"]:
        by_group["(tất cả)"][cdx["domain"]] += 1
        by_group[cdx["group"]][cdx["domain"]] += 1
        stype[cdx["domain"]] = cdx["source_type"]
    for g in ["(tất cả)"] + sorted(k for k in by_group if k != "(tất cả)"):
        top = ", ".join(f"{d} [{stype[d]}] ×{n}" for d, n in by_group[g].most_common(args.top))
        add(f"- **{g}**: {top}")

    # 5. Source types per group (who owns the answer)
    add("\n## 5. Loại nguồn được trích dẫn theo nhóm câu hỏi\n")
    types = sorted({cdx["source_type"] for cdx in cur["citations"]})
    add("| Nhóm | " + " | ".join(types) + " |\n|---|" + "---|" * len(types))
    for g in sorted({cdx["group"] for cdx in cur["citations"]}):
        cnt = Counter(cdx["source_type"] for cdx in cur["citations"] if cdx["group"] == g)
        tot = sum(cnt.values())
        add(f"| {g} | " + " | ".join(pct(cnt[t], tot) for t in types) + " |")

    # 6. Page types on securities-firm sites: retrieved vs cited (like B7 in the source study)
    add("\n## 6. Loại trang trên website CTCK: được đọc so với được trích dẫn\n")
    ret = Counter()
    cit = Counter()
    for r in cur["retrieved"]:
        if r["source_type"] in ("chinh_chu", "doi_thu_ctck"):
            ret[r["page_type"]] += 1
            cit[r["page_type"]] += r["cited"] == "1"
    add("| Loại trang | Xuất hiện | Được trích dẫn | Tỷ lệ |\n|---|---|---|---|")
    for pt, n in ret.most_common():
        add(f"| {pt} | {n} | {cit[pt]} | {pct(cit[pt], n)} |")
    if not ret:
        add("| (chưa có dữ liệu kết quả tìm kiếm trong export) | | | |")

    # 7. Brand pages cited
    add("\n## 7. Trang của thương hiệu được trích dẫn\n")
    own = Counter(cdx["url"] for cdx in cur["citations"] if cdx["is_brand"] == "1")
    if own:
        for u, n in own.most_common(args.top * 2):
            add(f"- {u} ×{n}")
    else:
        add("- Chưa có trang nào của thương hiệu được trích dẫn.")

    # 8. Top search queries (fan-out)
    if cur["queries"]:
        add("\n## 8. Lệnh tìm (query fan-out) ChatGPT dùng nhiều nhất\n")
        for q, n in Counter(q["query"].lower() for q in cur["queries"]).most_common(args.top * 2):
            add(f"- `{q}` ×{n}")

    # 9. Accuracy review
    add("\n## 9. Kiểm tra độ chính xác\n")
    rv = REVIEW / f"accuracy_{month}_{source}.csv"
    rows = read_csv(rv) if rv.exists() else []
    done = [r for r in rows if r["is_accurate"].strip()]
    wrong = [r for r in done if r["is_accurate"].strip().lower() in ("0", "no", "sai", "khong", "không")]
    add(f"Cần duyệt: {len(rows)} lượt | đã duyệt: {len(done)} | sai thông tin: {len(wrong)} "
        f"(file `review/{rv.name}`).\n")
    for r in wrong:
        add(f"- {r['prompt_id']}-r{r['run']} ({r['group']}): {r['wrong_fact']} | nguồn gây sai: {r['source_of_error']}")

    # 10. Completeness
    prompts = load_prompts(brand)
    have = {(r["prompt_id"], int(r["run"])) for r in cur["runs"]}
    planned = planned_runs(month, source, prompts)
    add(f"\n## 10. Độ đầy đủ dữ liệu\n\nĐã đo {len(have & planned)}/{len(planned)} lượt theo kế hoạch. "
        "Câu trả lời dao động giữa các lượt, nên chênh dưới 10 điểm % giữa hai tháng chưa đủ để kết luận.\n")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"geo_report_{month}_{source}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Đã ghi {out}")
    return 0


SITE_Q_RE = re.compile(r"site[:.]\s*([\w.-]+)", re.IGNORECASE)
NEG_RE = re.compile(r"xử phạt|bị phạt|thanh tra|vi phạm|sai phạm|khởi tố|khởi kiện|bị kiện", re.IGNORECASE)
NUM_RE = re.compile(r"(?<![\d.,])\d{1,2}(?:[.,]\d+)?\s*%")  # rates like 0,1% or 13,5%


VI_CHARS_RE = re.compile(r"[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", re.IGNORECASE)
TYPE_LABEL = {
    "chinh_chu": "Website thương hiệu", "doi_thu_ctck": "Website CTCK khác", "co_quan_nha_nuoc": "Cơ quan nhà nước VN",
    "co_quan_nuoc_ngoai": "Cơ quan nước ngoài", "phap_ly": "Văn bản pháp luật", "bao_chi": "Báo chí",
    "blog_kien_thuc": "Blog kiến thức", "toplist": "Toplist/review", "xep_hang": "Bảng xếp hạng",
    "ngan_hang_fintech": "Ngân hàng/fintech", "quy_dau_tu": "Quỹ đầu tư", "du_lieu_tai_chinh": "Dữ liệu tài chính",
    "giao_duc": "Giáo dục (.edu)", "wiki": "Wikipedia", "dien_dan": "Diễn đàn", "app_store": "App store",
    "hiep_hoi": "Hiệp hội", "trung_ten": "Công ty trùng tên", "khac": "Khác",
}


def group_patterns(t: dict, clf, top: int) -> list[str]:
    """How each question group is answered: search behaviour, sources read vs cited, answer shape."""
    L = ["## I0. ChatGPT trả lời từng nhóm câu hỏi như thế nào\n",
         "**Đọc** = trang có trong kết quả tìm. **Trích dẫn** = link trong câu trả lời. "
         "**Tỷ lệ chọn** = số trang được trích dẫn / số trang được đọc. Tỷ lệ chọn cao nghĩa là ChatGPT tin loại nguồn đó.\n"]
    for g in sorted({r["group"] for r in t["runs"]}):
        runs = [r for r in t["runs"] if r["group"] == g]
        n = len(runs)
        qs = [q["query"] for q in t["queries"] if q["group"] == g]
        site_q = [q for q in qs if SITE_Q_RE.search(q)]
        url_q = [q for q in qs if q.startswith("http")]
        en_q = [q for q in qs if not VI_CHARS_RE.search(q) and not q.startswith("http") and re.search(r"[a-z]{3,}", q.lower())]
        site_types = Counter()
        for q in site_q:
            for h in SITE_Q_RE.findall(q):
                site_types[clf.classify("https://" + h.lower().removeprefix("www.") + "/")["source_type"]] += 1
        ret = [r for r in t["retrieved"] if r["group"] == g]
        cit = [c for c in t["citations"] if c["group"] == g]
        rt, ct = Counter(r["source_type"] for r in ret), Counter(c["source_type"] for c in cit)
        sel = Counter(r["source_type"] for r in ret if r["cited"] == "1")
        L.append(f"### {g} ({n} lượt)\n")
        L.append(f"- **Tìm:** trung bình {len(qs) / n:.1f} lệnh tìm mỗi lượt. Lệnh `site:` chiếm {pct(len(site_q), len(qs))}, "
                 f"mở thẳng một URL chiếm {pct(len(url_q), len(qs))}, tìm bằng tiếng Anh chiếm {pct(len(en_q), len(qs))}.")
        if site_types:
            L.append("- **Lệnh `site:` nhắm vào:** " + ", ".join(
                f"{TYPE_LABEL.get(k, k)} {pct(v, sum(site_types.values()))}" for k, v in site_types.most_common(4)) + ".")
        L.append(f"- **Đọc** {len(ret) / n:.0f} trang mỗi lượt, **trích dẫn** {len(cit) / n:.1f} link mỗi lượt. "
                 f"Trung bình nhắc {sum(int(r['n_entities_mentioned']) for r in runs) / n:.1f} CTCK mỗi câu trả lời.")
        ex = [q for q in qs if not SITE_Q_RE.search(q) and not q.startswith("http")][:3] or qs[:3]
        if ex:
            L.append("- **Ví dụ lệnh tìm:** " + " · ".join(f"`{q[:80]}`" for q in ex))
        L.append("\n| Loại nguồn | % trang được đọc | % link trích dẫn | Tỷ lệ chọn |\n|---|---|---|---|")
        for k in sorted(set(rt) | set(ct), key=lambda k: -(ct[k] * 3 + rt[k]))[:7]:
            L.append(f"| {TYPE_LABEL.get(k, k)} | {pct(rt[k], len(ret))} | {pct(ct[k], len(cit))} | {pct(sel[k], rt[k])} |")
        topd = Counter(c["domain"] for c in cit).most_common(top)
        L.append("\nĐược trích dẫn nhiều nhất: " + ", ".join(f"{d} ×{k}" for d, k in topd) + "\n")
    return L


def cmd_insights(args):
    """Quangsilic-style evidence tables: funnel per firm, query fan-out, page read vs cited, consistency, risk."""
    source, month = args.source, args.month
    t = load_month(month, source)
    if t is None:
        print(f"Không có dữ liệu tháng {month} (nguồn {source}).")
        return 1
    t["answers"] = read_csv(data_dir(month, source) / "geo_answers.csv")
    brand = load_brand()
    clf = Classifier(load_entities(brand), load_source_types(), load_page_types())
    raw_q = {r["prompt_id"]: r["question"] for r in read_csv(CONFIG / "prompts.csv")}
    questions = {pid: p["question"] for pid, p in load_prompts(brand).items()}
    branded = {pid for pid, q in raw_q.items() if "{BRAND}" in q}
    key = lambda r: (r["prompt_id"], r["run"])  # noqa: E731
    ub = {key(r) for r in t["runs"] if r["prompt_id"] not in branded}
    br = {key(r) for r in t["runs"] if r["prompt_id"] in branded}
    L = []
    add = L.append
    add(f"# Bảng phân tích GEO – {brand['BRAND']} – tháng {month} – {SOURCE_LABEL[source]}\n")
    add(f"Câu hỏi **không nêu tên** thương hiệu: {len(ub)} lượt. Câu hỏi **có nêu tên**: {len(br)} lượt. "
        "Đơn vị đếm là **lượt** (một lần hỏi), trừ khi ghi khác.\n")
    L += group_patterns(t, clf, args.top)

    # I1. Funnel per firm on unbranded questions
    site_runs, ret_runs, cit_runs, named_runs = (defaultdict(set) for _ in range(4))
    n_q = n_site = 0
    for q in t["queries"]:
        if key(q) not in ub:
            continue
        n_q += 1
        hosts = SITE_Q_RE.findall(q["query"])
        n_site += bool(hosts)
        for h in hosts:
            ent = clf.entity_for(h.lower().removeprefix("www."))
            if ent:
                site_runs[ent["entity"]].add(key(q))
    for r in t["retrieved"]:
        if key(r) in ub and r["entity"]:
            ret_runs[r["entity"]].add(key(r))
            if r["cited"] == "1":
                cit_runs[r["entity"]].add(key(r))
    for m in t["mentions"]:
        if key(m) in ub:
            named_runs[m["entity"]].add(key(m))
    add("## I1. Phễu hiển thị của từng CTCK (câu hỏi không nêu tên)\n")
    add("- **site:** = số lượt có lệnh tìm nhắm thẳng vào domain CTCK đó, tức CTCK đã nằm trong danh sách ứng viên trước khi tìm.\n"
        "- **Được đọc** = trang của CTCK có trong kết quả tìm.\n"
        "- **Được trích dẫn** = có link về website CTCK.\n"
        "- **Nhắc tên** = tên xuất hiện trong câu trả lời.\n")
    add(f"{n_site}/{n_q} lệnh tìm ({pct(n_site, n_q)}) là lệnh `site:`.\n")
    add("| CTCK | site: | Được đọc | Được trích dẫn | Nhắc tên | Nhắc tên nhưng không có link |\n|---|---|---|---|---|---|")
    ents = sorted(set(named_runs) | set(ret_runs) | {e["entity"] for e in clf.entities if e["is_brand"]},
                  key=lambda e: (-len(named_runs[e]), -len(ret_runs[e])))
    for e in ents[: args.top * 3]:
        mark = " **(thương hiệu)**" if e == brand["BRAND"] else ""
        add(f"| {e}{mark} | {len(site_runs[e])} | {len(ret_runs[e])} | {len(cit_runs[e])} | {len(named_runs[e])} "
            f"| {len(named_runs[e] - cit_runs[e])} |")

    # I2. Consideration set per prompt in high-value groups
    add("\n## I2. Danh sách CTCK được nhắc theo từng câu hỏi (câu không nêu tên, số lượt nhắc / số lượt hỏi)\n")
    runs_per = Counter(r["prompt_id"] for r in t["runs"])
    per_prompt = defaultdict(Counter)
    for m in t["mentions"]:
        if key(m) in ub:
            per_prompt[m["prompt_id"]][m["entity"]] += 1
    groups = {r["prompt_id"]: r["group"] for r in t["runs"]}
    add("| Câu | Nhóm | Câu hỏi | CTCK được nhắc |\n|---|---|---|---|")
    for pid in sorted(per_prompt):
        if groups[pid] in ("2_chon_ctck", "3_phi_margin", "4_mo_tai_khoan", "5_san_pham"):
            top = ", ".join(f"{e} {n}/{runs_per[pid]}" for e, n in per_prompt[pid].most_common(6))
            add(f"| {pid} | {groups[pid]} | {questions[pid]} | {top} |")

    # I3. Intermediary share per group
    add("\n## I3. Link trích dẫn trỏ về đâu, theo nhóm câu hỏi\n")
    add("| Nhóm | Số link | Website thương hiệu | Website CTCK khác | Nguồn trung gian (báo, toplist, cơ quan nhà nước…) |\n|---|---|---|---|---|")
    for g in sorted({c["group"] for c in t["citations"]}):
        cs = [c for c in t["citations"] if c["group"] == g]
        own = sum(c["source_type"] == "chinh_chu" for c in cs)
        comp = sum(c["source_type"] == "doi_thu_ctck" for c in cs)
        add(f"| {g} | {len(cs)} | {pct(own, len(cs))} | {pct(comp, len(cs))} | {pct(len(cs) - own - comp, len(cs))} |")

    # I4. Brand URLs read vs cited
    add("\n## I4. Trang của thương hiệu: được đọc so với được trích dẫn (tính theo lượt)\n")
    add("Trang được đọc nhiều nhưng ít được trích dẫn là trang ChatGPT đã thấy mà không chọn. "
        "Cần xem trang đó thiếu gì: con số cụ thể, ngày hiệu lực, hay câu trả lời thẳng.\n")
    rr, rc = defaultdict(set), defaultdict(set)
    for r in t["retrieved"]:
        if r["is_brand"] == "1":
            u = r["url"].split("?")[0]
            rr[u].add(key(r))
            if r["cited"] == "1":
                rc[u].add(key(r))
    add("| Trang | Được đọc | Được trích dẫn | Tỷ lệ | Ghi chú |\n|---|---|---|---|---|")
    for u in sorted(rr, key=lambda u: -len(rr[u]))[: args.top * 5]:
        note = "PDF" if u.lower().endswith(".pdf") else ("bản tiếng Anh" if "/en/" in u else "")
        add(f"| {u} | {len(rr[u])} | {len(rc[u])} | {pct(len(rc[u]), len(rr[u]))} | {note} |")

    # I5. Page format on all securities-firm sites
    add("\n## I5. Định dạng trang trên website CTCK: được đọc so với được trích dẫn\n")
    fmt_ret, fmt_cit = Counter(), Counter()
    for r in t["retrieved"]:
        if r["source_type"] in ("chinh_chu", "doi_thu_ctck"):
            f = "PDF" if r["url"].lower().split("?")[0].endswith(".pdf") else (
                "Bản tiếng Anh (/en/)" if "/en/" in r["url"] else "HTML tiếng Việt")
            fmt_ret[f] += 1
            fmt_cit[f] += r["cited"] == "1"
    add("| Định dạng | Được đọc | Được trích dẫn | Tỷ lệ |\n|---|---|---|---|")
    for f, n in fmt_ret.most_common():
        add(f"| {f} | {n} | {fmt_cit[f]} | {pct(fmt_cit[f], n)} |")

    # I6. Consistency of brand facts across runs (percentages quoted)
    add("\n## I6. Con số về thương hiệu có nhất quán giữa các lượt không (câu hỏi có nêu tên)\n")
    add("Một câu hỏi mà mỗi lượt trả lời một con số khác nhau thường do website thương hiệu không nêu rõ con số, "
        "nên ChatGPT phải lấy từ nguồn khác.\n")
    add("| Câu | Câu hỏi | Các con số % theo từng lượt |\n|---|---|---|")
    by_pid = defaultdict(list)
    for a in t["answers"]:
        if a["prompt_id"] in branded:
            by_pid[a["prompt_id"]].append(a)
    for pid in sorted(by_pid):
        nums = [sorted(set(n.replace(" ", "") for n in NUM_RE.findall(a["answer"])))[:6] for a in by_pid[pid]]
        if any(nums) and len({tuple(n) for n in nums}) > 1:
            add(f"| {pid} | {questions[pid]} | " + " / ".join(", ".join(n) or "(không nêu số)" for n in nums) + " |")

    # I7. Reputation risk
    add("\n## I7. Rủi ro danh tiếng: câu trả lời nhắc xử phạt, thanh tra hoặc vi phạm (câu hỏi có nêu tên)\n")
    hits = [a for a in t["answers"] if a["prompt_id"] in branded and NEG_RE.search(a["answer"])]
    hk = {key(a) for a in hits}
    add(f"{len(hits)}/{len(br)} lượt. Theo câu: " + ", ".join(f"{p} ({n})" for p, n in Counter(a['prompt_id'] for a in hits).most_common()) + ".\n")
    src = Counter(c["domain"] for c in t["citations"] if key(c) in hk and c["is_brand"] != "1")
    add("Nguồn bên ngoài được trích dẫn trong các lượt này: " + ", ".join(f"{d} ×{n}" for d, n in src.most_common(8)) + "\n")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"geo_insights_{month}_{source}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Đã ghi {out}")
    return 0


def subset(t: dict, pids: set[str]) -> dict:
    return {k: [r for r in rows if r["prompt_id"] in pids] for k, rows in t.items()}


def jaccard(a: set, b: set):
    return len(a & b) / len(a | b) if a | b else None


def cmd_calibrate(args):
    """Compare the codex proxy with real chatgpt.com answers on the prompts asked in both."""
    month = args.month
    cx, gp = load_month(month, "codex"), load_month(month, "chatgpt")
    if cx is None or gp is None:
        print(f"Cần dữ liệu cả hai nguồn cho tháng {month}: codex={'có' if cx else 'thiếu'}, "
              f"chatgpt={'có' if gp else 'thiếu'}.")
        return 1
    pids = {r["prompt_id"] for r in gp["runs"]} & {r["prompt_id"] for r in cx["runs"]}
    if not pids:
        print("Không có câu hỏi nào được đo ở cả hai nguồn.")
        return 1
    cx, gp = subset(cx, pids), subset(gp, pids)
    L = []
    add = L.append
    add(f"# Đối chiếu Codex với ChatGPT web – tháng {month}\n")
    add(f"So trên {len(pids)} câu hỏi được đo ở cả hai nguồn: ChatGPT web {len(gp['runs'])} lượt, "
        f"Codex {len(cx['runs'])} lượt.\n")

    add("## 1. Chỉ số chính trên cùng bộ câu hỏi\n")
    add("| Chỉ số | ChatGPT web | Codex | Codex lệch |\n|---|---|---|---|")
    mg, mc = core_metrics(gp), core_metrics(cx)
    for k, label in [("mention_rate", "Mention rate"), ("citation_rate", "Citation rate"),
                     ("sov", "Share of voice"), ("search_rate", "Tỷ lệ có tìm web")]:
        add(f"| {label} | {fmt(mg[k])} | {fmt(mc[k])} | {delta(mc[k], mg[k])} |")

    def per_prompt(t, key):
        out = defaultdict(set)
        for r in t[key]:
            if key == "mentions":
                out[r["prompt_id"]].add(r["entity"])
            else:
                out[r["prompt_id"]].add(r["domain"])
        return out

    ent_g, ent_c = per_prompt(gp, "mentions"), per_prompt(cx, "mentions")
    dom_g, dom_c = per_prompt(gp, "citations"), per_prompt(cx, "citations")

    def brand_rate(t, pid):
        runs = [r for r in t["runs"] if r["prompt_id"] == pid]
        return f"{sum(r['brand_mentioned'] == '1' for r in runs)}/{len(runs)}"

    add("\n## 2. Từng câu hỏi\n")
    add("Độ trùng = số phần tử chung / tổng số phần tử khác nhau của hai nguồn (1 = giống hệt, 0 = không trùng).\n")
    add("| Câu | Nhóm | Nhắc thương hiệu (web) | Nhắc thương hiệu (Codex) | Trùng CTCK được nhắc | Trùng domain trích dẫn |")
    add("|---|---|---|---|---|---|")
    groups = {r["prompt_id"]: r["group"] for r in gp["runs"]}
    agree, ej, dj = 0, [], []
    for pid in sorted(pids):
        e, d = jaccard(ent_g[pid], ent_c[pid]), jaccard(dom_g[pid], dom_c[pid])
        ej += [e] if e is not None else []
        dj += [d] if d is not None else []
        bg = any(r["brand_mentioned"] == "1" for r in gp["runs"] if r["prompt_id"] == pid)
        bc = any(r["brand_mentioned"] == "1" for r in cx["runs"] if r["prompt_id"] == pid)
        agree += bg == bc
        add(f"| {pid} | {groups[pid]} | {brand_rate(gp, pid)} | {brand_rate(cx, pid)} | {fmt(e)} | {fmt(d)} |")

    add("\n## 3. CTCK được nhắc: % lượt ở mỗi nguồn\n")
    add("| CTCK | ChatGPT web | Codex |\n|---|---|---|")
    share_g = Counter(m["entity"] for m in {(m["prompt_id"], m["run"], m["entity"]): m for m in gp["mentions"]}.values())
    share_c = Counter(m["entity"] for m in {(m["prompt_id"], m["run"], m["entity"]): m for m in cx["mentions"]}.values())
    for ent in sorted(set(share_g) | set(share_c), key=lambda e: -(share_g[e] + share_c[e]))[:15]:
        add(f"| {ent} | {pct(share_g[ent], len(gp['runs']))} | {pct(share_c[ent], len(cx['runs']))} |")

    avg = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
    add("\n## 4. Kết luận nhanh\n")
    add(f"- Hai nguồn cùng kết luận \"có/không nhắc {load_brand()['BRAND']}\" ở {agree}/{len(pids)} câu hỏi.")
    add(f"- Độ trùng trung bình của danh sách CTCK được nhắc: {fmt(avg(ej))}. Độ trùng domain trích dẫn: {fmt(avg(dj))}.")
    add("- Mẫu đối chiếu nhỏ (khoảng 20 lượt), nên chỉ dùng để thấy xu hướng lệch. Cần theo dõi qua nhiều tháng; "
        "đừng hiệu chỉnh số liệu Codex bằng một hệ số cố định.")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"calibration_{month}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Đã ghi {out}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="GEO tracker: ChatGPT mentions/citations for a securities brand")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("codex-run", help="ask every planned run through isolated `codex exec`, then parse")
    s.add_argument("--month", required=True, help="YYYY-MM")
    s.add_argument("--only", help="comma-separated prompt ids, e.g. Q009,Q010")
    s.add_argument("--limit", type=int, help="max runs this time (resumable)")
    s.add_argument("--workers", type=int, help="parallel runs (default from config/codex.json)")
    s.add_argument("--model", help="override config/codex.json model")
    s.add_argument("--force", action="store_true", help="re-ask runs that already succeeded")
    s = sub.add_parser("checklist", help="list of chats to ask by hand on chatgpt.com (calibration sample)")
    s.add_argument("--month", required=True, help="YYYY-MM")
    s.add_argument("--sample", type=int, default=20, help="number of runs; 0 = full plan")
    s = sub.add_parser("inspect", help="show which metadata fields a ChatGPT export contains")
    s.add_argument("export")
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--depth", type=int, default=3)
    s = sub.add_parser("parse", help="parse a ChatGPT conversations.json or a codex run folder into CSV tables")
    s.add_argument("export")
    s.add_argument("--month", help="force month YYYY-MM (default: chat create_time)")
    s.add_argument("--source", choices=SOURCES, help="default: codex for a folder, chatgpt for a file")
    s = sub.add_parser("report", help="write the monthly markdown report")
    s.add_argument("--month")
    s.add_argument("--source", choices=SOURCES, default="codex")
    s.add_argument("--top", type=int, default=5)
    s = sub.add_parser("calibrate", help="compare codex with chatgpt.com on the same prompts")
    s.add_argument("--month", required=True)
    s = sub.add_parser("insights", help="evidence tables: funnel per firm, fan-out, pages read vs cited, risk")
    s.add_argument("--month", required=True)
    s.add_argument("--source", choices=SOURCES, default="codex")
    s.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    return {"codex-run": cmd_codex_run, "checklist": cmd_checklist, "inspect": cmd_inspect, "parse": cmd_parse,
            "report": cmd_report, "calibrate": cmd_calibrate, "insights": cmd_insights}[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
