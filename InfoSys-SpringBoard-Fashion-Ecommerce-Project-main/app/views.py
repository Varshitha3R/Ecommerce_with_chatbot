from flask import Blueprint, render_template, get_flashed_messages, redirect, url_for, Response, flash, request, session, jsonify
from flask_login import login_required, current_user
from .models import db, Wishlist,Order,CartItem,OrderItems, ProductRatings
from .forms import UpdateUserForm
from .decorators import is_delivery_person, is_admin
from .constants import STATES_CITY, PRODUCTS
bp = Blueprint('views', __name__)
from .models import Product, Order
import os
from datetime import datetime,timezone
import logging
from werkzeug.utils import secure_filename
from .methods import send_thankyou_email

OrderItem = OrderItems

@bp.route("/")
@bp.route('/home')
@login_required
def home():
    if current_user.isDeliveryPerson():
        return redirect(url_for('views.dashboard'))
    
    if current_user.isAdmin():
        return redirect(url_for('admin.index'))
    
    global PRODUCTS
    PRODUCTS = Product.query.all()
    return render_template('home.html', products=PRODUCTS)


@bp.route('/product/<int:product_id>')
@login_required
def product_details(product_id):
    product = Product.query.get(product_id)
    PRODUCTS = Product.query.all()
    if product is None:
        return "Product not found", 404
    similar_products = [_ for _ in PRODUCTS if ((_.category == product.category or _.type == product.type or _.target_user == product.target_user) and _.id != product.id) ]
    
    ratings = ProductRatings.query.filter_by(product_id=product_id).all()

    return render_template('product.html', product=product, similar_products=similar_products, ratings = ratings)


