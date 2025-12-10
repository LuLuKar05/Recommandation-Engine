import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from core.engine import BookStore

# --- COLOR PALETTE (Modern Data Science Theme) ---
COLORS = {
    "bg_dark": "#2C3E50",       # Sidebar Background
    "bg_light": "#ECF0F1",      # Main Content Background
    "card_bg": "#FFFFFF",       # White Cards
    "primary": "#3498DB",       # Blue (Buttons/Headers)
    "accent1": "#E74C3C",       # Red (Actions)
    "accent2": "#8E44AD",       # Purple (Stats)
    "accent3": "#27AE60",       # Green (Success)
    "text_dark": "#2C3E50",     # Main Text
    "text_light": "#BDC3C7"     # Muted Text
}

class ModernBookstoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 InsightEngine | Recommendation Analytics")
        self.root.geometry("1200x800")
        self.root.configure(bg=COLORS["bg_light"])
        
        # Initialize Logic
        self.store = BookStore()
        self.current_user = None
        
        # Setup Styling
        self.setup_styles()
        
        # Create Layout (Sidebar + Main Area)
        self.create_layout()
        
        # Start at Login
        self.render_login_view()

    def setup_styles(self):
        """Configures the look and feel (CSS for Python)"""
        style = ttk.Style()
        style.theme_use('clam') # Best base for custom coloring

        # Treeview (Data Tables)
        style.configure("Treeview", 
                        background="white", 
                        foreground=COLORS["text_dark"], 
                        rowheight=30, 
                        fieldbackground="white",
                        font=('Segoe UI', 10))
        
        style.configure("Treeview.Heading", 
                        font=('Segoe UI', 10, 'bold'), 
                        background=COLORS["bg_dark"], 
                        foreground="white")
        
        style.map("Treeview", background=[('selected', COLORS["primary"])])

        # Frames
        style.configure("Card.TFrame", background=COLORS["card_bg"], relief="flat")
        style.configure("Sidebar.TFrame", background=COLORS["bg_dark"])
        style.configure("Main.TFrame", background=COLORS["bg_light"])

        # Labels
        style.configure("H1.TLabel", font=('Segoe UI', 24, 'bold'), background=COLORS["bg_light"], foreground=COLORS["text_dark"])
        style.configure("H2.TLabel", font=('Segoe UI', 16, 'bold'), background=COLORS["card_bg"], foreground=COLORS["text_dark"])
        style.configure("Stat.TLabel", font=('Segoe UI', 12), background=COLORS["card_bg"], foreground=COLORS["text_light"])
        style.configure("StatValue.TLabel", font=('Segoe UI', 22, 'bold'), background=COLORS["card_bg"], foreground=COLORS["primary"])

    def create_layout(self):
        """Creates the 2-column layout"""
        # 1. Sidebar (Left)
        self.sidebar = ttk.Frame(self.root, width=250, style="Sidebar.TFrame")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False) # Stop it from shrinking

        # App Logo / Title in Sidebar
        lbl_logo = tk.Label(self.sidebar, text="Insight\nEngine", bg=COLORS["bg_dark"], fg="white", font=('Segoe UI', 20, 'bold'), pady=20)
        lbl_logo.pack(fill="x")

        # Navigation Buttons Container
        self.nav_frame = tk.Frame(self.sidebar, bg=COLORS["bg_dark"])
        self.nav_frame.pack(fill="x", pady=20)

        # 2. Main Content Area (Right)
        self.main_area = ttk.Frame(self.root, style="Main.TFrame")
        self.main_area.pack(side="right", fill="both", expand=True)

    def create_nav_btn(self, text, command, active=False):
        """Helper to make pretty sidebar buttons"""
        bg_color = COLORS["primary"] if active else COLORS["bg_dark"]
        btn = tk.Button(self.nav_frame, text=f"  {text}", command=command,
                        bg=bg_color, fg="white", font=('Segoe UI', 11),
                        bd=0, anchor="w", padx=20, pady=10, cursor="hand2")
        btn.pack(fill="x", pady=2)

    def clear_main_area(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()
        for widget in self.nav_frame.winfo_children():
            widget.destroy()

    # ==========================================
    # VIEW 1: LOGIN (The "Data Overview" Screen)
    # ==========================================
    def render_login_view(self):
        self.clear_main_area()
        self.create_nav_btn("User Database", self.render_login_view, active=True)
        self.create_nav_btn("Exit System", self.root.quit)

        # Header
        header = ttk.Frame(self.main_area, style="Main.TFrame")
        header.pack(fill="x", padx=40, pady=30)
        ttk.Label(header, text="User Database", style="H1.TLabel").pack(side="left")
        
        # Add User Button (Modern Pill Shape)
        tk.Button(header, text="+ New User", bg=COLORS["accent3"], fg="white", 
                  font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=10, 
                  command=self.add_user_popup).pack(side="right")

        # KPI Cards Row
        kpi_frame = ttk.Frame(self.main_area, style="Main.TFrame")
        kpi_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        # Calculate Stats
        total_users = len(self.store.users)
        total_books = len(self.store.books)
        total_read = sum(len(u.purchased_books) for u in self.store.users.values())

        self.create_stat_card(kpi_frame, "Total Users", str(total_users), COLORS["primary"])
        self.create_stat_card(kpi_frame, "Book Catalog", str(total_books), COLORS["accent2"])
        self.create_stat_card(kpi_frame, "Interactions", str(total_read), COLORS["accent3"])

        # Data Table
        table_frame = ttk.Frame(self.main_area, style="Card.TFrame", padding=1)
        table_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        cols = ('ID', 'Name', 'Books Read', 'Action')
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=15)
        
        tree.heading('ID', text='ID')
        tree.heading('Name', text='Full Name')
        tree.heading('Books Read', text='History Size')
        tree.heading('Action', text='Status')
        
        tree.column('ID', width=50, anchor='center')
        tree.column('Name', width=200)
        tree.column('Books Read', width=100, anchor='center')
        tree.column('Action', width=100, anchor='center')

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        # Populate
        for user in self.store.users.values():
            tree.insert("", "end", values=(user.user_id, user.name, len(user.purchased_books), "Select ➤"))

        # Bind Click
        def on_select(event):
            selected = tree.selection()
            if selected:
                item = tree.item(selected[0])
                uid = item['values'][0]
                self.current_user = self.store.users[uid]
                self.render_dashboard_view()

        tree.bind("<Double-1>", on_select)

    def create_stat_card(self, parent, title, value, color):
        """Creates a colorful KPI card"""
        card = tk.Frame(parent, bg="white", highlightbackground="#E0E0E0", highlightthickness=1)
        card.pack(side="left", fill="x", expand=True, padx=10, ipady=10)
        
        # Color Strip
        tk.Frame(card, bg=color, height=5).pack(fill="x", side="top")
        
        tk.Label(card, text=title, font=("Segoe UI", 10), fg="#7F8C8D", bg="white").pack(anchor="w", padx=20, pady=(15,0))
        tk.Label(card, text=value, font=("Segoe UI", 24, "bold"), fg=COLORS["text_dark"], bg="white").pack(anchor="w", padx=20, pady=(5,15))

    # ==========================================
    # VIEW 2: USER DASHBOARD (Analytics View)
    # ==========================================
    def render_dashboard_view(self):
        self.clear_main_area()
        # Sidebar Navigation
        self.create_nav_btn("← Back to Users", lambda: (setattr(self, 'current_user', None), self.render_login_view()))
        self.create_nav_btn(f"{self.current_user.name}", self.render_dashboard_view, active=True)
        self.create_nav_btn("Add Book (Admin)", self.add_book_popup)

        # Header
        header = ttk.Frame(self.main_area, style="Main.TFrame")
        header.pack(fill="x", padx=40, pady=30)
        ttk.Label(header, text=f"Analysis: {self.current_user.name}", style="H1.TLabel").pack(side="left")

        # Two Column Layout
        content = ttk.Frame(self.main_area, style="Main.TFrame")
        content.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        # LEFT COLUMN: Recommendations
        left_col = ttk.Frame(content, style="Main.TFrame")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # Title + Refresh
        rec_header = tk.Frame(left_col, bg=COLORS["bg_light"])
        rec_header.pack(fill="x", pady=(0, 10))
        tk.Label(rec_header, text="Recommendations", font=("Segoe UI", 14, "bold"), bg=COLORS["bg_light"], fg=COLORS["text_dark"]).pack(side="left")
        
        # Recommendation Table
        self.rec_tree = ttk.Treeview(left_col, columns=('Title', 'Reason'), show='headings', height=10)
        self.rec_tree.heading('Title', text='Recommended Book')
        self.rec_tree.heading('Reason', text='Algorithm Logic')
        self.rec_tree.column('Title', width=200)
        self.rec_tree.column('Reason', width=300)
        self.rec_tree.pack(fill="both", expand=True)

        # RIGHT COLUMN: Catalog
        right_col = ttk.Frame(content, style="Main.TFrame")
        right_col.pack(side="right", fill="both", expand=True)

        cat_header = tk.Frame(right_col, bg=COLORS["bg_light"])
        cat_header.pack(fill="x", pady=(0, 10))
        tk.Label(cat_header, text="Purchase Catalog", font=("Segoe UI", 14, "bold"), bg=COLORS["bg_light"], fg=COLORS["text_dark"]).pack(side="left")
        
        self.cat_tree = ttk.Treeview(right_col, columns=('ID', 'Title', 'Genre'), show='headings', height=10)
        self.cat_tree.heading('ID', text='ID')
        self.cat_tree.heading('Title', text='Title')
        self.cat_tree.heading('Genre', text='Genre')
        self.cat_tree.column('ID', width=40)
        self.cat_tree.pack(fill="both", expand=True)
        self.cat_tree.bind("<Double-1>", self.on_buy_book)

        # Load Data
        self.refresh_dashboard_data()

    def refresh_dashboard_data(self):
        # 1. Load Recs
        for i in self.rec_tree.get_children(): self.rec_tree.delete(i)
        
        recs = self.store.recommend_books(self.current_user.user_id)
        for item in recs:
            # We combine Book title and Algo type for clarity
            title = f"{item['book'].title} ({item['book'].genre})"
            logic = f"[{item.get('algo', 'AI')}] {item['reason']}"
            self.rec_tree.insert("", "end", values=(title, logic))

        # 2. Load Catalog
        for i in self.cat_tree.get_children(): self.cat_tree.delete(i)
        
        for b in self.store.books.values():
            if b.book_id not in self.current_user.purchased_books:
                self.cat_tree.insert("", "end", values=(b.book_id, b.title, b.genre))

    # ==========================================
    # ACTIONS & POPUPS
    # ==========================================
    def on_buy_book(self, event):
        selected = self.cat_tree.selection()
        if not selected: return
        
        item = self.cat_tree.item(selected[0])
        book_id = item['values'][0]
        title = item['values'][1]
        
        if messagebox.askyesno("Purchase", f"Add '{title}' to history?"):
            self.store.purchase_book(self.current_user.user_id, book_id)
            self.refresh_dashboard_data()

    def add_user_popup(self):
        name = simpledialog.askstring("New User", "Enter Name:")
        if name:
            self.store.register_user(name)
            self.render_login_view()

    def add_book_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Admin: Add Book")
        popup.geometry("400x300")
        popup.configure(bg="white")

        def entry(lbl):
            tk.Label(popup, text=lbl, bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(10,0))
            e = ttk.Entry(popup, width=40)
            e.pack(padx=20, pady=5)
            return e

        e_t = entry("Book Title")
        e_a = entry("Author")
        e_g = entry("Genre")

        def save():
            if e_t.get():
                self.store.add_book(e_t.get(), e_a.get(), e_g.get())
                self.refresh_dashboard_data()
                popup.destroy()
                
        tk.Button(popup, text="Save to Database", bg=COLORS["primary"], fg="white", 
                  bd=0, padx=20, pady=10, command=save).pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernBookstoreApp(root)
    root.mainloop()