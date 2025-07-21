from flask import Blueprint, render_template, request
from .models import Patient

bp = Blueprint('main', __name__)

@bp.route('/')
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

    # Otimização: Usar 'joinedload' para evitar o problema N+1
    # Esta será implementada na refatoração do modelo.
    patients = query.order_by(Patient.name).all()
    
    return render_template('patients/list.html', patients=patients, active_filter=active_filter)
