import bpy, bmesh, math
from mathutils import Vector

# ============================================================
# 张家古楼 · 七层（终极 · 陨玉棺）
#   顶端一层：中央石台上一口陨玉大棺，四根立柱，顶上开一个口子
#   26×26，净高 8 m
# ============================================================
PLAN, WALL, H = 26.0, 1.2, 8.0
COL_R, COL_POS = 1.1, 5.6

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def mat(name, rgb, rough=0.85, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*rgb, 1); return m

M_WOOD  = mat("灰木", (0.26, 0.23, 0.20))
M_DARK  = mat("深木", (0.09, 0.085, 0.08))
M_STONE = mat("石台", (0.16, 0.155, 0.15))
M_JADE  = mat("陨玉", (0.055, 0.11, 0.09), rough=0.25)
M_HUMAN = mat("人", (0.75, 0.18, 0.12))
coll = bpy.context.scene.collection

def add_box(bm, cx, cy, cz, sx, sy, sz):
    cs = []
    for dx in (-.5,.5):
        for dy in (-.5,.5):
            for dz in (-.5,.5):
                cs.append(bm.verts.new((cx+dx*sx, cy+dy*sy, cz+dz*sz)))
    for f in [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]:
        try: bm.faces.new([cs[i] for i in f])
        except ValueError: pass

def tube(bm, p0, p1, r0, r1=None, segs=24):
    if r1 is None: r1 = r0
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1-p0).normalized(); up = Vector((0,0,1))
    if abs(d.dot(up)) > 0.95: up = Vector((1,0,0))
    a = d.cross(up).normalized(); b = d.cross(a).normalized()
    A, B = [], []
    for k in range(segs):
        t = 2*math.pi*k/segs
        off = a*math.cos(t) + b*math.sin(t)
        A.append(bm.verts.new(p0+off*r0)); B.append(bm.verts.new(p1+off*r1))
    for k in range(segs):
        k2 = (k+1) % segs
        try: bm.faces.new([A[k], A[k2], B[k2], B[k]])
        except ValueError: pass

def bake(bm, name, m):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.validate()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m)
    coll.objects.link(ob); return ob

half = PLAN/2; w2 = half + WALL

bm = bmesh.new(); add_box(bm, 0, 0, -0.25, w2*2, w2*2, 0.5); bake(bm, "地面", M_STONE)

bm = bmesh.new()
WW, WH, SILL = 1.8, 2.6, 3.4
for side in range(4):
    ang = side*math.pi/2; nx, ny = math.sin(ang), -math.cos(ang)
    for s in (-1,1):
        t0, t1 = s*WW/2, s*half; c = (t0+t1)/2; ln = abs(t1-t0)
        if side%2==0: add_box(bm, c, ny*w2, H/2, ln, WALL, H)
        else:         add_box(bm, nx*w2, c, H/2, WALL, ln, H)
    if H-(SILL+WH) > 0.01:
        zc = SILL+WH+(H-SILL-WH)/2
        if side%2==0: add_box(bm, 0, ny*w2, zc, WW, WALL, H-SILL-WH)
        else:         add_box(bm, nx*w2, 0, zc, WALL, WW, H-SILL-WH)
    if side%2==0: add_box(bm, 0, ny*w2, SILL/2, WW, WALL, SILL)
    else:         add_box(bm, nx*w2, 0, SILL/2, WALL, WW, SILL)
bake(bm, "墙体", M_WOOD)

bm = bmesh.new()
for side in range(4):
    ang = side*math.pi/2; nx, ny = math.sin(ang), -math.cos(ang)
    cz = SILL+WH/2
    if side%2==0: add_box(bm, 0, ny*(w2-0.2), cz, WW, 0.12, WH)
    else:         add_box(bm, nx*(w2-0.2), 0, cz, 0.12, WW, WH)
bake(bm, "方格窗", M_DARK)

# 四柱（八角，避开正轴）
bm = bmesh.new()
for k in range(4):
    a = 2*math.pi*k/4 + math.pi/4
    cx, cy = COL_POS*math.cos(a)*1.0, COL_POS*math.sin(a)*1.0
    tube(bm, (cx,cy,0), (cx,cy,H), COL_R*1.10, COL_R)
    tube(bm, (cx,cy,0), (cx,cy,0.45), COL_R*1.45, COL_R*1.42)
    for zz in (3.0, 5.6):
        tube(bm, (cx,cy,zz), (cx,cy,zz+0.24), COL_R*1.32, COL_R*1.30)
bake(bm, "四柱", M_DARK)

# 顶：中间开一个圆口（光从上面下来）
bm = bmesh.new()
N = 36; RO = 1.9
inner, outer = [], []
for k in range(N):
    a = 2*math.pi*k/N
    inner.append((RO*math.cos(a), RO*math.sin(a)))
    c, s = math.cos(a), math.sin(a); mm = max(abs(c), abs(s))
    outer.append((w2*c/mm, w2*s/mm))
vi = [bm.verts.new((x,y,H)) for x,y in inner]
vo = [bm.verts.new((x,y,H)) for x,y in outer]
vbi = [bm.verts.new((x,y,H+0.5)) for x,y in inner]
vbo = [bm.verts.new((x,y,H+0.5)) for x,y in outer]
for k in range(N):
    j = (k+1) % N
    bm.faces.new([vi[k], vo[k], vo[j], vi[j]])
    bm.faces.new([vbi[k], vbi[j], vbo[j], vbo[k]])
    bm.faces.new([vi[k], vi[j], vbi[j], vbi[k]])
bake(bm, "屋顶", M_WOOD)

# ---------- 中央石台（三级）+ 陨玉棺 ----------
bm = bmesh.new()
for i, s in enumerate([6.2, 5.2, 4.2]):
    add_box(bm, 0, 0, 0.25 + i*0.45, s, s*1.25, 0.45)
bake(bm, "石台", M_STONE)

bm = bmesh.new()
add_box(bm, 0, 0, 2.10, 2.30, 4.30, 1.30)      # 棺身
add_box(bm, 0, 0, 2.85, 2.52, 4.50, 0.36)      # 棺盖
add_box(bm, 0, 0, 3.08, 1.90, 3.90, 0.14)      # 盖顶脊
for sy in (-1, 1):
    add_box(bm, 0, sy*2.35, 2.10, 1.50, 0.42, 0.70)   # 棺首尾装饰
bake(bm, "陨玉棺", M_JADE)

bm = bmesh.new(); add_box(bm, 0, -9.2, 0.85, 0.45, 0.30, 1.70)
bake(bm, "人形参照", M_HUMAN)

print("BUILT", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath="/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floor7-rebuild.blend")
print("SAVED")
