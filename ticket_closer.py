"""
Ticket Closer - Handles quick close with empty weight
"""

import datetime
import random
import logging

class TicketCloser:
    """Handles ticket closing with automatic weight and image selection"""
    
    def __init__(self, vehicle_data_manager, image_selector):
        self.vehicle_mgr = vehicle_data_manager
        self.image_selector = image_selector
        self.logger = logging.getLogger('TicketCloser')
    
    def can_quick_close(self, vehicle_no):
        """Check if vehicle can be quick closed"""
        empty_weight = self.vehicle_mgr.get_empty_weight(vehicle_no)
        return empty_weight is not None, empty_weight
    
    def generate_closing_time(self, first_timestamp):
        """Generate random closing time 7-12 minutes after first weighment"""
        if isinstance(first_timestamp, str):
            dt = datetime.datetime.strptime(first_timestamp, "%d-%m-%Y %H:%M:%S")
        else:
            dt = first_timestamp
        
        # Random time between 7 and 12 minutes
        random_minutes = random.uniform(7, 12)
        closing_time = dt + datetime.timedelta(minutes=random_minutes)
        
        self.logger.info(f"Generated closing time: {random_minutes:.1f} minutes after first weighment")
        return closing_time.strftime("%d-%m-%Y %H:%M:%S")
    
    def quick_close(self, vehicle_no, first_weight, first_timestamp):
        """Quick close ticket using stored empty weight
        
        Args:
            vehicle_no: Vehicle number
            first_weight: First weighment value
            first_timestamp: First weighment timestamp
        
        Returns:
            dict: Closed ticket data with second weight, time, and images
        """
        # Get stored empty weight
        empty_weight = self.vehicle_mgr.get_empty_weight(vehicle_no)
        
        if empty_weight is None:
            self.logger.error(f"Cannot quick close - no empty weight for {vehicle_no}")
            return None
        
        # Generate closing time
        closing_time = self.generate_closing_time(first_timestamp)
        
        # Calculate net weight
        net_weight = abs(float(first_weight) - empty_weight)
        
        # Auto-select second weighment images
        images = self.image_selector.get_second_weighment_images(vehicle_no, first_timestamp)
        
        result = {
            'second_weight': empty_weight,
            'second_timestamp': closing_time,
            'net_weight': net_weight,
            'second_front_image': images['second_front'],
            'second_back_image': images['second_back']
        }
        
        self.logger.info(f"Quick closed ticket for {vehicle_no}: Net={net_weight:.2f}kg")
        return result
    
    def manual_close(self, vehicle_no, first_weight, second_weight, first_timestamp):
        """Close ticket with manual weight entry
        
        Args:
            vehicle_no: Vehicle number  
            first_weight: First weighment value
            second_weight: Manual second weight
            first_timestamp: First weighment timestamp
        
        Returns:
            dict: Closed ticket data
        """
        first_weight = float(first_weight)
        second_weight = float(second_weight)
        
        # Generate closing time
        closing_time = self.generate_closing_time(first_timestamp)
        
        # Calculate net weight
        net_weight = abs(first_weight - second_weight)
        
        # Update empty weight if second is lighter
        if second_weight < first_weight:
            self.vehicle_mgr.save_empty_weight(vehicle_no, second_weight)
            self.logger.info(f"Updated empty weight for {vehicle_no}: {second_weight}kg")
        
        # Auto-select second weighment images
        images = self.image_selector.get_second_weighment_images(vehicle_no, first_timestamp)
        
        result = {
            'second_weight': second_weight,
            'second_timestamp': closing_time,
            'net_weight': net_weight,
            'second_front_image': images['second_front'],
            'second_back_image': images['second_back']
        }
        
        self.logger.info(f"Manual closed ticket for {vehicle_no}: Net={net_weight:.2f}kg")
        return result