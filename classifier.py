from dataclasses import dataclass
from typing import List
from pymongo.collection import Collection
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

@dataclass
class ActivityRecord:
    details: str

class ActivityClassifier:
    def __init__(self, collection: Collection, n_clusters: int = 5):
        self.collection = collection
        self.n_clusters = n_clusters
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.model = None

    def load_data(self) -> List[str]:
        texts = []
        for doc in self.collection.find({"details": {"$ne": None}}):
            details = doc.get("details")
            if details:
                texts.append(details)
        return texts

    def train(self):
        texts = self.load_data()
        if not texts:
            return
        X = self.vectorizer.fit_transform(texts)
        self.model = KMeans(n_clusters=self.n_clusters, random_state=0)
        self.model.fit(X)

    def classify(self, text: str) -> int:
        if not self.model:
            return -1
        X = self.vectorizer.transform([text])
        return int(self.model.predict(X)[0])

