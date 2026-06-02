# dongchao-miaoda-translate LLM Eval Cases
# These test cases verify translation quality, not code behavior.
# Run manually: compare agent output against expected quality criteria.

## Case 1: Quick mode — short tweet
- **Input:** "AI agents are the new SaaS. But most people are building wrappers, not systems."
- **Mode:** quick
- **Expected:** 
  - Complete Chinese translation
  - "AI Wrapper" → "AI 套壳" (from glossary)
  - No analysis step output
  - Takes < 30 seconds

## Case 2: Normal mode — blog paragraph
- **Input:** A 500-word English blog post about AI agents
- **Mode:** normal
- **Expected:**
  - Analysis step outputs: content summary, terminology list, tone assessment, translation challenges
  - Translation reads like original Chinese, not translated Chinese
  - Technical terms kept in English with first-occurrence annotation
  - "Hallucination" → "幻觉", "Alignment" → "对齐"
  - Upgrade prompt at end: "如需进一步审校润色，回复'继续润色'"

## Case 3: Refined mode — key paragraph
- **Input:** A paragraph with metaphor and emotional language
- **Mode:** refined
- **Expected:**
  - All 4 phases executed: analysis → draft → review → polish
  - Review step marks specific sentences as "翻译腔"
  - Metaphors translated by intent, not literally
  - Emotional tone preserved (not flattened)
  - Final output reads as if originally written in Chinese

## Case 4: Glossary consistency
- **Input:** A text mentioning "Moat" and "Flywheel" multiple times
- **Mode:** normal
- **Expected:**
  - "Moat" → "护城河" consistently (not "壁垒" in one place and "护城河" in another)
  - "Flywheel" → "飞轮效应" consistently
  - First occurrence: "护城河（Moat）"

## Case 5: Format preservation
- **Input:** Markdown with headers, bold, code blocks, tables, and links
- **Mode:** normal
- **Expected:**
  - All Markdown formatting preserved exactly
  - Code blocks not translated
  - Links functional
  - Table structure intact
