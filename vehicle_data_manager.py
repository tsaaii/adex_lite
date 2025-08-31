"""
Vehicle Data Manager - Simple JSON storage for empty weights
"""

import json
import os
import logging

class VehicleDataManager:
    """Simple manager for vehicle empty weights with ±30kg validation"""
    
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        self.json_file = os.path.join(data_folder, "vehicle_data.json")
        self.weight_margin = 30  # ±30 kg margin
        self.logger = logging.getLogger('VehicleDataManager')
        
        # Ensure data folder exists
        os.makedirs(data_folder, exist_ok=True)
        
        # Load existing data
        self.load_data()
    
    def load_data(self):
        """Load vehicle data from JSON file"""
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r') as f:
                    data = json.load(f)
                    self.empty_weights = data.get("empty_weights", {})
            else:
                self.empty_weights = {}
                self.save_data()
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            self.empty_weights = {}
    
    def save_data(self):
        """Save vehicle data to JSON file"""
        try:
            data = {"empty_weights": self.empty_weights}
            with open(self.json_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            return False
    
    def get_empty_weight(self, vehicle_no):
        """Get stored empty weight for a vehicle"""
        vehicle_no = vehicle_no.strip().upper()
        return self.empty_weights.get(vehicle_no)
    
    def save_empty_weight(self, vehicle_no, weight):
        """Save or update empty weight for a vehicle"""
        vehicle_no = vehicle_no.strip().upper()
        self.empty_weights[vehicle_no] = float(weight)
        return self.save_data()
    
    def is_within_margin(self, vehicle_no, current_weight):
        """Check if current weight is within ±30kg of stored empty weight"""
        empty_weight = self.get_empty_weight(vehicle_no)
        if empty_weight is None:
            return False, None, None
        
        difference = abs(float(current_weight) - empty_weight)
        is_valid = difference <= self.weight_margin
        return is_valid, empty_weight, difference
    
    def requires_second_weighment(self, vehicle_no):
        """Check if vehicle requires second weighment (no stored empty weight)"""
        return self.get_empty_weight(vehicle_no) is None
    
    def update_from_weighment(self, vehicle_no, first_weight, second_weight):
        """Update empty weight from completed weighment (lighter weight = empty)"""
        empty_weight = min(float(first_weight), float(second_weight))
        return self.save_empty_weight(vehicle_no, empty_weight)