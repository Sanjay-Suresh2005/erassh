# erassh
Simple drive eraser with ledger
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

make sure the pillow version 11.0.0 is installed 
Open your web browser and navigate to:
```
http://localhost:5000
