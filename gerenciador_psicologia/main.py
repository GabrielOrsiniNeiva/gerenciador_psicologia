from flask import render_template, request, redirect, url_for, flash
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
    Rota principal que lista todos os pacientes.
    Permite busca por nome ou email.
    """
    search = request.args.get('search', '').lower()
    if search:
        patients = Patient.query.filter(
            (Patient.name.ilike(f'%{search}%')) |
            (Patient.email.ilike(f'%{search}%'))
        ).all()
    else:
        patients = Patient.query.all()
    return render_template('patients/list.html', patients=patients)

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
    Remove um paciente do sistema.
    Args:
        id: ID do paciente a ser removido
    """
    patient = Patient.query.get_or_404(id)
    try:
        db.session.delete(patient)
        db.session.commit()
        flash('Paciente removido com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover paciente: {str(e)}', 'danger')
        logging.error(f'Erro ao remover paciente: {str(e)}')
    return redirect(url_for('index'))

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
    return render_template('appointments/list.html', appointments=appointments)

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

            if request.form.get('recurrence_until'):
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

@app.route('/financial/payments')
def list_payments():
    """
    Lista todos os pagamentos com filtros opcionais de data.
    Calcula o valor total dos pagamentos filtrados.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Payment.query.join(Patient)

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
            payment_date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')
            new_payment = Payment(
                patient_id=request.form['patient_id'],
                date=payment_date,
                value=float(request.form['value']),
                payment_method=request.form['payment_method'],
                notes=request.form['notes']
            )
            db.session.add(new_payment)
            db.session.commit()
            flash('Pagamento registrado com sucesso!', 'success')
            return redirect(url_for('list_payments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar pagamento: {str(e)}', 'danger')
            logging.error(f'Erro ao registrar pagamento: {str(e)}')

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
