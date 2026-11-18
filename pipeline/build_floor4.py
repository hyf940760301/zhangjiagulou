import bpy, bmesh, math
from mathutils import Vector

# ============================================================
# 张家古楼 · 四层（千棺）
#   原著：一间间小房，每间两三平米，一间一口黑木大棺，
#         墙上挂满写满小楷的木牌（墓志铭），门关着、窗糊黑纸
#   为与塔身一致，仍取 30×30，用格网切出小间
# ============================================================
PLAN, WALL, H = 30.0, 1.2, 4.2
PITCH = 2.75          # 格间距
CELL = 1.85           # 净间宽
PART = PITCH - CELL   # 隔墙厚
CORR = 4              # 每 4 格一条走道

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
M_DARK  = mat("深木", (0.10, 0.09, 0.08))
M_STONE = mat("石板", (0.11, 0.105, 0.10))
M_COF   = mat("棺木", (0.055, 0.045, 0.04), rough=0.6)
M_TAB   = mat("木牌", (0.40, 0.31, 0.20))
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

def bake(bm, name, m):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.validate()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m)
    coll.objects.link(ob); return ob

half = PLAN/2; w2 = half + WALL

# 地面 / 外墙 / 顶
bm = bmesh.new(); add_box(bm, 0, 0, -0.25, w2*2, w2*2, 0.5); bake(bm, "地面", M_STONE)
bm = bmesh.new()
WW, WH, SILL = 1.6, 1.4, 2.2
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
bake(bm, "外墙", M_WOOD)

# 窗（糊黑纸 → 深色板）
bm = bmesh.new()
for side in range(4):
    ang = side*math.pi/2; nx, ny = math.sin(ang), -math.cos(ang)
    cz = SILL+WH/2
    if side%2==0: add_box(bm, 0, ny*(w2-0.15), cz, WW, 0.10, WH)
    else:         add_box(bm, nx*(w2-0.15), 0, cz, 0.10, WW, WH)
bake(bm, "糊纸窗", M_DARK)

# ---------- 格网：隔墙 + 棺 + 木牌 ----------
N = 9                       # 每边 9 格 → 81 间
span = (N-1)*PITCH          # 22.0
x0 = -span/2

bm_wall = bmesh.new()
bm_cof  = bmesh.new()
bm_tab  = bmesh.new()
rooms = 0
for i in range(N):
    for j in range(N):
        cx = x0 + i*PITCH
        cy = x0 + j*PITCH
        is_corr = (i % CORR == 0) or (j % CORR == 0)
        if is_corr:
            continue
        rooms += 1
        # 四壁（只在非走道侧立墙）
        if (i+1) % CORR != 0 and i+1 < N:
            add_box(bm_wall, cx+PITCH/2, cy, H/2, PART, PITCH, H)
        if (j+1) % CORR != 0 and j+1 < N:
            add_box(bm_wall, cx, cy+PITCH/2, H/2, PITCH, PART, H)
        # 黑木大棺
        add_box(bm_cof, cx, cy, 0.42, CELL-0.35, 0.86, 0.72)
        add_box(bm_cof, cx, cy, 0.86, CELL-0.45, 0.76, 0.16)
        # 墓志铭木牌（靠墙）
        add_box(bm_tab, cx, cy-CELL/2+0.10, 1.55, CELL-0.5, 0.06, 0.68)
bake(bm_wall, "隔墙", M_WOOD)
bake(bm_cof, "棺", M_COF)
bake(bm_tab, "墓志铭", M_TAB)
print("ROOMS", rooms)

# 顶
bm = bmesh.new(); add_box(bm, 0, 0, H+0.25, w2*2, w2*2, 0.5); bake(bm, "五层楼板", M_WOOD)

# 人形参照
bm = bmesh.new(); add_box(bm, 3.4, -13.5, 0.85, 0.45, 0.30, 1.70)
bake(bm, "人形参照", M_HUMAN)

print("BUILT", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath="/Users/huyifan/Desktop/DeepSeek Harness/out/zhangjialou/floor4-rebuild.blend")
print("SAVED")
