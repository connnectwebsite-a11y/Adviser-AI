import numpy as np
import faiss

from sentence_transformers import SentenceTransformer


class KnowledgeEngine:
    def __init__(
        self,
        model_name="all-MiniLM-L6-v2"
    ):
        self.model = SentenceTransformer(
            model_name
        )

        self.index = None
        self.chunks = []


    def build(self, chunks):
        self.chunks = list(chunks)

        if not self.chunks:
            self.index = None
            return

        texts = [
            str(chunk.get("text", ""))
            if isinstance(chunk, dict)
            else str(chunk)
            for chunk in self.chunks
        ]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        self.index = faiss.IndexFlatIP(
            embeddings.shape[1]
        )

        self.index.add(embeddings)


    def search(
        self,
        question,
        top_k=4
    ):
        if (
            self.index is None
            or not self.chunks
        ):
            return []

        query = self.model.encode(
            [str(question)],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        query = np.asarray(
            query,
            dtype="float32"
        )

        k = min(
            top_k,
            len(self.chunks)
        )

        scores, indices = self.index.search(
            query,
            k
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0]
        ):
            if index < 0:
                continue

            chunk = self.chunks[index]

            if isinstance(chunk, dict):
                result = dict(chunk)
            else:
                result = {
                    "text": str(chunk)
                }

            result["score"] = float(score)

            results.append(result)

        return results
