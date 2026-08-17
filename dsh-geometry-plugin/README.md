# geometry-knowledge

几何论（共扼谱几何，CSG）知识库插件，用于 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（DSH）。

纯离线 BM25 检索：**166 篇文章全文 + 3224 个分块 + 860 条主库真理层**，不依赖任何外部 API、嵌入模型或网络。

## 提供的工具

| 工具 | 说明 |
| --- | --- |
| `geo_list` | 文章清单（按编号/系列过滤） |
| `geo_search` | BM25 语义检索（文章分块 `scope=articles` / 主库真理层 `scope=truth`） |
| `geo_read` | 按文章编号或文件名读取原文（`section` 定位章节，`whole=true` 整篇） |
| `geo_truth` | 主库真理层检索（860 条已验证定理，永久编号 #N） |

## 安装（npm 发布后）

```sh
# 安装并自动激活（包声明了 dsh.bundle，会作为 profile 层追加进 dsh.profile.bundles）
dsh plugin --profile web add geometry-knowledge

# 重启 web profile 后，四个 geo_* 工具即注入会话
dsh web
```

## 安装（本地 checkout / tarball）

```sh
# 从本地目录安装（dsh plugin 转发给 pnpm，路径规格锚定到调用目录）
dsh plugin --profile web add ./dsh-geometry-plugin

# 或从 tarball
pnpm pack            # 生成 geometry-knowledge-0.1.0.tgz
dsh plugin --profile web add ./geometry-knowledge-0.1.0.tgz
```

## 安装（Git 托管）

```sh
dsh plugin --profile web add github:<你的用户名>/conjugate-spectral-geometry#<commit-sha>
```

Git 安装拉取的是源码，pnpm 会运行 `prepare` 脚本构建出 `dist/`；首次安装需要在
profile 的 `pnpm-workspace.yaml` 中为包键添加 `allowBuilds` 授权后重试（dsh 会打印确切写法）。

## 数据与构建

- `data/` 由 `scripts/export_dsh_index.py` 从几何论主库（app/articles + app/chroma_db）导出；
  运行 `pnpm export` 重新生成。
- `dist/` 由 TypeScript 源码编译：`pnpm build`。
- 冒烟测试：`pnpm smoke`。

## 引用规范

所有检索结果必须标注文章编号（article_id/fname）与章节；真理层条目优先引用永久编号 #N。
