import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


import openpyxl

from database import (
    create_database, insert_default_users, check_user,
    add_product, get_products, update_product, delete_product,
    get_sales, get_sales_summary, record_sale, cancel_sale,
)

root = None
content_frame = None
current_user = ""
cart = {}

BG = "#f5f0e8"
CARD = "#ffffff"
PRIMARY = "#c9a96e"
PRIMARY_DARK = "#a8823d"
TEXT = "#2c2417"


def clear_content():
    for w in content_frame.winfo_children():
        w.destroy()


def clear_all():
    for w in root.winfo_children():
        w.destroy()


def show_login():
    global current_user, cart
    current_user = ""
    cart = {}
    clear_all()

    frame = tk.Frame(root, bg=BG)
    frame.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(frame, text="StockStyle",
             font=("Arial", 18, "bold"), bg=BG, fg=TEXT).pack(pady=(0, 20))

    tk.Label(frame, text="Username:", bg=BG, font=("Arial", 10)).pack(anchor="w")
    username_entry = tk.Entry(frame, font=("Arial", 11), width=25)
    username_entry.pack(pady=(0, 10))

    tk.Label(frame, text="Password:", bg=BG, font=("Arial", 10)).pack(anchor="w")
    password_entry = tk.Entry(frame, font=("Arial", 11), width=25, show="*")
    password_entry.pack(pady=(0, 15))

    def do_login():
        global current_user
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if username == "" or password == "":
            messagebox.showwarning("Warning", "Username and password cannot be empty!")
            return

        role = check_user(username, password)
        if role:
            current_user = username
            setup_main(role)
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    
    def enter_pressed(event):
        do_login()

    username_entry.bind("<Return>", enter_pressed)
    password_entry.bind("<Return>", enter_pressed)

    tk.Button(frame, text="Log in", command=do_login,
              font=("Arial", 11, "bold"), bg=PRIMARY, fg="white",
              width=20, pady=6).pack()


def setup_main(role):
    global content_frame
    clear_all()

    menu = tk.Frame(root, bg=PRIMARY)
    menu.pack(fill="x")

    tk.Label(menu, text="Welcome, " + current_user,
             font=("Arial", 10, "bold"), bg=PRIMARY, fg="white"
             ).pack(side="left", padx=10, pady=8)

    if role == "admin":
        pages = [
            ("Dashboard", show_dashboard),
            ("Products", show_manage_products),
            ("Sales", show_sales),
            ("Charts", show_charts),
            ("Export", show_export),
        ]
    else:
        pages = [
            ("Dashboard", show_dashboard),
            ("Products", show_products),
            ("Make a Sale", show_cart),
            ("My Sales", show_my_sales),
        ]

    for text, cmd in pages:
        tk.Button(menu, text=text, font=("Arial", 10, "bold"),
                  bg=PRIMARY_DARK, fg="white", bd=0, padx=12, pady=8,
                  command=cmd).pack(side="left", padx=1)

    tk.Button(menu, text="Logout", font=("Arial", 10, "bold"),
              bg="#e06464", fg="white", bd=0, padx=12, pady=8,
              command=show_login).pack(side="right", padx=10)

    content_frame = tk.Frame(root, bg=BG)
    content_frame.pack(fill="both", expand=True)

    show_dashboard()


def show_dashboard():
    clear_content()

    tk.Label(content_frame, text="Welcome, " + current_user.capitalize(),
             font=("Arial", 16, "bold"), bg=BG, fg=TEXT).pack(pady=(20, 10))

    total_rev, total_cnt, top_name, _ = get_sales_summary()
    products = get_products()

    info_text = "Total Products: " + str(len(products)) + "   |   "
    info_text += "Total Sales: " + str(total_cnt) + "   |   "
    info_text += "Revenue: " + str(round(total_rev, 2)) + " TL   |   "
    info_text += "Top Product: " + str(top_name)

    tk.Label(content_frame, text=info_text,
             font=("Arial", 11), bg=BG, fg=TEXT).pack(pady=10)

    tk.Label(content_frame, text="Recent Sales",
             font=("Arial", 12, "bold"), bg=BG, fg=TEXT
             ).pack(pady=(15, 5), anchor="w", padx=20)

    frame = tk.Frame(content_frame)
    frame.pack(fill="both", expand=True, padx=20, pady=5)

    cols = ["ID", "Product ID", "Qty", "Total (TL)", "Date", "Sold By"]
    widths = [60, 80, 60, 110, 180, 110]

    tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
    for i in range(len(cols)):
        tree.heading(cols[i], text=cols[i])
        tree.column(cols[i], anchor="center", width=widths[i])

    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    
    all_sales = get_sales()
    recent = all_sales[-15:]
    for s in recent:
        tree.insert("", tk.END, values=s)


