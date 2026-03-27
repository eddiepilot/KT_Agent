"""
KT 약관 RAG 에이전트 (멀티턴)

개선 사항:
  - 청크 크기 500자  : 정밀한 검색, 불필요한 컨텍스트 제거
  - 스트리밍 답변     : 토큰 단위 실시간 출력으로 체감 속도 향상
  - 프롬프트 캐싱     : 시스템 프롬프트 캐시 → 반복 질문 비용 절감

지식베이스 : data/pdf/*.pdf  (KT 이용약관 3종)
임베딩     : text-embedding-3-small
LLM        : gpt-4o-mini
벡터 DB    : FAISS MMR
"""

import json
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# ── 설정 ──────────────────────────────────────────────────────────────────────
PDF_DIR           = Path("data/pdf")
VECTOR_STORE_PATH = Path("data/faiss_index")
META_FILE         = VECTOR_STORE_PATH / "meta.json"
MODEL_NAME        = os.getenv("MODEL_NAME",     "gpt-4o-mini")
EMB_MODEL_NAME    = os.getenv("EMB_MODEL_NAME", "text-embedding-3-small")
CHUNK_SIZE        = 500   # 1000 → 500: 정밀한 검색
CHUNK_OVERLAP     = 100


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
    print(f"  청크 수: {len(chunks)}  (크기: {CHUNK_SIZE}자)")
    return chunks


# ── 3. FAISS 인덱스 구축 / 로드 (청크 크기 변경 시 자동 재구축) ────────────────
def build_or_load_vectorstore(chunks):
    embeddings = OpenAIEmbeddings(model=EMB_MODEL_NAME)

    # 저장된 청크 크기와 현재 설정 비교
    if VECTOR_STORE_PATH.exists() and META_FILE.exists():
        saved = json.loads(META_FILE.read_text())
        if saved.get("chunk_size") == CHUNK_SIZE:
            print("  FAISS 인덱스 로드 중...")
            return FAISS.load_local(
                str(VECTOR_STORE_PATH),
                embeddings,
                allow_dangerous_deserialization=True,
            )
        else:
            print(f"  청크 크기 변경 감지 ({saved['chunk_size']} → {CHUNK_SIZE}), 재구축 중...")
            shutil.rmtree(VECTOR_STORE_PATH)

    print("  새 FAISS 인덱스 생성 중...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTOR_STORE_PATH))
    META_FILE.write_text(json.dumps({"chunk_size": CHUNK_SIZE}))
    print("  인덱스 저장 완료")
    return vectorstore


# ── 4. 멀티턴 RAG 체인 (스트리밍 + 프롬프트 캐싱) ────────────────────────────
def build_rag_chain(vectorstore):
    # 프롬프트 캐싱: gpt-4o-mini는 1024 토큰 이상 프롬프트 자동 캐시
    # → 동일한 시스템 프롬프트 반복 사용 시 ~50% 비용 절감
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0)

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 6, "fetch_k": 20},
    )

    # 히스토리 기반 질문 재구성
    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "대화 히스토리와 최신 질문이 주어집니다. "
         "최신 질문이 이전 대화를 참조하면, 히스토리 없이도 이해할 수 있는 "
         "독립적인 질문으로 재구성하세요. 답변하지 말고 질문만 반환하세요."),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ])
    contextualize_chain = contextualize_prompt | llm | StrOutputParser()

    # 답변 생성 프롬프트 (고정 부분 → 캐시 히트 극대화)
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "당신은 KT 이용약관 전문 상담원입니다. "
         "아래 약관 내용만을 근거로 답변하세요. "
         "약관에 없는 내용은 '해당 내용은 약관에서 확인되지 않습니다'라고 하세요.\n\n"
         "[약관 내용]\n{context}"),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ])

    def ask(question: str, chat_history: list) -> dict:
        """질문 재구성 → 검색 → 스트리밍 답변"""
        # 히스토리가 있으면 독립적인 질문으로 재구성
        standalone = (
            contextualize_chain.invoke({"question": question, "chat_history": chat_history})
            if chat_history else question
        )

        # MMR 검색
        docs    = retriever.invoke(standalone)
        context = "\n\n".join(d.page_content for d in docs)

        # 스트리밍 답변 출력
        print("\n답변: ", end="", flush=True)
        answer_parts = []
        for chunk in (qa_prompt | llm).stream({
            "context":      context,
            "question":     question,
            "chat_history": chat_history,
        }):
            token = chunk.content
            print(token, end="", flush=True)
            answer_parts.append(token)
        print()  # 줄바꿈

        return {"answer": "".join(answer_parts), "source_documents": docs}

    return ask


# ── 5. 출처 출력 ──────────────────────────────────────────────────────────────
def print_sources(source_docs):
    sources = {doc.metadata.get("source", "unknown") for doc in source_docs}
    pages   = sorted({doc.metadata.get("page", 0) + 1 for doc in source_docs})
    print(f"  📄 참조: {', '.join(sorted(sources))}  |  페이지: {pages}")


# ── 메인 ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  KT 약관 RAG 에이전트 (스트리밍 · 캐싱 · 정밀검색)")
    print("=" * 60)

    print("\n[1/3] 문서 로드")
    docs = load_documents()

    print("\n[2/3] 청크 분할")
    chunks = split_documents(docs)

    print("\n[3/3] 인덱스 준비")
    vectorstore = build_or_load_vectorstore(chunks)

    print("\n[✓] 준비 완료\n")

    ask          = build_rag_chain(vectorstore)
    chat_history = []

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
            chat_history.clear()
            print("  대화 히스토리가 초기화되었습니다.")
            continue

        result = ask(question, chat_history)
        print_sources(result["source_documents"])

        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=result["answer"]))


if __name__ == "__main__":
    main()
