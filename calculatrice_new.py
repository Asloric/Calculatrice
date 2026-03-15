# "C:/Program Files/Python38/python.exe" -m PyInstaller --noconfirm --clean --windowed --onefile --name Calculatrice calculatrice_new.py
import ast
import math
import re
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional


class SafeEvaluator(ast.NodeVisitor):
    ALLOWED_BINARY = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.FloorDiv: lambda a, b: a // b,
        ast.Mod: lambda a, b: a % b,
        ast.Pow: lambda a, b: a ** b,
        ast.BitXor: lambda a, b: a ** b,  # 2^3 behaves like power in this calculator
    }

    ALLOWED_UNARY = {
        ast.UAdd: lambda a: +a,
        ast.USub: lambda a: -a,
    }

    ALLOWED_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "floor": math.floor,
        "ceil": math.ceil,
        "pi": math.pi,
        "e": math.e,
    }

    def __init__(self, variables: Dict[str, float]):
        self.variables = variables

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_BinOp(self, node):
        op_type = type(node.op)
        if op_type not in self.ALLOWED_BINARY:
            raise ValueError("Opérateur non autorisé")
        left = self.visit(node.left)
        right = self.visit(node.right)
        return self.ALLOWED_BINARY[op_type](left, right)

    def visit_UnaryOp(self, node):
        op_type = type(node.op)
        if op_type not in self.ALLOWED_UNARY:
            raise ValueError("Opérateur unaire non autorisé")
        return self.ALLOWED_UNARY[op_type](self.visit(node.operand))

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Fonction invalide")
        func_name = node.func.id
        if func_name not in self.ALLOWED_FUNCTIONS or not callable(self.ALLOWED_FUNCTIONS[func_name]):
            raise ValueError(f"Fonction inconnue : {func_name}")
        args = [self.visit(arg) for arg in node.args]
        return self.ALLOWED_FUNCTIONS[func_name](*args)

    def visit_Name(self, node):
        if node.id in self.variables:
            return self.variables[node.id]
        if node.id in self.ALLOWED_FUNCTIONS and not callable(self.ALLOWED_FUNCTIONS[node.id]):
            return self.ALLOWED_FUNCTIONS[node.id]
        raise ValueError(f"Nom inconnu : {node.id}")

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Constante non autorisée")

    def visit_Num(self, node):  # pragma: no cover
        return node.n

    def generic_visit(self, node):
        raise ValueError(f"Expression non autorisée : {type(node).__name__}")