def show_manage_products():
    clear_content()

    tk.Label(content_frame, text="Product Management",
             font=("Arial", 16, "bold"), bg=BG, fg=TEXT).pack(pady=15)

    form = tk.LabelFrame(content_frame, text="Add New Product",
                         font=("Arial", 10, "bold"), bg=BG, padx=10, pady=8)
    form.pack(padx=20, fill="x")

    tk.Label(form, text="Name:", bg=BG).grid(row=0, column=0, sticky="w", pady=6)
    name_e = tk.Entry(form, width=18)
    name_e.grid(row=0, column=1, padx=5)

    tk.Label(form, text="Category:", bg=BG).grid(row=0, column=2, sticky="w")
    cat_e = tk.Entry(form, width=14)
    cat_e.grid(row=0, column=3, padx=5)

    tk.Label(form, text="Price:", bg=BG).grid(row=0, column=4, sticky="w")
    price_e = tk.Entry(form, width=8)
    price_e.grid(row=0, column=5, padx=5)

    tk.Label(form, text="Stock:", bg=BG).grid(row=0, column=6, sticky="w")
    stock_e = tk.Entry(form, width=8)
    stock_e.grid(row=0, column=7, padx=5)

    table_frame = tk.Frame(content_frame)
    table_frame.pack(fill="both", expand=True, padx=20, pady=5)

    cols = ["ID", "Product Name", "Category", "Price (TL)", "Stock"]
    widths = [50, 200, 150, 100, 80]

    tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
    for i in range(len(cols)):
        tree.heading(cols[i], text=cols[i])
        tree.column(cols[i], anchor="center", width=widths[i])

    sb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def load():
        tree.delete(*tree.get_children())
        for p in get_products():
            tree.insert("", tk.END,
                        values=(p[0], p[1], p[2], round(p[3], 2), p[4]))

    def add_action():
        name = name_e.get().strip()
        if name == "":
            messagebox.showerror("Error", "Product name cannot be empty!")
            return

        try:
            if price_e.get().strip() == "":
                price = 0
            else:
                price = float(price_e.get().strip())

            if stock_e.get().strip() == "":
                stock = 0
            else:
                stock = int(stock_e.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Price and stock must be numbers!")
            return

        add_product(name, cat_e.get().strip(), price, stock)
        messagebox.showinfo("Success", '"' + name + '" added.')

        name_e.delete(0, tk.END)
        cat_e.delete(0, tk.END)
        price_e.delete(0, tk.END)
        stock_e.delete(0, tk.END)
        load()

    tk.Button(form, text="Add", command=add_action, bg="#6aaa64", fg="white",
              font=("Arial", 10, "bold")).grid(row=0, column=8, padx=10)

    load()

    def edit_action():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Warning", "Select a product to edit.")
            return

        vals = tree.item(sel, "values")
        pid = int(vals[0])

        dlg = tk.Toplevel(root)
        dlg.title("Edit Product")
        dlg.geometry("300x250")
        dlg.grab_set()

        tk.Label(dlg, text="Name:").grid(row=0, column=0, padx=15, pady=8, sticky="w")
        name_edit = tk.Entry(dlg, width=20)
        name_edit.insert(0, vals[1])
        name_edit.grid(row=0, column=1, padx=10)

        tk.Label(dlg, text="Category:").grid(row=1, column=0, padx=15, pady=8, sticky="w")
        cat_edit = tk.Entry(dlg, width=20)
        cat_edit.insert(0, vals[2])
        cat_edit.grid(row=1, column=1, padx=10)

        tk.Label(dlg, text="Price:").grid(row=2, column=0, padx=15, pady=8, sticky="w")
        price_edit = tk.Entry(dlg, width=20)
        price_edit.insert(0, vals[3])
        price_edit.grid(row=2, column=1, padx=10)

        tk.Label(dlg, text="Stock:").grid(row=3, column=0, padx=15, pady=8, sticky="w")
        stock_edit = tk.Entry(dlg, width=20)
        stock_edit.insert(0, vals[4])
        stock_edit.grid(row=3, column=1, padx=10)

        def save():
            try:
                update_product(pid, name_edit.get().strip(),
                               cat_edit.get().strip(),
                               float(price_edit.get()),
                               int(stock_edit.get()))
                dlg.destroy()
                load()
            except ValueError:
                messagebox.showerror("Error", "Price/stock must be numbers!")

        tk.Button(dlg, text="Save", command=save, bg=PRIMARY, fg="white",
                  font=("Arial", 10, "bold")).grid(
            row=4, column=0, columnspan=2, pady=15)

    def delete_action():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Warning", "Select a product to delete.")
            return

        vals = tree.item(sel, "values")
        if messagebox.askyesno("Confirm", 'Delete "' + vals[1] + '"?'):
            delete_product(int(vals[0]))
            load()

    btn_row = tk.Frame(content_frame, bg=BG)
    btn_row.pack(fill="x", padx=20, pady=5)

    tk.Button(btn_row, text="Edit", command=edit_action,
              bg="#e8a838", fg="white", font=("Arial", 10, "bold")
              ).pack(side="left", padx=5)
    tk.Button(btn_row, text="Delete", command=delete_action,
              bg="#e06464", fg="white", font=("Arial", 10, "bold")
              ).pack(side="left")


def show_sales():
    clear_content()

    tk.Label(content_frame, text="Sales",
             font=("Arial", 16, "bold"), bg=BG, fg=TEXT).pack(pady=15)

    total_rev, total_cnt, top_name, _ = get_sales_summary()

    info = "Revenue: " + str(round(total_rev, 2)) + " TL   |   "
    info += "Sales: " + str(total_cnt) + "   |   Top: " + str(top_name)

    tk.Label(content_frame, text=info,
             font=("Arial", 11), bg=BG, fg=TEXT).pack(pady=5)

    frame = tk.Frame(content_frame)
    frame.pack(fill="both", expand=True, padx=20, pady=5)

    cols = ["ID", "Product ID", "Qty", "Total (TL)", "Date", "Sold By"]
    widths = [60, 80, 60, 110, 180, 110]

    tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
    for i in range(len(cols)):
        tree.heading(cols[i], text=cols[i])
        tree.column(cols[i], anchor="center", width=widths[i])

    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def load():
        tree.delete(*tree.get_children())
        for s in get_sales():
            tree.insert("", tk.END, values=s)

    load()

    def cancel_action():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Warning", "Select a sale to cancel.")
            return

        vals = tree.item(sel, "values")
        if messagebox.askyesno("Confirm", "Cancel sale #" + str(vals[0]) + "?"):
            result = cancel_sale(int(vals[0]))
            if result == "Sale cancelled successfully":
                messagebox.showinfo("Done", "Sale cancelled.")
                load()
            else:
                messagebox.showerror("Error", result)

    tk.Button(content_frame, text="Cancel Selected Sale", command=cancel_action,
              bg="#e06464", fg="white", font=("Arial", 10, "bold")
              ).pack(padx=20, pady=5, anchor="w")


def show_charts():
    clear_content()

    tk.Label(content_frame, text="Charts",
             font=("Arial", 16, "bold"), bg=BG, fg=TEXT).pack(pady=15)

    products = get_products()
    all_sales = get_sales()

    if len(products) == 0:
        tk.Label(content_frame, text="No products yet.",
                 bg=BG, font=("Arial", 11)).pack(pady=30)
        return

    prod_names = []
    prod_stocks = []
    for p in products:
        name = p[1]
        if len(name) > 12:
            name = name[:12]
        prod_names.append(name)
        prod_stocks.append(p[4])

    cat_map = {}
    for p in products:
        category = p[2]
        if category is None or category == "":
            category = "Other"
        cat_map[p[0]] = category

    cat_rev = {}
    for s in all_sales:
        product_id = s[1]
        total_price = s[3]
        if product_id in cat_map:
            category = cat_map[product_id]
        else:
            category = "Other"

        if category in cat_rev:
            cat_rev[category] = cat_rev[category] + total_price
        else:
            cat_rev[category] = total_price

    fig = Figure(figsize=(10, 4), facecolor=CARD)

    ax1 = fig.add_subplot(1, 2, 1)
    ax1.bar(prod_names, prod_stocks, color=PRIMARY)
    ax1.set_title("Stock Levels")
    ax1.set_ylabel("Units")
    ax1.tick_params(axis="x", rotation=30, labelsize=8)

    ax2 = fig.add_subplot(1, 2, 2)
    if len(cat_rev) > 0:
        labels = list(cat_rev.keys())
        values = list(cat_rev.values())
        colors = ["#c9a96e", "#6aaa64", "#3b82f6", "#e8a838", "#e06464"]
        ax2.pie(values, labels=labels, autopct="%1.0f%%", colors=colors)
    else:
        ax2.text(0.5, 0.5, "No sales yet", ha="center", va="center")
    ax2.set_title("Revenue by Category")

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=content_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)


