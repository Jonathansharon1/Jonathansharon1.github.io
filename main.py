import stripe
import sqlalchemy.exc
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user

import datetime
import forms


# Set up Flask environment
app = Flask(__name__,
            static_url_path='',
            static_folder='public')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items1.db'
app.secret_key = 'my_very_secret'
# Set up Sqlalchemy
db = SQLAlchemy()
db.init_app(app)
# Bootstrap
Bootstrap(app)
# flask authentication
login_manager = LoginManager()
login_manager.init_app(app)

# working with stripe to process payments
stripe.api_key = 'sk_test_51KRLWaEIrWO1NqlcROQzhnNNHG22rprb0hCCNZ38s5qVkzPtqwfH29ANVvKfxqDB0QJhI7e9hRzTaUUCRBElXYi800P3ELYKhQ'


YOUR_DOMAIN = 'http://127.0.0.1:5000'


# loading users
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# The database of all the items
class Items1(db.Model):
    __tablename__ = 'items1'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True)
    price = db.Column(db.Integer)
    img_url = db.Column(db.String)
    quantity = db.Column(db.Integer, default=1)
    stripe_id = db.Column(db.Integer)
    comments = db.relationship('Comment', backref='item')


# The database of the items that added to cart
class CartItems(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    price = db.Column(db.Integer)
    img_url = db.Column(db.String)
    quantity = db.Column(db.Integer, default=1)
    # define to all the products stripe id's to work with the API
    stripe_id = db.Column(db.Integer)
    # user_id and user_cart give all users a different cart
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_cart = db.relationship('User', back_populates='cart_items')


# The database of the comments
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_comment = db.relationship('User', back_populates='comments')
    post_id = db.Column(db.Integer, db.ForeignKey('items1.id'))


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String)
    comments = db.relationship('Comment', backref='comment')
    cart_items = db.relationship('CartItems', backref='cart_items')

    # functions that are part from Flask-login
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


with app.app_context():
    db.create_all()



# CREATE RECORD
"""
with app.app_context():
    new_items = [Items1(title="Blue Tennis Shirt", price=120,
                      img_url="https://images.pexels.com/photos/1103828/"
                              "pexels-photo-1103828.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
                      stripe_id='price_1NQDFyEIrWO1NqlceeN2CLN0'),
                 Items1(title="The Classic One", price=199,
                        img_url="https://images.pexels.com/photos/3597042/pexels-photo-3597042.jpeg?auto=compress&cs=tinysrgb&w=600",
                        stripe_id='price_1NQXBcEIrWO1Nqlcz98opuGz'),
                 Items1(title="The Exclusive Beige Suit", price=349,
                        img_url="https://images.pexels.com/photos/10679218/pexels-photo-10679218.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
                        stripe_id='price_1NQXHGEIrWO1NqlcuC4HaGTG'),
                 ]
    #for item in new_items:
    #    db.session.add(item)
    #    db.session.commit()


"""
@app.route('/')
def home():
    all_items = Items1.query.all()
    return render_template("index.html", all_items=all_items)


@app.route("/about")
def about():
    return render_template("about.html")




@app.route("/contact", methods=['GET', 'POST'])
def contact():
#    if True:


    return render_template("contact.html")


@app.route("/item/<item_id>", methods=['GET', 'POST'])
def product(item_id):
    item = Items1.query.get(item_id)
    date = datetime.datetime.now().strftime('%d/%m/%Y')
    print(date)
    if request.method == 'POST':
        if current_user.is_authenticated:
            new_comment = Comment(
                text=request.form.get('user_comment'),
                user_id=current_user.get_id(),
                post_id=item_id,
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('product', item_id=item_id))
        else:
            flash('You need to be logged in to comment.')
            return redirect(url_for('login'))

    return render_template("product.html", item=item, date=date)



@app.route('/cart', methods=["GET", "POST"])
def cart():
    if request.method == "POST":
        quantity = request.form.get('quantity')
        item_id = request.form.get('the_id')
        new_quantity = CartItems.query.get(item_id)
        new_quantity.quantity = int(quantity)
        db.session.commit()

    # Get all the cart items for a specific User.
    cart_items = CartItems.query.filter_by(user_id=current_user.get_id()).all()
    total = 0

    for item in cart_items:
        price_qu = item.price * item.quantity
        total += price_qu
    return render_template("cart.html", items=cart_items, total_price=total)


@app.route('/add_to_cart', methods=["GET", "POST"])
def add_to_cart():
    if current_user.is_authenticated:
    # taking the id from the item that the customer enter on from the shop
        item_id = request.form.get('hidden_value')
    # taking the item from the ITEMS database and copy it to the cart database
        item = Items1.query.get(item_id)
        add_item = CartItems(title=item.title, price=item.price, img_url=item.img_url, stripe_id=item.stripe_id,
                            quantity=item.quantity, user_id=current_user.get_id())
        # This will check if we have another item in the same title for this user .
        check_unique = CartItems.query.filter_by(user_id=current_user.get_id()).all()
        trues = []
        for item in check_unique:
            if item.title != add_item.title:
                trues.append(True)
            else:
                trues.append(False)
        if all(trues):
            print(trues)
            #try:
            db.session.add(add_item)
            db.session.commit()
            #except sqlalchemy.exc.IntegrityError:
            #    return redirect("cart")

        return redirect("cart")
    else:
        flash('You need to be logged in to add to cart.')
        return redirect(url_for('login'))


@app.route('/remove/<int:item_id>', methods=["GET", "POST"])
def remove(item_id):
    delete_item = CartItems.query.get(item_id)
    db.session.delete(delete_item)
    db.session.commit()
    return redirect(url_for('cart'))


@app.route('/create-checkout-session', methods=["GET", "POST"])
def create_checkout_session():
    checkout_items = CartItems.query.all()

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': item.stripe_id,
                    'quantity': item.quantity,
                }
                for item in checkout_items

                ],
                mode='payment',
                success_url=YOUR_DOMAIN + '/success',
                cancel_url=YOUR_DOMAIN + '/cart',
            )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        if form.password.data == form.confirm_password.data:
            hashed_password = generate_password_hash(form.password.data, "pbkdf2:sha256", 8)
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=hashed_password,
            )
            user = User.query.filter_by(email=new_user.email).first()
            if not user:
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for("home"))
            else:
                flash('The user is already have an account. please, Log in.')
                return redirect(url_for('login'))
        else:
            flash('The passwords are unmatched. Try again.')
    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = forms.LoginForm()
    username = form.username.data
    password = form.password.data
    if request.method == "POST":
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("This UserName is not exist.")
            return redirect(url_for('login'))
        elif not check_password_hash(pwhash=user.password, password=password):
            flash("The password is not true. Please try again.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            print('hello')
            return redirect(url_for('home'))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
