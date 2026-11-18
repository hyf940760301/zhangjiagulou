import bpy, bmesh, math, random
from mathutils import Vector

# ============================================================
# 张家古楼 · 五层（夹层）
#   原著：非常非常小的夹层，一米二三的层高；有些已经腐了的字画；
#         一间房有暗门；空气里有毒
#   这一层必须趴着看 —— 机位放到 0.65 m
# ============================================================
random.seed(23)
PLAN, WALL = 30.0, 1.2
H = 1.28                    # 净高
HATCH = 1.5                 # 地面检修口（光从下面来）

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def mat(name, rgb, rough=0.9, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*rgb, 1); return m

M_WOOD  = mat("灰木", (0.24, 0.21, 0.18))
M_DARK  = mat("深木", (0.09, 0.085, 0.08))
M_PAPER = mat("腐纸", (0.30, 0.25, 0.17))
M_PAPER2= mat("旧绢", (0.26, 0.22, 0.18))
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

def tube(bm, p0, p1, r, segs=12, axisdir=None):
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1-p0).normalized(); up = Vector((0,0,1))
    if abs(d.dot(up)) > 0.95: up = Vector((1,0,0))
    a = d.cross(up).normalized(); b = d.cross(a).normalized()
    r0, r1 = [], []
    for k in range(segs):
        t = 2*math.pi*k/segs
        off = a*math.cos(t)*r + b*math.sin(t)*r
        r0.append(bm.verts.new(p0+off)); r1.append(bm.verts.new(p1+off))
    for k in range(segs):
        k2 = (k+1) % segs
        try: bm.faces.new([r0[k], r0[k2], r1[k2], r1[k]])
        except ValueError: pass

def bake(bm, name, m):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.validate()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m)
    coll.objects.link(ob); return ob

half = PLAN/2; w2 = half + WALL

# 地面（中间一个检修口，光从下面来）
bm = bmesh.new()
N = 32
holes = [(0, -8)]
inner, outer = [], []
for k in range(N):
    a = 2*math.pi*k/N
    hx, hy = holes[0]
    rr = HATCH/2
    inner.append((hx+rr*math.cos(a), hy+rr*math.sin(a)))
    c, s = math.cos(a), math.sin(a); mm = max(abs(c), abs(s))
    outer.append((w2*c/mm, w2*s/mm))
vi = [bm.verts.new((x, y, 0)) for x, y in inner]
vo = [bm.verts.new((x, y, 0)) for x, y in outer]
for k in range(N):
    j = (k+1) % N
    bm.faces.new([vi[k], vo[k], vo[j], vi[j]])
bake(bm, "地面", M_WOOD)

# 四周矮墙
bm = bmesh.new()
for side in range(4):
    ang = side*math.pi/2; nx, ny = math.sin(ang), -math.cos(ang)
    if side % 2 == 0: add_box(bm, 0, ny*(w2-WALL/2), H/2, w2*2, WALL, H)
    else:             add_box(bm, nx*(w2-WALL/2), 0, H/2, WALL, w2*2, H)
bake(bm, "矮墙", M_WOOD)

# 顶（六层楼板）+ 密排搁栅
bm = bmesh.new()
add_box(bm, 0, 0, H+0.12, w2*2, w2*2, 0.24)
for k in range(-6, 7):
    add_box(bm, k*2.2, 0, H-0.09, 0.22, w2*2, 0.18)
    add_box(bm, 0, k*2.2, H-0.09, w2*2, 0.22, 0.18)
bake(bm, "顶棚与搁栅", M_DARK)

# ---------- 腐字画：卷轴 + 摊开的绢 ----------
bm = bmesh.new()
for k in range(90):
    x = random.uniform(-13, 13); y = random.uniform(-13, 13)
    if (x-0)**2 + (y+8)**2 < 2.4: continue
    if k % 3 == 0:
        # 摊开的一卷
        w = random.uniform(0.5, 1.1); d2 = random.uniform(0.35, 0.8)
        add_box(bm, x, y, 0.012, w, d2, 0.024)
    else:
        # 卷起来的轴
        ln = random.uniform(0.35, 0.95); r = random.uniform(0.035, 0.075)
        a = random.uniform(0, math.pi)
        ca, sa = math.cos(a), math.sin(a)
        p0 = (x - ca*ln/2, y - sa*ln/2, r)
        p1 = (x + ca*ln/2, y + sa*ln/2, r)
        tube(bm, p0, p1, r)
bake(bm, "腐字画", M_PAPER)

# 几只旧木箱
bm = bmesh.new()
for (x, y, s) in [(-9.5, 6.0, 1.1), (8.5, -10.5, 0.95), (11.0, 9.5, 1.2), (-11.5, -11.5, 0.9)]:
    add_box(bm, x, y, 0.32, s, s*0.8, 0.64)
bake(bm, "木箱", M_DARK)

# 人形参照（趴着，示意）
bm = bmesh.new(); add_box(bm, 4.0, -12.6, 0.22, 1.60, 0.45, 0.42)
bake(bm, "人形参照", M_HUMAN)

print("BUILT", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath="/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floor5-rebuild.blend")
print("SAVED")
