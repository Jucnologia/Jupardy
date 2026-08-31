
import json
import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

try:
    import pygame
    pygame.mixer.init()
    AUDIO_AVAILABLE = True
except Exception:
    pygame = None
    AUDIO_AVAILABLE = False


# ============================================================
# KONFIGURATION
# ============================================================

POINTS = [100, 200, 300, 400, 500]
CATEGORY_COUNT = 5
MAX_PLAYERS = 8

BG = "#252525"
PANEL = "#303030"
PANEL_DARK = "#1E1E1E"
PANEL_LIGHT = "#383838"

CYAN = "#00E5FF"
CYAN_HOVER = "#5DF2FF"
CYAN_DARK = "#0097A7"

TEXT = "#F2F2F2"
TEXT_SECONDARY = "#AAAAAA"

DANGER = "#FF5252"
SUCCESS = "#69F0AE"

FONT = "Segoe UI"


# ============================================================
# DESIGN HELPER
# ============================================================

def create_button(
    parent,
    text,
    command,
    width=None,
    font_size=10,
    bold=False,
    accent=CYAN
):
    font_style = "bold" if bold else "normal"

    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=PANEL_DARK,
        fg=accent,
        activebackground=accent,
        activeforeground=BG,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=accent,
        highlightcolor=accent,
        cursor="hand2",
        font=(FONT, font_size, font_style),
        padx=12,
        pady=7
    )

    if width is not None:
        button.config(width=width)

    def enter(event):
        if str(button["state"]) != "disabled":
            button.config(bg=accent, fg=BG)

    def leave(event):
        if str(button["state"]) != "disabled":
            button.config(bg=PANEL_DARK, fg=accent)

    button.bind("<Enter>", enter)
    button.bind("<Leave>", leave)

    return button


def create_entry(parent):
    border = tk.Frame(
        parent,
        bg=CYAN,
        padx=1,
        pady=1
    )

    entry = tk.Entry(
        border,
        bg=PANEL_DARK,
        fg=TEXT,
        insertbackground=CYAN,
        selectbackground=CYAN,
        selectforeground=BG,
        relief="flat",
        bd=0,
        font=(FONT, 10)
    )

    entry.pack(
        fill="both",
        expand=True,
        ipady=6,
        padx=1,
        pady=1
    )

    return border, entry


def create_text_area(parent, height=5):
    border = tk.Frame(
        parent,
        bg=CYAN,
        padx=1,
        pady=1
    )

    text = tk.Text(
        border,
        height=height,
        bg=PANEL_DARK,
        fg=TEXT,
        insertbackground=CYAN,
        selectbackground=CYAN,
        selectforeground=BG,
        relief="flat",
        bd=0,
        wrap="word",
        font=(FONT, 11),
        padx=10,
        pady=10
    )

    text.pack(fill="both", expand=True)

    return border, text


def create_section(parent, title):
    outer = tk.Frame(
        parent,
        bg=CYAN,
        padx=1,
        pady=1
    )

    inner = tk.Frame(
        outer,
        bg=PANEL
    )

    inner.pack(fill="both", expand=True)

    tk.Label(
        inner,
        text=title,
        bg=PANEL,
        fg=CYAN,
        font=(FONT, 11, "bold")
    ).pack(
        anchor="w",
        padx=12,
        pady=(10, 5)
    )

    content = tk.Frame(
        inner,
        bg=PANEL
    )

    content.pack(
        fill="both",
        expand=True,
        padx=12,
        pady=(0, 12)
    )

    return outer, content


# ============================================================
# JUPARDY EDITOR
# ============================================================

