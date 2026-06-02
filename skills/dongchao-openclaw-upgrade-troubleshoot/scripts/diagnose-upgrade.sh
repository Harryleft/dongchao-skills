#!/usr/bin/env bash
# OpenClaw 升级后快速诊断脚本
# 用法: sh scripts/diagnose-upgrade.sh

set -e

echo "=== OpenClaw 升级后诊断 ==="
echo ""

echo "[1] CLI 版本:"
openclaw --version 2>/dev/null || echo "  openclaw 未安装或不可用"
echo ""

echo "[2] Gateway 进程:"
PIDS=$(pgrep -af "openclaw" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "$PIDS"
else
    echo "  无 openclaw 进程运行"
fi
echo ""

echo "[3] 端口 18789 占用:"
PORT_PID=$(lsof -iTCP:18789 -sTCP:LISTEN -t 2>/dev/null || true)
if [ -n "$PORT_PID" ]; then
    echo "  被 PID $PORT_PID 占用"
else
    echo "  端口空闲"
fi
echo ""

echo "[4] Gateway 状态:"
GW_STATUS=$(openclaw gateway status --json 2>/dev/null || echo "{}")
CLI_VER=$(echo "$GW_STATUS" | grep -o '"version": "[^"]*"' | head -1 || echo "N/A")
GW_VER=$(echo "$GW_STATUS" | grep -o '"version": "[^"]*"' | tail -1 || echo "N/A")
RPC_OK=$(echo "$GW_STATUS" | grep '"ok":' | head -1 || echo "N/A")
echo "  CLI: $CLI_VER"
echo "  Gateway: $GW_VER"
echo "  RPC: $RPC_OK"
echo ""

echo "[5] 日志中 protocol mismatch 数量:"
MISMATCH_COUNT=$(grep -c "protocol mismatch" /tmp/openclaw-gateway.log 2>/dev/null || echo "0")
echo "  $MISMATCH_COUNT 条"
echo ""

echo "[6] Channel 状态:"
openclaw channels status --probe 2>/dev/null | grep -E "Feishu|Gateway" || echo "  Gateway 不可达"
echo ""

echo "=== 诊断完成 ==="
echo ""

# 版本一致性检查
if [ "$CLI_VER" != "$GW_VER" ] && [ "$GW_VER" != "N/A" ]; then
    echo "⚠️  警告: CLI 和 Gateway 版本不一致!"
    echo "   请执行: kill -9 <旧PID> && sh scripts/start.sh"
else
    echo "✅ 版本一致，服务正常"
fi