def show_export():
    clear_content()

    tk.Label(content_frame, text="Export Data",
             font=("Arial", 16, "bold"), bg=BG, fg=TEXT).pack(pady=15)

    frame = tk.Frame(content_frame, bg=BG)
    frame.pack(pady=20)

    def export_csv():
        folder = filedialog.askdirectory(title="Select folder")
        if not folder:
            return

        products_path = os.path.join(folder, "products.csv")
        f = open(products_path, "w", newline="", encoding="utf-8")
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Category", "Price", "Stock"])
        for p in get_products():
            writer.writerow(p)
        f.close()

        sales_path = os.path.join(folder, "sales.csv")
        f = open(sales_path, "w", newline="", encoding="utf-8")
        writer = csv.writer(f)
        writer.writerow(["Sale ID", "Product ID", "Qty", "Total", "Date", "Sold By"])
        for s in get_sales():
            writer.writerow(s)
        f.close()

        messagebox.showinfo("Done", "Files saved to:\n" + folder)

    def export_excel():
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")])
        if not path:
            return

        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "Products"
        ws1.append(["ID", "Name", "Category", "Price", "Stock"])
        for p in get_products():
            ws1.append(list(p))

        ws2 = wb.create_sheet("Sales")
        ws2.append(["Sale ID", "Product ID", "Qty", "Total", "Date", "Sold By"])
        for s in get_sales():
            ws2.append(list(s))

        wb.save(path)
        messagebox.showinfo("Done", "Saved to:\n" + path)

    tk.Button(frame, text="Export as CSV", command=export_csv,
              font=("Arial", 12, "bold"), bg=PRIMARY, fg="white",
              width=20, pady=8).pack(pady=10)

    tk.Button(frame, text="Export as Excel", command=export_excel,
              font=("Arial", 12, "bold"), bg="#6aaa64", fg="white",
              width=20, pady=8).pack(pady=10)


