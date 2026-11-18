import bpy, bmesh, math
from mathutils import Vector, Matrix

# ============================================================
# 张家古楼 · 三层（人面龟）
#   原著：正中央一只人面龟雕像，脖子和四肢都非常长，人面龟身，
#         前肢末端是人的手，后肢是乌龟的脚，脸是一张女性的脸，
#         阴毒凶狠，似笑非笑。龟背上有个凹陷，里面一个黑球。
# ============================================================
PLAN, WALL, H = 30.0, 1.2, 8.0
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

M_WOOD  = mat("灰木", (0.30, 0.27, 0.23))
M_DARK  = mat("深木", (0.12, 0.11, 0.10))
M_STONE = mat("石板", (0.11, 0.105, 0.10))
M_STAT  = mat("石雕", (0.26, 0.24, 0.21), rough=0.95)
M_BLACK = mat("黑球", (0.03, 0.03, 0.035), rough=0.35)
M_HUMAN = mat("人", (0.75, 0.18, 0.12))
coll = bpy.context.scene.collection

def add_box(bm, cx, cy, cz, sx, sy, sz, ang=0.0):
    ca, sa = math.cos(ang), math.sin(ang)
    cs = []
    for dx in (-.5,.5):
        for dy in (-.5,.5):
            for dz in (-.5,.5):
                lx, ly = dx*sx, dy*sy
                cs.append(bm.verts.new((cx+lx*ca-ly*sa, cy+lx*sa+ly*ca, cz+dz*sz)))
    for f in [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]:
        try: bm.faces.new([cs[i] for i in f])
        except ValueError: pass

def add_ellipsoid(bm, c, r, segs=24, rings=12, squash=(1,1,1)):
    ret = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    for v in ret["verts"]:
        v.co.x = v.co.x*r[0]*squash[0] + c[0]
        v.co.y = v.co.y*r[1]*squash[1] + c[1]
        v.co.z = v.co.z*r[2]*squash[2] + c[2]

def tube(bm, pts, radii, segs=14):
    """沿折线放样"""
    pts = [Vector(p) for p in pts]
    rings = []
    for i, p in enumerate(pts):
        if i == 0:          d = (pts[1]-pts[0])
        elif i == len(pts)-1: d = (pts[-1]-pts[-2])
        else:               d = (pts[i+1]-pts[i-1])
        d = d.normalized()
        up = Vector((0,0,1))
        if abs(d.dot(up)) > 0.95: up = Vector((1,0,0))
        a = d.cross(up).normalized(); b = d.cross(a).normalized()
        rr = radii[i]
        ring = []
        for k in range(segs):
            t = 2*math.pi*k/segs
            off = a*math.cos(t)*rr + b*math.sin(t)*rr
            ring.append(bm.verts.new(p+off))
        rings.append(ring)
    for i in range(len(rings)-1):
        for k in range(segs):
            k2 = (k+1) % segs
            try: bm.faces.new([rings[i][k], rings[i][k2], rings[i+1][k2], rings[i+1][k]])
            except ValueError: pass

def bake(bm, name, m):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.validate()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m)
    coll.objects.link(ob); return ob

half = PLAN/2; w2 = half + WALL

# 地面 / 墙 / 窗
bm = bmesh.new(); add_box(bm, 0, 0, -0.25, w2*2, w2*2, 0.5); bake(bm, "地面", M_STONE)
bm = bmesh.new()
WW, WH, SILL = 2.2, 2.6, 3.0
for side in range(4):
    ang = side*math.pi/2; nx, ny = math.sin(ang), -math.cos(ang)
    for s in (-1,1):
        t0, t1 = s*WW/2, s*half; c = (t0+t1)/2; ln = abs(t1-t0)
        if side%2==0: add_box(bm, c, ny*w2, H/2, ln, WALL, H)
        else:         add_box(bm, nx*w2, c, H/2, WALL, ln, H)
    top = H-(SILL+WH)
    if top > 0.01:
        zc = SILL+WH+top/2
        if side%2==0: add_box(bm, 0, ny*w2, zc, WW, WALL, top)
        else:         add_box(bm, nx*w2, 0, zc, WALL, WW, top)
    zc = SILL/2
    if side%2==0: add_box(bm, 0, ny*w2, zc, WW, WALL, SILL)
    else:         add_box(bm, nx*w2, 0, zc, WALL, WW, SILL)
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
        tube(bm, [(cx,cy,0),(cx,cy,H)], [COL_R*1.10, COL_R])
        tube(bm, [(cx,cy,0),(cx,cy,0.45)], [COL_R*1.45, COL_R*1.42])
        for zz in (2.6, 5.0):
            tube(bm, [(cx,cy,zz),(cx,cy,zz+0.26)], [COL_R*1.30, COL_R*1.28])
