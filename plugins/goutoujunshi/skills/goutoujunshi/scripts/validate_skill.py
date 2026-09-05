#!/usr/bin/env python3
"""Validate the distributable goutoujunshi skill without third-party packages."""

from __future__ import annotations

import re
import subprocess
import sys
from math import ceil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
SKILL_MAX_LINES = 150
SKILL_MAX_CHARACTERS = 5_000
SKILL_MAX_APPROX_TOKENS = 4_500

REQUIRED_KNOWLEDGE = (
    "01-证据分级与内容边界.md",
    "05-PUA操控与伦理替代.md",
    "08-同意边界性与亲密.md",
    "09-在线约会与数字关系.md",
    "17-中国法律安全与危机转介.md",
    "20-经典社交体系的机制、证据与风险边界.md",
)

REQUIRED_PRACTICAL = (
    "00-导读与使用分级.md",
    "关系投入失衡：互惠判断、降级投入与退出决策.md",
    "场景感、松弛感与社交校准：从接话到关系推进.md",
    "实战话术编排器：从一句回复到后续分支.md",
    "主动表达、第一次见面与自然接触.md",
    "自然流、内在状态与结构化互动：伦理能力转译.md",
    "ChatLab聊天记录分析适配.md",
    "长期记忆与关系档案.md",
    "公开表达案例的伦理转译.md",
)

def require(path: str) -> Path:
    target = ROOT / path
    if not target.exists():
        ERRORS.append(f"missing required path: {path}")
    return target


def validate_frontmatter() -> None:
    skill = require("SKILL.md")
    if not skill.is_file():
        return

    content = skill.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        ERRORS.append("SKILL.md has invalid YAML frontmatter boundaries")
        return

    frontmatter = match.group(1)
    keys = re.findall(r"^([A-Za-z0-9_-]+):", frontmatter, re.MULTILINE)
    if keys != ["name", "description"]:
        ERRORS.append(f"SKILL.md frontmatter keys must be name, description; got {keys}")

    name_match = re.search(r"^name:\s*([^\n]+)$", frontmatter, re.MULTILINE)
    description_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else ""
    description = description_match.group(1).strip() if description_match else ""
    if name != "goutoujunshi" or not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        ERRORS.append(f"invalid skill name: {name!r}")
    if not description or len(description) > 1024 or "<" in description or ">" in description:
        ERRORS.append("description is empty, too long, or contains angle brackets")


def approximate_token_count(content: str) -> int:
    """Return a conservative, dependency-free budget estimate for mixed Chinese text."""
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", content))
    latin_words = len(re.findall(r"[A-Za-z0-9_]+", content))
    other = len(re.findall(r"[^\sA-Za-z0-9_\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", content))
    return cjk + ceil(latin_words * 1.3) + ceil(other / 4)


def validate_skill_budget() -> None:
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        return

    content = skill.read_text(encoding="utf-8")
    lines = len(content.splitlines())
    characters = len(content)
    approx_tokens = approximate_token_count(content)
    if lines > SKILL_MAX_LINES:
        ERRORS.append(f"SKILL.md exceeds {SKILL_MAX_LINES} lines: {lines}")
    if characters > SKILL_MAX_CHARACTERS:
        ERRORS.append(
            f"SKILL.md exceeds {SKILL_MAX_CHARACTERS} characters: {characters}"
        )
    if approx_tokens > SKILL_MAX_APPROX_TOKENS:
        ERRORS.append(
            "SKILL.md exceeds approximate token budget "
            f"{SKILL_MAX_APPROX_TOKENS}: {approx_tokens}"
        )


def validate_inventory(runtime_only: bool) -> None:
    require("agents/openai.yaml")
    require("scripts/memory_store.py")
    if not runtime_only:
        require("README.md")
        require("LICENSE")
    for filename in REQUIRED_KNOWLEDGE:
        require(f"references/knowledge/{filename}")
    for filename in REQUIRED_PRACTICAL:
        require(f"references/practical/{filename}")
    agent = ROOT / "agents/openai.yaml"
    if agent.is_file() and "$goutoujunshi" not in agent.read_text(encoding="utf-8"):
        ERRORS.append("agents/openai.yaml default prompt must mention $goutoujunshi")


