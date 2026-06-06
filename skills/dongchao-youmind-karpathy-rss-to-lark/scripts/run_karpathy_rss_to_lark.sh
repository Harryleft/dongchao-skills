#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
DEFAULT_CONFIG_FILE="${PROJECT_ROOT}/.codex/skill-config/dongchao-youmind-karpathy-rss-to-lark.env.local"
DEFAULT_OUTPUT_ROOT="${PROJECT_ROOT}/data/outputs"

CONFIG_FILE="${DEFAULT_CONFIG_FILE}"
OUTPUT_ROOT="${DEFAULT_OUTPUT_ROOT}"
INIT_CONFIG=0
POLL_SECONDS=10
MAX_POLLS=24
USER_MESSAGE="${USER_MESSAGE:-请执行配置中指定的 YouMind RSS 日报技能。无需额外输入，按技能默认规则生成中文日报文档。重要要求：每篇入选文章都必须保留原始原文链接，并把该文章的小标题直接写成 Markdown 超链接格式 \`[文章标题](原文链接)\`，不要只在段落说明里零散提到来源链接。}"

usage() {
  cat <<'EOF'
Usage: run_karpathy_rss_to_lark.sh [options]

Run a YouMind Karpathy RSS daily-report workflow and create a Feishu Docx.
Archive, permission, and group notification are delegated to dongchao-feishu-publish.

Options:
  --config PATH          Private env config path
  --init-config          Interactively create/update the private config, chmod 600
  --output-root DIR      Directory for run artifacts
  --message TEXT         User message passed to YouMind createChat
  --poll-seconds N       Seconds between YouMind polls (default: 10)
  --max-polls N          Max YouMind polls (default: 24)
  -h, --help             Show this help

Required config:
  YOUMIND_API_KEY
  YOUMIND_BASE_URL
  YOUMIND_SKILL_ID
  YOUMIND_SKILL_NAME
  YOUMIND_BOARD_ID
  PUBLISH_ARCHIVE_PARENT_URL
  PUBLISH_ARCHIVE_SECTION_TITLE
  PUBLISH_MANAGER_OPEN_ID or PUBLISH_MANAGER_NAME
  PUBLISH_CHAT_ID or PUBLISH_CHAT_NAME
EOF
}

shell_quote() {
  local value="${1-}"
  printf "%q" "${value}"
}

prompt_value() {
  local var_name="$1"
  local prompt="$2"
  local default_value="${3-}"
  local secret="${4-0}"
  local value
  if [[ -n "${default_value}" ]]; then
    prompt="${prompt} [已有值，回车保留]"
  fi
  if [[ "${secret}" == "1" ]]; then
    read -r -s -p "${prompt}: " value
    printf "\n" >&2
  else
    read -r -p "${prompt}: " value
  fi
  if [[ -z "${value}" && -n "${default_value}" ]]; then
    value="${default_value}"
  fi
  printf -v "${var_name}" "%s" "${value}"
}

