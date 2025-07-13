document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const appointmentModal = new bootstrap.Modal(document.getElementById('appointmentModal'));
    const deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    const recurrenceEditModal = new bootstrap.Modal(document.getElementById('recurrenceEditModal'));
    
    let calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridWorkWeek,timeGridDay'
        },
        views: {
            timeGridWorkWeek: {
                type: 'timeGridWeek',
                buttonText: 'Semana Útil',
                hiddenDays: [0, 6] // Oculta domingo (0) e sábado (6)
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
            const event = info.event;
            if (event.extendedProps.isRecurring) {
                document.getElementById('recurrenceEditId').value = event.id;
                document.getElementById('recurrenceEditAction').value = 'edit';
                recurrenceEditModal.show();
            } else {
                // Populate form with event data
                document.getElementById('appointmentId').value = event.id;
                document.getElementById('appointmentDate').value = event.start.toISOString().slice(0, 16);
                document.getElementById('patientId').value = event.extendedProps.patientId;
                document.getElementById('value').value = event.extendedProps.value;
                document.getElementById('notes').value = event.extendedProps.notes;
                
                // Show modal for editing
                document.getElementById('modalTitle').textContent = 'Editar Consulta';
                document.getElementById('deleteButton').style.display = 'block';
                appointmentModal.show();
            }
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

        const event = calendar.getEventById(appointmentId);
        if (event && event.extendedProps.isRecurring) {
            appointmentModal.hide();
            document.getElementById('recurrenceEditId').value = appointmentId;
            document.getElementById('recurrenceEditAction').value = 'delete';
            recurrenceEditModal.show();
        } else {
            appointmentModal.hide();
            document.getElementById('deleteConfirmId').value = appointmentId;
            deleteConfirmModal.show();
        }
    });

    // Handle delete confirmation
    document.getElementById('deleteConfirmForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const appointmentId = document.getElementById('deleteConfirmId').value;
        const scope = document.getElementById('deleteConfirmScope').value || 'single';

        fetch(`/api/appointments/${appointmentId}?scope=${scope}`, {
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

    // Handle recurrence edit modal buttons
    document.getElementById('editOccurrenceBtn').addEventListener('click', function() {
        const appointmentId = document.getElementById('recurrenceEditId').value;
        const action = document.getElementById('recurrenceEditAction').value;
        
        recurrenceEditModal.hide();

        if (action === 'edit') {
            const event = calendar.getEventById(appointmentId);
            // Populate form with event data
            document.getElementById('appointmentId').value = event.id;
            document.getElementById('appointmentDate').value = event.start.toISOString().slice(0, 16);
            document.getElementById('patientId').value = event.extendedProps.patientId;
            document.getElementById('value').value = event.extendedProps.value;
            document.getElementById('notes').value = event.extendedProps.notes;
            
            // Show modal for editing
            document.getElementById('modalTitle').textContent = 'Editar Consulta';
            document.getElementById('deleteButton').style.display = 'block';
            appointmentModal.show();
        } else if (action === 'delete') {
            document.getElementById('deleteConfirmId').value = appointmentId;
            document.getElementById('deleteConfirmScope').value = 'single';
            deleteConfirmModal.show();
        }
    });

    document.getElementById('editSeriesBtn').addEventListener('click', function() {
        const appointmentId = document.getElementById('recurrenceEditId').value;
        const action = document.getElementById('recurrenceEditAction').value;

        recurrenceEditModal.hide();

        if (action === 'edit') {
            const event = calendar.getEventById(appointmentId);
            // Populate form with event data
            document.getElementById('appointmentId').value = event.id;
            document.getElementById('appointmentDate').value = event.start.toISOString().slice(0, 16);
            document.getElementById('patientId').value = event.extendedProps.patientId;
            document.getElementById('value').value = event.extendedProps.value;
            document.getElementById('notes').value = event.extendedProps.notes;
            
            // Show modal for editing
            document.getElementById('modalTitle').textContent = 'Editar Série de Consultas';
            document.getElementById('deleteButton').style.display = 'block';
            appointmentModal.show();
        } else if (action === 'delete') {
            document.getElementById('deleteConfirmId').value = appointmentId;
            document.getElementById('deleteConfirmScope').value = 'series';
            deleteConfirmModal.show();
        }
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