def show_products():
    clear_content()

    tk.Label(content_frame, text="Products",
             font=("Arial", 16, "bold"), bg=BG, fg=TEXT).pack(pady=15)

    frame = tk.Frame(content_frame)
    frame.pack(fill="both", expand=True, padx=20, pady=5)

    cols = ["ID", "Product Name", "Category", "Price (TL)", "Stock"]
    widths = [60, 220, 150, 110, 80]

    tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
    for i in range(len(cols)):
        tree.heading(cols[i], text=cols[i])
        tree.column(cols[i], anchor="center", width=widths[i])

    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    for p in get_products():
        tree.insert("", tk.END,
                    values=(p[0], p[1], p[2], round(p[3], 2), p[4]))


def show_cart():
    global cart
    clear_content()

    tk.Label(content_frame, text="Make a Sale",
             font=("Arial", 16, "bold"), bg=BG, fg=TEXT).pack(pady=10)

    outer = tk.Frame(content_frame, bg=BG)
    outer.pack(fill="both", expand=True, padx=20)

    left = tk.Frame(outer, bg=BG)
    left.pack(side="left", fill="both", expand=True, padx=(0, 10))

    tk.Label(left, text="Products", font=("Arial", 11, "bold"), bg=BG
             ).pack(anchor="w")

    pf = tk.Frame(left)
    pf.pack(fill="both", expand=True)

    prod_cols = ["ID", "Name", "Price (TL)", "Stock"]
    prod_widths = [50, 200, 100, 70]

    prod_tree = ttk.Treeview(pf, columns=prod_cols, show="headings", height=14)
    for i in range(len(prod_cols)):
        prod_tree.heading(prod_cols[i], text=prod_cols[i])
        prod_tree.column(prod_cols[i], anchor="center", width=prod_widths[i])

    sb = ttk.Scrollbar(pf, orient="vertical", command=prod_tree.yview)
    prod_tree.configure(yscrollcommand=sb.set)
    prod_tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def load_products():
        prod_tree.delete(*prod_tree.get_children())
        for p in get_products():
            prod_tree.insert("", tk.END,
                             values=(p[0], p[1], round(p[3], 2), p[4]))

    load_products()

    right = tk.Frame(outer, bg=BG, width=280)
    right.pack(side="right", fill="y")

    tk.Label(right, text="Cart", font=("Arial", 11, "bold"), bg=BG
             ).pack(anchor="w")

    cart_list = tk.Listbox(right, font=("Arial", 10), height=14, width=35)
    cart_list.pack(fill="both", expand=True, pady=5)

    total_label = tk.Label(right, text="Total: 0.00 TL",
                           font=("Arial", 12, "bold"), bg=BG)
    total_label.pack(pady=5)

    def refresh_cart():
        cart_list.delete(0, tk.END)
        total = 0.0
        for pid in cart:
            item = cart[pid]
            subtotal = item["price"] * item["qty"]
            total = total + subtotal
            line = item["name"] + " x" + str(item["qty"]) + " = " + str(round(subtotal, 2)) + " TL"
            cart_list.insert(tk.END, line)
        total_label.config(text="Total: " + str(round(total, 2)) + " TL")

    def add_to_cart():
        sel = prod_tree.focus()
        if not sel:
            messagebox.showwarning("Warning", "Select a product.")
            return

        vals = prod_tree.item(sel, "values")
        pid = int(vals[0])

        current = None
        for p in get_products():
            if p[0] == pid:
                current = p
                break

        if current is None:
            return

        if pid in cart:
            if cart[pid]["qty"] >= current[4]:
                messagebox.showwarning("Stock", "Not enough stock!")
                return
            cart[pid]["qty"] = cart[pid]["qty"] + 1
        else:
            if current[4] < 1:
                messagebox.showwarning("Stock", "Out of stock!")
                return
            cart[pid] = {"name": current[1], "price": current[3], "qty": 1}

        refresh_cart()

    def remove_from_cart():
        sel = cart_list.curselection()
        if not sel:
            return

        keys = list(cart.keys())
        pid = keys[sel[0]]
        del cart[pid]
        refresh_cart()

    def complete_sale():
        global cart
        if len(cart) == 0:
            messagebox.showwarning("Warning", "Cart is empty!")
            return

        errors = []
        done = []

        cart_items = list(cart.items())
        for pid, item in cart_items:
            result = record_sale(pid, item["qty"], sold_by=current_user)
            if result == "Sale recorded successfully":
                done.append(pid)
            else:
                errors.append(item["name"] + ": " + result)

        for pid in done:
            del cart[pid]

        if len(errors) > 0:
            messagebox.showerror("Error", "\n".join(errors))
        else:
            messagebox.showinfo("Success", "Sale completed!")

        refresh_cart()
        load_products()

    def clear_cart_action():
        global cart
        cart = {}
        refresh_cart()

    tk.Button(left, text="Add to Cart", command=add_to_cart,
              bg="#6aaa64", fg="white", font=("Arial", 10, "bold")
              ).pack(pady=5)

    btn_frame = tk.Frame(right, bg=BG)
    btn_frame.pack(fill="x")

    tk.Button(btn_frame, text="Remove", command=remove_from_cart,
              bg="#e8a838", fg="white", font=("Arial", 10, "bold")
              ).pack(fill="x", pady=2)
    tk.Button(btn_frame, text="Complete Sale", command=complete_sale,
              bg="#6aaa64", fg="white", font=("Arial", 10, "bold")
              ).pack(fill="x", pady=2)
    tk.Button(btn_frame, text="Clear Cart", command=clear_cart_action,
              bg="#e06464", fg="white", font=("Arial", 10, "bold")
              ).pack(fill="x", pady=2)

    refresh_cart()