write_config() {
  local path="$1"
  mkdir -p "$(dirname "${path}")"
  umask 077
  {
    printf "# Private config for dongchao-youmind-karpathy-rss-to-lark\n"
    printf "# Do not commit this file.\n"
    printf "YOUMIND_API_KEY=%s\n" "$(shell_quote "${YOUMIND_API_KEY:-}")"
    printf "YOUMIND_BASE_URL=%s\n" "$(shell_quote "${YOUMIND_BASE_URL:-https://youmind.com}")"
    printf "YOUMIND_SKILL_ID=%s\n" "$(shell_quote "${YOUMIND_SKILL_ID:-}")"
    printf "YOUMIND_SKILL_NAME=%s\n" "$(shell_quote "${YOUMIND_SKILL_NAME:-}")"
    printf "YOUMIND_BOARD_ID=%s\n" "$(shell_quote "${YOUMIND_BOARD_ID:-}")"
    printf "\n"
    printf "LARK_PARENT_POSITION=%s\n" "$(shell_quote "${LARK_PARENT_POSITION:-my_library}")"
    printf "LARK_PARENT_TOKEN=%s\n" "$(shell_quote "${LARK_PARENT_TOKEN:-}")"
    printf "\n"
    printf "PUBLISH_ARCHIVE_PARENT_URL=%s\n" "$(shell_quote "${PUBLISH_ARCHIVE_PARENT_URL:-}")"
    printf "PUBLISH_ARCHIVE_PARENT_TITLE=%s\n" "$(shell_quote "${PUBLISH_ARCHIVE_PARENT_TITLE:-}")"
    printf "PUBLISH_ARCHIVE_SECTION_TITLE=%s\n" "$(shell_quote "${PUBLISH_ARCHIVE_SECTION_TITLE:-}")"
    printf "PUBLISH_LINK_SHARE_ENTITY=%s\n" "$(shell_quote "${PUBLISH_LINK_SHARE_ENTITY:-tenant_readable}")"
    printf "PUBLISH_MANAGER_OPEN_ID=%s\n" "$(shell_quote "${PUBLISH_MANAGER_OPEN_ID:-}")"
    printf "PUBLISH_MANAGER_NAME=%s\n" "$(shell_quote "${PUBLISH_MANAGER_NAME:-}")"
    printf "PUBLISH_MANAGER_EMAIL=%s\n" "$(shell_quote "${PUBLISH_MANAGER_EMAIL:-}")"
    printf "PUBLISH_MANAGER_DEPARTMENT_HINT=%s\n" "$(shell_quote "${PUBLISH_MANAGER_DEPARTMENT_HINT:-}")"
    printf "PUBLISH_MANAGER_PERM=%s\n" "$(shell_quote "${PUBLISH_MANAGER_PERM:-full_access}")"
    printf "PUBLISH_CHAT_ID=%s\n" "$(shell_quote "${PUBLISH_CHAT_ID:-}")"
    printf "PUBLISH_CHAT_NAME=%s\n" "$(shell_quote "${PUBLISH_CHAT_NAME:-}")"
  } > "${path}"
  chmod 600 "${path}"
}

init_config() {
  if [[ -f "${CONFIG_FILE}" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${CONFIG_FILE}"
    set +a
  fi

  prompt_value YOUMIND_API_KEY "YouMind API Key" "${YOUMIND_API_KEY:-}" 1
  prompt_value YOUMIND_BASE_URL "YouMind Base URL" "${YOUMIND_BASE_URL:-https://youmind.com}"
  prompt_value YOUMIND_SKILL_ID "YouMind Skill ID" "${YOUMIND_SKILL_ID:-}"
  prompt_value YOUMIND_SKILL_NAME "YouMind Skill Name" "${YOUMIND_SKILL_NAME:-}"
  prompt_value YOUMIND_BOARD_ID "YouMind Board ID" "${YOUMIND_BOARD_ID:-}"
  prompt_value LARK_PARENT_POSITION "Feishu docs create parent position" "${LARK_PARENT_POSITION:-my_library}"
  prompt_value LARK_PARENT_TOKEN "Optional Feishu parent token" "${LARK_PARENT_TOKEN:-}"
  prompt_value PUBLISH_ARCHIVE_PARENT_URL "Publish archive parent wiki URL or node token" "${PUBLISH_ARCHIVE_PARENT_URL:-}"
  prompt_value PUBLISH_ARCHIVE_PARENT_TITLE "Optional publish archive parent title" "${PUBLISH_ARCHIVE_PARENT_TITLE:-}"
  prompt_value PUBLISH_ARCHIVE_SECTION_TITLE "Publish archive section title" "${PUBLISH_ARCHIVE_SECTION_TITLE:-}"
  prompt_value PUBLISH_LINK_SHARE_ENTITY "Publish link share entity" "${PUBLISH_LINK_SHARE_ENTITY:-tenant_readable}"
  prompt_value PUBLISH_MANAGER_OPEN_ID "Manager open_id, optional if searchable fields are provided" "${PUBLISH_MANAGER_OPEN_ID:-}"
  prompt_value PUBLISH_MANAGER_NAME "Manager name, optional if open_id is provided" "${PUBLISH_MANAGER_NAME:-}"
  prompt_value PUBLISH_MANAGER_EMAIL "Manager email, optional" "${PUBLISH_MANAGER_EMAIL:-}"
  prompt_value PUBLISH_MANAGER_DEPARTMENT_HINT "Manager department hint, optional" "${PUBLISH_MANAGER_DEPARTMENT_HINT:-}"
  prompt_value PUBLISH_MANAGER_PERM "Manager permission" "${PUBLISH_MANAGER_PERM:-full_access}"
  prompt_value PUBLISH_CHAT_ID "Notification chat_id, optional if chat name is provided" "${PUBLISH_CHAT_ID:-}"
  prompt_value PUBLISH_CHAT_NAME "Notification chat name, optional if chat_id is provided" "${PUBLISH_CHAT_NAME:-}"

  write_config "${CONFIG_FILE}"
  echo "Wrote private config: ${CONFIG_FILE}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG_FILE="$2"; shift 2 ;;
    --init-config) INIT_CONFIG=1; shift ;;
    --output-root) OUTPUT_ROOT="$2"; shift 2 ;;
    --message) USER_MESSAGE="$2"; shift 2 ;;
    --poll-seconds) POLL_SECONDS="$2"; shift 2 ;;
    --max-polls) MAX_POLLS="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "${INIT_CONFIG}" -eq 1 ]]; then
  init_config
  exit 0
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "Missing private config: ${CONFIG_FILE}" >&2
  echo "Run: $0 --init-config" >&2
  exit 2
