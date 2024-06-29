let statusTimeout = null;
let temporaryStatusActive = false;
let targetTemperature = null;
let temperatureData = []; // Array to store temperature data points
let timeData = []; // Array to store time points

// Function to update the status message and dot color
function updateStatus(text, dotClass, textClass, duration = 0) {
    console.log(`Updating status: ${text}`);
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
            updateStatus('Online', 'green-dot', 'green-text');
            statusTimeout = null;
        }, duration);
    }
}

// Function to update the temperature status dot
function updateTemperatureStatus(currentTemp) {
    console.log(`Updating temperature status: ${currentTemp}`);
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
        if (!temporaryStatusActive) {
            updateStatus('Error fetching target temperature', 'red-dot', 'red-text');
        }
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
        addTemperatureData(parseFloat(temp)); // Update the chart with the new temperature
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
        initializeChart(); // Initialize the temperature chart
        updateStatus('Online', 'green-dot', 'green-text'); // Update status to online after initial data fetch
        setInterval(fetchTemperature, 1000); // Periodically fetch the temperature every second
    } catch (error) {
        console.error('Error during initial load:', error);
        updateStatus('Error during initial load', 'red-dot', 'red-text');
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
        updateStatus('Error fetching initial data', 'red-dot', 'red-text');
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

// Function to initialize the Plotly.js temperature chart
function initializeChart() {
    const trace = {
        x: [],
        y: [],
        mode: 'lines',
        name: 'Temperature (°C)',
        line: { color: 'rgba(75, 192, 192, 1)' }
    };
    const data = [trace];
    const layout = {
        title: 'Temperature Over Time',
        xaxis: {
            title: 'Time',
            type: 'date'
        },
        yaxis: {
            title: 'Temperature (°C)',
            range: [0, 140] // Adjust y-axis to start from 0 and end at a reasonable value
        },
        paper_bgcolor: 'rgba(0,0,0,0)', // Set the paper background to transparent
        plot_bgcolor: 'rgba(0,0,0,0)', // Set the plot background to transparent
        autosize: true
    };
    Plotly.newPlot('tempChart', data, layout, {responsive: true});
}

// Function to add temperature data to the chart
function addTemperatureData(temp) {
    const now = new Date();
    const cutoffTime = new Date(now.getTime() - 60000);

    // Remove data older than 60 seconds
    while (timeData.length > 0 && timeData[0] < cutoffTime) {
        timeData.shift();
        temperatureData.shift();
    }

    timeData.push(now);
    temperatureData.push(temp);

    Plotly.extendTraces('tempChart', {
        x: [[now]],
        y: [[temp]]
    }, [0]);

    Plotly.relayout('tempChart', {
        'xaxis.range': [cutoffTime, now]
    });
}

// Call initialLoad when the window loads
window.onload = () => {
    initialLoad();
};
