# 张家古楼 · 工作流（已跑通一层）

> 现状：**七层全部跑通**。三层 28 帧（已验收）+ 其余六层各 14–15 帧，合计 117 帧照片级图。

## 一句话

**Blender 出精确几何与深度 → Atlas 按深度长出照片级材质 → 环视页**。

几何的可信度来自 Blender，质感来自 Atlas。两者不抢活。

---

## 四步

```
① 深度      all_floors_depth.py   20 台相机，射线求交，渲 1280×720 EXR（约 6 分钟/层）
② 体检      audit_one_floor.py    标记"扎进物件"的机位（median < 1.2 m）
③ 生成      chisel_all.py         上传深度 → atlasChisel（一次请求 20 机位，约 60 秒）
④ 装配      assemble_tour.py      图 + 相机位姿 → floor-tour 页面
```

### 一条命令

```bash
source .tools/atlas-env-zjl.sh
out/zhangjialou/zjl-floor.sh 3            # 单层
out/zhangjialou/zjl-floor.sh 1 2 4 5 6 7  # 批量
```

脚本是**幂等**的：深度已存在就跳过，体检已存在就跳过，Chisel 结果已存在就跳过。
中断后重跑不会重复花钱。

---

## 交付物

| 项 | 路径 |
|---|---|
| **七层环视页（主交付）** | `web/zhangjialou/floor-tour/` → `http://127.0.0.1:8099/zhangjialou/floor-tour/` |
| 各层图 | `out/zhangjialou/floors/f1..f7/views/`（三层在 `floor3-chisel2/`） |
| 单层图（第 3 层，28 帧） | `out/zhangjialou/floor3-chisel2/` |
| 七层深度（140 帧） | `out/zhangjialou/floors/f1..f7/` |
| 七层几何 | `out/zhangjialou/zhangjialou-v15.blend` |

页面功能：楼层按钮切换、左右键换机位、上下键换楼层、右上角平面图显示机位与朝向。

---

## 每层机位必须避让的东西（踩过的坑）

| 层 | 撞到什么 | 处理 |
|---|---|---|
| 4 玄龟 | 龟壳半径正好 4 m，A 环整圈贴壳 | 半径 6.2 + 转角 22.5° |
| 5 族长棺 | 棺床占满中轴 | A 环抬高 1.5 m |
| 6 藏宝 | 箱高 1.55 m 且铺满 | 半径 5.4 + 抬高 1.5 m |
| 7 玉棺 | 天井角柱 (3,3)、中柱 (4.2,4.2) | 半径 5.0 + 转角 22.5° |

**这些只有渲出深度才能发现** —— 深度图是"相机有没有扎进墙里"的唯一证据。

---

## 三个必须记住的 bug

### 1. EXR 写不进去（曾导致两次全盘失败）
```python
img.pixels = numpy_array          # ✗ 静默失效，文件全是 0
img.pixels.foreach_set(arr.ravel())  # ✓
```

### 2. depsgraph 会失效
新增相机会让 `bpy.context.evaluated_depsgraph_get()` 拿到的那份失效，
`ray_cast` 全部 miss → 深度全 0。**必须每次在函数内重新取。**

### 3. 管道会杀死长任务
```bash
python chisel_all.py 1 2 | head -20   # ✗ SIGPIPE，Chisel 根本没跑
python chisel_all.py 1 2 > log 2>&1   # ✓
```

---

## 成本（待精确）

| 项 | 分 |
|---|---|
| 深度渲染（140 帧） | **0**（本地） |
| Chisel 20 帧/层 | **待测** —— 需充一次小额实测 |
| 泼溅（可选） | 5,000（**不建议**：源图近黑白，泼溅也是灰的） |

**结论：这条交付不用泼溅。** 三层那 5,000 分换来的 SPZ 是灰的、颗粒粗，不如 28 张图有用。

---

## 15 核心机位（省一半钱）

深度渲 20 个机位，但**只提交 15 个**：

```
B0–B7（半径 8，看整层）  8
A0 A2 A4 A6（近景正向）   4
U0 U1 U2（仰视天窗）      3
```

第一帧永远是 B 环（最能看整层的机位）。

### 装配时的两个坑
1. **机位名必须与请求顺序一致** —— 按字母排序会张冠李戴，地图上的点也会错位
2. 请求里不带名字 → **用位姿反查**（位置距离 < 0.01 视为同一机位）

## 下一步

```bash
# 充好额度后
out/zhangjialou/zjl-floor.sh 1 2 4 5 6 7
```

跑完就是**七层 × 20 张照片级图 + 完整七层环视页**。