fi

set -a
# shellcheck disable=SC1090
source "${CONFIG_FILE}"
set +a

require_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required config variable: ${name}" >&2
    echo "Run: $0 --init-config" >&2
    exit 2
  fi
}

require_var YOUMIND_API_KEY
require_var YOUMIND_BASE_URL
require_var YOUMIND_SKILL_ID
require_var YOUMIND_SKILL_NAME
require_var YOUMIND_BOARD_ID
require_var PUBLISH_ARCHIVE_PARENT_URL
require_var PUBLISH_ARCHIVE_SECTION_TITLE

if [[ -z "${PUBLISH_MANAGER_OPEN_ID:-}" && -z "${PUBLISH_MANAGER_NAME:-}" ]]; then
  echo "Missing manager config: set PUBLISH_MANAGER_OPEN_ID or PUBLISH_MANAGER_NAME" >&2
  exit 2
fi

if [[ -z "${PUBLISH_CHAT_ID:-}" && -z "${PUBLISH_CHAT_NAME:-}" ]]; then
  echo "Missing chat config: set PUBLISH_CHAT_ID or PUBLISH_CHAT_NAME" >&2
  exit 2
fi

LARK_PARENT_POSITION="${LARK_PARENT_POSITION:-my_library}"
PUBLISH_LINK_SHARE_ENTITY="${PUBLISH_LINK_SHARE_ENTITY:-tenant_readable}"
PUBLISH_MANAGER_PERM="${PUBLISH_MANAGER_PERM:-full_access}"

command -v curl >/dev/null || { echo "curl is required" >&2; exit 127; }
command -v node >/dev/null || { echo "node is required" >&2; exit 127; }
command -v lark-cli >/dev/null || { echo "lark-cli is required" >&2; exit 127; }

mkdir -p "${OUTPUT_ROOT}"
RUN_DIR="$(mktemp -d "${OUTPUT_ROOT}/karpathy-rss-doc.XXXXXX")"
chmod 700 "${RUN_DIR}"
SECRET_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${SECRET_DIR}"
}
trap cleanup EXIT

