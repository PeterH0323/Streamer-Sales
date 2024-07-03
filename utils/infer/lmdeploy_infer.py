import json
import logging

import streamlit as st
import torch
from lagent.actions import ActionExecutor
from lagent.agents.internlm2_agent import Internlm2Protocol
from lagent.schema import ActionReturn, AgentReturn
from lmdeploy import GenerationConfig

from utils.digital_human.digital_human_worker import gen_digital_human_video_in_spinner
from utils.rag.rag_worker import build_rag_prompt
from utils.tts.tts_worker import gen_tts_in_spinner



def prepare_generation_config(skip_special_tokens=True):

    gen_config = GenerationConfig(
        top_p=0.8,
        temperature=0.7,
        repetition_penalty=1.005,
        skip_special_tokens=skip_special_tokens,
    )  # top_k=40, min_new_tokens=200
    return gen_config


def combine_history(prompt, meta_instruction, history_msg=None, first_input_str=""):
    total_prompt = [{"role": "system", "content": meta_instruction}]

    if first_input_str != "":
        total_prompt.append({"role": "user", "content": first_input_str})

    if history_msg is not None:
        for message in history_msg:
            total_prompt.append({"role": message["role"], "content": message["content"]})

    total_prompt.append({"role": "user", "content": prompt})
    return [total_prompt]


@st.cache_resource
def init_handlers(departure_place, delivery_company_name):
    
    from utils.agent.delivery_time_query import DeliveryTimeQueryAction  # isort:skip

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


def get_agent_result(model_pipe, prompt_input, departure_place, delivery_company_name):

    action_executor, protocol_handler = init_handlers(departure_place, delivery_company_name)

    inner_history = [{"role": "user", "content": prompt_input}]  # NOTE TEST ！！！
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
        for item in model_pipe.stream_infer(prompt, gen_config=prepare_generation_config(skip_special_tokens=False)):
            if "~" in item.text:
                item.text = item.text.replace("~", "。").replace("。。", "。")

            cur_response += item.text

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


def get_turbomind_response(
    prompt,
    meta_instruction,
    user_avator,
    robot_avator,
    model_pipe,
    session_messages,
    add_session_msg=True,
    first_input_str="",
    rag_retriever=None,
    product_name="",
    enable_agent=True,
    departure_place=None,
    delivery_company_name=None,
):

    # ====================== Agent ======================
    agent_response = ""
    if enable_agent:
        GENERATE_AGENT_TEMPLATE = (
            "这是网上获取到的信息：“{}”\n 客户的问题：“{}” \n 请认真阅读信息并运用你的性格进行解答。"  # RAG prompt 模板
        )
        agent_response = get_agent_result(model_pipe, prompt, departure_place, delivery_company_name)
        if agent_response != "":
            agent_response = GENERATE_AGENT_TEMPLATE.format(agent_response, prompt)
            print(f"Agent response: {agent_response}")
    prompt_pro = agent_response

    # ====================== RAG ======================
    if rag_retriever is not None and prompt_pro == "":
        # 如果 Agent 没有执行，则使用 RAG 查询数据库
        prompt_pro = build_rag_prompt(rag_retriever, product_name, prompt)

    # ====================== 加上历史信息 ======================
    real_prompt = combine_history(
        prompt_pro if prompt_pro != "" else prompt,
        meta_instruction,
        history_msg=session_messages,
        first_input_str=first_input_str,
    )  # 是否加上历史对话记录

    print(real_prompt)

    # Add user message to chat history
    if add_session_msg:
        session_messages.append({"role": "user", "content": prompt, "avatar": user_avator})

    with st.chat_message("assistant", avatar=robot_avator):
        message_placeholder = st.empty()
        cur_response = ""
        for item in model_pipe.stream_infer(real_prompt, gen_config=prepare_generation_config()):

            if "~" in item.text:
                item.text = item.text.replace("~", "。").replace("。。", "。")

            cur_response += item.text
            message_placeholder.markdown(cur_response + "▌")
        message_placeholder.markdown(cur_response)

        tts_save_path = gen_tts_in_spinner(cur_response)  # 一整句生成
        gen_digital_human_video_in_spinner(tts_save_path)

        # Add robot response to chat history
        session_messages.append(
            {
                "role": "assistant",
                "content": cur_response,  # pylint: disable=undefined-loop-variable
                "avatar": robot_avator,
                "wav": tts_save_path,
            }
        )
    torch.cuda.empty_cache()
