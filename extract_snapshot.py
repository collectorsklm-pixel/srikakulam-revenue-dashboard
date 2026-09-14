#!/usr/bin/env python3
"""
Revenue Subjects daily pack (PDF)  ->  one snapshot JSON per day.

    python extract_snapshot.py "Revenue_Subjects_Reports_as_on_10_09_26.pdf" data/

Writes  data/snapshot_YYYY-MM-DD.json.  Load those files into the dashboard.
Needs:  pip install pdfplumber
"""
import sys, os, re, json, datetime
import pdfplumber

DIVISION = {
    "Palasa": ["Ichchapuram", "Kaviti", "Kanchili", "Mandasa", "Palasa", "Sompeta", "Vajrapukothuru"],
    "Tekkali": ["Hiramandalam", "Kotabommali", "Kothuru", "L.N.Peta", "Meliaputti", "Nandigam",
                "Pathapatnam", "Santhabommali", "Saravakota", "Tekkali"],
    "Srikakulam": ["Amadalavalasa", "Burja", "Etcherla", "G.Sigadam", "Gara", "Jalumuru", "Laveru",
                   "Narasannapeta", "Polaki", "Ponduru", "Ranasthalam", "Sarubujjili", "Srikakulam"],
}
MANDALS = [m for v in DIVISION.values() for m in v]
DIV_OF = {m: d for d, v in DIVISION.items() for m in v}

_k = lambda s: re.sub(r"[^a-z]", "", (s or "").lower())
ALIAS = {_k(m): m for m in MANDALS}
ALIAS.update({_k(a): b for a, b in {
    "ichapuram": "Ichchapuram", "ichapuramurban": "Ichchapuram", "ichchapuram": "Ichchapuram",
    "vajrapukotturu": "Vajrapukothuru", "palasakasibugga": "Palasa", "palasakasigugga": "Palasa",
    "palasakasiguggaurban": "Palasa", "kotturu": "Kothuru", "kotabommili": "Kotabommali",
    "lnpeta": "L.N.Peta", "lakshminarasannapeta": "L.N.Peta", "meilaputti": "Meliaputti",
    "ranastalam": "Ranasthalam", "amudalavalasa": "Amadalavalasa",
    "ganguvarisingadam": "G.Sigadam", "singadam": "G.Sigadam", "ganguvari": "G.Sigadam", "ganguvarisigadam": "G.Sigadam", "gsigadam": "G.Sigadam",
    "srikakulamurban": "Srikakulam", "santabommali": "Santhabommali",
}.items()})

# Telugu-script pages come out of the PDF as (cid:NNN) glyph runs. They are stable
# for this report generator, so they are matched literally (longest suffix wins,
# because the row prints "<division><mandal>" with no separator).
CID_RAW = {
 "(cid:415)(cid:633)(cid:521)": "Laveru", "(cid:420)రవ(cid:711)ట": "Saravakota",
 "ఎచ(cid:316)ర(cid:343)": "Etcherla", "(cid:675)(cid:546)(cid:326)(cid:521)": "Kothuru",
 "నరసన(cid:330)(cid:623)ట": "Narasannapeta", "(cid:407)తపట(cid:330)ం": "Pathapatnam",
 "(cid:695)ం(cid:548)(cid:521)": "Ponduru", "(cid:711)ట(cid:733)(cid:411)(cid:335)(cid:452)": "Kotabommali",
 "(cid:711)ట(cid:733)(cid:411)(cid:335)(cid:451)": "Kotabommali", "ప(cid:415)స": "Palasa",
 "(cid:744)ం(cid:623)ట": "Sompeta", "ఆమ(cid:404)లవలస": "Amadalavalasa",
 "గం(cid:497)(cid:417)(cid:449)(cid:456)(cid:389)(cid:399)ం": "G.Sigadam", "క(cid:453)(cid:433)": "Kaviti",
 "వజ(cid:338)(cid:515)క(cid:546)(cid:326)(cid:521)": "Vajrapukothuru", "రణస(cid:328)లం": "Ranasthalam",
 "సంత(cid:733)మ(cid:335)(cid:451)": "Santhabommali", "సంత(cid:733)మ(cid:335)(cid:452)": "Santhabommali",
 "జ(cid:523)(cid:555)(cid:521)": "Jalumuru", "(cid:389)ర": "Gara", "(cid:553)ర(cid:318)": "Burja",
 "(cid:490)(cid:337)(cid:387)(cid:495)ళం": "Srikakulam", "(cid:457)రమండలం": "Hiramandalam",
 "మందస": "Mandasa", "ల(cid:459)(cid:335)నరసన(cid:330)జ(cid:479)ట": "L.N.Peta",
 "ల(cid:339)(cid:335)నరసన(cid:330)జ(cid:487)ట": "L.N.Peta", "స(cid:521)(cid:517)(cid:430)(cid:318)(cid:451)": "Sarubujjili",
 "స(cid:521)(cid:559)(cid:410)(cid:318)(cid:452)": "Sarubujjili", "నం(cid:440)(cid:389)ం": "Nandigam",
 "(cid:731)(cid:415)(cid:423)": "Polaki", "(cid:695)(cid:415)(cid:407)": "Polaki",
 "కం(cid:428)(cid:451)": "Kanchili", "ఇ(cid:392)(cid:316)(cid:515)రం": "Ichchapuram",
 "(cid:577)క(cid:311)(cid:451)": "Tekkali",
}
CID = {re.sub(r"\s+", "", k): v for k, v in CID_RAW.items()}
CID_KEYS = sorted(CID, key=len, reverse=True)

