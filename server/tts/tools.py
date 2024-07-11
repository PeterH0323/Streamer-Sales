
SYMBOL_SPLITS = {
    "。",
    "？",
    "！",
    "……",
    ".",
    "?",
    "!",
    "~",
    "…",
}


def make_text_chunk(original_text, strat_index, max_len=5, max_try=5000):
    cut_string = original_text
    end_index = strat_index

    while True:
        if original_text[end_index] in SYMBOL_SPLITS:
            end_index += 1
            cut_string = original_text[strat_index:end_index]
            break
        else:
            end_index += 1

        if end_index >= len(original_text):
            # 文本太短，没找到
            return 0, ""

        if end_index > max_try:
            # 有问题
            raise ValueError("Reach max try")
    return end_index, cut_string
