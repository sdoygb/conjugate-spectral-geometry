# geometry-knowledge

**几何论（共扼谱几何 CSG）知识库插件** —— 用于 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（DSH）。

纯离线 BM25 检索：**166 篇文章全文 + 3222 个分块 + 860 条主库真理层**，不依赖任何外部 API、嵌入模型或网络，安装即用、零运行时依赖。

## 几何论是什么

几何论（共扼谱几何，Conjugate Spectral Geometry）是一套尝试通过**少量而合理的实验数据锚定**，正确描述这个物理世界的几何理论体系。它不宣称能从少量公理和假设必然地推导出整个物理世界。

- **公理起点**：零之动（非平凡自映射 δ 持续产生区分）+ 总作用量为零（S_total = 0）
- **推导主干**：δ → Clifford 代数 → Bott 周期（δ⁸ = 2π Berry 相位）→ E₈ 偶幺模格 → 结构常数 {2,3,5} → 乘子序列 → Born 法则代数导出 → M₅ Birkhoff 矩阵不动点 → **α⁻¹ ≈ 137.036** → 三扇区物理（ℳ物质 / 𝒞因果 / ℐ信息）→ 标准模型重建 → 引力与宇宙学 → 预言检验
- **11 卷 166 篇文章、320 个定理**，覆盖从量子力学数学结构、夸克质量谱、中微子 Majorana 本质，到暗物质替代、黑洞信息悖论、CMB、量子纠错码等主题

本插件把整套知识库做成 DSH 的原生工具集，让 Agent 在会话中直接检索原文与已验证定理，并强制标注文章编号与章节引用。

## 提供的工具

| 工具 | 说明 |
| --- | --- |
| `geo_list` | 文章清单（编号、标题、文件名、分块数），可按系列过滤（如 `series="10."` 只看应用篇） |
| `geo_search` | BM25 语义检索：`scope=articles` 检索 3222 个文章分块；`scope=truth` 检索 860 条主库真理层 |
| `geo_read` | 读取文章：默认结构摘要视图（元信息+章节目录+核心结论速览），`section` 关键词精确定位章节，`whole=true` 整篇；带翻页防护（顺序翻页警告 + 单篇 25000 字符上限） |
| `geo_calc` | 精确数学计算（纯 JS 安全求值，零依赖）：四则/幂/三角/对数/开方，多行赋值，会话内中间变量跨调用保留 |
| `geo_truth` | 主库真理层检索（860 条已验证定理，含永久编号 #N、公式名、证明摘要） |

## 安装

### npm 安装（推荐，免构建授权）

```sh
# 安装并自动激活：包声明了 dsh.bundle，会作为 profile 层追加进 dsh.profile.bundles
dsh plugin --profile web add geometry-knowledge

# 重启后四个 geo_* 工具即注入会话
dsh web
```

### tarball 安装

```sh
pnpm pack            # 生成 geometry-knowledge-0.1.4.tgz
dsh plugin --profile web add ./geometry-knowledge-0.1.4.tgz
```

### Git 安装

```sh
dsh plugin --profile web add github:sdoygb/conjugate-spectral-geometry#<commit-sha>
```

Git 安装拉取源码，pnpm 会运行 `prepare` 脚本构建 `dist/`；首次安装需在 profile 的 `pnpm-workspace.yaml` 中为包键添加 `allowBuilds` 授权（dsh 会打印确切写法）。

## 使用示例

```text
geo_list series="7."          → 标准模型重建卷的全部文章清单
geo_search "弱混合角"         → 检索弱混合角相关分块
geo_search "谱刚性" scope=truth → 检索主库已验证真理
geo_read "10.8" section="Strouhal" → 读取 10.8 的 Strouhal 数推导章节
geo_read "7.5"                → 7.5 的结构摘要视图（默认，省 token）
geo_calc "57.93+26.16+5.91"   → 90（精确计算）
geo_calc "D=10/7821; D*2"     → 0.00256（会话内变量保留）
geo_read "7.5" whole=true     → 读取整篇 7.5 弱混合角
```

检索提示：先提取文章中的精确术语（如 θ_M、N_dec、η_K、Strouhal、谱刚性、弱混合角、Kolmogorov）效果最佳。

## 工作目录数据覆盖（geo-data，安装者改文章的正道）

安装者想改文章，**不需要改包**：把已装包的 `data/` 完整拷贝到**工作目录**的 `geo-data/` 子目录，插件启动时自动检测并优先使用：

```sh
# 1. 拷贝一份完整数据副本到工作目录（一次即可）
cp -r ~/.dsh/profiles/web/node_modules/geometry-knowledge/data  ./geo-data

# 2. 自由编辑副本里的文章（geo_read 立即读到新内容）
edit ./geo-data/articles/10.8_几何流体力学_CN_260808.md

# 3. 照常启动，插件自动使用 ./geo-data/
dsh web
```

- **独立性**：`geo-data/` 是你的副本，升级/重装插件不影响你的修改
- **数据来源优先级**：插件配置 `dataDir` > 环境变量 `GEO_DATA_DIR` > 工作目录 `./geo-data/` > 包内内置数据（启动日志会打印实际数据源）
- **限制**：修改 `.md` 只影响 `geo_read`（全文阅读）；`geo_search` 的分块索引（articles.jsonl）是导出时的静态快照，需按上文"数据与构建"流程重新导出才会更新

## 数据与构建

- `data/` 由 `scripts/export_dsh_index.py` 从几何论主库导出；运行 `pnpm export` 重新生成
- `dist/` 由 TypeScript 编译：`pnpm build`
- 冒烟测试：`pnpm smoke`

## 引用规范

所有检索结果必须标注文章编号（article_id/fname）与章节；真理层条目优先引用永久编号 #N。

## 许可证

MIT
