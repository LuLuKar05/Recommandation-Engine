import json
import os
from core.models import Book, User

class BookStore:
    def __init__(self, data_dir='data'):
        self.books_file = os.path.join(data_dir, 'books.json')
        self.users_file = os.path.join(data_dir, 'users.json')
        
        # 1. Main Data Containers
        self.books = {} 
        self.users = {}
        
        # 2. Optimization Structures
        self.book_subscribers = {} # Inverted Index {book_id: {user_ids}}
        self.co_occurrence_matrix = {} # Association Rules {book_id: {related_id: count}}
        
        self.load_data()

    def _add_to_index(self, user_id, book_id):
        """Updates the Inverted Index (User-Based CF)."""
        if book_id not in self.book_subscribers:
            self.book_subscribers[book_id] = set()
        self.book_subscribers[book_id].add(user_id)

    def _update_associations(self, user_history_set):
        """Updates the Co-occurrence Matrix (Association Rules)."""
        books = list(user_history_set)
        for i in range(len(books)):
            book_a = books[i]
            for j in range(i + 1, len(books)):
                book_b = books[j]
                
                # A -> B
                if book_a not in self.co_occurrence_matrix: self.co_occurrence_matrix[book_a] = {}
                self.co_occurrence_matrix[book_a][book_b] = self.co_occurrence_matrix[book_a].get(book_b, 0) + 1
                
                # B -> A
                if book_b not in self.co_occurrence_matrix: self.co_occurrence_matrix[book_b] = {}
                self.co_occurrence_matrix[book_b][book_a] = self.co_occurrence_matrix[book_b].get(book_a, 0) + 1

    def load_data(self):
        print("Loading System Data...")
        
        # A. Load Books
        if os.path.exists(self.books_file):
            with open(self.books_file, 'r') as f:
                book_list = json.load(f)
                for item in book_list:
                    new_book = Book(item['book_id'], item['title'], item['author'], item['genre'])
                    self.books[new_book.book_id] = new_book
        
        # B. Load Users & Build Indices
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                user_list = json.load(f)
                for item in user_list:
                    new_user = User(item['user_id'], item['name'])
                    for book_id in item['purchased_books']:
                        new_user.add_book(book_id)
                        self._add_to_index(new_user.user_id, book_id)
                    self.users[new_user.user_id] = new_user

        # C. Train Association Model
        print("Training Association Model...")
        self.co_occurrence_matrix = {}
        for user in self.users.values():
            if len(user.purchased_books) > 1:
                self._update_associations(user.purchased_books)

    def save_data(self):
        users_data = [u.to_dict() for u in self.users.values()]
        books_data = [b.to_dict() for b in self.books.values()]
        with open(self.users_file, 'w') as f: json.dump(users_data, f, indent=4)
        with open(self.books_file, 'w') as f: json.dump(books_data, f, indent=4)

    # --- ADMIN FUNCTIONS ---
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
            user = self.users[user_id]
            user.add_book(book_id)
            
            # Update RAM structures instantly
            self._add_to_index(user_id, book_id)
            self._update_associations(user.purchased_books)
            
            self.save_data()
            return True
        return False

    # --- ALGORITHMIC HELPERS ---
    def calculate_jaccard_similarity(self, user1, user2):
        set_a = user1.purchased_books
        set_b = user2.purchased_books
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return 0.0 if union == 0 else intersection / union

    def get_similar_items(self, target_book_id):
        """Item-Based CF: Finds books with similar subscriber sets."""
        if target_book_id not in self.book_subscribers: return []
        target_subs = self.book_subscribers[target_book_id]
        scores = []
        for other_id, other_subs in self.book_subscribers.items():
            if other_id == target_book_id: continue
            intersect = len(target_subs.intersection(other_subs))
            union = len(target_subs.union(other_subs))
            score = intersect / union if union > 0 else 0
            if score > 0: scores.append((other_id, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    # --- MASTER RECOMMENDATION ENGINE ---
    def recommend_books(self, target_user_id):
        if target_user_id not in self.users: return []
        target_user = self.users[target_user_id]
        results = []
        
        # Track IDs we've already recommended to avoid duplicates
        recommended_ids = set() 
        
        # === PHASE 1: USER-BASED COLLABORATIVE FILTERING (The Gold Standard) ===
        candidate_ids = set()
        for book_id in target_user.purchased_books:
            candidate_ids.update(self.book_subscribers.get(book_id, set()))
        candidate_ids.discard(target_user_id)
        
        scored_neighbors = []
        for nid in candidate_ids:
            neighbor = self.users[nid]
            score = self.calculate_jaccard_similarity(target_user, neighbor)
            if score > 0: scored_neighbors.append((neighbor, score))
        scored_neighbors.sort(key=lambda x: x[1], reverse=True)
        
        # Weighted Ranking
        book_scores = {}
        for neighbor, sim in scored_neighbors[:5]:
            new_books = neighbor.purchased_books - target_user.purchased_books
            shared = target_user.purchased_books.intersection(neighbor.purchased_books)
            reason_titles = {self.books[bid].title for bid in shared}
            
            for bid in new_books:
                if bid not in book_scores: book_scores[bid] = {'score': 0, 'reasons': set()}
                book_scores[bid]['score'] += sim
                book_scores[bid]['reasons'].update(reason_titles)

        sorted_ub_ids = sorted(book_scores.keys(), key=lambda k: book_scores[k]['score'], reverse=True)
        for bid in sorted_ub_ids[:5]:
            if bid in self.books:
                reasons = list(book_scores[bid]['reasons'])[:2]
                results.append({"book": self.books[bid], "reason": "Because you read " + " & ".join(reasons)})
                recommended_ids.add(bid)

        # === PHASE 2: ASSOCIATION RULE MINING (Market Basket) ===
        if len(results) < 5 and target_user.purchased_books:
            assoc_scores = {}
            for my_bid in target_user.purchased_books:
                if my_bid in self.co_occurrence_matrix:
                    for partner_id, count in self.co_occurrence_matrix[my_bid].items():
                        if partner_id not in target_user.purchased_books and partner_id not in recommended_ids:
                            if partner_id not in assoc_scores: assoc_scores[partner_id] = {'score': 0, 'trigger': ''}
                            assoc_scores[partner_id]['score'] += count
                            assoc_scores[partner_id]['trigger'] = self.books[my_bid].title
            
            sorted_assoc = sorted(assoc_scores.keys(), key=lambda k: assoc_scores[k]['score'], reverse=True)
            for bid in sorted_assoc[:3]:
                if len(results) >= 5: break
                results.append({"book": self.books[bid], "reason": f"Frequently bought with '{assoc_scores[bid]['trigger']}'"})
                recommended_ids.add(bid)

        # === PHASE 3: ITEM-BASED CF (Similar Reader Base) ===
        if len(results) < 5 and target_user.purchased_books:
            item_scores = {}
            for my_bid in target_user.purchased_books:
                twins = self.get_similar_items(my_bid)
                for twin_id, score in twins[:2]:
                    if twin_id not in target_user.purchased_books and twin_id not in recommended_ids:
                        if twin_id not in item_scores: item_scores[twin_id] = {'score': 0, 'trigger': ''}
                        if score > item_scores[twin_id]['score']:
                            item_scores[twin_id]['score'] = score
                            item_scores[twin_id]['trigger'] = self.books[my_bid].title
            
            sorted_items = sorted(item_scores.keys(), key=lambda k: item_scores[k]['score'], reverse=True)
            for bid in sorted_items[:3]:
                if len(results) >= 5: break
                results.append({"book": self.books[bid], "reason": f"Readers of '{item_scores[bid]['trigger']}' also read this"})
                recommended_ids.add(bid)

        # === PHASE 4: CONTENT-BASED (Fallback) ===
        if len(results) < 5 and target_user.purchased_books:
            liked_authors = {self.books[bid].author for bid in target_user.purchased_books if bid in self.books}
            for book in self.books.values():
                if len(results) >= 5: break
                if book.book_id not in target_user.purchased_books and book.book_id not in recommended_ids:
                    if book.author in liked_authors:
                        results.append({"book": book, "reason": f"From your favorite author {book.author}"})
                        recommended_ids.add(book.book_id)

        # === PHASE 5: GLOBAL POPULARITY (Cold Start) ===
        if not results:
            pop_map = {}
            for u in self.users.values():
                for pid in u.purchased_books: pop_map[pid] = pop_map.get(pid, 0) + 1
            sorted_pop = sorted(pop_map, key=pop_map.get, reverse=True)
            
            for bid in sorted_pop[:5]:
                if bid not in target_user.purchased_books:
                    results.append({"book": self.books[bid], "reason": "🔥 Trending Best Seller"})

        return results