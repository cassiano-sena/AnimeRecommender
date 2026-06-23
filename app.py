"""Ponto de entrada da aplicacao."""

from tkinter import messagebox

from ui import AnimeRecommenderApp


def main():
    try:
        app = AnimeRecommenderApp()
    except Exception as exc:
        messagebox.showerror("Erro ao iniciar", str(exc))
        return
    app.mainloop()


if __name__ == "__main__":
    main()
