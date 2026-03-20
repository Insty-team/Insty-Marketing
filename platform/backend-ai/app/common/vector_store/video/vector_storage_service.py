from typing import List, Callable, Optional
from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode

from pinecone import Pinecone
from openai import OpenAI
import tiktoken
from concurrent.futures import ThreadPoolExecutor, as_completed

settings = get_settings()

# Initialize OpenAI and Pinecone clients
openai_client = OpenAI(api_key=settings.openai.api_key)
pc = Pinecone(api_key=settings.pinecone.api_key)
index = pc.Index(settings.pinecone.index_name)


class VectorStorageService:
    def __init__(self):
        self.index = index
        self.encoding = tiktoken.encoding_for_model("text-embedding-3-large")

    def _chunk_text(self, text: str, max_tokens: int = 1000) -> List[str]:
        words = text.split()
        chunks = []
        current_chunk = []

        for word in words:
            current_chunk.append(word)
            try:
                if len(self.encoding.encode(" ".join(current_chunk))) > max_tokens:
                    current_chunk.pop()
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [word]
            except Exception as e:
                raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _embed_texts(
        self,
        texts: List[str],
        batch_size: int = 100,
        max_workers: int = 4,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[List[float]]:
        def embed_batch(batch: List[str]) -> List[List[float]]:
            response = openai_client.embeddings.create(
                input=batch,
                model="text-embedding-3-large"
            )
            return [r.embedding for r in response.data]

        try:
            chunks = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
            total_chunks = len(chunks)
            embeddings = []

            if progress_callback:
                progress_callback("임베딩 시작", 20)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(embed_batch, batch): idx for idx, batch in enumerate(chunks)}
                completed = 0

                for future in as_completed(futures):
                    result = future.result()
                    embeddings.extend(result)
                    completed += 1
                    if progress_callback:
                        progress_callback("임베딩 진행 중", 20 + int(30 * completed / total_chunks))

            return embeddings

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def upsert_text(
        self,
        video_id: int,
        text: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[str]:
        if not text:
            raise APIException(ErrorCode.BAD_REQUEST_BODY, details=["Empty text"])

        try:
            if progress_callback:
                progress_callback("텍스트 분할 중", 0)

            chunks = self._chunk_text(text)
            total = len(chunks)

            if progress_callback:
                progress_callback("텍스트 분할 완료", 10)

            embeddings = self._embed_texts(chunks, progress_callback=progress_callback)

            items = []
            ids = []

            for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
                doc_id = f"{video_id}-{i}"
                ids.append(doc_id)

                items.append({
                    "id": doc_id,
                    "values": vector,
                    "metadata": {
                        "video_id": str(video_id),
                        "chunk_index": i,
                        "text": chunk
                    }
                })

                if progress_callback:
                    percent = 50 + int((i + 1) / total * 40)  # 50~90%
                    progress_callback(f"벡터 저장 중 ({i + 1}/{total})", percent)

            self.index.upsert(vectors=items)

            if progress_callback:
                progress_callback("벡터 업서트 완료", 100)

            return ids

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])