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

// Globale Variablen für Marker und Gradienten
let markers = [];
let gradientLines = [];
let searchTerm = '';
let gradientsData = [];
let schoolsWithGradients = new Set();

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
// Radius anhand der Anzahl berechnen
function getRadius(anzahl) {    
    const dynamic = document.getElementById('dynamicRadius').checked;
    if (dynamic) {
        const base = Math.sqrt(anzahl) * 0.3;   // Skalierung
        return Math.min(base, 12);              // Maximale Grösse
    } else {
        return 5;
    }
}

// Funktion zum Überprüfen der Nähe zu existierenden Markern
function isNearOtherMarker(lat, lng, markers) {
    if (!lat || !lng || !markers.length) return false;
    
    const minDistance = 0.0002; // ca. 20-30 Meter
    return markers.some(marker => {
        try {
            const pos = marker.getLatLng();
            const dx = pos.lat - lat;
            const dy = pos.lng - lng;
            return Math.sqrt(dx * dx + dy * dy) < minDistance;
        } catch (e) {
            console.error('Fehler beim Prüfen der Marker-Position:', e);
            return false;
        }
    });
}

// Funktion zum Finden einer freie Position
function findFreePosition(lat, lng, markers) {
    const offset = 0.0002;
    const angles = [0, 45, 90, 135, 180, 225, 270, 315]; // 8 Richtungen
    
    for (let angle of angles) {
        const radian = angle * Math.PI / 180;
        const newLat = lat + Math.cos(radian) * offset;
        const newLng = lng + Math.sin(radian) * offset;
        
        if (!isNearOtherMarker(newLat, newLng, markers)) {
            return [newLat, newLng];
        }
    }
    
    return [lat, lng]; // Fallback zur ursprünglichen Position
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
        const showOnlyGradientSchools = document.getElementById('showOnlyGradientSchools')?.checked;
        if (activeTypes.includes(school.schultyp) && 
            (searchTerm === '' || 
             school.name.toLowerCase().includes(searchTerm) ||
             school.schulnummer.toString().includes(searchTerm)) &&
            (!showOnlyGradientSchools || schoolsWithGradients.has(school.schulnummer))) {
            const color = getColorForIndex(school.sozialindex);
            const lat = parseFloat(school.latitude);
            const lng = parseFloat(school.longitude);
            
            // Nur fortfahren, wenn gültige Koordinaten vorhanden sind
            if (isNaN(lat) || isNaN(lng)) {
                console.warn(`Ungültige Koordinaten für Schule: ${school.name}`);
                return;
            }

            let [finalLat, finalLng] = [lat, lng];
            
            // Prüfe und verschiebe nur, wenn es andere Marker gibt
            if (markers.length > 0 && isNearOtherMarker(lat, lng, markers)) {
                [finalLat, finalLng] = findFreePosition(lat, lng, markers);
            }
            
            const marker = L.circleMarker([finalLat, finalLng], {
                radius: getRadius(school.anzahl),
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
                    ${school.adresse}
                `);
            markers.push(marker);
        }
    });
    updateGradients();
}

// Funktion zum Laden der Schuldaten
function loadSchoolData(jsonFile) {
    fetch(jsonFile)
        .then(response => response.json())
        .then(schools => {
            // Schulen global verfügbar machen
            window.schools = schools;
            // Marker aktualisieren
            updateMarkers(schools);
            // Gradienten laden
            loadGradients();
        })
        .catch(error => {
            console.error('Fehler beim Laden der Schuldaten:', error);
        });
}

// Funktion zum Laden der Gradienten
function loadGradients() {
    fetch('schools-gradients.json')
        .then(response => response.json())
        .then(data => {
            gradientsData = data;
            // Set der Schulen mit Gradienten aktualisieren
            schoolsWithGradients.clear();
            data.forEach(gradient => {
                schoolsWithGradients.add(gradient.schule_1.schulnummer);
                schoolsWithGradients.add(gradient.schule_2.schulnummer);
            });
            if (document.getElementById('showGradients').checked) {
                updateGradients();
            }
            // Marker aktualisieren um ggf. nicht verbundene Schulen auszublenden
            updateMarkers(window.schools);
        })
        .catch(error => {
            console.error('Fehler beim Laden der Gradienten:', error);
        });
}

// Funktion zum Finden der korrigierten Position einer Schule
function getAdjustedSchoolPosition(school) {
    const lat = parseFloat(school.lat || school.latitude);
    const lng = parseFloat(school.lon || school.longitude);
    
    if (isNaN(lat) || isNaN(lng)) {
        console.warn(`Ungültige Koordinaten für Schule: ${school.name || school.schulnummer}`);
        return null;
    }

    // Suche nach einem existierenden Marker für diese Schule
    const existingMarker = markers.find(m => {
        const popupContent = m.getPopup().getContent();
        return popupContent.includes(school.schulnummer.toString());
    });

    if (existingMarker) {
        const pos = existingMarker.getLatLng();
        return [pos.lat, pos.lng];
    }

    // Falls kein Marker gefunden wurde, prüfe ob eine neue Position nötig ist
    if (markers.length > 0 && isNearOtherMarker(lat, lng, markers)) {
        return findFreePosition(lat, lng, markers);
    }

    return [lat, lng];
}

// Funktion zum Aktualisieren der Gradienten
function updateGradients() {
    // Bestehende Gradient-Linien entfernen
    gradientLines.forEach(line => line.remove());
    gradientLines = [];
    
    if (!document.getElementById('showGradients').checked) {
        return;
    }

    // Aktive Schultypen ermitteln
    const activeTypes = Array.from(document.querySelectorAll('.school-type-control input:checked:not(#type-all)'))
        .map(checkbox => checkbox.value);

    gradientsData.forEach(gradient => {
        // Prüfen ob beide Schulen zu den aktiven Schultypen gehören
        if (!activeTypes.includes(gradient.schule_1.schultyp) || 
            !activeTypes.includes(gradient.schule_2.schultyp)) {
            return; // Gradient überspringen wenn eine der Schulen nicht aktiv ist
        }

        // Korrigierte Positionen für beide Schulen holen
        const pos1 = getAdjustedSchoolPosition(gradient.schule_1);
        const pos2 = getAdjustedSchoolPosition(gradient.schule_2);

        if (!pos1 || !pos2) return; // Überspringen wenn eine Position ungültig ist

        // Koordinaten mit Sozialindex als z-Wert für den Farbverlauf
        const coordinates = [
            [...pos1, gradient.schule_1.sozialindex],
            [...pos2, gradient.schule_2.sozialindex]
        ];
        
        // Berechne die Liniendicke basierend auf dem Gradientenwert
        const minWeight = 1;    // Minimale Liniendicke
        const maxWeight = 10;    // Maximale Liniendicke
        const weight = Math.min(maxWeight, minWeight + Math.abs(gradient.gradient) * 1.5);

        const line = L.hotline(coordinates, {
            weight: weight,
            outlineWidth: 0,
            palette: {
                0.0: '#00ff00',  // Sozialindex 1 (grün)
                0.5: '#ffff00',  // Sozialindex 5 (gelb)
                1.0: '#ff0000'   // Sozialindex 9 (rot)
            },
            min: 1,  // Minimaler Sozialindex
            max: 9   // Maximaler Sozialindex
        }).addTo(map);

        // Popup mit Gradient-Informationen
        line.bindPopup(`
            Gradient: ${gradient.gradient.toFixed(2)}<br>
            Entfernung: ${(gradient.entfernung_km * 1000).toFixed(0)}m<br>
            Sozialindex-Differenz: ${gradient.differenz}<br>
            Schule 1: ${gradient.schule_1.name} (SI: ${gradient.schule_1.sozialindex})<br>
            Schule 2: ${gradient.schule_2.name} (SI: ${gradient.schule_2.sozialindex})
        `);

        gradientLines.push(line);
    });
}

// Initial Schulen laden und Event-Listener einrichten
const datasetSelect = document.getElementById('datasetSelect');
if (datasetSelect && datasetSelect.options.length > 0) {
    loadSchoolData(datasetSelect.options[0].value);
}

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

// Event-Listener für Options-Änderungen
document.getElementById('dynamicRadius').addEventListener('change', function(e) {
    updateMarkers(window.schools);
});

// Event-Listener für die Gradienten-Checkbox
document.getElementById('showGradients').addEventListener('change', function(e) {
    updateGradients();
});

// Event-Listener für die "Nur Schulen mit Gradienten"-Checkbox
document.getElementById('showOnlyGradientSchools').addEventListener('change', function(e) {
    updateMarkers(window.schools);
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

// Toggle-Funktionalität für zusammenklappbare Bereiche
function setupToggle(buttonId, contentId) {
    const toggleButton = document.getElementById(buttonId);
    const content = document.getElementById(contentId);
    let isVisible = false;

    toggleButton.addEventListener('click', () => {
        isVisible = !isVisible;
        content.classList.toggle('hidden');
        toggleButton.textContent = isVisible ? '▼' : '▲';
    });
}

// Toggle-Funktionalität für Optionen und Erklärung initialisieren
setupToggle('toggleOptions', 'optionsContent');
setupToggle('toggleExplanation', 'explanationContent');
