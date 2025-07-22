from ..app import db
from ..models import Patient, Appointment
from datetime import datetime, timezone

def create_patient(patient_data):
    """
    Creates a new patient.
    """
    birth_date = datetime.strptime(patient_data['birth_date'], '%Y-%m-%d').date()
    new_patient = Patient(
        name=patient_data['name'],
        email=patient_data['email'],
        phone=patient_data['phone'],
        birth_date=birth_date,
        notes=patient_data['notes']
    )
    db.session.add(new_patient)
    db.session.commit()
    return new_patient

def update_patient(patient, patient_data):
    """
    Updates an existing patient.
    """
    patient.name = patient_data['name']
    patient.email = patient_data['email']
    patient.phone = patient_data['phone']
    patient.birth_date = datetime.strptime(patient_data['birth_date'], '%Y-%m-%d').date()
    patient.notes = patient_data['notes']
    db.session.commit()
    return patient

def delete_patient(patient):
    """
    Deletes a patient.
    """
    db.session.delete(patient)
    db.session.commit()

def deactivate_patient(patient):
    """
    Deactivates a patient and deletes their future appointments.
    """
    today = datetime.now(timezone.utc).date()
    Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.date >= today
    ).delete()
    patient.is_active = False
    db.session.commit()

def activate_patient(patient):
    """
    Activates a patient.
    """
    patient.is_active = True
    db.session.commit()

def get_patient_by_id(patient_id):
    """
    Retrieves a patient by their ID.
    """
    return Patient.query.get_or_404(patient_id)

def get_all_patients():
    """
    Retrieves all patients.
    """
    return Patient.query.order_by(Patient.name).all()
