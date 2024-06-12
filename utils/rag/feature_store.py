"""extract feature and search with user query."""

import argparse
import json
import os
import re
import shutil
from multiprocessing import Pool
from pathlib import Path
from typing import Any, List, Optional

import yaml

# 解决 Warning：huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks…
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from BCEmbedding.tools.langchain import BCERerank
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import MarkdownHeaderTextSplitter, MarkdownTextSplitter, RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS as Vectorstore
from langchain_core.documents import Document
from loguru import logger
from torch.cuda import empty_cache

try:
    from utils.rag.file_operation import FileName, FileOperation
    from utils.rag.retriever import CacheRetriever, Retriever
except:
    # 用于 DEBUG
    from file_operation import FileName, FileOperation
    from retriever import CacheRetriever, Retriever


def read_and_save(file: FileName):
    if os.path.exists(file.copypath):
        # already exists, return
        logger.info("already exist, skip load")
        return
    file_opr = FileOperation()
    logger.info("reading {}, would save to {}".format(file.origin, file.copypath))
    content, error = file_opr.read(file.origin)
    if error is not None:
        logger.error("{} load error: {}".format(file.origin, str(error)))
        return

    if content is None or len(content) < 1:
        logger.warning("{} empty, skip save".format(file.origin))
        return

    with open(file.copypath, "w") as f:
        f.write(content)


def _split_text_with_regex_from_end(text: str, separator: str, keep_separator: bool) -> List[str]:
    # Now that we have the separator, split the text
    if separator:
        if keep_separator:
            # The parentheses in the pattern keep the delimiters in the result.
            _splits = re.split(f"({separator})", text)
            splits = ["".join(i) for i in zip(_splits[0::2], _splits[1::2])]
            if len(_splits) % 2 == 1:
                splits += _splits[-1:]
            # splits = [_splits[0]] + splits
        else:
            splits = re.split(separator, text)
    else:
        splits = list(text)
    return [s for s in splits if s != ""]


