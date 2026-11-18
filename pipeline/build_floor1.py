import bpy, bmesh, math, random
from mathutils import Vector

# ============================================================
# 张家古楼 · 一层重构（阴山古楼版）
#   平面 30×30，一层净高 10 m
#   四根 Ø2.6 麒麟巨柱，柱身有踏步可攀
#   中间一个边缘不规则的大窟窿（原著：被腐蚀）
#   灰白木门 + 清代方格窗，无台基
# ============================================================
random.seed(7)
PLAN = 30.0          # 内净
WALL = 1.2
H = 10.0             # 一层净高
COL_R = 1.3          # 巨柱半径
COL_POS = 6.5        # 柱心距中轴

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def mat(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1); return m

M_WOOD = mat("灰木", (0.34, 0.31, 0.27))
M_DARK = mat("深木", (0.16, 0.14, 0.12))
M_STONE = mat("石板", (0.13, 0.125, 0.115))
M_CLOTH = mat("幡布", (0.30, 0.16, 0.13))
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

def bake(bm, name, m):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.validate()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m)
    coll.objects.link(ob); return ob

half = PLAN/2          # 15
w2 = half + WALL       # 16.2 外皮

# ---------- 地面 ----------
bm = bmesh.new(); box(bm, 0, 0, -0.25, w2*2, w2*2, 0.5); bake(bm, "地面", M_STONE)

# ---------- 四面墙（正面灰白木门，其余方格窗）----------
bm = bmesh.new()
DOOR_W, DOOR_H = 3.6, 5.2
WIN_W, WIN_H = 2.0, 2.4
for side in range(4):
    ang = side*math.pi/2
    nx, ny = math.sin(ang), -math.cos(ang)
    front = (side == 0)
    ow = DOOR_W if front else WIN_W
    oh = DOOR_H if front else WIN_H
    sill = 0.0 if front else 3.2
    # 左右两段
    for s in (-1, 1):
        t0, t1 = s*ow/2, s*half
        c = (t0+t1)/2; ln = abs(t1-t0)
        if side % 2 == 0:
            box(bm, c, ny*w2, H/2, ln, WALL, H)
        else:
            box(bm, nx*w2, c, H/2, WALL, ln, H)
    # 洞上
    top = H - (sill + oh)
    if top > 0.01:
        zc = sill + oh + top/2
        if side % 2 == 0: box(bm, 0, ny*w2, zc, ow, WALL, top)
        else:             box(bm, nx*w2, 0, zc, WALL, ow, top)
    # 窗下墙
    if sill > 0.01:
        zc = sill/2
        if side % 2 == 0: box(bm, 0, ny*w2, zc, ow, WALL, sill)
        else:             box(bm, nx*w2, 0, zc, WALL, ow, sill)
bake(bm, "墙体", M_WOOD)

# 门扇（灰白、腐朽感用暗色）
bm = bmesh.new()
box(bm, 0, -(w2-0.3), DOOR_H/2, DOOR_W-0.3, 0.22, DOOR_H-0.2)
box(bm, 0, -(w2-0.18), DOOR_H/2, 0.10, 0.10, DOOR_H-0.25)   # 门缝
bake(bm, "门", M_DARK)

# 方格窗
bm = bmesh.new()
for side in range(1, 4):
    ang = side*math.pi/2; nx, ny = math.sin(ang), -math.cos(ang)
    cz = 3.2 + WIN_H/2
    if side % 2 == 0: box(bm, 0, ny*(w2-0.2), cz, WIN_W, 0.12, WIN_H)
    else:             box(bm, nx*(w2-0.2), 0, cz, 0.12, WIN_W, WIN_H)
    for k in range(4):
        off = -WIN_W/2 + (k+0.5)*WIN_W/4
        if side % 2 == 0: box(bm, off, ny*(w2-0.28), cz, 0.07, 0.1, WIN_H)
        else:             box(bm, nx*(w2-0.28), off, cz, 0.1, 0.07, WIN_H)
bake(bm, "方格窗", M_DARK)

