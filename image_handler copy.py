"""
Complete image_handler.py with fixed UI status updates
Replace your entire image_handler.py file with this code
"""

import os
import datetime
import cv2
import config
from tkinter import messagebox
import tkinter as tk

class ImageHandler:
    def __init__(self, main_form):
        self.main_form = main_form



    def save_unwatermarked_image(self, image, weighment, camera_type, site_name, vehicle_no, timestamp):
        """Save unwatermarked image to vehicle-specific folder structure with hourly subfolders"""
        try:
            # Create main images folder (your existing config.IMAGES_FOLDER)
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            
            # Create vehicle-specific folder inside images folder
            vehicle_folder = os.path.join(config.IMAGES_FOLDER, vehicle_no)
            os.makedirs(vehicle_folder, exist_ok=True)
            
            # Determine subfolder based on weighment and camera type
            if weighment == "first" and camera_type == "front":
                subfolder = "ff"
            elif weighment == "first" and camera_type == "back":
                subfolder = "fb"
            elif weighment == "second" and camera_type == "front":
                subfolder = "sf"
            elif weighment == "second" and camera_type == "back":
                subfolder = "sb"
            else:
                print(f"Invalid weighment/camera_type combination: {weighment}/{camera_type}")
                return None
            
            # Create the subfolder (ff, fb, sf, sb) inside vehicle folder
            subfolder_path = os.path.join(vehicle_folder, subfolder)
            os.makedirs(subfolder_path, exist_ok=True)
            
            # Get current hour (0-23) for hour-based subfolder
            current_hour = datetime.datetime.now().strftime("%02d")  # 00, 01, 02, ..., 23
            
            # Create hour subfolder inside the camera type folder
            hour_folder_path = os.path.join(subfolder_path, current_hour)
            os.makedirs(hour_folder_path, exist_ok=True)
            
            # Create filename for unwatermarked image
            unwatermarked_filename = f"{site_name}_{vehicle_no}_{timestamp}_{weighment}_{camera_type}_unwatermarked.jpg"
            
            # Full path for unwatermarked image (now includes vehicle/subfolder/hour)
            unwatermarked_filepath = os.path.join(hour_folder_path, unwatermarked_filename)
            
            # Save unwatermarked image
            success = cv2.imwrite(unwatermarked_filepath, image)
            
            if success and os.path.exists(unwatermarked_filepath):
                print(f"✅ Unwatermarked image saved: {vehicle_no}/{subfolder}/{current_hour}/{unwatermarked_filename}")
                return unwatermarked_filepath
            else:
                print(f"❌ Failed to save unwatermarked image to {vehicle_no}/{subfolder}/{current_hour}/")
                return None
                
        except Exception as e:
            print(f"Error saving unwatermarked image: {e}")
            return None

    def save_front_image(self, captured_image=None):
        """Save front camera image with filename format: {site}_{vehicle}_{timestamp}_{weighment}_front.jpg"""
        print("=== SAVE FRONT IMAGE ===")
        
        # Validate vehicle number first
        if not self.main_form.form_validator.validate_vehicle_number():
            print("Vehicle number validation failed")
            return False
        
        # Determine weighment stage
        image_weighment = self.determine_current_image_weighment()
        weighment_label = "2nd" if image_weighment == "second" else "1st"
        print(f"Image weighment stage: {image_weighment}")
        
        # Get image from camera or use provided image
        image = captured_image
        if image is None:
            if hasattr(self.main_form, 'front_camera') and self.main_form.front_camera:
                image = self.main_form.front_camera.get_current_frame()
                if image is not None:
                    print("✅ Got frame from front camera")
                else:
                    print("❌ No frame available from front camera")
            
        if image is None:
            print("ERROR: No image available. Please ensure camera is active and capture a frame first.")
            return False
        
        print(f"Image shape: {image.shape}")
        
        try:
            # Generate filename with new format
            site_name = self.main_form.site_var.get().replace(" ", "_")
            vehicle_no = self.main_form.vehicle_var.get().replace(" ", "_")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # New naming format: {site}_{vehicle}_{timestamp}_{weighment}_front.jpg
            filename = f"{site_name}_{vehicle_no}_{timestamp}_{weighment_label}_front.jpg"
            print(f"Generated filename: {filename}")
            
            # Ensure images folder exists
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            
            # Save file path
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            print(f"Saving to: {filepath}")
            
            # Save the original image WITHOUT watermark
            success = cv2.imwrite(filepath, image)
            print(f"cv2.imwrite returned: {success}")
            
            if not success:
                print("ERROR: cv2.imwrite failed")
                messagebox.showerror("Error", "Failed to save image file")
                return False
            
            # Verify file was created
            if not os.path.exists(filepath):
                print("ERROR: File was not created")
                messagebox.showerror("Error", "Image file was not created")
                return False
            
            print(f"File size: {os.path.getsize(filepath)} bytes")
            
            # Update the appropriate image path based on weighment stage
            if image_weighment == "first":
                self.main_form.first_front_image_path = filepath
            else:
                self.main_form.second_front_image_path = filepath
            
            # FIXED: Update status display immediately
            print("🔄 Updating UI status...")
            self.update_image_status()
            
            # FIXED: Force UI refresh
            self._force_ui_update()
            
            print(f"✅ Front image saved successfully: {filename}")
            return True
            
        except Exception as e:
            error_msg = f"Error saving front image: {str(e)}"
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", error_msg)
            return False

    def save_back_image(self, captured_image=None):
        """Save back camera image with filename format: {site}_{vehicle}_{timestamp}_{weighment}_back.jpg"""
        print("=== SAVE BACK IMAGE ===")
        
        # Validate vehicle number first
        if not self.main_form.form_validator.validate_vehicle_number():
            print("Vehicle number validation failed")
            return False
        
        # Determine weighment stage
        image_weighment = self.determine_current_image_weighment()
        weighment_label = "2nd" if image_weighment == "second" else "1st"
        print(f"Image weighment stage: {image_weighment}")
        
        # Get image from camera or use provided image
        image = captured_image
        if image is None:
            if hasattr(self.main_form, 'back_camera') and self.main_form.back_camera:
                image = self.main_form.back_camera.get_current_frame()
                if image is not None:
                    print("✅ Got frame from back camera")
                else:
                    print("❌ No frame available from back camera")
            
        if image is None:
            print("ERROR: No image available. Please ensure camera is active and capture a frame first.")
            return False
        
        print(f"Image shape: {image.shape}")
        
        try:
            # Generate filename
            site_name = self.main_form.site_var.get().replace(" ", "_")
            vehicle_no = self.main_form.vehicle_var.get().replace(" ", "_")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            filename = f"{site_name}_{vehicle_no}_{timestamp}_{weighment_label}_back.jpg"
            print(f"Generated filename: {filename}")
            
            # Ensure images folder exists
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            
            # Save file path
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            print(f"Saving to: {filepath}")
            
            # Save the original image WITHOUT watermark
            success = cv2.imwrite(filepath, image)
            print(f"cv2.imwrite returned: {success}")
            
            if not success:
                print("ERROR: cv2.imwrite failed")
                messagebox.showerror("Error", "Failed to save image file")
                return False
            
            # Verify file was created
            if not os.path.exists(filepath):
                print("ERROR: File was not created")
                messagebox.showerror("Error", "Image file was not created")
                return False
            
            print(f"File size: {os.path.getsize(filepath)} bytes")
            
            # Update the appropriate image path based on weighment stage
            if image_weighment == "first":
                self.main_form.first_back_image_path = filepath
            else:
                self.main_form.second_back_image_path = filepath
            
            # FIXED: Update status display immediately
            print("🔄 Updating UI status...")
            self.update_image_status()
            
            # FIXED: Force UI refresh
            self._force_ui_update()
            
            print(f"✅ Back image saved successfully: {filename}")
            return True
            
        except Exception as e:
            error_msg = f"Error saving back image: {str(e)}"
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", error_msg)
            return False

    def update_image_status(self):
        """Update image status indicators with enhanced feedback and UI refresh"""
        try:
            # Count first weighment images
            first_count = 0
            if hasattr(self.main_form, 'first_front_image_path') and self.main_form.first_front_image_path and os.path.exists(self.main_form.first_front_image_path):
                first_count += 1
            if hasattr(self.main_form, 'first_back_image_path') and self.main_form.first_back_image_path and os.path.exists(self.main_form.first_back_image_path):
                first_count += 1
                
            # Count second weighment images
            second_count = 0
            if hasattr(self.main_form, 'second_front_image_path') and self.main_form.second_front_image_path and os.path.exists(self.main_form.second_front_image_path):
                second_count += 1
            if hasattr(self.main_form, 'second_back_image_path') and self.main_form.second_back_image_path and os.path.exists(self.main_form.second_back_image_path):
                second_count += 1
                
            total_count = first_count + second_count
            
            print(f"Image status - First: {first_count}/2, Second: {second_count}/2, Total: {total_count}/4")
            
            # FIXED: Force UI update by calling the main form's update method
            if hasattr(self.main_form, 'update_image_status_display'):
                self.main_form.update_image_status_display()
            
            # FIXED: Also update any camera UI status displays
            if hasattr(self.main_form, 'parent') and hasattr(self.main_form.parent, 'update_image_status_display'):
                self.main_form.parent.update_image_status_display()
                
        except Exception as e:
            print(f"Error updating image status: {e}")

    def _force_ui_update(self):
        """Force immediate UI update to show tick marks"""
        try:
            # Get tkinter root and force update
            tk_root = self._get_tkinter_root()
            if tk_root:
                # Update all pending UI changes immediately
                tk_root.update_idletasks()
                tk_root.update()
                
                # Schedule another update after a brief delay to ensure it sticks
                tk_root.after(50, lambda: self._refresh_all_status_displays())
                tk_root.after(200, lambda: self._refresh_all_status_displays())
            
        except Exception as e:
            print(f"Error forcing UI update: {e}")

    def _get_tkinter_root(self):
        """Get the tkinter root widget for scheduling updates"""
        try:
            widget = self.main_form.parent
            while widget and hasattr(widget, 'master'):
                if widget.master is None:
                    return widget
                widget = widget.master
            return widget
        except:
            return None

    def _refresh_all_status_displays(self):
        """Force refresh of all status displays"""
        try:
            # Update the main form status displays
            if hasattr(self.main_form, 'update_image_status_display'):
                self.main_form.update_image_status_display()
            
            # Update individual status variables with proper tick marks
            self._update_status_variables()
            
        except Exception as e:
            print(f"Error refreshing status displays: {e}")

    def _update_status_variables(self):
        """Update individual status variables with tick marks"""
        try:
            # Check which images exist
            first_front = bool(hasattr(self.main_form, 'first_front_image_path') and 
                             self.main_form.first_front_image_path and 
                             os.path.exists(self.main_form.first_front_image_path))
            first_back = bool(hasattr(self.main_form, 'first_back_image_path') and 
                            self.main_form.first_back_image_path and 
                            os.path.exists(self.main_form.first_back_image_path))
            second_front = bool(hasattr(self.main_form, 'second_front_image_path') and 
                              self.main_form.second_front_image_path and 
                              os.path.exists(self.main_form.second_front_image_path))
            second_back = bool(hasattr(self.main_form, 'second_back_image_path') and 
                             self.main_form.second_back_image_path and 
                             os.path.exists(self.main_form.second_back_image_path))
            
            # Update first weighment status
            first_status = f"Front: {'✅' if first_front else '❌'} Back: {'✅' if first_back else '❌'}"
            if hasattr(self.main_form, 'first_image_status_var'):
                self.main_form.first_image_status_var.set(first_status)
                if hasattr(self.main_form, 'first_image_status'):
                    color = "green" if (first_front and first_back) else "orange" if (first_front or first_back) else "red"
                    self.main_form.first_image_status.config(foreground=color)
            
            # Update second weighment status
            second_status = f"Front: {'✅' if second_front else '❌'} Back: {'✅' if second_back else '❌'}"
            if hasattr(self.main_form, 'second_image_status_var'):
                self.main_form.second_image_status_var.set(second_status)
                if hasattr(self.main_form, 'second_image_status'):
                    color = "green" if (second_front and second_back) else "orange" if (second_front or second_back) else "red"
                    self.main_form.second_image_status.config(foreground=color)
            
            # Update total count
            total_count = sum([first_front, first_back, second_front, second_back])
            total_status = f"{total_count}/4 images captured"
            if hasattr(self.main_form, 'total_image_status_var'):
                self.main_form.total_image_status_var.set(total_status)
            
            print(f"✅ Status variables updated: {total_status}")
            
        except Exception as e:
            print(f"Error updating status variables: {e}")

    def save_first_front_image(self, captured_image):
        """Save image specifically for first weighment front - used by continuous camera system"""
        print("=== SAVE FIRST FRONT IMAGE (SPECIFIC) ===")
        
        # Validate vehicle number first
        if not self.main_form.form_validator.validate_vehicle_number():
            print("Vehicle number validation failed")
            return False
        
        if captured_image is None:
            print("ERROR: No captured image provided")
            return False
        
        try:
            # Generate filename
            site_name = self.main_form.site_var.get().replace(" ", "_")
            vehicle_no = self.main_form.vehicle_var.get().replace(" ", "_")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{site_name}_{vehicle_no}_{timestamp}_1st_front.jpg"
            
            # Save image WITHOUT watermark
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            
            success = cv2.imwrite(filepath, captured_image)
            if success and os.path.exists(filepath):
                self.main_form.first_front_image_path = filepath
                self.update_image_status()
                self._force_ui_update()
                print(f"✅ First front image saved: {filename}")
                return True
            else:
                print("ERROR: Failed to save first front image")
                return False
                
        except Exception as e:
            print(f"Error saving first front image: {e}")
            return False

    def save_first_back_image(self, captured_image):
        """Save image specifically for first weighment back - used by continuous camera system"""
        print("=== SAVE FIRST BACK IMAGE (SPECIFIC) ===")
        
        # Validate vehicle number first
        if not self.main_form.form_validator.validate_vehicle_number():
            print("Vehicle number validation failed")
            return False
        
        if captured_image is None:
            print("ERROR: No captured image provided")
            return False
        
        try:
            # Generate filename
            site_name = self.main_form.site_var.get().replace(" ", "_")
            vehicle_no = self.main_form.vehicle_var.get().replace(" ", "_")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{site_name}_{vehicle_no}_{timestamp}_1st_back.jpg"
            
            # Save image WITHOUT watermark
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            
            success = cv2.imwrite(filepath, captured_image)
            if success and os.path.exists(filepath):
                self.main_form.first_back_image_path = filepath
                self.update_image_status()
                self._force_ui_update()
                print(f"✅ First back image saved: {filename}")
                return True
            else:
                print("ERROR: Failed to save first back image")
                return False
                
        except Exception as e:
            print(f"Error saving first back image: {e}")
            return False
    
    def save_second_front_image(self, captured_image):
        """Save image specifically for second weighment front - used by continuous camera system"""
        print("=== SAVE SECOND FRONT IMAGE (SPECIFIC) ===")
        
        # Validate vehicle number first
        if not self.main_form.form_validator.validate_vehicle_number():
            print("Vehicle number validation failed")
            return False
        
        if captured_image is None:
            print("ERROR: No captured image provided")
            return False
        
        try:
            # Generate filename
            site_name = self.main_form.site_var.get().replace(" ", "_")
            vehicle_no = self.main_form.vehicle_var.get().replace(" ", "_")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{site_name}_{vehicle_no}_{timestamp}_2nd_front.jpg"
            
            # Save image WITHOUT watermark
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            
            success = cv2.imwrite(filepath, captured_image)
            if success and os.path.exists(filepath):
                self.main_form.second_front_image_path = filepath
                self.update_image_status()
                self._force_ui_update()
                print(f"✅ Second front image saved: {filename}")
                return True
            else:
                print("ERROR: Failed to save second front image")
                return False
                
        except Exception as e:
            print(f"Error saving second front image: {e}")
            return False
    
    def save_second_back_image(self, captured_image):
        """Save image specifically for second weighment back - used by continuous camera system"""
        print("=== SAVE SECOND BACK IMAGE (SPECIFIC) ===")
        
        # Validate vehicle number first
        if not self.main_form.form_validator.validate_vehicle_number():
            print("Vehicle number validation failed")
            return False
        
        if captured_image is None:
            print("ERROR: No captured image provided")
            return False
        
        try:
            # Generate filename
            site_name = self.main_form.site_var.get().replace(" ", "_")
            vehicle_no = self.main_form.vehicle_var.get().replace(" ", "_")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{site_name}_{vehicle_no}_{timestamp}_2nd_back.jpg"
            
            # Save image WITHOUT watermark
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            
            success = cv2.imwrite(filepath, captured_image)
            if success and os.path.exists(filepath):
                self.main_form.second_back_image_path = filepath
                self.update_image_status()
                self._force_ui_update()
                print(f"✅ Second back image saved: {filename}")
                return True
            else:
                print("ERROR: Failed to save second back image")
                return False
                
        except Exception as e:
            print(f"Error saving second back image: {e}")
            return False

    def load_images_from_record(self, record):
        """Load image paths from a record into the form"""
        print(f"Loading images from record for ticket: {record.get('ticket_no', 'unknown')}")
        
        # First weighment images
        first_front_image = record.get('first_front_image', '')
        first_back_image = record.get('first_back_image', '')
        
        # Second weighment images  
        second_front_image = record.get('second_front_image', '')
        second_back_image = record.get('second_back_image', '')
        
        # Store all image paths
        self.main_form.first_front_image_path = os.path.join(config.IMAGES_FOLDER, first_front_image) if first_front_image else None
        self.main_form.first_back_image_path = os.path.join(config.IMAGES_FOLDER, first_back_image) if first_back_image else None
        self.main_form.second_front_image_path = os.path.join(config.IMAGES_FOLDER, second_front_image) if second_front_image else None
        self.main_form.second_back_image_path = os.path.join(config.IMAGES_FOLDER, second_back_image) if second_back_image else None
        
        print(f"Loaded image paths:")
        print(f"  First front: {self.main_form.first_front_image_path}")
        print(f"  First back: {self.main_form.first_back_image_path}")
        print(f"  Second front: {self.main_form.second_front_image_path}")
        print(f"  Second back: {self.main_form.second_back_image_path}")
        
        # Update status
        self.update_image_status()
        self._force_ui_update()

    def reset_images(self):
        """Reset image paths and status"""
        print("Resetting all image paths")
        self.main_form.first_front_image_path = None
        self.main_form.first_back_image_path = None
        self.main_form.second_front_image_path = None
        self.main_form.second_back_image_path = None
        
        # Update status display
        self.update_image_status()
        self._force_ui_update()

    def get_all_image_filenames(self):
        """Get all image filenames for database storage
        
        Returns:
            dict: Dictionary with all 4 image filenames
        """
        result = {
            'first_front_image': os.path.basename(self.main_form.first_front_image_path) if self.main_form.first_front_image_path else "",
            'first_back_image': os.path.basename(self.main_form.first_back_image_path) if self.main_form.first_back_image_path else "",
            'second_front_image': os.path.basename(self.main_form.second_front_image_path) if self.main_form.second_front_image_path else "",
            'second_back_image': os.path.basename(self.main_form.second_back_image_path) if self.main_form.second_back_image_path else ""
        }
        print(f"Get all image filenames: {result}")
        return result