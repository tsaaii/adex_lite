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
        """Get images from the current hour folder in sb/sf directories
        
        Looks for any .jpg files in data/images/VEHICLE/sb/HH/ and sf/HH/
        where HH is the current hour (00-23)
        """
        import os
        import glob
        import datetime
        
        vehicle_no = vehicle_no.strip().upper()
        
        # Get current hour or use the hour from first_timestamp if provided
        if first_timestamp:
            try:
                dt = datetime.datetime.strptime(first_timestamp, "%d-%m-%Y %H:%M:%S")
            except:
                dt = datetime.datetime.now()
        else:
            dt = datetime.datetime.now()
        
        # Get the hour folder (00-23)
        hour_folder = dt.strftime("%H")
        
        result = {
            "second_front": None,
            "second_back": None
        }
        
        # Look for images in sb/HH folder (second back)
        sb_path = os.path.join("data", "images", vehicle_no, "sb", hour_folder)
        if os.path.exists(sb_path):
            sb_pattern = os.path.join(sb_path, "*.jpg")
            sb_images = glob.glob(sb_pattern)
            
            if sb_images:
                # Round-robin selection
                counter_key = f"{vehicle_no}_sb_{hour_folder}"
                if counter_key not in self.round_robin_counters:
                    self.round_robin_counters[counter_key] = 0
                
                index = self.round_robin_counters[counter_key] % len(sb_images)
                result["second_back"] = sb_images[index]
                self.round_robin_counters[counter_key] += 1
                
                self.logger.info(f"Selected sb image from hour {hour_folder}: {result['second_back']}")
        else:
            self.logger.info(f"No sb folder for hour {hour_folder}: {sb_path}")
        
        # Look for images in sf/HH folder (second front)
        sf_path = os.path.join("data", "images", vehicle_no, "sf", hour_folder)
        if os.path.exists(sf_path):
            sf_pattern = os.path.join(sf_path, "*.jpg")
            sf_images = glob.glob(sf_pattern)
            
            if sf_images:
                # Round-robin selection
                counter_key = f"{vehicle_no}_sf_{hour_folder}"
                if counter_key not in self.round_robin_counters:
                    self.round_robin_counters[counter_key] = 0
                
                index = self.round_robin_counters[counter_key] % len(sf_images)
                result["second_front"] = sf_images[index]
                self.round_robin_counters[counter_key] += 1
                
                self.logger.info(f"Selected sf image from hour {hour_folder}: {result['second_front']}")
        else:
            self.logger.info(f"No sf folder for hour {hour_folder}: {sf_path}")
        
        if not result["second_back"] and not result["second_front"]:
            self.logger.warning(f"No images found in hour folder {hour_folder} for vehicle {vehicle_no}")
        
        return result