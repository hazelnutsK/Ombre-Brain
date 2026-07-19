"""
========================================
tools/trace/core.py — trace 主路径（修改 / 删除 / 重生 embedding）
========================================

trace 是 OB 唯一的「写元数据」入口，承接所有桶字段更新和删除。模型
传什么字段，就改什么字段；-1 / 空串 表示「不改」。

关键行为：
- delete=True → Markdown 移入 archive/ 并清理可重建的 embedding
- hard_delete=True → 仅清理创建时明确标记 test_data=True 的测试桶；
  必须同时提供非空 delete_reason，普通记忆和 plan 均拒绝且保持原位
- 收集传入字段构造 updates dict（含 status/weight/dont_surface/
  why_remembered/pinned/digested/resolved/content/tags/domain 等）
- pinned=1 时强制 importance=10 并做配额检查；pinned=0 仅取消标记
- content 改写时同步重建 embedding，并对 plan 桶追加 change_log
- resolved/digested 切换会附中文语义提示

不做什么（边界）：
- 不创建桶（那是 hold/grow/plan/letter 的事）
- 不把普通记忆转换成可擦除测试数据，也不物理删除普通记忆
- 不返回结构化数据，统一中文短句

对外暴露：trace_core(bucket_id, name, domain, valence, arousal, importance,
                     tags, resolved, pinned, digested, content, delete,
                     status, weight, dont_surface, why_remembered,
                     meaning_append, meaning_replace, media_append, media_replace,
                     hard_delete, delete_reason, old_str, new_str) → str
========================================
"""

import math
from contextlib import AsyncExitStack
from typing import Optional

from ombrebrain.domain.memory_messages import resolved_hint
from utils import parse_bool
from .. import _runtime as rt
from .._common import (
    _HIGH_IMP_THRESHOLD,
    _quota_turn,
    check_content_size,
    check_metadata_size,
    check_pinned_quota,
    enforce_high_importance_quota,
    occupies_high_importance_quota_slot,
)


