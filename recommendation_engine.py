"""Algoritmos usados para calcular as recomendacoes."""

import math
import statistics


TOP_N = 10


def similarity(left, right):
    union = left["genres"] | right["genres"]
    if not union:
        return 0.0
    return len(left["genres"] & right["genres"]) / len(union)


def popularity_value(anime):
    return math.log1p(anime["members"]) * max(anime["score"], 0.0)


def format_score(value):
    return f"{value:.2f}"


class RecommendationEngine:
    def __init__(self, animes, anime_by_id):
        self.animes = animes
        self.anime_by_id = anime_by_id

    def generate(self, ratings):
        rated_ids = set(ratings)
        return {
            "Colaborativa por item": self.recommend_by_item(ratings, rated_ids),
            "Colaborativa por usuario": self.recommend_by_cluster(ratings, rated_ids),
            "Popularidade": self.recommend_by_popularity(rated_ids),
            "Conteudo": self.recommend_by_content(ratings, rated_ids),
        }

    def recommend_by_item(self, ratings, rated_ids):
        rows = []
        rated_animes = [self.anime_by_id[anime_id] for anime_id in rated_ids]
        for anime in self.animes:
            if anime["id"] in rated_ids:
                continue
            total = 0.0
            weight_sum = 0.0
            for rated in rated_animes:
                weight = similarity(anime, rated)
                total += weight * ratings[rated["id"]]
                weight_sum += weight
            predicted = total / weight_sum if weight_sum else 0.0
            rows.append((anime, predicted))
        return sorted(rows, key=lambda item: (item[1], popularity_value(item[0])), reverse=True)[:TOP_N]

    def recommend_by_cluster(self, ratings, rated_ids):
        cluster_scores = {}
        for anime_id, rating in ratings.items():
            cluster = self.anime_by_id[anime_id]["cluster"]
            cluster_scores.setdefault(cluster, []).append(rating)

        cluster_profile = {
            cluster: (statistics.mean(values), len(values))
            for cluster, values in cluster_scores.items()
        }

        rows = []
        for anime in self.animes:
            if anime["id"] in rated_ids:
                continue
            mean_rating, amount = cluster_profile.get(anime["cluster"], (0.0, 0))
            value = mean_rating + min(amount, 5) * 0.15 + popularity_value(anime) / 100.0
            rows.append((anime, value))
        return sorted(rows, key=lambda item: item[1], reverse=True)[:TOP_N]

    def recommend_by_popularity(self, rated_ids):
        rows = [
            (anime, popularity_value(anime))
            for anime in self.animes
            if anime["id"] not in rated_ids
        ]
        return sorted(rows, key=lambda item: item[1], reverse=True)[:TOP_N]

    def recommend_by_content(self, ratings, rated_ids):
        genre_weights = {}
        cluster_weights = {}
        for anime_id, rating in ratings.items():
            anime = self.anime_by_id[anime_id]
            for genre in anime["genres"]:
                genre_weights[genre] = genre_weights.get(genre, 0.0) + rating
            cluster_weights[anime["cluster"]] = cluster_weights.get(anime["cluster"], 0.0) + rating

        rows = []
        for anime in self.animes:
            if anime["id"] in rated_ids:
                continue
            genre_value = sum(genre_weights.get(genre, 0.0) for genre in anime["genres"])
            cluster_value = cluster_weights.get(anime["cluster"], 0.0) * 0.35
            value = genre_value + cluster_value + popularity_value(anime) / 120.0
            rows.append((anime, value))
        return sorted(rows, key=lambda item: item[1], reverse=True)[:TOP_N]