bake(bm, "四巨柱", M_DARK)

# 顶
bm = bmesh.new(); add_box(bm, 0, 0, H+0.25, w2*2, w2*2, 0.5); bake(bm, "四层楼板", M_WOOD)

# ================= 人面龟 =================
bm = bmesh.new()
add_box(bm, 0, 0, 0.30, 9.0, 12.0, 0.60)                  # 台座
add_ellipsoid(bm, (0, 0, 1.90), (3.3, 4.4, 1.35))          # 龟身
add_ellipsoid(bm, (0, 0, 2.55), (2.6, 3.6, 0.55))          # 背甲隆起
add_ellipsoid(bm, (0, 0, 3.00), (1.35, 1.55, 0.55))        # 背部凹陷外圈
# 龟甲分块（环形凸起，让 Chisel 读到"甲片"）
for k in range(10):
    a = 2*math.pi*k/10
    add_box(bm, 2.2*math.cos(a), 2.9*math.sin(a), 2.95, 0.9, 0.9, 0.22)
# 长颈：自龟身前端升起，向前拱出，脸朝门口（-Y）
neck = [(0, -2.9, 2.30), (0, -3.3, 3.40), (0, -3.8, 4.05), (0, -4.3, 4.15)]
tube(bm, neck, [0.60, 0.52, 0.46, 0.42])
# 头：女性脸，正面朝 -Y，略下俯
add_ellipsoid(bm, (0, -4.72, 4.02), (0.54, 0.46, 0.60))
add_ellipsoid(bm, (0, -5.08, 3.96), (0.32, 0.28, 0.36))     # 面部前突
add_ellipsoid(bm, (0, -4.45, 4.42), (0.48, 0.42, 0.32))     # 发髻
add_box(bm, 0, -5.18, 4.14, 0.54, 0.10, 0.08)              # 眉脊
add_box(bm, 0, -5.20, 3.80, 0.28, 0.08, 0.06)              # 口
# 前肢：长，末端人手
for sy in (-1, 1):
    limb = [(-1.8, sy*2.6, 1.6), (-2.6, sy*3.1, 1.9), (-3.3, sy*3.0, 1.2), (-3.7, sy*2.7, 0.7)]
    tube(bm, limb, [0.46, 0.38, 0.30, 0.26])
    add_box(bm, -3.95, sy*2.65, 0.62, 0.62, 0.34, 0.30)     # 手掌
    for f in range(4):                                       # 手指
        add_box(bm, -4.30, sy*2.65 + (f-1.5)*0.14, 0.55, 0.42, 0.09, 0.12)
# 后肢：乌龟的脚
for sy in (-1, 1):
    limb = [(1.9, sy*2.4, 1.5), (2.7, sy*2.9, 1.0), (3.3, sy*2.8, 0.5)]
    tube(bm, limb, [0.52, 0.44, 0.36])
    add_box(bm, 3.55, sy*2.85, 0.28, 0.80, 0.46, 0.28)       # 龟足
bake(bm, "人面龟", M_STAT)

# 背上的黑球
bm = bmesh.new()
add_ellipsoid(bm, (0.0, 0.0, 3.55), (0.62, 0.62, 0.62))
bake(bm, "黑球", M_BLACK)

# 人形参照
bm = bmesh.new(); add_box(bm, 0, -8.5, 0.85, 0.45, 0.30, 1.70)
bake(bm, "人形参照", M_HUMAN)

print("BUILT", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath="/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floor3-rebuild.blend")
print("SAVED")
