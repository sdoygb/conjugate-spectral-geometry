"""
prompts.py - 从 geometry_ai_server_v5_12.py 提取的提示词和教学系统模块

包含：
1. TeachingSystem 类（教学系统）
2. build_system_prompt 函数
3. check_response_quality 函数
4. check_correction_applied 函数
"""

import os
import logging
from typing import List, Tuple, Dict, Optional, Any

logger = logging.getLogger(__name__)

# 从 config 导入（主文件中定义的常量）
from config import (
    SHOUYI_PHILOSOPHY,
    GEOMETRY_KNOWLEDGE,
    TEACH_CORRECTION_SIMILARITY_THRESHOLD,
    TEACH_MAX_RECENT_CORRECTIONS,
    TEACH_ANTIPATTERN_SIMILARITY_THRESHOLD,
    UPLOAD_FOLDER,
)

# 从 models 导入
from models import _get_personal_db_summary, personal_db

# TEACH_CORRECTION_SIMILARITY_THRESHOLD, TEACH_MAX_RECENT_CORRECTIONS,
# TEACH_ANTIPATTERN_SIMILARITY_THRESHOLD, UPLOAD_FOLDER 已从 config 导入

# SHOUYI_PHILOSOPHY, GEOMETRY_KNOWLEDGE 已从 config 导入


# ==================== 输出质量门控（v10 增强：反模式检测） ====================

# 偏离共扼谱几何的红灯短语
_QUALITY_RED_FLAGS = [
    "未找到任何引用来源", "未找到引用", "no citation", "no reference found",
    "我无法访问", "我无法读取", "i cannot access", "i cannot read",
    "没有接收到你上传的文件", "没有收到文件", "未收到文件内容",
    "作为一个AI语言模型", "作为一个人工智能", "as an ai language model",
    "我是一个AI", "我是AI助手",
    "超出我的知识范围", "我不知道",
]

# 共扼谱几何正面信号
_QUALITY_GREEN_SIGNALS = [
    "公理", "定理", "命题", "引理", "推论", "证明",
    "theta", "eta", "lambda", "sin", "cos",
    "共扼谱几何", "信息场", "谱刚性", "九素互扼",
    "文章", "章节", "S_e", "Gamma_geo",
    "退相干", "全息屏", "量纲桥",
]


# ==================== TeachingSystem（教学系统） ====================

