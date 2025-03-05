document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const appointmentModal = new bootstrap.Modal(document.getElementById('appointmentModal'));
    const deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    
    let calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridWorkWeek,timeGridDay'
        },
        views: {
            timeGridWorkWeek: {
                type: 'timeGrid',
                duration: { days: 5 },
                buttonText: 'Semana Útil'
            }
        },
        slotMinTime: '07:00:00',
        slotMaxTime: '20:00:00',
        slotDuration: '01:00:00',
        allDaySlot: false,
        locale: 'pt-br',
        editable: true,
        selectable: true,
        selectMirror: true,
        dayMaxEvents: true,
        businessHours: {
            daysOfWeek: [1, 2, 3, 4, 5],
            startTime: '08:00',
            endTime: '19:00',
        },
        select: function(info) {
            // Clear form
            document.getElementById('appointmentForm').reset();
            document.getElementById('appointmentDate').value = info.startStr.slice(0, 16);
            document.getElementById('appointmentId').value = '';
            
            // Show modal for new appointment
            document.getElementById('modalTitle').textContent = 'Nova Consulta';
            document.getElementById('deleteButton').style.display = 'none';
            appointmentModal.show();
        },
        eventClick: function(info) {
            // Populate form with event data
            const event = info.event;
            document.getElementById('appointmentId').value = event.id;
            document.getElementById('appointmentDate').value = event.start.toISOString().slice(0, 16);
            document.getElementById('patientId').value = event.extendedProps.patientId;
            document.getElementById('value').value = event.extendedProps.value;
            document.getElementById('notes').value = event.extendedProps.notes;
            
            if (event.extendedProps.isRecurring) {
                document.getElementById('is_recurring').checked = true;
                document.getElementById('recurrence_frequency').value = event.extendedProps.recurrenceFrequency;
                if (event.extendedProps.recurrenceUntil) {
                    document.getElementById('recurrence_until').value = event.extendedProps.recurrenceUntil;
                }
            }
            
            // Show modal for editing
            document.getElementById('modalTitle').textContent = 'Editar Consulta';
            document.getElementById('deleteButton').style.display = 'block';
            appointmentModal.show();
        },
        eventDrop: function(info) {
            updateAppointment(info.event);
        },
        eventResize: function(info) {
            updateAppointment(info.event);
        },
        events: '/api/appointments'
    });

    calendar.render();

    // Handle form submission
    document.getElementById('appointmentForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const appointmentId = formData.get('appointmentId');
        
        // Converter os dados do formulário para um objeto
        const data = Object.fromEntries(formData);
        
        // Corrigir o valor do checkbox is_recurring
        data.is_recurring = formData.has('is_recurring') ? 'on' : 'off';
        
        const url = appointmentId ? `/api/appointments/${appointmentId}` : '/api/appointments';
        const method = appointmentId ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                calendar.refetchEvents();
                appointmentModal.hide();
                showAlert('Consulta salva com sucesso!', 'success');
            } else {
                showAlert(data.message || 'Erro ao salvar consulta', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Erro ao salvar consulta', 'danger');
        });
    });

    // Handle delete button
    document.getElementById('deleteButton').addEventListener('click', function() {
        const appointmentId = document.getElementById('appointmentId').value;
        if (!appointmentId) return;
        
        appointmentModal.hide();
        document.getElementById('deleteConfirmId').value = appointmentId;
        deleteConfirmModal.show();
    });

    // Handle delete confirmation
    document.getElementById('deleteConfirmForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const appointmentId = document.getElementById('deleteConfirmId').value;
        
        fetch(`/api/appointments/${appointmentId}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                calendar.refetchEvents();
                deleteConfirmModal.hide();
                showAlert('Consulta excluída com sucesso!', 'success');
            } else {
                showAlert(data.message || 'Erro ao excluir consulta', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Erro ao excluir consulta', 'danger');
        });
    });

    // Helper function to update appointment after drag/resize
    function updateAppointment(event) {
        fetch(`/api/appointments/${event.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                date: event.start.toISOString(),
                patientId: event.extendedProps.patientId,
                value: event.extendedProps.value,
                notes: event.extendedProps.notes
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                event.revert();
                showAlert(data.message || 'Erro ao atualizar consulta', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            event.revert();
            showAlert('Erro ao atualizar consulta', 'danger');
        });
    }

    // Helper function to show alerts
    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.getElementById('alertContainer').appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 5000);
    }
});
