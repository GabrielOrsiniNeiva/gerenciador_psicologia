import pytest
from flask import session
from datetime import datetime, date
from gerenciador_psicologia.app import create_app, db
from gerenciador_psicologia.models import Patient, Appointment

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
    patient = Patient(name="Test Patient", email="test@patient.com", phone="123456789", birth_date=date(1990, 1, 1))
    db.session.add(patient)
    db.session.commit()
    return patient

def test_list_appointments_empty(client):
    """Test listing appointments when none exist."""
    response = client.get("/appointments/")
    assert response.status_code == 200
    assert b'id="calendar"' in response.data

def test_create_appointment_get(client, new_patient):
    """Test GET request to create appointment form."""
    response = client.get("/appointments/new")
    assert response.status_code == 200
    assert b"Nova Consulta" in response.data

def test_create_single_appointment_post_success(client, new_patient):
    """Test successful creation of a single new appointment."""
    response = client.post("/appointments/new", data={
        "patient_id": new_patient.id,
        "date": "2025-08-01T10:00",
        "value": "150.00",
        "notes": "First session"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Consulta(s) agendada(s) com sucesso!" in response.data
    assert Appointment.query.count() == 1
    appointment = Appointment.query.first()
    assert appointment.patient_id == new_patient.id
    assert not appointment.is_recurring

def test_create_recurring_appointment_post_success(client, new_patient):
    """Test successful creation of a recurring weekly appointment."""
    response = client.post("/appointments/new", data={
        "patient_id": new_patient.id,
        "date": "2025-08-01T11:00",
        "value": "150.00",
        "notes": "Weekly session",
        "is_recurring": "on",
        "recurrence_frequency": "weekly",
        "recurrence_until": "2025-08-22"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Consulta(s) agendada(s) com sucesso!" in response.data
    # Expecting 4 appointments: Aug 1, 8, 15, 22
    assert Appointment.query.count() == 4
    parent_appointment = Appointment.query.filter_by(is_recurring=True).first()
    assert parent_appointment is not None
    assert Appointment.query.filter_by(parent_appointment_id=parent_appointment.id).count() == 3

def test_create_appointment_invalid_date(client, new_patient):
    """Test creating an appointment with an invalid date format."""
    response = client.post("/appointments/new", data={
        "patient_id": new_patient.id,
        "date": "invalid-date",
        "value": "150.00",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Data inv" in response.data # "Data inválida"
    assert Appointment.query.count() == 0

def test_edit_appointment_get(client, new_patient):
    """Test GET request to edit appointment form."""
    appointment = Appointment(patient_id=new_patient.id, date=datetime(2025, 8, 5, 10, 0), value=120.0)
    db.session.add(appointment)
    db.session.commit()

    response = client.get(f"/appointments/{appointment.id}/edit")
    assert response.status_code == 200
    assert b"Editar Consulta" in response.data
    assert b"120.0" in response.data

def test_edit_appointment_post_success(client, new_patient):
    """Test successful update of an appointment."""
    appointment = Appointment(patient_id=new_patient.id, date=datetime(2025, 8, 5, 10, 0), value=120.0, status='scheduled')
    db.session.add(appointment)
    db.session.commit()

    response = client.post(f"/appointments/{appointment.id}/edit", data={
        "date": "2025-08-05T11:30",
        "value": "130.50",
        "status": "completed",
        "notes": "Updated notes"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Consulta atualizada com sucesso!" in response.data
    
    updated_appointment = db.session.get(Appointment, appointment.id)
    assert updated_appointment.date == datetime(2025, 8, 5, 11, 30)
    assert updated_appointment.value == 130.50
    assert updated_appointment.status == 'completed'

def test_cancel_appointment_success(client, new_patient):
    """Test successfully canceling a scheduled appointment."""
    appointment = Appointment(patient_id=new_patient.id, date=datetime(2025, 8, 8, 15, 0), value=180.0, status='scheduled')
    db.session.add(appointment)
    db.session.commit()

    response = client.post(f"/appointments/{appointment.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    assert b"Consulta cancelada com sucesso!" in response.data
    
    cancelled_appointment = db.session.get(Appointment, appointment.id)
    assert cancelled_appointment.status == 'cancelled'

def test_cancel_appointment_already_cancelled(client, new_patient):
    """Test trying to cancel an appointment that is already cancelled."""
    appointment = Appointment(patient_id=new_patient.id, date=datetime(2025, 8, 8, 15, 0), value=180.0, status='cancelled')
    db.session.add(appointment)
    db.session.commit()

    response = client.post(f"/appointments/{appointment.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    assert b"S" in response.data # "Só é possível cancelar consultas agendadas."

# --- API Tests ---

def test_get_appointments_api(client, new_patient):
    """Test the API endpoint for fetching appointments for FullCalendar."""
    dt = datetime(2025, 8, 10, 14, 0)
    appointment = Appointment(patient_id=new_patient.id, date=dt, value=200.0)
    db.session.add(appointment)
    db.session.commit()

    response = client.get(f"/appointments/api?start={dt.date().isoformat()}&end={(dt.date() + date.resolution).isoformat()}")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['title'] == f'Consulta - {new_patient.name}'
    assert data[0]['id'] == appointment.id

def test_create_appointment_api_success(client, new_patient):
    """Test successful creation of an appointment via API."""
    response = client.post("/appointments/api", json={
        "patientId": new_patient.id,
        "date": "2025-08-11T16:00:00Z",
        "value": 210.00,
        "notes": "API test"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert Appointment.query.count() == 1

def test_update_appointment_api_success(client, new_patient):
    """Test successful update of an appointment via API."""
    appointment = Appointment(patient_id=new_patient.id, date=datetime(2025, 8, 12, 9, 0), value=100.0)
    db.session.add(appointment)
    db.session.commit()

    new_date = "2025-08-12T09:30:00Z"
    response = client.put(f"/appointments/api/{appointment.id}", json={
        "date": new_date
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    
    updated_appointment = db.session.get(Appointment, appointment.id)
    assert updated_appointment.date.isoformat() + "Z" == new_date

def test_delete_appointment_api_success(client, new_patient):
    """Test successful deletion of an appointment via API."""
    appointment = Appointment(patient_id=new_patient.id, date=datetime(2025, 8, 13, 11, 0), value=150.0)
    db.session.add(appointment)
    db.session.commit()
    appointment_id = appointment.id

    response = client.delete(f"/appointments/api/{appointment_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert db.session.get(Appointment, appointment_id) is None
