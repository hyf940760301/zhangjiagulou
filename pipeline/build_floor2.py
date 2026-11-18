import bpy, bmesh, math, random
from mathutils import Vector

# ============================================================
# 张家古楼 · 二层（密洛陀 / 铁人俑）
#   原著：穿过放置铁人俑的架子，以中心呈放射状排列，完整伏羲六十四卦
#   同样四根巨大柱子；层高 9 m
# ============================================================
random.seed(11)
PLAN = 30.0
WALL = 1.2
H = 9.0
COL_R = 1.3
COL_POS = 6.5
HOLE_R = 4.6

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def mat(name, rgb, rough=0.85, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*rgb, 1); return m

M_WOOD = mat("灰木", (0.30, 0.27, 0.23))
M_DARK = mat("深木", (0.12, 0.11, 0.10))
M_STONE = mat("石板", (0.11, 0.105, 0.10))
M_IRON = mat("生铁", (0.09, 0.09, 0.10), rough=0.55, metal=0.85)
M_TAB = mat("木牌", (0.42, 0.33, 0.22))
M_HUMAN = mat("人", (0.75, 0.18, 0.12))

coll = bpy.context.scene.collection

def box(bm, cx, cy, cz, sx, sy, sz):
    pts = []
    for dx in (-.5,.5):
        for dy in (-.5,.5):
            for dz in (-.5,.5):
                pts.append(bm.verts.new((cx+dx*sx, cy+dy*sy, cz+dz*sz)))
    for f in [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]:
        try: bm.faces.new([pts[i] for i in f])
        except ValueError: pass

def cyl(bm, p0, p1, r0, r1, segs=24):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1-p0; dirn = d.normalized(); up = Vector((0,0,1))
    if abs(dirn.dot(up)) > 0.95: up = Vector((1,0,0))
    a = dirn.cross(up).normalized(); b = dirn.cross(a).normalized()
    ra, rb = [], []
    for k in range(segs):
        ang = 2*math.pi*k/segs
        off = a*math.cos(ang)+b*math.sin(ang)
        ra.append(bm.verts.new(p0+off*r0)); rb.append(bm.verts.new(p1+off*r1))
    for k in range(segs):
        k2 = (k+1) % segs
        try: bm.faces.new([ra[k], ra[k2], rb[k2], rb[k]])
        except ValueError: pass

def bake(bm, name, m):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.validate()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m)
    coll.objects.link(ob); return ob

half = PLAN/2; w2 = half + WALL

# 地面（中间有锈穿窟窿）
bm = bmesh.new()
N = 40
inner, outer = [], []
for k in range(N):
    a = 2*math.pi*k/N
    rr = HOLE_R*(1.0 + 0.28*math.sin(3*a+1.1) + 0.16*math.sin(7*a+0.4))
    inner.append((rr*math.cos(a), rr*math.sin(a)))
    c, s = math.cos(a), math.sin(a); m = max(abs(c), abs(s))
    outer.append((w2*c/m, w2*s/m))
vi = [bm.verts.new((x, y, 0)) for x, y in inner]
vo = [bm.verts.new((x, y, 0)) for x, y in outer]
for k in range(N):
    j = (k+1) % N
    bm.faces.new([vi[k], vo[k], vo[j], vi[j]])
bake(bm, "地面", M_STONE)

# 墙 + 方格窗
bm = bmesh.new()
WIN_W, WIN_H, SILL = 2.2, 2.6, 3.4
for side in range(4):
    ang = side*math.pi/2; nx, ny = math.sin(ang), -math.cos(ang)
    for s in (-1, 1):
        t0, t1 = s*WIN_W/2, s*half
        c = (t0+t1)/2; ln = abs(t1-t0)
        if side % 2 == 0: box(bm, c, ny*w2, H/2, ln, WALL, H)
        else:             box(bm, nx*w2, c, H/2, WALL, ln, H)
    top = H-(SILL+WIN_H)
    if top > 0.01:
        zc = SILL+WIN_H+top/2
        if side % 2 == 0: box(bm, 0, ny*w2, zc, WIN_W, WALL, top)
        else:             box(bm, nx*w2, 0, zc, WALL, WIN_W, top)
    zc = SILL/2
    if side % 2 == 0: box(bm, 0, ny*w2, zc, WIN_W, WALL, SILL)
    else:             box(bm, nx*w2, 0, zc, WALL, WIN_W, SILL)
bake(bm, "墙体", M_WOOD)

