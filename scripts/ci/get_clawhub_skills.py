import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z\.-]+)?(?:\+[0-9A-Za-z\.-]+)?$")


def read_utf8_text(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        raise RuntimeError(f"文件不存在: {path_str}")

    content_bytes = path.read_bytes()
    if content_bytes.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError(f"文件不能使用 UTF-8 BOM 编码: {path_str}")

    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"文件不是合法的 UTF-8 编码: {path_str}") from exc

    if "\ufffd" in content:
        raise RuntimeError(f"文件中检测到乱码替换字符 '�': {path_str}")

    return content


def parse_frontmatter(skill_file_path: str) -> dict:
    content = read_utf8_text(skill_file_path)
    lines = re.split(r"\r?\n", content)

    if len(lines) < 3 or lines[0].strip() != "---":
        raise RuntimeError(f"SKILL.md 缺少 frontmatter: {skill_file_path}")

    end_index = -1
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

    if end_index < 0:
        raise RuntimeError(f"SKILL.md frontmatter 未正确结束: {skill_file_path}")

    frontmatter_lines = lines[1:end_index]
    data = {}
    for line in frontmatter_lines:
        if line.startswith((" ", "\t", "-")):
            continue
        match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.+?)\s*$", line)
        if match:
            data[match.group(1)] = match.group(2).strip()

    tags_raw = data.get("tags", "")
    tags = []
    if tags_raw.startswith("[") and tags_raw.endswith("]"):
        tags_content = tags_raw[1:-1].strip()
        if tags_content:
            tags = [
                item.strip().strip("'").strip('"')
                for item in tags_content.split(",")
                if item.strip()
            ]

    name = data.get("name", "")
    version = data.get("version", "")
    description = data.get("description", "")

    if not name:
        raise RuntimeError(f"SKILL.md frontmatter 缺少 name: {skill_file_path}")
    if not version:
        raise RuntimeError(f"SKILL.md frontmatter 缺少 version: {skill_file_path}")
    if not description:
        raise RuntimeError(f"SKILL.md frontmatter 缺少 description: {skill_file_path}")
    if not SEMVER_PATTERN.match(version):
        raise RuntimeError(f"SKILL.md version 不是合法的 semver 风格版本: {skill_file_path} => {version}")
    if "�" in content:
        raise RuntimeError(f"SKILL.md 中检测到乱码字符 '�': {skill_file_path}")

    return {
        "name": name,
        "version": version,
        "description": description,
        "tags": tags,
    }


def load_skills(config_path: str, skill_slug: str, expected_version: str) -> dict:
    config_content = read_utf8_text(config_path)
    config = json.loads(config_content)
    skills = config.get("skills") or []
    if not skills:
        raise RuntimeError(f"发布配置中未定义任何 skills: {config_path}")

    result_skills = []
    for item in skills:
        if not item:
            continue

        if item.get("publish", True) is False:
            continue

        source = item.get("source", "").strip()
        if not source:
            raise RuntimeError(f"发布配置项缺少 source: {config_path}")

        skill_dir = Path(source)
        if not skill_dir.is_dir():
            raise RuntimeError(f"Skill 目录不存在: {source}")

        skill_file = skill_dir / "SKILL.md"
        metadata = parse_frontmatter(str(skill_file))
        skill_name = metadata["name"]
        slug = (item.get("slug") or skill_name or skill_dir.name).strip()
        display_name = (item.get("name") or skill_name).strip()

        if item.get("slug") and slug != skill_name:
            raise RuntimeError(
                f"配置中的 slug 必须与 SKILL.md 的 name 一致: source={source}, slug={slug}, skillName={skill_name}"
            )

        result_skills.append(
            {
                "slug": slug,
                "source": source.replace("\\", "/"),
                "skillFile": str(skill_file).replace("\\", "/"),
                "skillName": skill_name,
                "name": display_name,
                "version": metadata["version"],
                "description": metadata["description"],
                "tags": metadata["tags"],
            }
        )

    if skill_slug:
        result_skills = [item for item in result_skills if item["slug"] == skill_slug]
        if not result_skills:
            raise RuntimeError(f"未在发布配置中找到指定 skill: {skill_slug}")

    if expected_version:
        for item in result_skills:
            if item["version"] != expected_version:
                raise RuntimeError(
                    f"版本不一致: slug={item['slug']}, SKILL.md={item['version']}, 期望版本={expected_version}"
                )

    return {
        "generatedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "count": len(result_skills),
        "skills": result_skills,
    }


def write_github_output(result: dict) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    compressed_json = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    with open(output_path, "a", encoding="utf-8", newline="\n") as output_file:
        output_file.write(f"count={result['count']}\n")
        output_file.write(f"has_skills={'true' if result['count'] > 0 else 'false'}\n")
        output_file.write("skills_json<<EOF\n")
        output_file.write(compressed_json + "\n")
        output_file.write("EOF\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-path", default="clawhub/skills.publish.json")
    parser.add_argument("--skill-slug", default="")
    parser.add_argument("--expected-version", default="")
    parser.add_argument("--json-output", action="store_true")
    args = parser.parse_args()

    result = load_skills(
        config_path=args.config_path,
        skill_slug=args.skill_slug,
        expected_version=args.expected_version,
    )
    write_github_output(result)

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    for item in result["skills"]:
        print(f"{item['slug']}\t{item['name']}\t{item['version']}\t{item['source']}")


if __name__ == "__main__":
    main()
