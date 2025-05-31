document.addEventListener('DOMContentLoaded', function () {
  function showCustomAlert() {
    document.getElementById('customModal').style.display = 'flex';
  }

  function closeModal() {
    document.getElementById('customModal').style.display = 'none';
  }

  const input = document.getElementById('datepicker');
  const specialist_id = document.getElementById('specialist-id').value

  function formatDateLocal(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function getQueryParam(param) {
    const params = new URLSearchParams(window.location.search);
    return params.get(param);
  }

  function parseISODate(isoStr) {
    const parts = isoStr.split('-');
    if (parts.length !== 3) return null;
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    return new Date(year, month, day);
  }

  const chosenDateStr = getQueryParam('choose_date');
  const chosenDate = chosenDateStr ? parseISODate(chosenDateStr) : null;

  if (!input) {
    console.error('Input не найден');
    return;
  }

  flatpickr(input, {
    defaultDate: chosenDate || 'today',
    dateFormat: 'd/m/Y',
    onChange: function(selectedDates) {
      if (selectedDates.length > 0) {
        const isoDate = formatDateLocal(selectedDates[0]);
        console.log('Выбрана дата:', isoDate);
        window.location.href = `/choose-datetime/${specialist_id}/?choose_date=${isoDate}`;
      }
    }
  });

  document.querySelectorAll('.time-slot-btn:not(.used)').forEach(button => {
    button.addEventListener('click', async () => {
      const time = button.getAttribute('data-time');
      const userId = button.getAttribute('data-user-id');
      const date = getQueryParam('choose_date');

      const payload = new URLSearchParams();
      payload.append('user_id', userId);
      payload.append('appointment_date', `${date}T${time}`);

      try {
        const userResponse = await fetch(`/user/${userId}`);
        const user = await userResponse.json();

        if (user.appointment) {
          showCustomAlert();

          const okButton = document.getElementById('okButton');
          const cancelButton = document.getElementById('cancelButton');

          if (okButton) {
            
            okButton.replaceWith(okButton.cloneNode(true));
            const newOkButton = document.getElementById('okButton');

            newOkButton.addEventListener('click', async function () {
              try {
                const deleteResponse = await fetch(`/appointment-delete/${user.appointment.id}`, {
                  method: 'DELETE'
                });

                if (deleteResponse.ok) {
                  const response = await fetch(`/get-date/${specialist_id}/?choose_date=${date}`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: payload.toString(),
                  });

                  if (response.ok) {
                    window.location.reload();
                  }
                }
              } catch (err) {
                console.error('Ошибка удаления:', err);
              }
            });
          }

          if (cancelButton) {
            cancelButton.replaceWith(cancelButton.cloneNode(true));
            const newCancelButton = document.getElementById('cancelButton');
            newCancelButton.addEventListener('click', function () {
              closeModal();
            });
          }

        } else {
          const response = await fetch(`/get-date/${specialist_id}/?choose_date=${date}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: payload.toString(),
          });

          if (response.ok) {
            window.location.reload();
          }
        }
      } catch (error) {
        console.log('Ошибка получения пользователя или брони:', error);
      }
    });
  });
});