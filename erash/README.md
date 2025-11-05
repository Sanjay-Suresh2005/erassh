# 🔒 ERASH - Erasure & Certification System

**Secure Disk Erasure with Blockchain Certification**

A comprehensive system for securely erasing storage devices and generating immutable certificates with blockchain verification. Perfect for data centers, IT asset disposal, and compliance demonstrations.

---

## ⚠️ CRITICAL SAFETY WARNING

**IRREVERSIBLE ACTION - READ CAREFULLY:**

- Disk wiping **permanently destroys ALL data** on the target device
- There is **NO recovery** after erasure begins
- For demonstrations, **ALWAYS use simulated mode** or disposable drives
- **NEVER** run real erasure on production systems without explicit confirmation
- Recommended for demos: Virtual disks (VirtualBox, VMware) or spare USB drives

---

## 🎯 Demo Goals

This system demonstrates:

1. **Device Management**: Friendly UI listing drives with type filtering (HDD/SSD/USB/Virtual)
2. **Partition Detection**: Scan and display all partitions with mount status and filesystem info
3. **Granular Control**: Erase entire disks OR individual partitions
4. **Live Erasure**: Real or simulated wiping using nwipe with streaming logs
5. **Certificate Generation**: Automated PDF certificates with QR codes
6. **Blockchain Integration**: Immutable ledger recording (local JSON or Hyperledger Fabric)
7. **Public Verification**: Search by serial number and compare certificate hashes
8. **Bulk Operations**: Group multiple devices for batch processing
9. **QR Verification**: QR-coded certificates linking to verification portal

---

## 🏗️ Architecture

```
erash/
├── backend/
│   ├── app.py              # Flask REST API server
│   ├── wipe_service.py     # nwipe integration & device detection
│   ├── certificate.py      # PDF generation with ReportLab
│   ├── ledger.py          # Blockchain/ledger logic
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html         # Main UI
│   ├── style.css          # Styling
│   └── app.js             # Client-side logic
├── data/
│   ├── ledger.json        # Local immutable ledger
│   └── certificates/      # Generated PDF certificates
└── README.md
```

---

## 🔧 Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended) - required for nwipe
- **Python**: 3.8 or higher
- **nwipe**: Secure disk wipe utility
- **Browser**: Modern web browser (Chrome, Firefox, Edge)

### Platform Compatibility

| Platform | Device Detection | Simulated Mode | Real Erasure | USB Support | Recommended For |
|----------|-----------------|----------------|--------------|-------------|-----------------|
| **Linux** | ✅ Full | ✅ Yes | ✅ Yes | ✅ Yes | Production & Demos |
| **WSL2** | ⚠️ Limited | ✅ Yes | ⚠️ Limited | ⚠️ Limited | Development & Demos |
| **VirtualBox VM** | ✅ Full | ✅ Yes | ✅ Yes | ✅ Yes (with USB passthrough) | Full Testing |
| **Windows Native** | ❌ No | ❌ No | ❌ No | ❌ No | Not Supported |
| **macOS** | ❌ No | ❌ No | ❌ No | ❌ No | Not Supported |

### For Windows Users

This system requires Linux for the nwipe utility. **Best Options:**

1. **WSL2** (Recommended for Demos)
   - Install: `wsl --install` in PowerShell (Admin)
   - Perfect for simulated mode demonstrations
   - USB device access is limited
   - Great for development and stage demos

2. **VirtualBox VM** (Recommended for Real Erasure)
   - Full Ubuntu installation
   - Enable USB passthrough in VM settings
   - Can erase real USB drives
   - Best for testing actual erasure

3. **Dual Boot** Linux installation
   - Full hardware access
   - Everything works perfectly
   - Requires disk partitioning

4. **Cloud VM** (AWS, Azure, Google Cloud)
   - Good for development
   - No physical device access

---

## 📦 Installation

### Step 1: Install System Dependencies

```bash
# Update package list
sudo apt update

# Install nwipe (secure disk wipe utility)
sudo apt install -y nwipe

# Install Python 3 and pip (if not already installed)
sudo apt install -y python3 python3-pip python3-venv

# Note: lsblk is usually pre-installed on Linux systems
# Verify with: lsblk --version
```

### Step 2: Set Up Python Environment

