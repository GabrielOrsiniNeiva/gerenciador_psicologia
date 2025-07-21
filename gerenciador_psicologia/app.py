import os
from flask import Flask
from dotenv import load_dotenv
from .extensions import db
from flask_migrate import Migrate

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def create_app(test_config=None):
    """
    Cria e configura uma instância da aplicação Flask.
    Utiliza o padrão Application Factory.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Configuração da aplicação
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SESSION_SECRET", "dev_secret_key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is None:
        # Carrega a configuração da instância, se existir, quando não estiver testando
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Carrega a configuração de teste se for passada
        app.config.from_mapping(test_config)

    # Inicializa as extensões
    db.init_app(app)
    Migrate(app, db)

    # Importa e registra os Blueprints
    from .routes import patients, appointments, financial
    from . import main

    app.register_blueprint(main.bp)
    app.register_blueprint(patients.bp)
    app.register_blueprint(appointments.bp)
    app.register_blueprint(financial.bp)

    # Importa os modelos para que o Flask-Migrate os reconheça
    from . import models

    return app
