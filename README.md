Here’s the updated `README.md` in your preferred style, now **including the chatbot integration (StyleVerseBot)** while keeping everything clean and without emojis:

---

# InfoSys-SpringBoard Interns Fashion-Ecommerce-Project

## Project Overview  
This project is a **Fashion E-Commerce Website**, designed as part of my internship project. It is a fully functional e-commerce platform with core features such as product browsing, user authentication, shopping cart management, order processing, and admin analytics. The theme of the website is centered around fashion, offering users a seamless and engaging shopping experience. It also includes **StyleVerseBot**, an integrated AI-powered chatbot to assist users throughout their shopping experience.

---

## Technologies Used

- **Python**: Backend development.  
- **Flask**: Web framework to build the web application.  
- **SQLAlchemy**: ORM (Object-Relational Mapping) for managing database with SQLite.  
- **SQLite3**: Database for storing user and product information.  
- **HTML/CSS**: For frontend pages.  
- **JavaScript**: For dynamic page elements and client-side validation.  
- **Matplotlib**: For admin analytics and visualizations.  
- **OpenAI API**: For AI chatbot responses using GPT models.

---

## Setup Instructions

1. Clone the repository:  
   ```bash  
   git clone https://github.com/ShudarsanRegmi/InfoSys-SpringBoard-Fashion-Ecommerce-Project.git
   cd InfoSys-SpringBoard-Fashion-Ecommerce-Project
   ```  

2. **Initialize and Migrate the Database**:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

3. **(Optional) Downgrade the Database**  
   ```bash 
   flask db downgrade
   ```

4. **Run the Application**  
   ```bash  
   python app.py  
   ```

5. Open your browser and navigate to:  
   ```
   http://localhost:5000  
   ```

---

## Features  

### User Features  
- **Home Page:** Displays featured and trending fashion items.  
- **Product Catalog:** Filter and search for products by category, size, and price.  
- **Product Details:** Detailed descriptions, multiple images, and reviews.  
- **Shopping Cart:** Add, update, and remove items before checkout.  
- **Order Processing:** Secure checkout and order confirmation.  
- **StyleVerseBot Chatbot:** AI assistant to help with product queries, order status, and shopping suggestions.  

### Admin Features  
- **Inventory Management:** Add, update, and delete products.  
- **Order Tracking:** View and manage user orders.  
- **Sales Analytics:** Visualizations using Matplotlib for sales trends and inventory analysis.  

---

## Chatbot Integration: StyleVerseBot  

**Route:** `/chatbot`  
The chatbot is implemented using OpenAI’s GPT API and is available on a dedicated route. It simulates a virtual shopping assistant to help users with:

- Product inquiries  
- Availability and price checks  
- Shopping cart and wishlist summaries  
- Order tracking and status  
- General store-related questions  

### Technologies Used  
- **Flask Routing**  
- **OpenAI API (gpt-4o-mini)**  
- **JavaScript (AJAX) for real-time interaction**

---

## Tech Stack  

### Frontend  
- HTML  
- CSS  
- JavaScript  

### Backend  
- Python (Flask Framework)  

### Database  
- SQLite (via SQLAlchemy ORM)  

### Data Visualization  
- Matplotlib  

### AI Integration  
- OpenAI (GPT API)

---

## Installation  

### Prerequisites  
Ensure Python 3.x is installed along with required libraries.

### Steps  
1. Clone the repository:  
   ```bash  
   git clone https://github.com/ShudarsanRegmi/InfoSys-SpringBoard-Fashion-Ecommerce-Project.git
   cd InfoSys-SpringBoard-Fashion-Ecommerce-Project
   ```  

2. Install dependencies:  
   ```bash  
   pip install -r requirements.txt  
   ```  

3. Run the application:  
   ```bash  
   python app.py  
   ```  

4. Open in browser:  
   ```
   http://localhost:5000  
   ```

---

## Usage  

1. **Browse Products:** Explore the catalog and view product details.  
2. **Add to Cart:** Add items to the shopping cart.  
3. **Checkout:** Complete the checkout process securely.  
4. **Use Chatbot:** Visit `/chatbot` and interact with StyleVerseBot for help.  
5. **Admin Dashboard:** Manage inventory and view analytics.

---

## Project Screenshots  
Screenshots will be added soon.

---

## Future Enhancements  

- User profiles with order history  
- AI-powered product recommendations  
- Third-party payment gateway integration  
- Discount and coupon functionality  
- Chatbot integration within product and cart pages  


---

## Acknowledgments  
- **Infosys SpringBoard** for the opportunity  
- **Mentors and Guides** for consistent support  
- **Flask and OpenAI** for extensive documentation  
- **MDN and Matplotlib** for reference materials

---
