import os
from flask import Flask, render_template, request, redirect, url_for
from core.engine import BookStore

app = Flask(__name__)

# --- CONFIGURATION ---
# 1. Get the folder where app.py is located
base_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Build the exact path to the 'data' folder
data_path = os.path.join(base_dir, 'data')
print(f"DEBUG: Looking for data in -> {data_path}")

# 3. Initialize the Engine
store = BookStore(data_dir=data_path)


# --- ROUTES ---

@app.route('/')
def index():
    """
    Home Page: Shows the 'Select Persona' screen.
    """
    # We convert values() to a list so the HTML can loop through it
    users_list = list(store.users.values())
    return render_template('index.html', users=users_list)


@app.route('/user/<int:user_id>')
def user_profile(user_id):
    """
    Profile Page: The Main Dashboard.
    Running the Recommendation Engine ON LOAD (Amazon Style).
    """
    user = store.users.get(user_id)
    if not user:
        return "User not found", 404

    # 1. Get My History (Book Objects)
    my_books = []
    for book_id in user.purchased_books:
        if book_id in store.books:
            my_books.append(store.books[book_id])

    # 2. Run the Algorithm (The Bottleneck happens here!)
    #    It calculates matches instantly so they are ready for the view.
    recommendations = store.recommend_books(user_id)

    # 3. Prepare the Catalog (Exclude books I already bought)
    catalog = []
    for book in store.books.values():
        if book.book_id not in user.purchased_books:
            catalog.append(book)

    return render_template('user_profile.html', 
                           user=user, 
                           my_books=my_books, 
                           recommendations=recommendations, # Passing the AI results
                           catalog=catalog)


@app.route('/buy/<int:user_id>/<int:book_id>')
def buy_book(user_id, book_id):
    """
    Action Route: Processes a buy and redirects immediately.
    """
    store.purchase_book(user_id, book_id)
    
    # Redirect back to the profile so the page refreshes 
    # and the recommendations update based on the new purchase.
    return redirect(url_for('user_profile', user_id=user_id))


if __name__ == '__main__':
    app.run(debug=True)