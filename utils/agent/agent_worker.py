import json
import logging

from lagent.actions import ActionExecutor
from lagent.agents.internlm2_agent import Internlm2Protocol
from lagent.schema import ActionReturn, AgentReturn
from loguru import logger

from utils.agent.delivery_time_query import DeliveryTimeQueryAction


def init_handlers(departure_place, delivery_company_name):
    META_CN = "当开启工具以及代码时，根据需求选择合适的工具进行调用"

    INTERPRETER_CN = (
        "你现在已经能够在一个有状态的 Jupyter 笔记本环境中运行 Python 代码。"
        "当你向 python 发送含有 Python 代码的消息时，它将在该环境中执行。"
        "这个工具适用于多种场景，如数据分析或处理（包括数据操作、统计分析、图表绘制），"
        "复杂的计算问题（解决数学和物理难题），编程示例（理解编程概念或特性），"
        "文本处理和分析（比如文本解析和自然语言处理），"
        "机器学习和数据科学（用于展示模型训练和数据可视化），"
        "以及文件操作和数据导入（处理CSV、JSON等格式的文件）。"
    )

    PLUGIN_CN = (
        "你可以使用如下工具："
        "\n{prompt}\n"
        "如果你已经获得足够信息，请直接给出答案. 避免不必要的工具调用! "
        "同时注意你可以使用的工具，不要随意捏造！"
    )

    protocol_handler = Internlm2Protocol(
        meta_prompt=META_CN,
        interpreter_prompt=INTERPRETER_CN,
        plugin_prompt=PLUGIN_CN,
        tool=dict(
            begin="{start_token}{name}\n",
            start_token="<|action_start|>",
            name_map=dict(plugin="<|plugin|>", interpreter="<|interpreter|>"),
            belong="assistant",
            end="<|action_end|>\n",
        ),
    )
    action_list = [
        DeliveryTimeQueryAction(
            departure_place=departure_place,
            delivery_company_name=delivery_company_name,
        ),
    ]
    plugin_map = {action.name: action for action in action_list}
    plugin_name = [action.name for action in action_list]
    plugin_action = [plugin_map[name] for name in plugin_name]
    action_executor = ActionExecutor(actions=plugin_action)

    return action_executor, protocol_handler


def get_agent_result(llm_model_handler, prompt_input, departure_place, delivery_company_name):

    action_executor, protocol_handler = init_handlers(departure_place, delivery_company_name)

    # 判断 name is None ，跳出循环
    inner_history = [{"role": "user", "content": prompt_input}]
    interpreter_executor = None
    max_turn = 7
    for _ in range(max_turn):

        prompt = protocol_handler.format(  # 生成 agent prompt
            inner_step=inner_history,
            plugin_executor=action_executor,
            interpreter_executor=interpreter_executor,
        )
        cur_response = ""

        agent_return = AgentReturn()

        logger.info(f"agent input for llm: {prompt}")

        model_name = llm_model_handler.available_models[0]
        for item in llm_model_handler.chat_completions_v1(
            model=model_name, messages=prompt, stream=True, skip_special_tokens=False
        ):
            # 从 prompt 推理结果例子：
            # '<|action_start|><|plugin|>\n{"name": "ArxivSearch.get_arxiv_article_information", "parameters": {"query": "InternLM2 Technical Report"}}<|action_end|>\n'

            logger.info(f"agent return = {item}")
            if "content" not in item["choices"][0]["delta"]:
                continue
            current_res = item["choices"][0]["delta"]["content"]

            if "~" in current_res:
                current_res = item.text.replace("~", "。").replace("。。", "。")

            cur_response += current_res

            logger.info(f"agent return = {item}")

            name, language, action = protocol_handler.parse(
                message=cur_response,
                plugin_executor=action_executor,
                interpreter_executor=interpreter_executor,
            )
            if name:  # "plugin"
                if name == "plugin":
                    if action_executor:
                        executor = action_executor
                    else:
                        logging.info(msg="No plugin is instantiated!")
                        continue
                    try:
                        action = json.loads(action)
                    except Exception as e:
                        logging.info(msg=f"Invaild action {e}")
                        continue
                elif name == "interpreter":
                    if interpreter_executor:
                        executor = interpreter_executor
                    else:
                        logging.info(msg="No interpreter is instantiated!")
                        continue

                agent_return.response = action

        print(f"Agent response: {cur_response}")

        if name:
            print(f"Agent action: {action}")
            action_return: ActionReturn = executor(action["name"], action["parameters"])

            try:
                return_str = action_return.result[0]["content"]
                return return_str
            except Exception as e:
                return ""

        if not name:
            agent_return.response = language
            break

    return ""