def show_my_sales():
    clear_content()

    tk.Label(content_frame, text="My Sales",
             font=("Arial", 16, "bold"), bg=BG, fg=TEXT).pack(pady=15)

    all_sales = get_sales()
    my_sales = []
    for s in all_sales:
        if s[5] == current_user:
            my_sales.append(s)

    total_rev = 0
    for s in my_sales:
        total_rev = total_rev + s[3]

    info = "Total: " + str(len(my_sales)) + " sales   |   "
    info += "Revenue: " + str(round(total_rev, 2)) + " TL"

    tk.Label(content_frame, text=info,
             font=("Arial", 11), bg=BG, fg=TEXT).pack(pady=5)

    frame = tk.Frame(content_frame)
    frame.pack(fill="both", expand=True, padx=20, pady=5)

    cols = ["ID", "Product ID", "Qty", "Total (TL)", "Date"]
    widths = [60, 80, 70, 120, 200]

    tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
    for i in range(len(cols)):
        tree.heading(cols[i], text=cols[i])
        tree.column(cols[i], anchor="center", width=widths[i])

    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    for s in my_sales:
        tree.insert("", tk.END,
                    values=(s[0], s[1], s[2], round(s[3], 2), s[4]))

if __name__ == "__main__":
    create_database()
    insert_default_users()

    root = tk.Tk()
    root.title("StockStyle")
    root.geometry("1000x650")
    root.minsize(800, 500)
    root.configure(bg=BG)

    show_login()
    root.mainloop()
