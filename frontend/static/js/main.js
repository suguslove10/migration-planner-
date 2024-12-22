// API endpoints
const API_URL = '/api';
const ENDPOINTS = {
    analyze: `${API_URL}/analyze`,
    estimate: `${API_URL}/estimate`,
    roadmap: `${API_URL}/roadmap`,
    servers: `${API_URL}/servers`,
    upload: `${API_URL}/upload-test-data`
};

// State management
let currentServers = [];
let selectedServer = null;

// UI Elements
const serverList = document.getElementById('serverList');
const analysisResults = document.getElementById('analysisResults');
const costEstimate = document.getElementById('costEstimate');
const roadmapTimeline = document.getElementById('roadmapTimeline');
const loadingIndicator = document.getElementById('loadingIndicator');
const uploadForm = document.getElementById('uploadForm');

// Initialize the application
async function initializeApp() {
    try {
        await checkAwsConfiguration();
        await loadDiscoveredServers();
        updateFreeTierUsage();
        setupEventListeners();
    } catch (error) {
        showError('Failed to initialize application: ' + error.message);
    }
}

// Check AWS configuration
async function checkAwsConfiguration() {
    const response = await fetch(`${API_URL}/check-config`);
    const { configured, mode } = await response.json();
    
    if (!configured) {
        showError('AWS configuration not found. Please configure AWS credentials or use test data.');
        return;
    }

    if (mode === 'test') {
        showMessage('Running in test mode with sample data');
    }
}

// Load discovered servers
async function loadDiscoveredServers() {
    showLoading(true);
    try {
        const response = await fetch(ENDPOINTS.servers);
        const data = await response.json();
        currentServers = data.servers;
        renderServerList();
    } catch (error) {
        showError('Failed to load servers: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Render server list
function renderServerList() {
    serverList.innerHTML = currentServers.map(server => `
        <div class="server-item" data-server-id="${server.serverId}">
            <div class="server-header">
                <h3>${server.serverName}</h3>
                <span class="status status-${getServerStatus(server)}">
                    ${server.status || 'Active'}
                </span>
            </div>
            <div class="server-details">
                <p><i class="fas fa-server"></i> Type: ${server.serverType}</p>
                <p><i class="fas fa-desktop"></i> OS: ${server.osName} ${server.osVersion}</p>
                <p><i class="fas fa-microchip"></i> CPU: ${server.metrics.cpu.cores} cores (${server.metrics.cpu.utilization}% used)</p>
                <p><i class="fas fa-memory"></i> Memory: ${formatBytes(server.metrics.memory.total)} (${getUsagePercentage(server.metrics.memory)}% used)</p>
                <p><i class="fas fa-hdd"></i> Storage: ${formatBytes(server.metrics.storage.total)} (${getUsagePercentage(server.metrics.storage)}% used)</p>
            </div>
        </div>
    `).join('');

    // Add click event listeners to server items
    document.querySelectorAll('.server-item').forEach(item => {
        item.addEventListener('click', () => {
            const serverId = item.dataset.serverId;
            analyzeServer(serverId);
        });
    });
}

// Upload test data
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('testDataFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('Please select a file to upload');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showLoading(true);
        const response = await fetch(ENDPOINTS.upload, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showMessage('Test data uploaded successfully');
            currentServers = result.servers;
            renderServerList();
        } else {
            showError(result.error || 'Failed to upload test data');
        }
    } catch (error) {
        showError('Error uploading test data: ' + error.message);
    } finally {
        showLoading(false);
    }
});

// Analyze server
async function analyzeServer(serverId) {
    showLoading(true);
    try {
        const response = await fetch(ENDPOINTS.analyze, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ serverId })
        });
        
        const analysis = await response.json();
        renderAnalysisResults(analysis);
        await estimateCosts(serverId);
    } catch (error) {
        showError('Failed to analyze server: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Estimate costs
async function estimateCosts(serverId) {
    try {
        const response = await fetch(ENDPOINTS.estimate, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ serverId })
        });
        
        const estimate = await response.json();
        renderCostEstimate(estimate);
    } catch (error) {
        showError('Failed to estimate costs: ' + error.message);
    }
}

