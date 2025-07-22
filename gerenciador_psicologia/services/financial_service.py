from ..app import db
from ..models import Payment
from datetime import datetime

def get_payments(start_date=None, end_date=None):
    """
    Retrieves payments with optional date filters.
    """
    query = Payment.query
    if start_date:
        query = query.filter(Payment.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Payment.date <= datetime.strptime(end_date, '%Y-%m-%d'))
    return query.order_by(Payment.date.desc()).all()

def get_total_value(payments):
    """
    Calculates the total value of a list of payments.
    """
    return sum(payment.value for payment in payments)

def register_payment(payment_data):
    """
    Registers a new payment.
    """
    payment_date = datetime.strptime(payment_data['date'], '%Y-%m-%dT%H:%M')
    payment_type = payment_data['payment_type']
    patient_id = payment_data.get('patient_id') if payment_type == 'income' else None
    try:
        patient_id = int(patient_id) if patient_id else None
    except ValueError:
        patient_id = None

    new_payment = Payment(
        date=payment_date,
        value=float(payment_data['value']),
        notes=payment_data['notes'],
        payment_type=payment_type
    )

    if patient_id:
        new_payment.patient_id = patient_id

    db.session.add(new_payment)
    db.session.commit()
    return new_payment

def delete_payment(payment):
    """
    Deletes a payment.
    """
    db.session.delete(payment)
    db.session.commit()

def get_payment_by_id(payment_id):
    """
    Retrieves a payment by its ID.
    """
    return Payment.query.get_or_404(payment_id)
