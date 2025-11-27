# core/engine.py
import json
import os
from core.models import Book, User

class BookStore:
    def __init__(self, data_dir='data'):
        # Dynamic paths based on where the app runs
        self.books_file = os.path.join(data_dir, 'books.json')
        self.users_file = os.path.join(data_dir, 'users.json')
        
        self.books = {} # {book_id: BookObj}
        self.users = {} # {user_id: UserObj}
        
        # THE INVERTED INDEX (Optimization)
        self.book_subscribers = {} # {book_id: {user_id, user_id...}}

        self.load_data()

    def _add_to_index(self, user_id, book_id):
        """Helper to safely update the Inverted Index."""
        if book_id not in self.book_subscribers:
            self.book_subscribers[book_id] = set()
        self.book_subscribers[book_id].add(user_id)

    def load_data(self):
        # A. Load Books
        if os.path.exists(self.books_file):
            with open(self.books_file, 'r') as f:
                book_list = json.load(f)
                for item in book_list:
                    new_book = Book(item['book_id'], item['title'], item['author'], item['genre'])
                    self.books[new_book.book_id] = new_book
        
        # B. Load Users & Build Index
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                user_list = json.load(f)
                for item in user_list:
                    new_user = User(item['user_id'], item['name'])
                    for book_id in item['purchased_books']:
                        new_user.add_book(book_id)
                        self._add_to_index(new_user.user_id, book_id)
                    self.users[new_user.user_id] = new_user

    def save_data(self):
        """Writes current state back to JSON."""
        # Save Users (Convert Sets back to Lists)
        users_data = [u.to_dict() for u in self.users.values()]
        
        # Save Books (In case we added new ones)
        books_data = [b.to_dict() for b in self.books.values()]

        with open(self.users_file, 'w') as f:
            json.dump(users_data, f, indent=4)
        
        with open(self.books_file, 'w') as f:
            json.dump(books_data, f, indent=4)

    def calculate_jaccard_similarity(self, user1, user2):
        set_a = user1.purchased_books
        set_b = user2.purchased_books
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return 0.0 if union == 0 else intersection / union

    def recommend_books(self, target_user_id):
        if target_user_id not in self.users: return []

        target_user = self.users[target_user_id]
        
        # --- STEP 1: Candidate Generation (Inverted Index) ---
        candidate_ids = set()
        for book_id in target_user.purchased_books:
            similar_readers = self.book_subscribers.get(book_id, set())
            candidate_ids.update(similar_readers)
        
        candidate_ids.discard(target_user_id)
        
        # --- STEP 2: Scoring Neighbors (Jaccard) ---
        scored_neighbors = []
        for neighbor_id in candidate_ids:
            neighbor = self.users[neighbor_id]
            score = self.calculate_jaccard_similarity(target_user, neighbor)
            if score > 0:
                scored_neighbors.append((neighbor, score))
        
        # Sort neighbors by similarity (Highest first)
        scored_neighbors.sort(key=lambda x: x[1], reverse=True)
        
        # --- STEP 3: Book Scoring (The "Weighted Ranking" Fix) ---
        # We look at the Top 5 neighbors (The "Committee")
        top_k = 5
        book_scores = {} # {book_id: total_score}

        for neighbor, sim_score in scored_neighbors[:top_k]:
            # Find books this neighbor read that Target has NOT read
            new_books = neighbor.purchased_books - target_user.purchased_books
            
            for book_id in new_books:
                # The score of the book is the sum of the similarity scores
                # of everyone who suggested it.
                if book_id not in book_scores:
                    book_scores[book_id] = 0
                book_scores[book_id] += sim_score

        # --- STEP 4: Final Sorting & Extraction ---
        # Sort books by their calculated score (Most recommended first)
        sorted_book_ids = sorted(book_scores.keys(), key=lambda bid: book_scores[bid], reverse=True)
        
        results = []
        for bid in sorted_book_ids:
            if bid in self.books:
                results.append(self.books[bid])
                
        return results

    def purchase_book(self, user_id, book_id):
        if user_id in self.users and book_id in self.books:
            user = self.users[user_id]
            user.add_book(book_id)
            self._add_to_index(user_id, book_id)
            self.save_data()
            return True
        return False