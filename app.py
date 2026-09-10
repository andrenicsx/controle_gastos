"""Casheye - personal expense tracker built with Python/Tkinter."""

import csv
import json
import uuid
import calendar
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

DATA_FILE = Path(__file__).with_name("lancamentos.json")
CATEGORIES = {"Expense": ["Food", "Housing", "Transport", "Health", "Leisure", "Subscriptions", "Other"], "Income": ["Salary", "Freelance", "Investments", "Gifts", "Other"]}
TYPE_MIGRATION = {"Despesa": "Expense", "Receita": "Income", "Ganhos": "Income"}
CATEGORY_MIGRATION = {"Alimentacao": "Food", "Moradia": "Housing", "Transporte": "Transport", "Saude": "Health", "Lazer": "Leisure", "Assinaturas": "Subscriptions", "Outros": "Other", "Salario": "Salary", "Investimentos": "Investments", "Presentes": "Gifts"}
PALETTE = ["#7667E8", "#F08A72", "#32AD8B", "#E8B84A", "#5795E8", "#C96BCB", "#7E899C"]
DISPLAY_FONT = "Bahnschrift"
BODY_FONT = "Segoe UI"
PAYMENT_METHODS = ["Cash", "PIX", "Debit card", "Credit card", "Meal voucher", "Bank transfer", "Other"]

def money(value):
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

class RoundedButton(tk.Canvas):
    """A small canvas button with reliably rounded corners on Windows Tk."""
    def __init__(self, parent, text, command, surface, fill, foreground, height=38, width=110, outline=None):
        super().__init__(parent, height=height, width=width, bg=surface, highlightthickness=0, bd=0, cursor="hand2")
        self.text, self.command = text, command
        self.surface, self.fill, self.foreground = surface, fill, foreground
        self.outline = outline or self.adjust_color(fill, 0.74)
        self.hover_fill, self.height = self.adjust_color(fill, 0.90), height
        self.current_fill = fill
        self.bind("<Configure>", self.draw)
        self.bind("<Enter>", lambda _event: self.set_fill(self.hover_fill))
        self.bind("<Leave>", lambda _event: self.set_fill(self.fill))
        self.bind("<Button-1>", lambda _event: self.command())
        self.bind("<Return>", lambda _event: self.command())
        self.configure(takefocus=True)

    @staticmethod
    def adjust_color(color, factor):
        channels = tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))
        return "#%02x%02x%02x" % tuple(max(0, min(255, int(channel * factor))) for channel in channels)

    def set_fill(self, color):
        self.current_fill = color
        self.draw()

    def draw(self, _event=None):
        width, height = max(self.winfo_width(), 2), self.height
        radius = height // 2
        self.delete("all")
        self.create_rectangle(radius, 0, width - radius, height, fill=self.current_fill, outline="")
        self.create_rectangle(0, radius, width, height - radius, fill=self.current_fill, outline="")
        self.create_oval(0, 0, radius * 2, height, fill=self.current_fill, outline="")
        self.create_oval(width - radius * 2, 0, width, height, fill=self.current_fill, outline="")
        self.create_line(radius, 0, width - radius, 0, fill=self.outline, width=1)
        self.create_line(radius, height - 1, width - radius, height - 1, fill=self.outline, width=1)
        self.create_arc(0, 0, radius * 2, height, start=90, extent=180, style="arc", outline=self.outline, width=1)
        self.create_arc(width - radius * 2, 0, width, height, start=270, extent=180, style="arc", outline=self.outline, width=1)
        self.create_text(width / 2, height / 2, text=self.text, fill=self.foreground, font=(BODY_FONT, 9, "bold"))

class ExpenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Casheye | Money control"); self.geometry("1180x770"); self.minsize(980, 650); self.configure(bg="#F4F5FA")
        self.transactions = self.load_transactions(); self.setup_style(); self.create_variables(); self.create_layout(); self.refresh()

    def setup_style(self):
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("TFrame", background="#F4F5FA"); s.configure("Card.TFrame", background="#FFFFFF")
        s.configure("TLabel", background="#FFFFFF", foreground="#22293A", font=(BODY_FONT, 10))
        s.configure("CardTitle.TLabel", background="#FFFFFF", foreground="#20283A", font=(DISPLAY_FONT, 16, "bold"))
        s.configure("Field.TLabel", background="#FFFFFF", foreground="#697186", font=(BODY_FONT, 9, "bold"))
        s.configure("Primary.TButton", font=(BODY_FONT, 10, "bold"), background="#5B4BC4", foreground="white", borderwidth=0, padding=(15, 11)); s.map("Primary.TButton", background=[("active", "#4839A5")])
        s.configure("Secondary.TButton", font=(BODY_FONT, 9, "bold"), background="#F0EEFF", foreground="#5849B5", borderwidth=0, padding=(11, 8)); s.map("Secondary.TButton", background=[("active", "#E3DFFF")])
        s.configure("Danger.TButton", font=(BODY_FONT, 9, "bold"), background="#FDE9E6", foreground="#B54F40", borderwidth=0, padding=(11, 8)); s.map("Danger.TButton", background=[("active", "#F8D9D3")])
        s.configure("TEntry", fieldbackground="#FAFAFD", bordercolor="#E4E6EF", padding=5); s.configure("TCombobox", fieldbackground="#FAFAFD", bordercolor="#E4E6EF", padding=4)
        s.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#293145", rowheight=39, font=(BODY_FONT, 10), borderwidth=0)
        s.configure("Treeview.Heading", background="#F8F8FC", foreground="#7A8294", font=(BODY_FONT, 9, "bold"), relief="flat", padding=(8, 10)); s.map("Treeview", background=[("selected", "#ECEAFC")], foreground=[("selected", "#40348C")])

    def create_variables(self):
        today = date.today(); self.editing_id = None; self.type_var = tk.StringVar(value="Expense"); self.description_var = tk.StringVar(); self.amount_var = tk.StringVar(); self.date_var = tk.StringVar(value=today.strftime("%d/%m/%Y")); self.category_var = tk.StringVar(value=CATEGORIES["Expense"][0]); self.payment_var = tk.StringVar(value="PIX"); self.installments_var = tk.StringVar(value="1"); self.month_var = tk.StringVar(value=today.strftime("%Y-%m")); self.filter_var = tk.StringVar(value="All"); self.balance_var = tk.StringVar(); self.income_var = tk.StringVar(); self.expense_var = tk.StringVar(); self.message_var = tk.StringVar()

    def available_periods(self):
        """Return a two-year month range centered on the current month."""
        today = date.today()
        periods = []
        for offset in range(-12, 13):
            month_number = today.month + offset
            year = today.year + (month_number - 1) // 12
            month = (month_number - 1) % 12 + 1
            periods.append(f"{year}-{month:02d}")
        return periods

    def create_layout(self):
        header = tk.Frame(self, bg="#242049", height=124); header.pack(fill="x"); header.pack_propagate(False)
        header_content = tk.Frame(header, bg="#242049")
        header_content.pack(fill="both", expand=True, padx=42, pady=16)
        header_content.columnconfigure(0, weight=1)
        tk.Label(header_content, text="CASHEYE", bg="#242049", fg="#C7C0FF", font=(BODY_FONT, 9, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(header_content, text="Clear vision. Better decisions.", bg="#242049", fg="white", font=(DISPLAY_FONT, 23, "bold")).grid(row=1, column=0, sticky="w", pady=(2, 0))
        tk.Label(header_content, text="Keep track of every move your money makes.", bg="#242049", fg="#B9B8CE", font=(BODY_FONT, 9)).grid(row=2, column=0, sticky="w", pady=(3, 0))
        period = tk.Frame(header_content, bg="#312B5C", padx=13, pady=8); period.grid(row=0, column=1, rowspan=3, sticky="e")
        period.columnconfigure(0, weight=1)
        tk.Label(period, text="PERIOD", bg="#312B5C", fg="#BDB8E7", font=(BODY_FONT, 7, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        month_box = ttk.Combobox(period, textvariable=self.month_var, values=self.available_periods(), state="readonly", width=10)
        month_box.grid(row=1, column=0, sticky="ew", pady=(3, 0)); month_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh())
        ttk.Button(period, text="OK", style="Secondary.TButton", command=self.refresh).grid(row=1, column=1, sticky="ns", padx=(6, 0), pady=(3, 0))
        shell = ttk.Frame(self, padding=(40, 16, 40, 20)); shell.pack(fill="both", expand=True)
        summaries = ttk.Frame(shell); summaries.pack(fill="x", pady=(0, 18))
        self.summary_card(summaries, "Period balance", self.balance_var, "#E8E5FF", "#5B4BC4", "Current balance", 0); self.summary_card(summaries, "Income", self.income_var, "#DCF5EC", "#248A6C", "Money received", 1); self.summary_card(summaries, "Expenses", self.expense_var, "#FFE8E1", "#C95F4B", "Money spent", 2); summaries.columnconfigure((0, 1, 2), weight=1, uniform="summary")
        content = ttk.Frame(shell); content.pack(fill="both", expand=True)
        form = ttk.Frame(content, style="Card.TFrame", padding=18); form.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        centre = ttk.Frame(content, style="Card.TFrame", padding=20); centre.grid(row=0, column=1, sticky="nsew", padx=(0, 16))
        insight = ttk.Frame(content, style="Card.TFrame", padding=18); insight.grid(row=0, column=2, sticky="nsew")
        content.columnconfigure(0, weight=0, minsize=276); content.columnconfigure(1, weight=1, minsize=410); content.columnconfigure(2, weight=0, minsize=230); content.rowconfigure(0, weight=1)
        self.create_form(form); self.create_dashboard(centre); self.create_insight(insight)

    def summary_card(self, parent, title, variable, color, accent, subtitle, column):
        card = tk.Frame(parent, bg=color, padx=17, pady=10); card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 6 if column < 2 else 0)); tk.Frame(card, bg=accent, width=30, height=4).pack(anchor="w", pady=(0, 7)); tk.Label(card, text=title.upper(), bg=color, fg="#626B7C", font=(BODY_FONT, 8, "bold")).pack(anchor="w"); tk.Label(card, textvariable=variable, bg=color, fg="#22293A", font=(DISPLAY_FONT, 19, "bold")).pack(anchor="w", pady=(3, 1)); tk.Label(card, text=subtitle, bg=color, fg="#6D7482", font=(BODY_FONT, 8)).pack(anchor="w")

    def create_form(self, parent):
        ttk.Label(parent, text="New transaction", style="CardTitle.TLabel").pack(anchor="w"); tk.Label(parent, text="Add a new money movement", bg="#FFFFFF", fg="#838A99", font=(BODY_FONT, 9)).pack(anchor="w", pady=(2, 5))
        self.field(parent, "TYPE", self.type_var, ("Expense", "Income"), self.update_categories); self.field(parent, "DESCRIPTION", self.description_var); self.field(parent, "AMOUNT (R$)", self.amount_var); self.field(parent, "DATE", self.date_var); self.field(parent, "CATEGORY", self.category_var, CATEGORIES["Expense"]); self.category_box = self.last_field
        self.field(parent, "PAYMENT METHOD", self.payment_var, PAYMENT_METHODS, self.update_payment_options); self.payment_box = self.last_field
        self.field(parent, "INSTALLMENTS", self.installments_var); self.installments_box = self.last_field
        self.installments_hint = tk.Label(parent, text="Available for credit card payments only.", bg="#FFFFFF", fg="#9AA0AD", font=(BODY_FONT, 8)); self.installments_hint.pack(anchor="w", pady=(3, 0))
        self.update_payment_options()
        self.submit_button = ttk.Button(parent, text="Add transaction  +", style="Primary.TButton", command=self.add_transaction); self.submit_button.pack(fill="x", pady=(12, 0)); tk.Label(parent, text="Your data is saved automatically.", bg="#FFFFFF", fg="#9AA0AD", font=(BODY_FONT, 8)).pack(anchor="center", pady=(6, 0))

    def field(self, parent, label, variable, combo=None, callback=None):
        ttk.Label(parent, text=label, style="Field.TLabel").pack(anchor="w", pady=(4, 0))
        if combo:
            widget = ttk.Combobox(parent, textvariable=variable, values=combo, state="readonly")
            if callback: widget.bind("<<ComboboxSelected>>", callback)
        else: widget = ttk.Entry(parent, textvariable=variable)
        widget.pack(fill="x", pady=(2, 0)); self.last_field = widget

    def create_dashboard(self, parent):
        top = ttk.Frame(parent, style="Card.TFrame"); top.pack(fill="x"); ttk.Label(top, text="Your transactions", style="CardTitle.TLabel").pack(side="left"); ttk.Button(top, text="Export CSV", style="Secondary.TButton", command=self.export_csv).pack(side="right")
        filters = ttk.Frame(parent, style="Card.TFrame"); filters.pack(fill="x", pady=(13, 12)); ttk.Label(filters, text="SHOW", style="Field.TLabel").pack(side="left"); filter_box = ttk.Combobox(filters, textvariable=self.filter_var, values=("All", "Expenses", "Income"), state="readonly", width=12); filter_box.pack(side="left", padx=(8, 0)); filter_box.bind("<<ComboboxSelected>>", lambda _event: self.render_table())
        columns = ("date", "description", "category", "payment", "type", "amount"); self.table = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        for key, label, width, anchor in [("date", "DATE", 58, "center"), ("description", "DESCRIPTION", 120, "w"), ("category", "CATEGORY", 76, "w"), ("payment", "PAYMENT", 82, "w"), ("type", "TYPE", 62, "center"), ("amount", "AMOUNT", 92, "e")]: self.table.heading(key, text=label); self.table.column(key, width=width, anchor=anchor, stretch=(key == "description"))
        self.table.pack(fill="both", expand=True); bottom = ttk.Frame(parent, style="Card.TFrame"); bottom.pack(fill="x", pady=(10, 0)); ttk.Label(bottom, textvariable=self.message_var, foreground="#6F7788").pack(side="left"); ttk.Button(bottom, text="Delete", style="Danger.TButton", command=self.delete_selected).pack(side="right"); ttk.Button(bottom, text="Edit", style="Secondary.TButton", command=self.edit_selected).pack(side="right", padx=(0, 7))

    def create_insight(self, parent):
        ttk.Label(parent, text="Expenses by category", style="CardTitle.TLabel").pack(anchor="w"); tk.Label(parent, text="Breakdown for this period", bg="#FFFFFF", fg="#838A99", font=(BODY_FONT, 9)).pack(anchor="w", pady=(3, 7)); self.chart = tk.Canvas(parent, width=190, height=240, bg="#FFFFFF", highlightthickness=0); self.chart.pack(anchor="center", pady=(0, 4)); self.legend = tk.Frame(parent, bg="#FFFFFF"); self.legend.pack_forget()

    def update_categories(self, _event=None):
        values = CATEGORIES[self.type_var.get()]; self.category_box["values"] = values; self.category_var.set(values[0])

    def update_payment_options(self, _event=None):
        is_credit_card = self.payment_var.get() == "Credit card"
        self.installments_box.configure(state="normal" if is_credit_card else "disabled")
        if not is_credit_card:
            self.installments_var.set("1")
        hint = "Enter the number of monthly installments." if is_credit_card else "Available for credit card payments only."
        self.installments_hint.configure(text=hint, fg="#6255C1" if is_credit_card else "#9AA0AD")

    @staticmethod
    def add_months(transaction_date, months):
        month_index = transaction_date.month - 1 + months
        year = transaction_date.year + month_index // 12
        month = month_index % 12 + 1
        day = min(transaction_date.day, calendar.monthrange(year, month)[1])
        return transaction_date.replace(year=year, month=month, day=day)

    def load_transactions(self):
        try:
            transactions = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            for transaction in transactions:
                transaction["type"] = TYPE_MIGRATION.get(transaction.get("type"), transaction.get("type"))
                transaction["category"] = CATEGORY_MIGRATION.get(transaction.get("category"), transaction.get("category"))
                transaction.setdefault("payment_method", "Not specified")
                transaction.setdefault("installment", 1)
                transaction.setdefault("installments", 1)
            return transactions
        except (FileNotFoundError, json.JSONDecodeError): return []
    def save_transactions(self): DATA_FILE.write_text(json.dumps(self.transactions, ensure_ascii=False, indent=2), encoding="utf-8")
    def period_transactions(self):
        try: datetime.strptime(self.month_var.get().strip(), "%Y-%m")
        except ValueError: return []
        return [item for item in self.transactions if item["date"].startswith(self.month_var.get().strip())]
    def add_transaction(self):
        try:
            amount = float(self.amount_var.get().replace(".", "").replace(",", ".")); transaction_date = datetime.strptime(self.date_var.get(), "%d/%m/%Y").date()
            if amount <= 0 or not self.description_var.get().strip(): raise ValueError
            installments = int(self.installments_var.get()) if self.payment_var.get() == "Credit card" else 1
            if not 1 <= installments <= 48: raise ValueError
        except ValueError: messagebox.showerror("Invalid data", "Enter a description, a valid date, a positive amount, and 1 to 48 installments."); return
        description = self.description_var.get().strip()
        if self.editing_id:
            transaction = next((item for item in self.transactions if item["id"] == self.editing_id), None)
            if transaction is None:
                self.reset_form()
                return
            transaction.update({"type": self.type_var.get(), "description": description, "amount": amount, "date": transaction_date.isoformat(), "category": self.category_var.get(), "payment_method": self.payment_var.get()})
            if self.payment_var.get() != "Credit card":
                transaction["installment"] = 1
                transaction["installments"] = 1
            self.save_transactions(); self.reset_form(); self.refresh()
            return
        installment_amount = round(amount / installments, 2)
        for installment in range(1, installments + 1):
            current_amount = installment_amount if installment < installments else round(amount - installment_amount * (installments - 1), 2)
            installment_description = f"{description} ({installment}/{installments})" if installments > 1 else description
            self.transactions.append({"id": str(uuid.uuid4()), "type": self.type_var.get(), "description": installment_description, "amount": current_amount, "date": self.add_months(transaction_date, installment - 1).isoformat(), "category": self.category_var.get(), "payment_method": self.payment_var.get(), "installment": installment, "installments": installments})
        self.save_transactions(); self.reset_form(); self.refresh()

    def reset_form(self):
        self.editing_id = None
        self.description_var.set("")
        self.amount_var.set("")
        self.installments_var.set("1")
        self.submit_button.configure(text="Add transaction  +")
        self.update_payment_options()

    def edit_selected(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showinfo("Select a transaction", "Select a transaction to edit.")
            return
        transaction = next((item for item in self.transactions if item["id"] == selection[0]), None)
        if transaction is None:
            return
        self.editing_id = transaction["id"]
        self.type_var.set(transaction["type"])
        self.update_categories()
        self.category_var.set(transaction["category"])
        payment_method = transaction.get("payment_method", "Other")
        self.payment_var.set(payment_method if payment_method in PAYMENT_METHODS else "Other")
        self.update_payment_options()
        self.installments_var.set(str(transaction.get("installments", 1)))
        self.description_var.set(transaction["description"])
        self.amount_var.set(f"{transaction['amount']:.2f}".replace(".", ","))
        self.date_var.set(datetime.fromisoformat(transaction["date"]).strftime("%d/%m/%Y"))
        self.submit_button.configure(text="Save changes")
        self.message_var.set("Editing the selected transaction.")
    def delete_selected(self):
        selection = self.table.selection()
        if not selection: messagebox.showinfo("Select a transaction", "Select a transaction to delete."); return
        if messagebox.askyesno("Delete transaction", "Do you want to delete the selected transaction?"):
            if self.editing_id == selection[0]: self.reset_form()
            self.transactions = [item for item in self.transactions if item["id"] != selection[0]]; self.save_transactions(); self.refresh()
    def render_table(self):
        self.table.delete(*self.table.get_children()); wanted = {"Expenses": "Expense", "Income": "Income"}.get(self.filter_var.get())
        for item in sorted(self.period_transactions(), key=lambda item: item["date"], reverse=True):
            if wanted and item["type"] != wanted: continue
            sign = "+" if item["type"] == "Income" else "-"; formatted_date = datetime.fromisoformat(item["date"]).strftime("%d/%m"); self.table.insert("", "end", iid=item["id"], values=(formatted_date, item["description"], item["category"], item.get("payment_method", "Not specified"), item["type"], f"{sign} {money(item['amount'])}"))
    def render_chart(self, items):
        totals = {}
        for item in items:
            if item["type"] == "Expense": totals[item["category"]] = totals.get(item["category"], 0) + item["amount"]
        self.chart.delete("all")
        if not totals:
            self.chart.create_text(95, 105, text="No expenses\nin this period", fill="#A0A6B4", font=(BODY_FONT, 10), justify="center")
            return
        total = sum(totals.values())
        entries = sorted(totals.items(), key=lambda pair: pair[1], reverse=True)
        self.chart.create_text(0, 8, text="TOTAL SPENT", anchor="w", fill="#8991A1", font=(BODY_FONT, 8, "bold"))
        self.chart.create_text(0, 28, text=money(total), anchor="w", fill="#273044", font=(DISPLAY_FONT, 17, "bold"))
        for index, (category, amount) in enumerate(entries[:4]):
            color = PALETTE[index % len(PALETTE)]
            y = 64 + index * 39
            self.chart.create_text(0, y, text=category, anchor="w", fill="#4A5365", font=(BODY_FONT, 9))
            self.chart.create_text(190, y, text=f"{amount / total:.0%}", anchor="e", fill="#6E7687", font=(BODY_FONT, 9, "bold"))
            self.chart.create_rectangle(0, y + 11, 190, y + 18, fill="#EEF0F6", outline="")
            self.chart.create_rectangle(0, y + 11, 190 * amount / total, y + 18, fill=color, outline="")
        if len(entries) > 4:
            self.chart.create_text(0, 225, text=f"+ {len(entries) - 4} more categories", anchor="w", fill="#8B92A0", font=(BODY_FONT, 8))
    def refresh(self):
        items = self.period_transactions(); income = sum(item["amount"] for item in items if item["type"] == "Income"); expense = sum(item["amount"] for item in items if item["type"] == "Expense"); balance = income - expense; self.income_var.set(money(income)); self.expense_var.set(money(expense)); self.balance_var.set(money(balance)); self.message_var.set("You are in the green this period." if balance >= 0 else "Heads up: spending is higher than income."); self.render_table(); self.render_chart(items)
    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"casheye-{self.month_var.get()}.csv", filetypes=[("CSV file", "*.csv")])
        if not path: return
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=";"); writer.writerow(["Date", "Type", "Description", "Category", "Payment method", "Installment", "Amount"])
            for item in self.period_transactions(): writer.writerow([item["date"], item["type"], item["description"], item["category"], item.get("payment_method", "Not specified"), f"{item.get('installment', 1)}/{item.get('installments', 1)}", f"{item['amount']:.2f}"])
        messagebox.showinfo("Export complete", "Your CSV file was created successfully.")

if __name__ == "__main__": ExpenseApp().mainloop()
