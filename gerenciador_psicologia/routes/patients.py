from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..services import patient_service
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
            patient_service.create_patient(request.form)
            flash('Paciente cadastrado com sucesso!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'Erro ao cadastrar paciente: {str(e)}', 'danger')
            logging.error(f'Erro ao cadastrar paciente: {str(e)}')
    return render_template('patients/create.html')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_patient(id):
    """
    Edita um paciente existente.
    """
    patient = patient_service.get_patient_by_id(id)

    if request.method == 'POST':
        try:
            patient_service.update_patient(patient, request.form)
            flash('Paciente atualizado com sucesso!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'Erro ao atualizar paciente: {str(e)}', 'danger')
            logging.error(f'Erro ao atualizar paciente: {str(e)}')

    return render_template('patients/edit.html', patient=patient)

@bp.route('/<int:id>/delete', methods=['POST'])
def delete_patient(id):
    """
    Remove um paciente e todas as suas dependências.
    """
    patient = patient_service.get_patient_by_id(id)
    try:
        patient_service.delete_patient(patient)
        flash('Paciente removido com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao remover paciente: {str(e)}', 'danger')
        logging.error(f'Erro ao remover paciente: {str(e)}')
    return redirect(url_for('main.index'))

@bp.route('/<int:id>/deactivate', methods=['POST'])
def deactivate_patient(id):
    """
    Inativa um paciente e exclui todas as suas consultas futuras.
    """
    patient = patient_service.get_patient_by_id(id)
    try:
        patient_service.deactivate_patient(patient)
        flash('Paciente inativado e consultas futuras excluídas com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao inativar paciente: {str(e)}', 'danger')
        logging.error(f'Erro ao inativar paciente: {str(e)}')
    return redirect(url_for('main.index'))

@bp.route('/<int:id>/activate', methods=['POST'])
def activate_patient(id):
    """
    Ativa um paciente no sistema.
    """
    patient = patient_service.get_patient_by_id(id)
    try:
        patient_service.activate_patient(patient)
        flash('Paciente ativado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao ativar paciente: {str(e)}', 'danger')
        logging.error(f'Erro ao ativar paciente: {str(e)}')
    return redirect(url_for('main.index', show_inactive='true'))
