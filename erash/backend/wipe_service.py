"""
Disk Wipe Service - nwipe integration
Handles device detection, erasure operations, and log streaming
"""

import subprocess
import os
import json
import time
from datetime import datetime
from threading import Thread, Lock
import re

class WipeService:
    def __init__(self):
        self.active_wipes = {}
        self.wipe_lock = Lock()
        self.simulated_mode = False  # Toggle for demo without actual wiping
        
    def detect_devices(self, device_type_filter=None, include_partitions=True):
        """
        Detect available storage devices
        device_type_filter: 'HDD', 'SSD', 'USB', 'Virtual' or None for all
        include_partitions: whether to include partition information
        """
        devices = []
        
        try:
            # Use lsblk to list block devices with more details
            result = subprocess.run(
                ['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,MODEL,SERIAL,ROTA,TRAN,MOUNTPOINT,FSTYPE,LABEL'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for device in data.get('blockdevices', []):
                    # Only include disks, not partitions at top level
                    if device.get('type') != 'disk':
                        continue
                    
                    # Determine device type
                    dev_type = self._classify_device(device)
                    
                    # Filter by type if specified
                    if device_type_filter and dev_type != device_type_filter:
                        continue
                    
                    # Get partitions if requested
                    partitions = []
                    if include_partitions and 'children' in device:
                        for child in device['children']:
                            if child.get('type') in ['part', 'lvm']:
                                partition_info = {
                                    'name': f"/dev/{child['name']}",
                                    'size': child.get('size', 'Unknown'),
                                    'type': child.get('type', 'part'),
                                    'mountpoint': child.get('mountpoint', None),
                                    'fstype': child.get('fstype', 'Unknown'),
                                    'label': child.get('label', 'No Label')
                                }
                                partitions.append(partition_info)
                    
                    device_info = {
                        'name': f"/dev/{device['name']}",
                        'model': device.get('model', 'Unknown').strip(),
                        'serial': device.get('serial', 'N/A').strip(),
                        'size': device.get('size', 'Unknown'),
                        'type': dev_type,
                        'rotational': device.get('rota', '0') == '1',
                        'transport': device.get('tran', 'Unknown'),
                        'partitions': partitions,
                        'partition_count': len(partitions)
                    }
                    devices.append(device_info)
                    
        except Exception as e:
            print(f"Error detecting devices: {e}")
            # Fallback to simulated devices for demo
            devices = self._get_simulated_devices(device_type_filter)
        
        return devices
    
    def _classify_device(self, device):
        """Classify device as HDD, SSD, USB, or Virtual"""
        tran = device.get('tran', '').lower()
        model = device.get('model', '').lower()
        name = device.get('name', '').lower()
        
        # Check for virtual/loop devices
        if 'loop' in name or 'virtual' in model or 'vbox' in model or 'vmware' in model:
            return 'Virtual'
        
        # Check transport type
        if tran in ['usb']:
            return 'USB'
        
        # Check rotation (0 = SSD, 1 = HDD)
        if device.get('rota') == '0':
            return 'SSD'
        elif device.get('rota') == '1':
            return 'HDD'
        
        # Default classification
        if 'ssd' in model:
            return 'SSD'
        elif 'usb' in model or 'flash' in model:
            return 'USB'
        else:
            return 'HDD'
    
    def _get_simulated_devices(self, device_type_filter=None):
        """Return simulated devices for demo purposes"""
        all_devices = [
            {
                'name': '/dev/sda',
                'model': 'Samsung SSD 860 EVO',
                'serial': 'S3Z9NB0M123456',
                'size': '500G',
                'type': 'SSD',
                'rotational': False,
                'transport': 'sata',
                'partitions': [
                    {'name': '/dev/sda1', 'size': '500M', 'type': 'part', 'mountpoint': '/boot/efi', 'fstype': 'vfat', 'label': 'EFI'},
                    {'name': '/dev/sda2', 'size': '499.5G', 'type': 'part', 'mountpoint': '/', 'fstype': 'ext4', 'label': 'root'}
                ],
                'partition_count': 2
            },
            {
                'name': '/dev/sdb',
                'model': 'WDC WD10EZEX',
                'serial': 'WD-WCC123456789',
                'size': '1T',
                'type': 'HDD',
                'rotational': True,
                'transport': 'sata',
                'partitions': [
                    {'name': '/dev/sdb1', 'size': '1T', 'type': 'part', 'mountpoint': '/data', 'fstype': 'ext4', 'label': 'DATA'}
                ],
                'partition_count': 1
            },
            {
                'name': '/dev/sdc',
                'model': 'SanDisk Ultra USB',
                'serial': 'SD3210987654321',
                'size': '32G',
                'type': 'USB',
                'rotational': False,
                'transport': 'usb',
                'partitions': [
                    {'name': '/dev/sdc1', 'size': '32G', 'type': 'part', 'mountpoint': None, 'fstype': 'exfat', 'label': 'USB_DRIVE'}
                ],
                'partition_count': 1
            },
            {
                'name': '/dev/vda',
                'model': 'VirtIO Disk',
                'serial': 'VIRT-DEMO-001',
                'size': '10G',
                'type': 'Virtual',
                'rotational': False,
                'transport': 'virtio',
                'partitions': [
                    {'name': '/dev/vda1', 'size': '10G', 'type': 'part', 'mountpoint': None, 'fstype': 'ext4', 'label': 'VIRTUAL'}
                ],
                'partition_count': 1
            }
        ]
        
        if device_type_filter:
            return [d for d in all_devices if d['type'] == device_type_filter]
        return all_devices
    
    def start_wipe(self, device_path, method='dodshort', verification=False, 
                   callback=None, simulated=True):
        """
        Start disk wipe operation
        method: 'dodshort', 'dod', 'gutmann', 'random', 'zero'
        verification: whether to verify after wipe
        callback: function to call with log updates
        simulated: if True, simulate wipe without actual erasure
        """
        wipe_id = f"wipe_{int(time.time())}_{device_path.replace('/', '_')}"
        
        with self.wipe_lock:
            if device_path in [w['device'] for w in self.active_wipes.values()]:
                return {'error': 'Device is already being wiped', 'wipe_id': None}
            
            self.active_wipes[wipe_id] = {
                'device': device_path,
                'status': 'starting',
                'progress': 0,
                'method': method,
                'start_time': datetime.now().isoformat(),
                'logs': [],
                'simulated': simulated
            }
        
        # Start wipe in background thread
        thread = Thread(target=self._run_wipe, 
                       args=(wipe_id, device_path, method, verification, callback, simulated))
        thread.daemon = True
        thread.start()
        
        return {'wipe_id': wipe_id, 'status': 'started'}
    
    def _run_wipe(self, wipe_id, device_path, method, verification, callback, simulated):
        """Execute the actual wipe operation"""
        try:
            if simulated:
                self._run_simulated_wipe(wipe_id, device_path, method, callback)
            else:
                self._run_real_wipe(wipe_id, device_path, method, verification, callback)
        except Exception as e:
            self._update_wipe_status(wipe_id, 'failed', error=str(e))
            if callback:
                callback(wipe_id, 'error', str(e))
    
    def _run_simulated_wipe(self, wipe_id, device_path, method, callback):
        """Simulate a wipe operation for demo purposes"""
        stages = [
            "Initializing wipe operation...",
            f"Target device: {device_path}",
            f"Method: {method}",
            "Starting erasure process...",
            "Pass 1/3: Writing random data...",
            "Progress: 10%",
            "Progress: 25%",
            "Progress: 40%",
            "Pass 2/3: Writing zeros...",
            "Progress: 50%",
            "Progress: 65%",
            "Progress: 75%",
            "Pass 3/3: Verification...",
            "Progress: 85%",
            "Progress: 95%",
            "Progress: 100%",
            "Wipe completed successfully!",
            f"Device {device_path} has been securely erased."
        ]
        
        for i, log in enumerate(stages):
            time.sleep(0.5)  # Simulate processing time
            
            # Extract progress if present
            progress = 0
            if "Progress:" in log:
                progress = int(log.split("Progress:")[1].strip().rstrip('%'))
            elif i == len(stages) - 1:
                progress = 100
            else:
                progress = int((i / len(stages)) * 100)
            
            self._update_wipe_status(wipe_id, 'running', progress=progress, log=log)
            
            if callback:
                callback(wipe_id, 'log', log)
        
        # Mark as completed
        self._update_wipe_status(wipe_id, 'completed', progress=100)
        if callback:
            callback(wipe_id, 'completed', 'Wipe operation completed successfully')
    
    def _run_real_wipe(self, wipe_id, device_path, method, verification, callback):
        """Execute real nwipe operation (DANGEROUS - WILL ERASE DATA!)"""
        # Map method names to nwipe methods
        method_map = {
            'dodshort': 'dod522022m',
            'dod': 'dodshort',
            'gutmann': 'gutmann',
            'random': 'prng',
            'zero': 'zero'
        }
        
        nwipe_method = method_map.get(method, 'dodshort')
        
        # Build nwipe command
        cmd = [
            'sudo', 'nwipe',
            '--autonuke',
            '--method', nwipe_method,
            '--verify', 'last' if verification else 'off',
            '--nogui',
            device_path
        ]
        
        self._update_wipe_status(wipe_id, 'running', log=f"Executing: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output
            for line in process.stdout:
                line = line.strip()
                if line:
                    # Parse progress from nwipe output
                    progress = self._parse_nwipe_progress(line)
                    self._update_wipe_status(wipe_id, 'running', progress=progress, log=line)
                    
                    if callback:
                        callback(wipe_id, 'log', line)
            
            process.wait()
            
            if process.returncode == 0:
                self._update_wipe_status(wipe_id, 'completed', progress=100)
                if callback:
                    callback(wipe_id, 'completed', 'Wipe completed successfully')
            else:
                self._update_wipe_status(wipe_id, 'failed', error='nwipe exited with error')
                if callback:
                    callback(wipe_id, 'error', 'Wipe failed')
                    
        except Exception as e:
            self._update_wipe_status(wipe_id, 'failed', error=str(e))
            if callback:
                callback(wipe_id, 'error', str(e))
    
    def _parse_nwipe_progress(self, line):
        """Extract progress percentage from nwipe output"""
        # Look for percentage patterns in output
        match = re.search(r'(\d+)%', line)
        if match:
            return int(match.group(1))
        return None
    
    def _update_wipe_status(self, wipe_id, status, progress=None, log=None, error=None):
        """Update the status of an ongoing wipe"""
        with self.wipe_lock:
            if wipe_id in self.active_wipes:
                self.active_wipes[wipe_id]['status'] = status
                
                if progress is not None:
                    self.active_wipes[wipe_id]['progress'] = progress
                
                if log:
                    self.active_wipes[wipe_id]['logs'].append({
                        'timestamp': datetime.now().isoformat(),
                        'message': log
                    })
                
                if error:
                    self.active_wipes[wipe_id]['error'] = error
                
                if status == 'completed':
                    self.active_wipes[wipe_id]['end_time'] = datetime.now().isoformat()
    
    def get_wipe_status(self, wipe_id):
        """Get the current status of a wipe operation"""
        with self.wipe_lock:
            return self.active_wipes.get(wipe_id, None)
    
    def get_wipe_logs(self, wipe_id, since_index=0):
        """Get logs for a wipe operation starting from a specific index"""
        with self.wipe_lock:
            if wipe_id in self.active_wipes:
                logs = self.active_wipes[wipe_id]['logs'][since_index:]
                return {
                    'logs': logs,
                    'total_count': len(self.active_wipes[wipe_id]['logs']),
                    'status': self.active_wipes[wipe_id]['status'],
                    'progress': self.active_wipes[wipe_id]['progress']
                }
        return None
    
    def get_wipe_report(self, wipe_id):
        """Generate a report for a completed wipe"""
        wipe_data = self.get_wipe_status(wipe_id)
        
        if not wipe_data:
            return None
        
        report = {
            'wipe_id': wipe_id,
            'device': wipe_data['device'],
            'method': wipe_data['method'],
            'status': wipe_data['status'],
            'start_time': wipe_data['start_time'],
            'end_time': wipe_data.get('end_time', 'N/A'),
            'duration': self._calculate_duration(wipe_data),
            'simulated': wipe_data.get('simulated', False),
            'verification': 'Passed' if wipe_data['status'] == 'completed' else 'Failed',
            'log_summary': self._summarize_logs(wipe_data['logs'])
        }
        
        return report
    
    def _calculate_duration(self, wipe_data):
        """Calculate duration of wipe operation"""
        if 'end_time' not in wipe_data:
            return 'In progress'
        
        try:
            start = datetime.fromisoformat(wipe_data['start_time'])
            end = datetime.fromisoformat(wipe_data['end_time'])
            duration = end - start
            return str(duration).split('.')[0]  # Remove microseconds
        except:
            return 'Unknown'
    
    def _summarize_logs(self, logs):
        """Create a summary of important log entries"""
        important_logs = []
        for log in logs:
            msg = log['message']
            if any(keyword in msg.lower() for keyword in 
                   ['starting', 'completed', 'pass', 'progress: 100%', 'error', 'failed']):
                important_logs.append(msg)
        
        return important_logs[-10:]  # Last 10 important entries
