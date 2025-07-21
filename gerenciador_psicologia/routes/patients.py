from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..app import db
from ..models import Patient, Appointment, Payment
from datetime import datetime, timezone
import logging

bp = Blueprint('patients', __name__, url_prefix='/patient')

@bp.route('/new', methods=['GET', 'POST'])
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
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar paciente: {str(e)}', 'danger')
            logging.error(f'Erro ao cadastrar paciente: {str(e)}')
    return render_template('patients/create.html')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_patient(id):
    """
    Edita um paciente existente.
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
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar paciente: {str(e)}', 'danger')
            logging.error(f'Erro ao atualizar paciente: {str(e)}')

    return render_template('patients/edit.html', patient=patient)

@bp.route('/<int:id>/delete', methods=['POST'])
def delete_patient(id):
    """
    Remove um paciente e todas as suas dependências.
    """
    patient = Patient.query.get_or_404(id)
    try:
        # A configuração de cascade no modelo cuidará da exclusão de dependências.
        db.session.delete(patient)
        db.session.commit()
        flash('Paciente removido com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover paciente: {str(e)}', 'danger')
        logging.error(f'Erro ao remover paciente: {str(e)}')
    return redirect(url_for('main.index'))

@bp.route('/<int:id>/deactivate', methods=['POST'])
def deactivate_patient(id):
    """
    Inativa um paciente e exclui todas as suas consultas futuras.
    """
    patient = Patient.query.get_or_404(id)
    try:
        # Exclui todas as consultas futuras associadas ao paciente
        today = datetime.now(timezone.utc).date()
        Appointment.query.filter(
            Appointment.patient_id == id,
            Appointment.date >= today
        ).delete()
        
        patient.is_active = False
        db.session.commit()
        flash('Paciente inativado e consultas futuras excluídas com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao inativar paciente: {str(e)}', 'danger')
        logging.error(f'Erro ao inativar paciente: {str(e)}')
    return redirect(url_for('main.index'))

@bp.route('/<int:id>/activate', methods=['POST'])
def activate_patient(id):
    """
    Ativa um paciente no sistema.
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
    return redirect(url_for('main.index', show_inactive='true'))