bm = bmesh.new()
for side in range(4):
    ang = side*math.pi/2; nx, ny = math.sin(ang), -math.cos(ang)
    cz = SILL+WIN_H/2
    if side % 2 == 0: box(bm, 0, ny*(w2-0.2), cz, WIN_W, 0.12, WIN_H)
    else:             box(bm, nx*(w2-0.2), 0, cz, 0.12, WIN_W, WIN_H)
    for k in range(4):
        off = -WIN_W/2+(k+0.5)*WIN_W/4
        if side % 2 == 0: box(bm, off, ny*(w2-0.28), cz, 0.07, 0.1, WIN_H)
        else:             box(bm, nx*(w2-0.28), off, cz, 0.1, 0.07, WIN_H)
bake(bm, "方格窗", M_DARK)

# 四根巨柱
bm = bmesh.new()
for sx in (-1, 1):
    for sy in (-1, 1):
        cx, cy = sx*COL_POS, sy*COL_POS
        cyl(bm, (cx,cy,0), (cx,cy,H), COL_R*1.12, COL_R, 28)
        cyl(bm, (cx,cy,0), (cx,cy,0.45), COL_R*1.45, COL_R*1.42, 28)
        for zz in (2.6, 5.2, 7.8):
            cyl(bm, (cx,cy,zz), (cx,cy,zz+0.26), COL_R*1.30, COL_R*1.28, 28)
        for k in range(12):
            a = 2*math.pi*k/12*1.6; z = 0.6+k*(H-1.4)/12
            r = COL_R+0.40
            box(bm, cx+r*math.cos(a), cy+r*math.sin(a), z, 0.62, 0.46, 0.20)
bake(bm, "四巨柱", M_DARK)

# 顶（三层楼板）
bm = bmesh.new()
vi = [bm.verts.new((x, y, H)) for x, y in inner]
vo = [bm.verts.new((x, y, H)) for x, y in outer]
vbi = [bm.verts.new((x, y, H-0.5)) for x, y in inner]
vbo = [bm.verts.new((x, y, H-0.5)) for x, y in outer]
for k in range(N):
    j = (k+1) % N
    bm.faces.new([vi[k], vo[k], vo[j], vi[j]])
    bm.faces.new([vbi[k], vbi[j], vbo[j], vbo[k]])
    bm.faces.new([vi[k], vi[j], vbi[j], vbi[k]])
bake(bm, "三层楼板", M_WOOD)

# ---------- 铁人俑架 + 铁人俑（伏羲六十四卦，8 卦 × 8 位）----------
bm = bmesh.new()
# 24 尊（8 卦 × 3 环），每尊约 2.9 m 高，才读得出来
n_rack = 0
for spoke in range(8):
    ang = 2*math.pi*spoke/8 + math.pi/8
    for ring in range(4):
        r = 5.5 + ring*2.0
        cx, cy = r*math.cos(ang), r*math.sin(ang)
        box(bm, cx, cy, 0.50, 1.45, 1.45, 1.00)          # 石座
        box(bm, cx, cy, 1.10, 1.15, 1.15, 0.24)          # 座顶线脚
        box(bm, cx, cy, 1.55, 0.70, 0.55, 0.70)          # 腿
        box(bm, cx, cy, 2.55, 0.92, 0.66, 1.40)          # 躯干
        box(bm, cx, cy, 3.30, 1.16, 0.50, 0.34)          # 肩甲（横向张开）
        box(bm, cx, cy, 3.62, 0.56, 0.52, 0.34)          # 颈
        box(bm, cx, cy, 3.94, 0.62, 0.60, 0.44)          # 头盔
        box(bm, cx, cy+0.34, 2.55, 0.30, 0.22, 1.10)     # 前持物
        n_rack += 1
bake(bm, "铁人俑", M_IRON)
print("RACKS", n_rack)

# 卦象木牌（挂在柱上，增加肃穆）
bm = bmesh.new()
for sx in (-1, 1):
    for sy in (-1, 1):
        box(bm, sx*COL_POS, sy*COL_POS-COL_R-0.06, 3.2, 0.7, 0.06, 1.6)
bake(bm, "卦牌", M_TAB)

# 1.7 m 人形参照
bm = bmesh.new()
box(bm, 0, -6.5, 0.85, 0.45, 0.30, 1.70)
bake(bm, "人形参照", M_HUMAN)

print("BUILT", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath="/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floor2-rebuild.blend")
print("SAVED")
