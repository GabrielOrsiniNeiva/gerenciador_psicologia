import pytest
from datetime import datetime, date
from gerenciador_psicologia.app import create_app, db
from gerenciador_psicologia.models import Patient, Payment

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def new_patient(app):
    """Fixture to create a new patient."""
    patient = Patient(name="Finance Test Patient", email="finance@patient.com", phone="987654321", birth_date=date(1985, 5, 5))
    db.session.add(patient)
    db.session.commit()
    return patient

def test_list_payments_empty(client):
    """Test listing payments when none exist."""
    response = client.get("/financial/payments")
    assert response.status_code == 200
    assert b"Nenhum registro financeiro no per" in response.data

def test_register_payment_get(client, new_patient):
    """Test GET request to register payment form."""
    response = client.get("/financial/payments/new")
    assert response.status_code == 200
    assert b"Registrar" in response.data

def test_register_income_payment_success(client, new_patient):
    """Test successful registration of an income payment."""
    response = client.post("/financial/payments/new", data={
        "patient_id": new_patient.id,
        "date": "2025-08-20T15:00",
        "value": "250.00",
        "notes": "Session payment",
        "type": "income"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Registro financeiro adicionado com sucesso!" in response.data
    assert Payment.query.count() == 1
    payment = Payment.query.first()
    assert payment.type == 'income'
    assert payment.value == 250.00
    assert payment.patient_id == new_patient.id

def test_register_expense_payment_success(client):
    """Test successful registration of an expense."""
    response = client.post("/financial/payments/new", data={
        "date": "2025-08-21T10:00",
        "value": "75.50",
        "notes": "Office supplies",
        "type": "expense"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Registro financeiro adicionado com sucesso!" in response.data
    assert Payment.query.count() == 1
    payment = Payment.query.first()
    assert payment.type == 'expense'
    assert payment.value == 75.50
    assert payment.patient_id is None

def test_register_payment_invalid_data(client):
    """Test registration of a payment with invalid data."""
    response = client.post("/financial/payments/new", data={
        "date": "invalid-date",
        "value": "not-a-number",
        "type": "income"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Erro ao registrar registro financeiro" in response.data
    assert Payment.query.count() == 0

def test_view_payment_detail(client, new_patient):
    """Test viewing the details of a specific payment."""
    payment = Payment(
        patient_id=new_patient.id,
        date=datetime(2025, 8, 22, 11, 0),
        value=300.00,
        type='income',
        notes="Detailed view test"
    )
    db.session.add(payment)
    db.session.commit()

    response = client.get(f"/financial/payments/{payment.id}")
    assert response.status_code == 200
    assert b"Detalhes do Pagamento" in response.data
    assert b"300.0" in response.data
    assert b"Detailed view test" in response.data

def test_delete_payment_success(client, new_patient):
    """Test successful deletion of a payment."""
    payment = Payment(patient_id=new_patient.id, date=datetime.now(), value=100.0, type='income')
    db.session.add(payment)
    db.session.commit()
    payment_id = payment.id

    response = client.post(f"/financial/payments/delete/{payment_id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Registro financeiro exclu" in response.data
    assert db.session.get(Payment, payment_id) is None

def test_delete_payment_not_found(client):
    """Test deleting a payment that does not exist."""
    response = client.post("/financial/payments/delete/999", follow_redirects=True)
    assert response.status_code == 404
