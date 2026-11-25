#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 site/ 部署到 Gitee Pages（下载页专用，独立仓库）。

用法：
    GITEE_TOKEN=你的私人令牌 python3 site/deploy_gitee.py

令牌需要「创建仓库 / 仓库写权限」。脚本不会把令牌写进任何文件：
推送时临时用带令牌的 URL，推送后立即还原为不含令牌的 URL。

说明：Gitee Pages 的开通/更新没有公开 API，脚本会创建仓库并推送文件，
最后打印需要你在网页手动点击一次「开通 Gitee Pages」的地址。
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

OWNER = "gfdaily"
REPO = "data-butler"
BRANCH = "main"
API = "https://gitee.com/api/v5"
SITE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_URL = "https://%s.gitee.io/%s/" % (OWNER, REPO)


def die(msg):
    print("错误：" + msg, file=sys.stderr)
    sys.exit(1)


def api(method, path, params=None):
    url = API + path
    data = None
    if params is not None:
        data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json;charset=UTF-8")
    if data is not None:
        req.add_header("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body.strip() else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            obj = json.loads(body)
        except Exception:
            obj = {"message": body[:200]}
        return e.code, obj
    except Exception as e:
        die("请求 Gitee API 失败：%s" % e)


def run(args, **kw):
    print("  $ " + " ".join(args[:4]) + (" ..." if len(args) > 4 else ""), flush=True)
    return subprocess.run(args, cwd=SITE_DIR, capture_output=True, text=True, **kw)


def main():
    token = os.environ.get("GITEE_TOKEN", "").strip()
    if not token:
        die("请先设置 GITEE_TOKEN 环境变量：\n"
            "  GITEE_TOKEN=你的令牌 python3 site/deploy_gitee.py")

    print("==> [1/4] 检查仓库 %s/%s" % (OWNER, REPO))
    code, obj = api("GET", "/repos/%s/%s" % (OWNER, REPO),
                    {"access_token": token})
    if code == 200:
        print("  仓库已存在，直接使用")
    elif code == 404:
        print("  仓库不存在，正在创建公开仓库…")
        code, obj = api("POST", "/user/repos", {
            "access_token": token,
            "name": REPO,
            "description": "数据管家下载页（静态站点）",
            "private": "0",
            "has_issues": "false",
            "has_wiki": "false",
        })
        if code not in (200, 201):
            die("创建仓库失败：HTTP %s %s" % (code, obj))
        print("  仓库创建成功")
    else:
        die("检查仓库失败：HTTP %s %s" % (code, obj))

    print("==> [2/4] 初始化本地站点仓库")
    if not os.path.isdir(os.path.join(SITE_DIR, ".git")):
        r = run(["git", "init", "-b", BRANCH])
        if r.returncode != 0:
            r = run(["git", "init"])
        if r.returncode != 0:
            die("git init 失败：" + r.stderr.strip())
    else:
        print("  已有 .git，跳过 init")

    clean_url = "https://gitee.com/%s/%s.git" % (OWNER, REPO)
    auth_url = "https://%s:%s@gitee.com/%s/%s.git" % (
        OWNER, urllib.parse.quote(token, safe=""), OWNER, REPO)

    run(["git", "config", "user.name", "gfdaily"])
    run(["git", "config", "user.email", "9403543+gfdaily@user.noreply.gitee.com"])
    run(["git", "remote", "remove", "origin"])
    run(["git", "remote", "add", "origin", auth_url])

    print("==> [3/4] 提交并推送下载页")
    run(["git", "add", "index.html", "README.md", "deploy_gitee.py"])
    r = run(["git", "commit", "-m", "deploy: 数据管家下载页（占位，安装包待上线）"])
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        die("git commit 失败：" + (r.stderr or r.stdout).strip())
    r = run(["git", "push", "-u", "origin", BRANCH])
    if r.returncode != 0:
        die("git push 失败：" + (r.stderr or r.stdout).strip())
    print("  推送成功")

    # 推送后立即还原 URL，令牌不落盘
    run(["git", "remote", "set-url", "origin", clean_url])

    print("==> [4/4] 完成")
    print("  下载页地址（开通 Pages 后）：" + PAGES_URL)
    print("  仓库地址：https://gitee.com/%s/%s" % (OWNER, REPO))
    print("")
    print("  下一步（Gitee Pages 无公开 API，需手动开通一次）：")
    print("  1) 登录 Gitee，打开 https://gitee.com/%s/%s" % (OWNER, REPO))
    print("  2) 在仓库顶部菜单点「服务」→「Gitee Pages」")
    print("  3) 部署分支选 main、部署目录填 /，点「启动」")
    print("  4) 需要 Gitee 实名认证；首次可能有审核")
    print("  5) 以后每次 push 后，回到 Pages 页点一次「更新」")
    print("")
    print("  提醒：当前页面下载按钮为占位状态（DOWNLOAD_READY=false）。")
    print("  安装包准备好后，把 site/index.html 里的 DOWNLOAD_READY 改为 true 并重新推送。")


if __name__ == "__main__":
    main()
