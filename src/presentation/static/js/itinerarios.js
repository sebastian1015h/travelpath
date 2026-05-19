// Autocomplete con debounce — guarda IATA, lat, lon y dispara callback
function setupAutocomplete(inputId, listId, hiddenIataId, hiddenLatId, hiddenLonId, onSelect) {
  const input  = document.getElementById(inputId);
  const list   = document.getElementById(listId);
  const hidden = document.getElementById(hiddenIataId);
  const hidLat = hiddenLatId ? document.getElementById(hiddenLatId) : null;
  const hidLon = hiddenLonId ? document.getElementById(hiddenLonId) : null;
  let timer;

  input.addEventListener('input', () => {
    const q = input.value.trim();
    hidden.value = '';
    if (hidLat) hidLat.value = '';
    if (hidLon) hidLon.value = '';
    clearTimeout(timer);
    if (q.length < 2) { list.classList.remove('open'); list.innerHTML = ''; return; }
    timer = setTimeout(() => buscarAeropuerto(q, list, input, hidden, hidLat, hidLon, onSelect), 300);
  });

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !list.contains(e.target))
      list.classList.remove('open');
  });
}

async function buscarAeropuerto(query, list, input, hidden, hidLat, hidLon, onSelect) {
  list.innerHTML = '<div class="autocomplete-item" style="color:var(--text-muted);pointer-events:none;">Buscando...</div>';
  list.classList.add('open');

  try {
    const res = await apiFetch(`/api/aeropuertos?nombre=${encodeURIComponent(query)}`);

    if (!res.ok) {
      list.innerHTML = '<div class="autocomplete-item" style="color:#ef4444;pointer-events:none;">Error al conectar con el servidor</div>';
      return;
    }

    const data = await res.json();

    if (data.error) {
      list.innerHTML = `<div class="autocomplete-item" style="color:#ef4444;pointer-events:none;">${data.error}</div>`;
      return;
    }

    list.innerHTML = '';
    if (!data.length) {
      list.innerHTML = '<div class="autocomplete-item" style="color:var(--text-muted);pointer-events:none;">Sin resultados para "' + query + '"</div>';
      return;
    }

    data.slice(0, 10).forEach(a => {
      const item = document.createElement('div');
      item.className = 'autocomplete-item';
      item.innerHTML = `<span class="ac-iata">${a.iata}</span> ${a.nombre} — ${a.ciudad}, ${a.pais}`;
      item.addEventListener('click', () => {
        input.value  = `${a.iata} — ${a.nombre}`;
        hidden.value = a.iata;
        if (hidLat) hidLat.value = a.latitud  ?? '';
        if (hidLon) hidLon.value = a.longitud ?? '';
        list.classList.remove('open');
        list.innerHTML = '';
        if (onSelect) onSelect();
      });
      list.appendChild(item);
    });
  } catch {
    list.innerHTML = '<div class="autocomplete-item" style="color:#ef4444;pointer-events:none;">Sin conexión con el servidor</div>';
  }
}
