# dongchao-feishu-bitable-design LLM Eval Cases

## Case 1: Simple single-table design
- **Input:** "帮我搭一个客户跟进的多维表格"
- **Expected:**
  - Agent asks the 6 questions before building
  - Does NOT immediately create tables
  - Identifies at least: customers table + follow-up records table (not one mega-table)

## Case 2: Many-to-many relationship
- **Input:** "我要管项目和人员，一个人员可以参与多个项目，一个项目有多个人"
- **Expected:**
  - Identifies many-to-many relationship
  - Creates 3 tables: projects, people, participation records (junction table)
  - Or uses bidirectional link field (type: 13) between projects and people

## Case 3: Lookup vs direct copy
- **Input:** "在跟进记录里我想看到客户名字"
- **Expected:**
  - Uses lookup field (type: 18), NOT a text field manually copying customer name
  - Creates link field first, then lookup field

## Case 4: API creation order
- **Input:** After design is done, agent builds the bitable
- **Expected:**
  - Order: app → all tables → all core fields → link fields → lookup fields
  - Link fields created AFTER both tables exist
  - Lookup fields created AFTER link fields exist

## Case 5: User can't answer all questions
- **Input:** "我不太确定数据关联是什么样的，先搭着看吧"
- **Expected:**
  - Agent doesn't block on unanswered questions
  - Starts with single table, plans to add associations later
  - Applies "答3个以上就动手" rule
