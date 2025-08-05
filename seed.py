import os
import random
from datetime import datetime, timedelta, time
from decimal import Decimal

from faker import Faker
from werkzeug.security import generate_password_hash

from gerenciador_psicologia.app import create_app
from gerenciador_psicologia.extensions import db
from gerenciador_psicologia.models import (
    Patient,
    Appointment,
    Payment,
)

fake = Faker("pt_BR")


def clear_data():
    """Limpa os dados das tabelas na ordem correta para evitar erros de FK."""
    try:
        # A ordem de deleção é importante por causa das foreign keys
        db.session.query(Payment).delete()
        db.session.query(Appointment).delete()
        db.session.query(Patient).delete()
        db.session.commit()
        print("Tabelas Payment, Appointment e Patient limpas com sucesso.")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao limpar os dados: {e}")


def create_patients(num_patients=10):
    """Cria pacientes falsos."""
    patients = []
    for _ in range(num_patients):
        patient = Patient(
            name=fake.name(),
            birth_date=fake.date_of_birth(minimum_age=18, maximum_age=70),
            phone=fake.phone_number(),
            email=fake.email(),
            notes=fake.paragraph(nb_sentences=2),
            is_active=True
        )
        patients.append(patient)
    db.session.add_all(patients)
    db.session.commit()
    return patients


def create_recurrent_appointments(patients):
    """Cria consultas recorrentes para os pacientes."""
    today = datetime.now()
    start_date = today - timedelta(days=60)  # 2 meses atrás
    end_date = today + timedelta(days=30)  # 1 mês no futuro

    # Horários fixos de segunda a sexta, 2 pacientes por dia
    schedule_slots = {
        0: [time(8, 0), time(9, 0)],   # Segunda
        1: [time(10, 0), time(11, 0)], # Terça
        2: [time(14, 0), time(15, 0)], # Quarta
        3: [time(16, 0), time(17, 0)], # Quinta
        4: [time(9, 0), time(10, 0)],  # Sexta
    }

    patient_index = 0
    for day_of_week, times in schedule_slots.items():
        for slot_time in times:
            if patient_index >= len(patients):
                break

            patient = patients[patient_index]
            current_date = start_date
            session_value = Decimal(random.choice([120, 150, 180, 200]))

            while current_date.date() <= end_date.date():
                if current_date.weekday() == day_of_week:
                    appointment_datetime = datetime.combine(current_date.date(), slot_time)
                    
                    status = "Paga"
                    if appointment_datetime > today:
                        status = "Agendada"
                    # Marca como 'Realizada' se for na última semana e ainda não paga
                    elif (today - appointment_datetime).days <= 7:
                        status = "Realizada"

                    appointment = Appointment(
                        patient_id=patient.id,
                        date=appointment_datetime,
                        status=status,
                        value=session_value,
                        notes=f"Sessão recorrente para {patient.name}.",
                    )
                    db.session.add(appointment)
                    db.session.commit()  # Commit para obter o ID

                    if status == "Paga":
                        payment = Payment(
                            appointment_id=appointment.id,
                            patient_id=patient.id,
                            value=appointment.value,
                            date=appointment_datetime.date(),
                            payment_type='income',
                            notes="Pagamento referente à sessão."
                        )
                        db.session.add(payment)

                current_date += timedelta(days=1)
            patient_index += 1
    db.session.commit()


def create_expenses():
    """Cria despesas mensais falsas para os últimos 3 meses."""
    today = datetime.now()
    for i in range(3):  # 3 meses de despesas
        # Define o primeiro dia do mês para cada iteração
        month_date = today.replace(day=1) - timedelta(days=i * 30)

        expenses = [
            {"notes": "Aluguel do Consultório", "value": Decimal(random.uniform(1200, 1800))},
            {"notes": "Conta de Luz", "value": Decimal(random.uniform(150, 250))},
            {"notes": "Conta de Água", "value": Decimal(random.uniform(80, 120))},
            {"notes": "Impostos (Simples Nacional)", "value": Decimal(random.uniform(400, 700))},
            {"notes": "Materiais de Escritório", "value": Decimal(random.uniform(50, 150))},
        ]

        for expense in expenses:
            payment = Payment(
                value=expense["value"],
                date=month_date.replace(day=random.randint(5, 20)),  # Paga em um dia aleatório do mês
                payment_type='expense',
                notes=expense["notes"]
            )
            db.session.add(payment)
    db.session.commit()


def main():
    """Função principal para popular o banco de dados."""
    app = create_app()
    with app.app_context():
        print("Iniciando o processo de seeding...")
        clear_data()
        
        patients = create_patients()
        print(f"{len(patients)} pacientes criados.")

        create_recurrent_appointments(patients)
        print("Consultas e pagamentos recorrentes criados.")

        create_expenses()
        print("Despesas mensais criadas.")

        print("Seeding concluído com sucesso!")


if __name__ == "__main__":
    main()
