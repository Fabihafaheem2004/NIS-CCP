
#!/usr/bin/env python3
"""CIPHERLAB — Classical Cryptography Studio.
Requires customtkinter and cipher.py in the same directory.
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
import queue
import random
import string
import time
import re
import statistics

from cipher import (
    clean_plaintext,
    encrypt,
    decrypt,
    parse_ciphertext,
    known_plaintext_attack,
    random_key,
    shift_encrypt,
)

# ============================================================
# DESIGN SYSTEM
# ============================================================

ctk.set_appearance_mode("light")

BG = "#F6F5F8"
WHITE = "#FFFFFF"
INK = "#252337"
MUTED = "#858294"
PURPLE = "#7966B3"
PURPLE_DARK = "#65519F"
LAVENDER = "#EEEAF7"
BORDER = "#E8E5ED"
GREEN = "#38836D"
RED = "#B65D6B"
PALE_GREEN = "#EAF4EF"
PALE_RED = "#F8ECEE"

FONT = "Segoe UI"
MONO = "Consolas"


class CipherLab(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("CIPHERLAB")
        self.geometry("1200x780")
        self.minsize(960, 650)
        self.configure(fg_color=BG)

        self.current_page = None
        self.benchmark_running = False
        self.benchmark_queue = queue.Queue()
        self.benchmark_data = None

        self.create_menu()
        self.create_shell()
        self.show_splash()

    # ========================================================
    # APPLICATION MENU
    # ========================================================

    def create_menu(self):

        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="Home",
            accelerator="Ctrl+H",
            command=lambda: self.navigate("Home")
        )
        file_menu.add_command(
            label="Clear Workspace",
            accelerator="Ctrl+L",
            command=self.clear_workspace
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)

        menubar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)

        for name in (
            "Encryption",
            "Decryption",
            "Cryptanalysis",
            "Benchmark Lab",
        ):
            tools_menu.add_command(
                label=name,
                command=lambda n=name: self.navigate(n)
            )

        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label="Documentation",
            command=lambda: self.navigate("Documentation")
        )
        help_menu.add_command(label="About", command=self.about)

        menubar.add_cascade(label="Help", menu=help_menu)

        self.configure(menu=menubar)

        self.bind_all(
            "<Control-h>",
            lambda event: self.navigate("Home")
        )

        self.bind_all(
            "<Control-l>",
            lambda event: self.clear_workspace()
        )

    # ========================================================
    # MAIN APPLICATION SHELL
    # ========================================================

    def create_shell(self):

        self.shell = ctk.CTkFrame(
            self,
            fg_color=BG,
            corner_radius=0
        )
        self.shell.pack(fill="both", expand=True)

        # Sidebar

        self.sidebar = ctk.CTkFrame(
            self.shell,
            width=215,
            fg_color=WHITE,
            corner_radius=0
        )

        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.create_brand()

        self.create_navigation()

        # Main application area

        self.content_area = ctk.CTkFrame(
            self.shell,
            fg_color=BG,
            corner_radius=0
        )

        self.content_area.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Top application bar

        self.topbar = ctk.CTkFrame(
            self.content_area,
            height=62,
            fg_color=WHITE,
            corner_radius=0
        )

        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)

        self.breadcrumb = ctk.CTkLabel(
            self.topbar,
            text="CIPHERLAB  /  HOME",
            font=(FONT, 10, "bold"),
            text_color=MUTED
        )

        self.breadcrumb.pack(
            side="left",
            padx=28
        )

        ctk.CTkLabel(
            self.topbar,
            text="VIGENÈRE  +  HILL",
            font=(FONT, 9, "bold"),
            text_color=PURPLE
        ).pack(side="right", padx=28)

        # Page container

        self.page_container = ctk.CTkFrame(
            self.content_area,
            fg_color=BG,
            corner_radius=0
        )

        self.page_container.pack(
            fill="both",
            expand=True
        )

    def create_brand(self):

        brand = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        brand.pack(
            fill="x",
            padx=20,
            pady=(25, 35)
        )

        logo = ctk.CTkFrame(
            brand,
            width=39,
            height=39,
            corner_radius=11,
            fg_color=PURPLE
        )

        logo.pack(side="left")
        logo.pack_propagate(False)

        ctk.CTkLabel(
            logo,
            text="C",
            text_color=WHITE,
            font=(FONT, 23, "bold")
        ).place(relx=.5, rely=.46, anchor="center")

        details = ctk.CTkFrame(
            brand,
            fg_color="transparent"
        )

        details.pack(side="left", padx=10)

        ctk.CTkLabel(
            details,
            text="CIPHERLAB",
            font=(FONT, 14, "bold"),
            text_color=INK
        ).pack(anchor="w")

        ctk.CTkLabel(
            details,
            text="CRYPTOGRAPHY STUDIO",
            font=(FONT, 8, "bold"),
            text_color=MUTED
        ).pack(anchor="w", pady=(2, 0))

    def create_navigation(self):

        ctk.CTkLabel(
            self.sidebar,
            text="APPLICATION",
            font=(FONT, 9, "bold"),
            text_color=MUTED
        ).pack(anchor="w", padx=22, pady=(0, 9))

        self.nav_buttons = {}

        pages = [
            ("Home", "Overview"),
            ("Encryption", "Encryption"),
            ("Decryption", "Decryption"),
            ("Cryptanalysis", "Known-plaintext attack"),
            ("Benchmark Lab", "Benchmark Lab"),
        ]

        for page, label in pages:
            self.add_nav_button(page, label)

        ctk.CTkLabel(
            self.sidebar,
            text="RESOURCES",
            font=(FONT, 9, "bold"),
            text_color=MUTED
        ).pack(anchor="w", padx=22, pady=(28, 9))

        self.add_nav_button("Documentation", "Documentation")

        footer = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        footer.pack(
            side="bottom",
            fill="x",
            padx=18,
            pady=19
        )

        ctk.CTkFrame(
            footer,
            height=1,
            fg_color=BORDER
        ).pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            footer,
            text="EDUCATIONAL EDITION",
            font=(FONT, 9, "bold"),
            text_color=MUTED
        ).pack(anchor="w")

        ctk.CTkLabel(
            footer,
            text="Not secure encryption",
            font=(FONT, 9),
            text_color=MUTED
        ).pack(anchor="w", pady=(4, 0))

    def add_nav_button(self, page, label):

        button = ctk.CTkButton(
            self.sidebar,
            text=label,
            anchor="w",
            height=39,
            corner_radius=7,
            fg_color="transparent",
            hover_color=LAVENDER,
            text_color=MUTED,
            font=(FONT, 11),
            command=lambda: self.navigate(page)
        )

        button.pack(
            fill="x",
            padx=12,
            pady=2
        )

        self.nav_buttons[page] = button

    # ========================================================
    # SPLASH SCREEN
    # ========================================================

    def show_splash(self):

        self.splash = ctk.CTkFrame(
            self,
            fg_color=BG,
            corner_radius=0
        )

        self.splash.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1
        )

        center = ctk.CTkFrame(
            self.splash,
            fg_color="transparent"
        )

        center.place(
            relx=.5,
            rely=.46,
            anchor="center"
        )

        logo = ctk.CTkFrame(
            center,
            width=76,
            height=76,
            corner_radius=21,
            fg_color=PURPLE
        )

        logo.pack()
        logo.pack_propagate(False)

        ctk.CTkLabel(
            logo,
            text="C",
            font=(FONT, 43, "bold"),
            text_color=WHITE
        ).place(relx=.5, rely=.46, anchor="center")

        ctk.CTkLabel(
            center,
            text="CIPHERLAB",
            font=(FONT, 29, "bold"),
            text_color=INK
        ).pack(pady=(18, 3))

        ctk.CTkLabel(
            center,
            text="CLASSICAL CRYPTOGRAPHY STUDIO",
            font=(FONT, 9, "bold"),
            text_color=MUTED
        ).pack()

        ctk.CTkLabel(
            center,
            text="Vigenère  /  Hill  /  Cryptanalysis",
            font=(FONT, 10),
            text_color=MUTED
        ).pack(pady=(14, 0))

        self.after(1000, self.finish_splash)

    def finish_splash(self):

        if self.splash.winfo_exists():
            self.splash.destroy()

        self.navigate("Home")

    # ========================================================
    # NAVIGATION
    # ========================================================

    def navigate(self, page):

        self.current_page = page

        for name, button in self.nav_buttons.items():

            active = name == page

            button.configure(
                fg_color=LAVENDER if active else "transparent",
                text_color=PURPLE_DARK if active else MUTED,
                font=(FONT, 11, "bold" if active else "normal")
            )

        self.breadcrumb.configure(
            text=f"CIPHERLAB  /  {page.upper()}"
        )

        for widget in self.page_container.winfo_children():
            widget.destroy()

        # Every workspace scrolls independently.
        self.workspace = ctk.CTkScrollableFrame(
            self.page_container,
            fg_color=BG,
            corner_radius=0,
            scrollbar_button_color="#D6D1E2",
            scrollbar_button_hover_color=PURPLE
        )

        self.workspace.pack(
            fill="both",
            expand=True
        )

        pages = {
            "Home": self.page_home,
            "Encryption": self.page_encrypt,
            "Decryption": self.page_decrypt,
            "Cryptanalysis": self.page_attack,
            "Benchmark Lab": self.page_benchmark,
            "Documentation": self.page_docs
        }

        pages[page](self.workspace)

    # ========================================================
    # REUSABLE COMPONENTS
    # ========================================================

    def heading(self, parent, title, subtitle):

        ctk.CTkLabel(
            parent,
            text=title,
            font=(FONT, 25, "bold"),
            text_color=INK
        ).pack(anchor="w", padx=30, pady=(27, 3))

        ctk.CTkLabel(
            parent,
            text=subtitle,
            font=(FONT, 11),
            text_color=MUTED
        ).pack(anchor="w", padx=30, pady=(0, 20))

    def panel(self, parent, title, subtitle=None):

        frame = ctk.CTkFrame(
            parent,
            fg_color=WHITE,
            corner_radius=9,
            border_width=1,
            border_color=BORDER
        )

        if title:

            header = ctk.CTkFrame(
                frame,
                fg_color="transparent"
            )

            header.pack(
                fill="x",
                padx=18,
                pady=(15, 10)
            )

            ctk.CTkLabel(
                header,
                text=title,
                font=(FONT, 12, "bold"),
                text_color=INK
            ).pack(anchor="w")

            if subtitle:
                ctk.CTkLabel(
                    header,
                    text=subtitle,
                    font=(FONT, 9),
                    text_color=MUTED
                ).pack(anchor="w", pady=(3, 0))

        return frame

    def field_label(self, parent, text):

        ctk.CTkLabel(
            parent,
            text=text.upper(),
            font=(FONT, 9, "bold"),
            text_color=MUTED
        ).pack(anchor="w", pady=(10, 6))

    def entry(self, parent, placeholder=""):

        return ctk.CTkEntry(
            parent,
            height=38,
            corner_radius=6,
            border_color=BORDER,
            fg_color="#FCFBFD",
            text_color=INK,
            placeholder_text=placeholder,
            font=(FONT, 11)
        )

    def textbox(self, parent, height=150, placeholder=""):

        return ctk.CTkTextbox(
            parent,
            height=height,
            corner_radius=6,
            border_width=1,
            border_color=BORDER,
            fg_color="#FCFBFD",
            text_color=INK,
            font=(MONO, 11),
            wrap="word",
            scrollbar_button_color="#D6D1E2",
            scrollbar_button_hover_color=PURPLE
        )

    def button(self, parent, text, command, primary=True, width=130):

        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=36,
            corner_radius=6,
            fg_color=PURPLE if primary else "#F0EEF4",
            hover_color=PURPLE_DARK if primary else "#E5E1ED",
            text_color=WHITE if primary else INK,
            font=(FONT, 10, "bold" if primary else "normal")
        )

    def set_output(self, widget, text):

        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", str(text))
        widget.configure(state="disabled")

    def get_text(self, widget):

        return widget.get("1.0", "end-1c").strip()

    def copy_text(self, widget):

        value = self.get_text(widget)

        if not value:
            return

        self.clipboard_clear()
        self.clipboard_append(value)
        self.update()

    def clear_workspace(self):

        if self.current_page:
            self.navigate(self.current_page)

    def validate_key(self, key):

        if not re.fullmatch(r"[A-Z]{10}", key):
            raise ValueError(
                "The key must contain exactly 10 uppercase letters A-Z."
            )

    # ========================================================
    # HOME
    # ========================================================

    def page_home(self, parent):

        self.heading(
            parent,
            "Overview",
            "Your classical cryptography workspace."
        )

        intro = ctk.CTkFrame(
            parent,
            fg_color=LAVENDER,
            corner_radius=9
        )

        intro.pack(
            fill="x",
            padx=30,
            pady=(0, 20)
        )

        ctk.CTkLabel(
            intro,
            text="Vigenère + 2×2 Hill Cipher",
            font=(FONT, 18, "bold"),
            text_color=PURPLE_DARK
        ).pack(anchor="w", padx=20, pady=(17, 4))

        ctk.CTkLabel(
            intro,
            text="Explore encryption, decryption and a known-plaintext attack "
                 "through an interactive cryptography studio.",
            font=(FONT, 10),
            text_color="#655D79"
        ).pack(anchor="w", padx=20, pady=(0, 17))

        ctk.CTkLabel(
            parent,
            text="WORKSPACES",
            font=(FONT, 9, "bold"),
            text_color=MUTED
        ).pack(anchor="w", padx=30, pady=(0, 8))

        items = [
            ("01", "Encryption", "Transform plaintext into ciphertext."),
            ("02", "Decryption", "Recover plaintext using the secret key."),
            ("03", "Cryptanalysis", "Explore the known-prefix attack."),
            ("04", "Benchmark Lab", "Compare performance across experiments.")
        ]

        for number, title, description in items:

            row = ctk.CTkFrame(
                parent,
                fg_color=WHITE,
                corner_radius=8,
                border_width=1,
                border_color=BORDER
            )

            row.pack(
                fill="x",
                padx=30,
                pady=4
            )

            ctk.CTkLabel(
                row,
                text=number,
                font=(MONO, 11, "bold"),
                text_color=PURPLE,
                width=43
            ).pack(side="left", padx=(14, 0), pady=14)

            details = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )

            details.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                details,
                text=title,
                font=(FONT, 11, "bold"),
                text_color=INK
            ).pack(anchor="w")

            ctk.CTkLabel(
                details,
                text=description,
                font=(FONT, 9),
                text_color=MUTED
            ).pack(anchor="w", pady=(2, 0))

            self.button(
                row,
                "Open",
                lambda p=title: self.navigate(
                    "Benchmark Lab" if p == "Benchmark Lab" else
                    "Cryptanalysis" if p == "Cryptanalysis" else p
                ),
                False,
                70
            ).pack(side="right", padx=14)

        warning = self.panel(parent, "Important")

        warning.pack(
            fill="x",
            padx=30,
            pady=(17, 20)
        )

        ctk.CTkLabel(
            warning,
            text="This implementation is intended for educational use. "
                 "It is not suitable for protecting real-world information.",
            font=(FONT, 10),
            text_color=MUTED
        ).pack(anchor="w", padx=18, pady=(0, 15))

    # ========================================================
    # ENCRYPTION
    # ========================================================

    def page_encrypt(self, parent):

        self.heading(
            parent,
            "Encryption",
            "Convert a plaintext message into marked ciphertext."
        )

        panel = self.panel(
            parent,
            "Encryption settings",
            "Six Vigenère characters followed by four Hill matrix characters."
        )

        panel.pack(fill="x", padx=30, pady=(0, 14))

        body = ctk.CTkFrame(
            panel,
            fg_color="transparent"
        )

        body.pack(fill="x", padx=18, pady=(0, 17))

        self.enc_key = self.entry(body, "Example: CRYPTOHILL")

        self.field_label(body, "Secret key")
        self.enc_key.pack(fill="x")

        self.field_label(body, "Plaintext")

        self.enc_input = self.textbox(
            body,
            150,
            "Enter your message..."
        )

        self.enc_input.pack(fill="x")

        actions = ctk.CTkFrame(
            body,
            fg_color="transparent"
        )

        actions.pack(fill="x", pady=(12, 0))

        self.button(
            actions,
            "Encrypt message",
            self.do_encrypt
        ).pack(side="left")

        self.button(
            actions,
            "Clear",
            lambda: self.clear_textboxes(
                self.enc_input,
                self.enc_output
            ),
            False,
            75
        ).pack(side="left", padx=8)

        result = self.panel(
            parent,
            "Ciphertext",
            "The complete output includes its leading parity marker."
        )

        result.pack(fill="x", padx=30)

        self.enc_output = self.textbox(result, 110)
        self.enc_output.pack(fill="x", padx=18, pady=(0, 10))
        self.enc_output.configure(state="disabled")

        self.button(
            result,
            "Copy ciphertext",
            lambda: self.copy_text(self.enc_output),
            False,
            115
        ).pack(anchor="e", padx=18, pady=(0, 15))

    def do_encrypt(self):

        key = self.enc_key.get().strip()

        try:

            self.validate_key(key)

            raw = self.get_text(self.enc_input)

            cleaned = clean_plaintext(raw)

            if not cleaned:
                raise ValueError("Enter at least one English letter.")

            result = encrypt(raw, key)

            self.set_output(self.enc_output, result)

        except ValueError as exc:

            messagebox.showerror(
                "Encryption error",
                str(exc),
                parent=self
            )

    # ========================================================
    # DECRYPTION
    # ========================================================

    def page_decrypt(self, parent):

        self.heading(
            parent,
            "Decryption",
            "Recover the cleaned plaintext from marked ciphertext."
        )

        panel = self.panel(parent, "Decryption settings")

        panel.pack(fill="x", padx=30, pady=(0, 14))

        body = ctk.CTkFrame(
            panel,
            fg_color="transparent"
        )

        body.pack(fill="x", padx=18, pady=(0, 17))

        self.dec_key = self.entry(body, "10 uppercase letters")

        self.field_label(body, "Secret key")
        self.dec_key.pack(fill="x")

        self.field_label(body, "Marked ciphertext")

        self.dec_input = self.textbox(
            body,
            135,
            "Paste ciphertext beginning with A or B..."
        )

        self.dec_input.pack(fill="x")

        self.button(
            body,
            "Decrypt message",
            self.do_decrypt
        ).pack(anchor="w", pady=(12, 0))

        result = self.panel(parent, "Recovered plaintext")

        result.pack(fill="x", padx=30)

        self.dec_output = self.textbox(result, 130)
        self.dec_output.pack(fill="x", padx=18, pady=(0, 10))
        self.dec_output.configure(state="disabled")

        self.button(
            result,
            "Copy plaintext",
            lambda: self.copy_text(self.dec_output),
            False,
            110
        ).pack(anchor="e", padx=18, pady=(0, 15))

    def do_decrypt(self):

        try:

            key = self.dec_key.get().strip()
            self.validate_key(key)

            ciphertext = self.get_text(self.dec_input)

            parse_ciphertext(ciphertext)

            result = decrypt(ciphertext, key)

            self.set_output(self.dec_output, result)

        except ValueError as exc:

            messagebox.showerror(
                "Decryption error",
                str(exc),
                parent=self
            )

    # ========================================================
    # KNOWN PLAINTEXT ATTACK
    # ========================================================

    def page_attack(self, parent):

        self.heading(
            parent,
            "Cryptanalysis",
            "Recover a candidate plaintext using a known prefix."
        )

        panel = self.panel(
            parent,
            "Attack configuration",
            "The secret key is not required."
        )

        panel.pack(fill="x", padx=30, pady=(0, 14))

        body = ctk.CTkFrame(
            panel,
            fg_color="transparent"
        )

        body.pack(fill="x", padx=18, pady=(0, 17))

        self.attack_ct = self.textbox(
            body,
            115,
            "Full marked ciphertext..."
        )

        self.field_label(body, "Complete ciphertext")
        self.attack_ct.pack(fill="x")

        self.attack_prefix = self.entry(
            body,
            "Enter the known beginning of the message"
        )

        self.field_label(body, "Known plaintext prefix")
        self.attack_prefix.pack(fill="x")

        self.button(
            body,
            "Run known-prefix attack",
            self.do_attack
        ).pack(anchor="w", pady=(12, 0))

        result = self.panel(
            parent,
            "Attack results",
            "Recovered candidate and key information."
        )

        result.pack(fill="x", padx=30)

        self.attack_output = self.textbox(result, 220)
        self.attack_output.pack(fill="x", padx=18, pady=(0, 16))
        self.attack_output.configure(state="disabled")

    def do_attack(self):

        try:

            ciphertext = self.get_text(self.attack_ct)
            prefix = self.attack_prefix.get().strip()

            parse_ciphertext(ciphertext)

            if not clean_plaintext(prefix):
                raise ValueError("Enter a known plaintext prefix.")

            result = known_plaintext_attack(
                prefix,
                ciphertext
            )

            if result["success"]:

                matrix = result["hill_matrix"]

                report = (
                    "ATTACK SUCCESSFUL\n\n"
                    f"Recovered plaintext:\n{result['plaintext']}\n\n"
                    f"Recovered Vigenère shifts:\n"
                    f"{result['vigenere_key']}\n\n"
                    "Recovered Hill matrix:\n"
                    f"[ {matrix[0][0]:2d}  {matrix[0][1]:2d} ]\n"
                    f"[ {matrix[1][0]:2d}  {matrix[1][1]:2d} ]\n\n"
                    "The candidate matches the supplied prefix. "
                    "Unknown plaintext cannot be independently verified "
                    "without ground truth."
                )

            else:

                report = (
                    "ATTACK UNSUCCESSFUL\n\n"
                    + result.get("reason", "No candidate recovered.")
                )

            self.set_output(self.attack_output, report)

        except ValueError as exc:

            messagebox.showerror(
                "Attack error",
                str(exc),
                parent=self
            )

    # ========================================================
    # BENCHMARK LAB
    # ========================================================

    def page_benchmark(self, parent):

        self.heading(
            parent,
            "Benchmark Lab",
            "Measure the performance of the cipher and known-prefix attack."
        )

        # Experiment controls

        settings = self.panel(
            parent,
            "Experiment settings",
            "Fixed-seed random A–Z messages and valid random keys."
        )

        settings.pack(fill="x", padx=30, pady=(0, 14))

        controls = ctk.CTkFrame(
            settings,
            fg_color="transparent"
        )

        controls.pack(fill="x", padx=18, pady=(0, 16))

        ctk.CTkLabel(
            controls,
            text="Trials per message length",
            font=(FONT, 10, "bold"),
            text_color=INK
        ).pack(side="left")

        self.trial_var = tk.StringVar(value="20")

        ctk.CTkEntry(
            controls,
            textvariable=self.trial_var,
            width=75,
            height=34,
            corner_radius=6,
            border_color=BORDER,
            fg_color="#FCFBFD"
        ).pack(side="left", padx=12)

        self.bench_button = self.button(
            controls,
            "Run experiment",
            self.start_benchmark,
            True,
            140
        )

        self.bench_button.pack(side="left")

        self.bench_status = ctk.CTkLabel(
            controls,
            text="Ready",
            font=(FONT, 10),
            text_color=MUTED
        )

        self.bench_status.pack(side="left", padx=15)

        # Performance chart

        chart_panel = self.panel(
            parent,
            "Execution time comparison",
            "Mean milliseconds per trial. Lower values indicate faster execution."
        )

        chart_panel.pack(fill="x", padx=30, pady=(0, 14))

        self.chart = tk.Canvas(
            chart_panel,
            height=260,
            bg=WHITE,
            highlightthickness=0
        )

        self.chart.pack(fill="x", padx=18, pady=(0, 15))

        self.draw_empty_chart()

        # Results

        table_panel = self.panel(
            parent,
            "Experiment results",
            "Measurements for each tested plaintext length."
        )

        table_panel.pack(fill="x", padx=30, pady=(0, 20))

        self.result_table = ctk.CTkTextbox(
            table_panel,
            height=175,
            corner_radius=6,
            fg_color="#FCFBFD",
            border_width=1,
            border_color=BORDER,
            text_color=INK,
            font=(MONO, 10)
        )

        self.result_table.pack(
            fill="x",
            padx=18,
            pady=(0, 15)
        )

        self.result_table.insert(
            "1.0",
            "Run an experiment to view detailed results."
        )

        self.result_table.configure(state="disabled")

        if self.benchmark_data:
            self.display_benchmark(self.benchmark_data)

    def draw_empty_chart(self):

        self.chart.delete("all")

        width = max(self.chart.winfo_width(), 650)
        height = 260

        self.chart.create_text(
            width / 2,
            height / 2,
            text="Your benchmark results will appear here",
            fill=MUTED,
            font=(FONT, 11)
        )

    def draw_chart(self, data):

        self.chart.delete("all")

        self.update_idletasks()

        width = max(self.chart.winfo_width(), 650)
        height = 260

        left = 70
        right = width - 25
        top = 30
        bottom = 205

        series = [
            ("Attack", PURPLE),
            ("Shift", "#91A6C8"),
            ("Custom enc.", "#C49B73"),
            ("Custom dec.", GREEN)
        ]

        max_value = max(
            max(row["means"]) for row in data
        ) or 1

        for i in range(5):

            y = bottom - (bottom - top) * i / 4

            self.chart.create_line(
                left, y, right, y,
                fill=BORDER
            )

            self.chart.create_text(
                left - 10,
                y,
                text=f"{max_value * i / 4:.3f}",
                anchor="e",
                fill=MUTED,
                font=(FONT, 8)
            )

        group_width = (right - left) / len(data)
        bar_width = min(15, group_width / 6)

        for index, row in enumerate(data):

            center = left + group_width * (index + .5)

            for series_index, (name, color) in enumerate(series):

                value = row["means"][series_index]

                x = center + (
                    series_index - 1.5
                ) * (bar_width + 3)

                bar_height = (
                    value / max_value
                ) * (bottom - top)

                self.chart.create_rectangle(
                    x,
                    bottom - bar_height,
                    x + bar_width,
                    bottom,
                    fill=color,
                    outline=""
                )

            self.chart.create_text(
                center,
                bottom + 17,
                text=str(row["length"]),
                fill=MUTED,
                font=(FONT, 9)
            )

        self.chart.create_text(
            (left + right) / 2,
            height - 12,
            text="Plaintext length",
            fill=MUTED,
            font=(FONT, 9)
        )

        # Legend

        x = left

        for name, color in series:

            self.chart.create_rectangle(
                x, 10, x + 9, 19,
                fill=color,
                outline=""
            )

            self.chart.create_text(
                x + 14, 14,
                text=name,
                anchor="w",
                fill=MUTED,
                font=(FONT, 8)
            )

            x += 125

    def start_benchmark(self):

        if self.benchmark_running:
            return

        try:

            trials = int(self.trial_var.get())

            if not 1 <= trials <= 100:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Invalid settings",
                "Trials must be a whole number from 1 to 100.",
                parent=self
            )

            return

        self.benchmark_running = True

        self.bench_button.configure(
            state="disabled",
            text="Running..."
        )

        self.bench_status.configure(
            text="Experiment running",
            text_color="#A67B3E"
        )

        self._set_table("Running benchmark...\nPlease wait.")

        thread = threading.Thread(
            target=self.benchmark_worker,
            args=(trials,),
            daemon=True
        )

        thread.start()

        self.after(100, self.poll_benchmark)

    def benchmark_worker(self, trials):

        rng = random.Random(486)

        lengths = (41, 80, 161, 320)

        results = []

        try:

            for length in lengths:

                totals = [0.0, 0.0, 0.0, 0.0]
                successes = 0
                ciphertext_length = 0

                for _ in range(trials):

                    message = "".join(
                        rng.choice(string.ascii_uppercase)
                        for _ in range(length)
                    )

                    key = random_key(rng)

                    start = time.perf_counter()
                    shift_encrypt(message)
                    totals[1] += time.perf_counter() - start

                    start = time.perf_counter()
                    ciphertext = encrypt(message, key)
                    totals[2] += time.perf_counter() - start

                    start = time.perf_counter()
                    recovered = decrypt(ciphertext, key)
                    totals[3] += time.perf_counter() - start

                    if recovered != message:
                        raise RuntimeError(
                            "Encryption/decryption round trip failed."
                        )

                    start = time.perf_counter()

                    attack = known_plaintext_attack(
                        message[:20],
                        ciphertext
                    )

                    totals[0] += time.perf_counter() - start

                    successes += int(
                        attack["success"]
                        and attack.get("plaintext") == message
                    )

                    ciphertext_length = len(ciphertext)

                results.append({
                    "length": length,
                    "ciphertext_length": ciphertext_length,
                    "successes": successes,
                    "trials": trials,
                    "means": [
                        value * 1000 / trials
                        for value in totals
                    ]
                })

            self.benchmark_queue.put(
                ("success", results)
            )

        except Exception as exc:

            self.benchmark_queue.put(
                ("error", str(exc))
            )

    def poll_benchmark(self):

        try:
            result = self.benchmark_queue.get_nowait()

        except queue.Empty:

            if self.benchmark_running:
                self.after(100, self.poll_benchmark)

            return

        self.benchmark_running = False

        self.bench_button.configure(
            state="normal",
            text="Run experiment"
        )

        if result[0] == "error":

            self.bench_status.configure(
                text="Experiment failed",
                text_color=RED
            )

            self._set_table(result[1])

            return

        self.benchmark_data = result[1]

        self.bench_status.configure(
            text="Experiment completed",
            text_color=GREEN
        )

        if self.current_page == "Benchmark Lab":
            self.display_benchmark(self.benchmark_data)

    def display_benchmark(self, data):

        self.draw_chart(data)

        lines = [
            "PLAIN   CIPHER   ATTACK SUCCESS   ATTACK ms   SHIFT ms   "
            "CUSTOM ENC ms   CUSTOM DEC ms",
            "-" * 91
        ]

        for row in data:

            means = row["means"]

            lines.append(
                f"{row['length']:5d}   "
                f"{row['ciphertext_length']:6d}   "
                f"{row['successes']:2d}/{row['trials']:<2d}"
                f"             "
                f"{means[0]:9.4f}   "
                f"{means[1]:8.4f}   "
                f"{means[2]:13.4f}   "
                f"{means[3]:13.4f}"
            )

        lines.extend([
            "",
            "All times are mean milliseconds per trial.",
            "The attack uses the first 20 plaintext letters.",
            "Fixed seed: 486. Timings vary with system load.",
            "The experiment checks full encryption/decryption round trips."
        ])

        self._set_table("\n".join(lines))

    def _set_table(self, text):

        if not hasattr(self, "result_table"):
            return

        if not self.result_table.winfo_exists():
            return

        self.result_table.configure(state="normal")
        self.result_table.delete("1.0", "end")
        self.result_table.insert("1.0", text)
        self.result_table.configure(state="disabled")

    # ========================================================
    # DOCUMENTATION
    # ========================================================

    def page_docs(self, parent):

        self.heading(
            parent,
            "Documentation",
            "Technical reference for the CIPHERLAB implementation."
        )

        sections = [
            (
                "Key structure",
                "Exactly 10 uppercase ASCII letters. The first six "
                "characters form the Vigenère key. The final four "
                "characters define the 2×2 Hill matrix in row-major order."
            ),
            (
                "Ciphertext format",
                "A leading A indicates an even-length plaintext. "
                "A leading B indicates an odd-length plaintext. "
                "The remaining ciphertext body always has even length."
            ),
            (
                "Plaintext cleaning",
                "Only ASCII letters A–Z are retained. Lowercase letters "
                "are converted to uppercase. Spaces and punctuation "
                "are discarded."
            ),
            (
                "Encryption process",
                "Vigenère transformation is performed first. If the "
                "cleaned message has odd length, X padding is appended. "
                "The Hill transformation is then applied to pairs."
            ),
            (
                "Decryption process",
                "The inverse Hill transformation is applied first. "
                "Padding is removed when the marker is B. The Vigenère "
                "transformation is then reversed."
            ),
            (
                "Known-prefix attack",
                "The attack attempts to recover the cipher parameters "
                "using a known plaintext prefix and complete ciphertext. "
                "It requires observations from all three phases and "
                "suitable invertible difference vectors."
            ),
            (
                "Security notice",
                "This application is an educational classical cryptography "
                "demonstration. It is not suitable for secure communication."
            )
        ]

        for title, description in sections:

            panel = self.panel(parent, title)

            panel.pack(
                fill="x",
                padx=30,
                pady=5
            )

            ctk.CTkLabel(
                panel,
                text=description,
                text_color=MUTED,
                font=(FONT, 10),
                wraplength=800,
                justify="left"
            ).pack(
                anchor="w",
                padx=18,
                pady=(0, 15)
            )

    # ========================================================
    # GENERAL UTILITIES
    # ========================================================

    def clear_textboxes(self, *widgets):

        for widget in widgets:

            if not widget.winfo_exists():
                continue

            widget.configure(state="normal")
            widget.delete("1.0", "end")

            if widget is not self.enc_input and widget is not self.dec_input:
                widget.configure(state="disabled")

    def about(self):

        messagebox.showinfo(
            "About CIPHERLAB",
            "CIPHERLAB\n"
            "Classical Cryptography Studio\n\n"
            "Vigenère + 2×2 Hill Cipher\n"
            "Educational use only.",
            parent=self
        )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app = CipherLab()
    app.mainloop()
