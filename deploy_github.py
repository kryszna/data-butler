#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 site/ 部署为 GitHub Pages（下载页专用，纯 GitHub API，不依赖 git 命令）。

用法：
    GITHUB_TOKEN=你的令牌 python3 site/deploy_github.py

classic token 需要 repo 权限；fine-grained token 需要对应仓库 Contents: write，
并且必须具备创建仓库权限，否则请先手动建好空的 data-butler 仓库。
脚本不会把令牌写进任何文件，日志和报错也会自动打码。
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

REPO = "data-butler"
BRANCH = "main"
API = "https://api.github.com"
SITE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN = ""
FILES = ["index.html", "README.md", "deploy_github.py"]


def mask(text):
    return text.replace(TOKEN, "***") if TOKEN else text


def die(msg):
    print("错误：" + mask(str(msg)), file=sys.stderr)
    sys.exit(1)


def api(method, path, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body.strip() else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            obj = json.loads(body)
        except Exception:
            obj = {"message": body[:300]}
        return e.code, obj
    except Exception as e:
        die("请求 GitHub API 失败：%s" % e)


def main():
    global TOKEN
    TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
    if not TOKEN:
        die("请先设置 GITHUB_TOKEN 环境变量：\n"
            "  GITHUB_TOKEN=你的令牌 python3 site/deploy_github.py")

    print("==> [1/6] 确认令牌与账号")
    code, user = api("GET", "/user")
    if code != 200:
        die("令牌无效：HTTP %s %s" % (code, user))
    owner = user.get("login")
    print("  账号：" + owner)

    repo_path = "/repos/%s/%s" % (owner, REPO)
    print("==> [2/6] 检查/创建仓库 %s/%s" % (owner, REPO))
    code, repo = api("GET", repo_path)
    if code == 200:
        print("  仓库已存在，直接使用")
    elif code == 404:
        code, repo = api("POST", "/user/repos", {
            "name": REPO,
            "description": "数据管家下载页（静态站点）",
            "public": True,
            "has_issues": False,
            "has_wiki": False,
            "auto_init": True,
        })
        if code not in (200, 201):
            die("创建仓库失败：HTTP %s %s" % (code, repo))
        print("  仓库创建成功")
    else:
        die("检查仓库失败：HTTP %s %s" % (code, repo))

    print("==> [3/6] 读取本地站点文件")
    blobs = {}
    for name in FILES:
        path = os.path.join(SITE_DIR, name)
        with open(path, "rb") as f:
            blobs[name] = f.read()
        print("  %-18s %d bytes" % (name, len(blobs[name])))

    print("==> [4/6] 提交文件到 %s 分支" % BRANCH)
    # 用 Contents API 逐文件写入，兼容刚创建的空仓库（Git Data API 对空仓库返回 409）
    code, ref = api("GET", repo_path + "/git/ref/heads/" + BRANCH)
    branch_exists = (code == 200)
    if not branch_exists:
        print("  空仓库：首个文件由 GitHub 自动创建默认分支")
    for name, content in blobs.items():
        file_path = repo_path + "/contents/" + name
        code, current = api("GET", file_path + ("?ref=" + BRANCH if branch_exists else ""))
        sha = current.get("sha") if code == 200 else None
        payload = {
            "message": "deploy: 数据管家下载页",
            "content": base64.b64encode(content).decode("ascii"),
        }
        if branch_exists:
            payload["branch"] = BRANCH
        if sha:
            payload["sha"] = sha
        code, result = api("PUT", file_path, payload)
        if code not in (200, 201):
            die("写入 %s 失败：HTTP %s %s" % (name, code, result))
        branch_exists = True
        print("  %-18s %s" % (name, "updated" if sha else "created"))

    print("==> [5/6] 开启 GitHub Pages")
    code, pages = api("GET", repo_path + "/pages")
    if code == 200:
        print("  Pages 已开启：" + pages.get("html_url", ""))
    elif code == 404:
        code, pages = api("POST", repo_path + "/pages", {
            "source": {"branch": BRANCH, "path": "/"},
        })
        if code not in (200, 201):
            print("  自动开启失败：HTTP %s %s" % (code, pages))
            print("  请手动到 https://github.com/%s/%s/settings/pages 开启" % (owner, REPO))
        else:
            print("  Pages 开启成功：" + pages.get("html_url", ""))
    else:
        print("  查询 Pages 失败：HTTP %s %s" % (code, pages))

    print("==> [6/6] 验证")
    code, root = api("GET", repo_path + "/git/trees/" + BRANCH + "?recursive=1")
    paths = [x["path"] for x in root.get("tree", [])] if code == 200 else []
    print("  仓库文件：" + ", ".join(paths))

    print("")
    print("  下载页：https://%s.github.io/%s/" % (owner, REPO))
    print("  仓库：https://github.com/%s/%s" % (owner, REPO))
    print("")
    print("  提醒：当前 DOWNLOAD_READY=false，下载按钮显示“即将上线”。")
    print("  安装包上线后把 site/index.html 里 DOWNLOAD_READY 改为 true 并重新执行本脚本。")


if __name__ == "__main__":
    main()
