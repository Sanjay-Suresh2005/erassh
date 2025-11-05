"""
ERASH - Erasure and Certification System
Flask backend server
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from wipe_service import WipeService
from certificate import CertificateGenerator
from ledger import LedgerService
import os
import json
from datetime import datetime
import threading

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Initialize services
wipe_service = WipeService()
cert_generator = CertificateGenerator(output_dir=os.path.join(os.path.dirname(__file__), '../data/certificates'))
ledger_service = LedgerService(ledger_path=os.path.join(os.path.dirname(__file__), '../data/ledger.json'))

# Store for SSE connections
log_subscribers = {}

@app.route('/')
def index():
    """Serve the main UI"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get list of available storage devices"""
    device_type = request.args.get('type', None)  # HDD, SSD, USB, Virtual, or None for all
    include_partitions = request.args.get('partitions', 'true').lower() == 'true'
    
    devices = wipe_service.detect_devices(device_type_filter=device_type, include_partitions=include_partitions)
    
    return jsonify({
        'success': True,
        'devices': devices,
        'count': len(devices),
        'total_partitions': sum(d.get('partition_count', 0) for d in devices)
    })

@app.route('/api/wipe/start', methods=['POST'])
def start_wipe():
    """Start a wipe operation"""
    data = request.json
    
    device_path = data.get('device_path')
    method = data.get('method', 'dodshort')
    verification = data.get('verification', False)
    simulated = data.get('simulated', True)  # Default to simulated for safety
    
    if not device_path:
        return jsonify({
            'success': False,
            'error': 'Device path is required'
        }), 400
    
    # Confirmation check
    confirmation = data.get('confirmation', False)
    if not confirmation:
        return jsonify({
            'success': False,
            'error': 'Confirmation required. This operation is IRREVERSIBLE!'
        }), 400
    
    result = wipe_service.start_wipe(
        device_path=device_path,
        method=method,
        verification=verification,
        simulated=simulated
    )
    
    if 'error' in result:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 400
    
    return jsonify({
        'success': True,
        'wipe_id': result['wipe_id'],
        'status': result['status']
    })

@app.route('/api/wipe/status/<wipe_id>', methods=['GET'])
def get_wipe_status(wipe_id):
    """Get status of a wipe operation"""
    status = wipe_service.get_wipe_status(wipe_id)
    
    if not status:
        return jsonify({
            'success': False,
            'error': 'Wipe operation not found'
        }), 404
    
    return jsonify({
        'success': True,
        'status': status
    })

@app.route('/api/wipe/logs/<wipe_id>', methods=['GET'])
def get_wipe_logs(wipe_id):
    """Get logs for a wipe operation (polling endpoint)"""
    since_index = int(request.args.get('since', 0))
    
    logs_data = wipe_service.get_wipe_logs(wipe_id, since_index)
    
    if not logs_data:
        return jsonify({
            'success': False,
            'error': 'Wipe operation not found'
        }), 404
    
    return jsonify({
        'success': True,
        'logs': logs_data['logs'],
        'total_count': logs_data['total_count'],
        'status': logs_data['status'],
        'progress': logs_data['progress']
    })

@app.route('/api/certificate/generate', methods=['POST'])
def generate_certificate():
    """Generate a certificate for a completed wipe"""
    data = request.json
    
    wipe_id = data.get('wipe_id')
    record_on_blockchain = data.get('record_on_blockchain', False)
    
    if not wipe_id:
        return jsonify({
            'success': False,
            'error': 'Wipe ID is required'
        }), 400
    
    # Get wipe report
    wipe_report = wipe_service.get_wipe_report(wipe_id)
    if not wipe_report:
        return jsonify({
            'success': False,
            'error': 'Wipe report not found'
        }), 404
    
    # Get device info
    wipe_status = wipe_service.get_wipe_status(wipe_id)
    device_path = wipe_status['device']
    
    # Find device info
    all_devices = wipe_service.detect_devices()
    device_info = next((d for d in all_devices if d['name'] == device_path), None)
    
    if not device_info:
        # Use fallback info
        device_info = {
            'name': device_path,
            'model': 'Unknown',
            'serial': 'UNKNOWN',
            'size': 'Unknown',
            'type': 'Unknown',
            'transport': 'Unknown'
        }
    
    # Record on blockchain if requested
    ledger_entry = None
    if record_on_blockchain:
        # Generate certificate first to get hash
        temp_cert = cert_generator.generate_certificate(wipe_report, device_info, None)
        
        # Record on ledger
        ledger_entry = ledger_service.record_erasure(temp_cert, wipe_report, device_info)
        
        # Regenerate certificate with ledger info
        certificate_data = cert_generator.generate_certificate(wipe_report, device_info, ledger_entry)
    else:
        # Generate certificate without blockchain
        certificate_data = cert_generator.generate_certificate(wipe_report, device_info, None)
    
    return jsonify({
        'success': True,
        'certificate': {
            'filename': certificate_data['certificate_filename'],
            'id': certificate_data['certificate_id'],
            'hash': certificate_data['certificate_hash'],
            'download_url': f"/api/certificate/download/{certificate_data['certificate_filename']}",
            'verification_url': certificate_data['verification_url'],
            'qr_data': certificate_data['qr_code_data']
        },
        'ledger_entry': ledger_entry
    })

