const appointmentDeleteForm = document.forms['deleteAppointment']

appointmentDeleteForm.onsubmit = async (e) => {
    e.preventDefault()

    const formData = new FormData(appointmentDeleteForm)
    await fetch(`/appointment-delete/${formData.get('appointment_id')}`, {
        method: 'DELETE'
    })
}