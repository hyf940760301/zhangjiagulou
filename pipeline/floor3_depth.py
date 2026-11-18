import bpy, json, os, time
import numpy as np
from mathutils import Vector, Matrix
W, H = 1280, 720
OUT = "/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/f3new/"
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
C = Matrix(((1,0,0),(0,0,1),(0,-1,0))); Cq = C.to_quaternion()

SPECS = [
    ("01-正面",   (0.0, -11.5, 1.7), (0, 0, 2.2),  24),
    ("02-侧面",   (11.0, 0.5, 1.7),  (0, 0, 2.2),  24),
    ("03-背面",   (0.0, 11.5, 1.7),  (0, 0, 2.2),  24),
    ("04-高位侧", (-10.5, 0.0, 7.2), (0, 0, 1.8),  20),
    ("05-头颈",   (-6.0, -9.0, 3.0), (0, -1, 3.0), 30),
    ("06-另一侧", (-11.5, 0.0, 1.7),(0, 0, 2.2),  24),
    ("07-高位正", (0.0, -9.0, 5.5),  (0, 0, 1.5),  22),
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
