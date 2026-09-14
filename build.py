#!/usr/bin/env python3
"""Build the dashboards from every snapshot in data/.

    python build.py [data_dir] [out_dir]

Writes one district file and one file per revenue division.
"""
import json, glob, os, sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
hide_mobile = "--no-mobile" in sys.argv        # drop applicant phone numbers from the build
public = "--public" in sys.argv                # for a build that anyone on the internet can open:
                                               # counts, ageing and officer levels stay, the people go
STRIP = ("mobile",) if not public else ("mobile", "name", "village", "remarks")
data = args[0] if len(args) > 0 else "data"
out  = args[1] if len(args) > 1 else "out"
os.makedirs(out, exist_ok=True)

snaps = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(data, "snapshot_*.json")), reverse=True)]
if not snaps:
    sys.exit("no snapshot files in " + data)
def scrub(j):
    for rows in (j.get("details") or {}).values():
        for r in rows:
            for k in STRIP:
                r.pop(k, None)
    return j

if public or hide_mobile:
    for snap in snaps:
        scrub(snap)
    print("left out of this build:", ", ".join(STRIP))

tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")).read()
blob = json.dumps(snaps, separators=(",", ":"))

name = "index.html"
open(os.path.join(out, name), "w").write(tpl.replace("__SNAPSHOT__", blob))
print("wrote", os.path.join(out, name))

# the same days as loose files, so a served copy can pick up new ones without a rebuild
import shutil
ddir = os.path.join(out, "data")
os.makedirs(ddir, exist_ok=True)
files = []
for f in sorted(glob.glob(os.path.join(data, "snapshot_*.json"))):
    if public or hide_mobile:
        json.dump(scrub(json.load(open(f))), open(os.path.join(ddir, os.path.basename(f)), "w"))
    else:
        shutil.copy(f, ddir)
    files.append(os.path.basename(f))
json.dump({"files": files}, open(os.path.join(ddir, "index.json"), "w"), indent=1)
print("wrote", ddir, "|", len(files), "snapshot files + index.json")
print(len(snaps), "days:", ", ".join(s["date"] for s in snaps))
