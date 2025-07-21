from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..app import db
from ..models import Patient, Payment
from datetime import datetime
import logging

bp = Blueprint('financial', __name__, url_prefix='/financial')

@bp.route('/payments')
def list_payments():
    """
    Lista todos os pagamentos com filtros opcionais de data.
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

@bp.route('/payments/new', methods=['GET', 'POST'])
def register_payment():
    """
    Registra um novo pagamento no sistema.
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
            return redirect(url_for('financial.list_payments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar registro financeiro: {str(e)}', 'danger')
            logging.error(f'Erro ao registrar registro financeiro: {str(e)}')

    patients = Patient.query.order_by(Patient.name).all()
    return render_template('financial/payment_form.html', patients=patients)

@bp.route('/payments/<int:id>')
def view_payment(id):
    """
    Exibe os detalhes de um pagamento específico.
    """
    payment = Payment.query.get_or_404(id)
    return render_template('financial/payment_detail.html', payment=payment)

@bp.route('/payments/delete/<int:payment_id>', methods=['POST'])
def delete_payment(payment_id):
    """
    Exclui um registro financeiro.
    """
    payment = Payment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    flash('Registro financeiro excluído com sucesso!', 'success')
    return redirect(url_for('financial.list_payments'))
