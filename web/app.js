const STORAGE_KEY = "casheye-transactions-v1";
const CATEGORIES = {
  Expense: ["Food", "Housing", "Transport", "Health", "Leisure", "Subscriptions", "Other"],
  Income: ["Salary", "Freelance", "Investments", "Gifts", "Other"]
};
const COLORS = ["#7667e8", "#f08a72", "#32ad8b", "#e8b84a", "#5795e8", "#c96bcb", "#7e899c"];
const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dateText = new Intl.DateTimeFormat("en", { day: "2-digit", month: "short" });

const $ = selector => document.querySelector(selector);
const el = {
  form: $("#transactionForm"), type: $("#type"), payment: $("#payment"), description: $("#description"), amount: $("#amount"), date: $("#date"), category: $("#category"), installments: $("#installments"), installmentField: $("#installmentField"), installmentHint: $("#installmentHint"),
  period: $("#period"), filter: $("#typeFilter"), list: $("#transactionList"), chart: $("#chart"), balance: $("#balance"), income: $("#income"), expense: $("#expense"), balanceNote: $("#balanceNote"), submit: $("#submitButton"), cancel: $("#cancelEdit"), formTitle: $("#formTitle"), importButton: $("#importButton"), importInput: $("#importInput"), exportButton: $("#exportButton")
};

let transactions = load();
let editingId = null;

