from __future__ import annotations

ENTITY_TYPE_TO_PROTOCOL = {
    "智能体": "agent",
    "技能": "skill",
    "工具箱": "toolbox",
    "工具": "tool",
    "系统页面": "knowledge",
    "业务知识": "knowledge",
    "元结构": "schema",
}

PROTOCOL_TO_ENTITY_TYPE = {value: key for key, value in ENTITY_TYPE_TO_PROTOCOL.items()}
PROTOCOL_TO_ENTITY_TYPE.update({
    "agent": "智能体",
    "skill": "技能",
    "toolbox": "工具箱",
    "tool": "工具",
    "knowledge": "系统页面",
    "schema": "元结构",
})

FIELD_ALIASES = {
    "实体类型": "type",
    "实体名称": "name",
    "唯一标识": "id",
    "所属工具箱": "toolbox",
    "所属分类": "categories",
    "当前状态": "status",
    "锁定状态": "lock_status",
    "禁用状态": "disabled_status",
    "权限等级": "permission_level",
        "工具权限等级": "tool_permission_level",
    "激活方式": "activation",
    "根技能": "root_skill",
    "可用工具箱": "toolboxes",
    "最大上下文长度": "max_prompt_chars",
    "模型服务": "provider",
    "模型名称": "model",
    "允许工具分类": "allowed_tool_categories",
    "禁止工具分类": "denied_tool_categories",
    "禁止工具": "denied_tools",
    "模块路径": "module",
    "类名称": "class",
    "风险等级": "risk_level",
    "最近更新": "updated_at",
    "作用范围": "scope",
    "局部关系": "local_relations",
    "依赖文件": "dependency_files",
    "更新策略": "update_policy",
}

PERMISSION_TO_LEVEL = {
    "只读": 1,
    "低风险": 1,
    "草稿": 2,
    "编辑": 2,
    "治理": 3,
    "管理员": 3,
    "发布": 4,
    "高权限": 4,
}

LEVEL_TO_PERMISSION = {1: "只读", 2: "草稿", 3: "治理", 4: "发布"}

ACTIVATION_TO_PROTOCOL = {
    "默认激活": "always",
    "永久激活": "always",
    "手动激活": "manual",
    "技能激活": "skill",
    "规则激活": "rule",
}

PROTOCOL_TO_ACTIVATION = {
    "always": "默认激活",
    "manual": "手动激活",
    "skill": "技能激活",
    "rule": "规则激活",
}

CATEGORY_TO_PROTOCOL = {
    "Wiki": "wiki",
    "治理": "governance",
    "版本": "version",
    "只读": "wiki_read",
    "文本": "text",
    "本地计算": "local_compute",
    "数据处理": "data_processing",
    "报告": "report",
    "文档": "document",
    "企业接口": "enterprise_api",
    "云服务": "cloud",
    "远程接口": "remote_api",
    "数模": "cad",
    "工作流": "workflow",
    "系统": "system",
    "外部": "external",
}

PROTOCOL_TO_CATEGORY = {value: key for key, value in CATEGORY_TO_PROTOCOL.items()}

TOOLBOX_DISPLAY_TO_ID = {
    "Wiki 治理工具箱": "wiki_app",
    "Wiki 只读工具箱": "wiki",
    "NX 工具箱": "nx",
    "Cloude 企业接口工具箱": "cloude",
    "设计报告工具箱": "design_report",
    "文本处理工具箱": "textops",
    "文件工具箱": "files",
    "命令工具箱": "shell",
    "工作区工具箱": "workspace",
    "任务工具箱": "task",
    "待办工具箱": "todo",
}

TOOLBOX_ID_TO_DISPLAY = {value: key for key, value in TOOLBOX_DISPLAY_TO_ID.items()}

def strip_link(value: str) -> str:
    raw = str(value or "").strip()
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].strip()
    if "|" in raw:
        left, right = raw.split("|", 1)
        raw = right.strip() or left.strip()
    return raw

def normalize_scalar(value: str):
    raw = strip_link(str(value or "").strip().strip("`"))
    if raw in PERMISSION_TO_LEVEL:
        return PERMISSION_TO_LEVEL[raw]
    if raw in ACTIVATION_TO_PROTOCOL:
        return ACTIVATION_TO_PROTOCOL[raw]
    if raw in ENTITY_TYPE_TO_PROTOCOL:
        return ENTITY_TYPE_TO_PROTOCOL[raw]
    if raw in TOOLBOX_DISPLAY_TO_ID:
        return TOOLBOX_DISPLAY_TO_ID[raw]
    if raw.isdigit():
        return int(raw)
    return raw

def normalize_list(values: list[str]) -> list[str]:
    out: list[str] = []
    for item in values:
        raw = strip_link(str(item or "").strip().strip("`"))
        if not raw or raw == "待补充":
            continue
        if raw in CATEGORY_TO_PROTOCOL:
            raw = CATEGORY_TO_PROTOCOL[raw]
        elif raw in TOOLBOX_DISPLAY_TO_ID:
            raw = TOOLBOX_DISPLAY_TO_ID[raw]
        out.append(raw)
    return out
