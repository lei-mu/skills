import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], capture_output: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture_output,
        check=False,
    )


def load_skills(args: argparse.Namespace) -> dict:
    helper_script = Path(__file__).with_name("get_clawhub_skills.py")
    command = [
        sys.executable,
        str(helper_script),
        "--config-path",
        args.config_path,
        "--skill-slug",
        args.skill_slug,
        "--expected-version",
        args.expected_version,
        "--json-output",
    ]
    result = run_command(command, capture_output=True)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        raise RuntimeError("读取待发布 skills 失败。")
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-path", default="clawhub/skills.publish.json")
    parser.add_argument("--skill-slug", default="")
    parser.add_argument("--expected-version", default="")
    parser.add_argument("--changelog", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    clawhub_token = os.environ.get("CLAWHUB_TOKEN", "").strip()
    if not clawhub_token:
        raise RuntimeError("缺少环境变量 CLAWHUB_TOKEN，无法执行 ClawHub 发布。")

    resolved_skills = load_skills(args)
    skills = resolved_skills.get("skills") or []
    if not skills:
        raise RuntimeError("没有可发布的 skill。")

    print("开始登录 ClawHub CLI...")
    login_result = run_command(
        ["npx", "--yes", "clawhub@latest", "login", "--token", clawhub_token, "--no-browser"]
    )
    if login_result.returncode != 0:
        raise RuntimeError("ClawHub CLI 登录失败。")

    if args.dry_run:
        print("当前为 dry-run 模式：会执行登录、元数据校验和远端版本探测，但不会真实发布。")

    publish_results = []
    for skill in skills:
        slug = skill["slug"]
        version = skill["version"]
        source = skill["source"]
        name = skill["name"]
        skill_changelog = skill.get("changelog", "")
        publish_changelog = args.changelog or skill_changelog

        print(f"检查远端版本是否已存在: slug={slug} version={version}")
        inspect_result = run_command(
            ["npx", "--yes", "clawhub@latest", "inspect", "--version", version, slug],
            capture_output=True,
        )
        inspect_output = f"{inspect_result.stdout}{inspect_result.stderr}"
        already_published = inspect_result.returncode == 0 and version in inspect_output

        if already_published:
            print(f"检测到远端已存在相同版本，跳过发布: slug={slug} version={version}")
            publish_results.append(
                {"slug": slug, "version": version, "status": "skipped", "reason": "version_exists"}
            )
            continue

        if args.dry_run:
            print(f"dry-run: 检测到可发布版本，但不会执行真实发布: slug={slug} version={version}")
            publish_results.append(
                {
                    "slug": slug,
                    "version": version,
                    "status": "dry_run",
                    "reason": "publish_skipped_in_dry_run",
                }
            )
            continue

        command = [
            "npx",
            "--yes",
            "clawhub@latest",
            "skill",
            "publish",
            source,
            "--slug",
            slug,
            "--name",
            name,
            "--version",
            version,
        ]
        if publish_changelog:
            command.extend(["--changelog", publish_changelog])

        print(f"执行发布: slug={slug} version={version} source={source}")
        publish_result = run_command(command)
        if publish_result.returncode == 0:
            publish_results.append({"slug": slug, "version": version, "status": "published", "reason": ""})
            continue

        print(f"发布失败，继续处理下一个 skill: slug={slug} version={version}", file=sys.stderr)
        publish_results.append(
            {"slug": slug, "version": version, "status": "failed", "reason": "publish_command_failed"}
        )

    print("发布结果汇总:")
    print(json.dumps(publish_results, ensure_ascii=False, indent=2))

    failed_items = [item for item in publish_results if item["status"] == "failed"]
    if failed_items:
        raise RuntimeError("存在发布失败的 skill，请检查上面的日志。")


if __name__ == "__main__":
    main()
