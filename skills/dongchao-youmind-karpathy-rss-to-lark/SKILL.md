---
name: dongchao-youmind-karpathy-rss-to-lark
description: "Run a YouMind Karpathy RSS daily-report skill, create a Feishu/Lark Docx from the generated report, then hand off archive, permission, and group notification governance to dongchao-feishu-publish. Use when the user asks to run or test a YouMind Karpathy RSS to Feishu/Lark workflow."
depends-on:
  - dongchao-feishu-publish
---

# YouMind Karpathy RSS To Lark

This Skill runs a YouMind daily-report workflow and creates a Feishu Docx. It does not hard-code tenant-specific wiki URLs, user IDs, chat IDs, email addresses, YouMind skill IDs, or board IDs. It also does not implement archive, permission, or group notification logic itself; those steps are delegated to `dongchao-feishu-publish`.

## Workflow

1. Load private runtime configuration from the project-local config file.
2. If config is missing, run `scripts/run_karpathy_rss_to_lark.sh --init-config` and ask the user for the required variables.
3. Execute the YouMind skill and poll until the task completes.
4. Read the generated YouMind document content.
5. Create a Feishu Docx from the report.
6. Read back the Feishu document and write `summary.json`.
7. Pass `title`, `doc_url`, and the publish config to `dongchao-feishu-publish`.

## Private Config

Default config path, resolved from the current project directory:

```text
.codex/skill-config/dongchao-youmind-karpathy-rss-to-lark.env.local
```

The config file is private and must not be committed. It may contain:

```bash
YOUMIND_API_KEY=
YOUMIND_BASE_URL=
YOUMIND_SKILL_ID=
YOUMIND_SKILL_NAME=
YOUMIND_BOARD_ID=

LARK_PARENT_POSITION=my_library
LARK_PARENT_TOKEN=

PUBLISH_ARCHIVE_PARENT_URL=
PUBLISH_ARCHIVE_PARENT_TITLE=
PUBLISH_ARCHIVE_SECTION_TITLE=
PUBLISH_LINK_SHARE_ENTITY=tenant_readable
PUBLISH_MANAGER_OPEN_ID=
PUBLISH_MANAGER_NAME=
PUBLISH_MANAGER_EMAIL=
PUBLISH_MANAGER_DEPARTMENT_HINT=
PUBLISH_MANAGER_PERM=full_access
PUBLISH_CHAT_ID=
PUBLISH_CHAT_NAME=
```

Required values:

- `YOUMIND_API_KEY`
- `YOUMIND_SKILL_ID`
- `YOUMIND_SKILL_NAME`
- `YOUMIND_BOARD_ID`
- `PUBLISH_ARCHIVE_PARENT_URL`
- `PUBLISH_ARCHIVE_SECTION_TITLE`
- manager identity: either `PUBLISH_MANAGER_OPEN_ID` or enough searchable fields such as `PUBLISH_MANAGER_NAME` plus optional email or department hint
- chat identity: either `PUBLISH_CHAT_ID` or `PUBLISH_CHAT_NAME`

Do not use historical run values, memory values, or examples as defaults for tenant-specific IDs.

## Commands

Initialize private config:

```bash
.codex/skills/dongchao-youmind-karpathy-rss-to-lark/scripts/run_karpathy_rss_to_lark.sh --init-config
```

Run the document-generation step:

```bash
.codex/skills/dongchao-youmind-karpathy-rss-to-lark/scripts/run_karpathy_rss_to_lark.sh
```

Use a custom config path:

```bash
.codex/skills/dongchao-youmind-karpathy-rss-to-lark/scripts/run_karpathy_rss_to_lark.sh --config path/to/private.env
```

## Output Contract

The script prints a JSON summary and writes the same data to `<run_dir>/summary.json`. The summary includes:

- `title`
- `doc_url`
- `doc_token`
- `youmind_document_id`
- `source_type`: `YouMind/Karpathy RSS`
- `publish_config`: variables needed by `dongchao-feishu-publish`
- `run_dir`

Keep original source links visible in the generated report. For each selected article, the article title line should itself be a clickable Markdown hyperlink in the format `[文章标题](原文链接)`.

## Publishing

After the script creates the Feishu Docx and validates the document body, call `dongchao-feishu-publish` with:

- `doc_url`
- `title`
- source type: `YouMind/Karpathy RSS`
- publish config from `summary.json`

Archive location is controlled by `PUBLISH_ARCHIVE_PARENT_URL` and `PUBLISH_ARCHIVE_SECTION_TITLE`. For Karpathy RSS daily reports, the user can set the section title in private config, but the section name must not be hard-coded in this repository.

## Safety Rules

- Never put `YOUMIND_API_KEY` in `SKILL.md`, command arguments, Git-tracked files, final answers, or logs.
- Never commit private config files.
- Treat YouMind network access, Feishu doc creation, publishing, permissions, wiki updates, and IM sends as live operations.
- If `youmind.com` is unreachable, report a network boundary failure before debugging Feishu steps.
- If a required publish variable is missing, stop and ask the user to run `--init-config` or edit the private config.

## Verification Expectations

After a successful run, report:

- YouMind generated document title and ID.
- Feishu Docx URL.
- Local `summary.json` path.
- Whether `dongchao-feishu-publish` completed archive, permission, and group notification verification.

Keep the user-facing summary short and in Chinese for this workspace.
