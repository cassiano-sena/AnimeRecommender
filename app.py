import csv
import math
import statistics
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
import webbrowser


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "urlanime1.csv"
TOP_N = 10


def parse_float(value, default=0.0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except ValueError:
        return default


def parse_int(value, default=0):
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except ValueError:
        return default


def parse_genres(value):
    return {
        genre.strip().replace('"', "").replace("'", "")
        for genre in (value or "").split(",")
        if genre.strip()
    }


def load_animes():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Arquivo de dados nao encontrado: {DATA_PATH}")

    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    animes = []
    for row in rows:
        anime = {
            "id": parse_int(row.get("uid")),
            "title": (row.get("title") or "").strip(),
            "synopsis": (row.get("synopsis") or "").strip(),
            "genre": (row.get("genre") or "").strip(),
            "genres": parse_genres(row.get("genre")),
            "episodes": row.get("episodes") or "",
            "members": parse_int(row.get("members")),
            "popularity": parse_int(row.get("popularity")),
            "ranked": parse_int(row.get("ranked")),
            "score": parse_float(row.get("score")),
            "image": row.get("img_url") or "",
            "link": row.get("link") or "",
            "cluster": parse_int(row.get("cluster"), -1),
        }
        if anime["id"] and anime["title"]:
            animes.append(anime)

    return sorted(animes, key=lambda item: item["title"].lower())


def similarity(left, right):
    union = left["genres"] | right["genres"]
    if not union:
        return 0.0
    return len(left["genres"] & right["genres"]) / len(union)


def popularity_value(anime):
    return math.log1p(anime["members"]) * max(anime["score"], 0.0)


def format_score(value):
    return f"{value:.2f}"


class AnimeRecommenderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Animes Recommender")
        self.geometry("1120x720")
        self.minsize(980, 620)

        self.animes = load_animes()
        self.anime_by_id = {anime["id"]: anime for anime in self.animes}
        self.ratings = {}

        self.search_var = tk.StringVar()
        self.selected_rating_var = tk.DoubleVar(value=8.0)
        self.selected_anime_id = None
        self.recommendation_tables = {}

        self.configure_style()
        self.build_layout()
        self.refresh_anime_list()
        self.refresh_rated_list()

    def configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f6f7f9")
        style.configure("Header.TLabel", background="#f6f7f9", font=("Segoe UI", 18, "bold"))
        style.configure("Subheader.TLabel", background="#f6f7f9", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def build_layout(self):
        header = ttk.Frame(self, padding=(18, 16, 18, 8))
        header.pack(fill="x")
        ttk.Label(header, text="Animes Recommender", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Selecione animes avaliados, informe notas e gere recomendacoes em Python.",
            style="Subheader.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        main = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=18, pady=12)

        left = ttk.Frame(main, padding=10)
        right = ttk.Frame(main, padding=10)
        main.add(left, weight=2)
        main.add(right, weight=3)

        self.build_catalog(left)
        self.build_recommendations(right)

    def build_catalog(self, parent):
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(search_frame, text="Buscar anime").pack(anchor="w")
        entry = ttk.Entry(search_frame, textvariable=self.search_var)
        entry.pack(fill="x", pady=(4, 0))
        entry.bind("<KeyRelease>", lambda _event: self.refresh_anime_list())

        columns = ("title", "score", "members", "cluster")
        self.anime_tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        self.anime_tree.heading("title", text="Anime")
        self.anime_tree.heading("score", text="Score")
        self.anime_tree.heading("members", text="Membros")
        self.anime_tree.heading("cluster", text="Cluster")
        self.anime_tree.column("title", width=310)
        self.anime_tree.column("score", width=70, anchor="center")
        self.anime_tree.column("members", width=90, anchor="e")
        self.anime_tree.column("cluster", width=70, anchor="center")
        self.anime_tree.pack(fill="both", expand=True)
        self.anime_tree.bind("<<TreeviewSelect>>", self.on_anime_selected)
        self.anime_tree.bind("<Double-1>", lambda _event: self.add_selected_rating())

        controls = ttk.Frame(parent)
        controls.pack(fill="x", pady=(10, 0))
        ttk.Label(controls, text="Nota").pack(side="left")
        ttk.Spinbox(
            controls,
            from_=0,
            to=10,
            increment=0.5,
            width=6,
            textvariable=self.selected_rating_var,
            format="%.1f",
        ).pack(side="left", padx=(8, 10))
        ttk.Button(controls, text="Adicionar avaliacao", command=self.add_selected_rating).pack(side="left")
        ttk.Button(controls, text="Abrir link", command=self.open_selected_link).pack(side="left", padx=(8, 0))

        self.details = tk.Text(parent, height=8, wrap="word", font=("Segoe UI", 10))
        self.details.pack(fill="x", pady=(10, 0))
        self.details.configure(state="disabled")

    def build_recommendations(self, parent):
        rated_frame = ttk.LabelFrame(parent, text="Avaliacoes do usuario", padding=10)
        rated_frame.pack(fill="x")

        rated_columns = ("title", "rating")
        self.rated_tree = ttk.Treeview(rated_frame, columns=rated_columns, show="headings", height=5)
        self.rated_tree.heading("title", text="Anime")
        self.rated_tree.heading("rating", text="Nota")
        self.rated_tree.column("title", width=420)
        self.rated_tree.column("rating", width=80, anchor="center")
        self.rated_tree.pack(fill="x", expand=True)

        rated_buttons = ttk.Frame(rated_frame)
        rated_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(rated_buttons, text="Remover selecionado", command=self.remove_selected_rating).pack(side="left")
        ttk.Button(rated_buttons, text="Limpar avaliacoes", command=self.clear_ratings).pack(side="left", padx=(8, 0))
        ttk.Button(rated_buttons, text="Gerar recomendacoes", command=self.generate_recommendations).pack(side="right")

        self.tabs = ttk.Notebook(parent)
        self.tabs.pack(fill="both", expand=True, pady=(12, 0))

        tab_names = [
            "Colaborativa por item",
            "Colaborativa por usuario",
            "Popularidade",
            "Conteudo",
        ]
        for tab_name in tab_names:
            frame = ttk.Frame(self.tabs, padding=8)
            self.tabs.add(frame, text=tab_name)
            table = self.create_recommendation_table(frame)
            self.recommendation_tables[tab_name] = table

    def create_recommendation_table(self, parent):
        columns = ("title", "reason", "score", "members", "cluster")
        table = ttk.Treeview(parent, columns=columns, show="headings")
        table.heading("title", text="Anime")
        table.heading("reason", text="Afinidade")
        table.heading("score", text="Score")
        table.heading("members", text="Membros")
        table.heading("cluster", text="Cluster")
        table.column("title", width=300)
        table.column("reason", width=100, anchor="center")
        table.column("score", width=80, anchor="center")
        table.column("members", width=100, anchor="e")
        table.column("cluster", width=80, anchor="center")
        table.pack(fill="both", expand=True)
        table.bind("<Double-1>", self.open_recommendation_link)
        return table

    def refresh_anime_list(self):
        query = self.search_var.get().strip().lower()
        self.anime_tree.delete(*self.anime_tree.get_children())
        count = 0
        for anime in self.animes:
            if query and query not in anime["title"].lower() and query not in anime["genre"].lower():
                continue
            self.anime_tree.insert(
                "",
                "end",
                iid=str(anime["id"]),
                values=(anime["title"], format_score(anime["score"]), f"{anime['members']:,}", anime["cluster"]),
            )
            count += 1
            if count >= 250:
                break

    def refresh_rated_list(self):
        self.rated_tree.delete(*self.rated_tree.get_children())
        for anime_id, rating in sorted(
            self.ratings.items(),
            key=lambda item: self.anime_by_id[item[0]]["title"].lower(),
        ):
            anime = self.anime_by_id[anime_id]
            self.rated_tree.insert("", "end", iid=str(anime_id), values=(anime["title"], f"{rating:.1f}"))

    def on_anime_selected(self, _event=None):
        selected = self.anime_tree.selection()
        if not selected:
            return
        self.selected_anime_id = int(selected[0])
        anime = self.anime_by_id[self.selected_anime_id]
        text = (
            f"{anime['title']}\n"
            f"Generos: {anime['genre']}\n"
            f"Episodios: {anime['episodes']} | Score: {format_score(anime['score'])} | "
            f"Membros: {anime['members']:,}\n\n"
            f"{anime['synopsis'][:600]}"
        )
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", text)
        self.details.configure(state="disabled")

    def add_selected_rating(self):
        if self.selected_anime_id is None:
            messagebox.showinfo("Selecao necessaria", "Selecione um anime na lista.")
            return
        rating = self.selected_rating_var.get()
        if rating <= 0:
            self.ratings.pop(self.selected_anime_id, None)
        else:
            self.ratings[self.selected_anime_id] = float(rating)
        self.refresh_rated_list()

    def remove_selected_rating(self):
        selected = self.rated_tree.selection()
        if not selected:
            return
        for item in selected:
            self.ratings.pop(int(item), None)
        self.refresh_rated_list()

    def clear_ratings(self):
        self.ratings.clear()
        self.refresh_rated_list()

    def open_selected_link(self):
        if self.selected_anime_id is None:
            messagebox.showinfo("Selecao necessaria", "Selecione um anime na lista.")
            return
        link = self.anime_by_id[self.selected_anime_id]["link"]
        if link:
            webbrowser.open(link)

    def open_recommendation_link(self, event):
        table = event.widget
        selected = table.selection()
        if not selected:
            return
        anime = self.anime_by_id.get(int(selected[0]))
        if anime and anime["link"]:
            webbrowser.open(anime["link"])

    def generate_recommendations(self):
        if not self.ratings:
            messagebox.showwarning("Sem avaliacoes", "Adicione pelo menos uma avaliacao maior que zero.")
            return

        rated_ids = set(self.ratings)
        recommendations = {
            "Colaborativa por item": self.recommend_by_item(rated_ids),
            "Colaborativa por usuario": self.recommend_by_cluster(rated_ids),
            "Popularidade": self.recommend_by_popularity(rated_ids),
            "Conteudo": self.recommend_by_content(rated_ids),
        }
        for name, rows in recommendations.items():
            self.fill_recommendation_table(self.recommendation_tables[name], rows)

    def fill_recommendation_table(self, table, rows):
        table.delete(*table.get_children())
        for anime, value in rows:
            table.insert(
                "",
                "end",
                iid=str(anime["id"]),
                values=(
                    anime["title"],
                    format_score(value),
                    format_score(anime["score"]),
                    f"{anime['members']:,}",
                    anime["cluster"],
                ),
            )

    def recommend_by_item(self, rated_ids):
        rows = []
        rated_animes = [self.anime_by_id[anime_id] for anime_id in rated_ids]
        for anime in self.animes:
            if anime["id"] in rated_ids:
                continue
            total = 0.0
            weight_sum = 0.0
            for rated in rated_animes:
                weight = similarity(anime, rated)
                total += weight * self.ratings[rated["id"]]
                weight_sum += weight
            predicted = total / weight_sum if weight_sum else 0.0
            rows.append((anime, predicted))
        return sorted(rows, key=lambda item: (item[1], popularity_value(item[0])), reverse=True)[:TOP_N]

    def recommend_by_cluster(self, rated_ids):
        cluster_scores = {}
        for anime_id, rating in self.ratings.items():
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

    def recommend_by_content(self, rated_ids):
        genre_weights = {}
        cluster_weights = {}
        for anime_id, rating in self.ratings.items():
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


def main():
    try:
        app = AnimeRecommenderApp()
    except Exception as exc:
        messagebox.showerror("Erro ao iniciar", str(exc))
        return
    app.mainloop()


if __name__ == "__main__":
    main()
