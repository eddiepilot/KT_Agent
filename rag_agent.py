"""
KT 약관 RAG 에이전트 (멀티턴)

지식베이스 : data/pdf/*.pdf  (KT 이용약관 3종)
임베딩     : text-embedding-3-small
LLM        : gpt-4o-mini
벡터 DB    : FAISS
멀티턴     : 대화 히스토리 기반 질문 재구성 → 검색 → 답변
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# ── 설정 ──────────────────────────────────────────────────────────────────────
PDF_DIR           = Path("data/pdf")
VECTOR_STORE_PATH = Path("data/faiss_index")
MODEL_NAME        = os.getenv("MODEL_NAME",     "gpt-4o-mini")
EMB_MODEL_NAME    = os.getenv("EMB_MODEL_NAME", "text-embedding-3-small")
CHUNK_SIZE        = 1000
CHUNK_OVERLAP     = 200


# ── 1. 문서 로드 ──────────────────────────────────────────────────────────────
def load_documents():
    docs = []
    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        loaded = PyMuPDFLoader(str(pdf_path)).load()
        for doc in loaded:
            doc.metadata["source"] = pdf_path.name
        docs.extend(loaded)
        print(f"  로드: {pdf_path.name}  ({len(loaded)}페이지)")
    return docs


# ── 2. 청크 분할 ──────────────────────────────────────────────────────────────
def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(docs)
    print(f"  청크 수: {len(chunks)}")
    return chunks


# ── 3. FAISS 인덱스 구축 / 로드 ───────────────────────────────────────────────
def build_or_load_vectorstore(chunks=None):
    embeddings = OpenAIEmbeddings(model=EMB_MODEL_NAME)

    if VECTOR_STORE_PATH.exists():
        print("  기존 인덱스 로드 중...")
        return FAISS.load_local(
            str(VECTOR_STORE_PATH),
            embeddings,
            allow_dangerous_deserialization=True,
        )

    print("  새 인덱스 생성 중...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTOR_STORE_PATH))
    print("  인덱스 저장 완료")
    return vectorstore


# ── 4. 멀티턴 RAG 체인 ────────────────────────────────────────────────────────
def build_rag_chain(vectorstore):
    llm       = ChatOpenAI(model=MODEL_NAME, temperature=0)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # 4-1. 이전 대화를 반영해 독립적인 검색 질문으로 재구성
    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "대화 히스토리와 최신 질문이 주어집니다. "
         "최신 질문이 이전 대화를 참조하면, 히스토리 없이도 이해할 수 있는 "
         "독립적인 질문으로 재구성하세요. 답변하지 말고 질문만 반환하세요."),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ])
    contextualize_chain = contextualize_prompt | llm | StrOutputParser()

    # 4-2. 재구성된 질문으로 검색 후 답변
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "당신은 KT 이용약관 전문 상담원입니다. "
         "아래 약관 내용만을 근거로 답변하세요. "
         "약관에 없는 내용은 '해당 내용은 약관에서 확인되지 않습니다'라고 하세요.\n\n"
         "[약관 내용]\n{context}"),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ])

    def retrieve_with_history(inputs: dict) -> dict:
        """히스토리가 있으면 질문 재구성 후 검색, 없으면 바로 검색"""
        question = inputs["question"]
        history  = inputs.get("chat_history", [])

        standalone = (
            contextualize_chain.invoke({"question": question, "chat_history": history})
            if history else question
        )

        docs = retriever.invoke(standalone)
        return {
            "context":          "\n\n".join(d.page_content for d in docs),
            "question":         question,
            "chat_history":     history,
            "source_documents": docs,
        }

    # 4-3. 전체 파이프라인
    chain = (
        RunnableLambda(retrieve_with_history)
        | {
            "answer":           qa_prompt | llm | StrOutputParser(),
            "source_documents": RunnableLambda(lambda x: x["source_documents"]),
          }
    )

    # 4-4. 히스토리 자동 관리 (세션별 인메모리)
    store: dict[str, ChatMessageHistory] = {}

    def get_session_history(session_id: str) -> ChatMessageHistory:
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store[session_id]

    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
        output_messages_key="answer",
    ), store


# ── 5. 출처 출력 ──────────────────────────────────────────────────────────────
def print_sources(source_docs):
    sources = {doc.metadata.get("source", "unknown") for doc in source_docs}
    pages   = sorted({doc.metadata.get("page", 0) + 1 for doc in source_docs})
    print(f"\n  📄 참조: {', '.join(sorted(sources))}  |  페이지: {pages}")


# ── 메인 ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  KT 약관 RAG 에이전트 (멀티턴)")
    print("=" * 60)

    # 인덱스 준비
    if VECTOR_STORE_PATH.exists():
        print("\n[1/2] 기존 인덱스 로드")
        vectorstore = build_or_load_vectorstore()
    else:
        print("\n[1/3] 문서 로드")
        docs = load_documents()
        print("\n[2/3] 청크 분할 및 인덱싱")
        chunks = split_documents(docs)
        vectorstore = build_or_load_vectorstore(chunks)

    print("\n[✓] 멀티턴 RAG 체인 준비 완료\n")

    chain, store = build_rag_chain(vectorstore)
    SESSION_ID   = "kt-session"
    config       = {"configurable": {"session_id": SESSION_ID}}

    print("이전 대화 맥락이 유지됩니다.")
    print("명령어: 'reset' = 대화 초기화 | 'q' = 종료")
    print("=" * 60)

    while True:
        print()
        question = input("질문: ").strip()
        if not question:
            continue
        if question.lower() in ("q", "quit", "exit", "종료"):
            print("종료합니다.")
            break
        if question.lower() in ("reset", "초기화"):
            store.clear()
            print("  대화 히스토리가 초기화되었습니다.")
            continue

        result = chain.invoke({"question": question}, config=config)
        print(f"\n답변: {result['answer']}")
        print_sources(result["source_documents"])


if __name__ == "__main__":
    main()
