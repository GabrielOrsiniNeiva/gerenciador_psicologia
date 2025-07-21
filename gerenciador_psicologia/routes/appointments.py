from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..app import db
from ..models import Patient, Appointment
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging

bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@bp.route('/')
def list_appointments():
    """
    Lista todas as consultas com filtros opcionais de data.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Appointment.query.join(Patient)

    if start_date:
        query = query.filter(Appointment.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Appointment.date <= datetime.strptime(end_date, '%Y-%m-%d'))

    appointments = query.order_by(Appointment.date.desc()).all()
    patients = Patient.query.order_by(Patient.name).all()
    return render_template('appointments/list.html', appointments=appointments, patients=patients)

@bp.route('/new', methods=['GET', 'POST'])
def create_appointment():
    """
    Cria uma nova consulta com suporte a recorrência.
    """
    if request.method == 'POST':
        try:
            logging.debug(f"Form data: {request.form}")

            appointment_date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')
            is_recurring = 'is_recurring' in request.form
            recurrence_frequency = request.form.get('recurrence_frequency')
            recurrence_until = None
            no_end_date = 'no_end_date' in request.form

            if is_recurring and not no_end_date and request.form.get('recurrence_until'):
                recurrence_until = date.fromisoformat(request.form['recurrence_until'])

                if recurrence_until <= appointment_date.date():
                    flash('A data final da recorrência deve ser posterior à data inicial.', 'danger')
                    return redirect(url_for('appointments.create_appointment'))

            existing_appointment = Appointment.query.filter(
                Appointment.date == appointment_date,
                Appointment.status == 'scheduled'
            ).first()

            if existing_appointment:
                flash('Já existe uma consulta agendada para este horário.', 'danger')
                return redirect(url_for('appointments.create_appointment'))

            # Lógica de criação de consulta será refatorada para um serviço
            _create_recurring_appointments(
                patient_id=request.form['patient_id'],
                appointment_date=appointment_date,
                value=float(request.form['value']),
                notes=request.form.get('notes', ''),
                is_recurring=is_recurring,
                recurrence_frequency=recurrence_frequency,
                recurrence_until=recurrence_until
            )
            
            db.session.commit()
            flash('Consulta(s) agendada(s) com sucesso!', 'success')
            return redirect(url_for('appointments.list_appointments'))

        except ValueError as e:
            db.session.rollback()
            flash('Data inválida. Por favor, verifique os campos de data.', 'danger')
            logging.error(f'Erro de validação de data: {str(e)}')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao agendar consulta: {str(e)}', 'danger')
            logging.error(f'Erro ao agendar consulta: {str(e)}')

    patients = Patient.query.order_by(Patient.name).all()
    return render_template('appointments/form.html', patients=patients, appointment=None)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_appointment(id):
    """
    Edita uma consulta existente.
    """
    appointment = Appointment.query.get_or_404(id)

    if request.method == 'POST':
        try:
            if appointment.status != 'cancelled':
                appointment.date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')
                appointment.value = float(request.form['value'])
                appointment.status = request.form['status']
                appointment.notes = request.form['notes']
                db.session.commit()
                flash('Consulta atualizada com sucesso!', 'success')
            else:
                flash('Não é possível editar uma consulta cancelada.', 'danger')
            return redirect(url_for('appointments.list_appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar consulta: {str(e)}', 'danger')
            logging.error(f'Erro ao atualizar consulta: {str(e)}')

    patients = Patient.query.order_by(Patient.name).all()
    return render_template('appointments/form.html', appointment=appointment, patients=patients)

@bp.route('/<int:id>')
def view_appointment(id):
    """
    Exibe os detalhes de uma consulta específica.
    """
    appointment = Appointment.query.get_or_404(id)
    return render_template('appointments/detail.html', appointment=appointment)

@bp.route('/<int:id>/cancel', methods=['POST'])
def cancel_appointment(id):
    """
    Cancela uma consulta agendada.
    """
    appointment = Appointment.query.get_or_404(id)
    try:
        if appointment.status == 'scheduled':
            appointment.status = 'cancelled'
            db.session.commit()
            flash('Consulta cancelada com sucesso!', 'success')
        else:
            flash('Só é possível cancelar consultas agendadas.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cancelar consulta: {str(e)}', 'danger')
        logging.error(f'Erro ao cancelar consulta: {str(e)}')
    return redirect(url_for('appointments.list_appointments'))

# --- API Routes ---

@bp.route('/api')
def get_appointments_api():
    """
    API endpoint para retornar todas as consultas em formato compatível com FullCalendar.
    """
    start = request.args.get('start')
    end = request.args.get('end')
    
    query = Appointment.query.join(Patient)
    
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
    
    return jsonify(events)

@bp.route('/api', methods=['POST'])
def create_appointment_api():
    """
    API endpoint para criar uma nova consulta.
    """
    try:
        data = request.get_json()
        appointment_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
        is_recurring = data.get('is_recurring') == 'on'
        recurrence_frequency = data.get('recurrence_frequency')
        recurrence_until = None
        no_end_date = data.get('no_end_date') == 'on'
        
        if is_recurring and not no_end_date and data.get('recurrence_until'):
            recurrence_until = date.fromisoformat(data['recurrence_until'])
            if recurrence_until <= appointment_date.date():
                return jsonify({
                    'success': False,
                    'message': 'A data final da recorrência deve ser posterior à data inicial.'
                })
        
        existing_appointment = Appointment.query.filter(
            Appointment.date == appointment_date,
            Appointment.status == 'scheduled'
        ).first()
        
        if existing_appointment:
            return jsonify({
                'success': False,
                'message': 'Já existe uma consulta agendada para este horário.'
            })
        
        _create_recurring_appointments(
            patient_id=data['patientId'],
            appointment_date=appointment_date,
            value=float(data['value']),
            notes=data.get('notes'),
            is_recurring=is_recurring,
            recurrence_frequency=recurrence_frequency,
            recurrence_until=recurrence_until
        )
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Erro ao criar consulta: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Erro ao criar consulta: {str(e)}'
        })

@bp.route('/api/<int:id>', methods=['PUT'])
def update_appointment_api(id):
    """
    API endpoint para atualizar uma consulta existente.
    """
    scope = request.args.get('scope', 'single')
    try:
        appointment = Appointment.query.get_or_404(id)
        data = request.get_json()

        if scope == 'series':
            # Lógica de atualização de série será refatorada para um serviço
            pass
        else: # scope == 'single'
            if 'date' in data:
                appointment.date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            if 'patientId' in data:
                appointment.patient_id = data['patientId']
            if 'value' in data:
                appointment.value = float(data['value'])
            if 'notes' in data:
                appointment.notes = data.get('notes')

        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Erro ao atualizar consulta: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar consulta: {str(e)}'
        })

@bp.route('/api/<int:id>', methods=['DELETE'])
def delete_appointment_api(id):
    """
    API endpoint para excluir uma consulta.
    """
    scope = request.args.get('scope', 'single')
    try:
        appointment = Appointment.query.get_or_404(id)
        
        if scope == 'series':
            # Lógica de exclusão de série será refatorada para um serviço
            pass
        else: # scope == 'single'
            db.session.delete(appointment)
            
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Erro ao excluir consulta: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir consulta: {str(e)}'
        })

# --- Helper Functions / Services ---

def _create_recurring_appointments(patient_id, appointment_date, value, notes, is_recurring, recurrence_frequency, recurrence_until):
    """
    Cria uma consulta principal e suas recorrências, se aplicável.
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
