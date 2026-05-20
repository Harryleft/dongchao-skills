# feishu-cron LLM Eval Cases

## Case 1: Create daily reminder
- **Input:** "每天早上9点提醒我喝水"
- **Expected:**
  - schedule: `{kind: "cron", expr: "0 9 * * *", tz: "Asia/Shanghai"}`
  - sessionTarget: "current"
  - delivery.mode: "none"
  - payload: direct Chinese text, no tool call

## Case 2: Create weekday reminder
- **Input:** "工作日每天下午2点提醒我写周报"
- **Expected:**
  - expr: "0 14 * * 1-5"
  - tz: "Asia/Shanghai"
  - delivery.mode: "none"

## Case 3: Troubleshoot "Outbound not configured" error
- **Input:** User reports cron error: `Outbound not configured for channel: feishu`
- **Expected:**
  - Identify: delivery.mode is "announce" or default
  - Fix: change to delivery.mode: "none"
  - Verify with `cron run`

## Case 4: Cron expression translation
- **Input:** "每个周一早上10点"
- **Expected:** expr: "0 10 * * 1"

## Case 5: Reject announce mode
- **Input:** User tries to create cron with delivery.mode: "announce"
- **Expected:** Agent warns that announce doesn't work in feishu, suggests mode: "none"
