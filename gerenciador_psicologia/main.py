from flask import render_template, request, redirect, url_for, flash, jsonify
import logging
from datetime import datetime, date
from .app import app, db
from .models import Patient, Payment, Appointment
from sqlalchemy import func
from dateutil.relativedelta import relativedelta

"""
Módulo principal da aplicação de gerenciamento de consultório.
Contém todas as rotas e lógica de negócio para gerenciar pacientes,
agendamentos e pagamentos.
"""

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    """
    Rota principal que lista pacientes.
    Por padrão, exibe apenas pacientes ativos.
    Permite busca e visualização de inativos.
    """
    search = request.args.get('search', '').lower()
    show_inactive = request.args.get('show_inactive', 'false').lower() == 'true'

    query = Patient.query

    if show_inactive:
        query = query.filter(Patient.is_active == False)
        active_filter = 'inactive'
    else:
        query = query.filter(Patient.is_active == True)
        active_filter = 'active'

    if search:
        query = query.filter(
            (Patient.name.ilike(f'%{search}%')) |
            (Patient.email.ilike(f'%{search}%'))
        )

    patients = query.all()
    return render_template('patients/list.html', patients=patients, active_filter=active_filter)

@app.route('/patient/new', methods=['GET', 'POST'])
def create_patient():
    """
    Cria um novo paciente no sistema.
    GET: Exibe o formulário de cadastro
    POST: Processa o formulário e salva o paciente
    """
    if request.method == 'POST':
        try:
            birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
            new_patient = Patient(
                name=request.form['name'],
                email=request.form['email'],
                phone=request.form['phone'],
                birth_date=birth_date,
                notes=request.form['notes']
            )
            db.session.add(new_patient)
            db.session.commit()
            flash('Paciente cadastrado com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar paciente: {str(e)}', 'danger')
            logging.error(f'Erro ao cadastrar paciente: {str(e)}')
    return render_template('patients/create.html')

@app.route('/patient/<int:id>/edit', methods=['GET', 'POST'])
def edit_patient(id):
    """
    Edita um paciente existente.
    Args:
        id: ID do paciente a ser editado
    """
    patient = Patient.query.get_or_404(id)

    if request.method == 'POST':
        try:
            patient.name = request.form['name']
            patient.email = request.form['email']
            patient.phone = request.form['phone']
            patient.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
            patient.notes = request.form['notes']
            db.session.commit()
            flash('Paciente atualizado com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar paciente: {str(e)}', 'danger')
            logging.error(f'Erro ao atualizar paciente: {str(e)}')

    return render_template('patients/edit.html', patient=patient)

@app.route('/patient/<int:id>/delete', methods=['POST'])
def delete_patient(id):
    """
    Remove um paciente e todas as suas dependências (consultas, pagamentos).
    Args:
        id: ID do paciente a ser removido
    """
    patient = Patient.query.get_or_404(id)
    try:
        # Exclui todas as consultas e pagamentos associados
        Appointment.query.filter_by(patient_id=id).delete()
        Payment.query.filter_by(patient_id=id).delete()
        
        db.session.delete(patient)
        db.session.commit()
        flash('Paciente removido com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover paciente: {str(e)}', 'danger')
        logging.error(f'Erro ao remover paciente: {str(e)}')
    return redirect(url_for('index'))

@app.route('/patient/<int:id>/deactivate', methods=['POST'])
def deactivate_patient(id):
    """
    Inativa um paciente e exclui todas as suas consultas futuras.
    Args:
        id: ID do paciente a ser inativado
    """
    patient = Patient.query.get_or_404(id)
    try:
        # Exclui todas as consultas associadas ao paciente
        Appointment.query.filter_by(patient_id=id).delete()
        
        # Inativa o paciente
        patient.is_active = False
        
        db.session.commit()
        flash('Paciente inativado e consultas excluídas com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao inativar paciente: {str(e)}', 'danger')
        logging.error(f'Erro ao inativar paciente: {str(e)}')
    return redirect(url_for('index'))

@app.route('/patient/<int:id>/activate', methods=['POST'])
def activate_patient(id):
    """
    Ativa um paciente no sistema.
    Args:
        id: ID do paciente a ser ativado
    """
    patient = Patient.query.get_or_404(id)
    try:
        patient.is_active = True
        db.session.commit()
        flash('Paciente ativado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao ativar paciente: {str(e)}', 'danger')
        logging.error(f'Erro ao ativar paciente: {str(e)}')
    return redirect(url_for('index', show_inactive='true'))

