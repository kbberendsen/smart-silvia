let statusTimeout = null;
let temporaryStatusActive = false;

// Function to update the status message and dot color
function updateStatus(text, dotClass, textClass, duration = 0) {
    const statusText = document.getElementById('statusText');
    const statusDot = document.getElementById('statusDot');
    statusText.innerText = text;
    statusText.className = `status-text ${textClass}`; // Apply the color to the text
    statusDot.className = `status-dot ${dotClass}`;
    document.getElementById('statusMessage').classList.remove('hidden');

    // Clear any existing timeout
    if (statusTimeout) {
        clearTimeout(statusTimeout);
        statusTimeout = null;
    }

    // If a duration is specified, reset the status after the duration
    if (duration > 0) {
        temporaryStatusActive = true;
        statusTimeout = setTimeout(() => {
            temporaryStatusActive = false;
            statusTimeout = null;
        }, duration);
    }
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
        console.error('Error fetching target temperature:', error);
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
        console.error('Error setting mode:', error);
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
        if (!temporaryStatusActive) { // Only update status if no manual status timeout is set
            updateStatus('Online', 'green-dot', 'green-text'); // Update status to online
        }
    } catch (error) {
        console.error('Error fetching temperature:', error);
        updateTemperatureStatus(null); // Set status to orange dot when temperature cannot be read
        if (!temporaryStatusActive) { // Only update status if no manual status timeout is set
            updateStatus('Error fetching temperature', 'red-dot', 'red-text');
        }
    }
}

// Initial data fetch and periodic updates
async function initialLoad() {
    try {
        await fetchInitialData();
        updateStatus('Online', 'green-dot', 'green-text'); // Update status to online after initial data fetch
        setInterval(async () => {
            try {
                await fetchTemperature();
            } catch (error) {
                if (!temporaryStatusActive) { // Only update status if no manual status timeout is set
                    updateStatus('Server disconnected', 'red-dot', 'red-text');
                }
            }
        }, 1000); // Periodically fetch the temperature every second
    } catch (error) {
        console.error('Error during initial load:', error);
        updateStatus('Error during initial load', 'red-dot', 'red-text', 3000); // Display error message for 3 seconds
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
        console.error('Error fetching initial data:', error);
        updateStatus('Error fetching initial data', 'red-dot', 'red-text', 3000); // Display error message for 3 seconds
    }
}

// Function to set temperature
async function setTemperature() {
    const newTemp = parseFloat(document.getElementById('tempInput').value);
    if (newTemp && newTemp >= 90 && newTemp <= 98) {
        try {
            const response = await fetch('/setTemperature', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `temperature=${newTemp}`
            });
            const responseBody = await response.text();
            if (!response.ok) {
                throw new Error(`Failed to set temperature: ${responseBody}`);
            }
            console.log('Set temperature response:', responseBody);
            updateStatus('New temperature set', 'green-dot', 'green-text', 3000); // Display message for 3 seconds
            await fetchTargetTemperature(); // Update the target temperature display
        } catch (error) {
            console.error('Error setting temperature:', error);
            updateStatus('Error setting temperature', 'red-dot', 'red-text', 3000); // Display error message for 3 seconds
        }
    } else {
        updateStatus('Invalid temperature', 'red-dot', 'red-text', 3000); // Display error message for 3 seconds
    }
}

// Call initialLoad when the window loads
window.onload = initialLoad;
