#!/bin/bash
# ============================================================
# 张家古楼 · 单层流水线
#   用法: ./zjl-floor.sh 3          只跑第 3 层
#         ./zjl-floor.sh 1 2 4 5    批量
#   环境: 需要 WLT_API_KEY（source .tools/atlas-env-zjl.sh）
# ============================================================
set -u
ROOT="/Users/huyifan/Desktop/DeepSeek Harness"
BLEND="$ROOT/out/zhangjialou/zhangjialou-v15.blend"
OUT="$ROOT/out/zhangjialou/floors"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"

[ $# -eq 0 ] && { echo "用法: $0 <楼层号 1-7> [...]"; exit 1; }
[ -z "${WLT_API_KEY:-}" ] && { echo "缺少 WLT_API_KEY，先 source .tools/atlas-env-zjl.sh"; exit 1; }

for N in "$@"; do
  IDX=$((N - 1))
  # 第 3 层已有 28 帧成品（用户已验收），重跑只会得到较少的 20 帧并花钱
  if [ "$N" = "3" ] && [ -d "$ROOT/out/zhangjialou/floor3-chisel2" ]; then
    echo "第 3 层已有 28 帧成品，跳过（如需重做先移走 floor3-chisel2/）"
    continue
  fi
  D="$OUT/f$N"
  echo "============================================================"
  echo "第 $N 层  (index $IDX)"
  echo "============================================================"

  # --- 1. 深度 ---
  if [ -f "$D/cameras.json" ] && [ "$(ls "$D"/*.exr 2>/dev/null | wc -l | tr -d ' ')" -ge 20 ]; then
    echo "[1/4] 深度已存在，跳过"
  else
    echo "[1/4] 渲染深度（20 机位，约 6 分钟）…"
    rm -rf "$D"; mkdir -p "$D"
    "$BLENDER" --background --factory-startup "$BLEND" \
      --python "$ROOT/out/zhangjialou/all_floors_depth.py" -- "$IDX" 2>&1 | grep -E "^FLOOR|ALL DONE"
    [ -f "$D/cameras.json" ] || { echo "  ✗ 深度渲染失败"; continue; }
  fi

  # --- 2. 深度体检 ---
  if [ -f "$D/depth-audit.json" ]; then
    echo "[2/4] 体检已存在，跳过"
  else
    echo "[2/4] 深度体检（标记扎进物件的机位）…"
    "$BLENDER" --background --factory-startup \
      --python "$ROOT/out/zhangjialou/audit_one_floor.py" -- "$N" 2>&1 | grep -E "^f[0-9]"
  fi

  # --- 3. Chisel ---
  echo "[3/4] atlasChisel（上传深度 + 生成 + 下载）…"
  python3 "$ROOT/out/zhangjialou/chisel_all.py" "$N" || { echo "  ✗ Chisel 失败（额度？）"; continue; }

  # --- 4. 装配 ---
  echo "[4/4] 装配环视页…"
  python3 "$ROOT/out/zhangjialou/assemble_tour.py"
done

echo "============================================================"
echo "完成。查看: http://127.0.0.1:8099/zhangjialou/floor-tour/"