```bash
# Navigate to the project directory
cd erash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
cd backend
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
# Check nwipe installation
sudo nwipe --version

# Check Python packages
pip list | grep -E "Flask|reportlab|qrcode"

# Test device detection
lsblk -J
```

---

## 🚀 Running the Application

### Start the Backend Server

```bash
# Activate virtual environment (if not already active)
cd erash
source venv/bin/activate

# Start Flask server
cd backend
python3 app.py
```

The server will start on `http://localhost:5000`

You should see:
```
============================================================
ERASH - Erasure and Certification System
============================================================
⚠️  WARNING: This system can PERMANENTLY ERASE disk data!
   Always use simulated mode for demos unless working with
   disposable drives or virtual disks.
============================================================

Starting server on http://localhost:5000
```

### Access the Web UI

Open your web browser and navigate to:
```
http://localhost:5000
```

---

## 🎮 Usage Guide

### 1. Scan & Detect Devices

- **Click "🔍 Scan All Devices"**: Primary button to detect all storage devices
- **Device Type Filter**: Choose HDD, SSD, USB, Virtual, or All Devices to filter results
- **Refresh**: Click "🔄 Refresh" button to re-scan devices
- **Automatic Detection**: System detects and displays:
  - Device name (e.g., `/dev/sda`, `/dev/sdc`)
  - Model and serial number
  - Total size and transport type
  - All partitions with details
  - Mount status for each partition
  - Filesystem type (ext4, NTFS, FAT32, etc.)

### 1.1 Understanding Device Information

Each detected device shows:
```
┌─────────────────────────────────┐
│ [USB]                      32G  │  ← Device type badge and size
│ /dev/sdc                        │  ← Device path
│ Model: SanDisk Ultra USB        │  ← Hardware info
│ Serial: SD3210987654321         │  ← Unique identifier
│ Transport: usb                  │
│ ▼ 1 Partition(s)                │  ← Expandable partition list
│   ┌─────────────────────────┐   │
│   │ /dev/sdc1               │   │  ← Partition path
│   │ Size: 32G | FS: exfat   │   │  ← Partition details
│   │ ⚠️ 📍 Mounted at: /media/│   │  ← Mount warning
│   │         username/USB    │   │
│   │ [🗑️ Erase Partition]    │   │  ← Erase this partition only
│   └─────────────────────────┘   │
│ [🗑️ Erase Entire Disk]          │  ← Erase all partitions
└─────────────────────────────────┘
```

### 1.2 Partition Management

- **Expand Partitions**: Click "▼ X Partition(s)" to view all partitions
- **View Details**: Each partition shows:
  - Size and filesystem type
  - Label/name (if available)
  - Mount status (⚠️ warning if mounted)
  - Mount point location
- **Choose Target**: 
  - Click "🗑️ Erase Partition" for single partition
  - Click "🗑️ Erase Entire Disk" for all partitions
- **Safety Warnings**: Mounted partitions show warning indicators

### 2. Configure Operation

**Wipe Method:**
- `DoD 5220.22-M (3 passes)` - Fast, government standard
- `DoD 5220.22-M (7 passes)` - Thorough, government standard
- `Gutmann (35 passes)` - Maximum security, very slow
- `Random Data (1 pass)` - Quick overwrite
- `Zero Fill (1 pass)` - Fastest option

**Operation Mode:**
- `Simulated (Demo Mode)` - ✅ SAFE for demos, no actual erasure
- `Real Erasure` - ⚠️ DANGEROUS, permanently destroys data

**Certification Mode:**
- `Certificate Only` - Generate PDF certificate
- `Record on Blockchain` - Also add immutable ledger entry

### 3. Start Erasure

1. Select a device
2. Click "🗑️ Erase" button
3. Review confirmation dialog carefully
4. Check the confirmation checkbox
5. Click "Start Erasure"

### 4. Monitor Progress

- **Active Operations**: Shows real-time progress
- **Operation Logs**: Streams live logs from nwipe
- **Progress Bar**: Visual indication of completion percentage

### 5. Certificate Generation

- After completion, certificate generates automatically
- Or click "📄 Generate Certificate" manually
- Download PDF with "⬇️ Download PDF" button
- QR code embedded in certificate for verification

### 6. Verification

**By Serial Number:**
1. Enter device serial in verification field
2. Click "🔍 Verify by Serial"
3. View all erasure records for that device