class MagicCalculator(tk.Tk):
    RE_ANS = re.compile(r"ans\((\d+)\)")
    RE_LEADING_OPERATOR = re.compile(r"^\s*([+\-*/%^])")

    def __init__(self):
        super().__init__()
        self.title("Magic Calculator")
        self.geometry("720x520")
        self.minsize(680, 460)
        self.configure(bg="#10131a")

        self.results: List[Any] = []
        self.formulas: List[str] = []
        self.error_details: List[str] = []
        self.display_line_indices: List[int] = []
        self.recalc_job: Optional[str] = None

        self.palette = {
            "bg": "#10131a",
            "panel": "#171c25",
            "panel_alt": "#1e2531",
            "editor": "#0f141c",
            "line": "#283244",
            "accent": "#6ea8fe",
            "accent_2": "#7ef0c5",
            "text": "#e6edf7",
            "muted": "#97a3b6",
            "warning": "#ff7b72",
            "comment": "#6fbb7b",
            "function": "#ffd580",
            "paren": "#f4d35e",
            "operator": "#88c0ff",
            "selection": "#2b3950",
        }

        self._configure_ttk_style()
        self._build_ui()
        self._bind_events()
        self.refresh_all()

    def _configure_ttk_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "App.TFrame",
            background=self.palette["bg"],
        )
        style.configure(
            "Panel.TFrame",
            background=self.palette["panel"],
            borderwidth=0,
        )
        style.configure(
            "Sidebar.TFrame",
            background=self.palette["panel_alt"],
            borderwidth=0,
        )
        style.configure(
            "Title.TLabel",
            background=self.palette["bg"],
            foreground=self.palette["text"],
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.palette["bg"],
            foreground=self.palette["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background=self.palette["panel_alt"],
            foreground=self.palette["text"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Hint.TLabel",
            background=self.palette["panel_alt"],
            foreground=self.palette["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Status.TLabel",
            background=self.palette["bg"],
            foreground=self.palette["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Primary.TButton",
            background=self.palette["accent"],
            foreground="#0a0d12",
            borderwidth=0,
            focusthickness=0,
            focuscolor=self.palette["accent"],
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#8cb9ff")],
            foreground=[("active", "#0a0d12")],
        )
        style.configure(
            "Secondary.TButton",
            background=self.palette["panel_alt"],
            foreground=self.palette["text"],
            borderwidth=0,
            focusthickness=0,
            focuscolor=self.palette["panel_alt"],
            font=("Segoe UI", 10),
            padding=(12, 8),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#263245")],
        )

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="App.TFrame", padding=(20, 18, 20, 10))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.header_title_var = tk.StringVar(value="Magic Calculator")
        self.header_title = tk.Entry(
            header,
            textvariable=self.header_title_var,
            justify="left",
            bd=0,
            relief="flat",
            highlightthickness=0,
            insertbackground=self.palette["accent"],
            bg=self.palette["bg"],
            fg=self.palette["text"],
            font=("Segoe UI", 18, "bold"),
            selectbackground=self.palette["selection"],
            selectforeground=self.palette["text"],
        )
        self.header_title.grid(row=0, column=0, sticky="w")
        actions = ttk.Frame(header, style="App.TFrame")
        actions.grid(row=0, column=1, sticky="e")
        ttk.Button(actions, text="Effacer", style="Secondary.TButton", command=self.clear_all).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(actions, text="Recalculer", style="Primary.TButton", command=self.refresh_all).grid(row=0, column=1)

        content = ttk.Frame(self, style="App.TFrame", padding=(20, 0, 20, 14))
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.main_pane = tk.PanedWindow(
            content,
            orient=tk.HORIZONTAL,
            sashwidth=10,
            showhandle=False,
            sashrelief="flat",
            bd=0,
            bg=self.palette["bg"],
            opaqueresize=True,
            relief="flat",
            handlepad=0,
            handlesize=0,
        )
        self.main_pane.grid(row=0, column=0, sticky="nsew")
        self.main_pane.bind("<Configure>", self._update_divider_hint)

        editor_card = ttk.Frame(self.main_pane, style="Panel.TFrame", padding=1)
        editor_card.grid_columnconfigure(0, weight=1)
        editor_card.grid_rowconfigure(0, weight=1)

        self.text_area = tk.Text(
            editor_card,
            wrap="none",
            undo=True,
            padx=18,
            pady=16,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            insertbackground=self.palette["accent"],
            selectbackground=self.palette["selection"],
            selectforeground=self.palette["text"],
            bg=self.palette["editor"],
            fg=self.palette["text"],
            font=("Cascadia Code", 13),
            spacing1=2,
            spacing3=3,
        )
        self.text_area.grid(row=0, column=0, sticky="nsew")
        self.text_area.focus_set()

        sidebar = ttk.Frame(self.main_pane, style="Sidebar.TFrame", padding=(1, 1, 1, 1))
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(0, weight=1)

        self.result_list = tk.Text(
            sidebar,
            wrap="none",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            padx=10,
            pady=16,
            cursor="hand2",
            state="disabled",
            bg=self.palette["panel_alt"],
            fg=self.palette["text"],
            insertbackground=self.palette["text"],
            selectbackground=self.palette["selection"],
            selectforeground=self.palette["text"],
            font=("Cascadia Code", 13),
            spacing1=2,
            spacing3=3,
        )
        self.result_list.grid(row=0, column=0, sticky="nsew", padx=(6, 8), pady=0)

        self.main_pane.add(editor_card, stretch="always", minsize=380)
        self.main_pane.add(sidebar, minsize=135)

        self.divider_hint = tk.Label(
            content,
            text="⋮⋮",
            bg=self.palette["bg"],
            fg="#5f6b7c",
            font=("Segoe UI Symbol", 12, "bold"),
            cursor="sb_h_double_arrow",
            padx=2,
            pady=0,
            bd=0,
            highlightthickness=0,
        )
        self.divider_hint.place(relx=0.5, rely=0.5, anchor="center")
        self.divider_hint.bind("<ButtonPress-1>", self._start_divider_drag)
        self.divider_hint.bind("<B1-Motion>", self._drag_divider)
        self.divider_hint.bind("<ButtonRelease-1>", self._end_divider_drag)

        self.after_idle(self._set_initial_sash)

        self.status_var = tk.StringVar(value="Prêt")
        self.status_label = ttk.Label(self, textvariable=self.status_var, style="Status.TLabel", anchor="w")
        self.status_label.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))

        self._configure_tags()
        self._resize_title_entry()

    def _configure_tags(self):
        self.text_area.tag_config("operator", foreground=self.palette["operator"])
        self.text_area.tag_config("function", foreground=self.palette["function"])
        self.text_area.tag_config("paren", foreground=self.palette["paren"])
        self.text_area.tag_config("comment", foreground=self.palette["comment"])
        self.text_area.tag_config("ans", foreground=self.palette["accent_2"])
        self.text_area.tag_config("error_line", underline=True)
        self.result_list.tag_config("line_id", foreground="#475364")
        self.result_list.tag_config("line_value", foreground=self.palette["text"])
        self.result_list.tag_config("line_error", foreground=self.palette["warning"])

    def _bind_events(self):
        self.text_area.bind("<KeyRelease>", self.on_key_release)
        self.text_area.bind("<Return>", self.on_return_pressed)
        self.result_list.bind("<FocusIn>", self.return_focus)
        self.header_title.bind("<FocusIn>", self._on_title_focus)
        self.header_title.bind("<KeyRelease>", self._resize_title_entry)

    def _on_title_focus(self, event=None):
        self.after_idle(lambda: self.header_title.icursor(tk.END))

    def _resize_title_entry(self, event=None):
        title = self.header_title_var.get().strip() or "Magic Calculator"
        self.header_title.configure(width=max(12, min(len(title) + 1, 36)))

    def on_layout_change(self, event=None):
        parent = self.text_area.master.master
        parent.grid_columnconfigure(0, weight=3)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        self.text_area.master.grid_configure(row=0, column=0, sticky="nsew", padx=(0, 14), pady=0)
        self.result_list.master.grid_configure(row=0, column=1, sticky="nsew")


    def _set_initial_sash(self):
        try:
            total_w = max(self.main_pane.winfo_width(), 860)
            target_x = max(470, total_w - 165)
            self.main_pane.sash_place(0, target_x, 0)
        except tk.TclError:
            pass
        self._update_divider_hint()

    def _update_divider_hint(self, event=None):
        try:
            sash_x, _ = self.main_pane.sash_coord(0)
            pane_h = self.main_pane.winfo_height()
            self.divider_hint.place(x=sash_x + 5, y=max(pane_h // 2, 40), anchor="center")
            self.divider_hint.lift()
        except tk.TclError:
            pass

    def _start_divider_drag(self, event):
        self._divider_drag_origin = event.x_root
        try:
            self._divider_sash_origin = self.main_pane.sash_coord(0)[0]
        except tk.TclError:
            self._divider_sash_origin = 0

    def _drag_divider(self, event):
        try:
            delta = event.x_root - getattr(self, "_divider_drag_origin", event.x_root)
            new_x = getattr(self, "_divider_sash_origin", 0) + delta
            self.main_pane.sash_place(0, new_x, 0)
            self._update_divider_hint()
        except tk.TclError:
            pass

    def _end_divider_drag(self, event):
        self._update_divider_hint()

    def clear_all(self):
        self.cancel_pending_recalc()
        self.text_area.delete("1.0", tk.END)
        self.results = []
        self.formulas = []
        self.error_details = []
        self.refresh_all()
        self.status_var.set("Éditeur vidé")

    def return_focus(self, event=None):
        self.after_idle(self.text_area.focus_set)

    def on_key_release(self, event=None):
        self.colorize_text()
        if event and event.keysym in {"Return", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"}:
            return
        self.schedule_recalc()

    def on_return_pressed(self, event=None):
        self.cancel_pending_recalc()
        self.refresh_all(triggered_by_enter=True)
        return None

    def schedule_recalc(self):
        self.cancel_pending_recalc()
        self.status_var.set("Saisie détectée… recalcul dans 0,5 s")
        self.recalc_job = self.after(500, self.refresh_all)

    def cancel_pending_recalc(self):
        if self.recalc_job is not None:
            self.after_cancel(self.recalc_job)
            self.recalc_job: Optional[str] = None

    def refresh_all(self, triggered_by_enter=False):
        self.cancel_pending_recalc()
        lines = self.get_lines()
        self.formulas = lines[:]
        self.results = []
        self.error_details = []

        for index, raw_line in enumerate(lines):
            line = self.normalize_line(raw_line, index)
            if not line:
                self.results.append("")
                self.error_details.append("")
                continue

            try:
                result = self.evaluate_line(line, index)
                self.results.append(result)
                self.error_details.append("")
            except Exception as exc:
                self.results.append("error")
                self.error_details.append(str(exc))

        self.update_results_list()
        self.colorize_text()
        error_count = sum(1 for result in self.results if result == "error")
        filled = sum(1 for line in lines if line.strip())
        if triggered_by_enter:
            if error_count:
                self.status_var.set(f"Validation effectuée — {error_count} erreur(s) sur {filled} ligne(s)")
            else:
                self.status_var.set(f"Validation effectuée — {filled} ligne(s) calculée(s)")
        else:
            if error_count:
                self.status_var.set(f"Recalcul terminé — {error_count} erreur(s)")
            else:
                self.status_var.set("Recalcul terminé")

    def get_lines(self):
        content = self.text_area.get("1.0", "end-1c")
        return content.split("\n") if content else [""]

    def normalize_line(self, raw_line: str, line_number: int) -> str:
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            return ""
        if self.RE_LEADING_OPERATOR.match(line):
            if line_number == 0:
                raise ValueError("La première ligne ne peut pas commencer par un opérateur")
            line = f"ans({line_number - 1}){line}"
        return line.replace("^", "**")

    def build_context(self, current_line: int):
        context = {}
        for idx in range(current_line):
            value = self.results[idx] if idx < len(self.results) else ""
            if value in ("", "error"):
                raise ValueError(f"ans({idx}) est indisponible")
            context[f"ans_{idx}"] = value
        return context

    def transform_ans_references(self, expr: str) -> str:
        def repl(match):
            ref = int(match.group(1))
            return f"ans_{ref}"

        return self.RE_ANS.sub(repl, expr)

    def validate_ans_references(self, expr: str, current_line: int):
        for match in self.RE_ANS.finditer(expr):
            ref = int(match.group(1))
            if ref >= current_line:
                raise ValueError(f"ans({ref}) doit référencer une ligne précédente")

    def evaluate_line(self, expression: str, line_number: int):
        self.validate_ans_references(expression, line_number)
        transformed = self.transform_ans_references(expression)
        context = self.build_context(line_number)
        tree = ast.parse(transformed, mode="eval")
        evaluator = SafeEvaluator(context)
        return evaluator.visit(tree)

    def update_results_list(self):
        self.result_list.configure(state="normal")
        self.result_list.delete("1.0", tk.END)
        self.display_line_indices = []

        last_visible_index = -1
        for index, formula in enumerate(self.formulas):
            if formula.strip():
                last_visible_index = index

        if last_visible_index < 0:
            self.result_list.configure(state="disabled")
            return

        for index in range(last_visible_index + 1):
            line_start = self.result_list.index("end-1c")
            result = self.results[index]
            if result == "":
                self.result_list.insert(tk.END, f"{index}", ("line_id",))
            elif result == "error":
                detail = self.error_details[index]
                short = detail[:30] + "…" if len(detail) > 30 else detail
                self.result_list.insert(tk.END, f"{index}", ("line_id",))
                self.result_list.insert(tk.END, " : ", ("line_value",))
                self.result_list.insert(tk.END, f"✕ {short}", ("line_error",))
            else:
                self.result_list.insert(tk.END, f"{index}", ("line_id",))
                self.result_list.insert(tk.END, " : ", ("line_value",))
                self.result_list.insert(tk.END, f"{result}", ("line_value",))
            self.result_list.insert(tk.END, "\n")
            line_end = self.result_list.index("end-1c")
            self.display_line_indices.append(index)
            tag_name = f"click_{len(self.display_line_indices) - 1}"
            self.result_list.tag_add(tag_name, line_start, line_end)
            self.result_list.tag_bind(tag_name, "<Button-1>", lambda event, idx=index: self.insert_ans_reference(idx))

        self.result_list.configure(state="disabled")

    def insert_ans_reference(self, index: int):
        self.text_area.insert(tk.INSERT, f"ans({index})")
        self.text_area.focus_set()
        self.text_area.see(tk.INSERT)
        self.schedule_recalc()

    def on_result_selected(self, event=None):
        return "break"

    def colorize_text(self):
        for tag in ("operator", "function", "paren", "comment", "ans", "error_line"):
            self.text_area.tag_remove(tag, "1.0", tk.END)

        content = self.text_area.get("1.0", "end-1c")

        for match in re.finditer(r"#.*$", content, flags=re.MULTILINE):
            self._tag_span("comment", match.start(), match.end())

        for match in re.finditer(r"\b[a-zA-Z_]\w*(?=\s*\()", content):
            self._tag_span("function", match.start(), match.end())

        for match in re.finditer(r"ans\(\d+\)", content):
            self._tag_span("ans", match.start(), match.end())

        for match in re.finditer(r"[()\[\]]", content):
            self._tag_span("paren", match.start(), match.end())

        for match in re.finditer(r"(?:\*\*|[+\-*/%^])", content):
            self._tag_span("operator", match.start(), match.end())

        for index, result in enumerate(self.results):
            if result == "error":
                line_start = f"{index + 1}.0"
                line_end = f"{index + 1}.end"
                self.text_area.tag_add("error_line", line_start, line_end)

    def _tag_span(self, tag_name: str, start: int, end: int):
        start_pos = f"1.0 + {start} chars"
        end_pos = f"1.0 + {end} chars"
        self.text_area.tag_add(tag_name, start_pos, end_pos)


if __name__ == "__main__":
    app = MagicCalculator()
    app.mainloop()
