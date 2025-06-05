const tg = window.Telegram.WebApp;
const user = tg.initDataUnsafe?.user;


window.addEventListener('DOMContentLoaded', async () => {
    tg.ready();

    if (!user) return;

    
    if (document.cookie.includes("firstname=")) return;

    await fetch('/set-cookies/', {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
          data: user
      })
    });

    window.location.reload(); 
  });


  const response = fetch('/user-create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: user.id,
          name: user.first_name,
          lastname: user.last_name,
          tg_username: user.username,
        }),
      });

      if (response.ok) {
        console.log('User successfully created!');
        localStorage.setItem(userKey, 'true');
      } else {
        const errorText = response.text();
        console.error('Ошибка создания пользователя:', errorText);
      }

// async function createUserOnce() {
//   const userKey = `user_created_${user.id}`;
  
//   if (!localStorage.getItem(userKey)) {
//     try {
//       const response = await fetch('/user-create/', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({
//           id: user.id,
//           name: user.first_name,
//           lastname: user.last_name,
//           tg_username: user.username,
//         }),
//       });

//       if (response.ok) {
//         console.log('User successfully created!');
//         localStorage.setItem(userKey, 'true');
//       } else {
//         const errorText = await response.text();
//         console.error('Ошибка создания пользователя:', errorText);
//       }
//     } catch (error) {
//       console.error('Ошибка при создании пользователя:', error);
//     }
//   } else {
//     console.log('Пользователь уже создавался ранее.');
//   }
// }

// document.addEventListener('DOMContentLoaded', createUserOnce);
