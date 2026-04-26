from __future__ import annotations

DESIGN_RULES = [
    {"rule_ref": "MAT-001", "part_type": "*", "rule_name": "材料不能为空", "severity": "high", "rule_text": "材料牌号不能为空，且必须可映射到企业材料库。"},
    {"rule_ref": "ROD-101", "part_type": "connecting_rod", "rule_name": "中心距为正", "severity": "high", "rule_text": "连杆中心距必须为正数。"},
    {"rule_ref": "ROD-102", "part_type": "connecting_rod", "rule_name": "小头孔径为正", "severity": "high", "rule_text": "小头孔径必须为正数。"},
    {"rule_ref": "ROD-103", "part_type": "connecting_rod", "rule_name": "大头孔径大于小头孔径", "severity": "high", "rule_text": "大头孔径通常应大于小头孔径。"},
    {"rule_ref": "CRK-101", "part_type": "crankshaft", "rule_name": "行程为正", "severity": "high", "rule_text": "曲轴行程必须为正数。"},
    {"rule_ref": "CRK-102", "part_type": "crankshaft", "rule_name": "主轴颈直径为正", "severity": "high", "rule_text": "主轴颈直径必须为正数。"},
    {"rule_ref": "CRK-103", "part_type": "crankshaft", "rule_name": "连杆轴颈直径为正", "severity": "high", "rule_text": "连杆轴颈直径必须为正数。"},
    {"rule_ref": "CAM-101", "part_type": "camshaft", "rule_name": "凸轮数为正整数", "severity": "high", "rule_text": "凸轮数量必须为正整数。"},
    {"rule_ref": "CAM-102", "part_type": "camshaft", "rule_name": "升程为正", "severity": "high", "rule_text": "升程必须为正数。"},
    {"rule_ref": "CAM-103", "part_type": "camshaft", "rule_name": "持续角应在0到360之间", "severity": "medium", "rule_text": "持续角应处于 0~360 度区间。"},
]

FIELD_REQUIREMENTS = [
    {"part_type": "connecting_rod", "field": "material", "required": True, "group": "basic", "ask_text": "请确认连杆材料牌号。", "rule_ref": "MAT-001", "order": 10},
    {"part_type": "connecting_rod", "field": "center_distance", "required": True, "group": "geometry", "ask_text": "请提供连杆中心距。", "rule_ref": "ROD-101", "order": 20},
    {"part_type": "connecting_rod", "field": "small_end_diameter", "required": True, "group": "geometry", "ask_text": "请提供小头孔径。", "rule_ref": "ROD-102", "order": 30},
    {"part_type": "connecting_rod", "field": "big_end_diameter", "required": True, "group": "geometry", "ask_text": "请提供大头孔径。", "rule_ref": "ROD-103", "order": 40},
    {"part_type": "crankshaft", "field": "stroke", "required": True, "group": "geometry", "ask_text": "请提供曲轴行程。", "rule_ref": "CRK-101", "order": 20},
    {"part_type": "crankshaft", "field": "main_journal_diameter", "required": True, "group": "geometry", "ask_text": "请提供主轴颈直径。", "rule_ref": "CRK-102", "order": 30},
    {"part_type": "crankshaft", "field": "rod_journal_diameter", "required": True, "group": "geometry", "ask_text": "请提供连杆轴颈直径。", "rule_ref": "CRK-103", "order": 40},
    {"part_type": "camshaft", "field": "cam_count", "required": True, "group": "basic", "ask_text": "请确认凸轮数量。", "rule_ref": "CAM-101", "order": 20},
    {"part_type": "camshaft", "field": "lift", "required": True, "group": "motion", "ask_text": "请提供升程。", "rule_ref": "CAM-102", "order": 30},
    {"part_type": "camshaft", "field": "duration_angle", "required": True, "group": "motion", "ask_text": "请提供持续角。", "rule_ref": "CAM-103", "order": 40},
]

TOOL_CATALOG = [
    {"tool_ref": "textops.parse_text_from_url", "tool_role": "file_parse", "title": "解析文本/结构化文件", "enabled": True},
    {"tool_ref": "textops.parse_docx_from_url", "tool_role": "file_parse", "title": "解析 docx 文件", "enabled": True},
    {"tool_ref": "textops.design_rule_lookup", "tool_role": "rule_lookup", "title": "设计规则检索", "enabled": True},
    {"tool_ref": "textops.parameter_check", "tool_role": "parameter_check", "title": "参数校核", "enabled": True},
    {"tool_ref": "textops.estimate_action_cost", "tool_role": "cost_estimate", "title": "动作成本估算", "enabled": True},
    {"tool_ref": "cloude.query_ecr_list", "tool_role": "enterprise_query", "title": "ECR信息查询", "enabled": True},
    {"tool_ref": "cloude.query_ipm_list", "tool_role": "enterprise_query", "title": "IPM信息查询", "enabled": True},
    {"tool_ref": "nx.BuildCamshaftOneClick", "tool_role": "cad_automation", "title": "凸轮轴一键建模", "enabled": True},
    {"tool_ref": "design_report.create_report", "tool_role": "report", "title": "创建设计报告", "enabled": True},
]

KNOWLEDGE_CATALOG = [
    {"knowledge_ref": "catalog.field_requirement", "knowledge_type": "field_requirement", "title": "参数缺口规则目录", "source": "embedded"},
    {"knowledge_ref": "catalog.design_rules", "knowledge_type": "design_rule", "title": "设计规则目录", "source": "embedded"},
    {"knowledge_ref": "wiki.protocol", "knowledge_type": "system_protocol", "title": "Wiki Page / ProtocolView 运行协议", "source": "wiki"},
]

PART_ALIASES = {"连杆": "connecting_rod", "曲轴": "crankshaft", "凸轮轴": "camshaft"}
