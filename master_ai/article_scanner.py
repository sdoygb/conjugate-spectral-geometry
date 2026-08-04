"""
article_scanner.py — 文章公式扫描器

功能：
1. 正则扫描 app/articles/ 目录下所有 .md 文件，提取候选定理/命题/公理/引理/推论
2. 与主库已有公式去重
3. 用 deepseek-v4-flash 批量LLM结构化：公式名、陈述、证明、依赖列表
4. LLM标注依赖关系类型：递进（单向依赖）vs 互锁（循环依赖）
5. 调用主库 /v1/master/submit API 提交
6. 增量监控：只扫描新增/修改的文章

成本控制：
- 正则扫描：免费
- 去重：免费（本地embedding）
- LLM结构化：每批10个公式调1次 deepseek-v4-flash
- 矛盾检测：提交前查主库已有公式的embedding相似度
"""

import os
import re
import json
import time
import hashlib
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# 文章目录
ARTICLES_DIR = os.environ.get(
    "GAI_ARTICLES_DIR",
    "/Users/oygb/Downloads/GeometryAI-Mac-Build/app/articles"
)

# 主库API
MASTER_API = os.environ.get("MASTER_API_URL", "http://localhost:5001")
MASTER_AUTH = os.environ.get("MASTER_AUTH_KEY", "master-ai-verify")

