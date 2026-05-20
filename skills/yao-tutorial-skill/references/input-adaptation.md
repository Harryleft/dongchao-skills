# Input Adaptation

Use this guide before research. The user may provide only a topic, or they may provide a full packet of notes, URLs, drafts, papers, repos, examples, and style references. The skill should adapt its research effort to the evidence already provided.

## Priority Rule

User-provided material is the first-order reference for:

- intent and angle
- audience assumptions
- examples, cases, and terminology
- required claims or arguments
- style, tone, and output constraints
- URLs, named people, repos, papers, or projects the user explicitly wants considered

External research exists to verify, complete, update, and challenge the user material. Do not replace the user's angle with a generic web-research angle unless the user material is clearly wrong, unsafe, stale, or too thin to support the tutorial.

## Material Intake

Classify each item into one of these buckets:

- `must_use`: central material the tutorial should preserve or build around
- `supporting`: useful detail, example, data point, or source
- `style_reference`: layout, writing, visual, or tone reference
- `caution`: material that may be wrong, stale, promotional, unsupported, or out of scope
- `exclude`: material the user says not to use

Record the classification in `research/user-materials-register.md`.

Suggested schema:

```markdown
| id | type | title_or_label | user_priority | use_for | key_takeaway | limits_or_cautions |
| --- | --- | --- | --- | --- | --- | --- |
| U1 | pasted note | ... | must_use | angle, examples | ... | user-authored, verify factual claims |
```

Use `U1`, `U2`, `U3` for user material. External sources should keep `P`, `G`, `A`, `X`, or other source prefixes.

## Sufficiency Tiers

After intake, choose a research tier.

### Rich User Packet

Use this when the user provides at least one of:

- a substantial draft, transcript, or notes packet
- `5+` relevant URLs or files with a clear angle
- specific must-use papers, repos, cases, or benchmark projects
- enough examples and claims to support most chapters

Research behavior:

- use user material as the tutorial spine
- add only `3-8` external records for verification, freshness, missing theory, missing implementation, and counterexamples
- do not over-research familiar background if the user packet already supports the chapter

### Moderate User Packet

Use this when the user provides:

- a topic plus a few notes or URLs
- a clear angle but incomplete evidence
- examples but weak theory
- theory but weak practice

Research behavior:

- preserve the user's angle and examples
- add `6-12` external records
- fill only the missing source layers, such as papers, GitHub, official docs, or practitioner cases

### Thin User Packet

Use this when the user provides:

- only a topic
- one vague paragraph
- weak or mostly stylistic references
- unsupported claims with no source trail

Research behavior:

- preserve the user's wording and implied intent
- run the full source ladder from `references/research-sourcing.md`
- target `10-18` external records for a full tutorial

## Conflict Handling

When user material conflicts with external evidence:

- keep the user's goal visible
- separate opinion, practitioner signal, and supported fact
- cite the stronger source for factual claims
- explain the limitation briefly in the tutorial if it affects learning
- do not silently erase the user's idea; reshape it into a safer, source-backed version

When the user provides many references but no topic, infer the topic from the repeated pattern and state that assumption before writing.

When the user provides style references, extract rules rather than copying surface decoration.

## Personalization Hooks

Use supplied details to personalize:

- audience role: founder, engineer, teacher, student, operator, creator
- learning objective: understand, build, decide, teach, evaluate, sell, or operate
- domain context: business, education, software, AI, design, finance, healthcare, legal, or another field
- tone: formal textbook, practical playbook, narrative tutorial, internal manual
- output depth: sample, complete tutorial, deep manual

If the user gives none of these, default to a beginner practical tutorial with concrete examples and restrained document design.

## Minutes/Transcript As Input

When the user provides a Feishu Minutes URL, transcript file, or similar raw audio/video transcription:

### Material Classification

Treat the transcript as a `rich user packet`. The transcript is `must_use` for intent, examples, and sequence—but **not automatically factual** for technical terms.

### Mandatory Verification Rules

Transcripts are noisy. Speech-to-text introduces systematic errors that you must catch before they reach the tutorial:

1. **Technical term audit**: Every product name, file extension, API path, configuration key, and CLI flag mentioned in the transcript must be verified against official documentation. Common S2T errors include `.skill` ↔ `.scale`, `aily` ↔ `Ali`, `SQCA` ↔ `SCQA`, etc.
2. **Step-level accuracy**: If the speaker describes a UI workflow ("click X, then Y"), verify the path still exists and the labels are correct. Screenshots from the speaker's screen may be outdated.
3. **Scope claims**: If the speaker says "questions 6-10 are the same", verify the actual range. Speakers often round or generalize in live conversation.
4. **Named entities**: Person names, team names, permission names, and tool names must be spelled exactly as they appear in the system, not as they sound.

### Structure Fidelity Rule

**Do not inflate sparse content into equal-weight sections.** If 80% of the transcript covers topic A and 20% mentions topic B:

- Topic A becomes the main body with full chapters.
- Topic B becomes a brief section, an appendix note, or is omitted entirely—**never** inflated to match topic A's depth.
- The tutorial structure must reflect the information density of the source, not a false sense of completeness.

### Practical Detail Completeness

Transcripts often skip or assume practical details. When generating a tutorial from transcript:

- **Every operation path must be complete**: entry point → steps → result. Never write "go to the settings" without saying where the entry is.
- **Every link must be real and clickable**: never write "see the documentation link" or "the link in the reference"—find the actual URL.
- **Every screenshot position must be noted**: mark `【这里需要放一张XXX界面的截图】` where a screenshot is needed, e.g., `【这里需要放一张飞书开发后台-新建智能体页面的截图】`. A tutorial without screenshots for UI workflows is incomplete.
- **Multiple approaches**: when the speaker mentions more than one way to do something (e.g., "you can use the built-in dialog OR an external AI"), list all approaches. Do not collapse them into one.
- **Edge cases and failure modes**: if the speaker mentions a mistake they made ("I forgot to turn on recording and had to redo 4 times"), this becomes a prominent warning, not a footnote.

### Title And Framing

Prefer experience-framed titles over authoritative ones:
- ✅ `aily 智能体搭建经验（更新中）`
- ❌ `FDE 认证二通关教程：智能体创建 & 多维表格实操`

The transcript is one person's experience in one session. Frame it honestly—"经验" "实践笔记" "避坑指南"—not as a comprehensive "教程" or "通关指南" unless the content genuinely supports that scope.

## Research Budget Rule

External research should shrink when user material is strong and expand when user material is weak. It should never disappear entirely for current, factual, technical, legal, medical, financial, or tool/version-dependent topics.

Minimum external check even for rich packets:

- one authority or primary source for core definitions
- one implementation or case source when practice is involved
- one freshness check when tools, APIs, laws, prices, benchmarks, or public figures are involved