# ---------- 四根巨柱（带箍、可攀踏步）----------
def cyl(bm, p0, p1, r0, r1, segs=24):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0; dirn = d.normalized()
    up = Vector((0,0,1))
    if abs(dirn.dot(up)) > 0.95: up = Vector((1,0,0))
    a = dirn.cross(up).normalized(); b = dirn.cross(a).normalized()
    ra, rb = [], []
    for k in range(segs):
        ang = 2*math.pi*k/segs
        off = a*math.cos(ang) + b*math.sin(ang)
        ra.append(bm.verts.new(p0 + off*r0)); rb.append(bm.verts.new(p1 + off*r1))
    for k in range(segs):
        k2 = (k+1) % segs
        try: bm.faces.new([ra[k], ra[k2], rb[k2], rb[k]])
        except ValueError: pass

bm = bmesh.new()
for sx in (-1, 1):
    for sy in (-1, 1):
        cx, cy = sx*COL_POS, sy*COL_POS
        cyl(bm, (cx,cy,0), (cx,cy,H), COL_R*1.12, COL_R, 28)   # 柱身（微收分）
        cyl(bm, (cx,cy,0), (cx,cy,0.45), COL_R*1.45, COL_R*1.42, 28)  # 柱础
        # 箍（三道）
        for zz in (2.8, 5.6, 8.4):
            cyl(bm, (cx,cy,zz), (cx,cy,zz+0.28), COL_R*1.30, COL_R*1.28, 28)
        # 螺旋踏步（原著：踩麒麟头往上爬）
        steps = 14
        for k in range(steps):
            a = 2*math.pi*k/steps*1.6
            z = 0.6 + k*(H-1.4)/steps
            r = COL_R + 0.42
            px, py = cx + r*math.cos(a), cy + r*math.sin(a)
            box(bm, px, py, z, 0.66, 0.5, 0.22)
bake(bm, "四巨柱", M_DARK)

# ---------- 顶（二层楼板，中间不规则窟窿）----------
bm = bmesh.new()
N = 40
R_IN = 4.2
cx0, cy0 = 0.0, 0.0
ring_in = []
for k in range(N):
    a = 2*math.pi*k/N
    rr = R_IN * (1.0 + 0.28*math.sin(3*a+0.7) + 0.16*math.sin(7*a+2.1))   # 边缘不规则
    ring_in.append((cx0+rr*math.cos(a), cy0+rr*math.sin(a)))
ring_out = []
for k in range(N):
    a = 2*math.pi*k/N
    ring_out.append((w2*math.cos(a)/max(abs(math.cos(a)),abs(math.sin(a))),
                     w2*math.sin(a)/max(abs(math.cos(a)),abs(math.sin(a)))))
vt_in = [bm.verts.new((x, y, H)) for x, y in ring_in]
vt_out = [bm.verts.new((x, y, H)) for x, y in ring_out]
vb_in = [bm.verts.new((x, y, H-0.5)) for x, y in ring_in]
vb_out = [bm.verts.new((x, y, H-0.5)) for x, y in ring_out]
for k in range(N):
    j = (k+1) % N
    bm.faces.new([vt_in[k], vt_out[k], vt_out[j], vt_in[j]])   # 顶面
    bm.faces.new([vb_in[k], vb_in[j], vb_out[j], vb_out[k]])   # 底面
    bm.faces.new([vt_in[k], vt_in[j], vb_in[j], vb_in[k]])     # 窟窿内壁
bake(bm, "二层楼板", M_WOOD)

# ---------- 幡、供桌（贴边，不占中心）----------
# 幡暂不放（1.3×6.2 的板会挡住机位；等机位定下来再加薄幡）
M_CLOTH = M_CLOTH

bm = bmesh.new()
box(bm, 0, 12.2, 0.55, 9.0, 1.8, 1.1)
for k in range(5):
    box(bm, -3.6 + k*1.8, 12.6, 1.5, 0.7, 0.2, 2.0)
bake(bm, "供桌牌位", M_WOOD)

# ---------- 1.7 m 人形参照 ----------
bm = bmesh.new()
box(bm, 0.0, -4.0, 0.85, 0.45, 0.30, 1.70)
ob = bake(bm, "人形参照", M_HUMAN)
ob.location = (0, 0, 0)

print("BUILT", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath="/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floor1-rebuild.blend")
print("SAVED")