@app.route('/api/certificate/download/<filename>', methods=['GET'])
def download_certificate(filename):
    """Download a certificate PDF"""
    cert_dir = os.path.join(os.path.dirname(__file__), '../data/certificates')
    
    try:
        return send_file(
            os.path.join(cert_dir, filename),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Certificate not found'
        }), 404

@app.route('/api/certificate/bulk', methods=['POST'])
def generate_bulk_certificate():
    """Generate a bulk certificate for multiple wipe operations"""
    data = request.json
    
    wipe_ids = data.get('wipe_ids', [])
    job_id = data.get('job_id', f"BULK_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    if not wipe_ids:
        return jsonify({
            'success': False,
            'error': 'At least one wipe ID is required'
        }), 400
    
    wipe_reports = []
    device_infos = []
    
    for wipe_id in wipe_ids:
        report = wipe_service.get_wipe_report(wipe_id)
        if report:
            wipe_reports.append(report)
            
            # Get device info
            wipe_status = wipe_service.get_wipe_status(wipe_id)
            device_path = wipe_status['device']
            all_devices = wipe_service.detect_devices()
            device_info = next((d for d in all_devices if d['name'] == device_path), {
                'name': device_path,
                'model': 'Unknown',
                'serial': 'UNKNOWN',
                'size': 'Unknown',
                'type': 'Unknown'
            })
            device_infos.append(device_info)
    
    if not wipe_reports:
        return jsonify({
            'success': False,
            'error': 'No valid wipe reports found'
        }), 404
    
    # Generate bulk certificate
    bulk_cert = cert_generator.generate_bulk_certificate(wipe_reports, device_infos, job_id)
    
    return jsonify({
        'success': True,
        'certificate': {
            'filename': bulk_cert['certificate_filename'],
            'job_id': bulk_cert['job_id'],
            'device_count': bulk_cert['device_count'],
            'download_url': f"/api/certificate/download/{bulk_cert['certificate_filename']}"
        }
    })

@app.route('/api/verify/certificate', methods=['POST'])
def verify_certificate():
    """Verify a certificate against the blockchain ledger"""
    data = request.json
    
    certificate_id = data.get('certificate_id')
    serial_number = data.get('serial_number')
    certificate_hash = data.get('certificate_hash')
    
    if not any([certificate_id, serial_number, certificate_hash]):
        return jsonify({
            'success': False,
            'error': 'At least one verification parameter required (certificate_id, serial_number, or certificate_hash)'
        }), 400
    
    verification_result = ledger_service.verify_certificate(
        certificate_id=certificate_id,
        serial_number=serial_number,
        certificate_hash=certificate_hash
    )
    
    return jsonify({
        'success': True,
        'verification': verification_result
    })

@app.route('/api/verify/serial/<serial_number>', methods=['GET'])
def search_by_serial(serial_number):
    """Search for all erasure records for a device serial number"""
    records = ledger_service.search_by_serial(serial_number)
    
    return jsonify({
        'success': True,
        'serial_number': serial_number,
        'records': records,
        'count': len(records)
    })

@app.route('/api/ledger/stats', methods=['GET'])
def get_ledger_stats():
    """Get ledger statistics"""
    stats = ledger_service.get_ledger_stats()
    
    return jsonify({
        'success': True,
        'stats': stats
    })

@app.route('/api/ledger/export', methods=['GET'])
def export_ledger():
    """Export the entire ledger"""
    result = ledger_service.export_ledger()
    
    return jsonify({
        'success': True,
        'exported': result['exported'],
        'path': result['path']
    })

@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    return jsonify({
        'success': True,
        'system': {
            'name': 'ERASH',
            'version': '1.0.0',
            'description': 'Erasure and Certification System with Blockchain Integration',
            'features': [
                'Device type filtering (HDD/SSD/USB/Virtual)',
                'Multiple wipe methods (DoD, Gutmann, Random, Zero)',
                'Real-time log streaming',
                'PDF certificate generation with QR codes',
                'Blockchain/ledger integration',
                'Certificate verification',
                'Bulk operations'
            ],
            'wipe_methods': {
                'dodshort': 'DoD 5220.22-M (3 passes)',
                'dod': 'DoD 5220.22-M (7 passes)',
                'gutmann': 'Gutmann (35 passes)',
                'random': 'Random data (1 pass)',
                'zero': 'Zero fill (1 pass)'
            },
            'ledger_type': ledger_service.ledger_type,
            'safety_warning': 'IRREVERSIBLE ACTION - All data will be permanently destroyed'
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 60)
    print("ERASH - Erasure and Certification System")
    print("=" * 60)
    print("⚠️  WARNING: This system can PERMANENTLY ERASE disk data!")
    print("   Always use simulated mode for demos unless working with")
    print("   disposable drives or virtual disks.")
    print("=" * 60)
    print("\nStarting server on http://localhost:5000")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
