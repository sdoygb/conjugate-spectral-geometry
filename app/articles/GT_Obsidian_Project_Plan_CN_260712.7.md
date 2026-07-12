# 几何论 Obsidian Vault — 项目设计方案

**日期：** 260712.7  
**目标：** 将 137 篇手稿 + 355 个主库定理整合为 8 卷可导航、可交叉引用的 Obsidian 知识库

---

## 一、项目总体结构

```
geometric-theory/
│
├── .obsidian/                    # Obsidian 自动生成（主题/插件/热键）
│
├── 00_Home.md                    # 知识库首页（MOC）
├── 00_MasterIndex.md             # 全文章编号索引（按编号→文件路径）
├── 00_MasterTheoremIndex.md      # 主库定理索引（#1-#355 每一条）
├── 00_Glossary.md                # 术语表（几何论专用的~300个术语）
│
├── Vol-0_FromZero/               # 📘 第0卷：从零开始
│   ├── 00_MOC.md                 #   卷目录
│   ├── Ch1_ZeroPoint_S3.md       #   第1章：零维源点与S₃
│   ├── Ch2_SpectralExpansion.md  #   第2章：谱展开
│   ├── Ch3_ThreeAxioms.md        #   第3章：三公理
│   ├── Ch4_SixActions.md         #   第4章：六项作用量与九素互扼
│   ├── Ch5_ProductSphere.md      #   第5章：乘积球面谱刚性
│   ├── App_GroupTheory.md        #   附录A：群论速查
│   └── App_SpectralGeo.md        #   附录B：谱几何速查
│
├── Vol-1_GeoStructure/           # 📘 第1卷：几何结构
│   ├── 00_MOC.md
│   ├── Ch1_TriSplitBundle.md     #   第1章：三分切丛
│   ├── Ch2_Cl9Geometry.md        #   第2章：十方几何空间 Cl(9)
│   ├── Ch3_HolographicScreen.md  #   第3章：全息屏
│   ├── Ch4_ConstraintSection.md  #   第4章：约束截面
│   ├── Ch5_SpectralRigidity.md   #   第5章：谱刚性
│   ├── Ch6_PermeationFunc.md     #   第6章：渗透函数
│   └── App_CliffordAlg.md        #   附录：Clifford代数速查
│
├── Vol-2_DimensionBridge/        # 📘 第2卷：量纲桥
│   ├── 00_MOC.md
│   ├── Ch1_SpectralTriple.md     #   第1章：谱三元组 (A,H,D,J,γ)
│   ├── Ch2_LengthScale.md        #   第2章：长度标度重建
│   ├── Ch3_MassScale.md          #   第3章：质量标度重建
│   ├── Ch4_SpectralInterlock.md  #   第4章：谱互锁定理
│   ├── Ch5_GeoVelocity.md        #   第5章：几何速度代数
│   ├── Ch6_MultiPathVerify.md    #   第6章：多路径验证
│   └── App_NCG.md                #   附录：非交换几何基础
│
├── Vol-3A_InfoField/             # 📘 第3卷A：信息场动力学
│   ├── 00_MOC.md
│   ├── Ch1_InfoDensity.md        #   第1章：信息密度场
│   ├── Ch2_GraphModel.md         #   第2章：全息屏图论模型
│   ├── Ch3_Complexification.md   #   第3章：复化映射
│   ├── Ch4_Schrodinger.md        #   第4章：薛定谔方程层展
│   ├── Ch5_SlowingFactor.md      #   第5章：慢化因子
│   ├── Ch6_ObservationChain.md   #   第6章：观测映射链
│   └── App_InfoGeo.md            #   附录：信息几何基础
│
├── Vol-3B_CausalField/           # 📘 第3卷B：因果场动力学
│   ├── 00_MOC.md
│   ├── Ch1_Coordinates.md        #   第1章：坐标与因果推进
│   ├── Ch2_SteadyCirculation.md  #   第2章：稳态因果环流
│   ├── Ch3_CausalTime.md         #   第3章：因果时间
│   ├── Ch4_HardFreezing.md       #   第4章：硬方向冻结
│   ├── Ch5_CausalDepth.md        #   第5章：因果深度 N_cause=10
│   └── App_Ergodic.md            #   附录：遍历理论基础
│
├── Vol-3C_MField/                # 📘 第3卷C：M场动力学
│   ├── 00_MOC.md
│   ├── Ch1_MFieldNormal.md       #   第1章：M场法向结构
│   ├── Ch2_MassGeneration.md     #   第2章：质量生成动力学
│   ├── Ch3_BreathingMode.md      #   第3章：呼吸模式
│   ├── Ch4_ThreeGenerations.md   #   第4章：三代轻子质量
│   ├── Ch5_PhotonZeroMass.md     #   第5章：光子零质量定理
│   └── App_MassFormulas.md       #   附录：质量公式速查表
│
├── Vol-4_CoupledFields/          # 📘 第4卷：三场耦合
│   ├── 00_MOC.md
│   ├── Ch1_InfoUnifiedDynamics.md #  第1章：信息场统一动力学
│   ├── Ch2_CI_Coupling.md         #  第2章：C-I耦合
│   ├── Ch3_MC_Coupling.md         #  第3章：M-C耦合
│   ├── Ch4_MI_Coupling.md         #  第4章：M-I耦合
│   ├── Ch5_FullyCoupled.md        #  第5章：三场完全耦合
│   ├── Ch6_TimeScaleSeparation.md #  第6章：时间尺度分离
│   └── App_PDESetup.md            #  附录：偏微分方程设定
│
├── Vol-5_StandardModel/          # 📘 第5卷：标准模型几何重建
│   ├── 00_MOC.md
│   ├── Ch1_GaugeGroupOrigin.md   #   第1章：规范群几何根源
│   ├── Ch2_ThreeGenerations.md   #   第2章：三代拓扑必然性
│   ├── Ch3_QuarkMassSpectrum.md  #   第3章：夸克质量谱
│   ├── Ch4_LeptonMassSpectrum.md #   第4章：轻子质量谱
│   ├── Ch5_CouplingUnification.md #  第5章：耦合常数统一
│   ├── Ch6_Confinement.md        #   第6章：夸克禁闭拓扑证明
│   ├── Ch7_WeakMixingAngle.md    #   第7章：弱混合角
│   └── App_StandardModel.md      #   附录：标准模型对照表
│
├── Vol-6_GravityCosmo/           # 📘 第6卷：引力与宇宙学
│   ├── 00_MOC.md
│   ├── Ch1_GravityUnification.md #   第1章：引力统一
│   ├── Ch2_DarkMatterFalsified.md #  第2章：暗物质证伪
│   ├── Ch3_DarkEnergyFalsified.md #  第3章：暗能量证伪
│   ├── Ch4_CMB.md                 #  第4章：CMB声学峰
│   ├── Ch5_BlackHole.md          #   第5章：黑洞与信息悖论
│   ├── Ch6_EarlyUniverse.md      #   第6章：早期宇宙
│   ├── Ch7_Nucleosynthesis.md    #   第7章：原初核合成
│   └── App_CosmoConst.md         #   附录：宇宙学常数对照
│
├── Vol-7_ObserverBootstrapping/  # 📘 第7卷：观测者自举
│   ├── 00_MOC.md
│   ├── Ch1_UnitSelection.md      #   第1章：谱单位选择定理
│   ├── Ch2_SpectralConditions.md #   第2章：观测者五个谱条件
│   ├── Ch3_L8_Freedom.md         #   第3章：第八级不可计算自由度
│   ├── Ch4_AngleLocking.md       #   第4章：角度唯一锁定
│   ├── Ch5_EightStepLoop.md      #   第5章：八步自举闭环
│   ├── Ch6_ExternalityEliminated.md # 第6章：外部性消解
│   └── App_SelfReference.md      #   附录：自我指涉逻辑基础
│
├── Vol-8_Predictions/            # 📘 第8卷：实验预言与检验
│   ├── 00_MOC.md
│   ├── Ch1_ProtonDecay.md        #   第1章：质子衰变
│   ├── Ch2_NeutrinoMass.md       #   第2章：中微子绝对质量
│   ├── Ch3_Superconductivity.md  #   第3章：超导Tc几何公式
│   ├── Ch4_NuclearFusionEngine.md #  第4章：核聚变发动机
│   ├── Ch5_NoMonopole.md         #   第5章：磁单极子不存在
│   ├── Ch6_SuperconductorScreen.md # 第6章：超导候选材料筛选
│   ├── Ch7_QuantumCorrections.md #   第7章：量子修正
│   └── App_ExperimentCompare.md  #   附录：实验数据对照表
│
├── Vol-Applications/             # 📘 应用卷（跨学科）
│   ├── 00_MOC.md
│   ├── Biology/                  #   生物应用（DNA，经络，进化等）
│   ├── Chemistry/                #   化学应用（原子生成，分子生成）
│   ├── Engineering/              #   工程应用（核聚变发动机，超导筛选）
│   ├── Consciousness/            #   意识论（三界原理，中阴身）
│   └── Mathematics/              #   数学应用（黎曼猜想，杨-米尔斯）
│
├── Archive/                      # 旧版手稿归档
│   └── (按日期归档的旧版本)
│
├── Templates/                    # Obsidian 模板
│   ├── t_Chapter.md              #   章节模板
│   ├── t_Definition.md           #   定义卡片模板
│   ├── t_Theorem.md              #   定理卡片模板
│   └── t_Paper_Note.md           #   阅读笔记模板
│
└── Attachments/                  # 附件（图片、PDF等）
```

