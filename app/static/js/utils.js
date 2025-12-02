// async function createSession() {
//     const user = sessionStorage.getItem('user');
//     try {
//         const response = await fetch(`/api/session/create?user=${user}`);

//         if (!response.ok) {
//             throw Error('Fail to validate login information.')
//         }
//         const result = await response.json();

//         sessionStorage.setItem('session', result.session)
//     } catch (error) {
//         console.error(error)
//     }
// }


// function loadSession() {
//     var session = sessionStorage.getItem('session');
//     var pathname = window.location.pathname;
//     sessionStorage.removeItem('cache');
//     // we do is to reload the contents from the databse
//     fetch(`/api/session/load?session=${session}`).then(response => {
//         if (!response.ok) {
//             throw Error('Fail to load session data.');
//         }
//         return response.json()
//     }).then(result => {
//         if (!result.success) {
//             alert('Session expired. Please log in again.')
//             window.location.href = '/';
//         } else if (result.cache !== null && pathname in result.cache) {
//             Object.entries(result.cache[pathname]).forEach(([id, value]) => {
//                 if (document.getElementById(id)) {
//                     document.getElementById(id).value = value
//                 }
//             });
//             sessionStorage.setItem('cache', JSON.stringify(result.cache[pathname]))
//         }
//     })
// }