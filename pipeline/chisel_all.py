#!/usr/bin/env python3
"""逐层：上传深度 → atlasChisel → 下载 20 帧。可断点续跑。"""
import json, os, subprocess, sys, time, pathlib

CLI = "/Users/huyifan/Desktop/DeepSeek Harness/.tools/worldlabs/bin/worldlabs"
ROOT = pathlib.Path("/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floors")

STYLE = (
    "dark weathered timber ceiling and floor, rammed earth and aged wood walls, "
    "stone and wood furred with dust and ash, cobwebs, "
    "a single cold shaft of pale daylight falling through the opening in the centre, "
    "deep shadow in the corners, solemn and eerie, desaturated cold palette, "
    "no people, cinematic architectural photography"
)

FLOORS = {
    1: "An ancestral shrine hall inside an ancient Chinese tower: a long offering table with "
       "rows of dark wooden ancestor tablets, faded cloth banners hanging from the beams, a bronze censer, ",
    2: "A trap floor inside an ancient Chinese tower: stone channels running across the floor, "
       "rows of bronze nozzles aimed inward, corroded iron fittings, ",
    3: "A hall lined with rows of blackened bronze statues of armoured warriors, each standing on a "
       "heavy wooden plinth in concentric rings, ",
    4: "A chamber holding a colossal stone tortoise statue, its shell carved with scales and "
       "many skeletal human arms reaching out from the stone, ",
    5: "A burial hall of an ancient Chinese clan: rows of lacquered wooden coffins resting on low "
       "stone beds, a tall genealogy rack at the far end, ",
    6: "A treasure chamber: stacked iron-bound chests along the walls, a ring of bronze bells "
       "suspended from the beams, ",
    7: "A crypt at the very top of an ancient Chinese tower: a single dark jade coffin on a stepped "
       "stone platform, four carved columns around it, ",
}

def run(args, timeout=3600):
    r = subprocess.run([CLI, "--json"] + args, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} 失败:\n{r.stdout}\n{r.stderr}")
    out = r.stdout.strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        lines = [l for l in out.splitlines() if l.strip().startswith("{")]
        return json.loads(lines[-1])

def upload(p):
    return run(["assets", "upload", str(p)])["id"]

def do_floor(fi):
    d = ROOT / f"f{fi}"
    cams_p = d / "cameras.json"
    if not cams_p.exists():
        print(f"  跳过 f{fi}：无 cameras.json")
        return
    cams = json.load(open(cams_p))
    idmap_p = d / "depth-assets.json"
    idmap = json.load(open(idmap_p)) if idmap_p.exists() else {}

    audit_p = d / "depth-audit.json"
    bad = set(json.load(open(audit_p))["bad"]) if audit_p.exists() else set()
    # 15 个核心机位：B 环 8（看整层）+ A 环 4 个正向（近景）+ U 环 3（顶）
    CORE = [f"B{i}" for i in range(8)] + ["A0", "A2", "A4", "A6"] + ["U0", "U1", "U2"]
    names = [n for n in CORE if n in cams and n not in bad]
    if bad:
        print(f"  跳过坏机位 {sorted(bad)}，用 {len(names)} 帧")
    for n in names:
        if n in idmap:
            continue
        f = d / f"D_{n}.exr"
        if not f.exists():
            print(f"  缺 {f}")
            continue
        idmap[n] = upload(f)
        idmap_p.write_text(json.dumps(idmap, indent=1))
        print(f"  {n} -> {idmap[n][:18]}")

    req_p = d / "chisel-request.json"
    frames = []
    for n in names:
        if n not in idmap:
            continue
        fr = json.loads(json.dumps(cams[n]))
        fr["depth"] = {"depthAsset": {"assetId": idmap[n]}}
        frames.append(fr)
    req = {"targetFrames": frames,
           "prompt": FLOORS[fi] + STYLE,
           "enhancePrompt": False, "returnDepth": True, "voxelSize": 0.03}
    req_p.write_text(json.dumps(req, ensure_ascii=False, indent=1))
    print(f"  f{fi}: {len(frames)} 帧，预算 {len(frames)*4}/128")

    out_p = d / "chisel-clean.json"
    if out_p.exists():
        print(f"  f{fi} 已生成，跳过")
        return

    t = time.time()
    op = run(["tasks", "run", "atlasChisel", "--request", str(req_p), "--wait", "--json"])
    if op.get("error"):
        print(f"  f{fi} 失败: {op['error']}")
        return
    json.dump(op, open(out_p, "w"), indent=1)
    print(f"  f{fi} 生成完成 {time.time()-t:.0f}s -> {op['id']}")
    run(["operations", "download", op["id"], "--out", str(d / "views")])

if __name__ == "__main__":
    picks = [int(x) for x in sys.argv[1:]] or list(range(1, 8))
    for fi in picks:
        print(f"=== 第 {fi} 层")
        do_floor(fi)
    print("DONE")
