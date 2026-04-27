---
id: agent.memory_native_kernel
kind: Agent
status: published
maturity: runtime_ready
lens: lens.agent
source_refs:
  - evidence.system.memory_native_blueprint
tags:
  - architecture
  - kernel
---

# Memory-Native Agent Kernel

## Summary

统一以 MemoryView 和 CapabilityView 驱动运行时，不再直接拼接 Memory 原文进入 Prompt。

## Fields

- 角色定位：负责 Observe -> Orient -> Act -> Reflect -> Commit 的智能体内核
- 推荐技能：skill/core/memory, skill/core/query
- 推荐工具：graph.health
- 输入：用户任务、附件、运行时状态
- 输出：结构化回复、工具调用和 Proposal 提示

## Relations

- uses: [[skill/core/memory]]
- uses: [[skill/core/query]]
- can_activate: [[graph.health]]

## Runtime Notes

达到 runtime_ready 后，Prompt 仅拼 Identity、Task、MemoryView、CapabilityView、RuntimeState、ResponseContract。

## Evidence

- evidence.system.memory_native_blueprint
