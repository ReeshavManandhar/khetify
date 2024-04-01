from flask import Flask, render_template, request, redirect, url_for, flash
from utils.multipleregressionmodel import MultipleLinearRegression
from utils.lassoregressionmodel import  LassoRegression
from utils.fertilizer import fertilizer_dic
from markupsafe import Markup
import numpy as np
import pandas as pd
import pickle
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo


# Load the pickled model and preprocessor
with (open('models/best_model.pkl', 'rb') as model_file,
      open('models/preprocessor.pkl','rb') as preprocessor_file,
      open('models/implemented_model.pkl', 'rb') as implement_model_file,
      open('models/implemented2_model.pkl', 'rb') as implement2_model_file):
    best_model = pickle.load(model_file)
    preprocessor = pickle.load(preprocessor_file)
    impl_model = pickle.load(implement_model_file)
    impl2_model = pickle.load(implement2_model_file)
# ------------------------------------------------------#


app = Flask(__name__, static_url_path='/static')

app.config['SECRET_KEY'] = 'AJNG'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/khetify'

db = SQLAlchemy(app)


# data model for user
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'khetify'}
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    admin = db.relationship('Admin', back_populates='user', uselist=False)

    def get_id(self):
        return str(self.uid)


# data model for admin
class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    __table_args__ = {'schema': 'khetify'}
    adminid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('khetify.users.uid'))
    user = db.relationship('User', back_populates='admin')
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def get_id(self):
        return str(self.adminid)


# class for registrationform
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


login_manager = LoginManager(app)
login_manager.login_view = 'home'  # Specify the login route


# userlogin defination
@login_manager.user_loader
def load_user(user_id):
    user_id = int(user_id)

    admin = Admin.query.filter_by(adminid=user_id).first()
    if admin:
        # Admin
        print(f"Loaded admin: {admin.username}")
        return admin

    user = User.query.get(user_id)
    if user:
        # Regular user
        print(f"Loaded user: {user.username}")
        return user

    print(f"User with ID {user_id} not found.")
    return None


# route for userlogin
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Please check your username and password.', 'error')

    return render_template('login.html')


# route for adminlogin
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Input: Username={username}, Password={password}")

        admin = Admin.query.filter_by(username=username, password=password).first()

        print(f"Database: Admin={admin}")

        if admin:
            print(f"Logged in as admin: {admin.username}")
            login_user(admin)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Admin login failed. Please check your username and password.', 'error')

    return render_template('admin-login.html')


# route for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        # Form is valid, process registration
        username = form.username.data
        email = form.email.data
        password = form.password.data
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    # Form is not valid or not submitted yet, render registration template with form
    return render_template('registration.html', title='Register', form=form)


# route for admin dashboard
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    print(f"Current user: {current_user}")
    print(f"Is authenticated: {current_user.is_authenticated}")
    print(f"Is instance of Admin: {isinstance(current_user, Admin)}")

    if current_user.is_authenticated and isinstance(current_user, Admin):
        # Query all users for display on the admin dashboard
        all_users = User.query.all()
        return render_template('admin.html', all_users=all_users)
    else:
        flash('You do not have permission to access the admin dashboard.', 'error')
        return redirect(url_for('login'))


