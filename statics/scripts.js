document.addEventListener('DOMContentLoaded', function () {
  const input = document.getElementById('datepicker');
  const specialist_id = '12345678';

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

  if (!input) {
    console.error('Input не найден');
    return;
  }

  const chosenDateStr = getQueryParam('choose_date');
  const chosenDate = chosenDateStr ? parseISODate(chosenDateStr) : null;

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
});
