from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..services import appointment_service, patient_service
from ..models import Appointment, Patient
from datetime import datetime
import logging

bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@bp.route('/')
def list_appointments():
    """
    Lista todas as consultas com filtros opcionais de data.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # This logic could also be moved to the service layer for consistency
    query = Appointment.query.join(Patient)
    if start_date:
        query = query.filter(Appointment.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Appointment.date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    appointments = query.order_by(Appointment.date.desc()).all()
    patients = patient_service.get_all_patients()
    return render_template('appointments/list.html', appointments=appointments, patients=patients)

@bp.route('/new', methods=['GET', 'POST'])
def create_appointment():
    """
    Cria uma nova consulta com suporte a recorrência.
    """
    if request.method == 'POST':
        try:
            appointment_service.create_appointment(request.form)
            flash('Consulta(s) agendada(s) com sucesso!', 'success')
            return redirect(url_for('appointments.list_appointments'))
        except ValueError as e:
            flash(str(e), 'danger')
            logging.error(f'Erro de validação de data: {str(e)}')
        except Exception as e:
            flash(f'Erro ao agendar consulta: {str(e)}', 'danger')
            logging.error(f'Erro ao agendar consulta: {str(e)}')

    patients = patient_service.get_all_patients()
    return render_template('appointments/form.html', patients=patients, appointment=None)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_appointment(id):
    """
    Edita uma consulta existente.
    """
    appointment = appointment_service.get_appointment_by_id(id)

    if request.method == 'POST':
        try:
            appointment_service.update_appointment(appointment, request.form)
            flash('Consulta atualizada com sucesso!', 'success')
            return redirect(url_for('appointments.list_appointments'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Erro ao atualizar consulta: {str(e)}', 'danger')
            logging.error(f'Erro ao atualizar consulta: {str(e)}')

    patients = patient_service.get_all_patients()
    return render_template('appointments/form.html', appointment=appointment, patients=patients)

@bp.route('/<int:id>')
def view_appointment(id):
    """
    Exibe os detalhes de uma consulta específica.
    """
    appointment = appointment_service.get_appointment_by_id(id)
    return render_template('appointments/detail.html', appointment=appointment)

@bp.route('/<int:id>/cancel', methods=['POST'])
def cancel_appointment(id):
    """
    Cancela uma consulta agendada.
    """
    appointment = appointment_service.get_appointment_by_id(id)
    try:
        appointment_service.cancel_appointment(appointment)
        flash('Consulta cancelada com sucesso!', 'success')
    except ValueError as e:
        flash(str(e), 'warning')
    except Exception as e:
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
    events = appointment_service.get_appointments_for_calendar(start, end)
    return jsonify(events)

@bp.route('/api', methods=['POST'])
def create_appointment_api():
    """
    API endpoint para criar uma nova consulta.
    """
    try:
        # The service layer expects form-like data, so we adapt the JSON
        data = request.get_json()
        form_data = {
            'patient_id': data['patientId'],
            'date': data['date'].replace('Z', ''),
            'value': data['value'],
            'notes': data.get('notes'),
            'is_recurring': 'is_recurring' in data,
            'recurrence_frequency': data.get('recurrence_frequency'),
            'recurrence_until': data.get('recurrence_until')
        }
        appointment_service.create_appointment(form_data)
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        logging.error(f'Erro ao criar consulta via API: {str(e)}')
        return jsonify({'success': False, 'message': f'Erro ao criar consulta: {str(e)}'})

@bp.route('/api/<int:id>', methods=['PUT'])
def update_appointment_api(id):
    """
    API endpoint para atualizar uma consulta existente.
    """
    # Note: The service layer doesn't support partial updates yet.
    # This API endpoint would need to be updated to handle that.
    try:
        appointment = appointment_service.get_appointment_by_id(id)
        data = request.get_json()
        # This is a simplified update, a more robust solution is needed
        appointment_service.update_appointment(appointment, data)
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        logging.error(f'Erro ao atualizar consulta via API: {str(e)}')
        return jsonify({'success': False, 'message': f'Erro ao atualizar consulta: {str(e)}'})

@bp.route('/api/<int:id>', methods=['DELETE'])
def delete_appointment_api(id):
    """
    API endpoint para excluir uma consulta.
    """
    # Note: The service layer doesn't support deleting series yet.
    try:
        appointment = appointment_service.get_appointment_by_id(id)
        appointment_service.delete_appointment(appointment) # This function needs to be created
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f'Erro ao excluir consulta via API: {str(e)}')
        return jsonify({'success': False, 'message': f'Erro ao excluir consulta: {str(e)}'})