class TeachingSystem:
    """
    v10 新增：教学系统。
    管理教学反馈的完整生命周期：纠正、反模式、知识补丁。
    所有教学数据仅持久化到 ChromaDB（无 MySQL 依赖）。
    """

    def __init__(self, vector_kb):  # vector_kb: VectorKnowledgeBase，运行时传入
        self.vector_kb = vector_kb
        logger.info("[TEACH] 教学系统已初始化（仅 ChromaDB 存储）")

    def add_correction(self, wrong: str, correct: str, reason: str = "",
                       context: str = "", session_id: str = "",
                       article_id: str = "", trust: float = 0.5) -> Dict[str, Any]:
        """
        添加一条纠正记录。
        存入 ChromaDB corrections 集合。
        如果提供了 article_id 且 trust >= 0.5，自动回写到 articles 集合。
        """
        result = {
            "success": False,
            "error": None,
        }

        if not wrong or not correct:
            result["error"] = "wrong 和 correct 字段不能为空"
            return result

        # 存入 ChromaDB（add_correction 现在返回 Dict）
        chroma_result = self.vector_kb.add_correction(
            wrong=wrong, correct=correct, reason=reason,
            context=context, session_id=session_id,
            article_id=article_id, trust=trust
        )
        result["success"] = chroma_result.get("success", False)
        if not result["success"]:
            result["error"] = chroma_result.get("error", "ChromaDB 写入失败")
        else:
            result["article_rewrite"] = chroma_result.get("article_rewrite")

        return result

    def add_antipattern(self, pattern: str, description: str = "",
                        severity: str = "medium") -> Dict[str, Any]:
        """
        添加一条反模式。
        存入 ChromaDB antipatterns 集合。
        """
        result = {
            "success": False,
            "error": None,
        }

        if not pattern:
            result["error"] = "pattern 字段不能为空"
            return result

        severity = severity.lower()
        if severity not in ('high', 'medium', 'low'):
            severity = 'medium'

        # 存入 ChromaDB
        chroma_ok = self.vector_kb.add_antipattern(
            pattern=pattern, description=description, severity=severity
        )
        result["success"] = chroma_ok
        if not chroma_ok:
            result["error"] = "ChromaDB 写入失败"

        return result

    def add_patch(self, topic: str, content: str, source: str = "") -> Dict[str, Any]:
        """
        添加一条知识补丁。
        存入 ChromaDB patches 集合。
        """
        result = {
            "success": False,
            "error": None,
        }

        if not topic or not content:
            result["error"] = "topic 和 content 字段不能为空"
            return result

        # 存入 ChromaDB
        chroma_ok = self.vector_kb.add_patch(
            topic=topic, content=content, source=source
        )
        result["success"] = chroma_ok
        if not chroma_ok:
            result["error"] = "ChromaDB 写入失败"

        return result

    def get_stats(self) -> Dict[str, Any]:
        """获取教学统计"""
        return self.vector_kb.get_teaching_stats()

    def get_history(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """获取教学历史"""
        return self.vector_kb.get_teaching_history(page=page, per_page=per_page)

    def build_teaching_prompt_section(self, query: str) -> str:
        """
        v10 新增：构建教学反馈 prompt 段落。
        包含：已学到的纠正、反模式警告、教学知识补丁。
        """
        sections = []

        # 1. 已学到的纠正（检索与当前查询最相关的，最多3条，避免无关纠正占用上下文）
        recent_corrections = self.vector_kb.search_corrections(
            query, top_k=min(3, TEACH_MAX_RECENT_CORRECTIONS)
        )
        if recent_corrections:
            corr_lines = [f"【已学到的纠正（教学反馈，共{len(recent_corrections)}条，与当前问题相关）】"]
            for i, corr in enumerate(recent_corrections, 1):
                meta = corr['metadata']
                trust = meta.get('trust_level', 0.5)
                wrong = meta.get('wrong', '')[:100]
                correct = meta.get('correct', '')[:200]
                reason = meta.get('reason', '')
                line = f"{i}. [信任:{trust:.1f}] 错误: \"{wrong}\" -> 正确: \"{correct}\""
                if reason:
                    line += f" (原因: {reason[:100]})"
                corr_lines.append(line)
            sections.append("\n".join(corr_lines))

        # 2. 反模式警告（检索与当前查询相关的，最多2条）
        antipatterns = self.vector_kb.search_antipatterns(query, top_k=2)
        if antipatterns:
            anti_lines = ["【反模式警告】"]
            severity_map = {"high": "高", "medium": "中", "low": "低"}
            for ap in antipatterns:
                meta = ap['metadata']
                sev = severity_map.get(meta.get('severity', 'medium'), '中')
                pattern = meta.get('pattern', '')[:100]
                anti_lines.append(f"- [{sev}] 禁止回复\"{pattern}\"")
            sections.append("\n".join(anti_lines))

        # 3. 教学知识补丁（检索与当前查询相关的补丁，top_k=3 保持聚焦）
        patches = self.vector_kb.search_patches(query, top_k=3)
        if patches:
            patch_lines = ["【教学知识补丁】"]
            for p in patches:
                meta = p['metadata']
                source = meta.get('source', '未知来源')
                topic = meta.get('topic', '')
                content = meta.get('content', '')[:150]
                patch_lines.append(f"- [来源:{source}] {topic}: {content}")
            sections.append("\n".join(patch_lines))

        return "\n\n".join(sections)

    def check_antipattern_triggered(self, response_text: str) -> Tuple[bool, List[str]]:
        """
        v10 新增：检查回复是否触发了反模式。
        返回 (is_triggered, triggered_patterns)。
        """
        if not response_text:
            return False, []

        triggered = []
        antipatterns = self.vector_kb.search_antipatterns(
            response_text, top_k=5
        )

        for ap in antipatterns:
            meta = ap['metadata']
            pattern = meta.get('pattern', '')
            severity = meta.get('severity', 'medium')
            # 用向量相似度 + 文本匹配双重检测
            vec_sim = ap.get('distance', 1.0)
            # ChromaDB distance 越小越相似，转换为相似度
            similarity = max(0.0, 1.0 - vec_sim)

            # 同时检查文本是否包含反模式的关键词
            text_match = pattern.lower() in response_text.lower() if pattern else False

            if (similarity > (1.0 - TEACH_ANTIPATTERN_SIMILARITY_THRESHOLD)) or text_match:
                triggered.append({
                    "pattern": pattern,
                    "severity": severity,
                    "similarity": round(similarity, 4),
                    "text_match": text_match,
                })

        # 检查是否有高严重度的反模式被触发
        high_triggered = [t for t in triggered if t['severity'] == 'high']
        is_triggered = len(high_triggered) > 0

        return is_triggered, triggered

    def check_and_update_corrections(self, response_text: str) -> List[Dict[str, Any]]:
        """
        v10 新增：检查AI回复是否体现了某条纠正，如果是则更新信任等级。
        返回被成功应用的纠正列表。
        """
        applied = []

        if not response_text or not self.vector_kb.is_initialized:
            return applied

        # 获取所有纠正记录
        all_corrections = self.vector_kb.get_recent_corrections(limit=50)
        if not all_corrections:
            return applied

        # 批量嵌入：response_text 一次 + 全部 correct_text 一次批量调用
        # （correct 文本按 id 缓存，仅首次全量嵌入；后续每轮只嵌入 response_text）
        try:
            resp_text = response_text[:2000]
            vkb = self.vector_kb
            resp_emb = vkb._get_embeddings([resp_text])[0]
            uncached = [c for c in all_corrections
                        if c.get('id') not in vkb._corr_emb_cache]
            if uncached:
                c_texts = [c['metadata'].get('correct', '') or '' for c in uncached]
                c_embs = vkb._get_embeddings(c_texts)
                for c, emb in zip(uncached, c_embs):
                    if emb and any(abs(float(v)) > 1e-8 for v in emb[:32]):
                        vkb._corr_emb_cache[c['id']] = emb
            embeddings = [resp_emb] + [vkb._corr_emb_cache.get(c.get('id')) for c in all_corrections]
            if not embeddings or len(embeddings) != len(all_corrections) + 1:
                return applied
        except Exception as e:
            logger.error(f"[TEACH-CORRECT] 批量嵌入失败: {e}")
            return applied

        resp_emb = embeddings[0]
        for corr, correct_emb in zip(all_corrections, embeddings[1:]):
            if correct_emb is None:
                continue
            meta = corr['metadata']
            correct_text = meta.get('correct', '')
            if not correct_text:
                continue

            # 用向量相似度检查回复是否包含纠正内容的核心观点
            similarity = self.vector_kb._cosine_similarity(resp_emb, correct_emb)

            if similarity > TEACH_CORRECTION_SIMILARITY_THRESHOLD:
                # 纠正被应用，更新信任等级
                old_trust = meta.get('trust_level', 0.5)
                new_trust = min(old_trust + 0.1, 1.0)
                old_applied = meta.get('applied_count', 0)
                new_applied = old_applied + 1

                # 直接使用 get_recent_corrections 返回的 id 更新
                try:
                    corr_id = corr.get('id')
                    if corr_id:
                        self.vector_kb.update_correction_trust(
                            corr_id, new_trust, new_applied
                        )
                        applied.append({
                            "wrong": meta.get('wrong', '')[:100],
                            "correct": correct_text[:200],
                            "old_trust": old_trust,
                            "new_trust": new_trust,
                            "similarity": round(similarity, 4),
                        })
                except Exception as e:
                    logger.error(f"[TEACH-CORRECT] 更新纠正信任等级时出错: {e}")

        if applied:
            logger.info(
                f"[TEACH-CORRECT] {len(applied)} 条纠正被成功应用并更新信任等级"
            )

        return applied


# ==================== 输出质量门控 ====================

def check_response_quality(response_text: str, teaching_system: Optional['TeachingSystem'] = None) -> Tuple[bool, str]:
    """
    检查 AI 回复质量。返回 (is_good, reason)。
    v10 增强：增加反模式检测。
    如果回复包含红灯短语且缺少共扼谱几何术语，判定为低质量。
    如果回复匹配到高严重度的反模式，直接判定为低质量。
    """
    if not response_text or len(response_text.strip()) < 20:
        return False, "回复过短或为空"

    lower_text = response_text.lower()

    # v10 新增：反模式检测
    if teaching_system:
        try:
            is_triggered, triggered_patterns = teaching_system.check_antipattern_triggered(response_text)
            if is_triggered:
                high_patterns = [t for t in triggered_patterns if t['severity'] == 'high']
                if high_patterns:
                    pattern_text = high_patterns[0]['pattern'][:80]
                    return False, f"反模式触发: 回复包含被禁止的模式'{pattern_text}'"
        except Exception as e:
            logger.error(f"[QUALITY-GATE] 反模式检测失败: {e}")

    # 检查红灯短语
    red_flags_found = []
    for flag in _QUALITY_RED_FLAGS:
        if flag.lower() in lower_text:
            red_flags_found.append(flag)

    # 检查正面信号
    green_count = sum(1 for sig in _QUALITY_GREEN_SIGNALS if sig.lower() in lower_text)

    # 判定逻辑
    if red_flags_found and green_count == 0:
        return False, f"偏离共扼谱几何: 包含'{red_flags_found[0]}'，无共扼谱几何术语"

    if len(response_text.strip()) < 50 and green_count == 0:
        return False, "回复过短且无共扼谱几何内容"

    return True, "ok"


def check_correction_applied(response_text: str, correction: Dict, vector_kb=None) -> bool:
    """
    v10 新增：检查AI回复是否体现了某条纠正。
    用向量相似度检查回复是否包含纠正内容的核心观点。
    """
    if not response_text or not correction:
        return False
    correct_text = correction.get('correct', '')
    if not correct_text:
        return False
    if vector_kb and vector_kb.is_initialized:
        similarity = vector_kb._cosine_similarity_texts(response_text, correct_text)
        return similarity > TEACH_CORRECTION_SIMILARITY_THRESHOLD
    return False


# ==================== Prompt 与生成（v10 增强：教学反馈注入） ====================

def build_system_prompt(
    eta_before: float,
    stage: int,
    strategy: str,
    max_eta: float,
    markers: int,
    loaded_chunks: List[str],
    articles_content: str,
    metrics: Dict[str, float],
    index_empty: bool,
               search_no_result: bool = False,
    uploaded_files_content: str = "",
    teaching_section: str = "",
    msg_count: int = 0,
    recent_chats: str = ""
) -> str:
    """
    v10 增强：新增 teaching_section、msg_count、recent_chats 参数。
    """
    # 新对话提醒（deepseek-v4-pro 上下文128K，优化后约可容纳50+轮对话）
    new_chat_hint = ""
    if msg_count >= 50:
        new_chat_hint = f"\n\n【提示】当前对话已有 {msg_count} 条用户消息，如感觉回答变差则建议开新对话。\n"
    elif msg_count >= 40:
        new_chat_hint = f"\n\n【提醒】当前对话已有 {msg_count} 条用户消息，上下文逐渐接近上限，重要问题建议开新对话以保证质量。\n"
    index_warning = ""
    if index_empty:
        index_warning = """\n\n【索引状态警告】
当前向量知识库未索引到任何段落。请检查：
1. UPLOAD_FOLDER 路径是否正确（当前: """ + UPLOAD_FOLDER + """）
2. 目录下是否有 .md/.txt/.py/.tex 文件
3. 访问 /v1/files 查看已上传文件
4. 或 POST /v1/upload 上传新文件
5. 或 POST /v1/vector/rebuild 重建向量索引
"""
    elif search_no_result:
        index_warning = """\n\n【搜索提示】
本次向量检索未命中相关文章。这可能是因为：
1. 用户的问题与知识库文章关联度较低——直接用你的知识回答即可。
2. 关键词太短或太泛——可以尝试用 search_knowledge 换更具体的关键词再搜一次。
3. 文章确实不包含相关内容——不要逐篇 view_article 扫描，这非常低效。
"""

    uploaded_section = ""
    if uploaded_files_content:
        uploaded_section = f"\n\n【用户上传文件】\n{uploaded_files_content}\n"

    # v10 新增：教学反馈段落
    teaching_prompt = ""
    if teaching_section:
        teaching_prompt = f"\n\n{teaching_section}"

    # 根据阶段调整语气引导
    if stage <= 1:
        tone_hint = "简洁直接，像一位严谨的数学家在黑板前快速推导。"
    elif stage <= 3:
        tone_hint = "深入但不晦涩，像一位导师在和学生讨论一个有趣的问题。"
    elif stage <= 5:
        tone_hint = "开放探索，可以提出假设和猜想，像研究者在研讨会上的发言。"
    else:
        tone_hint = "前沿发散，大胆提出新方向，不必每句话都有定理支撑。"

    # 个人数据摘要
    personal_summary = _get_personal_db_summary(personal_db)
    personal_prompt = f"\n\n【个人档案】\n{personal_summary}"
    thinking_instruction = """
【推理协议——深度思考与广域分析】
在每次回答前，遵循以下四层分析协议。对简单问题可省略，但任何涉及因果解释、推导、证明、对比、
假设或推测的问题，必须在内部完成这四层分析：

=== 第一层：问题拆解与多视角映射 ===
- 将问题拆解为：定义层、机制层、边界层、外延层
- 对每一层思考：这个问题还可以从什么学科角度理解？（数学、物理、信息论、几何、系统论等）
- 寻找与问题表面无关但结构相似的已知结论
- 自问：问题的对偶形式是什么？反命题是否也成立？

=== 第二层：深层因果链 ===
- 不要停留在"因为A所以B"，追问：A为什么成立？它依赖什么更基础的假设？
  B是否只有在A存在时才成立？是否存在独立于A的路径也能到达B？
- 如果去掉一个关键条件，结论还成立吗？如果条件极端化（→∞或→0）呢？
- 对每一个推导步骤，标注其依赖的文章编号或引用来源

=== 第三层：反证与边界探索 ===
- 构造一个反例：什么情况下某个定理会失效？
- 检查是否存在隐藏假设（平滑性、可微性、线性等），这些假设是否必要？
- 考虑极端情况：当参数趋近0、无穷、临界值时，系统行为如何变化？
- 这个结论能否推广到更高维/更一般的框架？还是只能在当前框架下成立？

=== 第四层：外延与验证 ===
- 你的结论是否与你已知的所有相关文章一致？（如有不一致，说明哪个假设或前提不同）
- 你的结论是否可以通过实验或观测来验证？
- 写下至少一个开放问题：当前推理中无法确定的环节是什么？
- 如果有多个可能方向，给出概率权重或支持证据强度评价

对简单问题（事实查询、文件名读取等），按正常节奏回答。
对复杂问题，在回答中自然融入上述分析过程的关键洞见，不必列出步骤编号。
"""

    calc_discipline = """
【计算纪律——数值必须精确，禁止心算】
推导中凡涉及数值计算、公式求值、方程求解、符号推导，一律调用 calculate_math 工具完成，禁止自行心算得出数值。
必须遵守：
1. 需要计算数值（哪怕是简单的 2+3、根号、分数、阶乘、求和）时，必须调用 calculate_math，由工具返回精确结果；绝不凭心算或模型直觉填写数值。
2. 需要精确分数时，在表达式中使用 Rational(a,b)、sqrt、pi、E 等 sympy 符号，工具会返回数值近似（10位）并附「精确值(精简)」短形式；用这个精简值核对精确分数，不要只按近似值写结论。
3. 符号推导（求导、积分、化简、展开、解方程）也交给 calculate_math（如 diff、integrate、solve、expand、simplify），不靠印象写公式结果。
4. 把计算得到的每个数值写入回答前，回看一眼是不是工具返回的值；不记得就重算，绝不凭感觉改写。
"""

    cite_discipline = """
【引用纪律——引用必须真实存在，禁止幻觉引用】
当你引用文章/定理支撑推导时，必须遵守：
1. **只引用真实存在的文章编号**。文章编号形如"文章 X.Y"（例如"文章 5.6"、"文章 0.8"）。写进回答的每个"文章 X.Y"式引用，都必须是你在【参考资料】中看到、或通过 vector_search / list_articles 核实的确切编号。
2. **引用前先核实**：不确定某编号是否真实存在时，用 list_articles 查看全部文章概览，或用编号前缀搜索确认。禁止凭印象编造编号。
3. **编号要精确**：不要写"文章 7.15"这类你可能记错的编号。如果找不到对应编号，就改用描述性表述（如"相关工作"），或者明确说"在当前文章库中未找到直接对应内容"，不要编一个编号硬塞进去。
4. 系统会对每个回答做【引用硬校验】：任何不存在的文章编号会被自动拦截并触发重写。与其被拦截重写，不如一开始就引用真实编号。
"""

    multi_hop_discipline = """
【多跳推理——相关定理逐层查，禁止浅尝辄止】
推导时必须一层一层地把相关定理/文章找全，不要只查一层、查不到就直接说"无法推导/没有相关内容"。
必须遵守：
1. **先觉醒再下结论**：第一轮检索没命中核心定理时，不代表文章库中没有。用 vector_search 换不同关键词、或按已找到文章里引用的编号继续追查，通常多查两三轮就能打通。
2. **沿依赖链条走**：当你引用了某篇文章 A，而 A 的推导又依赖前置文章 B 时，继续用 vector_search 查 B 的内容，把链条完整拉起来（系统已在推导类问题时自动注入 A 的多跳引用图骨架，优先利用）。
3. **反查与扩展**：不仅查"这篇文章依赖谁"，还要查"谁依赖这篇文章"，往往能发现同族的对称结论，辅助建立完整推导。
4. **确认充分才动手**：只有当你确信已经找到闭环所需的全部关键定理，才开始组装推导；若仍有缺口，先用 list_articles 看清全库再定位，而不是凭印象补一个不存在的编号。
"""


    from datetime import datetime
    _today = datetime.now().strftime("%Y年%m月%d日")
    return f"""今天是{_today}。你是共扼谱几何研究者，不是AI助手。可用工具读写文章、个人数据库和对话记录。
{SHOUYI_PHILOSOPHY}
{GEOMETRY_KNOWLEDGE}{teaching_prompt}
{thinking_instruction}
{calc_discipline}
{cite_discipline}
{multi_hop_discipline}
【工具使用规则】
- get_current_time：在需要确定版本号日期、判断文件新旧、或任何需要知道当前时间时，调用 get_current_time 获取实时日期时间。不要猜测日期，务必调用工具确认。虽然系统提示中包含了今天日期，但工具返回的更精确（含时分秒），且适用于跨天对话场景。
- write_article：用户要求写入文章时，必须调用 write_article 工具实际写入。调用成功后才能说"已写入"。禁止在没有调用工具的情况下声称"已写入""已生成""已保存"。写入成功后，在回复中告诉用户文章已保存，并提供工具返回的预览链接（Markdown格式[点击预览](URL)）。
- write_article 分段写入：当文章内容超过 30000 字符时，必须分段调用 write_article。第一次调用使用 mode=write 写入前半部分，后续调用使用 mode=append 追加剩余部分。每次调用内容控制在 25000-30000 字符以内。最后一段 append 完成后，告知用户文章已完整保存。
- edit_article 局部修改：**修改已有文章中的若干处措辞/公式/段落时，必须优先使用 edit_article，不要用 write_article 全文重写**。edit_article 只需传入 old_text（要替换的原始文本）和 new_text（替换后文本），服务端会自动：①归档完整原文件 ②执行替换 ③更新向量索引 ④git提交。支持一次调用中提交多个替换（replacements数组）。old_text 必须精确匹配原文（包括空格和换行），建议先 view_article 确认原文内容。无论文章多大都不受 token 限制。

【修改文章的纪律】（修改任何已有文章时，必须严格遵守以下四条）
1. **不新开文章**：只修改已有文章，不创建新文件来替代或补充。
2. **只改错误，不加补丁**：仅修正公式错误、推导错误、数值错误。不添加"补丁文章"、"修正附录"、"勘误表"等额外内容。
3. **不留工作痕迹**：只修改公式和证明过程本身。不添加任何修正说明、版本号、修改日志、诚实标注、审核批注、脚注说明。不新增任何架构描述、小节标题、或自创术语。修改后的文本应与原文风格无缝融合，读者看不出被修改过。
4. **不删不减**：除非有明确指令，否则不精简、不删减原文。只替换错误内容，不删除正确内容。
- vector_search：主动向量语义搜索。用自然语言描述你要找的内容，返回最相关的文章片段和文件名。适用于：查找特定概念/定理/公式在哪些文章中出现、跨文章主题汇总、审核时查找相关引用。可以换不同查询词多次搜索覆盖不同角度。
- list_articles：轻量列出所有文章的编号、标题和摘要（每篇约1行）。**当你需要了解文章全貌、查找某主题属于哪篇文章、确认文章编号时，优先用此工具**。一次调用就能看到全部文章概览，不要用 view_article 逐篇查看。
- view_article：读取文章片段（默认5000字符/次）。**首次读取时会自动显示章节目录，之后可用 section 参数按章节名直接跳转**（如 section="公理3"），比 offset 更高效。只在已经确定要查看哪篇文章的具体内容时才使用。日常对话中每次对话不宜超过5次，但抽查/审核时不受此限制。**决策提示：如果需要阅读同一篇文章的3个或以上章节，建议直接用 full=true 一次性获取全文，比逐章读取更省 token 和 API 往返。**
- personal_write：重要信息可以写入个人数据库。
- calculate_math：任何数值计算、公式求值、方程求解、符号推导（求导/积分/化简/展开）都必须调用本工具。传入 expression 表达式即可，用 Rational(a,b) 得精确分数，需要小数时传 digits。涉及数值结果一律以本工具返回值为准，严禁心算。
- 参考资料已通过向量语义检索自动注入下方【参考资料】区域（基于当前问题的被动检索）。**日常对话中优先使用这些参考资料回答，不要重复用 view_article 去看已经在参考资料中出现的内容**。只有在参考资料明确不够时，才用 vector_search 换角度搜索，或 view_article 查看具体段落。
- 禁止幻觉：不确定的答案直接说"我不确定"，不要编造。**不要声称某篇文章不存在**——先用 vector_search 或编号前缀搜索确认。

【抽查/审核专用规则】（当用户要求审核、抽查、复查、检查文章内容时，以下规则覆盖日常规则）
- **核心原则：向量库 ≠ 原文。** 向量库存储的是分块嵌入（embedding），包含语义近似但非精确副本。向量检索可能遗漏关键细节（缺少运算符、数值偏差、公式错误），不能作为审核的唯一依据。
- **审核流程——三步走：**
  1. 用 vector_search 定位相关段落（作为"线索"找哪些区域可能有问题）
  2. **必须用 view_article 读取原文对应段落进行精确核实**（向量库返回的内容不可直接当作原文）
  3. 将原文与推导逻辑/公式规范逐项比对，做出判断
- view_article 不设次数限制——审核时可以反复调用，必要时逐节读取全文。
- 每个审核判断必须标注：是"基于原文核实"还是"基于向量库推断"。如需后者，诚实标注不确定性。
- 数值比对：必须从 view_article 读取原文的精确数值，不可用向量库返回的近似值做比对。
- 教学反馈工具（可选，在适当时机使用）：
  - teach_correction：当你发现之前的回答中有事实错误，或文章内容需要纠正时，调用此工具记录错误和正确内容。这会帮助你在后续对话中避免同样的错误。
  - teach_antipattern：当你意识到某种回答模式是不好的（如编造数据、过度推断、忽略限定条件），记录为反模式，帮助改进回复质量。
  - teach_patch：当对话中发现文章库缺少某个重要知识点时，调用此工具补充知识补丁。
  - 这些工具调用不会打断对话，用户不会看到细节。请自然地在合适时机使用。
【参考资料（系统自动检索）】
{articles_content if articles_content else "（无直接相关参考资料，基于共扼谱几何知识回答）"}{uploaded_section}
{recent_chats}
【当前状态】eta={eta_before:.2f}度 | {tone_hint}
{index_warning}{personal_prompt}
{new_chat_hint}"""
