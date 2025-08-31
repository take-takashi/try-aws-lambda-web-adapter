#!/usr/bin/env python
import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Sequence, overload, Literal, cast


@overload
def run(cmd: Sequence[str], *, capture: Literal[True]) -> str: ...

@overload
def run(cmd: Sequence[str], *, capture: Literal[False] = ...) -> None: ...

def run(cmd: Sequence[str], *, capture: bool = False) -> str | None:
    if capture:
        return subprocess.run(
            cmd, check=True, stdout=subprocess.PIPE, text=True
        ).stdout
    else:
        subprocess.run(cmd, check=True)
        return None


def infer_repo_from_git() -> str | None:
    try:
        remote = run(
            ["git", "config", "--get", "remote.origin.url"], capture=True
        ).strip()
    except subprocess.CalledProcessError:
        return None
    if not remote:
        return None
    # ssh: git@github.com:owner/repo.git
    # https: https://github.com/owner/repo.git
    remote = re.sub(r"^git@github\.com:", "https://github.com/", remote)
    remote = re.sub(r"\.git$", "", remote)
    m = re.search(r"github\.com/([^/]+/[^/]+)$", remote)
    return m.group(1) if m else None


def list_remote_secret_names(repo: str, env_name: str | None) -> list[str]:
    base = ["gh", "secret", "list", "--repo", repo, "--json", "name", "-q", ".[].name"]
    if env_name:
        base += ["--env", env_name]
    out = run(base, capture=True)
    return sorted(set(out.splitlines()))


def set_secret(
    repo: str, name: str, value: str, env_name: str | None, dry: bool
) -> None:
    base = ["gh", "secret", "set", name, "--repo", repo, "--body", value]
    if env_name:
        base += ["--env", env_name]
    if dry:
        print(
            f"[DRY] gh secret set {name} --repo {repo}"
            + (f" --env {env_name}" if env_name else "")
        )
        return
    # 値は表示しない
    subprocess.run(base, check=True, stdout=subprocess.DEVNULL)


def delete_secret(repo: str, name: str, env_name: str | None, dry: bool) -> None:
    base = ["gh", "secret", "delete", name, "--repo", repo, "-y"]
    if env_name:
        base += ["--env", env_name]
    if dry:
        print(
            f"[DRY] gh secret delete {name} --repo {repo}"
            + (f" --env {env_name}" if env_name else "")
        )
        return
    subprocess.run(base, check=True, stdout=subprocess.DEVNULL)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Update GitHub Secrets from TOML table (e.g. .mise.local.toml [env])"
    )
    p.add_argument("--repo", help="owner/repo. 省略時は git remote から推定")
    p.add_argument(
        "--env",
        dest="env_name",
        help="GitHub Environment name（指定時は Environment Secret を更新）",
    )
    p.add_argument("--file", default=".mise.local.toml", help="TOML ファイルパス")
    p.add_argument("--table", default="env", help="TOML テーブル名（例: env）")
    p.add_argument("--only", help="更新対象キーの正規表現（ホワイトリスト）")
    p.add_argument("--exclude", help="除外キーの正規表現（ブラックリスト）")
    p.add_argument("--prefix", help="Secret名に付与する接頭辞（例: APP_ ）")
    p.add_argument(
        "--delete-missing",
        action="store_true",
        help="TOMLに無いリモートSecretsを削除（注意）",
    )
    p.add_argument("--dry-run", action="store_true", help="適用せず内容だけ表示")
    args = p.parse_args()

    # 型を安定させる（Pyright向け）
    repo_arg: str | None = args.repo
    env_name: str | None = args.env_name
    file_arg: str = args.file
    table_arg: str = args.table
    only_arg: str | None = args.only
    exclude_arg: str | None = args.exclude
    prefix_arg: str | None = args.prefix
    delete_missing: bool = args.delete_missing
    dry_run: bool = args.dry_run

    # gh が使えるかチェック
    try:
        run(["gh", "--version"], capture=True)
    except Exception:
        print(
            "gh CLI が見つかりません。`mise install` 済みか確認してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    repo = repo_arg or infer_repo_from_git()
    if not repo:
        print(
            "--repo owner/repo を指定するか、git remote origin から推定できる場所で実行してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    toml_path = Path(file_arg)
    if not toml_path.exists():
        print(f"ファイルがありません: {toml_path}", file=sys.stderr)
        sys.exit(1)

    with toml_path.open("rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    tbl = data.get(table_arg)
    if not isinstance(tbl, dict):
        print(f"TOMLにテーブル [{table_arg}] が見つかりません。", file=sys.stderr)
        sys.exit(1)

    raw_items = cast(dict[str, object], tbl)
    only_re = re.compile(only_arg) if only_arg else None
    excl_re = re.compile(exclude_arg) if exclude_arg else None

    # TOML値はstrに揃える（数値/真偽/配列は用途次第で文字列化）
    def to_str(v: object) -> str:
        if v is None:
            return ""
        if isinstance(v, (str, int, float, bool)):
            return str(v)
        # 配列/テーブルはJSON文字列として入れる
        return json.dumps(v, ensure_ascii=False)

    # 抽出＆フィルタ
    items: list[tuple[str, str]] = []
    for k, v in raw_items.items():
        if only_re and not only_re.search(k):
            continue
        if excl_re and excl_re.search(k):
            continue
        name = (prefix_arg + k) if prefix_arg else k
        items.append((name, to_str(v)))

    if not items:
        print("更新対象がありません（フィルタで全て除外された可能性）。")
        return

    print(f"Target repo: {repo}{' (env: ' + env_name + ')' if env_name else ''}")
    print(f"Source     : {toml_path} [{table_arg}]")
    print(f"Upserting  : {len(items)} secrets")
    for name, _ in items:
        print(f" - {name}")

    # 反映
    for name, value in items:
        set_secret(repo, name, value, env_name, dry_run)

    # 削除
    if delete_missing:
        remote = list_remote_secret_names(repo, env_name)
        desired = sorted({n for n, _ in items})
        to_del = sorted(set(remote) - set(desired))
        if to_del:
            print(f"Deleting {len(to_del)} secrets not in TOML: {', '.join(to_del)}")
            for n in to_del:
                delete_secret(repo, n, env_name, dry_run)
        else:
            print("No secrets to delete.")

    print("Done.")


if __name__ == "__main__":
    main()
