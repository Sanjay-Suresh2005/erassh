// ERASH - Frontend JavaScript Application

const API_BASE = 'http://localhost:5000/api';

// Application State
const state = {
    devices: [],
    selectedDevice: null,
    activeOperations: {},
    certificates: [],
    currentFilter: 'all',
    pollingIntervals: {}
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadSystemInfo();
    // Don't auto-load devices - wait for user to click scan
});

// Event Listeners Setup
function initializeEventListeners() {
    // Device type filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            state.currentFilter = e.target.dataset.type;
            loadDevices();
        });
    });

    // Scan devices button (primary action)
    document.getElementById('scanDevicesBtn').addEventListener('click', () => scanDevices(true));

    // Refresh devices button
    document.getElementById('refreshDevicesBtn').addEventListener('click', () => scanDevices(false));

    // System info button
    document.getElementById('systemInfoBtn').addEventListener('click', showSystemInfo);

    // Ledger stats button
    document.getElementById('ledgerStatsBtn').addEventListener('click', showLedgerStats);

    // Verify button
    document.getElementById('verifyBtn').addEventListener('click', verifyBySerial);

    // Clear logs button
    document.getElementById('clearLogsBtn').addEventListener('click', clearLogs);

    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.modal').classList.remove('active');
        });
    });

    // Confirmation modal
    document.getElementById('confirmCheckbox').addEventListener('change', (e) => {
        document.getElementById('confirmEraseBtn').disabled = !e.target.checked;
    });

    document.getElementById('confirmCancelBtn').addEventListener('click', closeConfirmModal);
    document.getElementById('confirmEraseBtn').addEventListener('click', executeWipe);

    // Close modals on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
}