function today() { return new Date().toISOString().slice(0, 10); }
function monthOf(date) { return date.slice(0, 7); }
function load() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; } catch { return []; } }
function save() { localStorage.setItem(STORAGE_KEY, JSON.stringify(transactions)); }
function id() { return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`; }
function addMonths(iso, months) { const value = new Date(`${iso}T12:00:00`); const day = value.getDate(); value.setDate(1); value.setMonth(value.getMonth() + months); const last = new Date(value.getFullYear(), value.getMonth() + 1, 0).getDate(); value.setDate(Math.min(day, last)); return value.toISOString().slice(0, 10); }
function setCategories() { el.category.replaceChildren(...CATEGORIES[el.type.value].map(category => new Option(category, category))); }
function toggleInstallments() { const credit = el.payment.value === "Credit card"; el.installments.disabled = !credit; el.installmentField.classList.toggle("disabled", !credit); if (!credit) el.installments.value = 1; el.installmentHint.textContent = credit ? "Monthly installments, up to 48." : "Credit card only."; }
function periodItems() { return transactions.filter(item => monthOf(item.date) === el.period.value); }
function visibleItems() { const filter = el.filter.value; return periodItems().filter(item => filter === "All" || item.type === filter).sort((a, b) => b.date.localeCompare(a.date)); }

function renderSummary(items) {
  const income = items.filter(item => item.type === "Income").reduce((sum, item) => sum + Number(item.amount), 0);
  const expense = items.filter(item => item.type === "Expense").reduce((sum, item) => sum + Number(item.amount), 0);
  const balance = income - expense;
  el.income.textContent = money.format(income); el.expense.textContent = money.format(expense); el.balance.textContent = money.format(balance);
  el.balanceNote.textContent = !items.length ? "Start by adding a transaction." : balance >= 0 ? "You are in the green this period." : "Spending is higher than income.";
}

function renderChart(items) {
  const totals = items.filter(item => item.type === "Expense").reduce((result, item) => ({ ...result, [item.category]: (result[item.category] || 0) + Number(item.amount) }), {});
  const entries = Object.entries(totals).sort((a, b) => b[1] - a[1]);
  if (!entries.length) { el.chart.innerHTML = '<p class="empty">No expenses in this period.</p>'; return; }
  const total = entries.reduce((sum, [, amount]) => sum + amount, 0);
  el.chart.innerHTML = `<p class="chart-kicker">TOTAL SPENT</p><p class="chart-total">${money.format(total)}</p>${entries.map(([category, amount], index) => `<div class="chart-row"><div class="chart-label"><span>${escapeHtml(category)}</span><span>${Math.round(amount / total * 100)}%</span></div><div class="track"><div class="bar" style="width:${amount / total * 100}%;background:${COLORS[index % COLORS.length]}"></div></div></div>`).join("")}`;
}

function renderList(items) {
  if (!items.length) { el.list.innerHTML = '<p class="empty">No transactions found for this period.</p>'; return; }
  const template = $("#transactionTemplate"); const fragment = document.createDocumentFragment();
  items.forEach(item => {
    const node = template.content.cloneNode(true); const row = node.querySelector(".transaction"); row.classList.toggle("income", item.type === "Income");
    node.querySelector(".transaction-description").textContent = item.description;
    node.querySelector(".transaction-meta").textContent = `${item.category} · ${item.payment_method || "Not specified"} · ${dateText.format(new Date(`${item.date}T12:00:00`))}`;
    node.querySelector(".transaction-value > strong").textContent = `${item.type === "Income" ? "+" : "−"} ${money.format(item.amount)}`;
    node.querySelector(".edit").addEventListener("click", () => startEdit(item.id));
    node.querySelector(".delete").addEventListener("click", () => remove(item.id));
    fragment.append(node);
  });
  el.list.replaceChildren(fragment);
}

function render() { const period = periodItems(); renderSummary(period); renderChart(period); renderList(visibleItems()); }
function resetForm() { editingId = null; el.form.reset(); el.type.value = "Expense"; el.payment.value = "PIX"; el.date.value = today(); el.installments.value = 1; setCategories(); toggleInstallments(); el.submit.textContent = "Add transaction"; el.formTitle.textContent = "New transaction"; el.cancel.classList.add("hidden"); }

function startEdit(transactionId) {
  const item = transactions.find(transaction => transaction.id === transactionId); if (!item) return;
  editingId = transactionId; el.type.value = item.type; setCategories(); el.category.value = item.category; el.payment.value = ["Cash", "PIX", "Debit card", "Credit card", "Meal voucher", "Bank transfer", "Other"].includes(item.payment_method) ? item.payment_method : "Other"; toggleInstallments(); el.installments.value = item.installments || 1; el.description.value = item.description; el.amount.value = item.amount; el.date.value = item.date; el.submit.textContent = "Save changes"; el.formTitle.textContent = "Edit transaction"; el.cancel.classList.remove("hidden"); window.scrollTo({ top: 0, behavior: "smooth" });
}

function remove(transactionId) { if (!confirm("Delete this transaction?")) return; transactions = transactions.filter(item => item.id !== transactionId); save(); if (editingId === transactionId) resetForm(); render(); }
function escapeHtml(value) { const div = document.createElement("div"); div.textContent = value; return div.innerHTML; }

el.form.addEventListener("submit", event => {
  event.preventDefault(); const amount = Number(el.amount.value); const installments = el.payment.value === "Credit card" ? Number(el.installments.value) : 1;
  if (!el.description.value.trim() || !amount || amount <= 0 || !el.date.value || !Number.isInteger(installments) || installments < 1 || installments > 48) { alert("Enter a description, valid date, amount, and 1 to 48 installments."); return; }
  const base = { type: el.type.value, description: el.description.value.trim(), amount, date: el.date.value, category: el.category.value, payment_method: el.payment.value };
  if (editingId) { const current = transactions.find(item => item.id === editingId); Object.assign(current, base); if (base.payment_method !== "Credit card") { current.installment = 1; current.installments = 1; } save(); resetForm(); render(); return; }
  const installmentAmount = Math.round(amount / installments * 100) / 100;
  for (let installment = 1; installment <= installments; installment += 1) { const currentAmount = installment < installments ? installmentAmount : Math.round((amount - installmentAmount * (installments - 1)) * 100) / 100; transactions.push({ id: id(), ...base, description: installments > 1 ? `${base.description} (${installment}/${installments})` : base.description, amount: currentAmount, date: addMonths(base.date, installment - 1), installment, installments }); }
  save(); resetForm(); render();
});

el.type.addEventListener("change", setCategories); el.payment.addEventListener("change", toggleInstallments); el.period.addEventListener("change", render); el.filter.addEventListener("change", render); el.cancel.addEventListener("click", () => resetForm());
el.exportButton.addEventListener("click", () => { const rows = [["Date", "Type", "Description", "Category", "Payment method", "Installment", "Amount"], ...periodItems().map(item => [item.date, item.type, item.description, item.category, item.payment_method || "Not specified", `${item.installment || 1}/${item.installments || 1}`, Number(item.amount).toFixed(2)])]; const csv = rows.map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(";")).join("\n"); const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" }); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `casheye-${el.period.value}.csv`; link.click(); URL.revokeObjectURL(link.href); });
el.importButton.addEventListener("click", () => el.importInput.click());
el.importInput.addEventListener("change", async event => { const file = event.target.files[0]; if (!file) return; try { const imported = JSON.parse(await file.text()); if (!Array.isArray(imported)) throw new Error(); const importedItems = imported.filter(item => item && item.id && item.date && item.type).map(item => ({ ...item, type: { Despesa: "Expense", Receita: "Income", Ganhos: "Income" }[item.type] || item.type, payment_method: item.payment_method || "Not specified", installment: item.installment || 1, installments: item.installments || 1 })); if (!confirm(`Import ${importedItems.length} transactions? This will replace the transactions stored in this browser.`)) return; transactions = importedItems; save(); resetForm(); render(); } catch { alert("This file could not be imported. Select a valid lancamentos.json file."); } finally { event.target.value = ""; } });

el.period.value = today().slice(0, 7); resetForm();
if ("serviceWorker" in navigator) window.addEventListener("load", () => navigator.serviceWorker.register("sw.js"));