// Generate migration roadmap
async function generateRoadmap() {
    showLoading(true);
    try {
        const response = await fetch(ENDPOINTS.roadmap, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ servers: currentServers })
        });
        
        const roadmap = await response.json();
        renderRoadmap(roadmap);
    } catch (error) {
        showError('Failed to generate roadmap: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Render analysis results
function renderAnalysisResults(analysis) {
    analysisResults.innerHTML = `
        <div class="analysis-content">
            <h3>Complexity: ${analysis.complexity.level}</h3>
            <div class="complexity-score">
                Score: ${analysis.complexity.score}/10
            </div>
            <p>${analysis.complexity.description}</p>
            
            <h3>Migration Strategy: ${analysis.migrationStrategy.strategy}</h3>
            <div class="risk-level ${analysis.migrationStrategy.risk_level.toLowerCase()}">
                Risk Level: ${analysis.migrationStrategy.risk_level}
            </div>
            <p>${analysis.migrationStrategy.description}</p>
            
            <h3>Dependencies</h3>
            <ul class="dependencies-list">
                ${analysis.dependencies.map(dep => `
                    <li>
                        <span class="dependency-type">${dep.type}</span>
                        ${dep.name}
                    </li>
                `).join('')}
            </ul>
        </div>
    `;
}

// Render cost estimate
function renderCostEstimate(estimate) {
    costEstimate.innerHTML = `
        <div class="cost-content">
            <div class="cost-summary">
                <h3>Monthly Cost Analysis</h3>
                <div class="cost-grid">
                    <div class="cost-item">
                        <span class="label">Current Cost:</span>
                        <span class="value">₹${(estimate.currentMonthlyCost || 0).toLocaleString()}</span>
                    </div>
                    <div class="cost-item">
                        <span class="label">Projected Cost:</span>
                        <span class="value">₹${(estimate.projectedMonthlyCost || 0).toLocaleString()}</span>
                    </div>
                    <div class="cost-item savings">
                        <span class="label">Monthly Savings:</span>
                        <span class="value">₹${(estimate.monthlySavings || 0).toLocaleString()}</span>
                    </div>
                </div>
            </div>

            <div class="recommendations">
                <h3>Recommendations</h3>
                <div class="compute-recommendation">
                    <h4>Compute Resources</h4>
                    <ul>
                        <li>Instance Type: ${estimate.recommendations?.compute?.instanceType || 'N/A'}</li>
                        <li>vCPUs: ${estimate.recommendations?.compute?.specs?.cpu || 'N/A'}</li>
                        <li>Memory: ${estimate.recommendations?.compute?.specs?.memory || 'N/A'} GB</li>
                        <li>Monthly Cost: ₹${(estimate.recommendations?.compute?.monthlyCost || 0).toLocaleString()}</li>
                    </ul>
                </div>
                <div class="storage-recommendation">
                    <h4>Storage Resources</h4>
                    <ul>
                        <li>Type: ${estimate.recommendations?.storage?.type || 'N/A'}</li>
                        <li>Size: ${estimate.recommendations?.storage?.sizeGB || 'N/A'} GB</li>
                        <li>Monthly Cost: ₹${(estimate.recommendations?.storage?.monthlyCost || 0).toLocaleString()}</li>
                    </ul>
                </div>
            </div>

            <div class="roi-analysis">
                <h3>ROI Analysis</h3>
                <div class="roi-grid">
                    <div class="roi-item">
                        <span class="label">Migration Cost:</span>
                        <span class="value">₹${(estimate.migrationCost || 0).toLocaleString()}</span>
                    </div>
                    <div class="roi-item">
                        <span class="label">Break-even Period:</span>
                        <span class="value">${((estimate.roiMonths || 0).toFixed(1))} months</span>
                    </div>
                    <div class="roi-item">
                        <span class="label">3-Year Savings:</span>
                        <span class="value">₹${(estimate.threeYearSavings || 0).toLocaleString()}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Render roadmap
function renderRoadmap(roadmap) {
    const timelineContainer = document.getElementById('roadmapTimeline');
    timelineContainer.innerHTML = '';

    roadmap.timeline.forEach(phase => {
        const phaseElement = document.createElement('div');
        phaseElement.className = 'roadmap-phase';
        phaseElement.innerHTML = `
            <h3>${phase.name}</h3>
            <div class="duration">${phase.duration} (${phase.startDate} - ${phase.endDate})</div>
            <ul>
                ${phase.tasks.map(task => `<li>${task}</li>`).join('')}
            </ul>
        `;
        timelineContainer.appendChild(phaseElement);
    });

    // Add project summary
    const summaryElement = document.createElement('div');
    summaryElement.className = 'project-summary';
    summaryElement.innerHTML = `
        <h3>Project Summary</h3>
        <p>Total Duration: ${roadmap.projectSummary.duration}</p>
        <p>Total Servers: ${roadmap.projectSummary.totalServers}</p>
        <p>Total Effort: ${roadmap.projectSummary.totalEffort} hours</p>
        <p>Critical Path: ${roadmap.projectSummary.criticalPath.join(' > ')}</p>
    `;
    timelineContainer.appendChild(summaryElement);
}

// Update Free Tier usage
function updateFreeTierUsage() {
    fetch('/api/free-tier-usage')
        .then(response => response.json())
        .then(data => {
            document.getElementById('lambdaUsage').textContent = `${data.lambda.used}/${data.lambda.limit} invocations`;
            document.getElementById('s3Usage').textContent = `${data.s3.used}/${data.s3.limit} GB`;
            document.getElementById('dynamoUsage').textContent = `${data.dynamodb.used}/${data.dynamodb.limit} GB`;
            document.getElementById('apiUsage').textContent = `${data.apiGateway.used}/${data.apiGateway.limit} calls`;
        })
        .catch(error => console.error('Error fetching Free Tier usage:', error));
}

// Update progress bar
function updateProgressBar(progress) {
    const progressBar = document.querySelector('.progress');
    progressBar.style.width = `${progress}%`;
}

// Utility functions
function formatBytes(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let value = bytes;
    let unitIndex = 0;
    
    while (value >= 1024 && unitIndex < units.length - 1) {
        value /= 1024;
        unitIndex++;
    }
    
    return `${value.toFixed(2)} ${units[unitIndex]}`;
}

function getUsagePercentage(metric) {
    return ((metric.used / metric.total) * 100).toFixed(1);
}

function getServerStatus(server) {
    const cpuUtilization = server.metrics.cpu.utilization;
    if (cpuUtilization > 80) return 'danger';
    if (cpuUtilization > 60) return 'warning';
    return 'success';
}

function showLoading(show) {
    loadingIndicator.style.display = show ? 'flex' : 'none';
    document.body.classList.toggle('loading', show);
    if (show) {
        loadingIndicator.style.opacity = '0';
        setTimeout(() => {
            loadingIndicator.style.opacity = '1';
        }, 10);
    }
}

function showMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'alert alert-success';
    messageDiv.textContent = message;
    document.body.appendChild(messageDiv);
    setTimeout(() => messageDiv.remove(), 3000);
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger';
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
}

// Event listeners
function setupEventListeners() {
    // Server selection
    serverList.addEventListener('click', (e) => {
        const serverItem = e.target.closest('.server-item');
        if (serverItem) {
            const serverId = serverItem.dataset.serverId;
            selectedServer = currentServers.find(s => s.serverId === serverId);
            analyzeServer(serverId);
        }
    });

    // Generate roadmap button
    const roadmapBtn = document.getElementById('generateRoadmap');
    if (roadmapBtn) {
        roadmapBtn.addEventListener('click', generateRoadmap);
    }

    // Refresh button
const refreshBtn = document.getElementById('refreshServers');
if (refreshBtn) {
    refreshBtn.addEventListener('click', loadDiscoveredServers);
}

// Add event listener to update Free Tier usage periodically
setInterval(updateFreeTierUsage, 60000); // Update every minute
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);