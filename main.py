from flask import Flask, render_template, url_for, request, flash, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from dataSource.binanceData import get_all_binance_symbols,fetch_binance_ohlc
import datetime as dt
from collections import defaultdict
import asyncio
import json
import pandas as pd
from datetime import datetime
from flask_migrate import Migrate, upgrade, migrate, init, downgrade
from flask_migrate import Migrate, stamp, upgrade, migrate as _migrate
import sys
from analatics.functions import getPivots,getSwingBreaks,getGaps



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'kjaslkdfjasl;kdfjasl;kdflksadfjl;kasdf234243*&^*&'
db = SQLAlchemy(app)
chart={}
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

class TickerData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False)
    exchange = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)  # New column
    end_date = db.Column(db.DateTime, nullable=True)    # New column
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, 
                         default=db.func.current_timestamp(),
                         onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f"<TickerData {self.symbol} - {self.exchange}>"
    
    #     updated_record = db.Column(db.DateTime, default=dt.datetime.now, onupdate=dt.datetime.now)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), 
                         onupdate=db.func.current_timestamp())

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
    # Assuming get_all_yfinance_tickers() returns a Pandas DataFrame
   
    user = User.query.get(current_user.id)
    return render_template('home.html', user=user)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
     logout_user()
     flash('Logged out succesfully, please come back again.')
     return redirect(url_for('login'))

@app.route('/fetch-tickers', methods=['GET'])
@login_required
def fetch_tickers():
    asyncio.run(fetch_and_save_ticker_data())
    flash("Ticker data is being fetched and saved.")
    return redirect(url_for('home'))

async def fetch_and_save_ticker_data():
    # Fetch data asynchronously
    symbol_df = await asyncio.to_thread(get_all_binance_symbols)

    # Convert the DataFrame to a list of dictionaries
    symbol_data = symbol_df.to_dict('records')

    # Save data to the database
    for record in symbol_data:
     #    print(record)
        ticker = TickerData(
            symbol=record['Symbol'],
            exchange=record['Asset Class'],
            name=record.get('Name', None)
        )
        db.session.add(ticker)
    db.session.commit()
    print("Ticker data saved to the database.")

@app.route('/saved-tickers', methods=['GET'])
@login_required
def saved_tickers():
    # Retrieve all records from the database
    records = TickerData.query.all()
    
    # Check if there are any records
    if not records or len(records)==0:
        flash("No tickers found.", "info")  # Optional: Notify the user
        asyncio.run(fetch_and_save_ticker_data())
        print('records : \n',records)
        return render_template('saved_tickers.html', grouped_records={})  # Pass an empty dictionary

    # Group records by exchange
    grouped_records = defaultdict(list)
    for record in records:
        grouped_records[record.exchange].append({
            "id": record.id,
            "symbol": record.symbol,
            "name": record.name,
          #   "updated_at": record.updated_at
        })

    return render_template('saved_tickers.html', grouped_records=grouped_records)

@app.route('/tickDataForm', methods=['POST'])
@login_required
def tick_data_form():
    symbol = request.json.get('symbol')
    name = request.json.get('name')

    # Render a partial template for the form
    return render_template('tick_data_form.html', symbol=symbol, name=name)

@app.route('/swings',methods=['POST'])
@login_required
def getSwing():
    requestData = request.json.get('data')
    data = pd.DataFrame(requestData)

    swingData= getPivots(data)
    df = pd.DataFrame(swingData['data'])

    dfSwingHigh=df[df['isSwingHigh'].notna()][['index','startIndex','endIndex','isSwingHigh']]
    dfSwingHigh.rename(columns={'index': 'time', 'isSwingHigh': 'value'}, inplace=True)

    dfSwingLow=df[df['isSwingLow'].notna()][['index','startIndex','endIndex','isSwingLow']]
    dfSwingLow.rename(columns={'index': 'time', 'isSwingLow': 'value'}, inplace=True)

    resp={
        'swingHigh':dfSwingHigh.to_dict(orient='records'),
        'swingLow':dfSwingLow.to_dict(orient='records')
    }
    return jsonify(resp)

