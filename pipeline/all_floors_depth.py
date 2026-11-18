import bpy, math, json, time, os
import numpy as np
from mathutils import Vector, Matrix

W, H = 1280, 720
BASE, SH = 3.2, 5.2
OUT = "/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floors/"
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
sc.render.resolution_x = W; sc.render.resolution_y = H
C = Matrix(((1,0,0),(0,0,1),(0,-1,0)))
Cq = C.to_quaternion()

def cam_at(name, pos, target, lens=24):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    cd.clip_start = 0.05; cd.clip_end = 400
    o = bpy.data.objects.new(name, cd); o.location = pos
    o.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(o)
    return o

def depth_of(cam):
    deps = bpy.context.evaluated_depsgraph_get()      # 必须每次取新
    mw = cam.matrix_world
    origin = mw.translation
    fwd = (mw.to_3x3() @ Vector((0,0,-1))).normalized()
    right = (mw.to_3x3() @ Vector((1,0,0))).normalized()
    up = (mw.to_3x3() @ Vector((0,1,0))).normalized()
    fx = cam.data.lens / cam.data.sensor_width * W
    out = np.zeros((H, W), dtype=np.float32)
    for y in range(H):
        for x in range(W):
            d = (fwd + right*((x - W/2)/fx) + up*(-(y - H/2)/fx)).normalized()
            hit, loc, nor, idx, ob, mat = sc.ray_cast(deps, origin, d, distance=500.0)
            out[y, x] = (loc - origin).dot(fwd) if hit else 0.0
    return out

def save_exr(arr, path):
    h, w = arr.shape
    img = bpy.data.images.new("D", width=w, height=h, float_buffer=True)
    rgba = np.zeros((h, w, 4), dtype=np.float32)
    rgba[..., 0] = arr
    rgba[..., 3] = 1.0
    img.pixels.foreach_set(rgba.ravel())
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    img.filepath_raw = path; img.file_format = 'OPEN_EXR'
    img.save()
    bpy.data.images.remove(img)

def floor_specs(fi):
    z0 = BASE + fi * SH
    eye = z0 + 1.70
    specs = []
    # 七层的玉棺平台更宽，A 环要外扩，否则相机扎进天井角柱/棺台
    # 各层陈设不同，A 环要按占位避让
    ra = 4.0; aoff = 0.0; ea = eye
    if fi == 3:          # 玄龟壳半径 4 m
        ra, aoff = 6.2, math.pi/8
    elif fi == 5:        # 藏宝箱高 1.55 m 且铺满
        ra, aoff, ea = 5.4, math.pi/8, eye + 1.5
    elif fi == 6:        # 玉棺平台宽
        ra, aoff = 5.0, math.pi/8
    for k in range(8):
        a = 2*math.pi*k/8 + aoff
        specs.append((f"A{k}", (ra*math.cos(a), ra*math.sin(a), ea), (0, 0, z0+1.2)))
    for k in range(8):
        a = 2*math.pi*k/8 + math.pi/8
        specs.append((f"B{k}", (8.0*math.cos(a), 8.0*math.sin(a), eye), (0, 0, z0+1.2)))
    for k in range(4):
        a = 2*math.pi*k/4
        specs.append((f"U{k}", (2.5*math.cos(a), 2.5*math.sin(a), z0+3.0),
                      (2.5*math.cos(a), 2.5*math.sin(a), z0 + SH)))
    return specs, z0

import sys
_ONLY = [int(x) for x in sys.argv[sys.argv.index('--')+1:]] if '--' in sys.argv else list(range(7))
t0 = time.time()
for fi in _ONLY:
    d = os.path.join(OUT, f"f{fi+1}")
    os.makedirs(d, exist_ok=True)
    specs, z0 = floor_specs(fi)
    cams = {}
    for name, pos, tgt in specs:
        cam = cam_at(f"F{fi}_{name}", pos, tgt)
        arr = depth_of(cam)
        save_exr(arr, os.path.join(d, f"D_{name}.exr"))
        fx = cam.data.lens / cam.data.sensor_width * W
        p = C @ cam.matrix_world.to_translation()
        q = Cq @ cam.matrix_world.to_quaternion()
        cams[name] = {"camera": {
            "extrinsics": {"position": [round(float(v),4) for v in p],
                           "quaternion": [round(float(v),5) for v in (q.x,q.y,q.z,q.w)],
                           "coordinateSystem": "rub"},
            "intrinsics": {"fx": round(fx,3), "fy": round(fx,3),
                           "cx": W/2, "cy": H/2, "width": W, "height": H}}}
    json.dump(cams, open(os.path.join(d, "cameras.json"), "w"), indent=1)
    print(f"FLOOR {fi+1} done {time.time()-t0:.0f}s")

print("ALL DONE", f"{time.time()-t0:.0f}s")