@bp.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    get_flashed_messages()
    form = UpdateUserForm(obj=current_user)  # Populate the form with the current user's data
    if form.state.data in STATES_CITY:
        form.city.choices = [(city, city) for city in STATES_CITY[form.state.data]]
    else:
        form.city.choices = []

    if request.method == 'POST' and form.validate_on_submit():
        try:
            current_user.firstname = form.firstname.data
            current_user.lastname = form.lastname.data
            current_user.address_line_1 = form.address_line_1.data
            current_user.state = form.state.data
            current_user.city = form.city.data
            current_user.role = form.role.data
            current_user.pincode = form.pincode.data

            db.session.commit()
            flash('Details updated successfully!', 'success')
            return redirect(url_for('views.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template(
        'update_user.html',
        form=form,
        STATES_CITY=STATES_CITY
    )


@bp.route('/auth_error')
def auth_error():
    return render_template('notAuthorized.html')


@bp.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    # Find the product 
    product = Product.query.get(product_id)

    if not product:
        # If product not found, flash an error message and redirect
        flash('Product not found', 'danger')
        return redirect(url_for('views.product_details', product_id=product_id))

    # Check if product already exists in wishlist
    existing_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if existing_item:
        # If product already in wishlist, flash a message and redirect
        flash('Product already in wishlist', 'info')
        return redirect(url_for('views.product_details', product_id=product_id))

    # Add the product to the wishlist
    wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
    db.session.add(wishlist_item)
    db.session.commit()

    # Flash success message and redirect
    flash('Product added to wishlist!', 'success')
    return redirect(url_for('views.product_details', product_id=product_id))


@bp.route('/wishlist')
@login_required
def view_wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    products_in_wishlist = []
    for item in wishlist_items:
        product = Product.query.get(item.product_id)
        if product:
            products_in_wishlist.append(product)

    return render_template('wishlist.html', products=products_in_wishlist)

@bp.route('/remove-from-wishlist/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash("Item removed from wishlist!", "success")
    else:
        flash("Item not found in wishlist.", "error")

    return redirect(url_for('views.view_wishlist'))


@bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if not current_user.is_authenticated:
        flash("Please log in to add items to the cart.", "warning")
        return redirect(url_for('auth.login'))

    # Get the product details
    product = Product.query.get(product_id)
    if not product:
        return "Product not found", 404

    # Check if the item already exists in the user's cart
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if cart_item:
        # If the product is already in the cart, update the quantity
        if cart_item.quantity < product.stock_quantity:
            cart_item.quantity += 1
        else:
            flash("Stock limit reached!", "warning")
    else:
        # Add new product to the cart
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    # flash("Product added to cart!", "success")
    return redirect(request.referrer)


@bp.route('/cart')
def cart():
    if not current_user.is_authenticated:
        flash("Please log in to view your cart.", "warning")
        return redirect(url_for('auth.login'))

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_amount = sum(item.quantity * item.product.price for item in cart_items)
    total_items = sum(item.quantity for item in cart_items)

    return render_template(
        'cart.html',
        cart_items=cart_items,
        total_price=total_amount,
        total_items=total_items
    )

@bp.route("/update_quantity/<int:product_id>", methods=["POST"])
@login_required
def update_quantity(product_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please log in to update your cart.'}), 403

    # Get the cart item for the user and product
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not cart_item:
        return jsonify({'success': False, 'message': 'Item not found in cart'}), 404

    try:
        new_quantity = int(request.json.get('quantity', 1))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid quantity'}), 400

    # Check if the new quantity exceeds stock
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    if new_quantity > product['stock']:
        return jsonify({'success': False, 'message': f'Stock limit reached. Maximum available: {product["stock"]}'}), 400

    # Update or delete the cart item
    if new_quantity < 1:
        db.session.delete(cart_item)
    else:
        cart_item.quantity = new_quantity

    db.session.commit()

    # Calculate total price and total items
    total_price = sum(item.quantity * next((p for p in PRODUCTS if p['id'] == item.product_id), {}).get('price', 0)
                      for item in CartItem.query.filter_by(user_id=current_user.id).all())
    total_items = sum(item.quantity for item in CartItem.query.filter_by(user_id=current_user.id).all())

    return jsonify({'success': True, 'new_quantity': cart_item.quantity, 'total_price': total_price, 'total_items': total_items})


@bp.route('/remove-from-cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    if not current_user.is_authenticated:
        flash("Please log in to modify your cart.", "warning")
        return redirect(url_for('auth.login'))

    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash("Item removed from cart!", "success")
    return redirect(url_for('views.cart'))


@bp.route('/search')
@login_required
def search():
    query = request.args.get('query', '').lower()  # Get the search query from the URL parameters
    query_words = query.split()  # Split the query into individual words

    PRODUCTS = Product.query.all()
    
    if query:
        results = []
        
        # Loop through each product and check if it matches the individual words or combined query
        for p in PRODUCTS:
            try:
                # Combine product attributes into one string for easier matching
                product_str = str(p.name).lower() + ' ' + str(p.description).lower() + ' ' + str(p.brand).lower() + ' ' + str(p.colour).lower() + ' ' + str(p.category).lower() + ' ' + str(p.target_user).lower() + ' ' + str(p.type).lower()
                
                # Check for exact matches for each word in the query
                individual_match = all(word in product_str.split() for word in query_words)
                
                # Check if the entire query (combined) exists in the product attributes (combined search)
                combined_match = query in product_str
                
                if individual_match or combined_match:
                    results.append(p)
            except Exception as e:
                print(f"Error processing product: {p}. Error: {e}")
                continue  # Skip any products that cause an error
                
    else:
        results = []  # No results if query is empty
    return render_template('search_results.html', query=query, results=results)


@bp.route('/category/<category>')
def category(category):
    PRODUCTS = Product.query.all()
    results = [p for p in PRODUCTS if p.category.lower() == category.lower()]
    return render_template('category_results.html', category=category.capitalize(), results=results)

@bp.route('/deliver')
@login_required
@is_delivery_person
def deliver():
    return Response("Delivered", status=200)

@bp.route('/partner_dash')
@login_required
@is_delivery_person
def dashboard():
     # Use current_user which represents the logged-in delivery person
    delivery_person = current_user
    pincode = delivery_person.pincode  # Get pincode from current_user

    # Fetch new orders that haven't been assigned (deliver_person is None) and match the pincode
    new_orders = Order.query.filter(Order.delivery_person_id.is_(None), Order.pincode == pincode, Order.status == "Pending").all()

    # Fetch orders assigned to this delivery person, 
    assigned_orders = Order.query.filter(Order.delivery_person_id == current_user.id, Order.status == 'Pending').all()

    # Fetch orders cancelled by this delivery person
    cancelled_orders = Order.query.filter(Order.delivery_person_id == current_user.id, Order.status == 'Cancelled').all()

    # Fetch delivered orders (status 'Delivered Successfully') for this delivery person
    delivered_orders = Order.query.filter(Order.delivery_person_id == current_user.id, Order.status == 'Delivered').all()

    return render_template('partner_home.html',
                           new_orders=new_orders,
                           assigned_orders=assigned_orders,
                           delivered_orders=delivered_orders,
                           cancelled_orders=cancelled_orders)


@bp.route('/update_status/<int:order_id>', methods=['POST'])
@is_delivery_person
def update_status(order_id):
    order = Order.query.filter_by(id = order_id).first()

    if order:
        new_status = request.form['status']
        order.status = new_status

        # If the order was not assigned (deliver_person is None), assign it to the current delivery person
        if order.delivery_person_id is None:
            order.delivery_person_id = current_user.id

        # Handle the case when the order is successfully delivered
        if order.status == 'Delivered':
            order.delivery_date = datetime.now(timezone.utc)
            # def send_thankyou_email(to_email, user_name, rating_url = None):
            send_thankyou_email(order_id)  # Send a thank you email
            # Move the order to the delivered orders section
            # Optionally, remove it from the assigned orders (this is handled by the dashboard query)

        # Commit the changes to the database
        db.session.commit()


    return redirect(url_for('views.dashboard'))  # Redirect back to the dashboard



@bp.route('/rate_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def rate_product(product_id):
    # Fetch the order using the order_id
    # order = Order.query.get_or_404(order_id)

    # Fetch the product associated with the order
    product = Product.query.get_or_404(product_id)
    
    order = OrderItems.query.filter(OrderItems.UserID == current_user.id, OrderItems.ProductID == product_id).first()

    if not order:
        return redirect(url_for('views.product_details', product_id=product_id))
        
    if request.method == 'POST':

        try:
            # Get the user's rating from the form (  is expected to be between 1 and 5)
            rating = request.form['rating']  # Assumes the form will send a 'rating' field as 1, 2, 3, 4, or 5
            description = request.form['description']

            Ratings = ProductRatings(current_user.id, product_id, float(rating), description)
            db.session.add(Ratings)

            customer_rating = int(rating)  # Convert rating to integer

            # Check if the product has already been rated
            if not product.rating or product.rating == 'not rated':  # Handles None or 'not rated'
                # If not rated yet, store the customer's rating
                product.rating = str(customer_rating)
            else:
                # If rated, calculate the new average rating
                current_rating = float(product.rating)
                new_rating = (current_rating + customer_rating) / 2
                product.rating = str(new_rating)

            # Commit the changes to the database
            db.session.commit()

            return redirect(url_for('views.home'))

        except Exception as e:
            db.session.rollback()
            print(f"Error occurred while rating the product: {e}")

    return render_template('rate_product.html', product=product)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('profile.html')


# Team 2 Merge

@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items_db = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items_db:
        flash('Your cart is empty!', 'danger')
        return redirect(url_for('views.cart'))

    # Fetch products and calculate costs from cart
    cart_items = []
    subtotal = 0
    for cart_item in cart_items_db:
        product = Product.query.get(cart_item.product_id)
        if product:
            cart_items.append({
                'id': cart_item.product_id,
                'name': product.name,
                'price': product.price,
                'quantity': cart_item.quantity
            })
            subtotal += product.price * cart_item.quantity

    shipping = 40
    tax = subtotal * 5/100  # 5% tax
    total = subtotal + shipping + tax

    # Pass data to the template
    return render_template(
        'checkout.html',
        cart_items=cart_items,
        subtotal=round(subtotal, 2),
        shipping=round(shipping, 2),
        tax=round(tax, 2),
        total=round(total, 2)
    )


@bp.route('/place_order', methods=['POST'])
@login_required
def place_order():
    user = current_user

    address_line_1 = request.form.get('address_line_1')
    state = request.form.get('state')
    city = request.form.get('city')
    pincode = request.form.get('pincode')
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    email = request.form.get('email')

    # Fetch the product ID and quantity from the cart
    cart_items_db = CartItem.query.filter_by(user_id=user.id).all()
    if not cart_items_db:
        flash('Your cart is empty!', 'danger')
        return redirect(url_for('views.checkout'))

    
    # Create a new order
    new_order = Order(customer_id=user.id, customer_name=firstname+" "+lastname, address_line_1=address_line_1, state=state, city=city, pincode=pincode, price=0, status="Pending", mail=email)
    db.session.add(new_order)
    db.session.commit()  # Commit order immediately to get order ID
    db.session.refresh(new_order)  # Refresh to get the latest order ID

    for cart_item in cart_items_db:
        # Fetch the product from the dummy data using product_id from the cart
        product = Product.query.get(cart_item.product_id)
        if not product:
            flash(f"Product with ID {cart_item.product_id} not found.", 'danger')
            continue

        # Calculate total cost for the product
        total_cost = product.price * cart_item.quantity


        new_order.price += total_cost

        # Create an OrderItem entry for this order
        order_item = OrderItem(OrderID=new_order.id, ProductID=cart_item.product_id, UserID=user.id, Quantity=cart_item.quantity, Price=total_cost)
        
        db.session.add(order_item)
        db.session.commit()  # Commit order item immediately
        db.session.refresh(order_item)  # Refresh order item

        #decrease the stock levels of the products
        
        product.stock_quantity -= cart_item.quantity

    # Clear the user's cart after order placement
    CartItem.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    # flash('Order(s) placed successfully and your cart has been emptied!', 'success')

    return jsonify({"success": True})


@bp.route('/my_orders')
@login_required
def my_orders():
    # Fetch all orders for the current user
    orders = db.session.query(Order).filter(Order.customer_id == current_user.id).all()

    # Create a structured data format for orders with their items
    orders_with_items = []
    for order in orders:
        order_items = OrderItem.query.filter_by(OrderID=order.id).all()
        items_data = [{'name': item.product.name, 'quantity': item.Quantity} for item in order_items]

        orders_with_items.append({
            'id': order.id,
            'status': order.status,
            'price': order.price,
            'order_items': items_data
        })

    return render_template('my_orders.html', orders=orders_with_items)

@bp.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        flash('You can only cancel your own orders.', 'danger')
        return redirect(url_for('views.my_orders'))

    # Update the order status to 'Cancelled'
    order.status = 'Cancelled'

    #increace the stock levels of the products
    order_items = OrderItem.query.filter_by(OrderID=order_id).all()
    for order_item in order_items:
        product = Product.query.get(order_item.ProductID)
        product.stock_quantity += order_item.Quantity

    db.session.commit()

    # flash('Order has been cancelled successfully.', 'success')
    return redirect(url_for('views.my_orders'))


@bp.route('/order/<int:order_id>')
@login_required
def view_order_items(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first()
    if not order:
        flash("Order not found or unauthorized access.", "danger")
        return redirect(url_for('views.my_orders'))
    
    order_items = OrderItem.query.filter_by(OrderID=order.id).all()
    return render_template('view_order_items.html', order=order, order_items=order_items)

@bp.route('/order/<int:order_id>/remove_item/<int:item_id>', methods=['POST'])
@login_required
def remove_order_item(order_id, item_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first()
    if not order:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('views.view_order_items', order_id=order_id))
    
    order_item = OrderItem.query.filter_by(OrderItemID=item_id, OrderID=order.id).first()
    if not order_item:
        flash("Item not found.", "danger")
        return redirect(url_for('views.view_order_items', order_id=order_id))
    
    # Increase stock quantity of the product
    product = Product.query.get(order_item.ProductID)
    if product:
        product.stock_quantity += order_item.Quantity
    
    db.session.delete(order_item)
    db.session.commit()

    #deleting the order if no items left
    if not OrderItem.query.filter_by(OrderID=order.id).all():
        db.session.delete(order)
        db.session.commit()
        return redirect(url_for('views.my_orders'))
    
    return redirect(url_for('views.view_order_items', order_id=order_id))

import openai  # This imports OpenAI's library, assuming you want to use GPT models.
import os
from flask import render_template, request, Blueprint, jsonify
from flask_login import login_required


# Set up your OpenAI API key (make sure it's correct)
# It's better to use environment variables to store API keys
openai.api_key = ''  # Replace with your actual API key
 # Recommended way to get the key from the environment

# @bp.route('/chatbot', methods=['GET', 'POST'])
# @login_required
# def chatbot():
#     if request.method == 'POST':
#         try:
#             # Log the incoming request data for debugging
#             data = request.get_json()
#             print("Received data:", data)  # Log the received data

#             if not data or 'message' not in data:
#                 return jsonify({"reply": "Please provide a valid message."}), 400  # 400 Bad Request
            
#             user_message = data['message']  # Extract the user's message from the JSON

#             # Set up the conversation context for e-commerce
#             response = openai.ChatCompletion.create(
#                 model="gpt-4",  # You can also use models like "gpt-3.5-turbo"
#                 messages=[
#                     {"role": "system", "content": 
#                         "You are a helpful assistant for an e-commerce website called 'StyleVerse'. You can answer questions about the store's products, pricing, shipping policies, and other services. "
#                         "For example, you can say things like: 'Tell me about the new arrivals', 'What is the shipping policy?', or 'How do I track my order?'. "
#                         "Please provide helpful and detailed answers regarding the e-commerce platform and products."},
#                     {"role": "user", "content": user_message}  # The user's question
#                 ]
#             )
            
#             # Extract the bot response from OpenAI's API response
#             bot_message = response['choices'][0]['message']['content'].strip()  # Extract the bot response
#             return jsonify({"reply": bot_message})  # Return bot's response as JSON

#         except openai.error.OpenAIError as e:
#             return jsonify({"reply": f"Error with OpenAI API: {e}"}), 500  # Internal Server Error
#         except Exception as e:
#             return jsonify({"reply": "An error occurred: " + str(e)}), 500  # Internal Server Error
    
#     # For GET requests, render the chatbot page with a default message
#     bot_message = "Welcome to the chatbot! Ask about our products or services."
#     return render_template('chatbot.html', bot_message=bot_message)  # Render the page with the message
# from flask import render_template, request, jsonify, Blueprint
# from flask_login import login_required
# import openai
# import os
# from models import Product  # Assuming you're using SQLAlchemy for database models

# # Ensure you have set the OpenAI API key
# openai.api_key = os.getenv('OPENAI_API_KEY')  # Set this in environment or hardcode for testing

from flask import render_template, request, jsonify, Blueprint
from flask_login import login_required
import openai
import os
from app.models import Product  # Assuming you're using SQLAlchemy for database models

# Ensure you have set the OpenAI API ke # Set this in environment or hardcode for testing

# @bp.route('/chatbot', methods=['GET', 'POST'])
# @login_required
# def chatbot():
#     if request.method == 'POST':
#         try:
#             data = request.get_json()
#             print("Received data:", data)

#             if not data or 'message' not in data:
#                 return jsonify({"reply": "Please provide a valid message."}), 400

#             user_message = data['message'].lower()  # Convert to lowercase for easier matching
#             wishlist_items = []
#             cart_items = []
#             orders=[]

#             # Check if the user is asking about their wishlist
#             if 'wishlist' in user_message:
#                 # Query the Wishlist table to get the user's wishlist
#                 wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()

#                 if wishlist_items:
#                     product_names = []
#                     for item in wishlist_items:
#                         product = Product.query.get(item.product_id)
#                         if product:
#                             product_names.append(f"{product.name} - ${product.price}")

#                     # Return the list of products in the wishlist
#                     return jsonify({"reply": "Your wishlist contains the following products:\n" + "\n".join(product_names)})
#                 else:
#                     return jsonify({"reply": "Your wishlist is currently empty."})

#             # Check if the user is asking about their cart
#             elif 'cart' in user_message or 'shopping cart' in user_message:
#                 # Query the CartItem table to get the user's cart items
#                 cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

#                 if cart_items:
#                     cart_details = []
#                     total_price = 0
#                     for item in cart_items:
#                         product = Product.query.get(item.product_id)
#                         if product:
#                             item_total_price = product.price * item.quantity
#                             total_price += item_total_price
#                             cart_details.append(f"{product.name} (x{item.quantity}) - ${product.price} each, Total: ${item_total_price}")
#                     cart_details.append(f"Total Cart Price: ${total_price}")
#                     return jsonify({"reply": "Your cart contains the following items:\n" + "\n".join(cart_details)})
#                 else:
#                     return jsonify({"reply": "Your cart is currently empty."})


#             # Check if the user is asking about a product
#             if 'product' in user_message or 'dress' in user_message or 'price' in user_message:
#                 # Try to match product name (basic search logic)
#                 product_name = extract_product_name(user_message)  # You need to implement a way to extract product names from message

#                 # Query the database for the product
#                 product = Product.query.filter(Product.name.ilike(f"%{product_name}%")).first()  # Assuming the product name contains the searched term

#                 if product:
#                     product_info = f"Product: {product.name}\nPrice: ${product.price}\nStock: {product.stock_quantity}\nDescription: {product.description}"
#                     return jsonify({"reply": product_info})
#                 else:
#                     return jsonify({"reply": "Sorry, I couldn't find any products matching your query."}), 404
                
#             elif 'order' in user_message or 'my orders' in user_message:
#                 # Query the Order table to get the user's orders
#                 orders = Order.query.filter_by(customer_id=current_user.id).all()

#                 if orders:
#                     order_details = []
#                     for order in orders:
#                         order_details.append(f"Order ID: {order.id}, Status: {order.status}, Price: ${order.price}, Order Date: {order.order_date}")
#                     return jsonify({"reply": "Your orders are as follows:\n" + "\n".join(order_details)})
#                 else:
#                     return jsonify({"reply": "You have no orders."})

#             # Check if the user is asking about shipping or tracking information
#             elif 'shipping' in user_message or 'track' in user_message:
#                 # Check if there are any orders
#                 orders = Order.query.filter_by(customer_id=current_user.id).all()
#                 if orders:
#                     order_tracking_details = []
#                     for order in orders:
#                         if order.delivery_date:
#                             order_tracking_details.append(f"Order ID: {order.id}, Delivery Date: {order.delivery_date}, Status: {order.status}")
#                         else:
#                             order_tracking_details.append(f"Order ID: {order.id}, Status: {order.status}, Delivery: Not yet dispatched.")
#                     return jsonify({"reply": "Shipping/Tracking details:\n" + "\n".join(order_tracking_details)})
#                 else:
#                     return jsonify({"reply": "You have no orders to track."})
#             else:
#                 # If the message isn't related to a product, use OpenAI to provide a general response
#                 response = openai.ChatCompletion.create(
#                     model="gpt-4o-mini",  # Use the GPT-4 model (adjust as needed)
#                     messages=[
#                         {"role": "system", "content": 
#                     "You are a helpful assistant for an e-commerce website called 'StyleVerse'. "
#                     "You can answer questions about the store's products, pricing, shipping policies, and other services. "
#                     "Provide responses that are clear and concise. Like the question Give me the order details. If asked about orders, wishlist, or cart, provide the details in bullet points. "
#                     "For example, 'Here are your orders: ...', 'Here are the items in your wishlist: ...', or 'Here are the items in your cart: ..."
#                     " If the user asks about how to place an order, respond with: 'To place an order on StyleVerse, go to http://127.0.0.1:5000, browse/select the item, add to cart, click on the cart icon in the top-right corner, review your cart, and checkout to enter shipping details and place the order.' If the user's question doesn't match any of the above topics, feel free to provide a general response related to e-commerce or the website."},

#                         {"role": "user", "content": user_message}  # The user's question
#                     ]
#                 )

#                 bot_reply = response['choices'][0]['message']['content']
#                 return jsonify({"reply": bot_reply})

#         except Exception as e:
#             return jsonify({"reply": "An error occurred: " + str(e)}), 500

#     # For GET requests, render the chatbot page with a default message
#     bot_message = "Welcome to the chatbot! Ask about our products or services."
#     return render_template('chatbot.html', bot_message=bot_message)


# def extract_product_name(message):
#     # This is a basic placeholder function, you can extend it to better match products.
#     keywords = ['dress', 'shirt', 'shoes', 'bag', 'accessory', 'jacket']  # Add more categories as needed
#     for keyword in keywords:
#         if keyword in message:
#             return keyword  # Return keyword as product name, you can improve this logic to match specific products.
#     return "unknown product"  # Return a default value if no match
SYSTEM_PROMPT = """
You are a helpful assistant for an e-commerce website called 'StyleVerse'.
You can answer questions about the store's products, pricing, shipping policies, and other services.
Please provide clear and concise responses.
- If the user asks about **order details**, respond with the order ID, status, price, order date, and delivery status in bullet points.
- If the user asks about **how to place an order**, respond with the following instructions:
  'To place an order on StyleVerse, go to http://127.0.0.1:5000/home , browse/select the item, add it to your cart, click on the cart icon, review your cart, and checkout to enter shipping details and place the order.'
- For any **wishlist** or **cart-related questions**, return information like product name, price, size, color, and quantity where applicable.
- If the user asks something else, provide a general response based on e-commerce or StyleVerse.
"""

@bp.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    if request.method == 'POST':
        try:
            data = request.get_json()  # Get the incoming JSON data from the client
            print("Received data:", data)

            if not data or 'message' not in data:
                return jsonify({"reply": "Please provide a valid message."}), 400

            user_message = data['message'].lower()  # Convert to lowercase for easier matching
            wishlist_items = []
            cart_items = []
            orders = []

            # Check if the user is asking about how to place an order
            if 'how to place order' in user_message or 'place an order' in user_message:
                order_instructions = """
                To place an order on StyleVerse, go to http://127.0.0.1:5000/home , browse/select the item, add it to your cart, click on the cart icon, review your cart, and checkout to enter shipping details and place the order.
                """
                return jsonify({"reply": order_instructions})

            # Check if the user is asking about their wishlist
            if 'wishlist' in user_message:
                wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()

                if wishlist_items:
                    product_names = []
                    for item in wishlist_items:
                        product = Product.query.get(item.product_id)
                        if product:
                            product_names.append(f"{product.name} - ${product.price}")

                    return jsonify({"reply": "Your wishlist contains the following products:\n" + "\n".join(product_names)})
                else:
                    return jsonify({"reply": "Your wishlist is currently empty."})

            # Check if the user is asking about their cart
            elif 'cart' in user_message or 'shopping cart' in user_message:
                cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

                if cart_items:
                    cart_details = []
                    total_price = 0
                    for item in cart_items:
                        product = Product.query.get(item.product_id)
                        if product:
                            item_total_price = product.price * item.quantity
                            total_price += item_total_price
                            cart_details.append(f"{product.name} (x{item.quantity}) - ${product.price} each, Total: ${item_total_price}")
                    cart_details.append(f"Total Cart Price: ${total_price}")
                    return jsonify({"reply": "Your cart contains the following items:\n" + "\n".join(cart_details)})
                else:
                    return jsonify({"reply": "Your cart is currently empty."})

            # Check if the user is asking about a product
            if 'product' in user_message or 'dress' in user_message or 'price' in user_message:
                product_name = extract_product_name(user_message)  # Implement a better matching function

                product = Product.query.filter(Product.name.ilike(f"%{product_name}%")).first()  # Basic search for product name

                if product:
                    product_info = f"Product: {product.name}\nPrice: ${product.price}\nStock: {product.stock_quantity}\nDescription: {product.description}"
                    return jsonify({"reply": product_info})
                else:
                    return jsonify({"reply": "Sorry, I couldn't find any products matching your query."}), 404

            # Handle user asking for order details (after excluding the "place order" case)
            elif 'my orders' in user_message or "orders" in user_message:
                orders = Order.query.filter_by(customer_id=current_user.id).all()

                if orders:
                    order_details = []
                    for order in orders:
                        order_details.append(f"Order ID: {order.id}, Status: {order.status}, Price: ${order.price}, Order Date: {order.order_date}")
                    return jsonify({"reply": "Your orders are as follows:\n" + "\n".join(order_details)})
                else:
                    return jsonify({"reply": "You have no orders."})

            # Check if the user is asking about shipping or tracking information
            elif 'shipping' in user_message or 'track' in user_message:
                orders = Order.query.filter_by(customer_id=current_user.id).all()
                if orders:
                    order_tracking_details = []
                    for order in orders:
                        if order.delivery_date:
                            order_tracking_details.append(f"Order ID: {order.id}, Delivery Date: {order.delivery_date}, Status: {order.status}")
                        else:
                            order_tracking_details.append(f"Order ID: {order.id}, Status: {order.status}, Delivery: Not yet dispatched.")
                    return jsonify({"reply": "Shipping/Tracking details:\n" + "\n".join(order_tracking_details)})
                else:
                    return jsonify({"reply": "You have no orders to track."})

            else:
                # If the message isn't related to a product, use OpenAI to provide a general response
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",  # Use the GPT-4 model (adjust as needed)
                    messages=[ 
                        {"role": "system", "content": SYSTEM_PROMPT},  # Use the defined SYSTEM_PROMPT here
                        {"role": "user", "content": user_message}  # The user's question
                    ]
                )

                bot_reply = response['choices'][0]['message']['content']
                return jsonify({"reply": bot_reply})

        except Exception as e:
            return jsonify({"reply": "An error occurred: " + str(e)}), 500

    # For GET requests, render the chatbot page with a default message
    bot_message = "Welcome to the chatbot! Ask about our products or services."
    return render_template('chatbot.html', bot_message=bot_message)


def extract_product_name(message):
    # This is a basic placeholder function, you can extend it to better match products.
    keywords = ['dress', 'shirt', 'shoes', 'bag', 'accessory', 'jacket']  # Add more categories as needed
    for keyword in keywords:
        if keyword in message:
            return keyword  # Return keyword as product name, you can improve this logic to match specific products.
    return "unknown product"  # Return a default value if no match