def validate_routes_and_regressions(runtime_only: bool) -> None:
    skill = ROOT / "SKILL.md"
    if skill.is_file():
        content = skill.read_text(encoding="utf-8")
        required_routes = (
            "references/knowledge/20-经典社交体系的机制、证据与风险边界.md",
            "references/practical/自然流、内在状态与结构化互动：伦理能力转译.md",
            "默认只读取当前问题直接需要的 1–3 份参考",
            "references/practical/ChatLab聊天记录分析适配.md",
            "references/practical/长期记忆与关系档案.md",
            "references/knowledge/04-MBTI人格与匹配.md",
        )
        for route in required_routes:
            if route not in content:
                ERRORS.append(f"SKILL.md missing required progressive-disclosure route: {route}")

        regression_markers = (
            "## 每次分析",
            "**情绪落地**",
            "**事实拆分**",
            "**利益判断**",
            "**明确建议**",
            "**行动收束**",
            "观察窗口或停止条件",
            "当前对话没有档案时，先发紧凑问卷",
            "你：MBTI / 主观综合评分0–100 / 主要优势和短板",
            "对象A：代号 / MBTI / 主观综合评分0–100 / 当前关系",
            "经过：认识方式、发展多久、最近三件关键事件、联系和双方投入",
            "明确表示不想发展、要求不要联系或反复表示不欢迎时停止推进",
            "第一屏先给一条可复制成品",
            "发送时机、主要代价和积极／含糊／不回应的后续",
            "锁定“用户／对象”的说话人映射",
            "不声称能直接读取、解密或导出",
            "首次明确同意后才启用",
            "不从姓名、MBTI、旧案例或模型推测补事实",
        )
        for marker in regression_markers:
            if marker not in content:
                ERRORS.append(f"SKILL.md missing required behavior boundary: {marker}")

def validate_runtime_boundaries() -> None:
    if (ROOT / ".git").exists():
        tracked_research = subprocess.run(
            ["git", "ls-files", "--", "research", "恋爱知识库"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        for path in tracked_research:
            ERRORS.append(
                f"raw research must remain untracked and outside runtime content: {path}"
            )

    runtime_roots = (
        ROOT / "SKILL.md",
        ROOT / "agents",
        ROOT / "references",
        ROOT / "scripts",
        ROOT / "assets",
    )
    forbidden_parts = {"research", "documentation", ".git", "__pycache__"}
    for runtime_root in runtime_roots:
        if not runtime_root.exists():
            continue
        paths = (runtime_root,) if runtime_root.is_file() else runtime_root.rglob("*")
        for path in paths:
            if forbidden_parts.intersection(path.relative_to(ROOT).parts):
                ERRORS.append(
                    "non-runtime content nested inside runtime allowlist: "
                    f"{path.relative_to(ROOT)}"
                )
            if path.is_file() and path.suffix in {".pyc", ".pyo"}:
                ERRORS.append(
                    f"compiled test/runtime artifact found: {path.relative_to(ROOT)}"
                )


def validate_markdown_links() -> None:
    link_pattern = re.compile(r"\]\(([^)]+)\)")
    for markdown in ROOT.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for raw_target in link_pattern.findall(text):
            target = raw_target.strip().split("#", 1)[0]
            if not target or re.match(r"^(?:https?://|mailto:)", target):
                continue
            resolved = (markdown.parent / target).resolve()
            if not resolved.exists():
                ERRORS.append(
                    f"broken local link in {markdown.relative_to(ROOT)}: {raw_target}"
                )


def validate_placeholders() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".py"}:
            continue
        text = path.read_text(encoding="utf-8")
        if "[" + "TODO" in text:
            ERRORS.append(f"template placeholder in {path.relative_to(ROOT)}")


def main() -> int:
    unexpected_args = [arg for arg in sys.argv[1:] if arg != "--runtime"]
    if unexpected_args:
        print(f"ERROR: unsupported arguments: {' '.join(unexpected_args)}")
        return 2
    runtime_only = "--runtime" in sys.argv[1:]

    validate_frontmatter()
    validate_skill_budget()
    validate_inventory(runtime_only)
    validate_routes_and_regressions(runtime_only)
    validate_runtime_boundaries()
    validate_markdown_links()
    validate_placeholders()
    if ERRORS:
        for error in ERRORS:
            print(f"ERROR: {error}")
        return 1
    print("goutoujunshi validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