async def trace_core(
    bucket_id: str,
    name: Optional[str] = "",
    domain: Optional[str] = "",
    valence: Optional[float] = -1,
    arousal: Optional[float] = -1,
    importance: Optional[int] = -1,
    tags: Optional[str] = "",
    resolved: Optional[int] = -1,
    pinned: Optional[int] = -1,
    digested: Optional[int] = -1,
    content: Optional[str] = "",
    delete: Optional[bool] = False,
    status: Optional[str] = "",
    weight: Optional[float] = -1,
    dont_surface: Optional[int] = -1,
    why_remembered: Optional[str] = "",
    meaning_append: Optional[str] = "",
    meaning_replace: Optional[list] = None,
    media_append: Optional[list | str] = None,
    media_replace: Optional[list | str] = None,
    hard_delete: Optional[bool] = False,
    delete_reason: Optional[str] = "",
    old_str: Optional[str] = "",
    new_str: Optional[str] = None,
) -> str:
    bucket_id = "" if bucket_id is None else str(bucket_id)
    if name is None:
        name = ""
    if domain is None:
        domain = ""
    if valence is None:
        valence = -1
    if arousal is None:
        arousal = -1
    if importance is None:
        importance = -1
    if tags is None:
        tags = ""
    if resolved is None:
        resolved = -1
    if pinned is None:
        pinned = -1
    if digested is None:
        digested = -1
    if content is None:
        content = ""
    if delete is None:
        delete = False
    if status is None:
        status = ""
    if weight is None:
        weight = -1
    if dont_surface is None:
        dont_surface = -1
    if why_remembered is None:
        why_remembered = ""
    if meaning_append is None:
        meaning_append = ""
    if media_append is None:
        media_append = []
    new_str_provided = new_str is not None
    old_str = "" if old_str is None else str(old_str)
    new_str = "" if new_str is None else str(new_str)
    content = str(content)
    name = str(name)
    domain = str(domain)
    tags = str(tags)
    status = str(status)
    why_remembered = str(why_remembered)
    meaning_append = str(meaning_append)
    delete = parse_bool(delete, default=False)
    hard_delete = parse_bool(hard_delete, default=False)
    delete_reason = "" if delete_reason is None else str(delete_reason).strip()

    def _finite_float(value, default: float) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError, OverflowError):
            return default
        return numeric if math.isfinite(numeric) else default

    def _safe_int(value, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError, OverflowError):
            return default

    valence = _finite_float(valence, -1)
    arousal = _finite_float(arousal, -1)
    weight = _finite_float(weight, -1)
    importance = _safe_int(importance, -1)
    resolved = _safe_int(resolved, -1)
    pinned = _safe_int(pinned, -1)
    digested = _safe_int(digested, -1)
    dont_surface = _safe_int(dont_surface, -1)

    metadata_err = check_metadata_size(
        bucket_id=bucket_id,
        name=name,
        domain=domain,
        tags=tags,
        status=status,
        why_remembered=why_remembered,
        meaning_append=meaning_append,
        delete_reason=delete_reason,
    )
    if metadata_err:
        return metadata_err
    if rt.mark_op:
        rt.mark_op("trace")
    rt.record_v3_tool_event("trace", {
        "bucket_id": bucket_id,
        "name": name,
        "domain": domain,
        "valence": valence,
        "arousal": arousal,
        "importance": importance,
        "tags": tags,
        "resolved": resolved,
        "pinned": pinned,
        "digested": digested,
        "content_length": len(content or ""),
        "delete": delete,
        "hard_delete": hard_delete,
        "delete_reason_length": len(delete_reason),
        "old_str_length": len(old_str),
        "new_str_length": len(new_str) if new_str_provided else 0,
        "status": status,
        "weight": weight,
        "dont_surface": dont_surface,
        "why_remembered_length": len(why_remembered or ""),
    })

    if not bucket_id or not bucket_id.strip():
        return "请提供有效的 bucket_id。"

    patch_args_supplied = bool(old_str) or new_str_provided
    if patch_args_supplied and (delete or hard_delete):
        return (
            "参数冲突：old_str/new_str 局部替换不能与 delete/hard_delete 同时使用；"
            "本次未修改、未删除、未归档。"
        )
    if patch_args_supplied and content:
        return (
            "参数冲突：不能同时使用 content 完整替换和 old_str/new_str 局部替换；"
            "本次未修改。"
        )
    if patch_args_supplied and (not old_str or not new_str_provided):
        return (
            "局部替换必须同时提供 old_str 和 new_str；new_str 可以是空字符串以删除片段。"
            "本次未修改。"
        )
    if patch_args_supplied and old_str == new_str:
        return "old_str 与 new_str 完全相同，没有内容需要替换；本次未修改。"

    # --- Delete 模式（F-10：普通记忆只允许软删除/归档）---
    if hard_delete and delete:
        return (
            "参数冲突：delete=True 表示归档，hard_delete=True 仅表示清理测试桶，"
            "两者不能同时使用；本次未删除、未归档。"
        )
    if hard_delete:
        if not delete_reason:
            return (
                "拒绝永久删除：hard_delete 仅用于创建时明确标记为 test_data 的测试桶，"
                "并且必须提供非空 delete_reason；本次未删除、未归档。"
            )
        if len(delete_reason) > 500:
            return "拒绝永久删除：delete_reason 不能超过 500 个字符；本次未删除、未归档。"
        result = await rt.bucket_mgr.hard_delete_test_bucket(
            bucket_id, reason=delete_reason
        )
        if result.get("ok"):
            return f"已永久删除测试桶: {bucket_id}"
        if result.get("error") == "not_erasable_test_data":
            return (
                "拒绝永久删除：普通记忆桶（包括 plan）不可被 trace 物理删除；"
                "只有创建时明确标记为 test_data 的测试桶可以清理。"
                "本次未删除、未归档；若只想从日常召回隐藏，请改用 delete=True 归档。"
            )
        if result.get("error") == "missing_delete_reason":
            return "拒绝永久删除：必须提供非空 delete_reason；本次未删除、未归档。"
        if result.get("error") == "delete_reason_too_long":
            return "拒绝永久删除：delete_reason 不能超过 500 个字符；本次未删除、未归档。"
        return f"永久删除失败: {result.get('error', 'unknown_error')}"

    if delete:
        success = await rt.bucket_mgr.delete(bucket_id)
        return f"已将记忆桶存入档案（不可在日常召回中浮现）: {bucket_id}" if success else f"未找到记忆桶: {bucket_id}"

    bucket = await rt.bucket_mgr.get(bucket_id)
    if not bucket:
        return f"未找到记忆桶: {bucket_id}"

    meta = bucket.get("metadata", {})
    current_pinned = parse_bool(meta.get("pinned"), default=False)
    protected = parse_bool(meta.get("protected"), default=False)
    unpinning_now = pinned == 0 and current_pinned
    if (
        1 <= importance <= 10
        and (current_pinned or protected)
        and not (unpinning_now and not protected)
    ):
        return (
            f"记忆桶 {bucket_id} 是 pinned/protected 核心桶，importance 被锁定为 10，"
            "本次未修改。请先 trace(bucket_id, pinned=0)，再单独 trace(bucket_id, importance=...)。"
        )

    # 配额判定 + 落盘必须在同一把锁里：check_pinned_quota/enforce_high_importance_quota
    # 到最终 bucket_mgr.update() 之间隔着别的字段处理和一次 await，两个并发 trace()
    # 都可能在对方提交前读到同一个「未满」快照。是否需要哪把锁在动 updates 之前就
    # 能从入参判断出来，所以先算好，再把整段检查+落盘包进对应的 quota turn。
    current_importance = int(meta.get("importance") or 0)
    current_type = str(meta.get("type") or "dynamic").strip().lower()
    pin_state_changed = pinned in (0, 1) and bool(pinned) != current_pinned
    final_pinned = bool(pinned) if pinned in (0, 1) else current_pinned
    final_type = current_type
    if pinned == 1:
        final_type = "permanent"
    elif unpinning_now and not protected:
        final_type = "dynamic"
    requested_importance = (
        int(importance) if 1 <= importance <= 10 else current_importance
    )
    final_importance = 10 if pinned == 1 else requested_importance
    current_dont_surface = parse_bool(
        meta.get("dont_surface"), default=False
    )
    final_dont_surface = (
        bool(dont_surface)
        if dont_surface in (0, 1)
        else current_dont_surface
    )
    before_quota_meta = dict(meta)
    before_quota_meta.update({
        "importance": current_importance,
        "pinned": current_pinned,
        "protected": protected,
        "type": current_type,
        "dont_surface": current_dont_surface,
    })
    after_quota_meta = dict(before_quota_meta)
    after_quota_meta.update({
        "importance": final_importance,
        "pinned": final_pinned,
        "type": final_type,
        "dont_surface": final_dont_surface,
    })
    occupied_high_before = occupies_high_importance_quota_slot(
        before_quota_meta
    )
    occupies_high_after = occupies_high_importance_quota_slot(after_quota_meta)
    reserves_high_importance = occupies_high_after and not occupied_high_before
    eligibility_field_changed = (
        pin_state_changed or final_dont_surface != current_dont_surface
    )
    importance_changed = final_importance != current_importance
    needs_high_importance_lock = (
        eligibility_field_changed
        or (
            importance_changed
            and max(current_importance, final_importance)
            >= _HIGH_IMP_THRESHOLD
        )
    )
    need_pinned_lock = pin_state_changed

    async with AsyncExitStack() as quota_stack:
        if need_pinned_lock:
            await quota_stack.enter_async_context(_quota_turn("pinned"))
        if needs_high_importance_lock:
            await quota_stack.enter_async_context(_quota_turn("high_importance"))

        if need_pinned_lock or needs_high_importance_lock:
            locked_bucket = await rt.bucket_mgr.get(bucket_id)
            if not locked_bucket:
                return f"未找到记忆桶: {bucket_id}"
            locked_meta = locked_bucket.get("metadata", {})
            locked_snapshot = (
                parse_bool(locked_meta.get("pinned"), default=False),
                parse_bool(locked_meta.get("protected"), default=False),
                str(locked_meta.get("type") or "dynamic").strip().lower(),
                int(locked_meta.get("importance") or 0),
                parse_bool(locked_meta.get("dont_surface"), default=False),
            )
            original_snapshot = (
                current_pinned,
                protected,
                current_type,
                current_importance,
                current_dont_surface,
            )
            if locked_snapshot != original_snapshot:
                return (
                    f"记忆桶 {bucket_id} 在本次修改期间已被其他请求更新，"
                    "为避免覆盖或配额误判，请重试。"
                )

        if reserves_high_importance:
            final_importance = await enforce_high_importance_quota(
                final_importance
            )

        updates: dict = {}
        if name:
            updates["name"] = name
        if domain:
            updates["domain"] = [d.strip() for d in domain.split(",") if d.strip()]
        if 0 <= valence <= 1:
            updates["valence"] = valence
        if 0 <= arousal <= 1:
            updates["arousal"] = arousal
        if 1 <= importance <= 10:
            updates["importance"] = final_importance
        if tags:
            updates["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
        if resolved in (0, 1):
            updates["resolved"] = bool(resolved)
        if pinned in (0, 1):
            updates["pinned"] = bool(pinned)
            if pinned == 1:
                if need_pinned_lock:
                    err = await check_pinned_quota()
                    if err:
                        return err
                updates["importance"] = 10
        if digested in (0, 1):
            updates["digested"] = bool(digested)
        if content:
            size_err = check_content_size(content)
            if size_err:
                return size_err
            updates["content"] = content
        if status:
            s = status.strip().lower()
            if s in ("active", "resolved", "abandoned"):
                updates["status"] = s
        if 0 <= weight <= 1:
            updates["weight"] = float(weight)
        if dont_surface in (0, 1):
            updates["dont_surface"] = bool(dont_surface)
        if (
            reserves_high_importance
            and final_importance != requested_importance
        ):
            # Unpinning/restoring surfacing can create an ordinary high slot.
            # Persist quota degradation in the same bucket transaction.
            updates["importance"] = final_importance
        why_remembered = str(why_remembered).strip()
        if why_remembered == "\\clear":
            updates["why_remembered"] = ""
        elif why_remembered:
            updates["why_remembered"] = why_remembered[:500]

        # --- Miss: meaning / media —— 追加是日常操作，整体替换只用于纠错/清理 ---
        if meaning_append.strip():
            updates["meaning_append"] = meaning_append.strip()
        if meaning_replace is not None:
            updates["meaning"] = meaning_replace
        if media_append:
            updates["media_append"] = media_append
        if media_replace is not None:
            updates["media"] = media_replace

        if not updates and not patch_args_supplied:
            return "没有任何字段需要修改。"

        # --- plan 桶：status / content 改变时追加 change_log ---
        content_change_requested = "content" in updates or patch_args_supplied
        is_plan = bucket.get("metadata", {}).get("type") == "plan"
        append_plan_history_in_patch = is_plan and patch_args_supplied
        if is_plan and not patch_args_supplied and (
            "status" in updates or content_change_requested
        ):
            from .._common import append_plan_change_log
            old_meta = bucket.get("metadata", {})
            history = list(old_meta.get("change_log") or [])
            if "status" in updates and updates["status"] != old_meta.get("status"):
                history = append_plan_change_log(
                    history, "status",
                    **{"from": old_meta.get("status"), "to": updates["status"]},
                )
            if content_change_requested:
                history = append_plan_change_log(history, "edit")
            updates["change_log"] = history

        if patch_args_supplied:
            patch_result = await rt.bucket_mgr.update_content_fragment(
                bucket_id,
                old_str=old_str,
                new_str=new_str,
                append_plan_history=append_plan_history_in_patch,
                **updates,
            )
            if not patch_result.get("ok"):
                patch_error = patch_result.get("error")
                if patch_error == "not_found":
                    return f"未找到记忆桶: {bucket_id}"
                if patch_error == "old_str_not_found":
                    return (
                        "未找到 old_str，正文未修改。请从 Dashboard 或对应记忆类型的读取入口"
                        "核对当前原文；普通记忆也可用 "
                        f'breath_advanced(query="{bucket_id}", max_results=1, '
                        "max_tokens=20000) 按完整 bucket_id 读取。复制连续且逐字一致的片段后重试。"
                    )
                if patch_error == "old_str_ambiguous":
                    return (
                        "old_str 在正文中至少出现 2 次，"
                        "无法安全确定要修改哪一处；正文未修改。请提供更长且唯一的原文片段。"
                    )
                if patch_error == "invalid_content":
                    return str(patch_result.get("message") or "替换后的内容不符合存储限制。")
                if patch_error == "unchanged":
                    return "old_str 与 new_str 替换后正文没有变化；本次未修改。"
                return f"修改失败: {bucket_id}"
        else:
            success = await rt.bucket_mgr.update(bucket_id, **updates)
            if not success:
                return f"修改失败: {bucket_id}"

    # 注意：完整正文更新和局部替换都会在 BucketManager 内汇入
    # _update_locked(content=...)，并投递 embedding outbox。这里不需要、也不应该
    # 重复调用 generate_and_store，否则同一条内容会多打一次向量 API。

    # --- plan 桶人工/AI 显式 resolve → 联动 related_bucket / resolved_by ---
    # rule.md §1：plan 是承诺，承诺被显式放下，承载它的事件桶也不该再浮上来。
    # 仅在 trace 把 plan.status 改成 resolved 时触发；其他路径（自动二判）不联动。
    cascaded: list[str] = []
    if (
        bucket.get("metadata", {}).get("type") == "plan"
        and updates.get("status") == "resolved"
    ):
        from .._common import cascade_plan_resolved_to_buckets
        # 用更新后的 metadata 视图，确保 related_bucket / resolved_by 是最新值
        merged_meta = {**bucket.get("metadata", {}), **{k: v for k, v in updates.items() if k != "change_log"}}
        try:
            cascaded = await cascade_plan_resolved_to_buckets(merged_meta, bucket_id)
        except Exception as e:
            rt.logger.warning(f"trace plan cascade outer error: {e}")

    _display_updates = {
        k: v for k, v in updates.items()
        if k not in ("content", "meaning_append", "meaning", "media_append", "media")
    }
    changed = ", ".join(f"{k}={v}" for k, v in _display_updates.items())
    if patch_args_supplied:
        changed += (", content=已局部替换" if changed else "content=已局部替换")
    elif "content" in updates:
        changed += (", content=已替换" if changed else "content=已替换")
    if "meaning_append" in updates:
        changed += (", " if changed else "") + "meaning=已追加一条"
    if "meaning" in updates:
        changed += (", " if changed else "") + f"meaning=整体替换({len(updates['meaning'])}条)"
    if "media_append" in updates:
        changed += (", " if changed else "") + f"media=已追加{len(updates['media_append'])}项"
    if "media" in updates:
        changed += (", " if changed else "") + f"media=整体替换({len(updates['media'])}项)"
    if "resolved" in updates:
        changed += f" → {resolved_hint(bool(updates['resolved']))}"
    if "digested" in updates:
        if updates["digested"]:
            changed += " → 已隐藏，保留但不再浮现"
        else:
            changed += " → 已取消隐藏，重新参与浮现"
    if cascaded:
        changed += f" → 同步把 {len(cascaded)} 个关联事件桶也标为已放下（{', '.join(cascaded)}）"
    return f"已修改记忆桶 {bucket_id}: {changed}"
