from pathlib import Path

import streamlit as st
import torch
from lmdeploy import GenerationConfig, TurbomindEngineConfig, pipeline
from modelscope import snapshot_download

from utils.rag.retriever import CacheRetriever


def prepare_generation_config():

    gen_config = GenerationConfig(
        top_p=0.8,
        temperature=0.7,
        repetition_penalty=1.005,
    )  # top_k=40, min_new_tokens=200
    return gen_config


@st.cache_resource
def load_turbomind_model(model_dir, enable_rag=True, rag_config=None, db_path=None):  # hf awq

    model_format = "hf"
    if Path(model_dir).stem.endswith("-4bit"):
        model_format = "awq"

    model_dir = snapshot_download(model_dir, revision="master")
    backend_config = TurbomindEngineConfig(model_format=model_format, session_len=32768, cache_max_entry_count=0.6)
    pipe = pipeline(model_dir, backend_config=backend_config, log_level="INFO", model_name="internlm2")

    retriever = None
    if enable_rag:
        # 加载 rag 模型
        retriever = CacheRetriever(config_path=rag_config).get(config_path=rag_config, work_dir=db_path)

        # update reject throttle
        # retriever = cache.get(config_path=rag_config, work_dir=db_path)
        # with open(os.path.join('resource', 'good_questions.json')) as f:
        #     good_questions = json.load(f)
        # with open(os.path.join('resource', 'bad_questions.json')) as f:
        #     bad_questions = json.load(f)
        # retriever.update_throttle(config_path=args.config_path,
        #                           good_questions=good_questions,
        #                           bad_questions=bad_questions)

        # cache.pop('default')

    return pipe, None, retriever


def combine_history(prompt, meta_instruction, history_msg=None, first_input_str=""):
    total_prompt = [{"role": "system", "content": meta_instruction}]

    if first_input_str != "":
        total_prompt.append({"role": "user", "content": first_input_str})

    if history_msg is not None:
        for message in history_msg:
            total_prompt.append({"role": message["role"], "content": message["content"]})

    total_prompt.append({"role": "user", "content": prompt})
    return [total_prompt]


def get_turbomind_response(
    prompt,
    meta_instruction,
    user_avator,
    robot_avator,
    model_pipe,
    tokenizer,
    session_messages,
    add_session_msg=True,
    first_input_str="",
    rag_retriever=None,
    product_name="",
):

    if rag_retriever is not None:

        GENERATE_TEMPLATE = "这是说明书：“{}”\n 客户的问题：“{}” \n 请阅读说明并运用你的性格进行解答。"  # noqa E501
        context_max_length = 3000
        chunk, db_context, references = rag_retriever.query(
            f"商品名：{product_name}。{prompt}", context_max_length=context_max_length - 2 * len(GENERATE_TEMPLATE)
        )
        
        print(f"@@@@@@@@@@@@{chunk}")
        
        if db_context is None:
            print("feature store reject")

        print(f"get db contenxt = {db_context}")
        prompt_rag = prompt
        if db_context is not None and len(db_context) > 0:
            prompt_rag = GENERATE_TEMPLATE.format(db_context, prompt)
            
        print("=" * 20)
        print(f"RAG reference = {references}")

    real_prompt = combine_history(
        prompt_rag if rag_retriever else prompt,
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
                item.text = item.text.replace("~", "")

            cur_response += item.text
            message_placeholder.markdown(cur_response + "▌")
        message_placeholder.markdown(cur_response)

    # Add robot response to chat history
    session_messages.append(
        {
            "role": "assistant",
            "content": cur_response,  # pylint: disable=undefined-loop-variable
            "avatar": robot_avator,
        }
    )
    torch.cuda.empty_cache()
