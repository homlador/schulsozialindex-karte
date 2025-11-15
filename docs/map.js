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
let schoolsWithGradients = new Map();
// Schulen, die unter aktuellen Filtern (Schultyp & Entfernung) wirklich eine angezeigte Linie haben
let filteredGradientSchoolNumbers = new Set();
// Gecachte Gradient-Daten nach Schultyp und Distanzbereich
let gradientCache = {
    'gs': { '0-1': null, '1-2': null, '2-3': null, '3-4': null, '4-5': null },
    'wf': { '0-1': null, '1-2': null, '2-3': null, '3-4': null, '4-5': null }
};
let sliderTimeout = null;

// Aktualisieren der Statistik in den Optionen (Anzahl der Schulen in aktueller Auswahl)
function updateStatistics(schools) {
    // Ermittle verfügbare Schultypen aus den Checkboxen
    const availableTypes = Array.from(document.querySelectorAll('.school-type-control input:not(#type-all)'))
        .map(checkbox => checkbox.value);
    
    // Zähle Schulen pro Typ (nur für verfügbare Typen)
    const stats = {};
    availableTypes.forEach(type => {
        stats[type] = 0;
    });
    
    schools.forEach(school => {
        // Nur zählen, wenn der Schultyp in der Liste der verfügbaren Typen ist
        if (availableTypes.includes(school.schultyp) && 
            (searchTerm === '' || school.name.toLowerCase().includes(searchTerm))) {
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

// Radius der Marker anhand der Anzahl der Schülerinnen und Schüler berechnen
function getRadius(anzahl) {    
    const dynamic = document.getElementById('dynamicRadius').checked;
    if (dynamic) {
        const base = Math.sqrt(anzahl) * 0.3;   // Skalierung
        return Math.min(base, 12);              // Maximale Grösse
    } else {
        return 5;
    }
}

// Überprüfen der Nähe zu existierenden Markern: Marker sollen nicht übereinander platziert werden
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

// Finden einer freien Position
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

// Aktualisieren der Marker basierend auf den Filtereinstellungen und der Suche
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
        const showOnlyWithSozialindex = document.getElementById('showOnlyWithSozialindex')?.checked;
        const hasSozialindex = school.sozialindex && school.sozialindex !== '';
        
        const hasCurrentGradient = filteredGradientSchoolNumbers.has(school.schulnummer);
        if (activeTypes.includes(school.schultyp) && 
            (searchTerm === '' || 
             school.name.toLowerCase().includes(searchTerm) ||
             school.schulnummer.toString().includes(searchTerm)) &&
            (!showOnlyGradientSchools || hasCurrentGradient) &&
            (!showOnlyWithSozialindex || hasSozialindex)) {
            const color = getColorForIndex(school.sozialindex);
            const lat = parseFloat(school.latitude);
            const lng = parseFloat(school.longitude);
            
            // Zusätzliche Prüfung entfällt: wir nutzen nur aktuell angezeigte Gradienten

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
            
            // Startchancen-Ring nur erstellen, wenn die Option aktiviert ist und die Schule sichtbar ist
            let startchancenRing = null;
            if (school['startchancen'] === "1" && document.getElementById('showStartchancenHighlight').checked) {
                startchancenRing = L.circleMarker([finalLat, finalLng], {
                    radius: getRadius(school.anzahl) + 2,
                    fillColor: 'transparent',
                    color: '#0066FF',
                    weight: 3,
                    opacity: 1
                });
                startchancenRing.addTo(map);
                // Ring zum Marker-Array hinzufügen, damit er später entfernt werden kann
                markers.push(startchancenRing);
            }
            
            // Erstelle den eigentlichen Marker
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
                    Startchancen-Schule: ${school.startchancen == '1'?  'Ja' : 'Nein'}<br>
                    Anzahl: ${school.anzahl}<br>
                    Schulnummer: ${school.schulnummer}<br>
                    ${school.adresse}
                `);
            markers.push(marker);
        }
    });
    updateGradients();
}

// Laden der Schuldaten
function loadSchoolData(jsonFile) {
    fetch(jsonFile)
        .then(response => response.json())
        .then(schools => {
            // Schulen global verfügbar machen
            window.schools = schools;
            // Marker aktualisieren
            updateMarkers(schools);
            // Gradienten für initiale Distanz laden
            const initialDistance = parseFloat(document.getElementById('maxGradientDistance').value);
            loadGradientsForDistance(initialDistance).then(() => {
                if (document.getElementById('showGradients').checked) {
                    updateGradients();
                }
                updateMarkers(window.schools);
            });
        })
        .catch(error => {
            console.error('Fehler beim Laden der Schuldaten:', error);
        });
}

// Laden der Gradienten basierend auf der gewählten Distanz und aktiven Schultypen
async function loadGradientsForDistance(maxDistance) {    
    const ranges = [];
    
    // Bestimme welche Bereiche geladen werden müssen
    if (maxDistance > 0) ranges.push('0-1');
    if (maxDistance > 1) ranges.push('1-2');
    if (maxDistance > 2) ranges.push('2-3');
    if (maxDistance > 3) ranges.push('3-4');
    if (maxDistance > 4) ranges.push('4-5');

    
    // Ermittle aktive Schultypen
    const activeTypes = Array.from(document.querySelectorAll('.school-type-control input:checked:not(#type-all)'))
        .map(checkbox => checkbox.value);
    
    const hasGrundschule = activeTypes.includes('Grundschule');
    const hasWeiterfuehrende = activeTypes.some(type => 
        ['Hauptschule', 'Realschule', 'Sekundarschule', 'Gesamtschule', 'Gymnasium', 'PRIMUS-Schule'].includes(type)
    );
    
    // Lade fehlende Bereiche für relevante Schultypen
    const loadPromises = [];
    
    if (hasGrundschule) {
        ranges.forEach(range => {
            if (!gradientCache.gs[range]) {
                loadPromises.push(
                    fetch(`schools-gradients-gs-${range}km.json`)
                        .then(response => response.json())
                        .then(data => {
                            gradientCache.gs[range] = data;
                            console.log(`Geladen: GS ${range}km (${data.length} Gradienten)`);
                        })
                        .catch(error => {
                            console.error(`Fehler beim Laden von GS ${range}km:`, error);
                            gradientCache.gs[range] = [];
                        })
                );
            }
        });
    }
    
    if (hasWeiterfuehrende) {
        ranges.forEach(range => {
            if (!gradientCache.wf[range]) {
                loadPromises.push(
                    fetch(`schools-gradients-wf-${range}km.json`)
                        .then(response => response.json())
                        .then(data => {
                            gradientCache.wf[range] = data;
                            console.log(`Geladen: WF ${range}km (${data.length} Gradienten)`);
                        })
                        .catch(error => {
                            console.error(`Fehler beim Laden von WF ${range}km:`, error);
                            gradientCache.wf[range] = [];
                        })
                );
            }
        });
    }
    
    await Promise.all(loadPromises);
    
    // Kombiniere alle relevanten Daten
    gradientsData = [];
    ranges.forEach(range => {
        if (hasGrundschule && gradientCache.gs[range]) {
            gradientsData.push(...gradientCache.gs[range]);
        }
        if (hasWeiterfuehrende && gradientCache.wf[range]) {
            gradientsData.push(...gradientCache.wf[range]);
        }
    });
    
    // Map der Schulen mit Gradienten aktualisieren
    schoolsWithGradients.clear();
    gradientsData.forEach(gradient => {
        if (!schoolsWithGradients.has(gradient.schule_1.schulnummer)) {
            schoolsWithGradients.set(gradient.schule_1.schulnummer, []);
        }
        schoolsWithGradients.get(gradient.schule_1.schulnummer).push(gradient.schule_2);
        if (!schoolsWithGradients.has(gradient.schule_2.schulnummer)) {
            schoolsWithGradients.set(gradient.schule_2.schulnummer, []);
        }
        schoolsWithGradients.get(gradient.schule_2.schulnummer).push(gradient.schule_1);
    });
}

// Finden der korrigierten Position einer Schule
function getAdjustedSchoolPosition(school) {
    const lat = parseFloat(school.lat || school.latitude);
    const lng = parseFloat(school.lon || school.longitude);
    
    if (isNaN(lat) || isNaN(lng)) {
        console.warn(`Ungültige Koordinaten für Schule: ${school.name || school.schulnummer}`);
        return null;
    }

    // Suche nach einem existierenden Marker für diese Schule
    const existingMarker = markers.find(m => {
        if (!m.getPopup()) return false;
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

// Aktualisieren der Gradienten
function updateGradients() {
    // Bestehende Gradient-Linien entfernen
    gradientLines.forEach(line => line.remove());
    gradientLines = [];
    filteredGradientSchoolNumbers.clear();
    
    if (!document.getElementById('showGradients').checked) {
        document.getElementById('gradientCount').textContent = '0';
        return;
    }

    // Aktive Schultypen ermitteln
    const activeTypes = Array.from(document.querySelectorAll('.school-type-control input:checked:not(#type-all)'))
        .map(checkbox => checkbox.value);

    // Maximale Entfernung ermitteln
    const maxDistance = parseFloat(document.getElementById('maxGradientDistance').value);

    const schoolNumbersInData = new Set(window.schools.map(s => s.schulnummer));

    let gradientCount = 0;
    gradientsData.forEach(gradient => {
        // Prüfe ob beide Schulnummern im aktuell angezeigten Datensatz der Schulen in window.schools sind        
        if (!schoolNumbersInData.has(gradient.schule_1.schulnummer) || 
            !schoolNumbersInData.has(gradient.schule_2.schulnummer)) {
            return; // Gradient überspringen wenn eine der Schulen nicht im Datensatz ist
        }
        
        // Prüfen ob beide Schulen zu den aktiven Schultypen gehören
        if (!activeTypes.includes(gradient.schule_1.schultyp) || 
            !activeTypes.includes(gradient.schule_2.schultyp)) {
            return; // Gradient überspringen wenn eine der Schulen nicht aktiv ist
        }

        // Prüfen ob die Entfernung innerhalb des eingestellten Bereichs liegt
        if (gradient.entfernung_km > maxDistance) {
            return; // Gradient überspringen wenn die Entfernung zu groß ist
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

        // Namen der Schulen aus window.schools holen
        const school1 = window.schools.find(s => s.schulnummer === gradient.schule_1.schulnummer);
        const school2 = window.schools.find(s => s.schulnummer === gradient.schule_2.schulnummer);
 
        // Popup mit Gradient-Informationen
        line.bindPopup(`
            Gradient: ${gradient.gradient.toFixed(2)}<br>
            Entfernung: ${(gradient.entfernung_km * 1000).toFixed(0)}m<br>
            Sozialindex-Differenz: ${gradient.differenz}<br>
            Schule 1: ${school1.name} (SI: ${school1.sozialindex})<br>
            Schule 2: ${school2.name} (SI: ${school2.sozialindex})
        `);

        gradientLines.push(line);
        filteredGradientSchoolNumbers.add(gradient.schule_1.schulnummer);
        filteredGradientSchoolNumbers.add(gradient.schule_2.schulnummer);
        gradientCount++;
    });
    
    // Aktualisiere die Anzeige der Gradientenzahl
    document.getElementById('gradientCount').textContent = gradientCount;
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
    document.getElementById('gradientCount').innerHTML = '<span class="spinner">⏳</span>';         
    (async () => await loadGradientsForDistance(document.getElementById('maxGradientDistance').value))();
    updateGradients();
});

// Event-Listener für die "Nur Schulen mit Gradienten"-Checkbox
document.getElementById('showOnlyGradientSchools').addEventListener('change', function(e) {
    updateMarkers(window.schools);
});

// Event-Listener für die "Nur Schulen mit Sozialindex"-Checkbox
document.getElementById('showOnlyWithSozialindex').addEventListener('change', function(e) {
    updateMarkers(window.schools);
});

// Event-Listener für die "Startchancen-Schulen markieren"-Checkbox
document.getElementById('showStartchancenHighlight').addEventListener('change', function(e) {
    updateMarkers(window.schools);
});

// Event-Listener für den Entfernungs-Slider mit Debouncing
document.getElementById('maxGradientDistance').addEventListener('input', function(e) {
    document.getElementById('gradientCount').innerHTML = '<span class="spinner">⏳</span>';
    const newDistance = parseFloat(e.target.value);
    document.getElementById('maxDistanceValue').textContent = newDistance;
    
    // Debounce: Nur alle 300ms aktualisieren
    clearTimeout(sliderTimeout);
    sliderTimeout = setTimeout(async () => {
        // Lade Daten für neue Distanz falls nötig
        await loadGradientsForDistance(newDistance);
        updateGradients();
        updateMarkers(window.schools);
    }, 300);
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

// Toggle-Funktionalität für Optionen initialisieren
setupToggle('toggleOptions', 'optionsContent');