# copy from https://github.com/chatchat-space/Langchain-Chatchat/blob/master/text_splitter/chinese_recursive_text_splitter.py
class ChineseRecursiveTextSplitter(RecursiveCharacterTextSplitter):

    def __init__(
        self,
        separators: Optional[List[str]] = None,
        keep_separator: bool = True,
        is_separator_regex: bool = True,
        **kwargs: Any,
    ) -> None:
        """Create a new TextSplitter."""
        super().__init__(keep_separator=keep_separator, **kwargs)
        self._separators = separators or ["\n\n", "\n", "。|！|？", "\.\s|\!\s|\?\s", "；|;\s", "，|,\s"]
        self._is_separator_regex = is_separator_regex

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Split incoming text and return chunks."""
        final_chunks = []
        # Get appropriate separator to use
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            _separator = _s if self._is_separator_regex else re.escape(_s)
            if _s == "":
                separator = _s
                break
            if re.search(_separator, text):
                separator = _s
                new_separators = separators[i + 1 :]
                break

        _separator = separator if self._is_separator_regex else re.escape(separator)
        splits = _split_text_with_regex_from_end(text, _separator, self._keep_separator)

        # Now go merging things, recursively splitting longer texts.
        _good_splits = []
        _separator = "" if self._keep_separator else separator
        for s in splits:
            if self._length_function(s) < self._chunk_size:
                _good_splits.append(s)
            else:
                if _good_splits:
                    merged_text = self._merge_splits(_good_splits, _separator)
                    final_chunks.extend(merged_text)
                    _good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)
        if _good_splits:
            merged_text = self._merge_splits(_good_splits, _separator)
            final_chunks.extend(merged_text)
        return [re.sub(r"\n{2,}", "\n", chunk.strip()) for chunk in final_chunks if chunk.strip() != ""]


class FeatureStore:
    """Tokenize and extract features from the project's documents, for use in
    the reject pipeline and response pipeline."""

    def __init__(
        self, embeddings: HuggingFaceEmbeddings, reranker: BCERerank, config_path: str = "rag_config.yaml", language: str = "zh"
    ) -> None:
        """Init with model device type and config."""
        self.config_path = config_path
        self.reject_throttle = -1
        self.language = language
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)["feature_store"]
            self.reject_throttle = config["reject_throttle"]

        logger.warning(
            "!!! If your feature generated by `text2vec-large-chinese` before 20240208, please rerun `python3 -m huixiangdou.service.feature_store`"  # noqa E501
        )

        logger.debug("loading text2vec model..")
        self.embeddings = embeddings
        self.reranker = reranker
        self.compression_retriever = None
        self.rejecter = None
        self.retriever = None
        self.md_splitter = MarkdownTextSplitter(chunk_size=768, chunk_overlap=32)

        if language == "zh":
            self.text_splitter = ChineseRecursiveTextSplitter(
                keep_separator=True, is_separator_regex=True, chunk_size=768, chunk_overlap=32
            )
        else:
            self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=768, chunk_overlap=32)

        self.head_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
        )

    def split_md(self, text: str, source: None):
        """Split the markdown document in a nested way, first extracting the
        header.

        If the extraction result exceeds 1024, split it again according to
        length.
        """
        docs = self.head_splitter.split_text(text)

        final = []
        for doc in docs:
            header = ""
            if len(doc.metadata) > 0:
                if "Header 1" in doc.metadata:
                    header += doc.metadata["Header 1"]
                if "Header 2" in doc.metadata:
                    header += " "
                    header += doc.metadata["Header 2"]
                if "Header 3" in doc.metadata:
                    header += " "
                    header += doc.metadata["Header 3"]

            if len(doc.page_content) >= 1024:
                subdocs = self.md_splitter.create_documents([doc.page_content])
                for subdoc in subdocs:
                    if len(subdoc.page_content) >= 10:
                        final.append("{} {}".format(header, subdoc.page_content.lower()))
            elif len(doc.page_content) >= 10:
                final.append("{} {}".format(header, doc.page_content.lower()))  # noqa E501

        for item in final:
            if len(item) >= 1024:
                logger.debug("source {} split length {}".format(source, len(item)))
        return final

    def clean_md(self, text: str):
        """Remove parts of the markdown document that do not contain the key
        question words, such as code blocks, URL links, etc."""
        # remove ref
        pattern_ref = r"\[(.*?)\]\(.*?\)"
        new_text = re.sub(pattern_ref, r"\1", text)

        # remove code block
        pattern_code = r"```.*?```"
        new_text = re.sub(pattern_code, "", new_text, flags=re.DOTALL)

        # remove underline
        new_text = re.sub("_{5,}", "", new_text)

        # remove table
        # new_text = re.sub('\|.*?\|\n\| *\:.*\: *\|.*\n(\|.*\|.*\n)*', '', new_text, flags=re.DOTALL)   # noqa E501

        # use lower
        new_text = new_text.lower()
        return new_text

    def get_md_documents(self, file: FileName):
        documents = []
        length = 0
        text = ""
        with open(file.copypath, encoding="utf8") as f:
            text = f.read()
        text = file.prefix + "\n" + self.clean_md(text)
        if len(text) <= 1:
            return [], length

        chunks = self.split_md(text=text, source=os.path.abspath(file.copypath))
        for chunk in chunks:
            new_doc = Document(page_content=chunk, metadata={"source": file.basename, "read": file.copypath})
            length += len(chunk)
            documents.append(new_doc)
        return documents, length

    def get_text_documents(self, text: str, file: FileName):
        if len(text) <= 1:
            return []
        chunks = self.text_splitter.create_documents([text])
        documents = []
        for chunk in chunks:
            # `source` is for return references
            # `read` is for LLM response
            chunk.metadata = {"source": file.basename, "read": file.copypath}
            documents.append(chunk)
        return documents

    def ingress_response(self, files: list, work_dir: str):
        """Extract the features required for the response pipeline based on the
        document."""
        feature_dir = os.path.join(work_dir, "db_response")
        if not os.path.exists(feature_dir):
            os.makedirs(feature_dir)

        # logger.info('glob {} in dir {}'.format(files, file_dir))
        file_opr = FileOperation()
        documents = []

        for i, file in enumerate(files):
            logger.debug("{}/{}.. {}".format(i + 1, len(files), file.basename))
            if not file.state:
                continue

            if file._type == "md":
                md_documents, md_length = self.get_md_documents(file)
                documents += md_documents
                logger.info("{} content length {}".format(file._type, md_length))
                file.reason = str(md_length)

            else:
                # now read pdf/word/excel/ppt text
                text, error = file_opr.read(file.copypath)
                if error is not None:
                    file.state = False
                    file.reason = str(error)
                    continue
                file.reason = str(len(text))
                logger.info("{} content length {}".format(file._type, len(text)))
                text = file.prefix + text
                documents += self.get_text_documents(text, file)

        if len(documents) < 1:
            return
        vs = Vectorstore.from_documents(documents, self.embeddings)
        vs.save_local(feature_dir)

    def ingress_reject(self, files: list, work_dir: str):
        """Extract the features required for the reject pipeline based on
        documents."""
        feature_dir = os.path.join(work_dir, "db_reject")
        if not os.path.exists(feature_dir):
            os.makedirs(feature_dir)

        documents = []
        file_opr = FileOperation()

        logger.debug("ingress reject..")
        for i, file in enumerate(files):
            if not file.state:
                continue

            if file._type == "md":
                # reject base not clean md
                text = file.basename + "\n"
                with open(file.copypath, encoding="utf8") as f:
                    text += f.read()
                if len(text) <= 1:
                    continue

                chunks = self.split_md(text=text, source=os.path.abspath(file.copypath))
                for chunk in chunks:
                    new_doc = Document(page_content=chunk, metadata={"source": file.basename, "read": file.copypath})
                    documents.append(new_doc)

            else:
                text, error = file_opr.read(file.copypath)
                if error is not None:
                    continue
                text = file.basename + text
                documents += self.get_text_documents(text, file)

        if len(documents) < 1:
            return
        vs = Vectorstore.from_documents(documents, self.embeddings)
        vs.save_local(feature_dir)

    def preprocess(self, files: list, work_dir: str):
        """Preprocesses files in a given directory. Copies each file to
        'preprocess' with new name formed by joining all subdirectories with
        '_'.

        Args:
            files (list): original file list.
            work_dir (str): Working directory where preprocessed files will be stored.  # noqa E501

        Returns:
            str: Path to the directory where preprocessed markdown files are saved.

        Raises:
            Exception: Raise an exception if no markdown files are found in the provided repository directory.  # noqa E501
        """
        preproc_dir = os.path.join(work_dir, "preprocess")
        if not os.path.exists(preproc_dir):
            os.makedirs(preproc_dir)

        pool = Pool(processes=16)
        file_opr = FileOperation()
        for idx, file in enumerate(files):
            if not os.path.exists(file.origin):
                file.state = False
                file.reason = "skip not exist"
                continue

            if file._type == "image":
                file.state = False
                file.reason = "skip image"

            elif file._type in ["pdf", "word", "excel", "ppt", "html"]:
                # read pdf/word/excel file and save to text format
                md5 = file_opr.md5(file.origin)
                file.copypath = os.path.join(preproc_dir, "{}.text".format(md5))
                pool.apply_async(read_and_save, (file,))

            elif file._type in ["md", "text"]:
                # rename text files to new dir
                md5 = file_opr.md5(file.origin)
                file.copypath = os.path.join(preproc_dir, file.origin.replace("/", "_")[-84:])
                try:
                    shutil.copy(file.origin, file.copypath)
                    file.state = True
                    file.reason = "preprocessed"
                except Exception as e:
                    file.state = False
                    file.reason = str(e)

            else:
                file.state = False
                file.reason = "skip unknown format"
        pool.close()
        logger.debug("waiting for preprocess read finish..")
        pool.join()

        # check process result
        for file in files:
            if file._type in ["pdf", "word", "excel"]:
                if os.path.exists(file.copypath):
                    file.state = True
                    file.reason = "preprocessed"
                else:
                    file.state = False
                    file.reason = "read error"

    def initialize(self, files: list, work_dir: str):
        """Initializes response and reject feature store.

        Only needs to be called once. Also calculates the optimal threshold
        based on provided good and bad question examples, and saves it in the
        configuration file.
        """
        logger.info("initialize response and reject feature store, you only need call this once.")  # noqa E501
        self.preprocess(files=files, work_dir=work_dir)
        self.ingress_response(files=files, work_dir=work_dir)
        self.ingress_reject(files=files, work_dir=work_dir)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Feature store for processing directories.")
    parser.add_argument("--work_dir", type=str, default="work_dir", help="Working directory.")
    parser.add_argument("--repo_dir", type=str, default="repodir", help="Root directory where the repositories are located.")
    parser.add_argument(
        "--config_path", default="rag_config.yaml", help="Feature store configuration path. Default value is rag_config.yaml"
    )
    # parser.add_argument(
    #     "--good_questions",
    #     default="resource/good_questions.json",
    #     help="Positive examples in the dataset. Default value is resource/good_questions.json",  # noqa E251  # noqa E501
    # )
    # parser.add_argument(
    #     "--bad_questions",
    #     default="resource/bad_questions.json",
    #     help="Negative examples json path. Default value is resource/bad_questions.json",  # noqa E251  # noqa E501
    # )
    # parser.add_argument("--sample", help="Input an json file, save reject and search output.")
    args = parser.parse_args()
    return args


# def test_reject(retriever: Retriever, sample: str = None):
#     """Simple test reject pipeline."""
#     if sample is None:
#         real_questions = [
#             "SAM 10个T 的训练集，怎么比比较公平呢~？速度上还有缺陷吧？",
#             "想问下，如果只是推理的话，amp的fp16是不会省显存么，我看parameter仍然是float32，开和不开推理的显存占用都是一样的。能不能直接用把数据和model都 .half() 代替呢，相比之下amp好在哪里",  # noqa E501
#             "mmdeploy支持ncnn vulkan部署么，我只找到了ncnn cpu 版本",
#             "大佬们，如果我想在高空检测安全帽，我应该用 mmdetection 还是 mmrotate",
#             "请问 ncnn 全称是什么",
#             "有啥中文的 text to speech 模型吗?",
#             "今天中午吃什么？",
#             "huixiangdou 是什么？",
#             "mmpose 如何安装？",
#             "使用科研仪器需要注意什么？",
#         ]
#     else:
#         with open(sample) as f:
#             real_questions = json.load(f)

#     for example in real_questions:
#         reject, _ = retriever.is_reject(example)

#         if reject:
#             logger.error(f"reject query: {example}")
#         else:
#             logger.warning(f"process query: {example}")

#         if sample is not None:
#             if reject:
#                 with open("workdir/negative.txt", "a+") as f:
#                     f.write(example)
#                     f.write("\n")
#             else:
#                 with open("workdir/positive.txt", "a+") as f:
#                     f.write(example)
#                     f.write("\n")

#     empty_cache()


def test_query(retriever: Retriever, sample: str = None):
    """Simple test response pipeline."""
    if sample is not None:
        with open(sample) as f:
            real_questions = json.load(f)
        logger.add("logs/feature_store_query.log", rotation="4MB")
    else:
        real_questions = ["mmpose installation", "how to use std::vector ?"]

    for example in real_questions:
        example = example[0:400]
        print(retriever.query(example))
        empty_cache()

    empty_cache()


def fix_system_error():
    """
    Fix `No module named 'faiss.swigfaiss_avx2`
    """
    import os
    from pathlib import Path

    import faiss

    if Path(faiss.__file__).parent.joinpath("swigfaiss_avx2.py").exists():
        return

    print("Fixing faiss error...")
    os.system(f"cd {Path(faiss.__file__).parent} && ln -s swigfaiss.py swigfaiss_avx2.py")


def gen_vector_db(config_path, source_dir, work_dir, test_mode=False, update_reject=False):

    # 解决 faiss 导入问题
    fix_system_error()

    # 必须是绝对路径，否则加载会有问题
    work_dir = str(Path(work_dir).absolute())

    cache = CacheRetriever(config_path=config_path)

    # 生成向量数据库
    fs_init = FeatureStore(embeddings=cache.embeddings, reranker=cache.reranker, config_path=config_path)

    # walk all files in repo dir
    file_opr = FileOperation()
    files = file_opr.scan_dir(repo_dir=source_dir)
    fs_init.initialize(files=files, work_dir=work_dir)
    file_opr.summarize(files)
    del fs_init

    # update reject throttle
    if update_reject:
        # 目前没有用到这块，可忽略
        retriever = cache.get(config_path=config_path, work_dir=work_dir)
        with open(os.path.join("resource", "good_questions.json")) as f:
            good_questions = json.load(f)
        with open(os.path.join("resource", "bad_questions.json")) as f:
            bad_questions = json.load(f)
        retriever.update_throttle(config_path=config_path, good_questions=good_questions, bad_questions=bad_questions)

        cache.pop("default")

    if test_mode:
        # test
        retriever = cache.get(config_path=config_path, work_dir=work_dir)
        # test_reject(retriever, args.sample)
        test_query(retriever, args.sample)


if __name__ == "__main__":
    args = parse_args()
    gen_vector_db(args.config_path, args.repo_dir, args.work_dir, test_mode=True)
