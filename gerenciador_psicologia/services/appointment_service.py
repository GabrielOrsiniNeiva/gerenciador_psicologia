from ..app import db
from ..models import Appointment
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def create_appointment(appointment_data):
    """
    Creates a new appointment, handling recurrence.
    """
    appointment_date = datetime.strptime(appointment_data['date'], '%Y-%m-%dT%H:%M')
    is_recurring = 'is_recurring' in appointment_data
    recurrence_frequency = appointment_data.get('recurrence_frequency')
    recurrence_until = None
    no_end_date = 'no_end_date' in appointment_data

    if is_recurring and not no_end_date and appointment_data.get('recurrence_until'):
        recurrence_until = date.fromisoformat(appointment_data['recurrence_until'])

        if recurrence_until <= appointment_date.date():
            raise ValueError('A data final da recorrência deve ser posterior à data inicial.')

    existing_appointment = Appointment.query.filter(
        Appointment.date == appointment_date,
        Appointment.status == 'scheduled'
    ).first()

    if existing_appointment:
        raise ValueError('Já existe uma consulta agendada para este horário.')

    _create_recurring_appointments(
        patient_id=appointment_data['patient_id'],
        appointment_date=appointment_date,
        value=float(appointment_data['value']),
        notes=appointment_data.get('notes', ''),
        is_recurring=is_recurring,
        recurrence_frequency=recurrence_frequency,
        recurrence_until=recurrence_until
    )
    db.session.commit()

def _create_recurring_appointments(patient_id, appointment_date, value, notes, is_recurring, recurrence_frequency, recurrence_until):
    """
    Creates a main appointment and its recurrences, if applicable.
    """
    new_appointment = Appointment(
        patient_id=patient_id,
        date=appointment_date,
        value=value,
        notes=notes,
        status='scheduled',
        is_recurring=is_recurring,
        recurrence_frequency=recurrence_frequency if is_recurring else None,
        recurrence_day=appointment_date.weekday() if is_recurring else None,
        recurrence_until=recurrence_until
    )
    db.session.add(new_appointment)
    db.session.flush()

    if is_recurring and recurrence_frequency:
        next_date = appointment_date
        count = 0
        max_recurrences = 52

        while count < max_recurrences:
            if recurrence_frequency == 'weekly':
                next_date = next_date + relativedelta(weeks=1)
            elif recurrence_frequency == 'biweekly':
                next_date = next_date + relativedelta(weeks=2)
            else:  # monthly
                next_date = next_date + relativedelta(months=1)

            if recurrence_until and next_date.date() > recurrence_until:
                break

            recurring_appointment = Appointment(
                patient_id=patient_id,
                date=next_date,
                value=value,
                notes=notes,
                status='scheduled',
                parent_appointment_id=new_appointment.id
            )
            db.session.add(recurring_appointment)
            count += 1

def get_appointment_by_id(appointment_id):
    """
    Retrieves an appointment by its ID.
    """
    return Appointment.query.get_or_404(appointment_id)

def update_appointment(appointment, appointment_data):
    """
    Updates an existing appointment.
    """
    if appointment.status != 'cancelled':
        appointment.date = datetime.strptime(appointment_data['date'], '%Y-%m-%dT%H:%M')
        appointment.value = float(appointment_data['value'])
        appointment.status = appointment_data['status']
        appointment.notes = appointment_data['notes']
        db.session.commit()
    else:
        raise ValueError('Não é possível editar uma consulta cancelada.')

def cancel_appointment(appointment):
    """
    Cancels an appointment.
    """
    if appointment.status == 'scheduled':
        appointment.status = 'cancelled'
        db.session.commit()
    else:
        raise ValueError('Só é possível cancelar consultas agendadas.')

def delete_appointment(appointment):
    """
    Deletes an appointment.
    """
    db.session.delete(appointment)
    db.session.commit()

def get_appointments_for_calendar(start, end):
    """
    Retrieves appointments for the calendar view.
    """
    query = Appointment.query.join(Appointment.patient)
    
    if start:
        query = query.filter(Appointment.date >= datetime.fromisoformat(start))
    if end:
        query = query.filter(Appointment.date <= datetime.fromisoformat(end))
        
    appointments = query.all()
    events = []
    
    for appointment in appointments:
        event = {
            'id': appointment.id,
            'title': f'Consulta - {appointment.patient.name}',
            'start': appointment.date.isoformat(),
            'end': (appointment.date + relativedelta(hours=1)).isoformat(),
            'extendedProps': {
                'patientId': appointment.patient_id,
                'value': float(appointment.value),
                'notes': appointment.notes,
                'isRecurring': appointment.is_recurring or appointment.parent_appointment_id is not None,
                'recurrenceFrequency': appointment.recurrence_frequency,
                'recurrenceUntil': appointment.recurrence_until.isoformat() if appointment.recurrence_until else None
            }
        }
        
        if appointment.status == 'cancelled':
            event['className'] = 'fc-event-cancelled'
            event['title'] = f'[CANCELADO] {event["title"]}'
        
        events.append(event)
    
    return events
