from flask import render_template, Blueprint, flash, request, redirect, url_for
from models import User, Product, Transaction
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, logout_user, current_user
from utils import role_required
from datetime import datetime

routes_bp = Blueprint("routes", __name__, template_folder="templates")

@routes_bp.route("/")
def home():
    return "Hello hi"

@routes_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!")
            return redirect(url_for("routes.dashboard"))
        else:
            flash("Invalid username or password!")
            return redirect(url_for("routes.login"))
    else:
        return render_template("login.html")

@routes_bp.route("/register", methods=['GET', 'POST'])
@login_required
@role_required("admin")
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "staff")

        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            flash("Username already exists!")
            return redirect(url_for("routes.register"))
        
        new_user = User(
            fullname=fullname,
            username=username,password=generate_password_hash(password),
            role=role
            )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully!")
        return redirect(url_for("routes.register"))
    else:
        return render_template("register.html")
    

@routes_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out!")
    return redirect(url_for("routes.login"))

@routes_bp.route("/dashboard")
@login_required
def dashboard():
    total_products = Product.query.count()
    stock_value = db.session.query(db.func.sum(Product.purchase_price * Product.quantity)).scalar() or 0
    revenue = db.session.query(db.func.sum(Product.selling_price * Product.quantity)).scalar() or 0
    transactions_today = Transaction.query.filter(
        db.func.date(Transaction.timestamp) == datetime.now().date()
    ).count()

    recent_transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(5).all()

    low_stock = Product.query.filter(Product.quantity < 5).all()

    return render_template("dashboard.html",
        total_products=total_products,
        stock_value=stock_value,
        revenue=revenue,
        transactions_today=transactions_today,
        recent_transactions=recent_transactions,
        low_stock=low_stock
    )

@routes_bp.route("/getusers")
@login_required
@role_required("admin")
def get_users():
    users = User.query.all()
    return render_template("users.html", users=users)

@routes_bp.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(user_id):
    user = db.session.get(User, user_id)

    if user.id == current_user.id:
        flash("You cannot delete your own account!", "warning")
        return redirect(url_for("routes.get_users"))

    if user:
        new_transaction = Transaction(
            user = current_user,
            change_type = f"DEL_USER_{user.id}"
            )
        db.session.add(new_transaction)
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully", "success")
    else:
        flash("User not found", "danger")
    return redirect(url_for("routes.get_users"))

@routes_bp.route("/add_product", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager")
def add_product():
    if request.method == "POST":
        name = request.form.get("p_name")
        sku = request.form.get("sku")
        category = request.form.get("category")
        buy_price = request.form.get("buy_price")
        sell_price = request.form.get("sell_price")
        quantity = request.form.get("quantity")

        existing_prod = Product.query.filter_by(sku=sku).first()
        
        if existing_prod:
            flash("Product already exists!")
            return redirect(url_for("routes.add_product"))
        
        new_product = Product(
            name=name, sku=sku, category=category, 
            purchase_price=buy_price, selling_price=sell_price, quantity=quantity
            )

        new_transaction = Transaction(
            product = new_product,
            user = current_user,
            change_type = "NEW_PROD",
            purchase_price=buy_price, selling_price=sell_price, quantity=quantity
        )

        db.session.add(new_product)
        db.session.add(new_transaction)
        db.session.commit()
        flash("Product created successfully!")
        return redirect(url_for("routes.add_product"))
    else:
        return render_template("add_product.html")
    
@routes_bp.route("/update_product", methods=["GET","POST"])
@login_required
@role_required("admin", "manager")
def update_product():
    if request.method == "POST":
        product_id = request.form.get("id")
        action = request.form.get("action")

        product = Product.query.get(product_id)

        if action == "update":
            product.name = request.form.get("name")
            product.category = request.form.get("category")
            product.purchase_price = request.form.get("purchase_price")
            product.selling_price = request.form.get("selling_price")
            product.quantity = request.form.get("quantity")

            new_transaction = Transaction(
                product = product,
                user = current_user,
                change_type = "UPD_PROD",
                purchase_price=product.purchase_price, 
                selling_price=product.selling_price, 
                quantity=product.quantity
            )
            db.session.add(new_transaction)
            db.session.commit()
            flash("Product updated successfully!")

        elif action == "delete":
            new_transaction = Transaction(
                product_id = product_id,
                user = current_user,
                change_type = "DEL_PROD",
                purchase_price=product.purchase_price, 
                selling_price=product.selling_price, 
                quantity=product.quantity
            )
            db.session.add(new_transaction)

            db.session.delete(product)
            db.session.commit()
            flash("Product deleted successfully!")

        return redirect(url_for("routes.update_product"))

    products = Product.query.all()
    return render_template("update_product.html", products=products)


@routes_bp.route("/update_stock", methods=["GET","POST"])
@login_required
@role_required("admin", "manager", "staff")
def update_stock():
    if request.method == "POST":
        product_id = request.form.get("id")
        action = request.form.get("action")

        if action == "update":
            product = Product.query.get(product_id)
            product.quantity = request.form.get("quantity")

            new_transaction = Transaction(
                product = product,
                user = current_user,
                change_type = "UPD_STCK",
                purchase_price=product.purchase_price, 
                selling_price=product.selling_price, 
                quantity=product.quantity
            )
            db.session.add(new_transaction)

            db.session.commit()
            flash("Stock updated successfully")
        else:
            flash("Invalid Action")

        return redirect(url_for("routes.update_stock"))
    else:
        products = Product.query.all()
        return render_template("update_stock.html", products=products)