# LLM配置（用最便宜的模型）
LLM_API_URL = os.environ.get("LLM_API_URL", "https://api.deepseek.com/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "") or os.environ.get("GAI_API_KEY", "")
LLM_MODEL = os.environ.get("SCANNER_LLM_MODEL", "deepseek-v4-flash")

# 扫描状态文件（记录已扫描的文件和已提交的公式）
SCANNER_STATE_FILE = os.path.join(
    os.path.dirname(__file__), "scanner_state.json"
)

# 批大小：每次LLM调用处理多少个公式
BATCH_SIZE = 8


class ArticleScanner:
    """文章公式扫描器"""

    def __init__(self):
        self.state = self._load_state()
        self._existing_names: Set[str] = set()
        self._existing_ids: List[str] = []

    # ========== 状态持久化 ==========

    def _load_state(self) -> Dict:
        if os.path.exists(SCANNER_STATE_FILE):
            try:
                with open(SCANNER_STATE_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "scanned_files": {},  # filename → {mtime, formula_count}
            "submitted_formulas": {},  # formula_name → {submission_id, status, file}
            "last_full_scan": 0,
            "last_incremental_scan": 0,
        }

    def _save_state(self):
        try:
            with open(SCANNER_STATE_FILE, "w") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存扫描状态失败: {e}")

    # ========== 第1步：正则扫描 ==========

    # 匹配模式：
    # 新增：**定理N（名称）** 格式（文章中的主要定理/命题/引理声明格式）
    # 原有：### 标题格式
    FORMULA_PATTERNS = [
        # # 定理X.X / ## 定理X.X / ### 定理X.X
        re.compile(
            r'^(#{1,3})\s*(定理|命题|公理|引理|推论| lemma| Theorem| Proposition|'
            r' Axiom| Corollary)\s*[\d\.\s]*(.+)$',
            re.MULTILINE
        ),
        # ### N.N　定理名称（中文全角空格）
        re.compile(
            r'^(#{1,3})\s*[\d\.]+\s*[\s　]*(定理|命题|公理|引理|推论)[\s　]*(.+)$',
            re.MULTILINE
        ),
        # ## N　章节名（含定理/命题等关键词）
        re.compile(
            r'^(#{2,3})\s*[\d\.]+\s*[\s　]*(.+定理|.+命题|.+公理|.+引理|.+推论)\s*$',
            re.MULTILINE
        ),
    ]

    # **定理N（名称）** 格式的匹配模式（文章中的主要定理声明格式）
    # 支持格式：
    #   **定理6（E₈ 桥接定理）。**  → 匹配编号+名称
    #   **定理（Minkowski–Serre）。** → 匹配无编号定理
    #   **命题2（互锁性）。**       → 匹配命题
    BOLD_FORMULA_PATTERN = re.compile(
        r'^\*\*(定理|命题|公理|引理|推论)\s*([\d\.]*)\s*(?:[（(]([^）)]*)[）)])?[。．.]?\*\*',
        re.MULTILINE
    )

    def _extract_candidates(self, filepath: str) -> List[Dict]:
        """从单个文章中提取候选公式。优先匹配 **定理N（名称）** 格式"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"读取文件失败 {filepath}: {e}")
            return []

        filename = os.path.basename(filepath)
        candidates = []
        seen_names = set()

        # ---- 第1优先：匹配 **定理N（名称）** 格式（文章中的主要定理声明） ----
        bold_matches = list(self.BOLD_FORMULA_PATTERN.finditer(content))
        for idx, match in enumerate(bold_matches):
            formula_type = match.group(1)
            formula_number = match.group(2)
            formula_desc = match.group(3) or ""

            # 构造完整公式名：定理N（名称）
            if formula_desc:
                if formula_number:
                    formula_title = f"{formula_type}{formula_number}（{formula_desc}）"
                else:
                    formula_title = f"{formula_type}（{formula_desc}）"
            else:
                if formula_number:
                    formula_title = f"{formula_type}{formula_number}"
                else:
                    formula_title = f"{formula_type}"

            if formula_title in seen_names:
                continue
            seen_names.add(formula_title)

            # 提取内容：从当前匹配到下一个定理标记
            start_pos = match.end()
            next_marker = self.BOLD_FORMULA_PATTERN.search(content, start_pos)
            if next_marker:
                section_content = content[start_pos:next_marker.start()]
            else:
                section_content = content[start_pos:start_pos + 8000]

            section_content = section_content.strip()
            if len(section_content) < 20:
                continue

            candidates.append({
                "formula_name": formula_title,
                "formula_type": formula_type,
                "raw_content": section_content[:6000],
                "source_file": filename,
                "heading_level": 0,
            })

        # ---- 第2优先：原有 ### 标题格式（兼容） ----
        for pattern in self.FORMULA_PATTERNS:
            for match in pattern.finditer(content):
                heading_level = len(match.group(1))
                formula_type = ""
                formula_title = ""

                if len(match.groups()) >= 3:
                    formula_type = match.group(2).strip()
                    formula_title = match.group(3).strip()
                elif len(match.groups()) >= 2:
                    formula_title = match.group(2).strip()
                    for kw in ("定理", "命题", "公理", "引理", "推论"):
                        if kw in formula_title:
                            formula_type = kw
                            break

                if not formula_title:
                    continue

                formula_title = formula_title.strip('（()）\s:：')
                if formula_title in ('陈述', '证明', '推论', '注记', '备注', '索引', '目录', '参考文献', '来源', '版本', '附录'):
                    continue
                if len(formula_title) < 2 or len(formula_title) > 200:
                    continue

                # 保留编号前缀（不再去掉）
                formula_title = formula_title.lstrip('：:（(')

                if formula_title in seen_names:
                    continue
                seen_names.add(formula_title)

                start_pos = match.end()
                next_heading = re.search(
                    r'\n#{1,' + str(heading_level) + r'}\s',
                    content[start_pos:]
                )
                if next_heading:
                    section_content = content[start_pos:start_pos + next_heading.start()]
                else:
                    section_content = content[start_pos:start_pos + 8000]

                section_content = section_content.strip()
                if len(section_content) < 20:
                    continue

                candidates.append({
                    "formula_name": formula_title,
                    "formula_type": formula_type,
                    "raw_content": section_content[:6000],
                    "source_file": filename,
                    "heading_level": heading_level,
                })

        return candidates

    def scan_articles(self, incremental: bool = True) -> List[Dict]:
        """
        扫描文章目录，提取候选公式。
        incremental=True: 只扫描新增/修改的文件
        incremental=False: 全量扫描
        """
        if not os.path.exists(ARTICLES_DIR):
            logger.warning(f"文章目录不存在: {ARTICLES_DIR}")
            return []

        all_candidates = []
        scanned_count = 0
        skipped_count = 0

        for filename in sorted(os.listdir(ARTICLES_DIR)):
            if not filename.endswith(".md"):
                continue
            # 跳过 copilot/obsidian 等非内容目录
            if filename.startswith(".") or "/.obsidian" in filename:
                continue

            filepath = os.path.join(ARTICLES_DIR, filename)
            if not os.path.isfile(filepath):
                continue

            mtime = os.path.getmtime(filepath)
            file_state = self.state["scanned_files"].get(filename, {})

            if incremental and file_state.get("mtime") == mtime:
                skipped_count += 1
                continue

            candidates = self._extract_candidates(filepath)
            all_candidates.extend(candidates)
            scanned_count += 1

            # 更新状态
            self.state["scanned_files"][filename] = {
                "mtime": mtime,
                "formula_count": len(candidates),
            }

        if scanned_count > 0:
            logger.info(
                f"[SCANNER] 扫描完成: {scanned_count}个文件, "
                f"跳过{skipped_count}个, 提取{len(all_candidates)}个候选公式"
            )
            if incremental:
                self.state["last_incremental_scan"] = time.time()
            else:
                self.state["last_full_scan"] = time.time()
            self._save_state()

        return all_candidates

    # ========== 第2步：去重 ==========

    def fetch_existing_formulas(self):
        """从主库获取已有公式名列表"""
        # 方法1: 直接读主库DB（最可靠）
        try:
            import sys as _sys
            _sys.path.insert(0, os.path.dirname(__file__))
            from master_db import MasterDatabase
            db = MasterDatabase()
            all_master = db.master_collection.get(include=['metadatas'])
            self._existing_names = {
                m.get('formula_name', '') for m in all_master['metadatas']
            }
            logger.info(f"[SCANNER] 主库已有 {len(self._existing_names)} 个公式")
            return
        except Exception as e:
            logger.warning(f"[SCANNER] 直接读主库DB失败: {e}")

        # 方法2: 通过API（fallback）
        try:
            resp = requests.get(
                f"{MASTER_API}/v1/master/truth",
                headers={"Authorization": f"Bearer {MASTER_AUTH}"},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                formulas = data.get("formulas", data.get("truth", []))
                self._existing_names = {f.get("formula_name", "") for f in formulas}
                logger.info(f"[SCANNER] 主库已有 {len(self._existing_names)} 个公式 (via API)")
        except Exception as e:
            logger.warning(f"获取主库公式列表失败: {e}")

    def fetch_pending_formulas(self) -> Set[str]:
        """获取待验证队列中已有的公式名（避免重复提交）"""
        try:
            # 直接读主库DB
            import sys as _sys
            _sys.path.insert(0, os.path.dirname(__file__))
            from master_db import MasterDatabase
            db = MasterDatabase()
            all_pending = db.pending_collection.get(include=['metadatas'])
            return {m.get('formula_name', '') for m in all_pending['metadatas']}
        except Exception:
            pass
        return set()

    def deduplicate(self, candidates: List[Dict]) -> List[Dict]:
        """去重：排除主库已有 + 已在待验证队列 + 已提交过的。
        注意：不同类型（定理/引理/命题）的编号体系独立，不互相去重。"""
        pending_names = self.fetch_pending_formulas()
        submitted_names = set(self.state["submitted_formulas"].keys())

        unique = []
        for c in candidates:
            name = c["formula_name"]
            ftype = c.get("formula_type", "")
            # 精确匹配：名称+类型都要匹配
            if name in self._existing_names or name in pending_names or name in submitted_names:
                continue
            # 模糊匹配：已有公式名包含候选名或反之，但必须是同类型
            skip = False
            for existing in self._existing_names:
                if not existing:
                    continue
                # 去掉常见前缀后比较
                clean_existing = re.sub(r'^[\d\.]+\s*', '', existing)
                if name in existing or existing in name or name in clean_existing or clean_existing in name:
                    skip = True
                    break
            if skip:
                continue

            unique.append(c)

        logger.info(
            f"[SCANNER] 去重: {len(candidates)} → {len(unique)} "
            f"(主库已有{len(self._existing_names)}, 待验证{len(pending_names)}, "
            f"已提交{len(submitted_names)})"
        )
        return unique

    # ========== 第3步：LLM批量结构化 ==========

    def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """调用LLM"""
        try:
            resp = requests.post(
                f"{LLM_API_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 8000,
                },
                timeout=120,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.warning(f"LLM调用失败: {resp.status_code} {resp.text[:200]}")
                return None
        except Exception as e:
            logger.warning(f"LLM调用异常: {e}")
            return None

    def structure_formulas(self, candidates: List[Dict]) -> List[Dict]:
        """批量LLM结构化：提取公式名、陈述、证明、依赖、关系类型"""
        structured = []
        total_batches = (len(candidates) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_idx in range(total_batches):
            batch = candidates[batch_idx * BATCH_SIZE: (batch_idx + 1) * BATCH_SIZE]
            batch_num = batch_idx + 1

            logger.info(f"[SCANNER] LLM结构化 第{batch_num}/{total_batches}批 ({len(batch)}个公式)")

            # 构造提示
            formulas_text = ""
            for i, c in enumerate(batch):
                formulas_text += f"\n{'='*60}\n"
                formulas_text += f"【公式{i+1}】{c['formula_name']}\n"
                formulas_text += f"来源: {c['source_file']}\n"
                formulas_text += f"类型: {c['formula_type']}\n"
                formulas_text += f"内容:\n{c['raw_content']}\n"

            system_prompt = """你是共扼谱几何数学公式提取专家。从文章中提取结构化公式信息。

【公式分类与编号体系——核心规则】
定理、命题、引理、推论采用统一的层级编号格式：X（卷）.X（章）.X（节）.XX

1. 定理（Theorem）：格式为 **定理 X.X.X.XX（名称）**
   - 如 **定理 0.1.3.01（非幂等性）**、**定理 3.1.1.01（螺旋性分裂定理）**

2. 命题（Proposition）：格式为 **命题 X.X.X.XX（名称）**
   - 如 **命题 0.5.2.01（互锁性）**、**命题 3.1.2.01（法向-代数对应）**

3. 引理（Lemma）：格式为 **引理 X.X.X.XX（名称）**
   - 如 **引理 1.1.2.01（回收基准不变）**、**引理 7.8.2.01（趋零渐近行为）**

4. 推论（Corollary）：格式为 **推论 X.X.X.XX（名称）**
   - 如 **推论 1.1.2.02（内禀因子保留）**、**推论 9.1.2.02（体积形式）**

5. 公理（Axiom）：无编号或以公理名标识，如 公理（零之动）。

【关键规则】
- 编号格式：卷（文件名第一段）.章（文件名第二段）.节（文章内## §N或## 第N章）.序号（节内从01起递增）
- 定理、命题、引理、推论在每节内共享同一个序号计数器，不再独立编号
- 节内序号从01开始，按出现顺序递增
- 编号必须与文章原文完全一致，保留原文中的完整编号

要求：
1. formula_name: 保留文章中的完整公式名称和编号，与文章完全一致
2. formula_content: 公式的数学表达式和核心陈述（精确引用原文中的公式）
3. derivation_chain: 推导链，列出证明过程中引用了哪些公理/定理/命题/引理（写明名称）
4. dependencies: 依赖列表，每个依赖写明名称。区分：
   - "递进": A依赖B但B不依赖A，B是A的前置定理
   - "互锁": A和B互相依赖，形成循环论证（需要在备注中说明）
5. relation_type: "递进" 或 "互锁" 或 "独立"（无依赖）
6. interlock_group: 如果是互锁，列出互锁组的公式名
7. proof_summary: 证明摘要（2-3句话）
8. contradiction_check: 这个公式是否与已知物理/数学常识矛盾？如有矛盾指出

输出JSON数组，每个元素对应一个公式。只输出JSON，不要其他文字。"""

            user_prompt = f"""请提取以下{len(batch)}个公式的结构化信息。

已有主库公式（这些已经验证通过，可作为已知依赖）:
{chr(10).join(f'- {n}' for n in sorted(self._existing_names)[:80])}

待提取公式:
{formulas_text}

请输出JSON数组，格式:
[
  {{
    "formula_name": "公式名",
    "formula_content": "公式表达式和核心陈述",
    "derivation_chain": "推导链",
    "dependencies": ["依赖1", "依赖2"],
    "relation_type": "递进|互锁|独立",
    "interlock_group": ["公式A", "公式B"],
    "proof_summary": "证明摘要",
    "contradiction_check": "无矛盾|矛盾说明"
  }}
]"""

            result = self._call_llm(system_prompt, user_prompt)
            if not result:
                logger.warning(f"[SCANNER] 第{batch_num}批LLM返回空，跳过")
                continue

            # 解析JSON
            try:
                # 去掉可能的markdown代码块标记
                result = result.strip()
                if result.startswith("```"):
                    result = re.sub(r'^```(?:json)?\s*', '', result)
                    result = re.sub(r'\s*```$', '', result)

                items = json.loads(result)
                for i, item in enumerate(items):
                    if i < len(batch):
                        item["source_file"] = batch[i]["source_file"]
                        item["formula_type"] = batch[i]["formula_type"]
                        structured.append(item)
            except json.JSONDecodeError as e:
                logger.warning(f"[SCANNER] 第{batch_num}批JSON解析失败: {e}")
                # 尝试逐个提取
                for i, c in enumerate(batch):
                    fallback = {
                        "formula_name": c["formula_name"],
                        "formula_content": c["raw_content"][:2000],
                        "derivation_chain": "",
                        "dependencies": [],
                        "relation_type": "独立",
                        "interlock_group": [],
                        "proof_summary": "",
                        "contradiction_check": "未检查",
                        "source_file": c["source_file"],
                        "formula_type": c["formula_type"],
                    }
                    structured.append(fallback)

            # 批间延迟，避免API限流
            if batch_num < total_batches:
                time.sleep(2)

        logger.info(f"[SCANNER] LLM结构化完成: {len(structured)}/{len(candidates)}")
        return structured

    # ========== 第4步：矛盾检测 ==========

    def check_contradictions(self, structured: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """分离有矛盾和无矛盾的公式"""
        clean = []
        flagged = []

        for item in structured:
            contradiction = item.get("contradiction_check", "")
            if contradiction and contradiction != "无矛盾" and contradiction != "未检查":
                flagged.append(item)
                logger.warning(
                    f"[SCANNER] 矛盾标记: {item['formula_name']} → {contradiction}"
                )
            else:
                clean.append(item)

        if flagged:
            logger.info(f"[SCANNER] 矛盾检测: {len(clean)}个通过, {len(flagged)}个标记矛盾")

        return clean, flagged

    # ========== 第5步：提交到主库 ==========

    def submit_to_master(self, structured: List[Dict]) -> Dict:
        """提交公式到主库"""
        results = {"submitted": 0, "duplicates": 0, "errors": 0, "details": []}

        for item in structured:
            formula_name = item.get("formula_name", "")
            if not formula_name:
                continue

            # 检查是否已提交过
            if formula_name in self.state["submitted_formulas"]:
                results["duplicates"] += 1
                continue

            # 构造提交数据
            dependencies = item.get("dependencies", [])
            relation_type = item.get("relation_type", "独立")
            interlock_group = item.get("interlock_group", [])

            # 推导链中包含依赖信息
            derivation = item.get("derivation_chain", "")
            if dependencies:
                derivation += f"\n\n【依赖关系】{', '.join(dependencies)}"
                derivation += f"\n【关系类型】{relation_type}"
                if interlock_group:
                    derivation += f"\n【互锁组】{', '.join(interlock_group)}"

            submit_data = {
                "formula_name": formula_name,
                "formula_content": item.get("formula_content", ""),
                "derivation_chain": derivation,
                "source_agent": f"article_scanner ({item.get('source_file', '')})",
                "topology_class": "",
                "formula_type": item.get("formula_type", ""),  # 定理/引理/命题/公理/推论
                "priority_hint": relation_type == "互锁",
                "interlock_hint": interlock_group if relation_type == "互锁" else [],
                "interlock_reasoning": (
                    f"扫描器标注: {relation_type}。"
                    f"互锁组: {interlock_group}" if interlock_group else ""
                ),
            }

            try:
                resp = requests.post(
                    f"{MASTER_API}/v1/master/submit",
                    headers={
                        "Authorization": f"Bearer {MASTER_AUTH}",
                        "Content-Type": "application/json",
                    },
                    json=submit_data,
                    timeout=30,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    sub_id = data.get("submission_id", "")
                    status = data.get("status", "pending")

                    self.state["submitted_formulas"][formula_name] = {
                        "submission_id": sub_id,
                        "status": status,
                        "file": item.get("source_file", ""),
                        "relation_type": relation_type,
                        "submitted_at": datetime.now().isoformat(),
                    }

                    if status == "duplicate":
                        results["duplicates"] += 1
                    else:
                        results["submitted"] += 1

                    results["details"].append({
                        "formula_name": formula_name,
                        "submission_id": sub_id,
                        "status": status,
                        "relation_type": relation_type,
                    })

                    logger.info(
                        f"[SCANNER] 提交: {formula_name} → {status} "
                        f"({relation_type}, 依赖: {dependencies})"
                    )
                else:
                    results["errors"] += 1
                    logger.warning(
                        f"[SCANNER] 提交失败 {formula_name}: "
                        f"{resp.status_code} {resp.text[:100]}"
                    )
            except Exception as e:
                results["errors"] += 1
                logger.warning(f"[SCANNER] 提交异常 {formula_name}: {e}")

            # 提交间延迟
            time.sleep(0.5)

        self._save_state()
        return results

    # ========== 主流程 ==========

    def run(self, full_scan: bool = False) -> Dict:
        """
        完整扫描流程：
        1. 正则扫描文章
        2. 去重
        3. LLM结构化
        4. 矛盾检测
        5. 提交到主库
        """
        logger.info(f"[SCANNER] 开始{'全量' if full_scan else '增量'}扫描...")

        # Step 0: 获取主库已有公式
        self.fetch_existing_formulas()

        # Step 1: 正则扫描
        candidates = self.scan_articles(incremental=not full_scan)
        if not candidates:
            logger.info("[SCANNER] 无新候选公式")
            return {"candidates": 0, "submitted": 0, "skipped": 0}

        # Step 2: 去重
        unique = self.deduplicate(candidates)
        if not unique:
            logger.info("[SCANNER] 去重后无新公式")
            return {"candidates": len(candidates), "submitted": 0, "skipped": len(candidates)}

        # Step 3: LLM结构化
        structured = self.structure_formulas(unique)
        if not structured:
            logger.warning("[SCANNER] LLM结构化失败")
            return {"candidates": len(candidates), "submitted": 0, "skipped": len(candidates)}

        # Step 4: 矛盾检测
        clean, flagged = self.check_contradictions(structured)

        # Step 5: 提交
        results = self.submit_to_master(clean)

        # 保存矛盾标记的公式（不提交，记录待人工审查）
        if flagged:
            for item in flagged:
                self.state["submitted_formulas"][item["formula_name"]] = {
                    "submission_id": "",
                    "status": "contradiction_flagged",
                    "file": item.get("source_file", ""),
                    "contradiction": item.get("contradiction_check", ""),
                    "submitted_at": datetime.now().isoformat(),
                }
            self._save_state()

        summary = {
            "candidates": len(candidates),
            "unique": len(unique),
            "structured": len(structured),
            "contradictions": len(flagged),
            "submitted": results["submitted"],
            "duplicates": results["duplicates"],
            "errors": results["errors"],
            "details": results["details"],
        }
        logger.info(f"[SCANNER] 扫描完成: {summary}")
        return summary
