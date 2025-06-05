document.addEventListener('DOMContentLoaded', function () {
    const url = new URL(window.location.href);

    const alreadyRedirected = url.searchParams.has('choose_date');
    const fromError = url.searchParams.has('error');

    const specialist_id = window.Telegram.WebApp?.initDataUnsafe?.start_param;

    if (!alreadyRedirected && !fromError && specialist_id) {
        const today = new Date();
        const dateStr = today.toISOString().split('T')[0];

        window.location.href = `/choose-datetime/${specialist_id}/?choose_date=${dateStr}`;
    }
});

