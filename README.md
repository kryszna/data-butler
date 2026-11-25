# 数据管家下载页（静态）

仿 WorkBuddy 官网风格的单文件静态下载页，无后端、无外部依赖。
页面托管在 **GitHub Pages**，安装包放在 **GitHub Releases**。

当前线上地址：https://kryszna.github.io/data-butler/

## 文件

- `index.html` — 全部内容（HTML + CSS + JS 内联）
- `deploy_github.py` — 纯 GitHub API 部署脚本
- `README.md` — 本说明

## 当前状态：仅部署页面

`index.html` 里 `DOWNLOAD_READY = false`，下载按钮显示“即将上线”，点击只弹提示、不跳转。
这是为了避免跳转到还不存在的 Release 页。等安装包上传到 GitHub Releases 后，把这一行改成 `true` 即可启用真实下载。

## 1. 填写 GitHub 仓库信息

打开 `index.html`，找到底部的 `var GITHUB = {...}` 配置块：

```js
var GITHUB = {
  owner : "kryszna",      // GitHub 用户名
  repo  : "data-butler",  // 仓库名
  tag   : "v1.0.0",       // Release 标签
  file  : "数据管家.dmg"   // 附件文件名
};
```

- 页面默认跳转到 `<owner>/<repo>/releases` 列表页（最稳妥，附件改动不用改页面）。
- 若想点按钮直接下载附件，把 `pick()` 里的 `releaseUrl()` 改成 `directUrl()`。

## 2. 上传安装包到 GitHub Releases

1. 打开 https://github.com/kryszna/data-butler/releases
2. 新建 Release，标签填 `v1.0.0`（需与配置里的 `tag` 一致）。
3. 上传 `数据管家.dmg` 作为附件并发布。
4. 把 `index.html` 里的 `DOWNLOAD_READY` 改为 `true`，重新执行部署脚本。

说明：GitHub Release 单文件上限约 2GB，当前 dmg 约 2.0GB 可直接上传；若超限可改用外链并修改 `directUrl()`。

## 3. 部署 / 更新页面

```bash
GITHUB_TOKEN=你的令牌 python3 site/deploy_github.py
```

- classic token 勾选 `repo`；细粒度令牌需要创建仓库权限 + 对应仓库 `Contents: write`。
- 脚本全程使用 GitHub API 提交文件，不调用 git、不写本地 remote，令牌不会落盘，日志和报错自动打码。
- 仓库不存在会自动创建；已存在则覆盖 `main` 分支内容，并通过 API 开启 Pages。
- 访问地址：`https://kryszna.github.io/data-butler/`
- 以后 `index.html` 有改动，重新执行上面命令即可。

## 4. 本地预览

直接双击 `index.html`，或起任意静态服务器：

```bash
cd site && python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```
