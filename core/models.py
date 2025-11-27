# core/models.py

class Book:
    """Represents a book in the store."""
    def __init__(self, book_id, title, author, genre):
        self.book_id = int(book_id)
        self.title = title
        self.author = author
        self.genre = genre

    def to_dict(self):
        """Converts object to dictionary for JSON storage/HTML display."""
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "genre": self.genre
        }

class User:
    """Represents a user and their reading history."""
    def __init__(self, user_id, name):
        self.user_id = int(user_id)
        self.name = name
        # The 'Set' is crucial for Jaccard Similarity (Fast Math)
        self.purchased_books = set() 

    def add_book(self, book_id):
        """Adds a book ID to the user's history."""
        self.purchased_books.add(int(book_id))

    def to_dict(self):
        """Converts object to dictionary (Sets become Lists here)."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "purchased_books": list(self.purchased_books)
        }