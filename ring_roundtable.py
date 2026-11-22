"""
环形圆桌协商架构（轮询对等型）。

三个立场不同的专家 Agent 按固定顺序轮流发言，主持人负责开场、控节奏、判断收敛。
默认用离线模拟回复，把 V_离线演示 改成 False 并配好 OPENAI_API_KEY 才会走真实模型。
"""

# 依赖
import json;
import os;
from dataclasses import dataclass;

try:
    from openai import OpenAI;
except ImportError:
    OpenAI = None;


# 常量
V_最大轮次 = 3;  # 圆桌最多开几轮，超过就强制收尾，防止无限循环辩论。
V_最大发言条数 = 12;  # 累计发言上限，防止 token 成本失控。
V_模型名称 = "gpt-4o-mini";  # 线上模式用的模型名，换成任意 OpenAI 兼容模型都可以。
V_接口地址 = "https://api.chatanywhere.tech/v1";  # OpenAI 兼容接口地址，按自己的服务改。
V_离线演示 = True;  # 没有 API Key 时保持 True，用内置模拟发言把全流程跑通。
V_讨论话题 = "是否要在两周内把客服系统接入大模型自动回复功能";


# 角色结构
@dataclass
class RoundTableRole:
    # 一位圆桌参与者：名字、立场、系统提示词。
    name: str;
    stance: str;
    system_prompt: str;


# 主流程
def main():
    # 项目入口，准备好角色就发起讨论。
    roles = build_roles();
    print("——" * 50);
    print("环形圆桌协商架构（轮询对等型）演示！");
    print(f"参会角色：{'、'.join([role.name for role in roles])}！");
    print(f"讨论议题：{V_讨论话题}！");
    result = run_roundtable(V_讨论话题, roles);
    return result;


# 圆桌逻辑
def build_roles():
    # 组装参会角色。三方立场故意错开，不然讨论会变成互相点头。
    roles = [
        RoundTableRole(
            name="产品经理",
            stance="尽快上线抢反馈，主张先做最小可用版本",
            system_prompt=(
                "你是产品经理，立场是尽快上线、拿真实用户反馈，倾向先做最小可用版本。"
                "发言要结合用户价值和交付节奏，不要重复别人的原话，控制在 120 字以内，不要客套。"
            ),
        ),
        RoundTableRole(
            name="研发负责人",
            stance="关心实现成本、稳定性和后续维护",
            system_prompt=(
                "你是研发负责人，关心技术可行性、稳定性和长期维护成本，讨厌为了赶工期牺牲工程质量。"
                "发言要给出具体的技术约束和时间估算，不要重复别人的原话，控制在 120 字以内，不要客套。"
            ),
        ),
        RoundTableRole(
            name="安全与风险专家",
            stance="关注合规、幻觉风险和错误回复的兜底",
            system_prompt=(
                "你是安全与风险专家，关注合规、模型幻觉和错误回复对外造成的影响，坚持要有兜底和留痕。"
                "发言要指出具体风险点并提出可执行的约束，不要重复别人的原话，控制在 120 字以内，不要客套。"
            ),
        ),
    ];
    return roles;


def run_roundtable(topic, roles):
    # 跑完整场圆桌，返回共识状态、轮次、发言数和对话历史。
    history = [
        {
            "角色": "主持人",
            "内容": f"今天的议题是：{topic}。请各位按顺序发言，观点不同就当场质疑，不要客套。",
        }
    ];
    print("——" * 50);
    print(f"【主持人】{history[0]['内容'].rstrip('。')}！");
    round_index = 0;
    is_consensus = False;
    conclusion = "";
    while round_index < V_最大轮次 and len(history) < V_最大发言条数 and not is_consensus:
        round_index += 1;
        print("——" * 50);
        print(f"第{round_index}轮讨论开始！");
        for role in roles:
            if len(history) >= V_最大发言条数:
                print("已经达到最大发言条数，本轮提前收尾！");
                break;
            speech = generate_speech(role, history);
            history.append({"角色": role.name, "内容": speech});
            print(f"【{role.name}】{speech.rstrip('。')}！");
        verdict = judge_round(topic, history, round_index);
        is_consensus = verdict["是否达成共识"];
        conclusion = verdict["讨论结论"];
        print(f"【主持人裁决】{conclusion.rstrip('。')}！");
        if verdict["下轮关注点"] and not is_consensus:
            print(f"【下轮关注点】{verdict['下轮关注点'].rstrip('。')}！");
    summary = build_summary(topic, history, conclusion, is_consensus);
    print("——" * 50);
    print("✅ 圆桌讨论结束！");
    print(f"✅ 是否达成共识：{'是' if is_consensus else '否'}！");
    print(f"✅ 最终结论：{summary.rstrip('。')}！");
    print(f"✅ 讨论轮次：{round_index} 轮，累计发言：{len(history)} 条！");
    return {
        "是否达成共识": is_consensus,
        "轮次": round_index,
        "发言条数": len(history),
        "结论": summary,
        "对话历史": history,
    };


