"""
KT 약관 RAG 에이전트 v2 — 속도·정확도·비용 최적화

개선 사항:
  - Hybrid Search  : BM25(키워드) + FAISS(의미) → RRF 결합
  - Re-ranking     : Flashrank 로컬 모델 (무료, 추가 API 없음)
  - 멀티턴         : 대화 히스토리 수동 관리 → 질문 재구성 → 검색 → 답변

지식베이스 : data/pdf/*.pdf  (KT 이용약관 3종)
임베딩     : text-embedding-3-small
LLM        : gpt-4o-mini
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

load_dotenv()

# ── 설정 ──────────────────────────────────────────────────────────────────────
PDF_DIR           = Path("data/pdf")
VECTOR_STORE_PATH = Path("data/faiss_index")
MODEL_NAME        = os.getenv("MODEL_NAME",     "gpt-4o-mini")
EMB_MODEL_NAME    = os.getenv("EMB_MODEL_NAME", "text-embedding-3-small")
CHUNK_SIZE        = 1000
CHUNK_OVERLAP     = 200
BM25_K            = 15   # BM25 후보 수
VECTOR_FETCH_K    = 30   # MMR 초기 후보 수
VECTOR_K          = 15   # MMR 최종 반환 수
RERANK_TOP_N      = 5    # Re-ranking 후 최종 전달 수


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
        print("  FAISS 인덱스 로드 중...")
        return FAISS.load_local(
            str(VECTOR_STORE_PATH),
            embeddings,
            allow_dangerous_deserialization=True,
        )

    print("  새 FAISS 인덱스 생성 중...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTOR_STORE_PATH))
    print("  인덱스 저장 완료")
    return vectorstore


# ── 4. Hybrid Retriever (BM25 + FAISS + RRF) ─────────────────────────────────
def reciprocal_rank_fusion(
    bm25_docs: list[Document],
    vector_docs: list[Document],
    k: int = 60,
) -> list[Document]:
    """BM25와 벡터 검색 결과를 RRF로 통합, 중복 제거"""
    scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    for rank, doc in enumerate(bm25_docs):
        key = doc.page_content
        scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
        doc_map[key] = doc

    for rank, doc in enumerate(vector_docs):
        key = doc.page_content
        scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
        doc_map[key] = doc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_map[key] for key, _ in ranked]


class HybridRetriever:
    """BM25 + FAISS 하이브리드 검색 후 Flashrank 재순위"""

    def __init__(self, chunks: list[Document], vectorstore: FAISS):
        self.bm25     = BM25Retriever.from_documents(chunks, k=BM25_K)
        self.vector   = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": VECTOR_K, "fetch_k": VECTOR_FETCH_K},
        )
        self.reranker = FlashrankRerank(top_n=RERANK_TOP_N)

    def retrieve(self, query: str) -> list[Document]:
        bm25_docs   = self.bm25.invoke(query)
        vector_docs = self.vector.invoke(query)
        merged      = reciprocal_rank_fusion(bm25_docs, vector_docs)
        reranked    = self.reranker.compress_documents(merged, query)
        return reranked


# ── 5. 멀티턴 RAG 체인 ────────────────────────────────────────────────────────
def build_rag_chain(retriever: HybridRetriever):
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0)

    # 5-1. 히스토리 기반 질문 재구성
    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "대화 히스토리와 최신 질문이 주어집니다. "
         "최신 질문이 이전 대화를 참조하면, 히스토리 없이도 이해할 수 있는 "
         "독립적인 질문으로 재구성하세요. 답변하지 말고 질문만 반환하세요."),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ])
    contextualize_chain = contextualize_prompt | llm | StrOutputParser()

    # 5-2. 답변 생성
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "당신은 KT 이용약관 전문 상담원입니다. "
         "아래 약관 내용만을 근거로 답변하세요. "
         "약관에 없는 내용은 '해당 내용은 약관에서 확인되지 않습니다'라고 하세요.\n\n"
         "[약관 내용]\n{context}"),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ])
    qa_chain = qa_prompt | llm | StrOutputParser()

    def ask(question: str, chat_history: list) -> dict:
        # 히스토리가 있으면 독립적 질문으로 재구성
        standalone = (
            contextualize_chain.invoke({"question": question, "chat_history": chat_history})
            if chat_history else question
        )

        # Hybrid Search + Re-ranking
        docs    = retriever.retrieve(standalone)
        context = "\n\n".join(d.page_content for d in docs)

        # 답변 생성
        answer = qa_chain.invoke({
            "context":      context,
            "question":     question,
            "chat_history": chat_history,
        })

        return {"answer": answer, "source_documents": docs}

    return ask


# ── 6. 출처 출력 ──────────────────────────────────────────────────────────────
def print_sources(source_docs):
    sources = {doc.metadata.get("source", "unknown") for doc in source_docs}
    pages   = sorted({doc.metadata.get("page", 0) + 1 for doc in source_docs})
    print(f"\n  📄 참조: {', '.join(sorted(sources))}  |  페이지: {pages}")


# ── 메인 ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  KT 약관 RAG 에이전트 v2 (Hybrid + Re-ranking)")
    print("=" * 60)

    # 문서 준비
    print("\n[1/3] 문서 로드 및 청크 분할")
    docs   = load_documents()
    chunks = split_documents(docs)

    print("\n[2/3] FAISS 인덱스 로드")
    vectorstore = build_or_load_vectorstore(chunks)

    print("\n[3/3] Hybrid Retriever 초기화 (BM25 + FAISS + Flashrank)")
    retriever = HybridRetriever(chunks, vectorstore)

    print("\n[✓] 준비 완료\n")

    ask          = build_rag_chain(retriever)
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
        print(f"\n답변: {result['answer']}")
        print_sources(result["source_documents"])

        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=result["answer"]))


if __name__ == "__main__":
    main()