// Scan Devices (with animation)
async function scanDevices(showAnimation = true) {
    const deviceList = document.getElementById('deviceList');
    const scanStatus = document.getElementById('scanStatus');
    
    if (showAnimation) {
        scanStatus.style.display = 'block';
        deviceList.innerHTML = '<div class="loading">Scanning storage devices...</div>';
        addLog('🔍 Initiating device scan...');
        
        // Simulate scan delay for better UX
        await new Promise(resolve => setTimeout(resolve, 1000));
    } else {
        deviceList.innerHTML = '<div class="loading">Refreshing devices...</div>';
    }

    try {
        const filterType = state.currentFilter === 'all' ? '' : `type=${state.currentFilter}&`;
        const response = await fetch(`${API_BASE}/devices?${filterType}partitions=true`);
        const data = await response.json();

        if (data.success) {
            state.devices = data.devices;
            renderDevices(data.devices);
            
            if (showAnimation) {
                scanStatus.style.display = 'none';
            }
            
            addLog(`✅ Found ${data.count} device(s) with ${data.total_partitions} partition(s)`, 'success');
        } else {
            deviceList.innerHTML = `<div class="error">Error loading devices: ${data.error}</div>`;
            addLog(`❌ Scan failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error loading devices:', error);
        deviceList.innerHTML = '<div class="error">Failed to scan devices. Is the server running?</div>';
        addLog(`❌ Scan error: ${error.message}`, 'error');
        
        if (showAnimation) {
            scanStatus.style.display = 'none';
        }
    }
}

// Load Devices (backward compatibility)
async function loadDevices() {
    await scanDevices(false);
}

// Render Devices
function renderDevices(devices) {
    const deviceList = document.getElementById('deviceList');

    if (devices.length === 0) {
        deviceList.innerHTML = '<div class="no-operations">No devices found matching the filter</div>';
        return;
    }

    deviceList.innerHTML = devices.map(device => {
        const hasPartitions = device.partitions && device.partitions.length > 0;
        const partitionsHtml = hasPartitions ? `
            <div class="partitions-section">
                <div class="partitions-header partition-toggle" onclick="event.stopPropagation(); togglePartitions('${device.name}')">
                    <span id="toggle-icon-${device.name.replace(/\//g, '_')}">▼</span>
                    <span>${device.partition_count} Partition(s)</span>
                </div>
                <div class="partitions-list" id="partitions-${device.name.replace(/\//g, '_')}" style="display: none;">
                    ${device.partitions.map(partition => `
                        <div class="partition-item ${partition.mountpoint ? 'mounted' : ''}">
                            <div class="partition-name">${partition.name}</div>
                            <div class="partition-details">
                                Size: ${partition.size} | FS: ${partition.fstype} | Label: ${partition.label || 'None'}
                                ${partition.mountpoint ? `<br>📍 Mounted at: ${partition.mountpoint}` : ''}
                            </div>
                            <button class="btn btn-danger partition-select-btn" onclick="event.stopPropagation(); startWipe('${partition.name}', true)">
                                🗑️ Erase Partition
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : '';

        return `
            <div class="device-card ${hasPartitions ? 'has-partitions' : ''}" data-device="${device.name}" onclick="selectDevice('${device.name}')">
                <div class="device-header">
                    <span class="device-type-badge ${device.type.toLowerCase()}">${device.type}</span>
                    <span>${device.size}</span>
                </div>
                <div class="device-info">
                    <strong>${device.name}</strong>
                    <div><strong>Model:</strong> ${device.model}</div>
                    <div><strong>Serial:</strong> ${device.serial}</div>
                    <div><strong>Transport:</strong> ${device.transport}</div>
                </div>
                ${partitionsHtml}
                <div class="device-actions">
                    <button class="btn btn-danger" onclick="event.stopPropagation(); startWipe('${device.name}', false)">
                        🗑️ Erase Entire Disk
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Toggle Partitions Visibility
function togglePartitions(deviceName) {
    const cleanName = deviceName.replace(/\//g, '_');
    const partitionsList = document.getElementById(`partitions-${cleanName}`);
    const toggleIcon = document.getElementById(`toggle-icon-${cleanName}`);
    
    if (partitionsList.style.display === 'none') {
        partitionsList.style.display = 'flex';
        toggleIcon.textContent = '▲';
    } else {
        partitionsList.style.display = 'none';
        toggleIcon.textContent = '▼';
    }
}

// Select Device
function selectDevice(deviceName) {
    state.selectedDevice = deviceName;
    
    document.querySelectorAll('.device-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    document.querySelector(`[data-device="${deviceName}"]`)?.classList.add('selected');
}

// Start Wipe - Show Confirmation
function startWipe(deviceName, isPartition = false) {
    // Find device info
    let device = state.devices.find(d => d.name === deviceName);
    let targetInfo = null;
    let partitionInfo = null;
    
    if (!device && isPartition) {
        // It's a partition, find the parent device
        for (const dev of state.devices) {
            const partition = dev.partitions?.find(p => p.name === deviceName);
            if (partition) {
                device = dev;
                partitionInfo = partition;
                break;
            }
        }
    }
    
    if (!device) {
        addLog(`Error: Device ${deviceName} not found`, 'error');
        return;
    }

    state.selectedDevice = deviceName;

    // Get selected method and mode
    const method = document.getElementById('wipeMethod').value;
    const mode = document.querySelector('input[name="mode"]:checked').value;

    // Populate confirmation modal
    if (isPartition && partitionInfo) {
        document.getElementById('confirmDeviceInfo').innerHTML = `
            <div><strong>⚠️ Erasing Partition:</strong> ${deviceName}</div>
            <div><strong>Parent Device:</strong> ${device.name}</div>
            <div><strong>Size:</strong> ${partitionInfo.size}</div>
            <div><strong>Filesystem:</strong> ${partitionInfo.fstype}</div>
            <div><strong>Label:</strong> ${partitionInfo.label || 'None'}</div>
            ${partitionInfo.mountpoint ? `<div style="color: red;"><strong>⚠️ MOUNTED AT:</strong> ${partitionInfo.mountpoint}</div>` : ''}
            <div style="margin-top: 10px; padding: 10px; background: #fff3cd; border-radius: 6px;">
                <strong>Note:</strong> Only this partition will be erased, not the entire disk.
            </div>
        `;
    } else {
        document.getElementById('confirmDeviceInfo').innerHTML = `
            <div><strong>⚠️ Erasing Entire Disk:</strong> ${device.name}</div>
            <div><strong>Model:</strong> ${device.model}</div>
            <div><strong>Serial:</strong> ${device.serial}</div>
            <div><strong>Size:</strong> ${device.size}</div>
            ${device.partition_count > 0 ? `<div style="color: red;"><strong>⚠️ This will erase ALL ${device.partition_count} partition(s)!</strong></div>` : ''}
        `;
    }
    
    document.getElementById('confirmMode').textContent = mode === 'simulated' ? 'Simulated (Safe Demo)' : 'REAL ERASURE (DANGEROUS!)';
    document.getElementById('confirmMethod').textContent = getMethodName(method);
    
    // Reset checkbox
    document.getElementById('confirmCheckbox').checked = false;
    document.getElementById('confirmEraseBtn').disabled = true;

    // Show modal
    document.getElementById('confirmModal').classList.add('active');
}

// Execute Wipe
async function executeWipe() {
    // Find device - could be a full device or partition
    let device = state.devices.find(d => d.name === state.selectedDevice);
    let isPartition = false;
    let deviceInfo = null;
    
    if (!device) {
        // Check if it's a partition
        for (const dev of state.devices) {
            const partition = dev.partitions?.find(p => p.name === state.selectedDevice);
            if (partition) {
                device = dev;
                deviceInfo = partition;
                isPartition = true;
                break;
            }
        }
    } else {
        deviceInfo = device;
    }
    
    if (!device) {
        addLog('Error: Device not found', 'error');
        return;
    }

    const method = document.getElementById('wipeMethod').value;
    const mode = document.querySelector('input[name="mode"]:checked').value;
    const simulated = mode === 'simulated';

    closeConfirmModal();

    try {
        const response = await fetch(`${API_BASE}/wipe/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_path: state.selectedDevice, // Could be device or partition
                method: method,
                verification: false,
                simulated: simulated,
                confirmation: true
            })
        });

        const data = await response.json();

        if (data.success) {
            const targetName = isPartition ? `${state.selectedDevice} (partition)` : state.selectedDevice;
            addLog(`Started wipe operation on ${targetName}: ${data.wipe_id}`, 'success');
            
            // Add to active operations
            state.activeOperations[data.wipe_id] = {
                wipe_id: data.wipe_id,
                device: deviceInfo,
                devicePath: state.selectedDevice,
                method: method,
                status: 'running',
                progress: 0,
                isPartition: isPartition
            };

            renderOperations();
            
            // Start polling for status
            pollWipeStatus(data.wipe_id);
            
        } else {
            addLog(`Error starting wipe: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error starting wipe:', error);
        addLog(`Failed to start wipe: ${error.message}`, 'error');
    }
}

// Poll Wipe Status
function pollWipeStatus(wipeId) {
    let logIndex = 0;

    const interval = setInterval(async () => {
        try {
            // Get logs
            const logsResponse = await fetch(`${API_BASE}/wipe/logs/${wipeId}?since=${logIndex}`);
            const logsData = await logsResponse.json();

            if (logsData.success) {
                // Update progress
                if (state.activeOperations[wipeId]) {
                    state.activeOperations[wipeId].progress = logsData.progress;
                    state.activeOperations[wipeId].status = logsData.status;
                }

                // Add new logs
                logsData.logs.forEach(log => {
                    addLog(`[${wipeId.slice(-8)}] ${log.message}`);
                });

                logIndex = logsData.total_count;

                // Update UI
                renderOperations();

                // Check if completed
                if (logsData.status === 'completed' || logsData.status === 'failed') {
                    clearInterval(interval);
                    delete state.pollingIntervals[wipeId];
                    
                    if (logsData.status === 'completed') {
                        addLog(`Wipe ${wipeId} completed successfully!`, 'success');
                        // Auto-generate certificate
                        setTimeout(() => generateCertificate(wipeId), 1000);
                    } else {
                        addLog(`Wipe ${wipeId} failed!`, 'error');
                    }
                }
            }
        } catch (error) {
            console.error('Error polling wipe status:', error);
        }
    }, 1000);

    state.pollingIntervals[wipeId] = interval;
}

// Render Active Operations
function renderOperations() {
    const operationsList = document.getElementById('operationsList');
    const operations = Object.values(state.activeOperations);

    if (operations.length === 0) {
        operationsList.innerHTML = '<div class="no-operations">No active operations</div>';
        return;
    }

    operationsList.innerHTML = operations.map(op => {
        const targetName = op.devicePath || op.device.name;
        const targetType = op.isPartition ? 'Partition' : 'Disk';
        const deviceLabel = op.device.model || op.device.name || 'Unknown Device';
        
        return `
            <div class="operation-card">
                <div class="operation-header">
                    <div>
                        <strong>${targetName}</strong> ${op.isPartition ? '(Partition)' : ''}
                        <div style="font-size: 0.85rem; color: #6c757d;">
                            ${deviceLabel} | Method: ${getMethodName(op.method)} | Type: ${targetType}
                        </div>
                    </div>
                    <span class="operation-status ${op.status}">${op.status.toUpperCase()}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${op.progress}%">
                        ${op.progress}%
                    </div>
                </div>
                <div class="operation-actions">
                    ${op.status === 'completed' ? `
                        <button class="btn btn-success" onclick="generateCertificate('${op.wipe_id}')">
                            📄 Generate Certificate
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Generate Certificate
async function generateCertificate(wipeId) {
    const certMode = document.querySelector('input[name="certMode"]:checked').value;
    const recordOnBlockchain = certMode === 'blockchain';

    addLog(`Generating certificate for ${wipeId}...`);

    try {
        const response = await fetch(`${API_BASE}/certificate/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wipe_id: wipeId,
                record_on_blockchain: recordOnBlockchain
            })
        });

        const data = await response.json();

        if (data.success) {
            addLog(`Certificate generated: ${data.certificate.id}`, 'success');
            
            // Add to certificates list
            state.certificates.push(data.certificate);
            renderCertificates();

            if (recordOnBlockchain && data.ledger_entry) {
                addLog(`Recorded on blockchain: Block ${data.ledger_entry.block_index}`, 'success');
            }
        } else {
            addLog(`Error generating certificate: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error generating certificate:', error);
        addLog(`Failed to generate certificate: ${error.message}`, 'error');
    }
}

// Render Certificates
function renderCertificates() {
    const certificatesList = document.getElementById('certificatesList');

    if (state.certificates.length === 0) {
        certificatesList.innerHTML = '<div class="no-certificates">No certificates generated yet</div>';
        return;
    }

    certificatesList.innerHTML = state.certificates.map(cert => `
        <div class="certificate-card">
            <div class="certificate-icon">📜</div>
            <div class="certificate-info">
                <strong>Certificate ID:</strong><br>
                <code>${cert.id}</code><br>
                <small>Hash: ${cert.hash.substring(0, 16)}...</small>
            </div>
            <div class="certificate-actions">
                <button class="btn btn-primary" onclick="downloadCertificate('${cert.filename}')">
                    ⬇️ Download PDF
                </button>
                <button class="btn btn-secondary" onclick="showQRCode('${cert.id}')">
                    📱 Show QR
                </button>
            </div>
        </div>
    `).join('');
}

// Download Certificate
function downloadCertificate(filename) {
    window.open(`${API_BASE}/certificate/download/${filename}`, '_blank');
    addLog(`Downloading certificate: ${filename}`);
}

// Show QR Code
function showQRCode(certId) {
    const cert = state.certificates.find(c => c.id === certId);
    if (!cert) return;

    alert(`Verification URL:\n${cert.verification_url}\n\nScan the QR code in the PDF certificate to verify.`);
}

// Verify by Serial
async function verifyBySerial() {
    const serial = document.getElementById('verifySerial').value.trim();
    
    if (!serial) {
        alert('Please enter a device serial number');
        return;
    }

    addLog(`Searching for serial: ${serial}...`);

    try {
        const response = await fetch(`${API_BASE}/verify/serial/${encodeURIComponent(serial)}`);
        const data = await response.json();

        if (data.success) {
            showVerificationResults(data);
        } else {
            addLog('Verification request failed', 'error');
        }
    } catch (error) {
        console.error('Error verifying:', error);
        addLog(`Verification error: ${error.message}`, 'error');
    }
}

// Show Verification Results
function showVerificationResults(data) {
    const modal = document.getElementById('verificationModal');
    const content = document.getElementById('verificationContent');

    if (data.records.length === 0) {
        content.innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <p>No records found for serial number: <strong>${data.serial_number}</strong></p>
            </div>
        `;
    } else {
        content.innerHTML = `
            <p>Found <strong>${data.count}</strong> record(s) for serial: <strong>${data.serial_number}</strong></p>
            <div style="margin-top: 20px;">
                ${data.records.map(record => `
                    <div style="border: 1px solid #dee2e6; padding: 15px; margin-bottom: 10px; border-radius: 6px;">
                        <div><strong>Certificate ID:</strong> ${record.certificate_id}</div>
                        <div><strong>Timestamp:</strong> ${record.timestamp}</div>
                        <div><strong>Method:</strong> ${record.wipe_method}</div>
                        <div><strong>Status:</strong> ${record.wipe_status}</div>
                        <div><strong>Hash:</strong> <code>${record.certificate_hash.substring(0, 32)}...</code></div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    modal.classList.add('active');
}

// Show System Info
async function showSystemInfo() {
    const modal = document.getElementById('systemInfoModal');
    const content = document.getElementById('systemInfoContent');

    content.innerHTML = '<div class="loading">Loading system information...</div>';
    modal.classList.add('active');

    try {
        const response = await fetch(`${API_BASE}/system/info`);
        const data = await response.json();

        if (data.success) {
            const system = data.system;
            content.innerHTML = `
                <h3>${system.name} v${system.version}</h3>
                <p>${system.description}</p>
                
                <h4 style="margin-top: 20px;">Features:</h4>
                <ul>
                    ${system.features.map(f => `<li>${f}</li>`).join('')}
                </ul>
                
                <h4 style="margin-top: 20px;">Wipe Methods:</h4>
                <ul>
                    ${Object.entries(system.wipe_methods).map(([key, desc]) => 
                        `<li><strong>${key}:</strong> ${desc}</li>`
                    ).join('')}
                </ul>
                
                <h4 style="margin-top: 20px;">Configuration:</h4>
                <p><strong>Ledger Type:</strong> ${system.ledger_type}</p>
                
                <div class="warning-banner" style="margin-top: 20px;">
                    ${system.safety_warning}
                </div>
            `;
        }
    } catch (error) {
        content.innerHTML = `<div class="error">Failed to load system info: ${error.message}</div>`;
    }
}

// Show Ledger Stats
async function showLedgerStats() {
    const modal = document.getElementById('ledgerStatsModal');
    const content = document.getElementById('ledgerStatsContent');

    content.innerHTML = '<div class="loading">Loading ledger statistics...</div>';
    modal.classList.add('active');

    try {
        const response = await fetch(`${API_BASE}/ledger/stats`);
        const data = await response.json();

        if (data.success) {
            const stats = data.stats;
            content.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                    <div style="border: 1px solid #dee2e6; padding: 15px; border-radius: 6px;">
                        <h4>Total Blocks</h4>
                        <p style="font-size: 2rem; color: var(--primary-color); margin: 10px 0;">${stats.total_blocks || 0}</p>
                    </div>
                    <div style="border: 1px solid #dee2e6; padding: 15px; border-radius: 6px;">
                        <h4>Erasure Records</h4>
                        <p style="font-size: 2rem; color: var(--success-color); margin: 10px 0;">${stats.erasure_records || 0}</p>
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                    <div><strong>Ledger Type:</strong> ${stats.ledger_type || 'Unknown'}</div>
                    <div><strong>Created:</strong> ${stats.created_at || 'N/A'}</div>
                    <div><strong>Last Block:</strong> ${stats.last_block_time || 'N/A'}</div>
                    <div><strong>Chain Valid:</strong> 
                        <span style="color: ${stats.chain_valid ? 'green' : 'red'};">
                            ${stats.chain_valid ? '✓ Yes' : '✗ No'}
                        </span>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        content.innerHTML = `<div class="error">Failed to load ledger stats: ${error.message}</div>`;
    }
}

// Load System Info (for initialization)
async function loadSystemInfo() {
    try {
        const response = await fetch(`${API_BASE}/system/info`);
        const data = await response.json();
        if (data.success) {
            console.log('ERASH System initialized:', data.system);
        }
    } catch (error) {
        console.error('Error loading system info:', error);
    }
}

// Logging Functions
function addLog(message, type = 'info') {
    const logViewer = document.getElementById('logViewer');
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    const timestamp = new Date().toLocaleTimeString();
    
    logEntry.innerHTML = `
        <span class="log-timestamp">[${timestamp}]</span>
        <span class="log-message ${type}">${message}</span>
    `;
    
    // Remove empty state
    const emptyState = logViewer.querySelector('.log-empty');
    if (emptyState) emptyState.remove();
    
    logViewer.appendChild(logEntry);
    logViewer.scrollTop = logViewer.scrollHeight;
}

function clearLogs() {
    const logViewer = document.getElementById('logViewer');
    logViewer.innerHTML = '<div class="log-empty">Logs cleared</div>';
}

// Helper Functions
function getMethodName(method) {
    const methods = {
        'dodshort': 'DoD 5220.22-M (3 passes)',
        'dod': 'DoD 5220.22-M (7 passes)',
        'gutmann': 'Gutmann (35 passes)',
        'random': 'Random Data',
        'zero': 'Zero Fill'
    };
    return methods[method] || method;
}

function closeConfirmModal() {
    document.getElementById('confirmModal').classList.remove('active');
}

// Export for use in HTML
window.selectDevice = selectDevice;
window.startWipe = startWipe;
window.togglePartitions = togglePartitions;
window.generateCertificate = generateCertificate;
window.downloadCertificate = downloadCertificate;
window.showQRCode = showQRCode;