def generate_speech(role, history):
    # 生成某位角色这一轮的发言，离线走模拟，线上走模型。
    if V_离线演示:
        return mock_speech(role, history);
    prompt = (
        f"当前讨论记录如下：\n{format_history(history)}\n\n"
        "请以你的角色身份继续发言，可以补充观点，也可以直接反驳前面发言里的漏洞。"
    );
    return chat_completion(role.system_prompt, prompt);


def mock_speech(role, history):
    # 离线演示用的固定发言，没有 Key 也能把讨论跑完整。
    spoken_count = len([item for item in history if item["角色"] != "主持人"]);
    if role.name == "产品经理":
        if spoken_count < 3:
            return "我主张先做一个最小可用版本，两周内上线常见问题自动回复，先把真实用户反馈拿回来。";
        return "我认可风险专家的顾虑，可以把自动回复限制在低风险问题，敏感问题一律转人工。";
    if role.name == "研发负责人":
        if spoken_count < 3:
            return "技术上两周能做出原型，但知识库检索、日志和回滚开关至少要预留三天，否则线上出问题没法收场。";
        return "既然只做受限试点，我可以把回滚开关和人工接管做进第一版，但灰度范围要控制在一成流量。";
    if role.name == "安全与风险专家":
        if spoken_count < 3:
            return "自动回复对外说错话就是公司承诺，我要求敏感问题转人工，并且每条回复都要留痕可追溯。";
        return "如果产品同意敏感问题转人工、研发保证全程留痕，我这边可以签字放行这个试点。";
    return f"我从{role.stance}的角度补充一点看法，建议先把验证指标定下来。";


def format_history(history):
    # 把对话历史拼成纯文本，直接塞进模型上下文。
    lines = [f"{item['角色']}：{item['内容']}" for item in history];
    return "\n".join(lines);


def chat_completion(system_prompt, user_content):
    # 调 OpenAI 兼容接口，拿到纯文本回复。
    if OpenAI is None:
        raise RuntimeError("没有安装 openai 库，请先执行 pip install openai。");
    api_key = os.environ.get("OPENAI_API_KEY");
    if not api_key:
        raise RuntimeError("没有检测到 OPENAI_API_KEY，请配置环境变量，或者把 V_离线演示 保持为 True。");
    client = OpenAI(api_key=api_key, base_url=V_接口地址);
    response = client.chat.completions.create(
        model=V_模型名称,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
    );
    return response.choices[0].message.content.strip();


def judge_round(topic, history, round_index):
    # 主持人裁决：这一轮是否收敛，下一轮该追问什么。
    if V_离线演示:
        return mock_judgment(topic, round_index);
    moderator_prompt = (
        "你是圆桌主持人，只负责控场，不参与专业辩论。"
        "你需要判断讨论是否已经达成可执行的共识，并指出下一轮最该追问的点。"
        "只输出一个 JSON 对象，不要输出其它文字。"
    );
    prompt = (
        f"议题：{topic}\n讨论记录：\n{format_history(history)}\n\n"
        '请按这个格式输出：{"是否达成共识": true 或 false, "讨论结论": "一句话结论", "下轮关注点": "下一轮最该追问的点"}'
    );
    return parse_json(chat_completion(moderator_prompt, prompt));


def mock_judgment(topic, round_index):
    # 模拟主持人裁决，第一轮压着不收，第二轮放行。
    if round_index < 2:
        return {
            "是否达成共识": False,
            "讨论结论": "第一轮各方立场都摆出来了，但风险约束还没有落到具体动作，先别急着收。",
            "下轮关注点": "请各位回应安全专家的合规要求，给出一个能落地的折中方案。",
        };
    return {
        "是否达成共识": True,
        "讨论结论": "各方同意先做两周的受限试点，只覆盖常见问题，保留人工兜底和随时回滚的开关。",
        "下轮关注点": "",
    };


def parse_json(text):
    # 从模型回复里抠 JSON。解析不出来就当成“还没达成共识”，别让流程崩。
    start = text.find("{");
    end = text.rfind("}");
    if start == -1 or end == -1:
        return {
            "是否达成共识": False,
            "讨论结论": text.strip() or "模型没有给出可解析的结论",
            "下轮关注点": "",
        };
    try:
        data = json.loads(text[start : end + 1]);
    except json.JSONDecodeError:
        return {
            "是否达成共识": False,
            "讨论结论": text.strip(),
            "下轮关注点": "",
        };
    return {
        "是否达成共识": bool(data.get("是否达成共识", False)),
        "讨论结论": str(data.get("讨论结论", "")).strip(),
        "下轮关注点": str(data.get("下轮关注点", "")).strip(),
    };


def build_summary(topic, history, conclusion, is_consensus):
    # 生成最终结论，线下直接用裁决结果拼一句，线上交给主持人汇总。
    if V_离线演示:
        if is_consensus:
            return f"围绕“{topic}”，{conclusion.rstrip('。')}";
        return f"围绕“{topic}”，讨论没有收敛：{conclusion.rstrip('。')}";
    prompt = (
        f"议题：{topic}\n讨论记录：\n{format_history(history)}\n\n"
        "请用三句话以内给出最终结论，明确说清达成的共识和仍需跟进的事项。"
    );
    return chat_completion("你是圆桌主持人，负责汇总讨论结论，不参与辩论。", prompt);


if __name__ == "__main__":
    main();