**By Certificate Hash:**
- Use `/api/verify/certificate` endpoint
- Compare SHA-256 hash against ledger

---

## 🎪 Demo Workflow

### Recommended Demo Script

**1. Introduction (2 min)**
```
"ERASH is a secure disk erasure system with blockchain certification.
It combines DoD-standard wiping methods with immutable proof of erasure."
```

**2. Show Device Detection (3 min)**
- Click "🔍 Scan All Devices" button with animation
- System detects all storage devices
- Show device type filters (HDD, SSD, USB, Virtual)
- Expand a device to show partition details
- Highlight mount status warnings
- Point out filesystem information
- Explain disk vs. partition erasure options

**3. Configure & Start Simulated Wipe (3 min)**
- Select "Simulated (Demo Mode)" - emphasize safety
- Choose a wipe method (e.g., DoD 3-pass)
- Select a virtual or test device
- Show confirmation dialog with safety warnings
- Start the erasure

**4. Real-Time Monitoring (2 min)**
- Point out live log streaming
- Show progress bar updating
- Explain multi-pass process

**5. Certificate Generation (2 min)**
- Certificate auto-generates on completion
- Download and open PDF
- Show embedded QR code
- Explain certificate contents:
  - Device information
  - Erasure details
  - SHA-256 hash
  - Verification URL

**6. Blockchain Verification (3 min)**
- Show ledger statistics
- Demonstrate serial number search
- Explain immutability
- Compare certificate hash to ledger entry

**7. Advanced Features (2 min)**
- Bulk operations capability
- Multiple concurrent wipes
- Export ledger functionality
- Optional Hyperledger Fabric integration

---

## 🔬 Testing with Virtual Disks & USB Drives

### Option 1: Virtual Disk (Safest)

Create a virtual disk for testing:

```bash
# Create a 1GB virtual disk file
dd if=/dev/zero of=test_disk.img bs=1M count=1024

# Setup loop device
sudo losetup -fP test_disk.img

# Check loop device name
losetup -a

# Now it appears as /dev/loop0 (or similar) in ERASH
```

**Cleanup After Testing:**
```bash
# Detach loop device
sudo losetup -d /dev/loop0

# Remove disk image
rm test_disk.img
```

### Option 2: USB Pendrive (For Demo)

**For Simulated Mode (Safe):**
1. Plug in any USB drive
2. Click "🔍 Scan All Devices"
3. USB appears in device list with partitions
4. Keep "Simulated (Demo Mode)" selected
5. Click "🗑️ Erase" (data stays safe!)
6. Show full workflow without risk

**For Real Erasure (DANGEROUS):**
1. ⚠️ Use a **disposable/blank USB drive ONLY**
2. Backup any important data first
3. Unmount the drive: `sudo umount /dev/sdX1`
4. Switch to "Real Erasure (DANGEROUS!)" mode
5. Carefully read all warnings
6. This **WILL permanently destroy all data**

**Detection Example:**
```bash
# Plug in USB drive
# In terminal, verify detection:
lsblk

# Output shows:
# sdc      8:32   1  29.9G  0 disk 
# └─sdc1   8:33   1  29.9G  0 part /media/username/USB

# Unmount before real erasure (good practice):
sudo umount /dev/sdc1

# Now scan in ERASH - it will appear with partition details
```

---

## 📡 API Reference

### Devices

**GET** `/api/devices?type={HDD|SSD|USB|Virtual}&partitions={true|false}`
- Get list of available devices with optional partition information
- **Parameters:**
  - `type`: Filter by device type (HDD, SSD, USB, Virtual) or omit for all
  - `partitions`: Include partition details (default: true)
- **Returns:**
  - Device list with model, serial, size, type, transport
  - Partition details: name, size, filesystem, mount point, label
  - Total device count and partition count

### Wipe Operations

**POST** `/api/wipe/start`
```json
{
  "device_path": "/dev/sda",
  "method": "dodshort",
  "verification": false,
  "simulated": true,
  "confirmation": true
}
```

**GET** `/api/wipe/status/{wipe_id}`
- Get current status of wipe operation

**GET** `/api/wipe/logs/{wipe_id}?since={index}`
- Get logs since specific index (for polling)

### Certificates

