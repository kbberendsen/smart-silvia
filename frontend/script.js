let temperatureData = [];
let timeLabels = [];
let targetTemperature = 0;

// Function to send control commands to the machine
async function controlMachine(action) {
    try {
        const response = await fetch(`/${action}`);
        if (!response.ok) throw new Error('Failed to control machine');
        const text = await response.text();
        updateStatus(text, 'green-dot', 'green-text');
    } catch (error) {
        console.error('Error:', error);
        updateStatus('Error', 'red-dot', 'red-text');
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
        const text = await response.text();
        updateStatus(`Mode: ${text}`, 'green-dot', 'green-text');
        fetchTargetTemperature(); // Fetch the target temperature when mode changes
    } catch (error) {
        console.error('Error:', error);
        updateStatus('Error', 'red-dot', 'red-text');
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

        // Update the temperature graph
        const currentTime = new Date().toLocaleTimeString();
        if (temperatureData.length >= 20) {
            temperatureData.shift();
            timeLabels.shift();
        }
        temperatureData.push(parseFloat(temp));
        timeLabels.push(currentTime);
        updateChart();
    } catch (error) {
        console.error('Error:', error);
        updateTemperatureStatus(null); // Set status to orange dot when temperature cannot be read
        updateStatus('Error', 'red-dot', 'red-text'); // Update status to error
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

// Function to open the set temperature page
function openSetTemperaturePage() {
    window.location.href = 'set_temp.html';
}

// Function to set the new temperature setpoint and redirect back to index.html
async function setSetpoint() {
    const setpoint = document.getElementById('setpoint').value;
    try {
        const response = await fetch('/setpoint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `setpoint=${setpoint}`
        });
        if (!response.ok) throw new Error('Failed to set setpoint');
        const text = await response.text();
        updateStatus(`Setpoint: ${text}`, 'green-dot', 'green-text');
        window.location.href = 'index.html';  // Redirect back to index.html after setting the temperature
    } catch (error) {
        console.error('Error:', error);
        updateStatus('Error', 'red-dot', 'red-text');
    }
}

// Initialize Chart.js chart with empty data
const ctx = document.getElementById('tempChart').getContext('2d');
const tempChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: timeLabels,
        datasets: [{
            label: 'Temperature (°C)',
            data: temperatureData,
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 2,
            fill: false
        }]
    },
    options: {
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'second'
                },
                title: {
                    display: true,
                    text: 'Time'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Temperature (°C)'
                }
            }
        }
    }
});

// Function to update the chart with new data
function updateChart() {
    tempChart.update();
}

// Periodically fetch the temperature every second
setInterval(fetchTemperature, 1000);

// Initial calls to fetch temperature and target temperature
fetchTemperature();
fetchTargetTemperature();
