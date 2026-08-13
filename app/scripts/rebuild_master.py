#!/usr/bin/env python3
"""重建主库真理层——从 pending 记录恢复（reset 误操作后使用）"""

import sys, os, json, hashlib
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../master_ai'))
from master_db import MasterDatabase


def rebuild(dry_run: bool = False):
    db = MasterDatabase()
    pending_coll = db.pending_collection
    master_coll = db.master_collection

    if master_coll is None:
        print("❌ master_collection 不可用")
        return

    # 获取所有记录
    all_data = pending_coll.get(include=["metadatas", "documents"])
    total = len(all_data["ids"])
    print(f"pending 总记录: {total}")

    # 筛选 promoted
    promoted = []
    for i in range(total):
        meta = all_data["metadatas"][i]
        if meta.get("status") == "promoted":
            promoted.append({
                "id": all_data["ids"][i],
                "meta": meta,
                "doc": all_data["documents"][i],
            })

    print(f"其中 promoted: {len(promoted)}")

    # 按 article_number 排序（保持逻辑顺序）
    def sort_key(item):
        an = item["meta"].get("article_number", "")
        try:
            parts = an.split(".")
            return tuple(int(p) for p in parts if p.isdigit())
        except:
            return (999,)

    promoted.sort(key=sort_key)

    # 检查当前 master
    current_master = master_coll.count()
    print(f"当前 master 记录: {current_master}")

    if current_master > 0:
        print("⚠️  master 非空，仅追加不覆盖")

    # 重建
    new_count = 0
    skip_count = 0
    seq = current_master + 1  # 从当前最大编号+1开始

    for i, item in enumerate(promoted):
        meta = item["meta"]
        formula_name = meta.get("formula_name", "unnamed")
        master_id = f"master_{hashlib.md5(formula_name.encode()).hexdigest()[:12]}"

        # 检查是否已存在
        existing = master_coll.get(ids=[master_id])
        if existing["ids"]:
            skip_count += 1
            if dry_run:
                print(f"  跳过 (已存在): {formula_name}")
            continue

        master_metadata = {
            "master_id": master_id,
            "permanent_number": str(seq),
            "formula_name": formula_name,
            "formula_type": meta.get("formula_type", ""),
            "source_agent": meta.get("source_agent", "rebuild_260811"),
            "verified_at": meta.get("processed_at", datetime.now().isoformat()),
            "verification_result": json.dumps({
                "rebuilt": True,
                "original_submission": meta.get("submission_id", ""),
                "note": "从pending记录重建，原始验证结果已丢失",
            }, ensure_ascii=False),
            "status": "verified",
            "original_submission": meta.get("submission_id", ""),
            "topology_class": meta.get("topology_class", "A0"),
            "article_number": meta.get("article_number", ""),
            "berry_status": "no_angle_data",
            "berry_phase": "0",
            "berry_n_value": "0",
            "berry_path_points": "[]",
            "source_trace": "[]",
            "source_risk_level": "unaudited",
            "berry_closure": "pending",
        }

        if not dry_run:
            db._write(
                master_coll, "add",
                ids=[master_id],
                documents=[item["doc"]],
                metadatas=[master_metadata],
            )
            # 更新 seq 文件
            seq += 1
            new_count += 1

        if (i + 1) % 100 == 0:
            print(f"  进度: {i+1}/{len(promoted)} (新增 {new_count}, 跳过 {skip_count})")

    # 更新 seq 文件到最终值
    if not dry_run and new_count > 0:
        with open(db._seq_file, "w") as f:
            json.dump({"next_number": seq}, f)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}重建完成:")
    print(f"  新增: {new_count}")
    print(f"  跳过 (已存在): {skip_count}")
    print(f"  master 总数: {master_coll.count()}")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    rebuild(dry_run=dry)
