from flask import Blueprint, render_template, request
from gerenciador_psicologia.services import financial_service, patient_service
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def index():
    # Get selected month from query params, default to current month
    selected_month_str = request.args.get('month', date.today().strftime('%Y-%m'))
    try:
        selected_date = datetime.strptime(selected_month_str, '%Y-%m').date()
    except ValueError:
        selected_date = date.today()

    # Calculate date ranges for selected and previous months
    selected_month_start = selected_date.replace(day=1)
    selected_month_end = selected_month_start + relativedelta(months=1) - relativedelta(days=1)
    
    previous_month_end = selected_month_start - relativedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)

    # Get financial summaries
    selected_month_summary = financial_service.get_financial_summary_for_period(
        selected_month_start, selected_month_end
    )
    previous_month_summary = financial_service.get_financial_summary_for_period(
        previous_month_start, previous_month_end
    )
    
    active_patients = patient_service.get_active_patients_count()
    chart_data = financial_service.get_financial_summary_for_chart(selected_date)

    print(f"Chart Data for {selected_date}: {chart_data}")

    return render_template(
        'dashboard/index.html',
        selected_month_summary=selected_month_summary,
        previous_month_summary=previous_month_summary,
        active_patients=active_patients,
        chart_data=chart_data,
        selected_month=selected_date.strftime('%Y-%m')
    )
