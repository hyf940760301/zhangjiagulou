import bpy, bmesh, math, random
from mathutils import Vector

# ============================================================
# 张家古楼 · 六层（藏宝）
#   箱柜沿墙堆放 + 一圈青铜铃铛悬在梁下
#   30×30，净高 6 m
# ============================================================
random.seed(31)
PLAN, WALL, H = 30.0, 1.2, 6.0
COL_R, COL_POS = 1.3, 6.5

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def mat(name, rgb, rough=0.85, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*rgb, 1); return m

M_WOOD  = mat("灰木", (0.27, 0.24, 0.21))
M_DARK  = mat("深木", (0.10, 0.09, 0.08))
M_STONE = mat("石板", (0.11, 0.105, 0.10))
M_CHEST = mat("箱木", (0.16, 0.12, 0.09))
M_BRASS = mat("青铜", (0.22, 0.17, 0.08), rough=0.4, metal=0.9)
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

def tube(bm, p0, p1, r0, r1=None, segs=14):
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
WW, WH, SILL = 2.2, 2.4, 3.0
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

# 四巨柱
bm = bmesh.new()
for sx in (-1,1):
    for sy in (-1,1):
        cx, cy = sx*COL_POS, sy*COL_POS
        tube(bm, (cx,cy,0), (cx,cy,H), COL_R*1.10, COL_R, 24)
        tube(bm, (cx,cy,0), (cx,cy,0.45), COL_R*1.45, COL_R*1.42, 24)
        for zz in (2.2, 4.2):
            tube(bm, (cx,cy,zz), (cx,cy,zz+0.24), COL_R*1.30, COL_R*1.28, 24)
bake(bm, "四巨柱", M_DARK)

bm = bmesh.new(); add_box(bm, 0, 0, H+0.25, w2*2, w2*2, 0.5); bake(bm, "七层楼板", M_WOOD)

# ---------- 箱柜（沿墙，堆叠）----------
bm = bmesh.new()
for side in range(4):
    ang = side*math.pi/2; nx, ny = math.sin(ang), -math.cos(ang)
    for k in range(-4, 5):
        t = k*2.6
        for lvl in range(2):
            sx = random.uniform(1.4, 2.0); sy = random.uniform(1.1, 1.5); sz = random.uniform(0.7, 1.0)
            off = 12.0
            cz = 0.4 + lvl*(sz+0.05) + sz/2
            if side % 2 == 0:
                add_box(bm, t, ny*off, cz, sx, sy, sz)
            else:
                add_box(bm, nx*off, t, cz, sy, sx, sz)
bake(bm, "箱柜", M_CHEST)

# ---------- 一圈青铜铃（悬在梁下，半径 6）----------
bm = bmesh.new()
for k in range(24):
    a = 2*math.pi*k/24
    x, y = 6.0*math.cos(a), 6.0*math.sin(a)
    tube(bm, (x, y, H-0.2), (x, y, 4.35), 0.035, 0.035, 8)     # 吊绳
    tube(bm, (x, y, 4.35), (x, y, 3.85), 0.16, 0.30, 12)       # 铃身（上小下大）
    add_box(bm, x, y, 3.80, 0.36, 0.36, 0.10)                   # 铃口
bake(bm, "铜铃阵", M_BRASS)

bm = bmesh.new(); add_box(bm, 0, -9.6, 0.85, 0.45, 0.30, 1.70)
bake(bm, "人形参照", M_HUMAN)

print("BUILT", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath="/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floor6-rebuild.blend")
print("SAVED")