@app.route('/appointments')
def list_appointments():
    """
    Lista todas as consultas com filtros opcionais de data.
    Permite filtrar por período (data inicial e final).
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

@app.route('/appointments/new', methods=['GET', 'POST'])
def create_appointment():
    """
    Cria uma nova consulta com suporte a recorrência.
    Permite agendar consultas únicas ou recorrentes (semanal, quinzenal, mensal).
    Valida conflitos de horário e gera automaticamente as consultas recorrentes.
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
                    return redirect(url_for('create_appointment'))

            logging.debug(f"Appointment date: {appointment_date}")
            logging.debug(f"Recurrence until: {recurrence_until}")

            existing_appointment = Appointment.query.filter(
                Appointment.date == appointment_date,
                Appointment.status == 'scheduled'
            ).first()

            if existing_appointment:
                flash('Já existe uma consulta agendada para este horário.', 'danger')
                return redirect(url_for('create_appointment'))

            new_appointment = Appointment(
                patient_id=request.form['patient_id'],
                date=appointment_date,
                value=float(request.form['value']),
                notes=request.form['notes'],
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

                    logging.debug(f"Creating recurring appointment for: {next_date}")

                    recurring_appointment = Appointment(
                        patient_id=request.form['patient_id'],
                        date=next_date,
                        value=float(request.form['value']),
                        notes=request.form['notes'],
                        status='scheduled',
                        parent_appointment_id=new_appointment.id
                    )
                    db.session.add(recurring_appointment)
                    count += 1

            db.session.commit()
            flash('Consulta(s) agendada(s) com sucesso!', 'success')
            return redirect(url_for('list_appointments'))

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

@app.route('/appointments/<int:id>/edit', methods=['GET', 'POST'])
def edit_appointment(id):
    """
    Edita uma consulta existente.
    Permite alterar data, valor, status e observações.
    Args:
        id: ID da consulta a ser editada
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
            return redirect(url_for('list_appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar consulta: {str(e)}', 'danger')
            logging.error(f'Erro ao atualizar consulta: {str(e)}')

    patients = Patient.query.order_by(Patient.name).all()
    return render_template('appointments/form.html', appointment=appointment, patients=patients)

@app.route('/appointments/<int:id>')
def view_appointment(id):
    """
    Exibe os detalhes de uma consulta específica.
    Args:
        id: ID da consulta a ser visualizada
    """
    appointment = Appointment.query.get_or_404(id)
    return render_template('appointments/detail.html', appointment=appointment)

@app.route('/appointments/<int:id>/cancel', methods=['POST'])
def cancel_appointment(id):
    """
    Cancela uma consulta agendada.
    Args:
        id: ID da consulta a ser cancelada
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
    return redirect(url_for('list_appointments'))

@app.route('/api/appointments')
def get_appointments():
    """
    API endpoint para retornar todas as consultas em formato compatível com FullCalendar.
    Suporta filtragem por intervalo de datas.
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

@app.route('/api/appointments', methods=['POST'])
def api_create_appointment():
    """
    API endpoint para criar uma nova consulta.
    Suporta criação de consultas recorrentes.
    """
    try:
        data = request.get_json()
        appointment_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
        is_recurring = data.get('is_recurring') == 'on'  # Convertendo 'on' para True
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
        
        new_appointment = Appointment(
            patient_id=data['patientId'],
            date=appointment_date,
            value=float(data['value']),
            notes=data.get('notes'),
            status='scheduled',
            is_recurring=is_recurring,  # Agora é um booleano
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
                    patient_id=data['patientId'],
                    date=next_date,
                    value=float(data['value']),
                    notes=data.get('notes'),
                    status='scheduled',
                    parent_appointment_id=new_appointment.id
                )
                db.session.add(recurring_appointment)
                count += 1
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Erro ao criar consulta: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Erro ao criar consulta: {str(e)}'
        })

@app.route('/api/appointments/<int:id>', methods=['PUT'])
def api_update_appointment(id):
    """
    API endpoint para atualizar uma consulta existente.
    Aceita o parâmetro 'scope' para 'single' ou 'series'.
    """
    scope = request.args.get('scope', 'single')
    try:
        appointment = Appointment.query.get_or_404(id)
        data = request.get_json()

        if scope == 'series':
            parent_appointment = appointment.parent_appointment or appointment
            
            # Exclui consultas futuras da série antiga
            Appointment.query.filter(
                (Appointment.parent_appointment_id == parent_appointment.id) &
                (Appointment.date > parent_appointment.date)
            ).delete(synchronize_session=False)

            # Atualiza a consulta pai
            parent_appointment.date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            parent_appointment.patient_id = data['patientId']
            parent_appointment.value = float(data['value'])
            parent_appointment.notes = data.get('notes')
            parent_appointment.is_recurring = data.get('is_recurring') == 'on'
            parent_appointment.recurrence_frequency = data.get('recurrence_frequency') if parent_appointment.is_recurring else None
            parent_appointment.recurrence_day = parent_appointment.date.weekday() if parent_appointment.is_recurring else None
            
            recurrence_until = None
            if parent_appointment.is_recurring and data.get('recurrence_until'):
                recurrence_until = date.fromisoformat(data['recurrence_until'])
            parent_appointment.recurrence_until = recurrence_until

            # Recria as consultas recorrentes
            if parent_appointment.is_recurring:
                next_date = parent_appointment.date
                count = 0
                max_recurrences = 52
                
                while count < max_recurrences:
                    if parent_appointment.recurrence_frequency == 'weekly':
                        next_date += relativedelta(weeks=1)
                    elif parent_appointment.recurrence_frequency == 'biweekly':
                        next_date += relativedelta(weeks=2)
                    else: # monthly
                        next_date += relativedelta(months=1)
                    
                    if recurrence_until and next_date.date() > recurrence_until:
                        break
                        
                    recurring_appointment = Appointment(
                        patient_id=parent_appointment.patient_id,
                        date=next_date,
                        value=parent_appointment.value,
                        notes=parent_appointment.notes,
                        status='scheduled',
                        parent_appointment_id=parent_appointment.id
                    )
                    db.session.add(recurring_appointment)
                    count += 1
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

@app.route('/api/appointments/<int:id>', methods=['DELETE'])
def api_delete_appointment(id):
    """
    API endpoint para excluir uma consulta.
    Aceita o parâmetro 'scope' para 'single' ou 'series'.
    """
    scope = request.args.get('scope', 'single')
    try:
        appointment = Appointment.query.get_or_404(id)
        
        if scope == 'series':
            # Se for uma consulta filha, encontre a consulta pai
            parent_appointment = appointment.parent_appointment or appointment
            
            # Exclui todas as consultas futuras da série
            Appointment.query.filter(
                (Appointment.parent_appointment_id == parent_appointment.id) &
                (Appointment.date >= appointment.date)
            ).delete(synchronize_session=False)
            
            # Exclui a consulta pai se a data for a mesma
            if parent_appointment.date >= appointment.date:
                db.session.delete(parent_appointment)

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

@app.route('/financial/payments')
def list_payments():
    """
    Lista todos os pagamentos com filtros opcionais de data.
    Calcula o valor total dos pagamentos filtrados.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Payment.query

    if start_date:
        query = query.filter(Payment.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Payment.date <= datetime.strptime(end_date, '%Y-%m-%d'))

    payments = query.order_by(Payment.date.desc()).all()
    total_value = sum(payment.value for payment in payments)

    return render_template('financial/payments_list.html',
                           payments=payments,
                           total_value=total_value)

@app.route('/financial/payments/new', methods=['GET', 'POST'])
def register_payment():
    """
    Registra um novo pagamento no sistema.
    Permite especificar paciente, valor, método de pagamento e observações.
    """
    if request.method == 'POST':
        try:
            logging.debug(f"Request form data: {request.form}")
            payment_date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')
            payment_type = request.form['type']  # 'income' or 'expense'
            patient_id = request.form.get('patient_id') if payment_type == 'income' else None
            try:
                patient_id = int(patient_id) if patient_id else None
            except ValueError:
                patient_id = None

            payment_type = request.form['type']  # 'income' or 'expense'
            patient_id = request.form.get('patient_id') if payment_type == 'income' else None
            try:
                patient_id = int(patient_id) if patient_id else None
            except ValueError:
                patient_id = None

            new_payment = Payment(
                date=payment_date,
                value=float(request.form['value']),
                notes=request.form['notes'],
                type=payment_type
            )

            if patient_id:
                new_payment.patient_id = patient_id


            db.session.add(new_payment)
            db.session.commit()
            flash('Registro financeiro adicionado com sucesso!', 'success')
            return redirect(url_for('list_payments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar registro financeiro: {str(e)}', 'danger')
            logging.error(f'Erro ao registrar registro financeiro: {str(e)}')

    patients = Patient.query.order_by(Patient.name).all()
    return render_template('financial/payment_form.html', patients=patients)

@app.route('/financial/payments/<int:id>')
def view_payment(id):
    """
    Exibe os detalhes de um pagamento específico.
    Args:
        id: ID do pagamento a ser visualizado
    """
    payment = Payment.query.get_or_404(id)
    return render_template('financial/payment_detail.html', payment=payment)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
