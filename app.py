import os
from flask import Flask, render_template, request, redirect, url_for
from core.engine import BookStore

app = Flask(__name__)
base_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_dir, 'data')
print(f"DEBUG: Looking for data in {data_path}")


# Initialize the Engine
# Ensure you have the 'data' folder with books.json and users.json
store = BookStore(data_dir=data_path)

@app.route('/')
def index():
    """Homepage: Lists all users to select who you want to be."""
    users = store.users.values()
    return render_template('index.html', users=users)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    """User Profile: Shows purchase history and a shop to buy more."""
    user = store.users.get(user_id)
    if not user:
        return "User not found", 404

    # Get the actual Book Objects for the IDs in user's history
    my_books = []
    for book_id in user.purchased_books:
        if book_id in store.books:
            my_books.append(store.books[book_id])

    # Get all books (for the 'Shop' section)
    all_books = store.books.values()

    return render_template('user_profile.html', 
                           user=user, 
                           my_books=my_books, 
                           all_books=all_books)

@app.route('/recommend/<int:user_id>')
def recommend(user_id):
    """The Logic Page: Runs the Jaccard Algorithm and shows results."""
    user = store.users.get(user_id)
    
    # CALL THE ENGINE
    recommendations = store.recommend_books(user_id)
    
    return render_template('recommend.html', user=user, recommendations=recommendations)

@app.route('/buy/<int:user_id>/<int:book_id>')
def buy_book(user_id, book_id):
    """Action Route: Processes a purchase and redirects back to profile."""
    success = store.purchase_book(user_id, book_id)
    if success:
        print(f"User {user_id} bought Book {book_id}")
    return redirect(url_for('user_profile', user_id=user_id))

if __name__ == '__main__':
    app.run(debug=True)