import json
import logging

from lagent.actions import ActionExecutor
from lagent.agents.internlm2_agent import Internlm2Protocol
from lagent.schema import ActionReturn, AgentReturn
from loguru import logger

from .delivery_time_query import DeliveryTimeQueryAction


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

    # 第一次将 prompt 生成 agent 形式的 prompt
    # [{'role': 'system', 'content': '当开启工具以及代码时，根据需求选择合适的工具进行调用'},
    # {'role': 'system', 'content': '你可以使用如下工具：\n[\n    {\n        "name": "ArxivSearch.get_arxiv_article_information",\n
    #                                                                       "description": "This is the subfunction for tool \'ArxivSearch\', you can use this tool. The description of this function is: \\nRun Arxiv search and get the article meta information.",\n
    #                                                                       "parameters": [\n            {\n                "name": "query",\n                "type": "STRING",\n                "description": "the content of search query"\n            }\n        ],\n        "required": [\n            "query"\n        ],\n        "return_data": [\n            {\n                "name": "content",\n                "description": "a list of 3 arxiv search papers",\n                "type": "STRING"\n            }\n        ],\n        "parameter_description": "If you call this tool, you must pass arguments in the JSON format {key: value}, where the key is the parameter name."\n    }\n]\n
    #                                                       如果你已经获得足够信息，请直接给出答案. 避免不必要的工具调用! 同时注意你可以使用的工具，不要随意捏造！',
    #                                       'name': 'plugin'},
    # {'role': 'user', 'content': '帮我搜索 InternLM2 Technical Report'}]

    # 推理得出：'<|action_start|><|plugin|>\n{"name": "ArxivSearch.get_arxiv_article_information", "parameters": {"query": "InternLM2 Technical Report"}}<|action_end|>\n'
    # 放入 assient 中

    # 使用 ArxivSearch.get_arxiv_article_information 方法得出结果，放到 envrinment 里面，结果是：
    # [{'role': 'system', 'content': '当开启工具以及代码时，根据需求选择合适的工具进行调用'},
    # {'role': 'system', 'content': '你可以使用如下工具：\n[\n    {\n        "name": "ArxivSearch.get_arxiv_article_information",\n        "description": "This is the subfunction for tool \'ArxivSearch\', you can use this tool. The description of this function is: \\nRun Arxiv search and get the article meta information.",\n        "parameters": [\n            {\n                "name": "query",\n                "type": "STRING",\n                "description": "the content of search query"\n            }\n        ],\n        "required": [\n            "query"\n        ],\n        "return_data": [\n            {\n                "name": "content",\n                "description": "a list of 3 arxiv search papers",\n                "type": "STRING"\n            }\n        ],\n        "parameter_description": "If you call this tool, you must pass arguments in the JSON format {key: value}, where the key is the parameter name."\n    }\n]\n如果你已经获得足够信息，请直接给出答案. 避免不必要的工具调用! 同时注意你可以使用的工具，不要随意捏造！', 'name': 'plugin'},
    # {'role': 'user', 'content': '帮我搜索 InternLM2 Technical Report'},
    # {'role': 'assistant', 'content': '<|action_start|><|plugin|>\n{"name": "ArxivSearch.get_arxiv_article_information", "parameters": {"query": "InternLM2 Technical Report"}}<|action_end|>\n'},
    # {'role': 'environment', 'content': '{"content": "Published: 2024-03-26\\nTitle: InternLM2 Technical Report\\nAuthors: Zheng Cai, Maosong Cao, Haojiong Chen, Kai Chen, Keyu Chen, Xin Chen, Xun Chen, Zehui Chen, Zhi Chen, Pei Chu, Xiaoyi Dong, Haodong Duan, Qi Fan, Zhaoye Fei, Yang Gao, Jiaye Ge, Chenya Gu, Yuzhe Gu, Tao Gui, Aijia Guo, Qipeng Guo, Conghui He, Yingfan Hu, Ting Huang, Tao Jiang, Penglong Jiao, Zhenjiang Jin, Zhikai Lei, Jiaxing Li, Jingwen Li, Linyang Li, Shuaibin Li, Wei Li, Yining Li, Hongwei Liu, Jiangning Liu, Jiawei Hong, Kaiwen Liu, Kuikun Liu, Xiaoran Liu, Chengqi Lv, Haijun Lv, Kai Lv, Li Ma, Runyuan Ma, Zerun Ma, Wenchang Ning, Linke Ouyang, Jiantao Qiu, Yuan Qu, Fukai Shang, Yunfan Shao, Demin Song, Zifan Song, Zhihao Sui, Peng Sun, Yu Sun, Huanze Tang, Bin Wang, Guoteng Wang, Jiaqi Wang, Jiayu Wang, Rui Wang, Yudong Wang, Ziyi Wang, Xingjian Wei, Qizhen Weng, Fan Wu, Yingtong Xiong, Chao Xu, Ruiliang Xu, Hang Yan, Yirong Yan, Xiaogui Yang, Haochen Ye, Huaiyuan Ying, Jia Yu, Jing Yu, Yuhang Zang, Chuyu Zhang, Li Zhang, Pan Zhang, Peng Zhang, Ruijie Zhang, Shuo Zhang, Songyang Zhang, Wenjian Zhang, Wenwei Zhang, Xingcheng Zhang, Xinyue Zhang, Hui Zhao, Qian Zhao, Xiaomeng Zhao, Fengzhe Zhou, Zaida Zhou, Jingming Zhuo, Yicheng Zou, Xipeng Qiu, Yu Qiao, Dahua Lin\\nSummary: The evolution of Large Language Models (LLMs) like ChatGPT and GPT-4 has\\nsparked discussions on the advent of Artificial General Intelligence (AGI).\\nHowever, replicating such advancements in open-source models has been\\nchallenging. This paper introduces InternLM2, an open-source LLM that\\noutperforms its predecessors in comprehensive evaluations across 6 dimensions\\nand 30 benchmarks, long-context modeling, and open-ended subjective evaluations\\nthrough innovative pre-training and optimization techniques. The pre-training\\nprocess of InternLM2 is meticulously detailed, highlighting the preparation of\\ndiverse data types including text, code, and long-context data. InternLM2\\nefficiently captures long-term dependencies, initially trained on 4k tokens\\nbefore advancing to 32k tokens in pre-training and fine-tuning stages,\\nexhibiting remarkable performance on the 200k ``Needle-in-a-Haystack\\" test.\\nInternLM2 is further aligned using Supervised Fine-Tuning (SFT) and a novel\\nConditional Online Reinforcement Learning from Human Feedback (COOL RLHF)\\nstrategy that addresses conflicting human preferences and reward hacking. By\\nreleasing InternLM2 models in different training stages and model sizes, we\\nprovide the community with insights into the model\'s evolution.\\n\\nPublished: 2017-07-27\\nTitle: Cumulative Reports of the SoNDe Project July 2017\\nAuthors: Sebastian Jaksch, Ralf Engels, Günter Kemmerling, Codin Gheorghe, Philip Pahlsson, Sylvain Désert, Frederic Ott\\nSummary: This are the cumulated reports of the SoNDe detector Project as of July 2017.\\nThe contained reports are: - Report on the 1x1 module technical demonstrator -\\nReport on used materials - Report on radiation hardness of components - Report\\non potential additional applications - Report on the 2x2 module technical\\ndemonstrator - Report on test results of the 2x2 technical demonstrator\\n\\nPublished: 2023-03-12\\nTitle: Banach Couples. I. Elementary Theory\\nAuthors: Jaak Peetre, Per Nilsson\\nSummary: This note is an (exact) copy of the report of Jaak Peetre, \\"Banach Couples.\\nI. Elementary Theory\\". Published as Technical Report, Lund (1971). Some more\\nrecent general references have been added and some references updated though"}', 'name': 'plugin'}]

    # 然后调用大模型推理总结，stream 输出

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

        # 根据 tokenizer_config.json 中查找到特殊的 token ：
        # token_map = {
        #     92538: "<|plugin|>",
        #     92539: "<|interpreter|>",
        #     92540: "<|action_end|>",
        #     92541: "<|action_start|>",
        # }

        # 将 prompt 给模型
        # [{'role': 'system', 'content': '当开启工具以及代码时，根据需求选择合适的工具进行调用'},
        # {'role': 'system', 'content': '你可以使用如下工具：\n[\n    {\n        "name": "ArxivSearch.get_arxiv_article_information",\n
        #                                                                       "description": "This is the subfunction for tool \'ArxivSearch\', you can use this tool. The description of this function is: \\nRun Arxiv search and get the article meta information.",\n
        #                                                                       "parameters": [\n            {\n                "name": "query",\n                "type": "STRING",\n                "description": "the content of search query"\n            }\n        ],\n        "required": [\n            "query"\n        ],\n        "return_data": [\n            {\n                "name": "content",\n                "description": "a list of 3 arxiv search papers",\n                "type": "STRING"\n            }\n        ],\n        "parameter_description": "If you call this tool, you must pass arguments in the JSON format {key: value}, where the key is the parameter name."\n    }\n]\n
        #                                                       如果你已经获得足够信息，请直接给出答案. 避免不必要的工具调用! 同时注意你可以使用的工具，不要随意捏造！',
        #                                       'name': 'plugin'},
        # {'role': 'user', 'content': '帮我搜索 InternLM2 Technical Report'}]

        # skip_special_tokens = False 输出 <|action_start|> <|plugin|> 等特殊字符
        # for item in model_pipe.stream_infer(prompt, gen_config=prepare_generation_config(skip_special_tokens=False)):

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
                # agent_return.state = agent_state
                agent_return.response = action

        print(f"Agent response: {cur_response}")

        if name:
            print(f"Agent action: {action}")
            action_return: ActionReturn = executor(action["name"], action["parameters"])
            # action_return.thought = language
            # agent_return.actions.append(action_return)
            try:
                return_str = action_return.result[0]["content"]
                return return_str
            except Exception as e:
                return ""

            # agent_return_list.append(dict(role='assistant', name=name, content=action))
            # agent_return_list.append(protocol_handler.format_response(action_return, name=name))

        # inner_history.append(dict(role="language", content=language))

        if not name:
            agent_return.response = language
            break
        # elif action_return.type == executor.finish_action.name:
        #     try:
        #         response = action_return.args["text"]["response"]
        #     except Exception:
        #         logging.info(msg="Unable to parse FinishAction.")
        #         response = ""
        #     agent_return.response = response
        #     break
        # else:
        #     inner_history.append(dict(role="tool", content=action, name=name))
        #     inner_history.append(protocol_handler.format_response(action_return, name=name))
        #     # agent_state += 1
        #     # agent_return.state = agent_state
        #     # yield agent_return
    return ""
