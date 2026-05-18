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
  try {
    const res = await apiFetch(`/api/aeropuertos?nombre=${encodeURIComponent(query)}`);
    if (!res.ok) { list.classList.remove('open'); return; }
    const data = await res.json();

    list.innerHTML = '';
    if (!data.length) {
      list.innerHTML = '<div class="autocomplete-item" style="color:var(--text-muted);">Sin resultados</div>';
      list.classList.add('open');
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

    list.classList.add('open');
  } catch {
    list.classList.remove('open');
  }
}