---

## 二、核心导航文件设计

### 2.1 首页 `00_Home.md`

```markdown
# 几何论 — Geometric Theory

> **几何是宇宙的语言。**  
> 三公理 → 355个已验证定理 → 完整的物理世界重建

```

| 卷号 | 卷名 | 核心内容 | 状态 |
|:---:|:---|:---|:---:|
| 0 | [[Vol-0_FromZero/00_MOC\|从零开始]] | 三公理→谱展开→乘积球面 | ✅ 可发布 |
| 1 | [[Vol-1_GeoStructure/00_MOC\|几何结构]] | 三分切丛→全息屏→约束截面 | ✅ 可发布 |
| 2 | [[Vol-2_DimensionBridge/00_MOC\|量纲桥]] | 谱三元组→物理常数重建 | ✅ 可发布 |
| 3A | [[Vol-3A_InfoField/00_MOC\|信息场动力学]] | 扩散→复化→量子力学层展 | ✅ 可发布 |
| 3B | [[Vol-3B_CausalField/00_MOC\|因果场动力学]] | 稳态因果环流→Lyapunov指数 | ⚠️ 需整理 |
| 3C | [[Vol-3C_MField/00_MOC\|M场动力学]] | 质量生成→呼吸模式→三代 | ⚠️ 需整理 |
| 4 | [[Vol-4_CoupledFields/00_MOC\|三场耦合]] | C-M-I完全耦合方程组 | ⚠️ 需整理 |
| 5 | [[Vol-5_StandardModel/00_MOC\|标准模型重建]] | 规范群→三代→质量谱→耦合常数 | ✅ 可发布 |
| 6 | [[Vol-6_GravityCosmo/00_MOC\|引力与宇宙学]] | 引力统一→暗物质证伪→CMB | ✅ 可发布 |
| 7 | [[Vol-7_ObserverBootstrapping/00_MOC\|观测者自举]] | 谱单位选择→第八级→自举闭环 | ⏳ 定理化中 |
| 8 | [[Vol-8_Predictions/00_MOC\|实验预言]] | 质子衰变→超导→核聚变引擎 | ⚠️ 需补充 |
| A | [[Vol-Applications/00_MOC\|跨学科应用]] | 生物/化学/工程/意识/数学 | ⚠️ 外展卷 |

