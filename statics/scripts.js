document.addEventListener('DOMContentLoaded', function () {
  const wrapper = document.querySelector('#calendarWrapper');

  if (!wrapper) {
    console.log('Календарь не найден на этой странице');
    return;
  }

  flatpickr(wrapper, {
    wrap: true,
    defaultDate: 'today',
    dateFormat: 'd/m/Y',
  });
});
