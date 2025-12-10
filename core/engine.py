import json
import os
from collections import defaultdict
from core.models import Book, User

# --- DATA STRUCTURE: FP-NODE ---
class FPNode:
    def __init__(self, item, count, parent):
        self.item = item
        self.count = count
        self.parent = parent
        self.children = {}
        self.link = None

    def increment(self, count):
        self.count += count

class BookStore:
    def __init__(self, data_dir='data'):
        self.books_file = os.path.join(data_dir, 'books.json')
        self.users_file = os.path.join(data_dir, 'users.json')
        
        self.books = {} 
        self.users = {}
        self.book_subscribers = {} # Inverted Index
        
        # FP-GROWTH Structures
        self.frequent_itemsets = {} 
        self.min_support = 1  # Low support for demo purposes
        
        self.load_data()

    # --- HELPER: UPDATE INVERTED INDEX ---
    def _add_to_index(self, user_id, book_id):
        if book_id not in self.book_subscribers:
            self.book_subscribers[book_id] = set()
        self.book_subscribers[book_id].add(user_id)

    # --- ALGORITHM: FP-GROWTH ---
    def run_fpgrowth(self):
        """Builds the FP-Tree and mines frequent patterns."""
        # 1. Prepare Transactions
        transactions = []
        for user in self.users.values():
            if len(user.purchased_books) > 0:
                transactions.append(list(user.purchased_books))

        # 2. Count Frequencies
        item_counts = defaultdict(int)
        for trans in transactions:
            for item in trans:
                item_counts[item] += 1
        
        # Filter & Sort Headers
        headers = {}
        for item, count in item_counts.items():
            if count >= self.min_support:
                headers[item] = [count, None]

        if not headers: return

        # 3. Build Tree
        root = FPNode('Null', 1, None)
        
        for trans in transactions:
            local_items = {}
            for item in trans:
                if item in headers:
                    local_items[item] = headers[item][0]
            
            if local_items:
                ordered_items = [v[0] for v in sorted(local_items.items(), key=lambda p: p[1], reverse=True)]
                self._insert_tree(ordered_items, root, headers)

        # 4. Mine Tree
        self.frequent_itemsets = {}
        sorted_headers = sorted(headers.items(), key=lambda p: p[1][0])
        
        for item, node_data in sorted_headers:
            prefix_paths = self._find_prefix_paths(item, node_data[1])
            if prefix_paths:
                self.frequent_itemsets[item] = prefix_paths

    def _insert_tree(self, items, node, headers):
        first = items[0]
        child = node.children.get(first)
        if child:
            child.increment(1)
        else:
            child = FPNode(first, 1, node)
            node.children[first] = child
            if headers[first][1] is None:
                headers[first][1] = child
            else:
                current = headers[first][1]
                while current.link:
                    current = current.link
                current.link = child
        
        if len(items) > 1:
            self._insert_tree(items[1:], child, headers)

    def _find_prefix_paths(self, base_pat, tree_node):
        cond_pats = {}
        while tree_node:
            prefix_path = []
            self._ascend_tree(tree_node.parent, prefix_path)
            if len(prefix_path) > 0:
                for path_item in prefix_path:
                    cond_pats[path_item] = cond_pats.get(path_item, 0) + tree_node.count
            tree_node = tree_node.link
        return cond_pats

    def _ascend_tree(self, node, prefix_path):
        if node.parent:
            prefix_path.append(node.item)
            self._ascend_tree(node.parent, prefix_path)

    # --- STANDARD METHODS ---
    def load_data(self):
        print("Loading System Data...")
        if os.path.exists(self.books_file):
            with open(self.books_file, 'r') as f:
                for item in json.load(f):
                    b = Book(item['book_id'], item['title'], item['author'], item['genre'])
                    self.books[b.book_id] = b
        
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                for item in json.load(f):
                    u = User(item['user_id'], item['name'])
                    for bid in item['purchased_books']:
                        u.add_book(bid)
                        self._add_to_index(u.user_id, bid)
                    self.users[u.user_id] = u

        print("Building FP-Tree...")
        self.run_fpgrowth()

    def save_data(self):
        users_data = [u.to_dict() for u in self.users.values()]
        books_data = [b.to_dict() for b in self.books.values()]
        with open(self.users_file, 'w') as f: json.dump(users_data, f, indent=4)
        with open(self.books_file, 'w') as f: json.dump(books_data, f, indent=4)

    def register_user(self, name):
        new_id = max(self.users.keys(), default=100) + 1
        new_user = User(new_id, name)
        self.users[new_id] = new_user
        self.save_data()
        return new_id

    def add_book(self, title, author, genre):
        new_id = max(self.books.keys(), default=0) + 1
        new_book = Book(new_id, title, author, genre)
        self.books[new_id] = new_book
        self.save_data()
        return new_id

    def purchase_book(self, user_id, book_id):
        if user_id in self.users and book_id in self.books:
            self.users[user_id].add_book(book_id)
            self._add_to_index(user_id, book_id)
            self.save_data()
            self.run_fpgrowth()
            return True
        return False

    def calculate_jaccard_similarity(self, user1, user2):
        a, b = user1.purchased_books, user2.purchased_books
        return len(a & b) / len(a | b) if len(a | b) > 0 else 0

    # --- THE MISSING FUNCTION THAT CAUSED YOUR ERROR ---
    def recommend_books(self, target_user_id):
        if target_user_id not in self.users: return []
        target_user = self.users[target_user_id]
        results = []
        rec_ids = set()

        # 1. USER-BASED CF
        candidates = set()
        for bid in target_user.purchased_books:
            candidates.update(self.book_subscribers.get(bid, set()))
        candidates.discard(target_user_id)
        
        neighbors = []
        for nid in candidates:
            score = self.calculate_jaccard_similarity(target_user, self.users[nid])
            if score > 0: neighbors.append((self.users[nid], score))
        neighbors.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to top 2 neighbors to allow other algos to show
        for neighbor, score in neighbors[:2]:
            new_books = neighbor.purchased_books - target_user.purchased_books
            count = 0
            for bid in new_books:
                if bid not in rec_ids and count < 2:
                    results.append({"book": self.books[bid], "reason": "Because you read similar books", "algo": "User Similarity"})
                    rec_ids.add(bid)
                    count += 1

        # 2. FP-GROWTH
        if len(results) < 5 and target_user.purchased_books:
            fp_scores = {}
            for my_book in target_user.purchased_books:
                if my_book in self.frequent_itemsets:
                    related_items = self.frequent_itemsets[my_book]
                    for rel_id, count in related_items.items():
                        if rel_id not in target_user.purchased_books and rel_id not in rec_ids:
                            fp_scores[rel_id] = fp_scores.get(rel_id, 0) + count
            
            sorted_fp = sorted(fp_scores.items(), key=lambda x: x[1], reverse=True)
            for bid, score in sorted_fp[:2]:
                if len(results) >= 5: break
                results.append({"book": self.books[bid], "reason": "Found in Frequent Pattern Tree", "algo": "FP-Growth"})
                rec_ids.add(bid)

        # 3. POPULARITY FALLBACK
        if not results:
            pop = {}
            for u in self.users.values():
                for b in u.purchased_books: pop[b] = pop.get(b, 0) + 1
            sorted_pop = sorted(pop.items(), key=lambda x: x[1], reverse=True)
            for bid, _ in sorted_pop[:5]:
                if bid not in target_user.purchased_books:
                     results.append({"book": self.books[bid], "reason": "Trending", "algo": "Best Seller"})

        return results