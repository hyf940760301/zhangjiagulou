import bpy, numpy as np, json, sys
from pathlib import Path
args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
ROOT = Path("/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floors")
targets = [ROOT / f"f{n}" for n in args] if args else sorted(ROOT.glob("f*"))
for f in targets:
    if not f.exists(): continue
    bad, meds = [], {}
    for p in sorted(f.glob("*.exr")):
        img = bpy.data.images.load(str(p))
        a = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)[:, :, 0]
        v = a[a > 0]
        m = float(np.median(v)) if v.size else 0.0
        name = p.stem[2:]
        meds[name] = round(m, 3)
        if m < 1.2: bad.append(name)
        bpy.data.images.remove(img)
    (f / "depth-audit.json").write_text(json.dumps({"median": meds, "bad": bad}, indent=1))
    print(f"{f.name}: {len(meds)} frames, bad={bad}")
