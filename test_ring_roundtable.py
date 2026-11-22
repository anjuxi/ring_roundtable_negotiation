"""
环形圆桌的冒烟测试，离线模式就能跑，不需要 Key。
"""

import ring_roundtable as rt;


def test_build_roles():
    # 角色至少三个，立场不能撞车。
    roles = rt.build_roles();
    assert len(roles) >= 3;
    assert len({role.stance for role in roles}) == len(roles);
    print("角色数量与立场互斥检查通过！");


def test_format_history():
    # 历史拼文本时，角色名和内容都不能丢。
    text = rt.format_history([{"角色": "产品经理", "内容": "先上线最小版本"}]);
    assert "产品经理" in text;
    assert "先上线最小版本" in text;
    print("对话历史格式化检查通过！");


def test_parse_json():
    # 模型爱在 JSON 前后加废话，得能抠出来；纯文本也别崩。
    verdict = rt.parse_json('结论如下：{"是否达成共识": true, "讨论结论": "达成一致", "下轮关注点": ""}');
    assert verdict["是否达成共识"] is True;
    assert verdict["讨论结论"] == "达成一致";
    fallback = rt.parse_json("这次就不输出格式了");
    assert fallback["是否达成共识"] is False;
    print("JSON 解析与降级检查通过！");


def test_run_roundtable():
    # 离线跑一整场，轮次和发言数都不能破上限。
    result = rt.run_roundtable(rt.V_讨论话题, rt.build_roles());
    assert result["是否达成共识"] is True;
    assert result["轮次"] <= rt.V_最大轮次;
    assert result["发言条数"] <= rt.V_最大发言条数;
    assert result["对话历史"][0]["角色"] == "主持人";
    assert any(item["角色"] == "安全与风险专家" for item in result["对话历史"]);
    print("完整圆桌流程检查通过！");


if __name__ == "__main__":
    test_build_roles();
    test_format_history();
    test_parse_json();
    test_run_roundtable();
    print("——" * 50);
    print("✅ 全部测试通过！");
