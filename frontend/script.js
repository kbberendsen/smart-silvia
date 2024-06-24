let targetTemperature = 0;

// Function to update the status message and dot color
function updateStatus(text, dotClass, textClass) {
    const statusText = document.getElementById('statusText');
    const statusDot = document.getElementById('statusDot');
    statusText.innerText = text;
    statusText.className = `status-text ${textClass}`; // Apply the color to the text
    statusDot.className = `status-dot ${dotClass}`;
    document.getElementById('statusMessage').classList.remove('hidden');
}

// Function to update the temperature status dot
function updateTemperatureStatus(currentTemp) {
    const tempStatusDot = document.getElementById('tempStatusDot');
    if (currentTemp === null) {
        tempStatusDot.className = 'status-dot orange-dot'; // Display orange dot when temperature cannot be read
    } else {
        const tempDiff = Math.abs(currentTemp - targetTemperature);
        if (tempDiff <= 1) {
            tempStatusDot.className = 'status-dot green-dot';
        } else {
            tempStatusDot.className = 'status-dot orange-dot';
        }
    }
}

// Function to fetch and display the target temperature
async function fetchTargetTemperature() {
    try {
        const response = await fetch('/targetTemperature');
        if (!response.ok) throw new Error('Failed to fetch target temperature');
        const targetTemp = await response.text();
        targetTemperature = parseFloat(targetTemp);
        document.getElementById('targetTemperature').innerText = targetTemp;
    } catch (error) {
        console.error('Error:', error);
    }
}

// Function to set the machine mode (coffee or steam)
async function setMode() {
    const mode = document.getElementById('mode').value;
    try {
        const response = await fetch('/mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `mode=${mode}`
        });
        if (!response.ok) throw new Error('Failed to set mode');
        await response.text();
        await fetchTargetTemperature(); // Fetch the target temperature when mode changes
    } catch (error) {
        console.error('Error:', error);
    }
}

// Function to periodically fetch the current temperature
async function fetchTemperature() {
    try {
        const response = await fetch('/temperature');
        if (!response.ok) throw new Error('Failed to fetch temperature');
        const temp = await response.text();
        document.getElementById('temperature').innerText = temp;
        updateTemperatureStatus(parseFloat(temp));
        updateStatus('Online', 'green-dot', 'green-text'); // Update status to online
    } catch (error) {
        console.error('Error:', error);
        updateTemperatureStatus(null); // Set status to orange dot when temperature cannot be read
        updateStatus('Error', 'red-dot', 'red-text'); // Update status to error
    }
}

// Initial data fetch and periodic updates
async function initialLoad() {
    try {
        await fetchInitialData();
        updateStatus('Online', 'green-dot', 'green-text'); // Update status to online after initial data fetch
        setInterval(fetchTemperature, 1000); // Periodically fetch the temperature every second
    } catch (error) {
        console.error('Error during initial load:', error);
        updateStatus('Error', 'red-dot', 'red-text'); // Update status to error if initial load fails
    }
}

// Function to fetch initial data (mode and temperature)
async function fetchInitialData() {
    try {
        const response = await fetch('/initialData');
        if (!response.ok) throw new Error('Failed to fetch initial data');
        const data = await response.json();
        document.getElementById('temperature').innerText = data.currentTemperature;
        document.getElementById('targetTemperature').innerText = data.targetTemperature;
        document.getElementById('mode').value = data.mode;
        updateTemperatureStatus(parseFloat(data.currentTemperature));
        targetTemperature = parseFloat(data.targetTemperature);
    } catch (error) {
        console.error('Error:', error);
        updateStatus('Error', 'red-dot', 'red-text'); // Update status to error
    }
}

// Call initialLoad when the window loads
window.onload = initialLoad;
