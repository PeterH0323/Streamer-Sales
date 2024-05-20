"""RAG 处理函数"""

# 基础配置
CONTEXT_MAX_LENGTH = 3000  # 上下文最大长度
GENERATE_TEMPLATE = "这是说明书：“{}”\n 客户的问题：“{}” \n 请阅读说明并运用你的性格进行解答。"  # RAG prompt 模板


def build_rag_prompt(rag_retriever, product_name, prompt):
    chunk, db_context, references = rag_retriever.query(
        f"商品名：{product_name}。{prompt}", context_max_length=CONTEXT_MAX_LENGTH - 2 * len(GENERATE_TEMPLATE)
    )

    if db_context is not None and len(db_context) > 0:
        prompt_rag = GENERATE_TEMPLATE.format(db_context, prompt)
    else:
        print("db_context is None")
        prompt_rag = prompt

    print("=" * 20)
    print(f"RAG reference = {references}")

    return prompt_rag
