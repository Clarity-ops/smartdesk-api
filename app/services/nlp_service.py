import math
from typing import List
from sentence_transformers import SentenceTransformer

class NLPService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Модель завантажується в пам'ять один раз при старті застосунку
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Перетворює текст на 384-вимірний семантичний вектор за допомогою Transformer-моделі.
        Вектор одразу нормалізується за L2-нормою.
        """
        if not text or not text.strip():
            return [0.0] * 384

        embedding = self.model.encode(text, normalize_embeddings=True)
        # Конвертуємо numpy array у звичайний python list для JSON-серіалізації в SQLite
        return embedding.tolist()

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Обчислення косинусної подібності.
        Оскільки модель повертає нормалізовані вектори (L2 norm = 1.0),
        косинусна схожість дорівнює простому скалярному добутку (Dot Product).
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        return round(float(dot_product), 4)
      