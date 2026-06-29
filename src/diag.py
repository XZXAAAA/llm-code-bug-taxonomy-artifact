import glob, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
BT = "```"
for f in sorted(glob.glob("data/raw/generations/*.jsonl")):
    lines = [json.loads(l) for l in open(f, encoding="utf-8")]
    closed = sum(1 for x in lines if x["raw_reply"].count(BT) >= 2)
    avglen = sum(len(x["raw_reply"]) for x in lines) // len(lines)
    print(f"{os.path.basename(f):44} closed:{closed:3}/{len(lines)}  unclosed:{len(lines)-closed:3}  avglen:{avglen}")
