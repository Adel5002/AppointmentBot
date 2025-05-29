const tg = window.Telegram.WebApp;
const user = tg.initDataUnsafe.user;

const setCookies = fetch('/set-cookies/', {
    method: 'POST',
    headers: {
          'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        data: user
    })
})


async function createUserOnce() {
  const userKey = `user_created_${user.id}`;
  
  if (!localStorage.getItem(userKey)) {
    try {
      const response = await fetch('/user-create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: user.id,
          name: user.first_name,
          lastname: user.last_name,
        }),
      });

      if (response.ok) {
        console.log('User successfully created!');
        localStorage.setItem(userKey, 'true');
      } else {
        const errorText = await response.text();
        console.error('Ошибка создания пользователя:', errorText);
      }
    } catch (error) {
      console.error('Ошибка при создании пользователя:', error);
    }
  } else {
    console.log('Пользователь уже создавался ранее.');
  }
}

document.addEventListener('DOMContentLoaded', createUserOnce);
