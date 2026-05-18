function renderizarMapa(origen, destino) {
  const gc = granCirculo(origen.latitud, origen.longitud, destino.latitud, destino.longitud, 80);

  // Arco de gran círculo
  const ruta = {
    type: 'scattermapbox',
    lat: gc.lats,
    lon: gc.lons,
    mode: 'lines',
    line: { width: 3, color: '#3B82F6' },
    hoverinfo: 'none',
    name: 'Ruta',
  };

  // Marcadores de aeropuertos
  const marcadores = {
    type: 'scattermapbox',
    lat: [origen.latitud, destino.latitud],
    lon: [origen.longitud, destino.longitud],
    mode: 'markers+text',
    marker: {
      size: [18, 18],
      color: ['#3B82F6', '#10B981'],
      symbol: 'airport',
    },
    text: [origen.iata, destino.iata],
    textfont: { size: 13, color: '#F9FAFB', family: 'Syne, sans-serif' },
    textposition: 'top right',
    hovertext: [
      `<b>${origen.iata}</b><br>${origen.nombre}<br>${origen.ciudad}, ${origen.pais}<br>` +
      `📍 ${origen.latitud?.toFixed(4)}°, ${origen.longitud?.toFixed(4)}°`,
      `<b>${destino.iata}</b><br>${destino.nombre}<br>${destino.ciudad}, ${destino.pais}<br>` +
      `📍 ${destino.latitud?.toFixed(4)}°, ${destino.longitud?.toFixed(4)}°`,
    ],
    hoverinfo: 'text',
    name: 'Aeropuertos',
  };

  // Punto de origen (anillo exterior azul)
  const anilloOrigen = {
    type: 'scattermapbox',
    lat: [origen.latitud],
    lon: [origen.longitud],
    mode: 'markers',
    marker: { size: 28, color: 'rgba(59,130,246,0.25)', symbol: 'circle' },
    hoverinfo: 'none',
    showlegend: false,
  };

  // Punto de destino (anillo exterior verde)
  const anilloDestino = {
    type: 'scattermapbox',
    lat: [destino.latitud],
    lon: [destino.longitud],
    mode: 'markers',
    marker: { size: 28, color: 'rgba(16,185,129,0.25)', symbol: 'circle' },
    hoverinfo: 'none',
    showlegend: false,
  };

  const centerLat = (origen.latitud + destino.latitud) / 2;
  const centerLon = midLon(origen.longitud, destino.longitud);
  const zoom = calcularZoom(origen.latitud, origen.longitud, destino.latitud, destino.longitud);

  const layout = {
    mapbox: {
      style: 'open-street-map',
      center: { lat: centerLat, lon: centerLon },
      zoom: zoom,
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { t: 0, b: 0, l: 0, r: 0 },
    showlegend: false,
    hoverlabel: {
      bgcolor: '#1E2130',
      bordercolor: '#374151',
      font: { color: '#F9FAFB', family: 'IBM Plex Sans, sans-serif', size: 13 },
    },
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d'],
    displaylogo: false,
  };

  Plotly.newPlot('mapa', [anilloOrigen, anilloDestino, ruta, marcadores], layout, config);
}

// Genera puntos del arco de gran círculo entre dos coordenadas
function granCirculo(lat1, lon1, lat2, lon2, n) {
  const toR = d => d * Math.PI / 180;
  const toD = r => r * 180 / Math.PI;

  const φ1 = toR(lat1), λ1 = toR(lon1);
  const φ2 = toR(lat2), λ2 = toR(lon2);

  const d = 2 * Math.asin(Math.sqrt(
    Math.sin((φ2 - φ1) / 2) ** 2 +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin((λ2 - λ1) / 2) ** 2
  ));

  const lats = [], lons = [];
  for (let i = 0; i <= n; i++) {
    const f = i / n;
    if (d < 0.0001) { lats.push(lat1); lons.push(lon1); continue; }
    const A = Math.sin((1 - f) * d) / Math.sin(d);
    const B = Math.sin(f * d) / Math.sin(d);
    const x = A * Math.cos(φ1) * Math.cos(λ1) + B * Math.cos(φ2) * Math.cos(λ2);
    const y = A * Math.cos(φ1) * Math.sin(λ1) + B * Math.cos(φ2) * Math.sin(λ2);
    const z = A * Math.sin(φ1) + B * Math.sin(φ2);
    lats.push(toD(Math.atan2(z, Math.sqrt(x ** 2 + y ** 2))));
    lons.push(toD(Math.atan2(y, x)));
  }
  return { lats, lons };
}

// Calcula zoom según la distancia entre aeropuertos
function calcularZoom(lat1, lon1, lat2, lon2) {
  const dlat = Math.abs(lat2 - lat1);
  const dlon = Math.abs(lon2 - lon1);
  const dist = Math.max(dlat, dlon);
  if (dist > 80) return 2;
  if (dist > 40) return 3;
  if (dist > 20) return 4;
  if (dist > 10) return 5;
  if (dist > 4)  return 6;
  return 7;
}

// Calcula longitud central evitando el anti-meridiano
function midLon(lon1, lon2) {
  let d = lon2 - lon1;
  if (d > 180)  d -= 360;
  if (d < -180) d += 360;
  let mid = lon1 + d / 2;
  if (mid > 180)  mid -= 360;
  if (mid < -180) mid += 360;
  return mid;
}