**POST** `/api/certificate/generate`
```json
{
  "wipe_id": "wipe_1234567890",
  "record_on_blockchain": true
}
```

**GET** `/api/certificate/download/{filename}`
- Download certificate PDF

**POST** `/api/certificate/bulk`
```json
{
  "wipe_ids": ["wipe_1", "wipe_2"],
  "job_id": "BULK_20251105"
}
```

### Verification

**POST** `/api/verify/certificate`
```json
{
  "certificate_id": "ABC123",
  "serial_number": "S3Z9NB0M123456",
  "certificate_hash": "sha256_hash"
}
```

**GET** `/api/verify/serial/{serial_number}`
- Search all records for a device serial

### Ledger

**GET** `/api/ledger/stats`
- Get ledger statistics

**GET** `/api/ledger/export`
- Export ledger for backup

### System

**GET** `/api/system/info`
- Get system information

**GET** `/api/health`
- Health check endpoint

---

## 🔐 Security Considerations

### Wipe Methods Explained

| Method | Passes | Speed | Security Level | Use Case |
|--------|--------|-------|----------------|----------|
| Zero Fill | 1 | ⚡ Fastest | Low | Quick disposal, non-sensitive |
| Random Data | 1 | ⚡ Fast | Medium | General purpose |
| DoD 3-pass | 3 | ⚡ Fast | High | Standard compliance |
| DoD 7-pass | 7 | 🔄 Medium | Very High | Sensitive data |
| Gutmann | 35 | 🐌 Slow | Maximum | Top secret data |

### Blockchain Integrity

The local ledger uses:
- **SHA-256 hashing** for block integrity
- **Chained hashes** to prevent tampering
- **Immutable append-only** structure
- **Genesis block** as foundation

Each block contains:
```json
{
  "block_index": 1,
  "timestamp": "2025-11-05T12:00:00",
  "transaction_id": "TXN-ABC123",
  "data": { "certificate details" },
  "previous_hash": "hash_of_previous_block",
  "block_hash": "calculated_hash_of_this_block"
}
```

### Certificate Verification Process

1. User scans QR code or enters serial number
2. System retrieves certificate hash from ledger
3. Compares expected hash with provided certificate
4. Verifies blockchain integrity from genesis block
5. Returns verification status: VALID / INVALID / NOT_FOUND

---

## 🎓 Hyperledger Fabric Integration (Optional)

For production blockchain integration, ERASH supports Hyperledger Fabric.

### Prerequisites

- Docker & Docker Compose
- Hyperledger Fabric binaries
- Hyperledger Fabric SDK for Python

### Setup Instructions

```bash
# Install Hyperledger Fabric
curl -sSL https://bit.ly/2ysbOFE | bash -s

# Start test network
cd fabric-samples/test-network
./network.sh up createChannel -c erasure-channel

# Deploy chaincode (see docs/hyperledger-setup.md)
```

### Configuration

Update `backend/ledger.py`:
```python
ledger_service = LedgerService(
    ledger_type='hyperledger',
    network_config='connection-profile.json'
)
```

---

## 🐛 Troubleshooting

### Issue: "Command not found: nwipe"

**Solution:**
```bash
sudo apt update
sudo apt install nwipe
```

### Issue: "Permission denied" when accessing devices

**Solution:**
```bash
# Run Flask with sudo (for device access)
sudo python3 app.py

# Or add user to disk group
sudo usermod -aG disk $USER
# Logout and login again
```

### Issue: "No devices detected"

**Solutions:**
1. Run `lsblk` to verify devices exist
2. Use simulated mode for demo
3. Check device permissions
4. Ensure devices aren't mounted

### Issue: "Module not found" errors

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Issue: Certificate generation fails

**Solution:**
```bash
# Install additional dependencies
sudo apt install python3-dev
pip install --upgrade reportlab Pillow
```

### Issue: Frontend not loading

**Solutions:**
1. Check Flask is running: `http://localhost:5000/api/health`
2. Check browser console for errors
3. Verify CORS is enabled
4. Clear browser cache

---

## 📊 Monitoring & Logs

### View Active Operations

Access `/api/wipe/status/{wipe_id}` for detailed status

### Export Ledger

```bash
curl http://localhost:5000/api/ledger/export > ledger_backup.json
```

