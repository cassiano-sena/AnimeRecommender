"""Interface grafica da aplicacao Anime Recommender."""

import statistics
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
import webbrowser

import io
import urllib.request
from pathlib import Path

from data_service import load_animes, validate_image_url, prefetch_valid_urls
from recommendation_engine import RecommendationEngine, TOP_N, format_score
from theme import COLORS, configure_theme


BACKGROUND_IMAGE_PATH = Path(__file__).resolve().parent / "assets" / "anime_background.png"


def _load_poster_image(url, target_w=160, target_h=210):
    """Baixa a capa do anime e a redimensiona via Pillow, preservando a proporcao
    original (usa toda a imagem, sem cortar nenhuma parte)."""
    if not url:
        return None
    try:
        from PIL import Image, ImageTk
        resample = getattr(Image, "Resampling", Image).LANCZOS
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = response.read()
                img = Image.open(io.BytesIO(data)).convert("RGBA")
                # thumbnail redimensiona mantendo a proporcao e nunca excede a caixa alvo
                img.thumbnail((target_w, target_h), resample)
                return ImageTk.PhotoImage(img)
    except Exception:
        pass
    return None


class AnimeRecommenderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Animes Recommender")
        self.geometry("1280x780")
        self.minsize(1080, 680)

        self.animes = load_animes()
        self.anime_by_id = {anime["id"]: anime for anime in self.animes}
        self.engine = RecommendationEngine(self.animes, self.anime_by_id)
        self.ratings = {}

        self.search_var = tk.StringVar()
        self.selected_rating_var = tk.DoubleVar(value=8.0)
        self.selected_anime_id = None
        self.recommendation_tables = {}
        self.shell = None
        self.background_photo = self.load_background_image()
        self.layout_windows = {}
        self.catalog_count_var = tk.StringVar()
        self.rated_summary_var = tk.StringVar(value="Nenhuma avaliacao adicionada")
        self.result_summary_var = tk.StringVar(value="Gere recomendacoes para preencher os rankings")
        self.status_var = tk.StringVar(value=f"{len(self.animes):,} animes carregados")

        configure_theme(self)
        self.build_layout()
        self.refresh_anime_list()
        self.refresh_rated_list()
        prefetch_valid_urls(self.animes)

    def load_background_image(self):
        if not BACKGROUND_IMAGE_PATH.exists():
            return None
        try:
            return tk.PhotoImage(file=str(BACKGROUND_IMAGE_PATH))
        except tk.TclError:
            return None

    def make_panel(self, parent, padding=14):
        return tk.Frame(
            parent,
            bg=COLORS["panel"],
            padx=padding,
            pady=padding,
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            highlightcolor=COLORS["accent"],
        )

    def make_panel_title(self, parent, title, subtitle=None):
        ttk.Label(parent, text=title, style="Title.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(parent, text=subtitle, style="Muted.TLabel").pack(anchor="w", pady=(2, 10))

    def make_scrollable_frame(self, parent):
        outer = ttk.Frame(parent, style="TFrame")
        canvas = tk.Canvas(outer, bg=COLORS["bg"], highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, style="TFrame")
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def update_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_inner(event):
            canvas.itemconfigure(window_id, width=event.width)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        inner.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", resize_inner)
        canvas.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return outer, inner

    def build_layout(self):
        self.shell = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0, borderwidth=0)
        self.shell.pack(fill="both", expand=True)
        if self.background_photo:
            self.shell.create_image(0, 0, anchor="nw", image=self.background_photo, tags=("background",))
        else:
            self.shell.create_rectangle(0, 0, 5000, 5000, fill=COLORS["bg"], outline="", tags=("background",))

        header = tk.Frame(
            self.shell,
            bg=COLORS["panel"],
            padx=18,
            pady=8,
            highlightthickness=1,
            highlightbackground=COLORS["line"],
        )

        title_row = ttk.Frame(header, style="Panel.TFrame")
        title_row.pack(fill="x")
        text_block = ttk.Frame(title_row, style="Panel.TFrame")
        text_block.pack(side="left", fill="x", expand=True)
        ttk.Label(text_block, text="Anime Recommender", style="Header.TLabel").pack(anchor="w")
        badges = ttk.Frame(title_row, style="Panel.TFrame")
        badges.pack(side="right")
        ttk.Label(badges, text=f"{len(self.animes):,} titulos", style="Badge.TLabel").pack(side="left")

        left = ttk.Frame(self.shell, style="TFrame")
        right = ttk.Frame(self.shell, style="TFrame")

        ## pro lado direito ficar scrollable apenas
        self.build_catalog(left)
        scroll_area, scroll_content = self.make_scrollable_frame(right)
        scroll_area.pack(fill="both", expand=True)
        self.build_recommendations(scroll_content)

        ## pro lado esquerdo e direito ficarem scrolalble
        # left_scroll_area, left_scroll_content = self.make_scrollable_frame(left)
        # left_scroll_area.pack(fill="both", expand=True)
        # self.build_catalog(left_scroll_content)
        # right_scroll_area, right_scroll_content = self.make_scrollable_frame(right)
        # right_scroll_area.pack(fill="both", expand=True)
        # self.build_recommendations(right_scroll_content)

        status = tk.Frame(
            self.shell,
            bg=COLORS["panel"],
            padx=14,
            pady=6,
            highlightthickness=1,
            highlightbackground=COLORS["line"],
        )
        ttk.Label(status, textvariable=self.status_var, style="Subheader.TLabel").pack(anchor="w")

        self.layout_windows = {
            "header": self.shell.create_window(22, 14, anchor="nw", window=header),
            "left": self.shell.create_window(22, 78, anchor="nw", window=left),
            "right": self.shell.create_window(520, 78, anchor="nw", window=right),
            "status": self.shell.create_window(22, 720, anchor="nw", window=status),
        }
        self.shell.tag_lower("background")
        self.shell.bind("<Configure>", self.resize_layout)

    # layout
    def resize_layout(self, event):
        width = max(event.width, 960)
        height = max(event.height, 640)
        margin = 22
        gap = 14

        header_height = 70 
        
        status_height = 34
        main_y = margin + header_height + gap
        main_height = max(430, height - main_y - status_height - gap - margin)
        content_width = max(900, width - margin * 2)
        left_width = max(350, int(content_width * 0.42))
        right_width = max(430, content_width - left_width - gap)
        if left_width + right_width + gap > content_width:
            left_width = max(350, content_width - right_width - gap)

        self.shell.coords(self.layout_windows["header"], margin, margin)
        self.shell.itemconfigure(self.layout_windows["header"], width=content_width, height=header_height)
        self.shell.coords(self.layout_windows["left"], margin, main_y)
        self.shell.itemconfigure(self.layout_windows["left"], width=left_width, height=main_height)
        self.shell.coords(self.layout_windows["right"], margin + left_width + gap, main_y)
        self.shell.itemconfigure(self.layout_windows["right"], width=right_width, height=main_height)
        self.shell.coords(self.layout_windows["status"], margin, main_y + main_height + gap)
        self.shell.itemconfigure(self.layout_windows["status"], width=content_width, height=status_height)

    def build_catalog(self, parent):
        catalog = self.make_panel(parent)
        # Para evitar conflitos de altura com o scrollable frame, o catalog nao deve expandir verticalmente
        catalog.pack(fill="x", expand=False)
        # self.make_panel_title(catalog, "Catalogo", "Selecione um anime e atribua uma nota.")

        search_frame = ttk.Frame(catalog, style="Panel.TFrame")
        search_frame.pack(fill="x", pady=(0, 10))
        
        entry = ttk.Entry(search_frame, textvariable=self.search_var)
        entry.pack(fill="x", pady=(5, 0))
    
        placeholder_text = "Buscar por título ou gênero..."
        
        def on_focus_in(_event):
            # Se o texto atual for o placeholder, limpa para o usuário digitar
            if self.search_var.get() == placeholder_text:
                self.search_var.set("")
                entry.configure(foreground=COLORS["text"]) # Cor normal do texto

        def on_focus_out(_event):
            # Se o usuário sair e não digitou nada, repõe o placeholder
            if not self.search_var.get().strip():
                self.search_var.set(placeholder_text)
                entry.configure(foreground=COLORS["muted"]) # Cor cinza/apagada

        # Inicializa o campo com o placeholder ativo
        self.search_var.set(placeholder_text)
        entry.configure(foreground=COLORS["muted"])

        # Vincula os eventos de Foco (clicar dentro e clicar fora)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        
        # Modificado o KeyRelease para ignorar a busca caso seja o texto do placeholder
        def handle_search(_event):
            if self.search_var.get() != placeholder_text:
                self.refresh_anime_list()
                
        entry.bind("<KeyRelease>", handle_search)

        ttk.Label(catalog, textvariable=self.catalog_count_var, style="Muted.TLabel").pack(anchor="w", pady=(0, 6))

        columns = ("title", "score", "members", "cluster")
        tree_wrap = ttk.Frame(catalog, style="Panel.TFrame")
        # expandindo verticalmente para ocupar o espaço disponível, mas não expandindo horizontalmente
        tree_wrap.pack(fill="x", expand=False)
        # height
        self.anime_tree = ttk.Treeview(tree_wrap, columns=columns, show="headings", selectmode="browse", height=8)
        self.anime_tree.heading("title", text="Anime")
        self.anime_tree.heading("score", text="Score")
        self.anime_tree.heading("members", text="Membros")
        self.anime_tree.heading("cluster", text="Cluster")
        self.anime_tree.column("title", width=330)
        self.anime_tree.column("score", width=70, anchor="center")
        self.anime_tree.column("members", width=90, anchor="e")
        self.anime_tree.column("cluster", width=70, anchor="center")
        self.anime_tree.tag_configure("odd", background="#101827")
        self.anime_tree.tag_configure("even", background="#142033")
        self.anime_tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.anime_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.anime_tree.configure(yscrollcommand=scrollbar.set)
        self.anime_tree.bind("<<TreeviewSelect>>", self.on_anime_selected)
        self.anime_tree.bind("<Double-1>", lambda _event: self.add_selected_rating())

        controls = ttk.Frame(catalog, style="Panel.TFrame")
        controls.pack(fill="x", pady=(12, 0))
        ttk.Label(controls, text="Nota", style="Body.TLabel").pack(side="left")
        ttk.Spinbox(
            controls,
            from_=0,
            to=10,
            increment=0.5,
            width=6,
            textvariable=self.selected_rating_var,
            format="%.1f",
        ).pack(side="left", padx=(8, 10))
        ttk.Button(controls, text="Adicionar", style="Accent.TButton", command=self.add_selected_rating).pack(side="left")
        ttk.Button(controls, text="Abrir link", command=self.open_selected_link).pack(side="left", padx=(8, 0))

        details = ttk.Frame(catalog, style="Soft.TFrame", padding=12)
        details.pack(fill="x", pady=(12, 0))
        self.poster = tk.Canvas(details, width=170, height=240, bg=COLORS["panel_alt"], highlightthickness=0)
        self.poster.pack(side="left", padx=(0, 12))
        info = ttk.Frame(details, style="Soft.TFrame")
        info.pack(side="left", fill="both", expand=True)
        self.detail_title = ttk.Label(info, text="Selecione um anime", background=COLORS["panel_alt"], foreground=COLORS["text"], font=("Segoe UI", 14, "bold"), wraplength=460)
        self.detail_title.pack(anchor="w", pady=(4, 10))
        self.detail_meta = ttk.Label(info, text="Os detalhes aparecem aqui.", background=COLORS["panel_alt"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        self.detail_meta.pack(anchor="w", pady=(0, 12))
        
        text_container = ttk.Frame(info, style="Soft.TFrame")
        text_container.pack(fill="x", expand=True)

        synopsis_scroll = ttk.Scrollbar(text_container, orient="vertical")
        
        # details
        self.details = tk.Text(
            text_container, 
            height=10, 
            wrap="word", 
            font=("Segoe UI", 9), 
            bg=COLORS["panel_alt"], 
            fg=COLORS["text"], 
            insertbackground=COLORS["text"], 
            relief="flat", 
            borderwidth=0,
            yscrollcommand=synopsis_scroll.set
        )
        synopsis_scroll.config(command=self.details.yview)

        self.details.pack(side="left", fill="both", expand=True)
        synopsis_scroll.pack(side="right", fill="y")
        
        self.details.configure(state="disabled")
        self.draw_poster(None)

    def build_recommendations(self, parent):
        rated_frame = self.make_panel(parent)
        rated_frame.pack(fill="x")
        self.make_panel_title(rated_frame, "Seu perfil", "As notas adicionadas alimentam todos os metodos.")
        ttk.Label(rated_frame, textvariable=self.rated_summary_var, style="Muted.TLabel").pack(anchor="w", pady=(0, 6))

        rated_columns = ("title", "rating")
        self.rated_tree = ttk.Treeview(rated_frame, columns=rated_columns, show="headings", height=5)
        self.rated_tree.heading("title", text="Anime")
        self.rated_tree.heading("rating", text="Nota")
        self.rated_tree.column("title", width=420)
        self.rated_tree.column("rating", width=80, anchor="center")
        self.rated_tree.tag_configure("odd", background="#101827")
        self.rated_tree.tag_configure("even", background="#142033")
        self.rated_tree.pack(fill="x", expand=True)

        rated_buttons = ttk.Frame(rated_frame, style="Panel.TFrame")
        rated_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(rated_buttons, text="Remover", style="Danger.TButton", command=self.remove_selected_rating).pack(side="left")
        ttk.Button(rated_buttons, text="Limpar", command=self.clear_ratings).pack(side="left", padx=(8, 0))
        ttk.Button(rated_buttons, text="Gerar recomendacoes", style="Accent.TButton", command=self.generate_recommendations).pack(side="right")

        result_frame = self.make_panel(parent)
        result_frame.pack(fill="both", expand=True, pady=(12, 0))
        self.make_panel_title(result_frame, "Rankings recomendados", "Duas vezes clique em qualquer resultado para abrir o link.")
        ttk.Label(result_frame, textvariable=self.result_summary_var, style="Muted.TLabel").pack(anchor="w", pady=(0, 8))

        self.tabs = ttk.Notebook(result_frame)
        self.tabs.pack(fill="both", expand=True, pady=(12, 0))

        tab_names = [
            "Colaborativa por item",
            "Colaborativa por usuario",
            "Popularidade",
            "Conteudo",
        ]
        for tab_name in tab_names:
            frame = ttk.Frame(self.tabs, style="Panel.TFrame", padding=8)
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
        table.tag_configure("odd", background="#101827")
        table.tag_configure("even", background="#142033")
        table.tag_configure("top", background="#164e63", foreground="#ecfeff")
        table.pack(fill="both", expand=True)
        table.bind("<Double-1>", self.open_recommendation_link)
        table.bind("<<TreeviewSelect>>", lambda e: self._sync_top_tag(e.widget))
        return table

    def refresh_anime_list(self):
        query = self.search_var.get().strip().lower()

        if query == "buscar por título ou gênero...":
            query = ""

        terms = query.split()

        self.anime_tree.delete(*self.anime_tree.get_children())

        count = 0
        total_matches = 0

        for anime in self.animes:

            if terms:
                title_lower = anime["title"].lower()
                genres_normalized = {g.lower() for g in anime["genres"]}

                match = True

                for term in terms:
                    term_clean = term.replace("'", "").lower()
                    # Cada termo deve existir no título OU nos gêneros
                    if term_clean not in title_lower and term_clean not in genres_normalized:
                        match = False
                        break

                if not match:
                    continue

            total_matches += 1

            if count >= 250:
                continue

            self.anime_tree.insert(
                "",
                "end",
                iid=str(anime["id"]),
                values=(
                    anime["title"],
                    format_score(anime["score"]),
                    f"{anime['members']:,}",
                    anime["cluster"],
                ),
                tags=("even" if count % 2 == 0 else "odd",),
            )

            count += 1

        shown = f"{count:,} exibidos"

        if total_matches > count:
            shown += f" de {total_matches:,}"

        self.catalog_count_var.set(shown)

    def refresh_rated_list(self):
        self.rated_tree.delete(*self.rated_tree.get_children())
        sorted_ratings = sorted(
            self.ratings.items(),
            key=lambda item: self.anime_by_id[item[0]]["title"].lower(),
        )
        for index, (anime_id, rating) in enumerate(sorted_ratings):
            anime = self.anime_by_id[anime_id]
            self.rated_tree.insert(
                "",
                "end",
                iid=str(anime_id),
                values=(anime["title"], f"{rating:.1f}"),
                tags=("even" if index % 2 == 0 else "odd",),
            )
        if self.ratings:
            average = statistics.mean(self.ratings.values())
            self.rated_summary_var.set(f"{len(self.ratings)} avaliados | media {average:.1f}/10")
        else:
            self.rated_summary_var.set("Nenhuma avaliacao adicionada")

    def on_anime_selected(self, _event=None):
        selected = self.anime_tree.selection()
        if not selected:
            return
        self.selected_anime_id = int(selected[0])
        anime = self.anime_by_id[self.selected_anime_id]
        self.detail_title.configure(text=anime["title"])
        self.detail_meta.configure(
            text=(
                f"{anime['genre']} | Episodios: {anime['episodes']} | "
                f"Score {format_score(anime['score'])} | {anime['members']:,} membros"
            )
        )
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", anime["synopsis"][:600])
        self.details.configure(state="disabled")
        self.draw_poster(anime)
        self.status_var.set(f"Selecionado: {anime['title']}")

    def draw_poster(self, anime):
        self.poster.delete("all")
        width = 170
        height = 240
        pad = 9
        footer_height = 46
        image_area_w = width - 2 * pad
        image_area_h = height - 2 * pad - footer_height
        palette = ["#0e7490", "#be185d", "#7c3aed", "#ca8a04", "#16a34a", "#dc2626"]
        cluster = anime["cluster"] if anime else 0
        color = palette[abs(cluster) % len(palette)]
        self.poster.create_rectangle(0, 0, width, height, fill="#0b1120", outline=COLORS["line"])
        self.poster.create_rectangle(pad, pad, width - pad, height - pad, fill=color, outline="")
        self.poster.create_rectangle(pad, height - pad - footer_height, width - pad, height - pad, fill="#111827", outline="")

        image = None
        if anime:
            url = anime.get("image", "")
            if url and validate_image_url(url):
                image = _load_poster_image(url, image_area_w, image_area_h)

        if image:
            self._current_poster_image = image
            iw = image.width()
            ih = image.height()
            # A imagem ja vem redimensionada (sem cortar); apenas centralizamos na area disponivel
            x = pad + image_area_w // 2
            y = pad + image_area_h // 2
            self.poster.create_image(x, y, image=image, anchor="center")
        else:
            self.poster.create_text(width // 2, pad + image_area_h // 2, text="ANIME", fill="#f8fafc", font=("Segoe UI", 16, "bold"))

        if anime:
            title = anime["title"]
            short_title = title[:30] + ("..." if len(title) > 30 else "")
            font_size = 8 if len(short_title) > 22 else 9
            self.poster.create_text(
                width // 2, height - footer_height - pad + 8,
                text=short_title,
                fill="#f8fafc",
                font=("Segoe UI", font_size, "bold"),
                width=image_area_w,
                anchor="n",
                justify="center"
            )
            self.poster.create_text(
                width // 2, height - pad - 6,
                text=f"Score {format_score(anime['score'])}",
                fill=COLORS["gold"],
                font=("Segoe UI", 9, "bold"),
                anchor="s"
            )
        else:
            self.poster.create_text(
                width // 2, height // 2,
                text="selecione um titulo",
                fill="#cbd5e1",
                font=("Segoe UI", 8, "bold"),
                width=image_area_w
            )

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
        anime = self.anime_by_id[self.selected_anime_id]
        self.status_var.set(f"Avaliacao salva: {anime['title']} recebeu {rating:.1f}")

    def remove_selected_rating(self):
        selected = self.rated_tree.selection()
        if not selected:
            return
        for item in selected:
            self.ratings.pop(int(item), None)
        self.refresh_rated_list()
        self.status_var.set("Avaliacao removida")

    def clear_ratings(self):
        self.ratings.clear()
        self.refresh_rated_list()
        self.result_summary_var.set("Gere recomendacoes para preencher os rankings")
        for table in self.recommendation_tables.values():
            table.delete(*table.get_children())
        self.status_var.set("Avaliacoes limpas")

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

    def _sync_top_tag(self, table):
        """Garante que a tag 'top' (destaque do 1º lugar) nao confunda com selecao.

        Quando o usuario seleciona qualquer linha que NAO seja a primeira, a tag
        visual 'top' e removida temporariamente do primeiro item para que ele nao
        parecam ambos selecionados ao mesmo tempo. Ao selecionar a primeira linha
        (ou limpar a selecao), a tag 'top' e restaurada.
        """
        children = table.get_children()
        if not children:
            return
        first_iid = children[0]
        selected = table.selection()
        if selected and selected[0] != first_iid:
            # Outra linha foi selecionada: esconde destaque do 1o lugar
            table.item(first_iid, tags=("even",))
        else:
            # Nada selecionado ou o proprio 1o lugar foi clicado: restaura destaque
            table.item(first_iid, tags=("top",))

    def generate_recommendations(self):
        if not self.ratings:
            messagebox.showwarning("Sem avaliacoes", "Adicione pelo menos uma avaliacao maior que zero.")
            return

        recommendations = self.engine.generate(self.ratings)
        for name, rows in recommendations.items():
            self.fill_recommendation_table(self.recommendation_tables[name], rows)
        self.result_summary_var.set(f"{TOP_N} sugestoes geradas por metodo com base em {len(self.ratings)} avaliacao(oes)")
        self.status_var.set("Recomendacoes atualizadas")

    def fill_recommendation_table(self, table, rows):
        table.delete(*table.get_children())
        table.selection_remove(*table.selection())
        for index, (anime, value) in enumerate(rows):
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
                tags=("top" if index == 0 else "even" if index % 2 == 0 else "odd",),
            )