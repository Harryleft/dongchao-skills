---
name: openclaw-upgrade-troubleshoot
description: "Use when OpenClaw upgrade/update causes gateway connection failure, protocol mismatch, pairing code prompt, or version mismatch between CLI and Gateway process. 触发词：升级后连不上, gateway closed 1006, protocol mismatch, 升级后飞书无法使用, pairing code, 版本不匹配, upgrade broken, gateway 1006, openclaw 升级, 更新后故障"
---

# OpenClaw 升级故障排查

OpenClaw 核心升级后常见的两类故障及修复策略。

---

## 问题 1：Gateway 版本不匹配 (gateway closed 1006)

### 症状

- 飞书/Web 连接断开，报错 `gateway closed (1006)`
- 日志大量 `protocol mismatch`：`client=openclaw-control-ui ui v1.0.0 min=3 max=3 expected=4`
- `openclaw gateway status --json` 中 `server.version: null` 或 `rpc.ok: false`
- CLI 版本与 Gateway 进程版本不一致

### 根因

旧 Gateway 进程以 `openclaw`（无参数）方式启动，`restart.sh` 中的 `pgrep -f "openclaw-gateway|openclaw gateway"` **无法匹配到无参数的主进程**，导致旧进程未被杀死。新 Gateway 启动时端口被旧进程占用，实际运行的仍是旧版本。

```
restart.sh kill 逻辑:
  pgrep -f "openclaw-gateway|openclaw gateway"
  ↑ 匹配带参数的子进程
  ✗ 不匹配 "openclaw" 无参数主进程 ← 旧进程存活
```

### 修复步骤

```
升级后 Gateway 异常？
├─ 1. 确认旧进程
│   pgrep -af "openclaw"
│   → 记录 PID（如 224420 openclaw）
│
├─ 2. 杀死旧进程（不要用 restart.sh）
│   kill -9 <OLD_PID>
│   sleep 2
│   lsof -iTCP:18789 -sTCP:LISTEN -t || echo "port free"
│
├─ 3. 启动新 Gateway
│   sh scripts/start.sh
│   （或 nohup openclaw gateway run --port 18789 > /tmp/openclaw-gateway.log 2>&1 &）
│
├─ 4. 等待冷启动
│   sleep 15
│
└─ 5. 验证
    openclaw gateway status --json | grep '"version"'
    → 应显示 CLI 和 Gateway 版本一致（如 2026.5.18）
    openclaw health
    openclaw channels status --probe
```

### 验证标准

| 检查项 | 期望结果 |
|--------|----------|
| `openclaw gateway status --json` | `rpc.ok: true`, `server.version` 与 CLI 一致 |
| `openclaw health` | Gateway 状态正常 |
| `openclaw channels status --probe` | Feishu: enabled, configured, running, works |
| `/tmp/openclaw-gateway.log` | 无 `protocol mismatch`，有 `ready (N plugins, Xs)` |

---

## 问题 2：升级后飞书出现 Pairing Code

### 症状

飞书对话中提示：
```
OpenClaw: access not configured.
ou_xxxxxxxxxxxxxxxx
Pairing code: XXXXXX
Ask the bot owner to approve with:
openclaw pairing approve feishu XXXXXX
```

### 根因

OpenClaw 升级后 **pairing 状态被重置**，即使该用户已在 `channels.feishu.allowFrom` 白名单中，也需要重新完成配对授权。

### 修复步骤

```bash
# 1. 批准配对码（从用户提示中获取 code）
openclaw pairing approve feishu <PAIRING_CODE>

# 2. 确认用户已在白名单
openclaw config get channels.feishu.allowFrom

# 3. 如果不在，添加用户
openclaw config set channels.feishu.allowFrom '["ou_xxx"]'
```

> **注意**：`openclaw pairing approve` 不接受 `--yes` 参数，直接运行即可。

---

## 标准升级流程（预防）

每次升级 OpenClaw 时，按以下顺序执行，可避免上述问题：

```bash
# 1. 升级核心
openclaw update --yes

# 2. 升级飞书插件（必须同步升级）
npx -y @larksuite/openclaw-lark@latest install --use-existing

# 3. 彻底停止旧进程
OLD_PID=$(pgrep -f "^openclaw$" | head -1)
if [ -n "$OLD_PID" ]; then
    kill -9 $OLD_PID
    sleep 2
fi

# 4. 启动新版本
sh scripts/start.sh

# 5. 等待冷启动
sleep 15

# 6. 验证
openclaw gateway status --json | grep '"version"'
openclaw health
openclaw channels status --probe
```

---

## 快速诊断脚本

```bash
#!/usr/bin/env bash
# 用法: sh scripts/diagnose-upgrade.sh
echo "=== OpenClaw 升级后诊断 ==="
echo ""
echo "[1] CLI 版本:"
openclaw --version
echo ""
echo "[2] Gateway 进程:"
pgrep -af "openclaw" || echo "  无 openclaw 进程"
echo ""
echo "[3] 端口占用:"
lsof -iTCP:18789 -sTCP:LISTEN -t 2>/dev/null || echo "  端口 18789 空闲"
echo ""
echo "[4] Gateway 状态:"
openclaw gateway status --json 2>/dev/null | grep -E '"version"|"ok"|"error"' || echo "  Gateway 不可达"
echo ""
echo "[5] 最近日志 (protocol mismatch):"
grep -c "protocol mismatch" /tmp/openclaw-gateway.log 2>/dev/null || echo "  0 条"
echo ""
echo "[6] Channel 状态:"
openclaw channels status --probe 2>/dev/null | grep -E "Feishu|Gateway" || echo "  不可达"
```