# route for deleting user
@app.route('/admin/delete_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)

    # Perform user deletion
    db.session.delete(user_to_delete)
    db.session.commit()

    flash(f'User {user_to_delete.username} has been deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


# render Homepage
@app.route('/')
def home():
    title = 'Khetify - Home'
    return render_template('index.html', title=title)


# render crop yield prediction from page
@app.route('/crop')
@login_required
def crop_predict():
    title = 'Khetify - Crop Yield Prediction'
    return render_template('crop.html', title=title)


# render fertilizer recommendation form page
@app.route('/fertilizer')
@login_required
def fertilizer_recommendation():
    title = ' Khelify - Fertilizer Recommendation'

    return render_template('fertilizer.html', title=title)


# render about page
@app.route('/about')
def about():
    return render_template('about.html')


# render aboutcrop
@app.route('/about_crop')
def about_crop():
    return render_template('about-crop.html')


# render aboutfer
@app.route('/about_fer')
def about_fer():
    return render_template('about-fer.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


# --------------------------------------------------#

# RENDER PREDICTION PAGES

# render crop yield prediction page
@app.route('/crop-prediction', methods=['POST'])
def crop_prediction():
    title = 'Khetify- Crop Recommendation'

    if request.method == 'POST':
        Cropname = request.form.get("Cropname")
        DistrictName = request.form.get("District")
        Production = float(request.form['Production'])
        Rainfall = float(request.form['Rainfall'])
        Area = float(request.form['Area'])
        features = np.array([[DistrictName, Cropname, Production, Rainfall, Area]], dtype=object)
        transformed_features = preprocessor.transform(features)
        selected_model = request.form.get("model")
        accuracy_metrics = {
            "Lasso Regression": {"MSE": 314420.555534, "RMSE": 560.732160, "MAE": 378.191597, "R2": 0.722497},
            "XGBoost": {"MSE": 48967.418287, "RMSE": 221.285829, "MAE": 127.939818, "R2": 0.956782},
            "Multiple Linear Regression": {"MSE": 313316.381049, "RMSE": 559.746712, "MAE": 376.565688, "R2": 0.723472}
        }
        if selected_model == "Multiple Linear Regression":
            model = impl_model
        elif selected_model == "XGBoost":
            model = best_model
        elif selected_model=='Lasso Regression':
            model=impl2_model
        elif selected_model == "All":
            model_data = [
                ("XGBoost", best_model),
                ("Multiple Linear Regression", impl_model),
                ("Lasso Regression", impl2_model)
            ]
            results = []
            for model_name, model in model_data:
                # Make the prediction
                predicted_yield = model.predict(transformed_features.toarray()).reshape(1, -1)
                final_prediction = round(float(predicted_yield[0]),3)
                accuracy = accuracy_metrics.get(model_name, {})
                results.append({
                    "model_name": model_name,
                    "prediction": final_prediction,
                    "accuracy_metrics": accuracy
                })
            return render_template('crop-result.html', results=results, title=title)
        else:
            model = best_model
        predicted_yield = model.predict(transformed_features.toarray()).reshape(1, -1)
        final_prediction = round(float(predicted_yield[0]),3)
        accuracy = accuracy_metrics.get(selected_model, {})
        result = [{
            "model_name": selected_model,
            "prediction": final_prediction,
            "accuracy_metrics": accuracy
        }]
        return render_template('crop-result.html', results=result, title=title)

# render fertilizer recommendation result page
@app.route('/fertilizer-recommend', methods=['POST'])
def fertilizer_recommend():
    title = 'Khetify - Fertilizer Suggestion'

    if request.method == 'POST':
        crop_name = str(request.form['cropname'])
        N = int(request.form['nitrogen'])
        P = int(request.form['phosphorous'])
        K = int(request.form['potassium'])
        df = pd.read_csv('data/fertilizer.csv')
        nr = df[df['Crop'] == crop_name]['N'].iloc[0]
        pr = df[df['Crop'] == crop_name]['P'].iloc[0]
        kr = df[df['Crop'] == crop_name]['K'].iloc[0]
        n = nr - N
        p = pr - P
        k = kr - K
        temp = {abs(n): "N", abs(p): "P", abs(k): "K"}
        max_value = temp[max(temp.keys())]
        if max_value == "N":
            if n < 0:
                key = 'NHigh'
            elif n > 0:
                key = "Nlow"
            else:
                key = "Perfect"
        elif max_value == "P":
            if p < 0:
                key = 'PHigh'
            elif n > 0:
                key = "Plow"
            else:
                key = "Perfect"
        else:
            if k < 0:
                key = 'KHigh'
            elif n > 0:
                key = "Klow"
            else:
                key = "Perfect"
        response = Markup(str(fertilizer_dic[key]))
        return render_template('fertilizer-result.html', recommendation=response, title=title)


# -------------------------------------------#
if __name__ == '__main__':
    app.run(debug=False)