class JupardyApp:

    def __init__(self, root):
        self.root = root

        self.root.title("Jupardy Editor")
        self.root.geometry("1350x800")
        self.root.minsize(1050, 700)
        self.root.configure(bg=BG)

        self.game_folder = None
        self.gamefile_folder = None
        self.mediaq_folder = None
        self.mediaa_folder = None

        self.data = self.create_empty_data()

        self.create_ui()
        self.refresh_editor()

    # ========================================================
    # LEERE SPIELDATEN
    # ========================================================

    def create_empty_data(self):
        data = {
            "format": "jupardy",
            "version": 2,
            "title": "Mein Jupardy",
            "categories": []
        }

        for i in range(CATEGORY_COUNT):
            category = {
                "name": f"Kategorie {i + 1}",
                "questions": {}
            }

            for points in POINTS:
                category["questions"][str(points)] = {
                    "type": "text",
                    "question": "",
                    "answer": "",
                    "media": "",
                    "answer_media": ""
                }

            data["categories"].append(category)

        return data

    # ========================================================
    # EDITOR UI
    # ========================================================

    def create_ui(self):
        header = tk.Frame(
            self.root,
            bg=PANEL,
            height=75
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=PANEL)
        left.pack(side="left", padx=25)

        tk.Label(
            left,
            text="JUPARDY",
            bg=PANEL,
            fg=CYAN,
            font=(FONT, 22, "bold")
        ).pack(side="left")

        tk.Label(
            left,
            text="  EDITOR",
            bg=PANEL,
            fg=TEXT,
            font=(FONT, 22)
        ).pack(side="left")

        right = tk.Frame(header, bg=PANEL)
        right.pack(side="right", padx=25)

        create_button(
            right,
            "Spielordner erstellen",
            self.create_game_folder
        ).pack(side="left", padx=4)

        create_button(
            right,
            "Spielordner laden",
            self.load_game_folder
        ).pack(side="left", padx=4)

        create_button(
            right,
            "Speichern",
            self.save_game
        ).pack(side="left", padx=4)

        create_button(
            right,
            "Spiel starten",
            self.start_game,
            bold=True
        ).pack(side="left", padx=(15, 4))

        tk.Frame(
            self.root,
            bg=CYAN,
            height=2
        ).pack(fill="x")

        folder_bar = tk.Frame(self.root, bg=BG)
        folder_bar.pack(
            fill="x",
            padx=25,
            pady=(15, 5)
        )

        tk.Label(
            folder_bar,
            text="SPIELEORDNER",
            bg=BG,
            fg=TEXT_SECONDARY,
            font=(FONT, 9, "bold")
        ).pack(side="left")

        self.folder_label = tk.Label(
            folder_bar,
            text="Kein Spieleordner ausgewählt",
            bg=BG,
            fg=DANGER,
            font=(FONT, 9)
        )

        self.folder_label.pack(
            side="left",
            padx=15
        )

        create_button(
            folder_bar,
            "Ordner öffnen",
            self.open_game_folder,
            font_size=9
        ).pack(side="right")

        main = tk.Frame(self.root, bg=BG)
        main.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=15
        )

        # Kategorien
        category_outer, category_content = create_section(
            main,
            "KATEGORIEN"
        )

        category_outer.pack(
            side="left",
            fill="y",
            padx=(0, 15)
        )

        self.category_entries = []

        for i in range(CATEGORY_COUNT):
            tk.Label(
                category_content,
                text=f"KATEGORIE {i + 1}",
                bg=PANEL,
                fg=TEXT_SECONDARY,
                font=(FONT, 8, "bold")
            ).pack(
                anchor="w",
                pady=(10, 4)
            )

            border, entry = create_entry(category_content)
            border.pack(fill="x")

            entry.bind(
                "<FocusOut>",
                lambda event, index=i:
                self.update_category_name(index)
            )

            self.category_entries.append(entry)

        # Fragen
        question_outer, question_content = create_section(
            main,
            "FRAGEN & PUNKTE"
        )

        question_outer.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 15)
        )

        self.question_buttons = []

        for category_index in range(CATEGORY_COUNT):
            row = tk.Frame(
                question_content,
                bg=PANEL
            )

            row.pack(fill="x", pady=7)

            tk.Label(
                row,
                text=f"K{category_index + 1}",
                bg=PANEL,
                fg=TEXT_SECONDARY,
                width=4,
                font=(FONT, 10, "bold")
            ).pack(side="left")

            buttons = []

            for points in POINTS:
                button = create_button(
                    row,
                    str(points),
                    lambda c=category_index, p=points:
                    self.open_question_editor(c, p),
                    width=7,
                    font_size=11,
                    bold=True
                )

                button.pack(side="left", padx=4)
                buttons.append(button)

            self.question_buttons.append(buttons)

        # Ordnerinfo
        info_outer, info_content = create_section(
            main,
            "SPIELEORDNER"
        )

        info_outer.pack(
            side="left",
            fill="both",
            expand=True
        )

        info_text = (
            "Portable Jupardy-Struktur\n\n"
            "spieleordner/\n"
            "  gamefile/\n"
            "    game.json\n"
            "  mediaq/\n"
            "    Medien der Fragen\n"
            "  mediaa/\n"
            "    Medien der Antworten\n\n"
            "Ausgewählte Medien werden automatisch "
            "in den Spieleordner kopiert.\n\n"
            "Dadurch kann der komplette Spieleordner "
            "auf einen anderen PC kopiert werden."
        )

        tk.Label(
            info_content,
            text=info_text,
            bg=PANEL,
            fg=TEXT,
            justify="left",
            anchor="nw",
            wraplength=330,
            font=(FONT, 10)
        ).pack(anchor="nw")

        footer = tk.Frame(
            self.root,
            bg=PANEL_DARK,
            height=35
        )

        footer.pack(fill="x")
        footer.pack_propagate(False)

        tk.Label(
            footer,
            text="By Jucno",
            bg=PANEL_DARK,
            fg=TEXT_SECONDARY,
            font=(FONT, 8)
        ).pack(side="left", padx=20)

    # ========================================================
    # SPIELEORDNER
    # ========================================================

    def set_game_folder(self, folder):
        self.game_folder = os.path.abspath(folder)

        self.gamefile_folder = os.path.join(
            self.game_folder,
            "gamefile"
        )

        self.mediaq_folder = os.path.join(
            self.game_folder,
            "mediaq"
        )

        self.mediaa_folder = os.path.join(
            self.game_folder,
            "mediaa"
        )

        os.makedirs(
            self.gamefile_folder,
            exist_ok=True
        )

        os.makedirs(
            self.mediaq_folder,
            exist_ok=True
        )

        os.makedirs(
            self.mediaa_folder,
            exist_ok=True
        )

        self.folder_label.config(
            text=self.game_folder,
            fg=CYAN
        )

    # ========================================================
    # SPIELEORDNER ERSTELLEN
    # ========================================================

    def create_game_folder(self):
        parent_folder = filedialog.askdirectory(
            title="Speicherort für Spieleordner auswählen"
        )

        if not parent_folder:
            return

        name_window = tk.Toplevel(self.root)
        name_window.title("Spieleordner erstellen")
        name_window.geometry("500x230")
        name_window.resizable(False, False)
        name_window.configure(bg=BG)
        name_window.transient(self.root)
        name_window.grab_set()

        tk.Label(
            name_window,
            text="NAME DES SPIELEORDNERS",
            bg=BG,
            fg=CYAN,
            font=(FONT, 10, "bold")
        ).pack(
            anchor="w",
            padx=30,
            pady=(30, 8)
        )

        border, entry = create_entry(name_window)
        border.pack(fill="x", padx=30)

        entry.insert(0, "Mein Jupardy")
        entry.focus_set()

        def create():
            folder_name = entry.get().strip()

            if not folder_name:
                messagebox.showerror(
                    "Fehler",
                    "Bitte einen Namen eingeben.",
                    parent=name_window
                )
                return

            invalid = '<>:"/\\|?*'

            if any(
                character in folder_name
                for character in invalid
            ):
                messagebox.showerror(
                    "Fehler",
                    "Der Ordnername enthält ungültige Zeichen.",
                    parent=name_window
                )
                return

            target = os.path.join(
                parent_folder,
                folder_name
            )

            if os.path.exists(target):
                messagebox.showerror(
                    "Fehler",
                    "Dieser Ordner existiert bereits.",
                    parent=name_window
                )
                return

            try:
                os.makedirs(target)

                self.set_game_folder(target)
                self.data = self.create_empty_data()
                self.data["title"] = folder_name

                self.refresh_editor()
                self.save_game(show_message=False)

                name_window.destroy()

                messagebox.showinfo(
                    "Spieleordner erstellt",
                    "Der Spieleordner wurde erstellt.\n\n"
                    f"{target}",
                    parent=self.root
                )

            except Exception as exc:
                messagebox.showerror(
                    "Fehler",
                    str(exc),
                    parent=name_window
                )

        buttons = tk.Frame(
            name_window,
            bg=BG
        )

        buttons.pack(
            fill="x",
            padx=30,
            pady=25
        )

        create_button(
            buttons,
            "Abbrechen",
            name_window.destroy
        ).pack(side="right")

        create_button(
            buttons,
            "ERSTELLEN",
            create,
            bold=True
        ).pack(
            side="right",
            padx=10
        )

        entry.bind(
            "<Return>",
            lambda event: create()
        )

    # ========================================================
    # SPIELEORDNER LADEN
    # ========================================================

    def load_game_folder(self):
        folder = filedialog.askdirectory(
            title="Jupardy Spieleordner auswählen"
        )

        if not folder:
            return

        gamefile = os.path.join(
            folder,
            "gamefile",
            "game.json"
        )

        if not os.path.isfile(gamefile):
            messagebox.showerror(
                "Kein Jupardy-Spiel",
                "Im ausgewählten Ordner wurde keine "
                "gültige Spieldatei gefunden.\n\n"
                "Erwartet wird:\n"
                "gamefile/game.json"
            )
            return

        try:
            with open(
                gamefile,
                "r",
                encoding="utf-8"
            ) as file:
                loaded_data = json.load(file)

            self.validate_game_data(loaded_data)
            self.set_game_folder(folder)

            self.data = loaded_data
            self.refresh_editor()

            messagebox.showinfo(
                "Spiel geladen",
                "Das Jupardy-Spiel wurde erfolgreich geladen."
            )

        except Exception as exc:
            messagebox.showerror(
                "Fehler",
                f"Das Spiel konnte nicht geladen werden:\n\n{exc}"
            )

    # ========================================================
    # DATEN VALIDIEREN
    # ========================================================

    def validate_game_data(self, data):
        if "categories" not in data:
            raise ValueError(
                "Die Datei enthält keine Kategorien."
            )

        if len(data["categories"]) != CATEGORY_COUNT:
            raise ValueError(
                "Das Spiel muss genau fünf Kategorien enthalten."
            )

        for category_index, category in enumerate(
            data["categories"]
        ):
            category.setdefault(
                "name",
                f"Kategorie {category_index + 1}"
            )

            category.setdefault(
                "questions",
                {}
            )

            for points in POINTS:
                key = str(points)

                if key not in category["questions"]:
                    category["questions"][key] = {
                        "type": "text",
                        "question": "",
                        "answer": "",
                        "media": "",
                        "answer_media": ""
                    }

                question = category["questions"][key]

                question.setdefault("type", "text")
                question.setdefault("question", "")
                question.setdefault("answer", "")
                question.setdefault("media", "")
                question.setdefault("answer_media", "")

    # ========================================================
    # SPEICHERN
    # ========================================================

    def save_game(self, show_message=True):
        if not self.require_game_folder():
            return False

        self.save_all_category_names()

        gamefile = os.path.join(
            self.gamefile_folder,
            "game.json"
        )

        try:
            with open(
                gamefile,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    self.data,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

            if show_message:
                messagebox.showinfo(
                    "Gespeichert",
                    "Das Jupardy-Spiel wurde gespeichert.\n\n"
                    f"{gamefile}"
                )

            return True

        except Exception as exc:
            messagebox.showerror(
                "Fehler",
                f"Spiel konnte nicht gespeichert werden:\n\n{exc}"
            )

            return False

    def require_game_folder(self):
        if self.game_folder:
            return True

        messagebox.showwarning(
            "Kein Spieleordner",
            "Bitte zuerst einen Spieleordner erstellen "
            "oder einen vorhandenen Spieleordner laden."
        )

        return False

    # ========================================================
    # ORDNER ÖFFNEN
    # ========================================================

    def open_game_folder(self):
        if not self.require_game_folder():
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(self.game_folder)

            elif sys.platform == "darwin":
                subprocess.Popen(
                    ["open", self.game_folder]
                )

            else:
                subprocess.Popen(
                    ["xdg-open", self.game_folder]
                )

        except Exception as exc:
            messagebox.showerror(
                "Fehler",
                str(exc)
            )

    # ========================================================
    # MEDIEN KOPIEREN
    # ========================================================

    def copy_media_file(
        self,
        source,
        destination_folder
    ):
        os.makedirs(
            destination_folder,
            exist_ok=True
        )

        original_filename = os.path.basename(source)

        name, extension = os.path.splitext(
            original_filename
        )

        destination = os.path.join(
            destination_folder,
            original_filename
        )

        if (
            os.path.abspath(source)
            == os.path.abspath(destination)
        ):
            return original_filename

        if os.path.exists(destination):
            counter = 1

            while True:
                filename = f"{name}_{counter}{extension}"

                destination = os.path.join(
                    destination_folder,
                    filename
                )

                if not os.path.exists(destination):
                    break

                counter += 1

        shutil.copy2(
            source,
            destination
        )

        return os.path.basename(destination)

    # ========================================================
    # EDITOR AKTUALISIEREN
    # ========================================================

    def refresh_editor(self):
        for index, entry in enumerate(
            self.category_entries
        ):
            entry.delete(0, tk.END)

            entry.insert(
                0,
                self.data["categories"][index]["name"]
            )

        if self.game_folder:
            self.folder_label.config(
                text=self.game_folder,
                fg=CYAN
            )
        else:
            self.folder_label.config(
                text="Kein Spieleordner ausgewählt",
                fg=DANGER
            )

        self.update_button_status()

    def update_category_name(self, index):
        name = self.category_entries[index].get().strip()

        if not name:
            name = f"Kategorie {index + 1}"

            self.category_entries[index].delete(
                0,
                tk.END
            )

            self.category_entries[index].insert(
                0,
                name
            )

        self.data["categories"][index]["name"] = name

    def save_all_category_names(self):
        for index in range(CATEGORY_COUNT):
            self.update_category_name(index)

    # ========================================================
    # BUTTON STATUS
    # ========================================================

    def update_button_status(self):
        for category_index in range(CATEGORY_COUNT):
            for point_index, points in enumerate(POINTS):
                question = (
                    self.data["categories"]
                    [category_index]
                    ["questions"]
                    [str(points)]
                )

                configured = (
                    question.get("question")
                    or question.get("answer")
                    or question.get("media")
                    or question.get("answer_media")
                )

                button = (
                    self.question_buttons
                    [category_index]
                    [point_index]
                )

                if configured:
                    button.config(
                        text=f"{points} ✓",
                        fg=CYAN_HOVER
                    )
                else:
                    button.config(
                        text=str(points),
                        fg=CYAN
                    )

    # ========================================================
    # FRAGENEDITOR
    # ========================================================

    def open_question_editor(
        self,
        category_index,
        points
    ):
        if not self.require_game_folder():
            return

        self.save_all_category_names()

        question_data = (
            self.data["categories"]
            [category_index]
            ["questions"]
            [str(points)]
        )

        category_name = (
            self.data["categories"]
            [category_index]
            ["name"]
        )

        window = tk.Toplevel(self.root)

        window.title(
            f"Jupardy - {category_name} - {points}"
        )

        window.geometry("820x850")
        window.minsize(700, 650)
        window.configure(bg=BG)
        window.transient(self.root)
        window.grab_set()

        header = tk.Frame(window, bg=PANEL)
        header.pack(fill="x")

        tk.Label(
            header,
            text=category_name,
            bg=PANEL,
            fg=TEXT,
            font=(FONT, 18, "bold")
        ).pack(
            side="left",
            padx=25,
            pady=18
        )

        tk.Label(
            header,
            text=f"{points} PUNKTE",
            bg=PANEL,
            fg=CYAN,
            font=(FONT, 14, "bold")
        ).pack(
            side="right",
            padx=25
        )

        tk.Frame(
            window,
            bg=CYAN,
            height=2
        ).pack(fill="x")

        outer = tk.Frame(window, bg=BG)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            outer,
            bg=BG,
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            outer,
            orient="vertical",
            command=canvas.yview
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        content = tk.Frame(
            canvas,
            bg=BG
        )

        canvas_window = canvas.create_window(
            (0, 0),
            window=content,
            anchor="nw"
        )

        def update_scroll(event=None):
            canvas.configure(
                scrollregion=canvas.bbox("all")
            )

        def update_width(event):
            canvas.itemconfig(
                canvas_window,
                width=event.width
            )

        content.bind(
            "<Configure>",
            update_scroll
        )

        canvas.bind(
            "<Configure>",
            update_width
        )

        form = tk.Frame(content, bg=BG)

        form.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=25
        )

        # Fragetyp
        tk.Label(
            form,
            text="DARSTELLUNG DER FRAGE",
            bg=BG,
            fg=CYAN,
            font=(FONT, 9, "bold")
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        type_var = tk.StringVar(
            value=question_data.get(
                "type",
                "text"
            )
        )

        type_border = tk.Frame(
            form,
            bg=CYAN,
            padx=1,
            pady=1
        )

        type_border.pack(
            fill="x",
            pady=(0, 20)
        )

        type_menu = tk.OptionMenu(
            type_border,
            type_var,
            "text",
            "image",
            "audio"
        )

        type_menu.config(
            bg=PANEL_DARK,
            fg=TEXT,
            activebackground=CYAN,
            activeforeground=BG,
            highlightthickness=0,
            relief="flat",
            font=(FONT, 10)
        )

        type_menu["menu"].config(
            bg=PANEL_DARK,
            fg=TEXT,
            activebackground=CYAN,
            activeforeground=BG
        )

        type_menu.pack(fill="x")

        # Frage
        tk.Label(
            form,
            text="FRAGE / AUFGABE",
            bg=BG,
            fg=CYAN,
            font=(FONT, 9, "bold")
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        question_border, question_text = create_text_area(
            form,
            6
        )

        question_border.pack(
            fill="x",
            pady=(0, 20)
        )

        question_text.insert(
            "1.0",
            question_data.get(
                "question",
                ""
            )
        )

        # Antwort
        tk.Label(
            form,
            text="LÖSUNG / ANTWORT",
            bg=BG,
            fg=CYAN,
            font=(FONT, 9, "bold")
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        answer_border, answer_text = create_text_area(
            form,
            4
        )

        answer_border.pack(
            fill="x",
            pady=(0, 20)
        )

        answer_text.insert(
            "1.0",
            question_data.get(
                "answer",
                ""
            )
        )

        # Fragemedium
        question_media_outer, question_media_content = (
            create_section(
                form,
                "FRAGEMEDIUM · mediaq"
            )
        )

        question_media_outer.pack(
            fill="x",
            pady=(0, 20)
        )

        media_var = tk.StringVar(
            value=question_data.get(
                "media",
                ""
            )
        )

        tk.Label(
            question_media_content,
            textvariable=media_var,
            bg=PANEL_DARK,
            fg=TEXT_SECONDARY,
            anchor="w",
            padx=10,
            pady=8
        ).pack(
            fill="x",
            pady=(0, 10)
        )

        question_media_buttons = tk.Frame(
            question_media_content,
            bg=PANEL
        )

        question_media_buttons.pack(fill="x")

        def select_question_media():
            selected_type = type_var.get()

            if selected_type == "text":
                messagebox.showinfo(
                    "Textfrage",
                    "Für eine Textfrage wird kein "
                    "Fragemedium benötigt.",
                    parent=window
                )
                return

            if selected_type == "image":
                filetypes = [
                    (
                        "Bilddateien",
                        "*.png *.jpg *.jpeg *.gif *.bmp *.webp"
                    ),
                    ("Alle Dateien", "*.*")
                ]
            else:
                filetypes = [
                    (
                        "Audiodateien",
                        "*.mp3 *.wav *.ogg"
                    ),
                    ("Alle Dateien", "*.*")
                ]

            source = filedialog.askopenfilename(
                title="Fragemedium auswählen",
                filetypes=filetypes,
                parent=window
            )

            if not source:
                return

            try:
                filename = self.copy_media_file(
                    source,
                    self.mediaq_folder
                )

                media_var.set(filename)

            except Exception as exc:
                messagebox.showerror(
                    "Fehler",
                    f"Datei konnte nicht kopiert werden:\n\n{exc}",
                    parent=window
                )

        create_button(
            question_media_buttons,
            "Datei auswählen",
            select_question_media
        ).pack(side="left")

        create_button(
            question_media_buttons,
            "Verknüpfung entfernen",
            lambda: media_var.set("")
        ).pack(
            side="left",
            padx=8
        )

        # Antwortbild
        answer_media_outer, answer_media_content = (
            create_section(
                form,
                "ANTWORTBILD · mediaa"
            )
        )

        answer_media_outer.pack(
            fill="x",
            pady=(0, 20)
        )

        answer_media_var = tk.StringVar(
            value=question_data.get(
                "answer_media",
                ""
            )
        )

        tk.Label(
            answer_media_content,
            textvariable=answer_media_var,
            bg=PANEL_DARK,
            fg=TEXT_SECONDARY,
            anchor="w",
            padx=10,
            pady=8
        ).pack(
            fill="x",
            pady=(0, 10)
        )

        answer_media_buttons = tk.Frame(
            answer_media_content,
            bg=PANEL
        )

        answer_media_buttons.pack(fill="x")

        def select_answer_media():
            source = filedialog.askopenfilename(
                title="Antwortbild auswählen",
                filetypes=[
                    (
                        "Bilddateien",
                        "*.png *.jpg *.jpeg *.gif *.bmp *.webp"
                    ),
                    ("Alle Dateien", "*.*")
                ],
                parent=window
            )

            if not source:
                return

            try:
                filename = self.copy_media_file(
                    source,
                    self.mediaa_folder
                )

                answer_media_var.set(filename)

            except Exception as exc:
                messagebox.showerror(
                    "Fehler",
                    f"Datei konnte nicht kopiert werden:\n\n{exc}",
                    parent=window
                )

        create_button(
            answer_media_buttons,
            "Bild auswählen",
            select_answer_media
        ).pack(side="left")

        create_button(
            answer_media_buttons,
            "Verknüpfung entfernen",
            lambda: answer_media_var.set("")
        ).pack(
            side="left",
            padx=8
        )

        # Speichern
        def save_question():
            question_data["type"] = type_var.get()

            question_data["question"] = (
                question_text.get(
                    "1.0",
                    tk.END
                ).strip()
            )

            question_data["answer"] = (
                answer_text.get(
                    "1.0",
                    tk.END
                ).strip()
            )

            if question_data["type"] == "text":
                question_data["media"] = ""
            else:
                question_data["media"] = media_var.get()

            question_data["answer_media"] = (
                answer_media_var.get()
            )

            self.update_button_status()
            self.save_game(show_message=False)

            window.destroy()

        bottom = tk.Frame(form, bg=BG)
        bottom.pack(fill="x", pady=10)

        create_button(
            bottom,
            "Abbrechen",
            window.destroy
        ).pack(side="right")

        create_button(
            bottom,
            "FRAGE SPEICHERN",
            save_question,
            bold=True
        ).pack(
            side="right",
            padx=10
        )

    # ========================================================
    # SPIEL STARTEN
    # ========================================================

    def start_game(self):
        if not self.require_game_folder():
            return

        self.save_game(show_message=False)

        PlayerSetupWindow(
            self.root,
            self.data,
            self.game_folder
        )


# ============================================================
# SPIELER EINRICHTEN
# ============================================================

class PlayerSetupWindow:

    def __init__(
        self,
        parent,
        data,
        game_folder
    ):
        self.parent = parent
        self.data = data
        self.game_folder = game_folder

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Jupardy - Spieler einrichten"
        )

        self.window.geometry("600x650")
        self.window.minsize(500, 550)
        self.window.configure(bg=BG)
        self.window.transient(parent)
        self.window.grab_set()

        self.player_entries = []

        self.create_ui()

    def create_ui(self):
        header = tk.Frame(
            self.window,
            bg=PANEL
        )

        header.pack(fill="x")

        tk.Label(
            header,
            text="JUPARDY",
            bg=PANEL,
            fg=CYAN,
            font=(FONT, 22, "bold")
        ).pack(
            pady=(18, 0)
        )

        tk.Label(
            header,
            text="SPIELER EINRICHTEN",
            bg=PANEL,
            fg=TEXT,
            font=(FONT, 14, "bold")
        ).pack(
            pady=(3, 4)
        )

        tk.Label(
            header,
            text="Lege die Teilnehmer der Runde fest",
            bg=PANEL,
            fg=TEXT_SECONDARY,
            font=(FONT, 10)
        ).pack(
            pady=(0, 18)
        )

        tk.Frame(
            self.window,
            bg=CYAN,
            height=2
        ).pack(fill="x")

        main = tk.Frame(
            self.window,
            bg=BG
        )

        main.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=30
        )

        tk.Label(
            main,
            text="SPIELERANZAHL",
            bg=BG,
            fg=CYAN,
            font=(FONT, 9, "bold")
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        count_frame = tk.Frame(
            main,
            bg=BG
        )

        count_frame.pack(
            fill="x",
            pady=(0, 25)
        )

        self.player_count = tk.IntVar(
            value=2
        )

        for count in range(
            1,
            MAX_PLAYERS + 1
        ):
            button = tk.Radiobutton(
                count_frame,
                text=str(count),
                variable=self.player_count,
                value=count,
                command=self.refresh_player_entries,
                indicatoron=False,
                bg=PANEL_DARK,
                fg=CYAN,
                selectcolor=CYAN_DARK,
                activebackground=CYAN,
                activeforeground=BG,
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=CYAN,
                font=(FONT, 10, "bold"),
                width=3,
                pady=5,
                cursor="hand2"
            )

            button.pack(
                side="left",
                padx=3
            )

        outer, self.players_content = (
            create_section(
                main,
                "SPIELERNAMEN"
            )
        )

        outer.pack(
            fill="both",
            expand=True
        )

        self.refresh_player_entries()

        buttons = tk.Frame(
            main,
            bg=BG
        )

        buttons.pack(
            fill="x",
            pady=(25, 0)
        )

        create_button(
            buttons,
            "Abbrechen",
            self.window.destroy
        ).pack(side="right")

        create_button(
            buttons,
            "RUNDE STARTEN",
            self.start_round,
            font_size=11,
            bold=True
        ).pack(
            side="right",
            padx=10
        )

    def refresh_player_entries(self):
        old_names = [
            entry.get()
            for entry in self.player_entries
        ]

        for widget in (
            self.players_content.winfo_children()
        ):
            widget.destroy()

        self.player_entries = []

        for index in range(
            self.player_count.get()
        ):
            row = tk.Frame(
                self.players_content,
                bg=PANEL
            )

            row.pack(
                fill="x",
                pady=5
            )

            tk.Label(
                row,
                text=f"SPIELER {index + 1}",
                bg=PANEL,
                fg=TEXT_SECONDARY,
                font=(FONT, 9, "bold"),
                width=12,
                anchor="w"
            ).pack(side="left")

            border, entry = create_entry(row)

            border.pack(
                side="left",
                fill="x",
                expand=True
            )

            if index < len(old_names):
                name = old_names[index]
            else:
                name = f"Spieler {index + 1}"

            entry.insert(0, name)

            self.player_entries.append(entry)

    def start_round(self):
        players = []

        for index, entry in enumerate(
            self.player_entries
        ):
            name = entry.get().strip()

            if not name:
                name = f"Spieler {index + 1}"

            players.append(
                {
                    "name": name,
                    "score": 0
                }
            )

        self.window.destroy()

        JupardyGameWindow(
            self.parent,
            self.data,
            self.game_folder,
            players
        )


# ============================================================
# SPIELFENSTER
# ============================================================

class JupardyGameWindow:

    def __init__(
        self,
        parent,
        data,
        game_folder,
        players
    ):
        self.data = data
        self.game_folder = game_folder
        self.players = players

        self.mediaq_folder = os.path.join(
            self.game_folder,
            "mediaq"
        )

        self.mediaa_folder = os.path.join(
            self.game_folder,
            "mediaa"
        )

        self.used_questions = set()
        self.image_references = []

        self.current_category_index = None
        self.current_points = None
        self.current_question = None

        self.window = tk.Toplevel(parent)

        self.window.title("Jupardy")
        self.window.geometry("1450x900")
        self.window.minsize(1000, 700)
        self.window.configure(bg=BG)

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.close_game
        )

        self.main_container = tk.Frame(
            self.window,
            bg=BG
        )

        self.main_container.pack(
            fill="both",
            expand=True
        )

        self.create_board()

    # ========================================================
    # SCREEN LEEREN
    # ========================================================

    def clear_screen(self):
        if AUDIO_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

        for widget in (
            self.main_container.winfo_children()
        ):
            widget.destroy()

        self.image_references.clear()

    # ========================================================
    # SPIEL SCHLIESSEN
    # ========================================================

    def close_game(self):
        answer = messagebox.askyesno(
            "Jupardy beenden",
            "Möchtest du die aktuelle Runde wirklich beenden?",
            parent=self.window
        )

        if not answer:
            return

        if AUDIO_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

        self.window.destroy()

    # ========================================================
    # HEADER
    # ========================================================

    def create_header(
        self,
        title="JUPARDY",
        subtitle=None,
        show_result_button=True
    ):
        header = tk.Frame(
            self.main_container,
            bg=PANEL,
            height=75
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        left = tk.Frame(
            header,
            bg=PANEL
        )

        left.pack(
            side="left",
            fill="y",
            padx=30
        )

        tk.Label(
            left,
            text=title,
            bg=PANEL,
            fg=CYAN,
            font=(FONT, 25, "bold")
        ).pack(
            side="left",
            pady=15
        )

        if subtitle:
            tk.Label(
                left,
                text=f"   {subtitle}",
                bg=PANEL,
                fg=TEXT,
                font=(FONT, 15, "bold")
            ).pack(
                side="left",
                pady=15
            )

        right = tk.Frame(
            header,
            bg=PANEL
        )

        right.pack(
            side="right",
            padx=30
        )

        if show_result_button:
            create_button(
                right,
                "Ergebnis",
                self.show_results
            ).pack(
                side="left",
                padx=5
            )

        create_button(
            right,
            "Runde beenden",
            self.close_game,
            accent=DANGER
        ).pack(
            side="left",
            padx=5
        )

        tk.Frame(
            self.main_container,
            bg=CYAN,
            height=2
        ).pack(fill="x")

    # ========================================================
    # PUNKTESTAND
    # ========================================================

    def create_score_bar(self):
        area = tk.Frame(
            self.main_container,
            bg=BG
        )

        area.pack(
            fill="x",
            padx=30,
            pady=(18, 5)
        )

        for player in self.players:
            border = tk.Frame(
                area,
                bg=CYAN,
                padx=1,
                pady=1
            )

            border.pack(
                side="left",
                fill="both",
                expand=True,
                padx=5
            )

            card = tk.Frame(
                border,
                bg=PANEL
            )

            card.pack(
                fill="both",
                expand=True
            )

            tk.Label(
                card,
                text=player["name"].upper(),
                bg=PANEL,
                fg=TEXT_SECONDARY,
                font=(FONT, 10, "bold")
            ).pack(
                pady=(8, 2)
            )

            score = player["score"]

            if score < 0:
                color = DANGER
            elif score > 0:
                color = CYAN
            else:
                color = TEXT

            tk.Label(
                card,
                text=f"{score} Punkte",
                bg=PANEL,
                fg=color,
                font=(FONT, 16, "bold")
            ).pack(
                pady=(0, 8)
            )

    # ========================================================
    # SPIELBRETT
    # ========================================================

    def create_board(self):
        self.clear_screen()

        self.current_category_index = None
        self.current_points = None
        self.current_question = None

        self.create_header()
        self.create_score_bar()

        board = tk.Frame(
            self.main_container,
            bg=BG
        )

        board.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=20
        )

        for column, category in enumerate(
            self.data["categories"]
        ):
            border = tk.Frame(
                board,
                bg=CYAN,
                padx=1,
                pady=1
            )

            border.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=5,
                pady=5
            )

            tk.Label(
                border,
                text=category["name"].upper(),
                bg=PANEL,
                fg=TEXT,
                font=(FONT, 15, "bold"),
                wraplength=200
            ).pack(
                fill="both",
                expand=True
            )

        for column in range(CATEGORY_COUNT):
            for row, points in enumerate(
                POINTS,
                start=1
            ):
                key = (
                    column,
                    points
                )

                border = tk.Frame(
                    board,
                    bg=CYAN,
                    padx=1,
                    pady=1
                )

                border.grid(
                    row=row,
                    column=column,
                    sticky="nsew",
                    padx=5,
                    pady=5
                )

                button = tk.Button(
                    border,
                    text=str(points),
                    bg=PANEL_DARK,
                    fg=CYAN,
                    activebackground=CYAN,
                    activeforeground=BG,
                    relief="flat",
                    bd=0,
                    cursor="hand2",
                    font=(FONT, 26, "bold"),
                    command=lambda c=column, p=points:
                    self.show_question(c, p)
                )

                button.pack(
                    fill="both",
                    expand=True
                )

                if key in self.used_questions:
                    button.config(
                        text="",
                        state="disabled",
                        bg=BG,
                        cursor="arrow"
                    )

                    border.config(
                        bg=PANEL
                    )

        for column in range(CATEGORY_COUNT):
            board.columnconfigure(
                column,
                weight=1
            )

        for row in range(6):
            board.rowconfigure(
                row,
                weight=1
            )

        footer = tk.Frame(
            self.main_container,
            bg=PANEL_DARK,
            height=30
        )

        footer.pack(fill="x")
        footer.pack_propagate(False)

        remaining = (
            CATEGORY_COUNT
            * len(POINTS)
            - len(self.used_questions)
        )

        tk.Label(
            footer,
            text="By Jucno",
            bg=PANEL_DARK,
            fg=TEXT_SECONDARY,
            font=(FONT, 8)
        ).pack(
            side="left",
            padx=20
        )

        tk.Label(
            footer,
            text=f"Noch {remaining} Fragen",
            bg=PANEL_DARK,
            fg=TEXT_SECONDARY,
            font=(FONT, 8)
        ).pack(
            side="right",
            padx=20
        )

    # ========================================================
    # FRAGE
    # ========================================================

    def show_question(
        self,
        category_index,
        points
    ):
        self.current_category_index = category_index
        self.current_points = points

        self.current_question = (
            self.data["categories"]
            [category_index]
            ["questions"]
            [str(points)]
        )

        question = self.current_question

        category_name = (
            self.data["categories"]
            [category_index]
            ["name"]
        )

        self.clear_screen()

        self.create_header(
            category_name.upper(),
            f"{points} PUNKTE",
            False
        )

        self.create_score_bar()

        body = tk.Frame(
            self.main_container,
            bg=BG
        )

        body.pack(
            fill="both",
            expand=True,
            padx=50,
            pady=20
        )

        question_text = question.get(
            "question",
            ""
        )

        if question_text:
            tk.Label(
                body,
                text=question_text,
                bg=BG,
                fg=TEXT,
                font=(FONT, 26, "bold"),
                wraplength=1200,
                justify="center"
            ).pack(
                fill="x",
                pady=(10, 15)
            )

        question_type = question.get(
            "type",
            "text"
        )

        media = question.get(
            "media",
            ""
        )

        # Eigener Bereich nur für das Medium
        media_area = tk.Frame(
            body,
            bg=BG
        )

        media_area.pack(
            fill="both",
            expand=True,
            pady=5
        )

        if (
            question_type == "image"
            and media
        ):
            self.show_image(
                media_area,
                os.path.join(
                    self.mediaq_folder,
                    media
                ),
                1100,
                480
            )

        elif (
            question_type == "audio"
            and media
        ):
            self.show_audio(
                media_area,
                os.path.join(
                    self.mediaq_folder,
                    media
                )
            )

        actions = tk.Frame(
            body,
            bg=BG
        )

        actions.pack(
            fill="x",
            side="bottom",
            pady=10
        )

        create_button(
            actions,
            "ZURÜCK",
            self.create_board,
            accent=TEXT_SECONDARY
        ).pack(side="left")

        create_button(
            actions,
            "ANTWORT ANZEIGEN",
            self.show_answer,
            font_size=13,
            bold=True
        ).pack(side="right")

    # ========================================================
    # ANTWORT
    # ========================================================

    def show_answer(self):
        if not self.current_question:
            return

        question = self.current_question
        points = self.current_points
        category_index = self.current_category_index

        category_name = (
            self.data["categories"]
            [category_index]
            ["name"]
        )

        self.clear_screen()

        self.create_header(
            "ANTWORT",
            f"{category_name.upper()} · {points} PUNKTE",
            False
        )

        self.create_score_bar()

        body = tk.Frame(
            self.main_container,
            bg=BG
        )

        body.pack(
            fill="both",
            expand=True,
            padx=50,
            pady=15
        )

        answer = question.get(
            "answer",
            ""
        )

        if answer:
            tk.Label(
                body,
                text=answer,
                bg=BG,
                fg=TEXT,
                font=(FONT, 24, "bold"),
                wraplength=1200,
                justify="center"
            ).pack(
                fill="x",
                pady=(5, 10)
            )

        answer_media = question.get(
            "answer_media",
            ""
        )

        if answer_media:
            image_area = tk.Frame(
                body,
                bg=BG
            )

            image_area.pack(
                fill="both",
                expand=True,
                pady=5
            )

            self.show_image(
                image_area,
                os.path.join(
                    self.mediaa_folder,
                    answer_media
                ),
                900,
                300
            )

        # Punktevergabe
        score_changes = {
            index: 0
            for index in range(
                len(self.players)
            )
        }

        scoring_outer, scoring = (
            create_section(
                body,
                "PUNKTE VERGEBEN"
            )
        )

        scoring_outer.pack(
            fill="x",
            pady=10
        )

        player_rows = []

        def refresh():
            for index, widgets in enumerate(
                player_rows
            ):
                change = score_changes[index]

                new_score = (
                    self.players[index]["score"]
                    + change
                )

                widgets["change"].config(
                    text=f"Änderung: {change:+d}"
                )

                widgets["score"].config(
                    text=f"{new_score} Punkte"
                )

        def add(index):
            score_changes[index] += points
            refresh()

        def subtract(index):
            score_changes[index] -= points
            refresh()

        def reset(index):
            score_changes[index] = 0
            refresh()

        for index, player in enumerate(
            self.players
        ):
            row = tk.Frame(
                scoring,
                bg=PANEL_DARK
            )

            row.pack(
                fill="x",
                pady=4
            )

            info = tk.Frame(
                row,
                bg=PANEL_DARK
            )

            info.pack(
                side="left",
                fill="x",
                expand=True,
                padx=15,
                pady=8
            )

            tk.Label(
                info,
                text=player["name"],
                bg=PANEL_DARK,
                fg=TEXT,
                font=(FONT, 11, "bold")
            ).pack(anchor="w")

            score_label = tk.Label(
                info,
                text=f"{player['score']} Punkte",
                bg=PANEL_DARK,
                fg=CYAN,
                font=(FONT, 10)
            )

            score_label.pack(anchor="w")

            change_label = tk.Label(
                info,
                text="Änderung: +0",
                bg=PANEL_DARK,
                fg=TEXT_SECONDARY,
                font=(FONT, 9)
            )

            change_label.pack(anchor="w")

            buttons = tk.Frame(
                row,
                bg=PANEL_DARK
            )

            buttons.pack(
                side="right",
                padx=15
            )

            create_button(
                buttons,
                f"+{points}",
                lambda i=index: add(i),
                accent=SUCCESS,
                bold=True
            ).pack(
                side="left",
                padx=3
            )

            create_button(
                buttons,
                f"-{points}",
                lambda i=index: subtract(i),
                accent=DANGER,
                bold=True
            ).pack(
                side="left",
                padx=3
            )

            create_button(
                buttons,
                "0",
                lambda i=index: reset(i),
                accent=TEXT_SECONDARY
            ).pack(
                side="left",
                padx=3
            )

            player_rows.append(
                {
                    "score": score_label,
                    "change": change_label
                }
            )

        def finish():
            for index, change in score_changes.items():
                self.players[index]["score"] += change

            self.used_questions.add(
                (
                    category_index,
                    points
                )
            )

            self.create_board()

        def no_points():
            for index in score_changes:
                score_changes[index] = 0

            refresh()

        bottom = tk.Frame(
            body,
            bg=BG
        )

        bottom.pack(
            fill="x",
            pady=10
        )

        create_button(
            bottom,
            "KEINE PUNKTE",
            no_points,
            accent=TEXT_SECONDARY
        ).pack(side="left")

        create_button(
            bottom,
            "WERTUNG ÜBERNEHMEN & ZURÜCK",
            finish,
            font_size=12,
            bold=True
        ).pack(side="right")

    # ========================================================
    # BILDDARSTELLUNG
    #
    # Kleine Bilder werden hier ausdrücklich HOCHSKALIERT.
    # Große Bilder werden entsprechend verkleinert.
    #
    # KEIN thumbnail(), da thumbnail() kleine Bilder nicht
    # hochskaliert.
    # ========================================================

    def show_image(
        self,
        parent,
        path,
        max_width,
        max_height
    ):
        if not os.path.isfile(path):
            tk.Label(
                parent,
                text=f"Bild nicht gefunden:\n{path}",
                bg=BG,
                fg=DANGER,
                font=(FONT, 10)
            ).pack(pady=10)

            return

        try:
            # Bild vollständig laden
            with Image.open(path) as source_image:
                source_image.load()

                # RGB/RGBA-Kopie erzeugen, damit die Datei
                # danach problemlos geschlossen werden kann.
                if source_image.mode in ("RGBA", "LA"):
                    image = source_image.convert("RGBA")
                else:
                    image = source_image.convert("RGB")

            original_width, original_height = image.size

            if original_width <= 0 or original_height <= 0:
                raise ValueError(
                    "Das Bild besitzt eine ungültige Größe."
                )

            # -----------------------------------------------
            # Skalierungsfaktor
            #
            # WICHTIG:
            # Der Faktor wird NICHT auf maximal 1 begrenzt.
            #
            # Deshalb:
            #
            # scale_factor > 1  -> Bild wird vergrößert
            # scale_factor < 1  -> Bild wird verkleinert
            # -----------------------------------------------

            width_scale = (
                float(max_width)
                / float(original_width)
            )

            height_scale = (
                float(max_height)
                / float(original_height)
            )

            scale_factor = min(
                width_scale,
                height_scale
            )

            new_width = max(
                1,
                int(
                    round(
                        original_width
                        * scale_factor
                    )
                )
            )

            new_height = max(
                1,
                int(
                    round(
                        original_height
                        * scale_factor
                    )
                )
            )

            # Pillow-Kompatibilität
            try:
                resampling = Image.Resampling.LANCZOS
            except AttributeError:
                resampling = Image.LANCZOS

            # -----------------------------------------------
            # IMMER RESIZE
            #
            # Auch wenn das Original kleiner ist.
            # Genau dadurch findet das Hochskalieren statt.
            # -----------------------------------------------

            image = image.resize(
                (
                    new_width,
                    new_height
                ),
                resampling
            )

            photo = ImageTk.PhotoImage(image)

            # Referenz behalten, sonst kann Tkinter das
            # Bild aus dem Speicher verlieren.
            self.image_references.append(photo)

            # -----------------------------------------------
            # MEDIENBEREICH
            # -----------------------------------------------

            image_container = tk.Frame(
                parent,
                bg=BG,
                width=max_width + 10,
                height=max_height + 10
            )

            image_container.pack(
                fill="both",
                expand=True,
                pady=5
            )

            # Verhindert, dass sich der Container nur nach
            # der ursprünglichen Bildgröße richtet.
            image_container.pack_propagate(False)

            # Cyan-Rahmen
            border = tk.Frame(
                image_container,
                bg=CYAN,
                padx=2,
                pady=2
            )

            # Mittig im Medienbereich positionieren
            border.place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

            label = tk.Label(
                border,
                image=photo,
                bg=PANEL_DARK,
                bd=0,
                highlightthickness=0
            )

            label.image = photo
            label.pack()

        except Exception as exc:
            tk.Label(
                parent,
                text=f"Bildfehler:\n{exc}",
                bg=BG,
                fg=DANGER,
                font=(FONT, 10)
            ).pack(pady=10)

    # ========================================================
    # AUDIO
    # ========================================================

    def show_audio(
        self,
        parent,
        path
    ):
        if not AUDIO_AVAILABLE:
            tk.Label(
                parent,
                text="Audio ist auf diesem System nicht verfügbar.",
                bg=BG,
                fg=DANGER
            ).pack(pady=15)

            return

        if not os.path.isfile(path):
            tk.Label(
                parent,
                text=(
                    "Audiodatei nicht gefunden:\n"
                    f"{path}"
                ),
                bg=BG,
                fg=DANGER
            ).pack(pady=15)

            return

        outer, content = create_section(
            parent,
            "AUDIO"
        )

        outer.pack(pady=20)

        def play():
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()

            except Exception as exc:
                messagebox.showerror(
                    "Audiofehler",
                    str(exc),
                    parent=self.window
                )

        def stop():
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

        create_button(
            content,
            "ABSPIELEN",
            play,
            bold=True
        ).pack(
            side="left",
            padx=5
        )

        create_button(
            content,
            "STOP",
            stop
        ).pack(
            side="left",
            padx=5
        )

    # ========================================================
    # ERGEBNIS
    # ========================================================

    def show_results(self):
        self.clear_screen()

        self.create_header(
            "JUPARDY",
            "ERGEBNIS",
            False
        )

        content = tk.Frame(
            self.main_container,
            bg=BG
        )

        content.pack(
            fill="both",
            expand=True,
            padx=100,
            pady=50
        )

        tk.Label(
            content,
            text="AKTUELLER PUNKTESTAND",
            bg=BG,
            fg=TEXT_SECONDARY,
            font=(FONT, 11, "bold")
        ).pack(
            pady=(0, 25)
        )

        sorted_players = sorted(
            self.players,
            key=lambda player:
            player["score"],
            reverse=True
        )

        for index, player in enumerate(
            sorted_players,
            start=1
        ):
            border = tk.Frame(
                content,
                bg=(
                    CYAN
                    if index == 1
                    else PANEL_LIGHT
                ),
                padx=1,
                pady=1
            )

            border.pack(
                fill="x",
                pady=6
            )

            row = tk.Frame(
                border,
                bg=PANEL
            )

            row.pack(fill="x")

            tk.Label(
                row,
                text=f"#{index}",
                bg=PANEL,
                fg=(
                    CYAN
                    if index == 1
                    else TEXT_SECONDARY
                ),
                font=(FONT, 18, "bold"),
                width=5
            ).pack(
                side="left",
                padx=15,
                pady=15
            )

            tk.Label(
                row,
                text=player["name"],
                bg=PANEL,
                fg=TEXT,
                font=(FONT, 16, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=f"{player['score']} Punkte",
                bg=PANEL,
                fg=CYAN,
                font=(FONT, 16, "bold")
            ).pack(
                side="right",
                padx=25
            )

        create_button(
            content,
            "ZURÜCK ZUM SPIELFELD",
            self.create_board,
            font_size=12,
            bold=True
        ).pack(pady=35)

        tk.Label(
            content,
            text="By Jucno",
            bg=BG,
            fg=TEXT_SECONDARY,
            font=(FONT, 9)
        ).pack()


# ============================================================
# PROGRAMMSTART
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()

    root.configure(bg=BG)

    app = JupardyApp(root)

    root.mainloop()