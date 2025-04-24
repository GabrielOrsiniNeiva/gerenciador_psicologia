import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
from .models import Payment
from .extensions import db

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure o SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

migrate = Migrate(app, db)

# Configure o SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

with app.app_context():
    from . import models
    db.create_all()

@app.route('/payments/delete/<int:payment_id>', methods=['POST'])
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    flash('Registro financeiro excluído com sucesso!', 'success')
    return redirect(url_for('list_payments'))
