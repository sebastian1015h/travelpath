// Helpers de autenticación compartidos (complementa base.html)
function getUsuario() {
  try { return JSON.parse(localStorage.getItem('usuario') || '{}'); } catch { return {}; }
}

function isLoggedIn() {
  return !!localStorage.getItem('access_token');
}