to_workspace_rel() {
  local path="$1"
  if [[ "${path}" = "$(pwd)"/* ]]; then
    printf "%s\n" "${path#$(pwd)/}"
  else
    printf "%s\n" "${path}"
  fi
}

CURL_CONFIG="${SECRET_DIR}/curl.conf"
cat > "${CURL_CONFIG}" <<CURLCONF
header = "x-api-key: ${YOUMIND_API_KEY}"
header = "Content-Type: application/json"
header = "x-use-camel-case: true"
CURLCONF
chmod 600 "${CURL_CONFIG}"

CREATE_CHAT_PAYLOAD="${RUN_DIR}/create-chat.json"
CREATE_CHAT_RESULT="${RUN_DIR}/create-chat-result.json"
FINAL_CHAT="${RUN_DIR}/final-chat.json"
FINAL_MESSAGES="${RUN_DIR}/final-messages.json"
YOUMIND_DOC_JSON="${RUN_DIR}/youmind-doc.json"
YOUMIND_REPORT_MD="${RUN_DIR}/youmind-report.md"
FEISHU_MD="${RUN_DIR}/feishu-import.md"
LARK_CREATE_JSON="${RUN_DIR}/lark-create.json"
DOC_FETCH_JSON="${RUN_DIR}/lark-doc-fetch.json"
SUMMARY_JSON="${RUN_DIR}/summary.json"

node - "${CREATE_CHAT_PAYLOAD}" "${USER_MESSAGE}" "${YOUMIND_BOARD_ID}" "${YOUMIND_SKILL_ID}" "${YOUMIND_SKILL_NAME}" <<'NODE'
const fs = require('fs');
const [out, message, boardId, skillId, skillName] = process.argv.slice(2);
fs.writeFileSync(out, JSON.stringify({
  message,
  boardId,
  skill: { id: skillId, name: skillName, config: {} }
}));
NODE

curl -fsS -X POST -K "${CURL_CONFIG}" "${YOUMIND_BASE_URL}/openapi/v1/createChat" \
  -d "@${CREATE_CHAT_PAYLOAD}" \
  -o "${CREATE_CHAT_RESULT}"

CHAT_ID="$(node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); if(!d.id) process.exit(2); process.stdout.write(d.id)" "${CREATE_CHAT_RESULT}")"

for i in $(seq 1 "${MAX_POLLS}"); do
  curl -fsS -X POST -K "${CURL_CONFIG}" "${YOUMIND_BASE_URL}/openapi/v1/getChat" \
    -d "{\"chatId\":\"${CHAT_ID}\"}" \
    -o "${RUN_DIR}/get-chat-${i}.json"
  CHAT_STATUS="$(node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); process.stdout.write(String(d.status || 'unknown'))" "${RUN_DIR}/get-chat-${i}.json")"
  echo "YouMind poll ${i}: ${CHAT_STATUS}" >&2
  if [[ "${CHAT_STATUS}" == "completed" ]]; then
    cp "${RUN_DIR}/get-chat-${i}.json" "${FINAL_CHAT}"
    break
  fi
  sleep "${POLL_SECONDS}"
done

if [[ ! -f "${FINAL_CHAT}" ]]; then
  cp "${RUN_DIR}/get-chat-${MAX_POLLS}.json" "${FINAL_CHAT}"
  echo "YouMind task did not complete within polling window" >&2
  exit 3
fi

curl -fsS -X POST -K "${CURL_CONFIG}" "${YOUMIND_BASE_URL}/openapi/v1/listMessages" \
  -d "{\"chatId\":\"${CHAT_ID}\"}" \
  -o "${FINAL_MESSAGES}"

node - "${FINAL_MESSAGES}" "${RUN_DIR}/youmind-generated-meta.json" <<'NODE'
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const candidates = [];
function walk(value) {
  if (!value || typeof value !== 'object') return;
  if (value.toolName === 'write' && value.toolResult) {
    const page = value.toolResult.page || {};
    const content = value.toolResult.content || {};
    const id = page.id || page.documentId || content.documentId || content.id;
    const title = page.title || content.title;
    if (id && title) candidates.push({ id, title, source: 'write-tool' });
  }
  const out = value.toolOutput?.value || value.toolResponse || value.data;
  if (typeof out === 'string') {
    for (const m of out.matchAll(/<document meta="true" id="([^"]+)" title="([^"]+)"/g)) {
      candidates.push({ id: m[1], title: m[2], source: 'document-meta' });
    }
    for (const m of out.matchAll(/<craft_meta id="([^"]+)"[^>]*title="([^"]+)"/g)) {
      candidates.push({ id: m[1], title: m[2], source: 'craft-meta' });
    }
  }
  for (const child of Object.values(value)) walk(child);
}
walk(input);
if (!candidates.length) {
  console.error('No generated YouMind document found');
  process.exit(4);
}
const chosen = candidates[candidates.length - 1];
fs.writeFileSync(process.argv[3], JSON.stringify(chosen, null, 2));
console.log(JSON.stringify(chosen));
NODE

YOUMIND_DOC_ID="$(node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); process.stdout.write(d.id)" "${RUN_DIR}/youmind-generated-meta.json")"

curl -fsS -X POST -K "${CURL_CONFIG}" "${YOUMIND_BASE_URL}/openapi/v1/getFile" \
  -d "{\"id\":\"${YOUMIND_DOC_ID}\"}" \
  -o "${YOUMIND_DOC_JSON}"

RAW_REPORT_FOUND=0
if node - "${FINAL_MESSAGES}" "${YOUMIND_REPORT_MD}" <<'NODE'
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const candidates = [];
function walk(value) {
  if (!value || typeof value !== 'object') return;
  if (value.toolName === 'write' && typeof value.toolArguments?.content === 'string') {
    candidates.push(value.toolArguments.content);
  }
  for (const child of Object.values(value)) walk(child);
}
walk(input);
if (!candidates.length) process.exit(1);
fs.writeFileSync(process.argv[3], candidates[candidates.length - 1]);
NODE
then
  RAW_REPORT_FOUND=1
fi

node - "${YOUMIND_DOC_JSON}" "${FEISHU_MD}" "${YOUMIND_REPORT_MD}" "${RAW_REPORT_FOUND}" <<'NODE'
const fs = require('fs');
const doc = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const rawReportPath = process.argv[4];
const rawReportFound = process.argv[5] === '1';
let content = rawReportFound
  ? String(fs.readFileSync(rawReportPath, 'utf8') || '').trim()
  : String(doc.content || '').trim();
const title = doc.title || 'YouMind RSS 日报';
if (!content.startsWith('#')) content = `# ${title}\n\n${content}`;
if (!content.includes('（AI生成）')) content += '\n\n（AI生成）\n';
fs.writeFileSync(process.argv[3], content);
console.error(JSON.stringify({ youmind_document_id: doc.id, title, chars: content.length, raw_report_found: rawReportFound }));
NODE

FEISHU_MD_REL="$(to_workspace_rel "${FEISHU_MD}")"

CREATE_ARGS=(docs +create --api-version v2 --as user --doc-format markdown --parent-position "${LARK_PARENT_POSITION}" --content "@${FEISHU_MD_REL}" --format json)
if [[ -n "${LARK_PARENT_TOKEN:-}" ]]; then
  CREATE_ARGS+=(--parent-token "${LARK_PARENT_TOKEN}")
fi
lark-cli "${CREATE_ARGS[@]}" > "${LARK_CREATE_JSON}"

LARK_DOC_URL="$(node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); const doc=d.data&&d.data.document; if(!doc||!doc.url) process.exit(2); process.stdout.write(doc.url)" "${LARK_CREATE_JSON}")"
LARK_DOC_ID="$(node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); const doc=d.data&&d.data.document; if(!doc||!doc.document_id) process.exit(2); process.stdout.write(doc.document_id)" "${LARK_CREATE_JSON}")"
REPORT_TITLE="$(node -e "const fs=require('fs'); const d=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); process.stdout.write(d.title || 'YouMind RSS 日报')" "${RUN_DIR}/youmind-generated-meta.json")"

lark-cli docs +fetch --api-version v2 --doc "${LARK_DOC_URL}" --doc-format markdown --scope full --format json > "${DOC_FETCH_JSON}"

node - "${SUMMARY_JSON}" "${RUN_DIR}/youmind-generated-meta.json" "${LARK_CREATE_JSON}" "${DOC_FETCH_JSON}" "${RUN_DIR}" \
  "${PUBLISH_ARCHIVE_PARENT_URL}" "${PUBLISH_ARCHIVE_PARENT_TITLE:-}" "${PUBLISH_ARCHIVE_SECTION_TITLE}" "${PUBLISH_LINK_SHARE_ENTITY}" \
  "${PUBLISH_MANAGER_OPEN_ID:-}" "${PUBLISH_MANAGER_NAME:-}" "${PUBLISH_MANAGER_EMAIL:-}" "${PUBLISH_MANAGER_DEPARTMENT_HINT:-}" "${PUBLISH_MANAGER_PERM}" \
  "${PUBLISH_CHAT_ID:-}" "${PUBLISH_CHAT_NAME:-}" <<'NODE'
const fs = require('fs');
const [
  out, ymPath, larkPath, fetchPath, runDir,
  archiveParentUrl, archiveParentTitle, archiveSectionTitle, linkShareEntity,
  managerOpenId, managerName, managerEmail, managerDepartmentHint, managerPerm,
  chatId, chatName
] = process.argv.slice(2);
const ym = JSON.parse(fs.readFileSync(ymPath, 'utf8'));
const lark = JSON.parse(fs.readFileSync(larkPath, 'utf8'));
const fetch = JSON.parse(fs.readFileSync(fetchPath, 'utf8'));
const doc = lark.data.document;
const content = fetch.data?.document?.content || '';
const summary = {
  title: ym.title || 'YouMind RSS 日报',
  doc_url: doc.url,
  doc_token: doc.document_id,
  youmind_document_id: ym.id,
  source_type: 'YouMind/Karpathy RSS',
  validation: {
    fetched: Boolean(content),
    has_ai_footer: content.includes('（AI生成）')
  },
  publish_config: {
    archive_parent_url: archiveParentUrl,
    archive_parent_title: archiveParentTitle || null,
    archive_section_title: archiveSectionTitle,
    link_share_entity: linkShareEntity,
    manager: {
      open_id: managerOpenId || null,
      name: managerName || null,
      email: managerEmail || null,
      department_hint: managerDepartmentHint || null,
      perm: managerPerm
    },
    notification_chat: {
      chat_id: chatId || null,
      name: chatName || null
    },
    notification_identity: 'user'
  },
  run_dir: runDir
};
fs.writeFileSync(out, JSON.stringify(summary, null, 2));
console.log(JSON.stringify(summary, null, 2));
NODE
