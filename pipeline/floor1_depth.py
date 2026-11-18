import bpy, math, json, os, time
import numpy as np
from mathutils import Vector, Matrix

W, H = 1280, 720
OUT = "/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/f1new2/"
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x = W; sc.render.resolution_y = H
C = Matrix(((1,0,0),(0,0,1),(0,-1,0)))
Cq = C.to_quaternion()

# 10 个核心机位（Blender 坐标：X 右, Y 深, Z 上）
SPECS = [
    ("01-俯视45",   (13.5, -13.5, 9.2), (0, 2, 0.8),   20),
    ("02-俯视45反", (13.5,  13.5, 9.0), (0, 2, 0.8),   20),
    ("03-俯视60",   (0.0,  -10.0, 8.2), (0, 4, 1.0),   20),
    ("04-高位斜",   (9.0,    6.0, 7.5), (-2, -2, 1.0), 20),
    ("05-高位斜反", (-9.0,   2.0, 7.8), (4, 4, 1.2),   20),
    ("06-门内平视", (0.0,  -14.6, 1.7), (0, 8, 4.2),   20),
    ("07-侧墙",     (12.5,   0.0, 1.7), (-8, 6, 3.6),  20),
    ("08-供桌前",   (-3.0,   5.0, 1.7), (0, 13, 2.4),  18),
    ("09-仰视中心", (0.0,    0.0, 1.7), (3, -3, 9.5),  16),
    ("10-仰视柱间", (9.5,   -9.5, 1.7), (4, -4, 7.5),  15),
]

def depth_of(cam):
    deps = bpy.context.evaluated_depsgraph_get()
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
            hit, loc, nor, idx, ob, mat = sc.ray_cast(deps, origin, d, distance=300.0)
            out[y, x] = (loc - origin).dot(fwd) if hit else 0.0
    return out

def save_exr(arr, path):
    h, w = arr.shape
    img = bpy.data.images.new("D", width=w, height=h, float_buffer=True)
    rgba = np.zeros((h, w, 4), dtype=np.float32)
    rgba[..., 0] = arr; rgba[..., 3] = 1.0
    img.pixels.foreach_set(rgba.ravel())
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    img.filepath_raw = path; img.file_format = 'OPEN_EXR'
    img.save(); bpy.data.images.remove(img)

cams = {}
t0 = time.time()
for name, pos, tgt, lens in [s for s in SPECS if s[0][:2] in ('03','08','09','10')]:
    cd = bpy.data.cameras.new(name); cd.lens = lens
    cd.clip_start = 0.05; cd.clip_end = 300
    o = bpy.data.objects.new(name, cd); o.location = pos
    o.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(o)
    arr = depth_of(o)
    save_exr(arr, os.path.join(OUT, f"D_{name}.exr"))
    v = arr[arr > 0]
    fx = lens / cd.sensor_width * W
    p = C @ o.matrix_world.to_translation()
    q = Cq @ o.matrix_world.to_quaternion()
    cams[name] = {"camera": {
        "extrinsics": {"position": [round(float(x),4) for x in p],
                       "quaternion": [round(float(x),5) for x in (q.x,q.y,q.z,q.w)],
                       "coordinateSystem": "rub"},
        "intrinsics": {"fx": round(fx,3), "fy": round(fx,3),
                       "cx": W/2, "cy": H/2, "width": W, "height": H}}}
    print(f"DONE {name} median={float(np.median(v)) if v.size else 0:.2f} {time.time()-t0:.0f}s")

json.dump(cams, open(os.path.join(OUT, "cameras.json"), "w"), indent=1)
print("ALL DONE", f"{time.time()-t0:.0f}s")