### Application Logs

Flask logs appear in terminal where `app.py` is running

---

## 🚢 Deployment

### Production Deployment

**Not recommended for production without:**
1. HTTPS/TLS encryption
2. Authentication & authorization
3. Rate limiting
4. Input validation hardening
5. Audit logging
6. Backup systems
7. Hardware security modules (HSM) for key storage

### Docker Deployment (Future)

```dockerfile
# Dockerfile example
FROM ubuntu:22.04
RUN apt update && apt install -y nwipe python3 python3-pip
COPY . /app
WORKDIR /app
RUN pip3 install -r backend/requirements.txt
CMD ["python3", "backend/app.py"]
```

---

## 🤝 Contributing

This is a demonstration project. For production use:
- Add comprehensive error handling
- Implement user authentication
- Add database for persistent storage
- Enhance security measures
- Add comprehensive logging
- Implement rate limiting
- Add automated testing

---

## 📄 License

This project is for educational and demonstration purposes.

**Use at your own risk. The authors are not responsible for data loss or system damage.**

---

## 🆘 Support & Contact

For questions or issues:
1. Check troubleshooting section above
2. Review API documentation
3. Check Flask/nwipe documentation
4. Review system logs

---

## 🎬 Quick Start Summary

### For WSL2 (Windows Users - Development/Demos)

```bash
# 1. Install WSL2 (PowerShell as Admin)
wsl --install

# 2. Open Ubuntu terminal and navigate to project
cd /mnt/c/Users/sures/OneDrive/Desktop/erash

# 3. Install dependencies
sudo apt update
sudo apt install nwipe python3 python3-pip python3-venv

# 4. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 5. Start server
cd backend
python3 app.py

# 6. Open browser → http://localhost:5000

# 7. Click "🔍 Scan All Devices"

# 8. Demo safely with "Simulated Mode"!
```

### For Native Linux

```bash
# 1. Install dependencies
sudo apt install nwipe python3 python3-pip python3-venv

# 2. Setup environment
cd erash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 3. Start server
cd backend
python3 app.py

# 4. Open browser → http://localhost:5000

# 5. Click "🔍 Scan All Devices" to detect devices

# 6. For real erasure:
#    - Unmount target: sudo umount /dev/sdX1
#    - Switch to "Real Erasure" mode
#    - ⚠️ This WILL destroy data!
```

### For Stage Demo (Recommended)

```bash
# Use Simulated Mode - completely safe!
1. Boot system (WSL2 or Linux)
2. Start ERASH: python3 backend/app.py
3. Open browser: http://localhost:5000
4. Click "🔍 Scan All Devices"
5. Show device detection with partitions
6. Select device/partition
7. Keep "Simulated (Demo Mode)" selected
8. Click "🗑️ Erase"
9. Watch progress and logs
10. Generate certificate with QR
11. Verify on blockchain
12. Your data is completely safe!
```

---

## ⭐ Key Features Summary

✅ **Comprehensive Device Scanning** - One-click detection of all storage devices  
✅ **Partition-Level Control** - View and erase individual partitions or entire disks  
✅ **Device Type Filtering** - Filter by HDD/SSD/USB/Virtual  
✅ **Mount Status Detection** - Warns if partitions are currently mounted  
✅ **Multiple Wipe Methods** - DoD 3-pass, DoD 7-pass, Gutmann, Random, Zero  
✅ **Real-time Log Streaming** - Watch erasure progress live  
✅ **Automated PDF Certificates** - Professional reports with QR codes  
✅ **QR Code Verification** - Quick verification via smartphone  
✅ **Immutable Blockchain Ledger** - Tamper-proof audit trail  
✅ **Serial Number Search** - Find all erasure records for a device  
✅ **Bulk Operations** - Group multiple devices for batch processing  
✅ **Chain Integrity Validation** - Verify blockchain from genesis block  
✅ **Export/Backup** - Ledger export functionality  
✅ **USB Drive Support** - Detect and erase external USB storage  
✅ **Simulated Mode** - Safe demos without data loss  
✅ **Granular Selection** - Choose entire disk or specific partitions  

---

**Remember: Safety first! Always use simulated mode for demos unless you have explicit disposable hardware.**

🔒 **ERASH - Where Secure Erasure Meets Blockchain Verification** 🔒