NUM = re.compile(r"^-?\d[\d,]*(?:\.\d+)?%?$")


def canon(name):
    if not name:
        return None
    n = re.sub(r"[-\u2013]\s*(R|U)$", "", name.strip())
    n = re.sub(r"\((urban|rural|u|r)\)", "", n, flags=re.I).strip()
    if _k(n) in ALIAS:
        return ALIAS[_k(n)]
    c = re.sub(r"\s+", "", n)
    for k in CID_KEYS:                      # longest suffix wins
        if c.endswith(k):
            return CID[k]
    return None


def nums(toks):
    out = []
    for t in toks:
        t = t.strip()
        if NUM.match(t):
            t = t.replace(",", "").rstrip("%")
            if t not in ("", "-"):
                out.append(float(t))
    return out


SKIPHOLD = re.compile(r"division|report|total|register|abstract", re.I)


def prep(text, telugu=False):
    """Normalise rows; re-join rows whose name or numbers wrapped to their own line."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if telugu:
        return lines
    out, numhold, namehold = [], None, None
    for ln in lines:
        toks = ln.split()
        m0 = re.match(r"^(\d+)\s+(.*)$", ln)
        allnum = len(toks) > 2 and all(NUM.match(t) for t in toks)
        if allnum and namehold and m0 and int(m0.group(1)) <= 120:
            out.append(" ".join([m0.group(1)] + namehold + m0.group(2).split()))
            numhold = namehold = None
            continue
        if allnum:
            numhold = toks
            continue
        if (not any(re.search(r"\d", t) for t in toks) and len(toks) <= 4
                and len(ln) < 40 and not SKIPHOLD.search(ln)):
            namehold = toks
            continue
        m = re.match(r"^(\d+)\s+(.*)$", ln)
        if m and (numhold or namehold):
            rest = m.group(2).split()
            nm, i = [], 0
            while i < len(rest) and not NUM.match(rest[i]):
                nm.append(rest[i]); i += 1
            name = nm if nm else (namehold or [])
            if numhold and nm:
                name = nm
            vals = (numhold or []) + rest[i:]
            out.append(" ".join([m.group(1)] + name + vals))
            numhold = namehold = None
            continue
        numhold = namehold = None
        out.append(ln)
    return out


def eng_rows(lines):
    for line in lines:
        if re.match(r"^(sub total|grand total|total)", line, re.I):
            continue
        m = re.match(r"^(\d+)\s+(.*)$", line)
        if not m:
            continue
        toks, name_toks, i = m.group(2).split(), [], 0
        while i < len(toks) and not NUM.match(toks[i]):
            name_toks.append(toks[i]); i += 1
        n = canon(" ".join(name_toks))
        v = nums(toks[i:])
        if n and v:
            yield n, v


def tel_rows(lines):
    """Telugu pages print the numbers first and the name on the following line."""
    pend = None
    for line in lines:
        if re.match(r"^(sub total|grand total|total)", line, re.I):
            pend = None; continue
        m = re.match(r"^(\d+)\s+(.*)$", line)
        if m and re.search(r"\d", m.group(2)):
            pend = nums(m.group(2).split())
        elif pend is not None and ("cid:" in line or re.search(r"[\u0c00-\u0c7f]", line)):
            n = canon(line)
            if n:
                yield n, pend
            pend = None


TITLE_RE = re.compile(r"\breport\b|\babstract\b|status on", re.I)


def page_title(txt):
    """Best-effort report title for a page, used to name unrecognised subjects."""
    best = None
    for ln in txt.split("\n")[:40]:
        l = " ".join(ln.split())
        if len(l) < 18 or re.match(r"^\d", l) or "cid:" in l:
            continue
        if TITLE_RE.search(l):
            l = re.sub(r"\s*\b(as on|from)\b.*$", "", l, flags=re.I).strip(" -–:")
            best = l[:70]
            break
    return best


def slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:40]


def guess_cols(header, ncols):
    """Try to read column names off the header line that mentions 'Mandal'."""
    for ln in header:
        if re.search(r"mandal", ln, re.I) and not re.match(r"^\d", ln):
            toks = ln.split()
            i = max(j for j, t in enumerate(toks) if re.match(r"mandal|name", t, re.I))
            rest = toks[i + 1:]
            if len(rest) == ncols:
                return rest
            if len(rest) == ncols + 1 and rest[-1] == "%":
                rest[-2] += " %"
                return rest[:-1]
    return ["Col %d" % (i + 1) for i in range(ncols)]


OFFICER_RE = re.compile(r"(Collector & District Magistrate|Joint Collector|Revenue Divisional Officer, \w+|"
                        r"Tahsildar, \w+|Constituency Special Officer, \w+)")


def split_mandal_village(txt):
    toks = txt.split()
    for n in (3, 2, 1):
        if len(toks) >= n:
            c = canon(" ".join(toks[:n]))
            if c:
                return c, " ".join(toks[n:])
    return None, txt


def a22_details(pages):
    """Application-level list behind the 22-A pendency figures."""
    out, seen = [], set()
    row = re.compile(r"(TTA\d+)\s+(.*?)\s*(\d{10})\s+(.*?)\s+(\d{2}-\d{2}-\d{4})\s*(\S+)?\s*(.*?)\s*"
                     r"(22A-\(1\)\([A-E]\))\s+(BSLA|WSLA)(.*)$")
    loose = re.compile(r"(TTA\d+)\s+(.*?)\s*(\d{10})\s+(.*?)\s+(\d{2}-\d{2}-\d{4})\s*(\S+)?")
    for t in pages:
        if "22-a list service list pending application" not in t.lower():
            continue
        f = re.sub(r"\s+", " ", t)
        pos = [m.start() for m in re.finditer(r"TTA\d+", f)] + [len(f)]
        for a, b in zip(pos, pos[1:]):
            m = row.match(f[a:b])
            if m:
                app, name, mob, mv, dt, off, rem1, cat, sla, tail = m.groups()
            else:
                m2 = loose.match(f[a:b])
                if not m2:
                    continue
                app, name, mob, mv, dt, off = m2.groups()
                rem1, cat, sla, tail = "", "", "", ""
            if app in seen:
                continue
            seen.add(app)
            mandal, village = split_mandal_village(mv)
            rem = ((rem1 or "") + " " + re.sub(r"^\s*\d+\s*", "", tail or "")).strip()[:170]
            raw = (off or "").strip()
            lvl = ("VRO" if re.search(r"VRO|WRS", raw) else
                   "MRO" if "MRO" in raw or "Tahsildar" in raw else
                   "RDO" if "RDO" in raw else "JC" if raw.startswith("JC") else raw or "—")
            out.append({"id": app, "name": (name or "").title() or "—", "level": lvl,
                        "mobile": mob, "mandal": mandal,
                        "village": village.title(), "date": dt, "with": (off or "").strip(),
                        "cat": cat, "sla": sla, "remarks": rem})
    return [r for r in out if r["mandal"]]


PGRS_SUBJECTS = ["Record Of Rights (RoR)", "Complaints on Revenue Officers", "Complaints on Land Grabbing",
                 "Grievances in Re-Survey", "Request for Removal from 22(A)", "Conversion Of Agriculture Lands",
                 "Land Acquisition Issues", "Agency Land Problems", "Caste Verification",
                 "Encroachments", "Encoachments", "Assignments", "Miscellaneous"]


def _sub(needle, hay):
    """Is needle a subsequence of hay?  Column bleed interleaves two strings but
    keeps the order of each, so the original survives as a subsequence."""
    it = iter(hay)
    return all(ch in it for ch in needle)


def match_subject(cell):
    c = re.sub(r"[^a-z0-9]", "", (cell or "").lower())
    best = None
    for v in PGRS_SUBJECTS:
        k = re.sub(r"[^a-z0-9]", "", v.lower())
        if k and _sub(k, c) and (best is None or len(k) > len(re.sub(r"[^a-z0-9]", "", best.lower()))):
            best = v
    return ("Encroachments" if best == "Encoachments" else best) or ""


def pgrs_details(pdf, reopened):
    """Grievance-level lists behind the beyond-SLA and re-opened figures."""
    out = []
    for page in pdf.pages:
        t = page.extract_text() or ""
        if "grievance no" not in t.lower():
            continue
        if ("re_open" in t.lower()) != reopened:
            continue
        for r in (page.extract_table() or [])[1:]:
            cells = [(c or "").replace("\n", " ").strip() for c in r]
            joined = " ".join(cells)
            gid = next((c for c in cells if re.match(r"^(SKL|RSSKL|PRPM|KKD)\w+$", c)), None)
            dt = next((c for c in cells if re.match(r"^\d{2}/\d{2}/\d{4}$", c)), None)
            if not gid:
                continue
            i = cells.index(gid)
            mandal = None
            for c in cells[i:i + 6]:
                mandal = mandal or canon(c)
            off = OFFICER_RE.search(joined)
            who = off.group(1) if off else ""
            for full, shrt in (("Revenue Divisional Officer", "RDO"),
                               ("Collector & District Magistrate", "Collector"),
                               ("Constituency Special Officer", "Special Officer")):
                who = who.replace(full, shrt)
            subj = ""
            for c in cells[i + 6:i + 10]:
                subj = subj or match_subject(c)
            lvl = ("Collector" if who.startswith("Collector") else
                   "Joint Collector" if who.startswith("Joint Collector") else
                   "RDO" if who.startswith("RDO") else
                   "Tahsildar" if who.startswith("Tahsildar") else
                   "Special Officer" if who.startswith("Special Officer") else "Not shown")
            out.append({"id": gid, "name": cells[i + 1] if len(cells) > i + 1 else "", "subject": subj,
                        "level": lvl,
                        "date": dt, "mandal": mandal,
                        "secretariat": cells[i + 4] if len(cells) > i + 4 else "",
                        "with": who.strip(" ,")})
    return [r for r in out if r["mandal"]]


HOUSE_OFF = [("rdo", 2), ("tah", 3), ("vro", 4), ("jc", 5), ("wrs", 6), ("mc", 7)]


def house_officers(pdf):
    """Housing pendency by the level it is sitting at, mandal wise."""
    out = {}
    for page in pdf.pages:
        t = page.extract_text() or ""
        if "housing for all officer wise" not in t.lower():
            continue
        for r in (page.extract_table() or []):
            cells = [(c or "").strip() for c in r]
            if len(cells) < 8:
                continue
            m = canon(cells[1])
            if not m:
                continue
            row = out.setdefault(m, {})
            for key, i in HOUSE_OFF:
                if cells[i].replace(",", "").isdigit():
                    row["house_" + key] = row.get("house_" + key, 0) + float(cells[i].replace(",", ""))
    return out


def parse(pdf_path):
    d = {}
    pdf = pdfplumber.open(pdf_path)
    pages = [(p.extract_text() or "") for p in pdf.pages]

    date = None
    m = re.search(r"(\d{1,2})[_.](\d{1,2})[_.](\d{2})(?!\d)", os.path.basename(pdf_path))
    if m:
        date = "20%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1)))
    if not date:
        for t in pages[:4]:
            m = re.search(r"to\s*(\d{1,2})\.(\d{1,2})\.(\d{2})(?!\d)", t)
            if m:
                date = "20%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1))); break
    if not date:
        date = str(datetime.date.today())

    def add(m, k, v):
        if v is not None:
            r = d.setdefault(m, {}); r[k] = round(r.get(k, 0) + v, 4)

    def first(m, k, v):
        r = d.setdefault(m, {})
        if k not in r and v is not None:
            r[k] = v

    kind = None
    autos, auto_slug = {}, None
    for txt in pages:
        low = txt.lower()
        matched = False
        for key, sig in (("a22", "modification of 22a lists pending"),
                         ("skip", "22-a list service list pending application"),
                         ("pgrs", "revenue dept., - status on pgrs"),
                         ("sslr", "sslr dept., - status on pgrs"),
                         ("r1", "certificates uploaded report"),
                         ("inv", "inventory approval report"),
                         ("house", "housing for all report from"),
                         ("skip", "housing for all officer wise"),
                         ("mutf", "mutations - corrections"),
                         ("fpolr", "abstract report on fpolr"),
                         ("case6", "case-6 (itharulu)"),
                         ("epts", "electronic performance tracking")):
            if sig in low:
                kind = key
                matched = True
                if key == "mutf":
                    kind = "mutc" if "15.06.24 to" in low else "mut"
                break

        if not matched:
            t = page_title(txt)
            if t:
                sl = slugify(t)
                if sl not in autos:
                    autos[sl] = {"title": t, "rows": {}, "ncols": 0,
                                 "header": [" ".join(l.split()) for l in txt.split("\n")[:6]]}
                kind, auto_slug = "auto", sl
        if kind == "auto":
            a = autos[auto_slug]
            for n, v in eng_rows(prep(txt)):
                if n not in a["rows"]:
                    a["rows"][n] = v
                    a["ncols"] = max(a["ncols"], len(v))
            continue

        if kind in (None, "skip"):
            continue

        tel = kind in ("case6", "fpolr")
        lines = prep(txt, telugu=tel)
        rows = tel_rows(lines) if tel else eng_rows(lines)

        for n, v in rows:
            if kind == "a22" and len(v) >= 15:
                add(n, "a22_total", v[0]); add(n, "a22_closed", v[3])
                add(n, "a22_pending", v[6]); add(n, "a22_pend_bsla", v[5])
                add(n, "a22_vro", v[7] + v[8]); add(n, "a22_mro", v[9] + v[10])
                add(n, "a22_rdo", v[11] + v[12]); add(n, "a22_jc", v[13] + v[14])
                if len(v) >= 18:
                    add(n, "a22_vc_disposed", v[17])
            elif kind == "pgrs" and len(v) >= 9:
                add(n, "pgrs_recd", v[0]); add(n, "pgrs_pending", v[1]); add(n, "pgrs_bsla", v[3])
                add(n, "pgrs_redressed", v[4]); add(n, "pgrs_reopened", v[8])
            elif kind == "sslr" and len(v) >= 9:
                add(n, "sslr_recd", v[0]); add(n, "sslr_pending", v[1]); add(n, "sslr_bsla", v[3])
                add(n, "sslr_redressed", v[4]); add(n, "sslr_reopened", v[8])
            elif kind == "r1" and len(v) >= 6:
                add(n, "r1_villages", v[0]); add(n, "r1_updated", v[1])
                add(n, "r1_balance", v[2]); add(n, "r1_cert_approved", v[4])
            elif kind == "inv" and len(v) >= 12:
                add(n, "inv_registered", v[9]); add(n, "inv_scanned", v[11])
            elif kind == "house" and len(v) >= 8:
                add(n, "house_total", v[0]); add(n, "house_open_bsla", v[1])
                add(n, "house_open_wsla", v[2]); add(n, "house_closed", v[-1])
            elif kind in ("mut", "mutc") and len(v) >= 17:
                p = "mut_" if kind == "mut" else "mutc_"
                for j, who in enumerate(("form8", "vro", "ri", "tah")):
                    first(n, p + who + "_w", v[6 + j*2]); first(n, p + who + "_b", v[7 + j*2])
            elif kind in ("mut", "mutc") and len(v) >= 9:
                p = "mut_" if kind == "mut" else "mutc_"
                first(n, p + "recd", v[0]); first(n, p + "approved", v[1])
                first(n, p + "rejected", v[3]); first(n, p + "disposed", v[5])
                first(n, p + "disp_bsla", v[6]); first(n, p + "pending", v[8])
            elif kind == "case6" and len(v) >= 4:
                add(n, "case6_pending_sy", v[0]); add(n, "case6_pending_ext", v[1])
                add(n, "case6_cleared_sy", v[2])
            elif kind == "fpolr" and len(v) >= 2:
                add(n, "fpolr_apps", v[0]); add(n, "fpolr_lpms", v[1])
            elif kind == "epts" and len(v) >= 5:
                add(n, "epts_target", v[0]); add(n, "epts_uploaded", v[1])
                add(n, "epts_prev_week", v[2]); add(n, "epts_day", v[4])

    for m, r in d.items():
        pct = lambda a, b: round(100.0 * r.get(a, 0) / r[b], 1) if r.get(b) else None
        r["r1_cert_pct"] = pct("r1_cert_approved", "r1_villages")
        r["inv_scan_pct"] = pct("inv_scanned", "inv_registered")
        r["epts_pct"] = pct("epts_uploaded", "epts_target")
        r["mut_pend_pct"] = pct("mut_pending", "mut_recd")
        r["mutc_pend_pct"] = pct("mutc_pending", "mutc_recd")
        r["mut_bsla_pct"] = pct("mut_disp_bsla", "mut_disposed")
        r["pgrs_reopen_pct"] = pct("pgrs_reopened", "pgrs_recd")
        r["house_pending"] = r.get("house_open_bsla", 0) + r.get("house_open_wsla", 0)
        r["a22_closed_pct"] = pct("a22_closed", "a22_total")

    subjects = {}
    for sl, a in autos.items():
        if len(a["rows"]) < 5:            # not a mandal-wise table; ignore
            continue
        cols = guess_cols(a["header"], a["ncols"])
        subjects[sl] = {"title": a["title"], "ncols": a["ncols"],
                        "cols": cols, "header": a["header"]}
        for m, vals in a["rows"].items():
            for i, v in enumerate(vals):
                d.setdefault(m, {})["x:%s:%d" % (sl, i + 1)] = v

    for m, row in house_officers(pdf).items():
        d.setdefault(m, {}).update(row)

    details = {"a22": a22_details(pages),
               "pgrs_bsla": pgrs_details(pdf, False),
               "pgrs_reopen": pgrs_details(pdf, True)}
    pdf.close()

    out = {"date": date, "source": os.path.basename(pdf_path), "subjects": subjects,
           "details": details, "mandals": {}}
    for m in MANDALS:
        out["mandals"][m] = {"division": DIV_OF[m], **d.get(m, {})}
    return out


if __name__ == "__main__":
    src = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(outdir, exist_ok=True)
    snap = parse(src)
    p = os.path.join(outdir, "snapshot_%s.json" % snap["date"])
    json.dump(snap, open(p, "w"), indent=1)
    keys = set()
    for r in snap["mandals"].values():
        keys |= set(r)
    print("wrote", p, "|", len(snap["mandals"]), "mandals,", len(keys), "fields")
    for kind, rows in snap.get("details", {}).items():
        print("  detail list:", kind, len(rows), "records")
    for sl, meta in snap.get("subjects", {}).items():
        print("  new subject picked up:", meta["title"], "(%d columns)" % meta["ncols"])
    for m, r in snap["mandals"].items():
        miss = [k for k in ("a22_pending", "pgrs_pending", "mut_pending", "epts_pct", "case6_pending_sy") if k not in r]
        if miss:
            print("  note:", m, "missing", ", ".join(miss))
