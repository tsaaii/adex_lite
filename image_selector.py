"""
Image Selector - Automatic selection for second weighment images
"""

import os
import glob
import datetime
import logging

class ImageSelector:
    """Automatically selects second front and back images from vehicle folders"""
    
    def __init__(self, images_folder="images"):
        self.images_folder = images_folder
        self.logger = logging.getLogger('ImageSelector')
        
        # Round-robin counters for each vehicle
        self.round_robin_counters = {}
    
    def get_vehicle_hour_folder(self, vehicle_no, timestamp=None):
        """Get the hour folder path for a vehicle"""
        vehicle_no = vehicle_no.strip().upper().replace(" ", "_")
        
        if timestamp:
            if isinstance(timestamp, str):
                # Parse string timestamp
                try:
                    dt = datetime.datetime.strptime(timestamp, "%d-%m-%Y %H:%M:%S")
                except:
                    dt = datetime.datetime.now()
            else:
                dt = timestamp
        else:
            dt = datetime.datetime.now()
        
        # Format: images/VEHICLE_NO/YYYYMMDD_HH/
        hour_folder = dt.strftime("%Y%m%d_%H")
        folder_path = os.path.join(self.images_folder, vehicle_no, hour_folder)
        
        return folder_path
    
    def get_images_by_type(self, vehicle_no, image_type, timestamp=None):
        """Get all images of a specific type for a vehicle"""
        folder_path = self.get_vehicle_hour_folder(vehicle_no, timestamp)
        
        if not os.path.exists(folder_path):
            self.logger.info(f"No folder found: {folder_path}")
            return []
        
        # Find images with the specified type suffix
        pattern = os.path.join(folder_path, f"*_{image_type}.jpg")
        images = glob.glob(pattern)
        
        # Sort for consistent ordering
        images.sort()
        
        self.logger.info(f"Found {len(images)} {image_type} images in {folder_path}")
        return images
    
    def select_image_round_robin(self, vehicle_no, image_type, timestamp=None):
        """Select an image using round-robin method"""
        # Get available images
        images = self.get_images_by_type(vehicle_no, image_type, timestamp)
        
        if not images:
            return None
        
        # Create unique counter key
        hour_folder = self.get_vehicle_hour_folder(vehicle_no, timestamp)
        counter_key = f"{vehicle_no}_{image_type}_{hour_folder}"
        
        # Get or initialize counter
        if counter_key not in self.round_robin_counters:
            self.round_robin_counters[counter_key] = 0
        
        # Select image using round-robin
        index = self.round_robin_counters[counter_key] % len(images)
        selected_image = images[index]
        
        # Increment counter for next selection
        self.round_robin_counters[counter_key] += 1
        
        self.logger.info(f"Selected {image_type} image {index+1}/{len(images)}: {os.path.basename(selected_image)}")
        return selected_image
    
    def get_second_weighment_images(self, vehicle_no, first_timestamp=None):
        """Automatically select second front and second back images
        
        Args:
            vehicle_no: Vehicle number
            first_timestamp: Timestamp of first weighment (to find correct hour folder)
        
        Returns:
            dict: Paths to selected sf and sb images
        """
        # Select second front image
        sf_image = self.select_image_round_robin(vehicle_no, "sf", first_timestamp)
        
        # Select second back image
        sb_image = self.select_image_round_robin(vehicle_no, "sb", first_timestamp)
        
        result = {
            "second_front": sf_image,
            "second_back": sb_image
        }
        
        if sf_image or sb_image:
            self.logger.info(f"Auto-selected images for {vehicle_no}: SF={sf_image is not None}, SB={sb_image is not None}")
        else:
            self.logger.warning(f"No second weighment images found for {vehicle_no}")
        
        return result