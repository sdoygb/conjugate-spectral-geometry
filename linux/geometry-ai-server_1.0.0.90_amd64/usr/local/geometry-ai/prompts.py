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

# 偏离几何论的红灯短语
_QUALITY_RED_FLAGS = [
    "未找到任何引用来源", "未找到引用", "no citation", "no reference found",
    "我无法访问", "我无法读取", "i cannot access", "i cannot read",
    "没有接收到你上传的文件", "没有收到文件", "未收到文件内容",
    "作为一个AI语言模型", "作为一个人工智能", "as an ai language model",
    "我是一个AI", "我是AI助手",
    "超出我的知识范围", "我不知道",
]

# 几何论正面信号
_QUALITY_GREEN_SIGNALS = [
    "公理", "定理", "命题", "引理", "推论", "证明",
    "theta", "eta", "lambda", "sin", "cos",
    "几何论", "信息场", "谱刚性", "九素互扼",
    "文章", "章节", "S_e", "Gamma_geo",
    "退相干", "全息屏", "量纲桥", "质量映射",
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
                       context: str = "", session_id: str = "") -> Dict[str, Any]:
        """
        添加一条纠正记录。
        存入 ChromaDB corrections 集合。
        """
        result = {
            "success": False,
            "error": None,
        }

        if not wrong or not correct:
            result["error"] = "wrong 和 correct 字段不能为空"
            return result

        # 存入 ChromaDB
        chroma_ok = self.vector_kb.add_correction(
            wrong=wrong, correct=correct, reason=reason,
            context=context, session_id=session_id
        )
        result["success"] = chroma_ok
        if not chroma_ok:
            result["error"] = "ChromaDB 写入失败"

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

        # 1. 已学到的纠正（按 trust_level 降序，最近10条）
        recent_corrections = self.vector_kb.get_recent_corrections(
            limit=TEACH_MAX_RECENT_CORRECTIONS
        )
        if recent_corrections:
            corr_lines = [f"【已学到的纠正（教学反馈，共{len(recent_corrections)}条）】"]
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

        # 2. 反模式警告
        antipatterns = self.vector_kb.get_all_antipatterns()
        if antipatterns:
            anti_lines = ["【反模式警告】"]
            severity_map = {"high": "高", "medium": "中", "low": "低"}
            for ap in antipatterns:
                meta = ap['metadata']
                sev = severity_map.get(meta.get('severity', 'medium'), '中')
                pattern = meta.get('pattern', '')[:100]
                anti_lines.append(f"- [{sev}] 禁止回复\"{pattern}\"")
            sections.append("\n".join(anti_lines))

        # 3. 教学知识补丁（检索与当前查询相关的补丁，top_k=10 平衡覆盖率和速度）
        patches = self.vector_kb.search_patches(query, top_k=5)
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

        for corr in all_corrections:
            meta = corr['metadata']
            correct_text = meta.get('correct', '')
            if not correct_text:
                continue

            # 用向量相似度检查回复是否包含纠正内容的核心观点
            similarity = self.vector_kb._cosine_similarity_texts(
                response_text, correct_text
            )

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
    如果回复包含红灯短语且缺少几何论术语，判定为低质量。
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
        return False, f"偏离几何论: 包含'{red_flags_found[0]}'，无几何论术语"

    if len(response_text.strip()) < 50 and green_count == 0:
        return False, "回复过短且无几何论内容"

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
    uploaded_files_content: str = "",
    teaching_section: str = "",
    msg_count: int = 0,
    recent_chats: str = ""
) -> str:
    """
    v10 增强：新增 teaching_section、msg_count、recent_chats 参数。
    """
    # 新对话提醒（deepseek-v4-pro 上下文128K，约可容纳30轮对话）
    new_chat_hint = ""
    if msg_count >= 30:
        new_chat_hint = f"\n\n【重要提醒】当前对话已有 {msg_count} 条用户消息，上下文接近上限，如果感觉回答质量下降或出现幻觉，建议开一个新对话。\n"
    elif msg_count >= 45:
        new_chat_hint = f"\n\n【提示】当前对话已有 {msg_count} 条消息，如在合理使用范围内可继续，若感觉回答变差则建议开新对话。\n"
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


    return f"""你是几何论研究者，不是AI助手。可用工具读写文章、个人数据库和对话记录。
{SHOUYI_PHILOSOPHY}
{GEOMETRY_KNOWLEDGE}{teaching_prompt}
{thinking_instruction}
【工具使用规则】
- write_article：用户要求写入文章时，必须调用 write_article 工具实际写入。调用成功后才能说"已写入"。禁止在没有调用工具的情况下声称"已写入""已生成""已保存"。写入成功后，在回复中告诉用户文章已保存，并提供工具返回的预览链接（Markdown格式[点击预览](URL)）。
- write_article 分段写入：当文章内容超过 30000 字符时，必须分段调用 write_article。第一次调用使用 mode=write 写入前半部分，后续调用使用 mode=append 追加剩余部分。每次调用内容控制在 25000-30000 字符以内。最后一段 append 完成后，告知用户文章已完整保存。
- vector_search：主动向量语义搜索。用自然语言描述要找的内容，返回最相关的文章片段和文件名。适用于查找特定概念/定理在哪些文章中出现、跨文章主题汇总、审核时查找相关引用。可以换不同查询词多次搜索覆盖不同角度。
- view_article：读取完整文章内容。**必须使用 vector_search 或【参考资料】中显示的文件名**，不要自己编造。limit 建议 3000-5000，offset 用于跳到指定位置。
- personal_write：重要信息可以写入个人数据库。
- 参考资料已通过向量语义检索自动注入下方【参考资料】区域（基于当前问题的被动检索）。你还可以用 vector_search 主动搜索其他角度的内容。
- 禁止幻觉：不确定的答案直接说"我不确定"，不要编造。**不要声称某篇文章不存在**——先用 vector_search 或编号前缀搜索确认。
- 教学反馈工具（可选，在适当时机使用）：
  - teach_correction：当你发现之前的回答中有事实错误，或文章内容需要纠正时，调用此工具记录错误和正确内容。这会帮助你在后续对话中避免同样的错误。
  - teach_antipattern：当你意识到某种回答模式是不好的（如编造数据、过度推断、忽略限定条件），记录为反模式，帮助改进回复质量。
  - teach_patch：当对话中发现文章库缺少某个重要知识点时，调用此工具补充知识补丁。
  - 这些工具调用不会打断对话，用户不会看到细节。请自然地在合适时机使用。
【参考资料（系统自动检索）】
{articles_content if articles_content else "（无直接相关参考资料，基于几何论知识回答）"}{uploaded_section}
{recent_chats}
【当前状态】eta={eta_before:.2f}度 | {tone_hint}
{index_warning}{personal_prompt}
{new_chat_hint}"""
