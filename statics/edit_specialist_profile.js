const getForm = document.forms['editSpecialistProfile']

getForm.onsubmit = async (e) => {
    e.preventDefault()

    const formData = new FormData(getForm)

    const submitData = {}

    for (const [key, value] of formData) {
        submitData[key] = value
    }

    let response = await fetch(`/specialist-update/${user.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData)
    })

    let result = await response.json();
    console.log(result)
    alert('Успех!')
}