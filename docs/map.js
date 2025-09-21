// Karte initialisieren und auf Duisburg zentrieren
const map = L.map('map').setView([51.4344, 6.7623], 12);

// OpenStreetMap Layer hinzufügen
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Funktion um Farbe basierend auf Sozialindex zu bestimmen
function getColorForIndex(index) {
    // Farbskala von grün (Index 1) bis rot (Index 9)
    const colors = [
        '#00ff00', // 1 - Grün
        '#40ff00',
        '#80ff00',
        '#bfff00',
        '#ffff00', // 5 - Gelb
        '#ffbf00',
        '#ff8000',
        '#ff4000',
        '#ff0000'  // 9 - Rot
    ];
    return colors[index - 1] || '#808080'; // Grau als Fallback
}

// Globale Variable für alle Marker
let markers = [];
let searchTerm = '';

// Suchfeld Event-Listener
document.getElementById('schoolSearch').addEventListener('input', function(e) {
    searchTerm = e.target.value.toLowerCase();
    updateMarkers(window.schools);
});

// Reset-Button Event-Listener
document.getElementById('resetSearch').addEventListener('click', function() {
    document.getElementById('schoolSearch').value = '';
    searchTerm = '';
    updateMarkers(window.schools);
});

// Funktion zum Aktualisieren der Statistik
function updateStatistics(schools) {
    // Zähle Schulen pro Typ
    const stats = {};
    schools.forEach(school => {
        if (!stats[school.schultyp]) {
            stats[school.schultyp] = 0;
        }
        if (searchTerm === '' || school.name.toLowerCase().includes(searchTerm)) {
            stats[school.schultyp]++;
        }
    });

    // Update Statistik für jeden Schultyp
    document.querySelectorAll('.school-type-control').forEach(control => {
        const checkbox = control.querySelector('input');
        const label = control.querySelector('label');
        const countSpan = control.querySelector('.school-count');
        
        if (checkbox.id === 'type-all') {
            // Für "Alle" die Gesamtsumme berechnen
            const total = Object.values(stats).reduce((sum, count) => sum + count, 0);
            if (!countSpan) {
                label.innerHTML = `${label.textContent.split('(')[0]} (${total})`;
            } else {
                countSpan.textContent = `(${total})`;
            }
        } else {
            const count = stats[checkbox.value] || 0;
            if (!countSpan) {
                label.innerHTML = `${label.textContent.split('(')[0]} (${count})`;
            } else {
                countSpan.textContent = `(${count})`;
            }
        }
    });
}

// Funktion zum Aktualisieren der Marker basierend auf den Filtereinstellungen und der Suche
function updateMarkers(schools) {
    // Alle aktuellen Marker entfernen
    markers.forEach(marker => marker.remove());
    markers = [];

    // Statistik aktualisieren
    updateStatistics(schools);

    // Aktive Schultypen ermitteln
    const activeTypes = Array.from(document.querySelectorAll('.school-type-control input:checked:not(#type-all)'))
        .map(checkbox => checkbox.value);

    // Nur Schulen des ausgewählten Typs anzeigen, die dem Suchbegriff entsprechen
    schools.forEach(school => {
        if (activeTypes.includes(school.schultyp) && 
            (searchTerm === '' || school.name.toLowerCase().includes(searchTerm))) {
            const color = getColorForIndex(school.sozialindex);
            const marker = L.circleMarker([school.latitude, school.longitude], {
                radius: 8,
                fillColor: color,
                color: '#000',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            })
                .addTo(map)
                .bindPopup(`
                    <strong>${school.name} (${school.schultyp})</strong><br>
                    Sozialindex: ${school.sozialindex}<br>
                    Anzahl: ${school.anzahl}<br>
                    Schulnummer: ${school.schulnummer}<br>
                    ${school.address}
                `);
            markers.push(marker);
        }
    });
}

// Funktion zum Laden und Aktualisieren der Schulen
function loadSchoolData(jsonFile) {
    fetch(jsonFile)
        .then(response => response.json())
        .then(schools => {
            // Schulen global verfügbar machen
            window.schools = schools;
            // Marker aktualisieren
            updateMarkers(schools);
        })
        .catch(error => {
            console.error('Fehler beim Laden der Schuldaten:', error);
        });
}

// Initial Schulen laden und Event-Listener einrichten
const datasetSelect = document.getElementById('datasetSelect');
if (datasetSelect && datasetSelect.options.length > 0) {
    loadSchoolData(datasetSelect.options[0].value);
}

// Statistik-Spans für alle Labels erstellen
document.querySelectorAll('.school-type-control label').forEach(label => {
    const span = document.createElement('span');
    span.className = 'school-count';
    span.textContent = '(0)';
    label.appendChild(span);
});

// Event-Listener für Dropdown-Änderungen
document.getElementById('datasetSelect').addEventListener('change', function(e) {
    loadSchoolData(e.target.value);
});

// Event-Listener für Checkbox-Änderungen
document.querySelectorAll('.school-type-control input').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
        if (e.target.id === 'type-all') {
            // Wenn "Alle" geklickt wird, setze alle anderen Checkboxen auf den gleichen Status
            document.querySelectorAll('.school-type-control input:not(#type-all)').forEach(cb => {
                cb.checked = e.target.checked;
            });
        } else {
            // Wenn eine andere Checkbox geklickt wird, prüfe ob "Alle" angepasst werden muss
            const allCheckbox = document.getElementById('type-all');
            const otherCheckboxes = document.querySelectorAll('.school-type-control input:not(#type-all)');
            const allChecked = Array.from(otherCheckboxes).every(cb => cb.checked);
            allCheckbox.checked = allChecked;
        }
        updateMarkers(window.schools);
    });
});
