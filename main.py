from flask import Flask, render_template, url_for, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'kjaslkdfjasl;kdfjasl;kdflksadfjl;kasdf234243*&^*&'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(db.Model, UserMixin):
     id = db.Column(db.Integer(), primary_key=True)
     username = db.Column(db.String(50), unique=True, nullable=False)
     password = db.Column(db.String(500), nullable=False)

     def __repr__(self):
          return f'ID: {self.id}, Username: {self.username}'

class LoginForm(FlaskForm):
     username = StringField('Username', render_kw={'placeholder': 'Enter your username'})
     password = PasswordField('Password', render_kw={'placeholder': 'Enter your password'})
     submit = SubmitField('Login')

class RegisterForm(FlaskForm):
     username = StringField('Username', render_kw={'placeholder': 'Enter your username'})
     password = PasswordField('Password', render_kw={'placeholder': 'Enter your password'})
     password2 = PasswordField('Confirm Password', render_kw={'placeholder': 'Re-type your password'})
     submit = SubmitField('Sign up!')

@login_manager.user_loader
def load_user(user_id):
     return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
     form = LoginForm()

     if request.method == 'POST':
          username = request.form.get('username')
          password = request.form.get('password')
          user = User.query.filter_by(username=username).first()

          if user and check_password_hash(user.password, password):
               login_user(user)
               flash('Logged in succesfully')
               return redirect(url_for('home'))
          else:
               flash('Error logging in, make sure your credentials are correct.')
               return redirect(url_for('login'))

     return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
     form = RegisterForm()
     if request.method == "POST":
          username = request.form.get('username')
          password = request.form.get('password')
          password2 = request.form.get('password2')

          if password != password2:
               flash('Both passwords must be the same.')
               return redirect(url_for('register'))
          elif User.query.filter_by(username=username).first():
               flash('Username already taken, please choose another one.')
               return redirect(url_for('register'))
          else:
               hashed_password = generate_password_hash(password)
               new_user = User(username=username, password=hashed_password)
               db.session.add(new_user)
               db.session.commit()
               flash('User created, redirecting to the login page now.')
               return redirect(url_for('login'))

     return render_template('register.html', form=form)

@app.route('/home', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
     user = User.query.get(current_user.id)
     return render_template('home.html', user=user)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
     logout_user()
     flash('Logged out succesfully, please come back again.')
     return redirect(url_for('login'))

with app.app_context():
     db.create_all()

if __name__ == "__main__":
     app.run(debug=True)