```

### 2.2 卷 MOC 模板

```markdown
# 📘 第X卷：卷名

> **卷描述：** 一句话概述

| 章 | 标题 | 覆盖手稿 | 主库定理 |
|:--:|:---|:---|:---:|
| 1 | [[Ch1_xxx\|第1章：xxx]] | 0.x.x, 0.x.y | #N, #M |
| 2 | ... | ... | ... |

#### 阅读路径建议
- **从第0卷开始** → 如果读者需要从公理理解
- **直接读本卷** → 如果读者有群论/微分几何基础
- **搭配第X卷** → [[xxx]]

#### 对应手稿
- `[[0.x.x]]` → 原始手稿
- `[[0.x.y]]` → 补充手稿
```

### 2.3 文件命名规则

```
[卷号]_[章号]_[英文短标题]_[语言]_[日期].md
```

| 元素 | 规则 | 示例 |
|:---|:---|:---|
| 卷号 | `Vol-N` 或 `Vol-NA/NB/NC` | `Vol-0`, `Vol-3A` |
| 章号 | `ChN` | `Ch1` |
| 短标题 | PascalCase, ≤4词 | `ZeroPoint_S3` |
| 语言 | `CN` 或 `EN` | `CN` |
| 日期 | 版本号 | `260712` |

**示例：** `Vol-0_Ch1_ZeroPoint_S3_CN_260712.md`

### 2.4 YAML Front Matter 设计

每篇文章头部：

```yaml
---
title: "第1章：零维源点与S₃"
volume: 0
chapter: 1
aliases:
  - "零维源点"
  - "S₃"
tags:
  - vol-0
  - foundation
  - group-theory
