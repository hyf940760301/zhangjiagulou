import bpy, json, os, time
import numpy as np
from mathutils import Vector, Matrix
W, H = 1280, 720
OUT = "/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/f5new/"
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
C = Matrix(((1,0,0),(0,0,1),(0,-1,0))); Cq = C.to_quaternion()

SPECS = [
    ("01-爬向口子", (0.0, -13.5, 0.62), (0, -6, 0.35), 18),
    ("02-横爬",     (-13.0, 0.0, 0.62), (10, 0, 0.35), 18),
    ("03-贴地",     (-4.0, -3.0, 0.42), (3, -8, 0.30), 16),
    ("04-斜爬",     (9.0, 9.0, 0.66),   (-6, -6, 0.35), 18),
    ("05-反向",     (0.0, 13.5, 0.62),  (0, -4, 0.35), 18),
    ("06-俯看口子", (2.6, -8.0, 1.05),  (0, -8, 0.0),  20),
]

def depth_of(cam):
    deps = bpy.context.evaluated_depsgraph_get()
    mw = cam.matrix_world; origin = mw.translation
    fwd = (mw.to_3x3() @ Vector((0,0,-1))).normalized()
    right = (mw.to_3x3() @ Vector((1,0,0))).normalized()
    up = (mw.to_3x3() @ Vector((0,1,0))).normalized()
    fx = cam.data.lens / cam.data.sensor_width * W
    out = np.zeros((H, W), np.float32)
    for y in range(H):
        for x in range(W):
            d = (fwd + right*((x-W/2)/fx) + up*(-(y-H/2)/fx)).normalized()
            hit, loc, nor, idx, ob, mat = sc.ray_cast(deps, origin, d, distance=300.0)
            out[y, x] = (loc-origin).dot(fwd) if hit else 0.0
    return out

def save_exr(a, path):
    h, w = a.shape
    img = bpy.data.images.new("D", width=w, height=h, float_buffer=True)
    rgba = np.zeros((h,w,4), np.float32); rgba[...,0]=a; rgba[...,3]=1.0
    img.pixels.foreach_set(rgba.ravel())
    sc.render.image_settings.file_format='OPEN_EXR'; sc.render.image_settings.color_depth='32'
    img.filepath_raw=path; img.file_format='OPEN_EXR'; img.save(); bpy.data.images.remove(img)

cams = {}
t0=time.time()
for name,pos,tgt,lens in SPECS:
    cd = bpy.data.cameras.new(name); cd.lens=lens; cd.clip_start=0.05; cd.clip_end=300
    o = bpy.data.objects.new(name,cd); o.location=pos
    o.rotation_euler=(Vector(tgt)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
    sc.collection.objects.link(o)
    arr = depth_of(o); save_exr(arr, os.path.join(OUT, f"D_{name}.exr"))
    v = arr[arr>0]
    fx = lens/cd.sensor_width*W
    p = C @ o.matrix_world.to_translation(); q = Cq @ o.matrix_world.to_quaternion()
    cams[name] = {"camera": {"extrinsics": {"position":[round(float(x),4) for x in p],
                   "quaternion":[round(float(x),5) for x in (q.x,q.y,q.z,q.w)], "coordinateSystem":"rub"},
                   "intrinsics": {"fx":round(fx,3),"fy":round(fx,3),"cx":W/2,"cy":H/2,"width":W,"height":H}}}
    print(f"DONE {name} median={float(np.median(v)) if v.size else 0:.2f}")
json.dump(cams, open(os.path.join(OUT,"cameras.json"),"w"), indent=1)
print("ALL DONE", f"{time.time()-t0:.0f}s")
