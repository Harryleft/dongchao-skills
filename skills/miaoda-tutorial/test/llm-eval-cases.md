# miaoda-tutorial LLM Eval Cases

## Case 1: FDE 落地指南 — 多维表格客户
- **Input:** "帮我做一个制造业客户的多维表格落地指南，客户是500人汽车零部件厂，要用多维表格管理质量检测流程"
- **Expected:**
  - Step 0 识别为「落地指南」类型
  - Brief 包含 product=飞书多维表格, industry=制造业, tutorial_type=落地指南
  - 大纲至少 6 章，含环境准备、核心场景、排障
  - 操作步骤有具体菜单位径（如"多维表格 → 添加字段 → 类型选单选"）
  - 每章有行动项
  - 输出为飞书云文档

## Case 2: 快速上手 — aily 演示
- **Input:** "给我一个5分钟能演示完的aily快速上手"
- **Expected:**
  - 识别为「快速上手」类型，3-4章
  - 时间预算 15-30 min
  - 极简：一分钟理解 → 三步完成 → 进阶技巧
  - 不需要排障章节

## Case 3: 培训手册 — FDE 新人
- **Input:** "生成一份FDE新人培训手册，教他们怎么用多维表格做客户交付"
- **Expected:**
  - 受众=FDE新人，不是客户
  - 包含内部工具使用（gbrain、feishu_search_doc_wiki）
  - 4-6章结构
  - 含常见错误和自助排障

## Case 4: 资料不足场景
- **Input:** "帮我做一个零售行业的妙搭教程"（无参考资料）
- **Expected:**
  - 识别为 thin packet
  - 自动启动研究流程：gbrain搜索零售案例 → 飞书文档搜妙搭 → web_search补
  - 每章标注「待验证」

## Case 5: 修订循环
- **Input:** 用户收到教程后反馈"第3章的操作路径不对，现在菜单已经改了"
- **Expected:**
  - 识别为「事实错误」类型反馈
  - 用 feishu_update_doc replace_range + selection_by_title 定位第3章
  - 修正后重新跑该章质量审核
  - 不全书覆写