sources: 
  - "手稿 [[0.0.0]]"
theorems:
  - "#1"
  - "#2"
status: "published"  # published | drafting | pending
date: 260712
---
```

---

## 三、双链引用系统设计

### 3.1 四种引用方式

| 引用类型 | 语法 | 渲染效果 | 使用场景 |
|:---|:---|:---|:---|
| 章引用 | `[[Vol-0_Ch1_ZeroPoint\|§0.1]]` | 可点击跳转 | 卷内交叉引用 |
| 定理引用 | `[[#定理3.1\|#276]]` | 可查看定理详情 | 引用已验证主库定理 |
| 手稿引用 | `[[0.0.0\|手稿0.0.0]]` | 可查看原始手稿 | 追溯原始推导 |
| 术语引用 | `[[三分切丛\|术语]]` | 悬停显示定义 | 首次出现术语时 |

### 3.2 标签系统

```
#vol-0          # 第0卷
#vol-1          # 第1卷
...
#theorem        # 定理卡片
#definition     # 定义卡片
#lemma          # 引理卡片
#open-question  # 开放问题
#proof          # 证明过程
#conjecture     # 猜想
#experiment     # 实验预测
```

---

## 四、实施路线图

### 第一阶段：骨架搭建（约2-3天）
| 步骤 | 内容 | 预计产出 |
|:---|:---|:---:|
| 1 | 创建目录结构 | 12个卷文件夹 + Templates + Attachments |
| 2 | 写首页 `00_Home.md` | 知识库入口 |
| 3 | 写 `00_MasterIndex.md` | 137篇文章编号→路径映射 |
| 4 | 写 `00_MasterTheoremIndex.md` | 355个定理的完整索引 |
| 5 | 写 `00_Glossary.md` | ~300个术语的全表 |
| 6 | 写 12 个卷的 `00_MOC.md` | 每卷目录和阅读路径 |

### 第二阶段：核心卷转换为正式论文（约1-2周/卷）
| 顺序 | 卷 | 优先级 | 理由 |
|:---:|:---|:---:|:---|
| 1 | **第0卷** 从零开始 | 🥇 | 纯数学，最短，最快成形 |
| 2 | **第5卷** 标准模型 | 🥇 | 物理学家最感兴趣 |
| 3 | **第2卷** 量纲桥 | 🥇 | 最原创、最关键 |
| 4 | **第1卷** 几何结构 | 🥈 | 基础框架 |
| 5 | **第6卷** 引力宇宙学 | 🥈 | 暗物质替代最震撼 |
| 6 | **第3卷ABC** 动力学 | 🥉 | 需前面打好基础 |
| 7 | **第4卷** 三场耦合 | 🥉 | 数学最复杂 |
| 8 | **第7卷** 观测者自举 | 🏆 | 理论最高潮 |
| 9 | **第8卷** 预言检验 | 📋 | 随时可补充 |
| 10 | **应用卷** | 📋 | 跨学科拓展 |

### 第三阶段：持续维护
- 主库有新定理入库 → 更新 `00_MasterTheoremIndex.md`
- 有新推导 → 更新对应章节
- 实验验证了一则预言 → 更新 `Vol-8_Predictions`
- 发现推导错误 → 更新章节+在开头标注修正

---

## 五、与当前文件系统的关系

当前系统的 `articles/` 目录下存放的是 **原始工作手稿**（137篇，编号0.0.x, 0.x, 1-79）。

Obsidian Vault 的定位是 **正式论文**，不是原始手稿的复制品：

```
articles/  ← 原始工作手稿（编号制，带版本号）
    ↓ 整合、重写、精简、交叉引用
geometric-theory/  ← Obsidian知识库（论文制，分卷分章）
```

两者之间的关系：每一篇 Obsidian 论文在 YAML Front Matter 中标注 `sources: ["手稿 [[0.0.0]]"]`，保证可追溯。

---

## 六、工具与插件建议

| 插件 | 用途 |
|:---|:---|
| **Dataview** | 按标签/状态自动生成动态索引表 |
| **Graph View** | 可视化137篇文章和355个定理的引用网络 |
| **Excalidraw** | 嵌入数学图示（全息屏结构、三分切丛图等） |
| **LaTeX Suite** | 快速输入数学公式 |
| **Citations** | 主库定理引用管理 |
| **Templater** | 章节模板自动插入 |
| **Kanban** | 追踪每卷写作进度 |
| **Publish** | 可选，发布为静态网站 |

---

**设计方案结束。确认后开始实施。**
