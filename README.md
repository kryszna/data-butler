# 数据管家下载页（静态）

仿 WorkBuddy 官网风格的单文件静态下载页，无后端、无外部依赖。
页面托管在 **GitHub Pages**；Gitee 仓库仅继续用于存放安装包 / 更新包（Gitee Pages 已停服）。

## 文件

- `index.html` — 全部内容（HTML + CSS + JS 内联）

## 当前状态：仅部署页面

`index.html` 里 `DOWNLOAD_READY = false`，下载按钮显示"即将上线"，点击只弹提示、不跳转。
这是为了避免跳转到还不存在的 Release 页。等安装包上传到 Gitee Releases 后，把这一行改成 `true` 即可启用真实下载。

## 1. 填写 Gitee 仓库信息

打开 `index.html`，找到底部的 `var GITEE = {...}` 配置块，改成你的实际信息：

```js
var GITEE = {
  owner : "gfdaily",        // Gitee 用户名（个人空间地址）
  repo  : "data-butler",    // 仓库名
  tag   : "v1.0",           // Release 标签
  file  : "数据管家.dmg"     // 附件文件名
};
```

- 页面默认跳转到 `<owner>/<repo>/releases` 列表页（最稳妥，附件改动不用改页面）。
- 若想点按钮直接下载附件，把 `pick()` 里的 `releaseUrl()` 改成 `directUrl()`。
- 完整 dmg 超过 Gitee 单文件上限（免费版 50MB、附件 100MB），无法整包上传；如需在 Gitee 提供下载，需改放小体积核心包，或使用外部对象存储。

## 2. 上传安装包到 Gitee

1. 在 Gitee 创建公开仓库 `data-butler`（或按你改过的 `build/gitee.json` 里的 repo 名）。
2. 进入仓库 → **发行版 / Releases** → 新建发行版，标签填 `v1.0`（或与配置一致）。
3. 上传 `数据管家.dmg` 作为附件并发布。
4. 记下仓库用户名、仓库名、标签、文件名，填进上面的配置块。

注意：Gitee 免费版对单仓库容量和单文件大小有限制，2GB 的 dmg 可能超出附件上限。若上传失败，可改用 Gitee LFS 或外部对象存储，并把下载链接指向实际地址（改 `releaseUrl()` 返回即可）。

## 3. 部署到 GitHub Pages

使用已有脚本一键创建 / 复用仓库、推送 `site/`、并通过 API 开启 Pages：

```bash
GITHUB_TOKEN=你的令牌 python3 site/deploy_github.py
```

- classic token 勾选 `repo`；细粒度令牌需要创建仓库权限 + 对应仓库 `Contents: write`。
- 脚本全程使用 GitHub API 提交文件，不调用 git、不写本地 remote，令牌不会落盘，日志和报错自动打码。
- 仓库不存在会自动创建；已存在则覆盖 `main` 分支内容。
- 访问地址：`https://<GitHub用户名>.github.io/data-butler/`
- 以后 `index.html` 有改动，重新执行上面命令即可（或手动 push 到 GitHub 仓库）。

## 4. 本地预览

直接双击 `index.html`，或起任意静态服务器：

```bash
cd site && python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

## 5. 桌面端自动更新（来源 Gitee）

1. 打开 `build/gitee.json`，填 `owner` / `repo`（Gitee 用户名与仓库名），`notes` 可写本次更新说明。
2. 执行 `build/build_dmg.sh`：会同时输出 dmg 和 `build/release/core-<版本>-arm64.zip` + `update.json`（约 6MB，远小于 dmg）。
3. 发布更新包到 Gitee Release：
   ```bash
   GITEE_TOKEN=你的私人令牌 python3 build/release_gitee.py
   ```
   私人令牌需要仓库写权限，**不要**写进客户端。
4. 客户端启动后会自动检查该 Release 的 `update.json`，发现新版本就在侧边栏“设置”按钮旁显示“新版本”，随后自动下载核心包并显示百分比；下载完成后点击“安装”即备份、替换并重启，失败自动回滚。
5. 完整 dmg 仍放对象存储/网盘供新用户下载；Gitee Release 只放更新包，避免超过 100MB 附件上限。
