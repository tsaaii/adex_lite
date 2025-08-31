import tkinter as tk
from tkinter import messagebox
import os
import datetime
import cv2
import config
# from camera import add_watermark  # COMMENTED OUT - watermarking moved to PDF generation

class ImageHandler:
    """Enhanced image handler with watermarking removed from click-to-save functionality"""
    
    def __init__(self, main_form):
        """Initialize image handler
        
        Args:
            main_form: Reference to the main form instance
        """
        self.main_form = main_form
        print("ImageHandler initialized")
    
    def determine_current_image_weighment(self):
        """Determine which weighment images should be saved for based on actual weighment completion"""
        try:
            # Check what weighments are actually completed
            first_weight = self.main_form.first_weight_var.get().strip()
            first_timestamp = self.main_form.first_timestamp_var.get().strip()
            second_weight = self.main_form.second_weight_var.get().strip()
            second_timestamp = self.main_form.second_timestamp_var.get().strip()
            
            first_complete = bool(first_weight and first_timestamp)
            second_complete = bool(second_weight and second_timestamp)
            
            print(f"Weighment status - First: {first_complete}, Second: {second_complete}")
            
            # Decision logic for image weighment
            if not first_complete and not second_complete:
                # No weighments yet - images go to first
                image_weighment = "first"
                print("No weighments completed - images for FIRST weighment")
            elif first_complete and not second_complete:
                # First weighment done, second not done - images still go to first (until second weight is captured)
                image_weighment = "first"
                print("First weighment completed, second not done - images for FIRST weighment")
            elif first_complete and second_complete:
                # Both weighments done - images go to second
                image_weighment = "second"  
                print("Both weighments completed - images for SECOND weighment")
            elif not first_complete and second_complete:
                # Edge case: only second weighment (unusual) - images go to second
                image_weighment = "second"
                print("Only second weighment completed - images for SECOND weighment")
            else:
                # Default fallback
                image_weighment = "first"
                print("Default fallback - images for FIRST weighment")
            
            return image_weighment
            
        except Exception as e:
            print(f"Error determining image weighment: {e}")
            return "first"  # Safe fallback
    
    def check_vehicle_for_image_save(self):
        """Check vehicle status for image save - corrected logic"""
        try:
            print("CHECKING: Verifying vehicle status for image save")
            
            # Must have vehicle number first
            vehicle_no = self.main_form.vehicle_var.get().strip()
            if not vehicle_no:
                messagebox.showerror("Missing Vehicle Number", 
                                "Please enter a vehicle number before saving images.")
                return False
            
            # Determine which weighment this image is for
            image_weighment = self.determine_current_image_weighment()
            
            # Get the current form weighment state
            current_weighment = getattr(self.main_form, 'current_weighment', 'first')
            
            print(f"Image weighment: {image_weighment}, Current form state: {current_weighment}")
            
            # Only check pending for NEW first weighments
            if current_weighment == "first" and image_weighment == "first":
                print("This is a NEW FIRST weighment image - checking pending status")
                if hasattr(self.main_form, 'form_validator'):
                    is_allowed = self.main_form.form_validator.validate_vehicle_not_in_pending_for_new_weighment("image")
                    if not is_allowed:
                        print("❌ IMAGE SAVE BLOCKED - Vehicle is pending for NEW first weighment")
                        return False
                    print("✅ Image save allowed - vehicle not pending for new first weighment")
                    return True
                else:
                    print("❌ No form validator - blocking for safety")
                    messagebox.showerror("System Error", "Cannot validate vehicle status.")
                    return False
            else:
                # For second weighments or continuing first weighments - allow
                print("✅ Not a new first weighment - allowing image save")
                return True
            
        except Exception as e:
            print(f"Error checking vehicle status: {e}")
            return False
    
    def update_image_status(self):
        """Update image status indicators with enhanced feedback"""
        try:
            # Count first weighment images
            first_count = 0
            if self.main_form.first_front_image_path and os.path.exists(self.main_form.first_front_image_path):
                first_count += 1
            if self.main_form.first_back_image_path and os.path.exists(self.main_form.first_back_image_path):
                first_count += 1
            
            # Count second weighment images
            second_count = 0
            if hasattr(self.main_form, 'second_front_image_path') and self.main_form.second_front_image_path and os.path.exists(self.main_form.second_front_image_path):
                second_count += 1
            if hasattr(self.main_form, 'second_back_image_path') and self.main_form.second_back_image_path and os.path.exists(self.main_form.second_back_image_path):
                second_count += 1
            
            total_count = first_count + second_count
            print(f"Image status: First={first_count}/2, Second={second_count}/2, Total={total_count}/4")
            
            # Update UI indicators if they exist
            if hasattr(self.main_form, 'update_image_status_display'):
                self.main_form.update_image_status_display()
                
        except Exception as e:
            print(f"Error updating image status: {e}")
    
    def _force_ui_update(self):
        """Force UI update to reflect changes immediately"""
        try:
            if hasattr(self.main_form, 'parent') and self.main_form.parent:
                self.main_form.parent.update_idletasks()
                self.main_form.parent.update()
        except Exception as e:
            print(f"Error forcing UI update: {e}")

    def save_to_vehicle_folder(self, image, vehicle_no, folder_type):
        """Save image to vehicle-specific folder structure with hour-based subfolders"""
        try:
            # Create vehicle folder in images directory
            vehicle_folder = os.path.join(config.IMAGES_FOLDER, vehicle_no)
            os.makedirs(vehicle_folder, exist_ok=True)
            print("Created vehicle folder: " + vehicle_folder)
            
            # Create subfolder (sf or sb)
            subfolder_path = os.path.join(vehicle_folder, folder_type)
            os.makedirs(subfolder_path, exist_ok=True)
            print("Created subfolder: " + subfolder_path)
            
            # Create hour folder (00-23) - avoiding strftime
            now = datetime.datetime.now()
            current_hour = str(now.hour).zfill(2)  # Convert to 2-digit string
            hour_folder_path = os.path.join(subfolder_path, current_hour)
            os.makedirs(hour_folder_path, exist_ok=True)
            print("Created hour folder: " + hour_folder_path)
            
            # Simple filename - avoiding all strftime
            year = str(now.year)
            month = str(now.month).zfill(2)
            day = str(now.day).zfill(2)
            hour = str(now.hour).zfill(2)
            minute = str(now.minute).zfill(2)
            second = str(now.second).zfill(2)
            
            date_str = year + month + day
            time_str = hour + minute + second
            counter = str(now.microsecond)[:3]
            
            filename = vehicle_no + "_" + date_str + "_" + time_str + counter + ".jpg"
            print("Generated filename: " + filename)
            
            # Save image
            filepath = os.path.join(hour_folder_path, filename)
            print("Saving to path: " + filepath)
            success = cv2.imwrite(filepath, image)
            
            if success:
                print("SUCCESS: Image saved to " + vehicle_no + "/" + folder_type + "/" + current_hour + "/" + filename)
                return filepath
            else:
                print("FAILED: Could not save image to vehicle folder structure")
                return None
                
        except Exception as e:
            print("ERROR in save_to_vehicle_folder: " + str(e))
            import traceback
            traceback.print_exc()
            return None

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
            unwatermarked_filename = site_name + "_" + vehicle_no + "_" + timestamp + "_" + weighment + "_" + camera_type + "_unwatermarked.jpg"
            
            # Full path for unwatermarked image (now includes vehicle/subfolder/hour)
            unwatermarked_filepath = os.path.join(hour_folder_path, unwatermarked_filename)
            
            # Save unwatermarked image
            success = cv2.imwrite(unwatermarked_filepath, image)
            
            if success and os.path.exists(unwatermarked_filepath):
                print(f"✅ Unwatermarked image saved: {vehicle_no}/{subfolder}/{current_hour}/{unwatermarked_filename}")
                return unwatermarked_filepath
            else:
                print(f"❌ Failed to save unwatermarked image")
                return None
                
        except Exception as e:
            print(f"Error saving unwatermarked image: {e}")
            return None
    
    def save_front_image(self, captured_image=None):
        """MODIFIED: Save front view camera image - NO WATERMARKING"""
        print("=== SAVE FRONT IMAGE (NO WATERMARK) ===")
        print(f"Captured image provided: {captured_image is not None}")
        
        # Validate vehicle number first
        if not self.main_form.form_validator.validate_vehicle_number():
            print("Vehicle number validation failed")
            return False
        
        # Check vehicle status with proper logic
        if not self.check_vehicle_for_image_save():
            print("❌ FRONT IMAGE SAVE BLOCKED - Vehicle check failed")
            return False

        print("✅ Vehicle check passed - proceeding with front image save")
        
        # Determine weighment stage
        image_weighment = self.determine_current_image_weighment()
        weighment_label = "1st" if image_weighment == "first" else "2nd"
        print(f"Saving {weighment_label} weighment front image")
        
        # Use captured image if provided, otherwise try to get from camera
        image = captured_image
        if image is None:
            print("No captured image provided, trying to get from front camera")
            if hasattr(self.main_form, 'front_camera') and hasattr(self.main_form.front_camera, 'current_frame'):
                image = self.main_form.front_camera.current_frame
                print(f"Got image from front camera current_frame: {image is not None}")
            else:
                print("No front camera or current_frame available")
        
        if image is None:
            print("ERROR: No image available to save")
            messagebox.showerror("Error", "No image available to save. Please ensure camera is active and capture a frame first.")
            return False
        
        print(f"Image shape: {image.shape}")
        
        try:
            # Generate filename with new format
            site_name = self.main_form.site_var.get().replace(" ", "_")
            vehicle_no = self.main_form.vehicle_var.get().replace(" ", "_")
            ticket_id = self.main_form.rst_var.get().strip()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save unwatermarked image to structured folder first
            unwatermarked_path = self.save_unwatermarked_image(
                image, image_weighment, "front", site_name, vehicle_no, timestamp
            )
            if unwatermarked_path:
                print(f"✅ Unwatermarked front image saved: {unwatermarked_path}")
            
            # === MAIN IMAGE SAVE (NO WATERMARK) ===
            # New naming format: {site}_{vehicle}_{timestamp}_{weighment}_front.jpg
            filename = f"{site_name}_{vehicle_no}_{timestamp}_{weighment_label}_front.jpg"
            print(f"Generated filename: {filename}")
            
            # COMMENTED OUT: Watermarking functionality (moved to PDF generation)
            # watermark_text = f"{site_name} - {vehicle_no} - {timestamp} - {weighment_label.upper()} FRONT"
            # watermarked_image = add_watermark(image, watermark_text, ticket_id)
            
            # Ensure images folder exists
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            
            # Save file path
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            print(f"Saving to: {filepath}")
            
            # Save the original image directly (NO watermark)
            success = cv2.imwrite(filepath, image)  # Direct save, no watermark
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
                if hasattr(self.main_form, 'weight_manager'):
                    if hasattr(self.main_form.weight_manager, 'check_and_offer_quick_close_if_ready'):
                        self.main_form.weight_manager.check_and_offer_quick_close_if_ready()
            else:
                self.main_form.second_front_image_path = filepath
                # ALSO save to vehicle folder structure for second weighment (sf folder)
                self.save_to_vehicle_folder(image, vehicle_no, "sf")
            
            # Update status display immediately
            print("🔄 Updating UI status...")
            self.update_image_status()
            
            # Force UI refresh
            self._force_ui_update()
            
            print(f"✅ Front image saved successfully (no watermark): {filename}")
            return True
            
        except Exception as e:
            error_msg = f"Error saving front image: {str(e)}"
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", error_msg)
            return False

    def save_back_image(self, captured_image=None):
        """MODIFIED: Save back view camera image - NO WATERMARKING"""
        print("=== SAVE BACK IMAGE (NO WATERMARK) ===")
        print(f"Captured image provided: {captured_image is not None}")
        
        # Validate vehicle number first
        if not self.main_form.form_validator.validate_vehicle_number():
            print("Vehicle number validation failed")
            return False
        
        # Check vehicle status with proper logic
        if not self.check_vehicle_for_image_save():
            print("❌ BACK IMAGE SAVE BLOCKED - Vehicle check failed")
            return False

        print("✅ Vehicle check passed - proceeding with back image save")
        
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
            messagebox.showerror("Error", "No image available. Please ensure camera is active and capture a frame first.")
            return False
        
        print(f"Image shape: {image.shape}")
        
        try:
            # Generate filename
            site_name = self.main_form.site_var.get().replace(" ", "_")
            vehicle_no = self.main_form.vehicle_var.get().replace(" ", "_")
            ticket_id = self.main_form.rst_var.get().strip()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save unwatermarked image to structured folder first
            unwatermarked_path = self.save_unwatermarked_image(
                image, image_weighment, "back", site_name, vehicle_no, timestamp
            )
            if unwatermarked_path:
                print(f"✅ Unwatermarked back image saved: {unwatermarked_path}")
            
            # === MAIN IMAGE SAVE (NO WATERMARK) ===
            filename = f"{site_name}_{vehicle_no}_{timestamp}_{weighment_label}_back.jpg"
            print(f"Generated filename: {filename}")
            
            # COMMENTED OUT: Watermarking functionality (moved to PDF generation)
            # watermark_text = f"{site_name} - {vehicle_no} - {timestamp} - {weighment_label.upper()} BACK"
            # watermarked_image = add_watermark(image, watermark_text, ticket_id)
            
            # Ensure images folder exists
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            
            # Save file path
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            print(f"Saving to: {filepath}")
            
            # Save the original image directly (NO watermark)
            success = cv2.imwrite(filepath, image)  # Direct save, no watermark
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
                if hasattr(self.main_form, 'weight_manager'):
                    if hasattr(self.main_form.weight_manager, 'check_and_offer_quick_close_if_ready'):
                        self.main_form.weight_manager.check_and_offer_quick_close_if_ready()                
            else:
                self.main_form.second_back_image_path = filepath
                # ALSO save to vehicle folder structure for second weighment (sb folder)
                self.save_to_vehicle_folder(image, vehicle_no, "sb")
            
            # Update status display immediately
            print("🔄 Updating UI status...")
            self.update_image_status()
            
            # Force UI refresh
            self._force_ui_update()
            
            print(f"✅ Back image saved successfully (no watermark): {filename}")
            return True
            
        except Exception as e:
            error_msg = f"Error saving back image: {str(e)}"
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", error_msg)
            return False

    def save_first_front_image(self, captured_image):
        """Save image specifically for first weighment front - NO WATERMARKING"""
        print("=== SAVE FIRST FRONT IMAGE (NO WATERMARK) ===")
        
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
            ticket_id = self.main_form.rst_var.get().strip()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save unwatermarked image to structured folder first
            unwatermarked_path = self.save_unwatermarked_image(
                captured_image, "first", "front", site_name, vehicle_no, timestamp
            )
            if unwatermarked_path:
                print(f"✅ Unwatermarked first front image saved: {unwatermarked_path}")
            
            # === MAIN IMAGE SAVE (NO WATERMARK) ===
            filename = f"{site_name}_{vehicle_no}_{timestamp}_1st_front.jpg"
            
            # COMMENTED OUT: Watermarking functionality (moved to PDF generation)
            # watermark_text = f"{site_name} - {vehicle_no} - {timestamp} - 1ST FRONT"
            # watermarked_image = add_watermark(captured_image, watermark_text, ticket_id)
            
            # Save original image directly (NO watermark)
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            
            success = cv2.imwrite(filepath, captured_image)  # Direct save, no watermark
            if success and os.path.exists(filepath):
                self.main_form.first_front_image_path = filepath
                self.update_image_status()
                self._force_ui_update()
                print(f"✅ First front image saved (no watermark): {filename}")
                if hasattr(self.main_form, 'weight_manager'):
                    if hasattr(self.main_form.weight_manager, 'check_and_offer_quick_close_if_ready'):
                        self.main_form.weight_manager.check_and_offer_quick_close_if_ready()
    
                return True
            else:
                print("ERROR: Failed to save first front image")
                return False
                
        except Exception as e:
            print(f"Error saving first front image: {e}")
            return False

    def save_first_back_image(self, captured_image):
        """Save image specifically for first weighment back - NO WATERMARKING"""
        print("=== SAVE FIRST BACK IMAGE (NO WATERMARK) ===")
        
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
            ticket_id = self.main_form.rst_var.get().strip()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save unwatermarked image to structured folder first
            unwatermarked_path = self.save_unwatermarked_image(
                captured_image, "first", "back", site_name, vehicle_no, timestamp
            )
            if unwatermarked_path:
                print(f"✅ Unwatermarked first back image saved: {unwatermarked_path}")
            
            # === MAIN IMAGE SAVE (NO WATERMARK) ===
            filename = f"{site_name}_{vehicle_no}_{timestamp}_1st_back.jpg"
            
            # COMMENTED OUT: Watermarking functionality (moved to PDF generation)
            # watermark_text = f"{site_name} - {vehicle_no} - {timestamp} - 1ST BACK"
            # watermarked_image = add_watermark(captured_image, watermark_text, ticket_id)
            
            # Save original image directly (NO watermark)
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            
            success = cv2.imwrite(filepath, captured_image)  # Direct save, no watermark
            if success and os.path.exists(filepath):
                self.main_form.first_back_image_path = filepath
                self.update_image_status()
                self._force_ui_update()
                print(f"✅ First back image saved (no watermark): {filename}")
                if hasattr(self.main_form, 'weight_manager'):
                    if hasattr(self.main_form.weight_manager, 'check_and_offer_quick_close_if_ready'):
                        self.main_form.weight_manager.check_and_offer_quick_close_if_ready()
                return True
            else:
                print("ERROR: Failed to save first back image")
                return False
                
        except Exception as e:
            print(f"Error saving first back image: {e}")
            return False
    
    def save_second_front_image(self, captured_image):
        """Save image specifically for second weighment front - NO WATERMARKING"""
        print("=== SAVE SECOND FRONT IMAGE (NO WATERMARK) ===")
        
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
            ticket_id = self.main_form.rst_var.get().strip()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save unwatermarked image to structured folder first
            unwatermarked_path = self.save_unwatermarked_image(
                captured_image, "second", "front", site_name, vehicle_no, timestamp
            )
            if unwatermarked_path:
                print(f"✅ Unwatermarked second front image saved: {unwatermarked_path}")
            
            # === MAIN IMAGE SAVE (NO WATERMARK) ===
            filename = f"{site_name}_{vehicle_no}_{timestamp}_2nd_front.jpg"
            
            # COMMENTED OUT: Watermarking functionality (moved to PDF generation)
            # watermark_text = f"{site_name} - {vehicle_no} - {timestamp} - 2ND FRONT"
            # watermarked_image = add_watermark(captured_image, watermark_text, ticket_id)
            
            # Save original image directly (NO watermark)
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            
            success = cv2.imwrite(filepath, captured_image)  # Direct save, no watermark
            if success and os.path.exists(filepath):
                self.main_form.second_front_image_path = filepath
                self.update_image_status()
                self._force_ui_update()
                print(f"✅ Second front image saved (no watermark): {filename}")
                
                # ALSO save to vehicle folder structure (sf folder)
                self.save_to_vehicle_folder(captured_image, vehicle_no, "sf")
                
                return True
            else:
                print("ERROR: Failed to save second front image")
                return False
                
        except Exception as e:
            print(f"Error saving second front image: {e}")
            return False
    
    def save_second_back_image(self, captured_image):
        """Save image specifically for second weighment back - NO WATERMARKING"""
        print("=== SAVE SECOND BACK IMAGE (NO WATERMARK) ===")
        
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
            ticket_id = self.main_form.rst_var.get().strip()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save unwatermarked image to structured folder first
            unwatermarked_path = self.save_unwatermarked_image(
                captured_image, "second", "back", site_name, vehicle_no, timestamp
            )
            if unwatermarked_path:
                print(f"✅ Unwatermarked second back image saved: {unwatermarked_path}")
            
            # === MAIN IMAGE SAVE (NO WATERMARK) ===
            filename = f"{site_name}_{vehicle_no}_{timestamp}_2nd_back.jpg"
            
            # COMMENTED OUT: Watermarking functionality (moved to PDF generation)
            # watermark_text = f"{site_name} - {vehicle_no} - {timestamp} - 2ND BACK"
            # watermarked_image = add_watermark(captured_image, watermark_text, ticket_id)
            
            # Save original image directly (NO watermark)
            os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            
            success = cv2.imwrite(filepath, captured_image)  # Direct save, no watermark
            if success and os.path.exists(filepath):
                self.main_form.second_back_image_path = filepath
                self.update_image_status()
                self._force_ui_update()
                print(f"✅ Second back image saved (no watermark): {filename}")
                
                # ALSO save to vehicle folder structure (sb folder)
                self.save_to_vehicle_folder(captured_image, vehicle_no, "sb")
                
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
    
    def get_current_weighment_images(self):
        """Get images for current weighment state based on actual completion
        
        Returns:
            dict: Front and back image paths for current weighment
        """
        image_weighment = self.determine_current_image_weighment()
        
        if image_weighment == "first":
            return {
                'front_image': self.main_form.first_front_image_path,
                'back_image': self.main_form.first_back_image_path
            }
        else:
            return {
                'front_image': self.main_form.second_front_image_path,
                'back_image': self.main_form.second_back_image_path
            }
    
    def are_current_weighment_images_complete(self):
        """Check if current weighment has both images captured
        
        Returns:
            bool: True if both front and back images are captured for current weighment
        """
        current_images = self.get_current_weighment_images()
        
        front_exists = current_images['front_image'] and os.path.exists(current_images['front_image'])
        back_exists = current_images['back_image'] and os.path.exists(current_images['back_image'])
        
        result = front_exists and back_exists
        print(f"Current weighment images complete: {result} (front: {front_exists}, back: {back_exists})")
        return result
    
    def get_total_image_count(self):
        """Get total count of captured images across both weighments
        
        Returns:
            int: Total number of images captured (0-4)
        """
        count = 0
        
        # First weighment images
        if self.main_form.first_front_image_path and os.path.exists(self.main_form.first_front_image_path):
            count += 1
        if self.main_form.first_back_image_path and os.path.exists(self.main_form.first_back_image_path):
            count += 1
        
        # Second weighment images
        if self.main_form.second_front_image_path and os.path.exists(self.main_form.second_front_image_path):
            count += 1
        if self.main_form.second_back_image_path and os.path.exists(self.main_form.second_back_image_path):
            count += 1
        
        print(f"Total image count: {count}/4")
        return count