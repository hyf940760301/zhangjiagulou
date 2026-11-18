#!/usr/bin/env python3
"""把已完成各层装配进 floor-tour。views.json 结构：[{floor, views:[...]}]"""
import json, shutil
from pathlib import Path

ROOT = Path("/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floors")
TOUR = Path("/Users/huyifan/Desktop/DeepSeek Harness/web/zhangjialou/floor-tour")
IMG = TOUR / "img"
IMG.mkdir(parents=True, exist_ok=True)
for f in IMG.glob("*.jpg"):
    f.unlink()

EXTRA = {3: (Path("/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floor3-chisel2"),
             Path("/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floor3-depth/cameras.json"),
             [f"A{i}" for i in range(8)] + [f"B{i}" for i in range(8)] +
             [f"C{i}" for i in range(8)] + [f"U{i}" for i in range(4)])}

out = []
for fi in range(1, 8):
    if fi in EXTRA:
        src, cams_p, order = EXTRA[fi]
        files = sorted(src.glob("frames_*_image.jpg"))
    else:
        d = ROOT / f"f{fi}"
        ch, cams_p = d / "chisel-clean.json", d / "cameras.json"
        if not (ch.exists() and cams_p.exists()):
            print(f"f{fi}: 缺结果，跳过")
            continue
        vdir = d / "views"
        files = sorted(vdir.glob("*_image.jpg"))
        # 机位顺序必须与请求一致（CORE 顺序），不能按字母排
        req_p = d / "chisel-request.json"
        op = json.load(open(ch))
        poses = [f["camera"]["extrinsics"] for f in op["response"]["frames"]]
        req = json.load(open(req_p))
        order = None
    if not files:
        print(f"f{fi}: 无图，跳过")
        continue
    cams = json.load(open(cams_p))
    views = []
    for i, fp in enumerate(files):
        name = f"f{fi}-{i:02d}.jpg"
        shutil.copy(fp, IMG / name)
        if order:
            nm = order[i] if i < len(order) else f"V{i}"
            e = cams[nm]["camera"]["extrinsics"]
        else:
            e = poses[i]                       # 响应里的真实位姿
            # 用位置反查机位名（请求里不带名字）
            best, bd = "?", 1e9
            for cand, cv in cams.items():
                cp = cv["camera"]["extrinsics"]["position"]
                dd = sum((cp[k] - e["position"][k]) ** 2 for k in range(3))
                if dd < bd:
                    bd, best = dd, cand
            nm = best if bd < 0.01 else f"V{i}"
        views.append({"i": i, "name": nm, "file": name,
                      "pos": e["position"], "q": e["quaternion"]})
    out.append({"floor": fi, "views": views})
    print(f"f{fi}: {len(views)} 帧")

json.dump(out, open(TOUR / "views.json", "w"), indent=1)
print("可用楼层:", [o["floor"] for o in out])
