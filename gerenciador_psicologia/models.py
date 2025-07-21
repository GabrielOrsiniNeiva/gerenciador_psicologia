from datetime import datetime
import sqlalchemy as sa
from .extensions import db
import enum

class Patient(db.Model):
    """
    Modelo representando um paciente no sistema.

    Attributes:
        id: Identificador único do paciente
        name: Nome completo do paciente
        email: Endereço de email único do paciente
        phone: Número de telefone do paciente
        birth_date: Data de nascimento
        notes: Observações gerais sobre o paciente
        created_at: Data de criação do registro
        updated_at: Data da última atualização
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=sa.func.now())
    updated_at = db.Column(db.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())

    appointments = db.relationship('Appointment', backref='patient', lazy='joined', cascade="all, delete-orphan")
    payments = db.relationship('Payment', backref='patient', lazy='joined', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Patient {self.name}>'

class Appointment(db.Model):
    """
    Modelo representando uma consulta no sistema.

    Attributes:
        id: Identificador único da consulta
        patient_id: ID do paciente relacionado
        date: Data e hora da consulta
        status: Status atual (scheduled, completed, cancelled)
        value: Valor da consulta
        notes: Observações sobre a consulta
        is_recurring: Indica se é uma consulta recorrente
        recurrence_frequency: Frequência da recorrência (weekly, biweekly, monthly)
        recurrence_day: Dia da semana para recorrência (0-6)
        recurrence_until: Data final da recorrência
        parent_appointment_id: ID da consulta pai (para séries recorrentes)
    """
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum('scheduled', 'completed', 'cancelled', name='appointment_status'), nullable=False, default='scheduled')
    value = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=sa.func.now())
    updated_at = db.Column(db.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())

    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_frequency = db.Column(db.String(20))
    recurrence_day = db.Column(db.Integer)
    recurrence_until = db.Column(db.Date)
    parent_appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)

    recurring_appointments = db.relationship(
        'Appointment',
        backref=db.backref('parent_appointment', remote_side=[id]),
        lazy=True
    )

    def __repr__(self):
        return f'<Appointment {self.date} - Patient {self.patient_id}>'

class Payment(db.Model):
    """
    Modelo representando um pagamento no sistema.

    Attributes:
        id: Identificador único do pagamento
        patient_id: ID do paciente que realizou o pagamento
        date: Data e hora do pagamento
        value: Valor do pagamento
        notes: Observações sobre o pagamento
        created_at: Data de criação do registro
    """
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    date = db.Column(db.DateTime, nullable=False, server_default=sa.func.now())
    value = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text())
    type = db.Column(db.String(20), nullable=False, default='income')  # 'income' or 'expense'
    created_at = db.Column(db.DateTime, server_default=sa.func.now())

    def __repr__(self):
        return f'<Payment {self.date} - {self.value}>'
