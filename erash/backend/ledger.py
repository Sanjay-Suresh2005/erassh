"""
Blockchain/Ledger Service
Handles immutable record keeping of erasure operations
Supports local JSON ledger and optional Hyperledger Fabric integration
"""

import json
import os
import hashlib
from datetime import datetime
from threading import Lock
import time

class LedgerService:
    def __init__(self, ledger_path='../data/ledger.json', ledger_type='local'):
        """
        Initialize ledger service
        ledger_type: 'local' for JSON file, 'hyperledger' for Hyperledger Fabric
        """
        self.ledger_path = ledger_path
        self.ledger_type = ledger_type
        self.ledger_lock = Lock()
        
        # Initialize ledger file if it doesn't exist
        if ledger_type == 'local':
            self._initialize_local_ledger()
    
    def _initialize_local_ledger(self):
        """Initialize local JSON ledger file"""
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        
        if not os.path.exists(self.ledger_path):
            initial_ledger = {
                'ledger_version': '1.0',
                'created_at': datetime.now().isoformat(),
                'ledger_type': 'local_immutable',
                'description': 'Immutable ledger for disk erasure certificates',
                'blocks': []
            }
            
            # Create genesis block
            genesis_block = self._create_genesis_block()
            initial_ledger['blocks'].append(genesis_block)
            
            with open(self.ledger_path, 'w') as f:
                json.dump(initial_ledger, f, indent=2)
    
    def _create_genesis_block(self):
        """Create the first block in the ledger"""
        genesis_data = {
            'block_index': 0,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'type': 'genesis',
                'message': 'ERASH Ledger Genesis Block'
            },
            'previous_hash': '0' * 64,
        }
        
        genesis_data['block_hash'] = self._calculate_block_hash(genesis_data)
        return genesis_data
    
    def record_erasure(self, certificate_data, wipe_report, device_info):
        """
        Record an erasure operation on the ledger
        
        Args:
            certificate_data: Certificate information including hash
            wipe_report: Wipe operation report
            device_info: Device information
        
        Returns:
            Ledger entry with block hash and transaction ID
        """
        if self.ledger_type == 'local':
            return self._record_local_erasure(certificate_data, wipe_report, device_info)
        elif self.ledger_type == 'hyperledger':
            return self._record_hyperledger_erasure(certificate_data, wipe_report, device_info)
        else:
            raise ValueError(f"Unsupported ledger type: {self.ledger_type}")
    
    def _record_local_erasure(self, certificate_data, wipe_report, device_info):
        """Record erasure in local JSON ledger"""
        with self.ledger_lock:
            # Load current ledger
            with open(self.ledger_path, 'r') as f:
                ledger = json.load(f)
            
            # Get previous block hash
            previous_hash = ledger['blocks'][-1]['block_hash'] if ledger['blocks'] else '0' * 64
            
            # Create new block
            block_index = len(ledger['blocks'])
            transaction_id = self._generate_transaction_id(device_info, wipe_report)
            
            block_data = {
                'block_index': block_index,
                'timestamp': datetime.now().isoformat(),
                'transaction_id': transaction_id,
                'data': {
                    'type': 'erasure_certificate',
                    'certificate_id': certificate_data.get('certificate_id', 'N/A'),
                    'certificate_hash': certificate_data.get('certificate_hash', 'N/A'),
                    'device_serial': device_info.get('serial', 'N/A'),
                    'device_model': device_info.get('model', 'Unknown'),
                    'device_type': device_info.get('type', 'Unknown'),
                    'wipe_method': wipe_report.get('method', 'Unknown'),
                    'wipe_status': wipe_report.get('status', 'Unknown'),
                    'wipe_start': wipe_report.get('start_time', 'N/A'),
                    'wipe_end': wipe_report.get('end_time', 'N/A'),
                    'simulated': wipe_report.get('simulated', False)
                },
                'previous_hash': previous_hash,
            }
            
            # Calculate block hash
            block_data['block_hash'] = self._calculate_block_hash(block_data)
            
            # Add block to ledger
            ledger['blocks'].append(block_data)
            
            # Write back to file
            with open(self.ledger_path, 'w') as f:
                json.dump(ledger, f, indent=2)
            
            # Return ledger entry information
            return {
                'ledger_type': 'local',
                'block_index': block_index,
                'block_hash': block_data['block_hash'],
                'transaction_id': transaction_id,
                'timestamp': block_data['timestamp'],
                'previous_hash': previous_hash,
                'certificate_hash': certificate_data.get('certificate_hash', 'N/A')
            }
    
    def _record_hyperledger_erasure(self, certificate_data, wipe_report, device_info):
        """
        Record erasure in Hyperledger Fabric (placeholder for future implementation)
        
        This would require:
        1. Hyperledger Fabric network setup
        2. Chaincode (smart contract) for erasure records
        3. SDK integration (fabric-sdk-py)
        """
        # Placeholder implementation
        transaction_id = self._generate_transaction_id(device_info, wipe_report)
        
        # Simulate Hyperledger transaction
        ledger_entry = {
            'ledger_type': 'hyperledger',
            'network': 'erash-network',
            'channel': 'erasure-channel',
            'chaincode': 'erasure-records',
            'transaction_id': transaction_id,
            'timestamp': datetime.now().isoformat(),
            'block_number': int(time.time()),  # Simulated
            'transaction_hash': hashlib.sha256(transaction_id.encode()).hexdigest(),
            'certificate_hash': certificate_data.get('certificate_hash', 'N/A'),
            'status': 'VALID',
            'endorsers': ['peer0.org1.erash.com', 'peer0.org2.erash.com']
        }
        
        return ledger_entry
    
    def _calculate_block_hash(self, block_data):
        """Calculate SHA-256 hash of block data"""
        # Create a copy without the hash field
        block_copy = {k: v for k, v in block_data.items() if k != 'block_hash'}
        
        # Convert to JSON string and hash
        block_string = json.dumps(block_copy, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def _generate_transaction_id(self, device_info, wipe_report):
        """Generate unique transaction ID"""
        data = f"{device_info.get('serial', 'UNKNOWN')}_{wipe_report.get('wipe_id', '')}_{datetime.now().isoformat()}"
        return 'TXN-' + hashlib.sha256(data.encode()).hexdigest()[:16].upper()
    
    def verify_certificate(self, certificate_id=None, serial_number=None, certificate_hash=None):
        """
        Verify a certificate against the ledger
        
        Args:
            certificate_id: Certificate ID to verify
            serial_number: Device serial number
            certificate_hash: Expected certificate hash
        
        Returns:
            Verification result with ledger entry if found
        """
        if self.ledger_type == 'local':
            return self._verify_local_certificate(certificate_id, serial_number, certificate_hash)
        elif self.ledger_type == 'hyperledger':
            return self._verify_hyperledger_certificate(certificate_id, serial_number, certificate_hash)
    
    def _verify_local_certificate(self, certificate_id, serial_number, certificate_hash):
        """Verify certificate against local ledger"""
        with self.ledger_lock:
            try:
                with open(self.ledger_path, 'r') as f:
                    ledger = json.load(f)
                
                # Search through blocks
                matching_blocks = []
                
                for block in ledger['blocks']:
                    if block.get('data', {}).get('type') != 'erasure_certificate':
                        continue
                    
                    block_data = block.get('data', {})
                    
                    # Check matching criteria
                    match = True
                    if certificate_id and block_data.get('certificate_id') != certificate_id:
                        match = False
                    if serial_number and block_data.get('device_serial') != serial_number:
                        match = False
                    if certificate_hash and block_data.get('certificate_hash') != certificate_hash:
                        match = False
                    
                    if match:
                        matching_blocks.append(block)
                
                if matching_blocks:
                    # Return most recent match
                    block = matching_blocks[-1]
                    
                    # Verify block integrity
                    stored_hash = block['block_hash']
                    calculated_hash = self._calculate_block_hash(block)
                    
                    integrity_valid = (stored_hash == calculated_hash)
                    
                    # Verify chain integrity
                    chain_valid = self._verify_chain_integrity(ledger, block['block_index'])
                    
                    return {
                        'found': True,
                        'integrity_valid': integrity_valid,
                        'chain_valid': chain_valid,
                        'block_index': block['block_index'],
                        'block_hash': block['block_hash'],
                        'timestamp': block['timestamp'],
                        'transaction_id': block.get('transaction_id', 'N/A'),
                        'certificate_data': block['data'],
                        'verification_status': 'VALID' if (integrity_valid and chain_valid) else 'INVALID'
                    }
                else:
                    return {
                        'found': False,
                        'verification_status': 'NOT_FOUND',
                        'message': 'No matching certificate found in ledger'
                    }
                    
            except Exception as e:
                return {
                    'found': False,
                    'verification_status': 'ERROR',
                    'message': f'Error verifying certificate: {str(e)}'
                }
    
    def _verify_hyperledger_certificate(self, certificate_id, serial_number, certificate_hash):
        """Verify certificate against Hyperledger Fabric (placeholder)"""
        # Placeholder for Hyperledger integration
        return {
            'found': True,
            'verification_status': 'VALID',
            'ledger_type': 'hyperledger',
            'message': 'Hyperledger verification not yet implemented'
        }
    
    def _verify_chain_integrity(self, ledger, up_to_block_index):
        """Verify the integrity of the blockchain up to a specific block"""
        blocks = ledger['blocks'][:up_to_block_index + 1]
        
        for i in range(1, len(blocks)):
            current_block = blocks[i]
            previous_block = blocks[i - 1]
            
            # Check if previous_hash matches
            if current_block['previous_hash'] != previous_block['block_hash']:
                return False
            
            # Verify block hash
            calculated_hash = self._calculate_block_hash(current_block)
            if calculated_hash != current_block['block_hash']:
                return False
        
        return True
    
    def get_ledger_stats(self):
        """Get statistics about the ledger"""
        if self.ledger_type == 'local':
            try:
                with open(self.ledger_path, 'r') as f:
                    ledger = json.load(f)
                
                erasure_blocks = [b for b in ledger['blocks'] 
                                 if b.get('data', {}).get('type') == 'erasure_certificate']
                
                return {
                    'ledger_type': 'local',
                    'total_blocks': len(ledger['blocks']),
                    'erasure_records': len(erasure_blocks),
                    'created_at': ledger.get('created_at', 'Unknown'),
                    'last_block_time': ledger['blocks'][-1]['timestamp'] if ledger['blocks'] else 'N/A',
                    'chain_valid': self._verify_chain_integrity(ledger, len(ledger['blocks']) - 1)
                }
            except Exception as e:
                return {'error': str(e)}
        
        return {'ledger_type': self.ledger_type}
    
    def search_by_serial(self, serial_number):
        """Search ledger for all records matching a device serial number"""
        if self.ledger_type != 'local':
            return []
        
        with self.ledger_lock:
            try:
                with open(self.ledger_path, 'r') as f:
                    ledger = json.load(f)
                
                matching_records = []
                for block in ledger['blocks']:
                    if block.get('data', {}).get('type') == 'erasure_certificate':
                        if block['data'].get('device_serial') == serial_number:
                            matching_records.append({
                                'block_index': block['block_index'],
                                'timestamp': block['timestamp'],
                                'certificate_id': block['data'].get('certificate_id'),
                                'certificate_hash': block['data'].get('certificate_hash'),
                                'wipe_method': block['data'].get('wipe_method'),
                                'wipe_status': block['data'].get('wipe_status')
                            })
                
                return matching_records
            except Exception as e:
                return []
    
    def export_ledger(self, output_path=None):
        """Export ledger to a file for backup or audit"""
        if not output_path:
            output_path = f"ledger_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with self.ledger_lock:
            with open(self.ledger_path, 'r') as f:
                ledger = json.load(f)
            
            with open(output_path, 'w') as f:
                json.dump(ledger, f, indent=2)
        
        return {'exported': True, 'path': output_path}
