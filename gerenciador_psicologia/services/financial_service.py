from ..app import db
from ..models import Payment, Appointment
from datetime import datetime
from collections import defaultdict
from dateutil.relativedelta import relativedelta

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
    total = 0
    for payment in payments:
        if payment.payment_type == 'income':
            total += payment.value
        else:
            total -= payment.value
    return total

def register_payment(payment_data):
    """
    Registers a new payment.
    """
    payment_date = datetime.strptime(payment_data['date'], '%Y-%m-%d').date()
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

def get_total_income():
    """
    Calculates the total income.
    """
    total = db.session.query(db.func.sum(Payment.value)).filter(Payment.payment_type == 'income').scalar()
    return total or 0

def get_total_expenses():
    """
    Calculates the total expenses.
    """
    total = db.session.query(db.func.sum(Payment.value)).filter(Payment.payment_type == 'expense').scalar()
    return total or 0

def get_financial_summary_for_period(start_date, end_date):
    """
    Calculates financial summary (income, expenses, profit) for a given period.
    """
    income = db.session.query(db.func.sum(Payment.value)).filter(
        Payment.payment_type == 'income',
        Payment.date >= start_date,
        Payment.date <= end_date
    ).scalar() or 0

    expenses = db.session.query(db.func.sum(Payment.value)).filter(
        Payment.payment_type == 'expense',
        Payment.date >= start_date,
        Payment.date <= end_date
    ).scalar() or 0

    profit = income - expenses

    return {
        'income': income,
        'expenses': expenses,
        'profit': profit
    }

def get_expected_revenue_by_status_for_chart(start_date, end_date):
    """
    Retrieves expected revenue from 'Realizada' and 'Agendada' appointments 
    for chart visualization, separated by status.
    """
    expected_revenue_by_month = db.session.query(
        db.func.date_trunc('month', Appointment.date).label('month'),
        Appointment.status,
        db.func.sum(Appointment.value)
    ).filter(
        Appointment.status.in_(['Realizada', 'Agendada']),
        db.func.cast(Appointment.date, db.Date) >= start_date,
        db.func.cast(Appointment.date, db.Date) <= end_date
    ).group_by('month', Appointment.status).all()

    summary = defaultdict(lambda: {'Realizada': 0, 'Agendada': 0})
    for month_date, status, total in expected_revenue_by_month:
        month_key = month_date.strftime('%Y-%m')
        if status in summary[month_key]:
            summary[month_key][status] = float(total)

    return summary


def get_financial_summary_for_chart(selected_date=None):
    """
    Retrieves financial data for the last 12 months from the selected_date
    for chart visualization.
    """
    if selected_date is None:
        selected_date = datetime.utcnow().date()

    # The chart should always end on the last day of the selected month
    end_date = selected_date.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
    
    # The chart should start 11 months before the selected month
    start_date = (selected_date.replace(day=1) - relativedelta(months=11))

    # Filter payments within the 12-month window
    income_by_month = db.session.query(
        db.func.date_trunc('month', Payment.date).label('month'),
        db.func.sum(Payment.value)
    ).filter(
        Payment.payment_type == 'income',
        Payment.date >= start_date,
        Payment.date <= end_date
    ).group_by('month').all()

    expenses_by_month = db.session.query(
        db.func.date_trunc('month', Payment.date).label('month'),
        db.func.sum(Payment.value)
    ).filter(
        Payment.payment_type == 'expense',
        Payment.date >= start_date,
        Payment.date <= end_date
    ).group_by('month').all()

    # Usando defaultdict para simplificar a inicialização
    summary = defaultdict(lambda: {'income': 0, 'expense': 0})

    for month_date, total in income_by_month:
        month_key = month_date.strftime('%Y-%m')
        summary[month_key]['income'] = float(total)

    for month_date, total in expenses_by_month:
        month_key = month_date.strftime('%Y-%m')
        summary[month_key]['expense'] = float(total)

    # Get expected revenue data by status
    expected_revenue_summary = get_expected_revenue_by_status_for_chart(start_date, end_date)

    # Generate all months in the range to ensure continuity
    all_months = []
    current_month = start_date
    while current_month <= end_date:
        all_months.append(current_month.strftime('%Y-%m'))
        current_month += relativedelta(months=1)

    # Populate summary with data, ensuring all months are present
    for month_key in all_months:
        summary[month_key]  # Ensures the key exists with default values

    # Ordenando os meses para garantir a ordem cronológica no gráfico
    sorted_months = sorted(summary.keys())

    if not sorted_months:
        return {
            'labels': [],
            'income_data': [],
            'expense_data': [],
            'expected_revenue_realizada_data': [],
            'expected_revenue_agendada_data': []
        }

    # Use the generated list of all months for the labels
    labels = [datetime.strptime(m, '%Y-%m').strftime('%b/%Y') for m in all_months]
    income_data = [summary[m]['income'] for m in all_months]
    expense_data = [summary[m]['expense'] for m in all_months]
    
    expected_revenue_realizada_data = [expected_revenue_summary.get(m, {}).get('Realizada', 0) for m in all_months]
    expected_revenue_agendada_data = [expected_revenue_summary.get(m, {}).get('Agendada', 0) for m in all_months]

    return {
        'labels': labels,
        'income_data': income_data,
        'expense_data': expense_data,
        'expected_revenue_realizada_data': expected_revenue_realizada_data,
        'expected_revenue_agendada_data': expected_revenue_agendada_data
    }