@app.route('/BOS',methods=['POST'])
@login_required
def getBOS():
    requestData = request.json.get('data')
    data = pd.DataFrame(requestData)

    breaks=getSwingBreaks(data)
    resp={
        "breakLow":breaks["data"]["breakLow"],
        "breakHigh":breaks["data"]["breakHigh"]
    }
    return jsonify(resp)

@app.route('/getGap',methods=['POST'])
@login_required
def getGap():
    requestData = request.json.get('data')
    data = pd.DataFrame(requestData)

    breaks=getGaps(data)
    resp={
        "gap":pd.DataFrame(breaks["data"]).to_dict(orient='records'),
    }
    return jsonify(resp)

def formatedata(data):
    # Format the data as needed
    df=data.copy()
    print(df.head())
    # df.columns = df.columns.droplevel(1)
    # df=df.rename(columns={
    #     'Price':'',
    # }).add_prefix('')
    # df = df.reset_index()
    df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
    candlestick_data = df
    # candlestick_data['time'] = pd.to_datetime(candlestick_data['time'])
    volume_data = candlestick_data[['volume']]
    # volume_data['time'] = pd.to_datetime(volume_data['time'])
    df = df.drop(columns=['volume'])  # Removes only the 'volume' column
    # print(df.head())
    # df.index = pd.to_datetime(df['time'])
    # df = df.drop(columns=['time'])
    return df

@app.route('/chart', methods=['GET'])
@login_required
def chart_view():
    symbol = request.args.get('symbol')
    requested_start = request.args.get('startDate')
    requested_end = request.args.get('endDate')

    # Convert string dates to datetime objects
    try:
        requested_start_date = datetime.strptime(requested_start, '%Y-%m-%d') if requested_start else None
        requested_end_date = datetime.strptime(requested_end, '%Y-%m-%d') if requested_end else None
    except ValueError as e:
        flash(f"Invalid date format: {str(e)}")
        return redirect(url_for('saved_tickers'))


    # Determine the actual dates we need to fetch
    fetch_start = requested_start_date
    fetch_end = requested_end_date

    print('startDate',fetch_start)
    print('endDate',fetch_end)
    try:
        # Fetch historical data for the expanded range
        data = fetch_binance_ohlc(symbol, fetch_start.strftime('%Y-%m-%d'), fetch_end.strftime('%Y-%m-%d'))
        
        if data.empty:
            flash(f"No data found for {symbol} in the given date range")
            return redirect(url_for('saved_tickers'))

        # Format the data
        formatted_data = formatedata(data)
        
        print(formatted_data.head())
        return render_template('chart.html', 
                            data=formatted_data.to_json(orient='records'), 
                            symbol=symbol,
                            start_date=requested_start_date.strftime('%Y-%m-%d') if requested_start_date else '',
                            end_date=requested_end_date.strftime('%Y-%m-%d') if requested_end_date else '')

    except Exception as e:
        flash(f"Error fetching data for {symbol}: {str(e)}")
        print(f"Error fetching data for {symbol}: {str(e)}")
        return redirect(url_for('saved_tickers'))

    
migrate = Migrate(app, db)

with app.app_context():
     db.create_all()

if __name__ == "__main__":
    with app.app_context():
        if len(sys.argv) > 1:
            if sys.argv[1] == 'init':
                if not os.path.exists('migrations'):
                    os.system('flask db init')
            elif sys.argv[1] == 'migrate':
                message = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'auto migration'
                _migrate(message=message)
            elif sys.argv[1] == 'upgrade':
                upgrade()
            elif sys.argv[1] == 'downgrade':
                downgrade()
            elif sys.argv[1] == 'stamp':
                stamp()
            else:
                app.run(debug=True)
        else:
            app.run(debug=True)