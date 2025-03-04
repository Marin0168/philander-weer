// Initialiseer de kaart
const map = L.map('map').setView([52.3676, 4.9041], 6); // Start in Amsterdam
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Haal route-informatie op en teken de route
async function drawRoute() {
    const response = await fetch('/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
    });

    const data = await response.json();

    // Loop door de routepunten en teken lijnen
    data.forEach(segment => {
        if (segment.error) {
            console.error(`Fout voor segment ${segment.start.name} naar ${segment.end.name}: ${segment.error}`);
            return;
        }

        // Start- en eindcoördinaten
        const startCoords = segment.start.location.split(',').map(Number);
        const endCoords = segment.end.location.split(',').map(Number);

        // Voeg polyline toe met dynamische kleur
        L.polyline([startCoords, endCoords], { color: segment.color })
            .addTo(map)
            .bindPopup(`
                <strong>Van:</strong> ${segment.start.name}<br>
                <strong>Tot:</strong> ${segment.end.name}<br>
                <strong>Cloud Base:</strong> ${segment.cloud_base} m<br>
                <strong>Kleur:</strong> ${segment.color}
            `);
    });
}

// Roep de functie aan om de route te tekenen
drawRoute();

// Logica voor kaartklik om voorspellingen te tonen
map.on('click', async function (e) {
    const { lat, lng } = e.latlng;
    const resultDiv = document.getElementById('result');

    // Gebruik OpenStreetMap's Nominatim API voor omgekeerde geocoding
    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
    const data = await response.json();

    const location = data.address.city || data.address.town || data.address.village || "Onbekend";
    resultDiv.innerHTML = `<p>Geselecteerde locatie: ${location} (${lat.toFixed(5)}, ${lng.toFixed(5)})</p>`;

    // Stuur de locatie naar jouw server om het weer te voorspellen
    fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location: location })
    })
        .then(res => res.json())
        .then(prediction => {
            if (prediction.error) {
                resultDiv.innerHTML += `<p style="color: red;">Error: ${prediction.error}</p>`;
            } else {
                console.log(prediction);
                resultDiv.innerHTML += `
                <h3>Voorspelling</h3>
                <p>VVN: ${prediction.VVN}</p>
                <p>VVX: ${prediction.VVX}</p>
                <p>Cloud Base: ${prediction.cloud_base}</p>
            `;
            }
        })
        .catch(err => {
            resultDiv.innerHTML += `<p style="color: red;">Serverfout: ${err.message}</p>`;
        });
});
