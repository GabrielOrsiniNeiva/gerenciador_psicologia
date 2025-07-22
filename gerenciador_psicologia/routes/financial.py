from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..services import financial_service, patient_service
import logging

bp = Blueprint('financial', __name__, url_prefix='/financial')

@bp.route('/payments')
def list_payments():
    """
    Lista todos os pagamentos com filtros opcionais de data.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    payments = financial_service.get_payments(start_date, end_date)
    total_value = financial_service.get_total_value(payments)

    return render_template('financial/payments_list.html',
                           payments=payments,
                           total_value=total_value)

@bp.route('/payments/new', methods=['GET', 'POST'])
def register_payment():
    """
    Registra um novo pagamento no sistema.
    """
    if request.method == 'POST':
        try:
            financial_service.register_payment(request.form)
            flash('Registro financeiro adicionado com sucesso!', 'success')
            return redirect(url_for('financial.list_payments'))
        except Exception as e:
            flash(f'Erro ao registrar registro financeiro: {str(e)}', 'danger')
            logging.error(f'Erro ao registrar registro financeiro: {str(e)}')

    patients = patient_service.get_all_patients()
    return render_template('financial/payment_form.html', patients=patients)

@bp.route('/payments/<int:id>')
def view_payment(id):
    """
    Exibe os detalhes de um pagamento específico.
    """
    payment = financial_service.get_payment_by_id(id)
    return render_template('financial/payment_detail.html', payment=payment)

@bp.route('/payments/delete/<int:payment_id>', methods=['POST'])
def delete_payment(payment_id):
    """
    Exclui um registro financeiro.
    """
    payment = financial_service.get_payment_by_id(payment_id)
    try:
        financial_service.delete_payment(payment)
        flash('Registro financeiro excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir registro financeiro: {str(e)}', 'danger')
        logging.error(f'Erro ao excluir registro financeiro: {str(e)}')
    return redirect(url_for('financial.list_payments'))
