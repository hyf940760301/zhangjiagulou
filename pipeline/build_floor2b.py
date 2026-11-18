import bpy, bmesh, math
from mathutils import Vector, Matrix

# ============================================================
# 张家古楼 · 二层 v2
#   32 尊铁人俑：真正的人形（头盔、肩甲、双臂、长戟、甲裙）
#   8 卦 × 4 环 放射状，面朝中心
#   层高 9 m，30×30
# ============================================================
PLAN, WALL, H = 30.0, 1.2, 9.0
COL_R, COL_POS, HOLE_R = 1.3, 6.5, 4.6

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
M_IRON  = mat("生铁", (0.07, 0.07, 0.08), rough=0.45, metal=0.9)
M_TAB   = mat("木牌", (0.42, 0.33, 0.22))
M_HUMAN = mat("人", (0.75, 0.18, 0.12))
coll = bpy.context.scene.collection

def add_box(bm, cx, cy, cz, sx, sy, sz, ang=0.0, ox=0.0, oy=0.0):
    """在 (cx,cy) 处按 ang 旋转的盒子；ox/oy 为旋转前局部位移"""
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = ox, oy
    rx, ry = px*ca - py*sa, px*sa + py*ca
    cx2, cy2 = cx + rx, cy + ry
    corners = []
    for dx in (-.5, .5):
        for dy in (-.5, .5):
            for dz in (-.5, .5):
                lx, ly = dx*sx, dy*sy
                wx = cx2 + lx*ca - ly*sa
                wy = cy2 + lx*sa + ly*ca
                corners.append(bm.verts.new((wx, wy, cz + dz*sz)))
    for f in [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]:
        try: bm.faces.new([corners[i] for i in f])
        except ValueError: pass

def cyl(bm, p0, p1, r0, r1, segs=20):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1-p0; dirn = d.normalized(); up = Vector((0,0,1))
    if abs(dirn.dot(up)) > 0.95: up = Vector((1,0,0))
    a = dirn.cross(up).normalized(); b = dirn.cross(a).normalized()
    ra, rb = [], []
    for k in range(segs):
        t = 2*math.pi*k/segs
        off = a*math.cos(t)+b*math.sin(t)
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

def warrior(bm, cx, cy, ang):
    """一尊铁人俑，高约 3.9 m，面朝中心（ang 为其自身朝向）"""
    B = lambda cz, sx, sy, sz, ox=0.0, oy=0.0: add_box(bm, cx, cy, cz, sx, sy, sz, ang, ox, oy)
    B(0.55, 1.70, 1.70, 1.10)          # 石座
    B(1.16, 1.36, 1.36, 0.16, 0, 0)    # 座顶线脚
    B(1.30, 0.92, 0.46, 0.20)          # 双脚台
    B(1.74, 0.30, 0.32, 0.92, -0.22)   # 左腿
    B(1.74, 0.30, 0.32, 0.92,  0.22)   # 右腿
    B(2.32, 1.02, 0.62, 0.52)          # 甲裙
    B(2.88, 0.86, 0.56, 0.72)          # 躯干
    B(3.28, 0.98, 0.60, 0.14)          # 胸口横带
    B(3.30, 0.44, 0.52, 0.34, -0.62)   # 左肩甲
    B(3.30, 0.44, 0.52, 0.34,  0.62)   # 右肩甲
    B(2.86, 0.24, 0.26, 1.00, -0.60)   # 左臂
    B(2.86, 0.24, 0.26, 1.00,  0.60)   # 右臂
    B(2.30, 0.26, 0.28, 0.24, -0.60)   # 左手
    B(2.30, 0.26, 0.28, 0.24,  0.60)   # 右手
    B(3.62, 0.30, 0.30, 0.20)          # 颈
    B(3.88, 0.42, 0.44, 0.42)          # 头
    B(4.12, 0.50, 0.52, 0.16)          # 盔沿
    B(4.26, 0.20, 0.34, 0.22)          # 盔顶
    # 长戟（右手外侧，竖直）
    hx, hy = 0.90, 0.10
    ca, sa = math.cos(ang), math.sin(ang)
    px = cx + hx*ca - hy*sa; py = cy + hx*sa + hy*ca
    cyl(bm, (px, py, 1.30), (px, py, 4.40), 0.045, 0.045, 10)
    B_blade = 4.30
    add_box(bm, px, py, B_blade, 0.06, 0.34, 0.40, ang)

half = PLAN/2; w2 = half + WALL

# 地面（中间锈穿窟窿）
bm = bmesh.new(); N = 40; inner, outer = [], []
for k in range(N):
    a = 2*math.pi*k/N
    rr = HOLE_R*(1.0 + 0.28*math.sin(3*a+1.1) + 0.16*math.sin(7*a+0.4))
    inner.append((rr*math.cos(a), rr*math.sin(a)))
    c, s = math.cos(a), math.sin(a); m = max(abs(c), abs(s))
    outer.append((w2*c/m, w2*s/m))
vi = [bm.verts.new((x,y,0)) for x,y in inner]
vo = [bm.verts.new((x,y,0)) for x,y in outer]
for k in range(N):
    j = (k+1) % N
    bm.faces.new([vi[k], vo[k], vo[j], vi[j]])
bake(bm, "地面", M_STONE)

# 墙 + 方格窗
bm = bmesh.new()
WW, WH, SILL = 2.2, 2.6, 3.4
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
        cyl(bm, (cx,cy,0), (cx,cy,H), COL_R*1.12, COL_R, 28)
        cyl(bm, (cx,cy,0), (cx,cy,0.45), COL_R*1.45, COL_R*1.42, 28)
        for zz in (2.6, 5.2, 7.8):
            cyl(bm, (cx,cy,zz), (cx,cy,zz+0.26), COL_R*1.30, COL_R*1.28, 28)
        for k in range(12):
            a = 2*math.pi*k/12*1.6; z = 0.6+k*(H-1.4)/12; r = COL_R+0.40
            add_box(bm, cx+r*math.cos(a), cy+r*math.sin(a), z, 0.62, 0.46, 0.20)
bake(bm, "四巨柱", M_DARK)

# 三层楼板（同窟窿）
bm = bmesh.new()
vi = [bm.verts.new((x,y,H)) for x,y in inner]
vo = [bm.verts.new((x,y,H)) for x,y in outer]
vbi = [bm.verts.new((x,y,H-0.5)) for x,y in inner]
vbo = [bm.verts.new((x,y,H-0.5)) for x,y in outer]
for k in range(N):
    j=(k+1)%N
    bm.faces.new([vi[k], vo[k], vo[j], vi[j]])
    bm.faces.new([vbi[k], vbi[j], vbo[j], vbo[k]])
    bm.faces.new([vi[k], vi[j], vbi[j], vbi[k]])
bake(bm, "三层楼板", M_WOOD)

# ---------- 32 尊铁人俑（8 卦 × 4 环，面朝中心）----------
bm = bmesh.new()
n = 0
for spoke in range(8):
    ang = 2*math.pi*spoke/8 + math.pi/8
    for ring in range(4):
        r = 5.6 + ring*2.0
        cx, cy = r*math.cos(ang), r*math.sin(ang)
        face = ang + math.pi          # 面朝中心
        warrior(bm, cx, cy, face)
        n += 1
bake(bm, "铁人俑", M_IRON)
print("WARRIORS", n)

bm = bmesh.new()
add_box(bm, 0, -6.5, 0.85, 0.45, 0.30, 1.70)
bake(bm, "人形参照", M_HUMAN)

print("BUILT", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath="/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floor2-rebuild.blend")
print("SAVED")
