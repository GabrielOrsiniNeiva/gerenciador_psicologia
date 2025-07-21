import pytest
from datetime import date
from gerenciador_psicologia.app import create_app, db
from gerenciador_psicologia.models import Patient

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False  # Disable CSRF for testing
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

def test_create_patient_get(client):
    """Test GET request to create patient form."""
    response = client.get("/patient/new")
    assert response.status_code == 200
    assert b"Novo Paciente" in response.data

def test_create_patient_post_success(client):
    """Test successful creation of a new patient."""
    response = client.post("/patient/new", data={
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "1234567890",
        "birth_date": "1990-01-01",
        "notes": "Test notes"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Paciente cadastrado com sucesso!" in response.data
    patient = Patient.query.filter_by(email="john.doe@example.com").first()
    assert patient is not None
    assert patient.name == "John Doe"

def test_create_patient_post_invalid_data(client):
    """Test creation of a patient with invalid data."""
    response = client.post("/patient/new", data={
        "name": "",  # Invalid: name is required
        "email": "invalid-email",
        "phone": "123",
        "birth_date": "invalid-date",
        "notes": ""
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Erro ao cadastrar paciente" in response.data
    assert Patient.query.count() == 0

def test_edit_patient_get(client):
    """Test GET request to edit patient form."""
    patient = Patient(name="Jane Doe", email="jane.doe@example.com", phone="0987654321", birth_date=date(1992, 2, 2))
    db.session.add(patient)
    db.session.commit()

    response = client.get(f"/patient/{patient.id}/edit")
    assert response.status_code == 200
    assert b"Editar Paciente" in response.data
    assert b"Jane Doe" in response.data

def test_edit_patient_post_success(client):
    """Test successful update of a patient."""
    patient = Patient(name="Jane Doe", email="jane.doe@example.com", phone="0987654321", birth_date=date(1992, 2, 2))
    db.session.add(patient)
    db.session.commit()

    response = client.post(f"/patient/{patient.id}/edit", data={
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "111222333",
        "birth_date": "1992-02-03",
        "notes": "Updated notes"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Paciente atualizado com sucesso!" in response.data
    updated_patient = db.session.get(Patient, patient.id)
    assert updated_patient.name == "Jane Smith"
    assert updated_patient.email == "jane.smith@example.com"

def test_edit_patient_not_found(client):
    """Test editing a patient that does not exist."""
    response = client.get("/patient/999/edit")
    assert response.status_code == 404

def test_delete_patient_success(client):
    """Test successful deletion of a patient."""
    patient = Patient(name="To Be Deleted", email="delete@me.com", phone="123", birth_date=date(2000, 1, 1))
    db.session.add(patient)
    db.session.commit()
    patient_id = patient.id

    response = client.post(f"/patient/{patient_id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Paciente removido com sucesso!" in response.data
    assert db.session.get(Patient, patient_id) is None

def test_delete_patient_not_found(client):
    """Test deleting a patient that does not exist."""
    response = client.post("/patient/999/delete", follow_redirects=True)
    assert response.status_code == 404

def test_deactivate_patient_success(client):
    """Test successful deactivation of a patient."""
    patient = Patient(name="To Be Deactivated", email="deactivate@me.com", phone="123", birth_date=date(2000, 1, 1), is_active=True)
    db.session.add(patient)
    db.session.commit()

    response = client.post(f"/patient/{patient.id}/deactivate", follow_redirects=True)
    assert response.status_code == 200
    assert b"Paciente inativado e consultas futuras exclu" in response.data
    assert not db.session.get(Patient, patient.id).is_active

def test_activate_patient_success(client):
    """Test successful activation of a patient."""
    patient = Patient(name="To Be Activated", email="activate@me.com", phone="123", birth_date=date(2000, 1, 1), is_active=False)
    db.session.add(patient)
    db.session.commit()

    response = client.post(f"/patient/{patient.id}/activate", follow_redirects=True)
    assert response.status_code == 200
    assert b"Paciente ativado com sucesso!" in response.data
    assert db.session.get(Patient, patient.id).is_active
