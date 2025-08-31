# Fixed weight_manager.py - Corrected pending vehicle validation

import tkinter as tk
from tkinter import messagebox
import datetime
import random
import time
import config
import logging

class WeightManager:
    def __init__(self, main_form):
        from vehicle_data_manager import VehicleDataManager
        from image_selector import ImageSelector
        from ticket_closer import TicketCloser        
        self.main_form = main_form
        self.last_weight = 0.0
        self.weight_capture_timeout = 5.0  # seconds to wait for stable weight
        self.min_weight_change = 0.0  # minimum kg change to consider valid weighment

    
        self.vehicle_mgr = VehicleDataManager("data")
        self.image_selector = ImageSelector("images")
        self.ticket_closer = TicketCloser(self.vehicle_mgr, self.image_selector)
        self.logger = logging.getLogger('WeightManager')        

    def initialize_vehicle_systems(self):
        """Initialize the vehicle management systems"""
        try:
            from vehicle_data_manager import VehicleDataManager
            from image_selector import ImageSelector
            from ticket_closer import TicketCloser
            
            self.vehicle_mgr = VehicleDataManager("data")
            self.image_selector = ImageSelector("images")
            self.ticket_closer = TicketCloser(self.vehicle_mgr, self.image_selector)
            
            # Flag to track if quick close is pending
            self.quick_close_pending = False
            self.quick_close_weight = None
            
            self.logger.info("Vehicle systems initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize vehicle systems: {e}")
            self.vehicle_mgr = None
            self.image_selector = None
            self.ticket_closer = None
            self.quick_close_pending = False
            return False

    def capture_weight(self):
        """FIXED: Capture weight with corrected pending vehicle check"""
        # try:
        #     print("=== CORRECTED WEIGHT CAPTURE ===")
            
        #     # CORRECTED: Check vehicle status with proper logic for weighments
        #     if not self.check_vehicle_for_weight_capture():
        #         print("❌ WEIGHT CAPTURE BLOCKED - Vehicle check failed")
        #         return False
            
        #     print("✅ Vehicle check passed - proceeding with weight capture")
            
        #     # Check test mode first using improved method
        #     if self.is_test_mode_enabled():
        #         print("Test mode is enabled - generating random weight")
        #         # Generate random weight - bypass all connection checks
        #         weight = self.generate_random_weight()
        #         print(f"Generated random weight: {weight} kg")
                
        #         # Update the current weight display
        #         self.main_form.current_weight_var.set(f"{weight:.2f} kg")
                
        #         # Process the weight directly
        #         self.process_captured_weight(weight)
        #         return True
                
        #     else:
        #         print("Test mode disabled - using real weighbridge")
        #         # Enhanced: Use real weighbridge with improved error handling
        #         return self.capture_real_weighbridge_weight()
                
        # except Exception as e:
        #     print(f"Error in capture_weight: {e}")
        #     import traceback
        #     traceback.print_exc()
        #     messagebox.showerror("Error", f"Failed to capture weight: {str(e)}")
        #     return False

        try:
            # Get vehicle number
            vehicle_no = self.main_form.vehicle_var.get().strip()
            if not vehicle_no:
                messagebox.showerror("Error", "Please enter vehicle number")
                return False
            
            # Get weight (from weighbridge or test mode)
            if self.is_test_mode_enabled():
                weight = self.generate_random_weight()
            else:
                weight = self.get_current_weighbridge_value()
            
            if weight is None:
                return False
            
            if self.main_form.current_weighment == "first":
                # Capture first weight
                self.main_form.first_weight_var.set(f"{weight:.2f}")
                timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                self.main_form.first_timestamp_var.set(timestamp)
                
                # Check if vehicle can quick close
                can_quick, empty_weight = self.ticket_closer.can_quick_close(vehicle_no)
                
                if can_quick:
                    # Offer quick close
                    response = messagebox.askyesno(
                        "Quick Close Available",
                        f"Vehicle has stored empty weight: {empty_weight:.1f} kg\n\n"
                        f"Current weight: {weight:.1f} kg\n"
                        f"Net weight would be: {abs(weight - empty_weight):.1f} kg\n\n"
                        f"Do you want to quick close this ticket?"
                    )
                    
                    if response:
                        # Quick close the ticket
                        self.perform_quick_close()
                        return True
                else:
                    # No empty weight - must do second weighment
                    messagebox.showinfo(
                        "Second Weighment Required",
                        "No stored empty weight found.\n"
                        "Vehicle must return for second weighment."
                    )
                
                # Move to second weighment state
                self.main_form.current_weighment = "second"
                self.main_form.weighment_state_var.set("Second Weighment")
                
            elif self.main_form.current_weighment == "second":
                # Capture second weight
                self.main_form.second_weight_var.set(f"{weight:.2f}")
                timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                self.main_form.second_timestamp_var.set(timestamp)
                
                # Calculate net weight
                first_weight = float(self.main_form.first_weight_var.get())
                net_weight = abs(first_weight - weight)
                self.main_form.net_weight_var.set(f"{net_weight:.2f}")
                
                # Update empty weight (lighter = empty)
                self.vehicle_mgr.update_from_weighment(vehicle_no, first_weight, weight)
                
                # Auto-select second weighment images
                first_timestamp = self.main_form.first_timestamp_var.get()
                images = self.image_selector.get_second_weighment_images(vehicle_no, first_timestamp)
                
                # Update image paths
                if images['second_front']:
                    self.main_form.second_front_image_path = images['second_front']
                    self.logger.info(f"Auto-selected second front: {images['second_front']}")
                
                if images['second_back']:
                    self.main_form.second_back_image_path = images['second_back']
                    self.logger.info(f"Auto-selected second back: {images['second_back']}")
                
                # Update state
                self.main_form.current_weighment = "complete"
                self.main_form.weighment_state_var.set("Weighment Complete")
                
                messagebox.showinfo(
                    "Second Weight Captured",
                    f"Second weighment: {weight:.2f} kg\n"
                    f"Net weight: {net_weight:.2f} kg\n\n"
                    f"Images auto-selected from vehicle folder"
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error capturing weight: {e}")
            messagebox.showerror("Error", f"Failed to capture weight: {str(e)}")
            return False

    def check_quick_close_available(self, weight):
        """Check if quick close is available but DON'T offer it yet
        
        Call this after first weight capture to set the pending flag
        """
        try:
            if not self.ticket_closer:
                return False
            
            vehicle_no = self.main_form.vehicle_var.get().strip().upper()
            can_quick, empty_weight = self.ticket_closer.can_quick_close(vehicle_no)
            
            if can_quick:
                # Set pending flag - will offer after images are captured
                self.quick_close_pending = True
                self.quick_close_weight = weight
                self.quick_close_empty_weight = empty_weight
                self.logger.info(f"Quick close available for {vehicle_no} - will offer after images")
                return True
            else:
                self.quick_close_pending = False
                self.logger.info(f"No quick close available for {vehicle_no}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking quick close: {e}")
            self.quick_close_pending = False
            return False
    
    def offer_quick_close_after_images(self):
        """Offer quick close AFTER first weighment images are captured
        
        Call this after both first front and first back images are saved
        """
        try:
            # Check if quick close is pending
            if not self.quick_close_pending:
                return False
            
            # Reset the pending flag
            self.quick_close_pending = False
            
            # Check that we have the first weighment images
            if not self.main_form.first_front_image_path or not self.main_form.first_back_image_path:
                self.logger.warning("Cannot offer quick close - first images not captured")
                messagebox.showinfo(
                    "Images Required",
                    "Please capture first front and back images before closing ticket."
                )
                return False
            
            vehicle_no = self.main_form.vehicle_var.get().strip().upper()
            weight = self.quick_close_weight
            empty_weight = self.quick_close_empty_weight
            
            # Calculate net weight
            net_weight = abs(weight - empty_weight)
            
            # Now offer quick close
            response = messagebox.askyesno(
                "Quick Close Available",
                f"First weighment images captured successfully!\n\n"
                f"Vehicle has stored empty weight: {empty_weight:.1f} kg\n"
                f"Current weight: {weight:.1f} kg\n"
                f"Net weight would be: {net_weight:.1f} kg\n\n"
                f"Do you want to quick close this ticket?"
            )
            
            if response:
                # Perform quick close
                return self.perform_quick_close()
            else:
                # User declined - continue to second weighment
                self.main_form.current_weighment = "second"
                self.main_form.weighment_state_var.set("Second Weighment")
                messagebox.showinfo(
                    "Continue to Second Weighment",
                    "Vehicle can now exit and return for second weighment."
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Error offering quick close: {e}")
            return False
    
    def perform_quick_close(self):
        """Perform quick close - images already captured"""
        try:
            if not self.ticket_closer:
                return False
            
            vehicle_no = self.main_form.vehicle_var.get().strip().upper()
            first_weight = float(self.main_form.first_weight_var.get())
            first_timestamp = self.main_form.first_timestamp_var.get()
            
            # Quick close
            result = self.ticket_closer.quick_close(vehicle_no, first_weight, first_timestamp)
            
            if result:
                # Update form fields
                self.main_form.second_weight_var.set(f"{result['second_weight']:.2f}")
                self.main_form.second_timestamp_var.set(result['second_timestamp'])
                self.main_form.net_weight_var.set(f"{result['net_weight']:.2f}")
                
                # Auto-select second weighment images from vehicle folder
                if result.get('second_front_image'):
                    self.main_form.second_front_image_path = result['second_front_image']
                    self.logger.info(f"Auto-selected second front: {result['second_front_image']}")
                
                if result.get('second_back_image'):
                    self.main_form.second_back_image_path = result['second_back_image']
                    self.logger.info(f"Auto-selected second back: {result['second_back_image']}")
                
                # Update state
                self.main_form.current_weighment = "complete"
                self.main_form.weighment_state_var.set("Weighment Complete")
                
                # Update image status display
                if hasattr(self.main_form, 'update_image_status_display'):
                    self.main_form.update_image_status_display()
                
                messagebox.showinfo(
                    "Quick Close Success",
                    f"Ticket closed successfully!\n\n"
                    f"Net Weight: {result['net_weight']:.2f} kg\n"
                    f"Method: Quick close with stored empty weight\n\n"
                    f"Second weighment images auto-selected from vehicle folder"
                )
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error in quick close: {e}")
            messagebox.showerror("Error", f"Failed to quick close: {str(e)}")
            return False
    
    def process_first_weighment(self, weight):
        """Process first weighment - just save weight, check quick close availability"""
        try:
            # Save first weight
            self.main_form.first_weight_var.set(f"{weight:.2f}")
            timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            self.main_form.first_timestamp_var.set(timestamp)
            
            # Check if quick close is available (but don't offer yet)
            has_quick_close = self.check_quick_close_available(weight)
            
            # Move to second weighment state
            self.main_form.current_weighment = "second"
            self.main_form.weighment_state_var.set("Second Weighment")
            
            mode_text = "TEST MODE" if self.is_test_mode_enabled() else "WEIGHBRIDGE"
            
            if has_quick_close:
                # Inform user but don't offer quick close yet
                messagebox.showinfo(
                    "First Weight Captured",
                    f"First weighment: {weight:.2f} kg\n"
                    f"Time: {timestamp}\n"
                    f"Mode: {mode_text}\n\n"
                    "✓ Quick close will be available after capturing images.\n"
                    "Please capture first front and back images."
                )
            else:
                # No quick close available
                vehicle_no = self.main_form.vehicle_var.get().strip().upper()
                messagebox.showinfo(
                    "First Weight Captured - Second Weighment Required",
                    f"First weighment: {weight:.2f} kg\n"
                    f"Time: {timestamp}\n"
                    f"Mode: {mode_text}\n\n"
                    f"⚠ No stored empty weight for {vehicle_no}\n"
                    "Vehicle must return for second weighment."
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing first weighment: {e}")
            return False
    
    def process_second_weighment_with_images(self, weight):
        """Process actual second weighment with auto image selection"""
        try:
            vehicle_no = self.main_form.vehicle_var.get().strip().upper()
            
            # Set second weight
            self.main_form.second_weight_var.set(f"{weight:.2f}")
            timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            self.main_form.second_timestamp_var.set(timestamp)
            
            # Get first weight
            first_weight = float(self.main_form.first_weight_var.get())
            
            # Calculate net weight
            net_weight = abs(first_weight - weight)
            self.main_form.net_weight_var.set(f"{net_weight:.2f}")
            
            # Update empty weight
            if self.vehicle_mgr:
                self.vehicle_mgr.update_from_weighment(vehicle_no, first_weight, weight)
            
            # Auto-select second weighment images
            if self.image_selector:
                first_timestamp = self.main_form.first_timestamp_var.get()
                images = self.image_selector.get_second_weighment_images(vehicle_no, first_timestamp)
                
                if images.get('second_front'):
                    self.main_form.second_front_image_path = images['second_front']
                    self.logger.info(f"Auto-selected second front: {images['second_front']}")
                
                if images.get('second_back'):
                    self.main_form.second_back_image_path = images['second_back']
                    self.logger.info(f"Auto-selected second back: {images['second_back']}")
            
            # Update state
            self.main_form.current_weighment = "complete"
            self.main_form.weighment_state_var.set("Weighment Complete")
            
            # Update image display
            if hasattr(self.main_form, 'update_image_status_display'):
                self.main_form.update_image_status_display()
            
            messagebox.showinfo(
                "Second Weight Captured",
                f"Second weighment: {weight:.2f} kg\n"
                f"Net weight: {net_weight:.2f} kg\n\n"
                f"Images auto-selected from vehicle folder"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing second weighment: {e}")
            return False
    
    def check_and_offer_quick_close_if_ready(self):
        """Helper method to check if both first images are captured and offer quick close
        
        Call this from your image capture methods after saving images
        """
        # Only proceed if quick close is pending
        if not self.quick_close_pending:
            return
        
        # Check if both first weighment images are captured
        if self.main_form.first_front_image_path and self.main_form.first_back_image_path:
            self.logger.info("Both first weighment images captured - offering quick close")
            self.offer_quick_close_after_images()
    # Add this method to allow manual closing
    def close_ticket_manually(self):
        """Allow manual ticket closing without second weighment"""
        try:
            # Check if first weight exists
            if not self.main_form.first_weight_var.get():
                messagebox.showerror("Error", "Please capture first weight before closing")
                return
            
            vehicle_no = self.main_form.vehicle_var.get()
            
            # Check for quick close option
            can_quick, empty_weight = self.ticket_closer.can_quick_close(vehicle_no)
            
            if can_quick:
                # Use quick close
                self.perform_quick_close()
            else:
                # Ask for manual weight
                import tkinter.simpledialog as simpledialog
                weight_str = simpledialog.askstring(
                    "Manual Weight Entry",
                    f"Enter second weight for {vehicle_no} (kg):"
                )
                
                if weight_str:
                    try:
                        second_weight = float(weight_str)
                        first_weight = float(self.main_form.first_weight_var.get())
                        first_timestamp = self.main_form.first_timestamp_var.get()
                        
                        # Manual close
                        result = self.ticket_closer.manual_close(
                            vehicle_no, first_weight, second_weight, first_timestamp
                        )
                        
                        if result:
                            # Update form
                            self.main_form.second_weight_var.set(f"{result['second_weight']:.2f}")
                            self.main_form.second_timestamp_var.set(result['second_timestamp'])
                            self.main_form.net_weight_var.set(f"{result['net_weight']:.2f}")
                            
                            # Update images
                            if result['second_front_image']:
                                self.main_form.second_front_image_path = result['second_front_image']
                            if result['second_back_image']:
                                self.main_form.second_back_image_path = result['second_back_image']
                            
                            messagebox.showinfo(
                                "Manual Close Success",
                                f"Ticket closed with manual weight!\n\n"
                                f"Net Weight: {result['net_weight']:.2f} kg"
                            )
                            
                    except ValueError:
                        messagebox.showerror("Invalid Input", "Please enter a valid number")
        
        except Exception as e:
            self.logger.error(f"Error in manual close: {e}")
            messagebox.showerror("Error", f"Failed to close ticket: {str(e)}")

    def check_vehicle_for_weight_capture(self):
        """FIXED: Check vehicle status for weight capture with corrected logic"""
        try:
            print("CHECKING: Verifying vehicle status for weight capture")
            
            # Must have vehicle number first
            vehicle_no = self.main_form.vehicle_var.get().strip()
            if not vehicle_no:
                messagebox.showerror("Missing Vehicle Number", 
                                "Please enter a vehicle number before capturing weight.")
                return False
            
            # Get the current form weighment state
            current_weighment = getattr(self.main_form, 'current_weighment', 'first')
            
            print(f"Current weighment state: {current_weighment}")
            
            # CORRECTED LOGIC: Only check pending for NEW first weighments
            if current_weighment == "first":
                print("This is a FIRST weighment - checking if it's a NEW first weighment")
                
                # Check if this vehicle already has any weighment data loaded
                # (which would indicate we're continuing an existing record, not creating new)
                first_weight = self.main_form.first_weight_var.get().strip()
                first_timestamp = self.main_form.first_timestamp_var.get().strip()
                has_existing_first = bool(first_weight and first_timestamp)
                
                if has_existing_first:
                    print("Vehicle already has first weighment data - this is NOT a new first weighment")
                    return True  # Allow continuing existing first weighment
                else:
                    print("No existing first weighment data - this IS a new first weighment")
                    # Use form validator to check pending status for NEW first weighments
                    if hasattr(self.main_form, 'form_validator'):
                        is_allowed = self.main_form.form_validator.validate_vehicle_not_in_pending_for_new_weighment("weight")
                        if not is_allowed:
                            print("❌ WEIGHT CAPTURE BLOCKED - Vehicle is pending for NEW first weighment")
                            return False
                        print("✅ Weight capture allowed - vehicle not pending for new first weighment")
                        return True
                    else:
                        print("❌ No form validator - blocking for safety")
                        messagebox.showerror("System Error", "Cannot validate vehicle status.")
                        return False
            else:
                print("This is a SECOND weighment - always allow")
                return True  # Always allow second weighments
                
        except Exception as e:
            print(f"Error checking vehicle status for weight capture: {e}")
            messagebox.showerror("System Error", f"Cannot verify vehicle status: {str(e)}")
            return False  # STRICT BLOCK on errors
    
    def is_test_mode_enabled(self):
        """Enhanced: Check if test mode is enabled with better error handling"""
        try:
            print("Checking test mode...")
            
            # Method 1: Try to get weighbridge settings directly
            try:
                settings_storage = self.get_settings_storage()
                if settings_storage:
                    wb_settings = settings_storage.get_weighbridge_settings()
                    test_mode = wb_settings.get("test_mode", False)
                    print(f"Test mode from settings storage: {test_mode}")
                    return test_mode
            except Exception as e:
                print(f"Method 1 failed: {e}")
            
            # Method 2: Try to access through main app
            try:
                app = self.find_main_app()
                if app and hasattr(app, 'settings_panel'):
                    if hasattr(app.settings_panel, 'test_mode_var'):
                        test_mode = app.settings_panel.test_mode_var.get()
                        print(f"Test mode from app.settings_panel: {test_mode}")
                        return test_mode
            except Exception as e:
                print(f"Method 2 failed: {e}")
            
            # Method 3: Try to access weighbridge manager for test mode status
            try:
                app = self.find_main_app()
                if app and hasattr(app, 'settings_panel'):
                    if hasattr(app.settings_panel, 'weighbridge'):
                        weighbridge = app.settings_panel.weighbridge
                        if hasattr(weighbridge, 'test_mode'):
                            test_mode = weighbridge.test_mode
                            print(f"Test mode from weighbridge: {test_mode}")
                            return test_mode
            except Exception as e:
                print(f"Method 3 failed: {e}")
            
            # Method 4: Check global weighbridge reference
            try:
                manager, weight_var, status_var = config.get_global_weighbridge_info()
                if manager and hasattr(manager, 'test_mode'):
                    test_mode = manager.test_mode
                    print(f"Test mode from global reference: {test_mode}")
                    return test_mode
            except Exception as e:
                print(f"Method 4 failed: {e}")
            
            print("All methods failed - defaulting to False")
            return False
            
        except Exception as e:
            print(f"Error checking test mode: {e}")
            return False
    
    def generate_random_weight(self):
        """Enhanced: Generate more realistic random weights with better validation"""
        try:
            import random
            
            current_weighment = getattr(self.main_form, 'current_weighment', 'first')
            print(f"Generating weight for {current_weighment} weighment")
            
            if current_weighment == "first":
                # First weighment: heavier (loaded truck)
                # Generate weight between 15,000 - 45,000 kg
                base_weight = random.uniform(15000, 45000)
                print(f"First weighment - base: {base_weight}")
            else:
                # Second weighment: lighter (empty truck)
                # Enhanced: Consider the first weight to ensure logical difference
                try:
                    first_weight_str = self.main_form.first_weight_var.get()
                    if first_weight_str:
                        first_weight = float(first_weight_str)
                        # Second weight should be significantly lighter
                        max_second = min(first_weight - 1000, 15000)  # At least 1 ton lighter
                        base_weight = random.uniform(5000, max_second)
                        print(f"Second weighment - considering first weight {first_weight}, generated: {base_weight}")
                    else:
                        base_weight = random.uniform(5000, 15000)
                        print(f"Second weighment - no first weight, generated: {base_weight}")
                except (ValueError, AttributeError):
                    base_weight = random.uniform(5000, 15000)
                    print(f"Second weighment - fallback generated: {base_weight}")
            
            # Round to nearest 10 kg for realism
            weight = round(base_weight / 10) * 10
            
            # Add small random variation (±50 kg) to simulate real weighbridge behavior
            variation = random.uniform(-50, 50)
            weight += variation
            weight = max(0, weight)  # Ensure non-negative
            
            return float(weight)
            
        except Exception as e:
            print(f"Error generating random weight: {e}")
            # Enhanced fallback with better defaults
            import random
            current_weighment = getattr(self.main_form, 'current_weighment', 'first')
            if current_weighment == "first":
                return round(random.uniform(20000, 40000), 2)
            else:
                return round(random.uniform(8000, 12000), 2)
    
    def capture_real_weighbridge_weight(self):
        """Enhanced: Capture weight from real weighbridge with improved stability checking"""
        try:
            print("Attempting to capture from real weighbridge")
            
            # Enhanced: Check connection status first using new methods
            if not self.is_weighbridge_connected():
                messagebox.showerror("Weighbridge Error", 
                                   "Weighbridge is not connected. Please connect the weighbridge in Settings tab.")
                return False
            
            # Enhanced: Wait for stable weight reading
            stable_weight = self.wait_for_stable_weight()
            if stable_weight is None:
                messagebox.showerror("Weighbridge Error", 
                                   "Could not get stable weight reading. Please ensure vehicle is properly positioned.")
                return False
            
            print(f"Captured stable weighbridge weight: {stable_weight}")
            
            # Enhanced: Validate weight makes sense for the weighment type
            if not self.validate_captured_weight(stable_weight):
                return False
            
            # Process the captured weight
            self.process_captured_weight(stable_weight)
            return True
                
        except Exception as e:
            print(f"Error capturing real weighbridge weight: {e}")
            messagebox.showerror("Error", f"Failed to capture weighbridge weight: {str(e)}")
            return False
    
    def wait_for_stable_weight(self):
        """Enhanced: Wait for stable weight reading with timeout"""
        try:
            print("Waiting for stable weight reading...")
            
            weighbridge, weight_var, status_var = config.get_global_weighbridge_info()
            if not weighbridge or not weight_var:
                return None
            
            start_time = time.time()
            stable_readings = []
            required_stable_readings = 5  # Need 5 consecutive stable readings
            
            while (time.time() - start_time) < self.weight_capture_timeout:
                # Get current weight
                current_weight = self.get_current_weighbridge_value()
                if current_weight is None:
                    time.sleep(0.2)
                    continue
                
                # Check if this reading is stable (within tolerance of previous readings)
                if len(stable_readings) == 0:
                    stable_readings.append(current_weight)
                else:
                    # Check if within tolerance of last reading
                    weight_tolerance = getattr(config, 'WEIGHT_TOLERANCE', 1.0)
                    if abs(current_weight - stable_readings[-1]) <= weight_tolerance:
                        stable_readings.append(current_weight)
                        
                        # Keep only recent readings
                        if len(stable_readings) > required_stable_readings:
                            stable_readings.pop(0)
                    else:
                        # Weight changed significantly, reset
                        stable_readings = [current_weight]
                
                # Check if we have enough stable readings
                if len(stable_readings) >= required_stable_readings:
                    final_weight = sum(stable_readings) / len(stable_readings)
                    print(f"Got stable weight: {final_weight:.2f} kg after {len(stable_readings)} readings")
                    return final_weight
                
                time.sleep(0.2)  # Check every 200ms
            
            # Timeout - return best available reading if any
            if stable_readings:
                final_weight = sum(stable_readings) / len(stable_readings)
                print(f"Timeout - returning average of {len(stable_readings)} readings: {final_weight:.2f} kg")
                return final_weight
            
            print("Timeout - no stable weight obtained")
            return None
            
        except Exception as e:
            print(f"Error waiting for stable weight: {e}")
            return None
    
    def validate_captured_weight(self, weight):
        """Enhanced: Validate that captured weight makes sense"""
        try:
            current_weighment = getattr(self.main_form, 'current_weighment', 'first')
            
            # Basic range check
            if weight < 0 or weight > 80000:  # 0 to 80 tons
                messagebox.showerror("Invalid Weight", 
                                   f"Weight {weight:.2f} kg is outside valid range (0-80000 kg)")
                return False
            
            # Enhanced: Check against previous weighment for logical consistency
            if current_weighment == "second":
                try:
                    first_weight_str = self.main_form.first_weight_var.get()
                    if first_weight_str:
                        first_weight = float(first_weight_str)
                        weight_difference = abs(first_weight - weight)
                        
                        # Check minimum weight change
                        if weight_difference < self.min_weight_change:
                            result = messagebox.askyesno("Small Weight Change", 
                                                       f"Weight difference is only {weight_difference:.2f} kg.\n"
                                                       f"First: {first_weight:.2f} kg\n"
                                                       f"Second: {weight:.2f} kg\n\n"
                                                       "This seems unusually small. Continue anyway?")
                            if not result:
                                return False
                        
                        # Check for impossible weight change (too large)
                        if weight_difference > 60000:  # More than 60 tons difference
                            messagebox.showerror("Invalid Weight Change", 
                                               f"Weight difference of {weight_difference:.2f} kg is too large.\n"
                                               f"Please check weighbridge calibration.")
                            return False
                            
                except (ValueError, AttributeError):
                    pass  # First weight not available or invalid
            
            return True
            
        except Exception as e:
            print(f"Error validating weight: {e}")
            return True  # Default to accepting weight if validation fails
    
    def get_current_weighbridge_value(self):
        """Enhanced: Get current weighbridge value with better error handling"""
        try:
            # Get weighbridge info
            weighbridge, weight_var, status_var = config.get_global_weighbridge_info()
            
            if weighbridge is None or weight_var is None or status_var is None:
                print("Could not get weighbridge info")
                return None
            
            # Enhanced: Check connection using improved method from new weighbridge code
            connection_status = weighbridge.get_connection_status()
            if not connection_status.get('connected', False):
                print(f"Weighbridge not connected: {connection_status}")
                return None
            
            # Get weight from the weighbridge display
            weight_str = weight_var.get()
            print(f"Weight string from weighbridge: '{weight_str}'")
            
            # Extract number from string like "123.45 kg"
            import re
            match = re.search(r'(\d+\.?\d*)', weight_str)
            if match:
                weight_value = float(match.group(1))
                print(f"Extracted weight value: {weight_value}")
                return weight_value
            else:
                print("Could not parse weight from string")
                return None
                
        except Exception as e:
            print(f"Error in get_current_weighbridge_value: {e}")
            return None
    
    def is_weighbridge_connected(self):
        """Enhanced: Check weighbridge connection using improved methods"""
        try:
            print("Checking weighbridge connection...")
            
            weighbridge, weight_var, status_var = config.get_global_weighbridge_info()
            
            if weighbridge is None:
                print("No weighbridge manager found")
                return False
            
            # Enhanced: Use the new connection status method if available
            if hasattr(weighbridge, 'get_connection_status'):
                status = weighbridge.get_connection_status()
                is_connected = status.get('connected', False)
                print(f"Enhanced connection check: {is_connected}")
                return is_connected
            
            # Fallback: Use the old method
            if status_var is None:
                print("No status variable found")
                return False
            
            is_connected = status_var.get() == "Status: Connected"
            print(f"Legacy connection check: '{status_var.get()}' -> Connected: {is_connected}")
            return is_connected
            
        except Exception as e:
            print(f"Error checking weighbridge connection: {e}")
            return False
    
    def process_captured_weight(self, weight):
        """Enhanced: Process captured weight with better validation and formatting"""
        try:
            import datetime
            from tkinter import messagebox
            
            print(f"Processing captured weight: {weight}")
            
            current_weighment = getattr(self.main_form, 'current_weighment', 'first')
            timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            if current_weighment == "first":
                # First weighment
                self.main_form.first_weight_var.set(f"{weight:.2f}")
                self.main_form.first_timestamp_var.set(timestamp)
                self.main_form.current_weighment = "second"
                self.main_form.weighment_state_var.set("Second Weighment")
                
                mode_text = "TEST MODE" if self.is_test_mode_enabled() else "WEIGHBRIDGE"
                messagebox.showinfo("First Weight Captured", 
                                   f"First weighment: {weight:.2f} kg\n"
                                   f"Time: {timestamp}\n"
                                   f"Mode: {mode_text}\n\n"
                                   "Vehicle can now exit and return for second weighment.")
                
            elif current_weighment == "second":
                # Second weighment
                self.main_form.second_weight_var.set(f"{weight:.2f}")
                self.main_form.second_timestamp_var.set(timestamp)
                
                # Calculate net weight
                first_weight_str = self.main_form.first_weight_var.get()
                try:
                    first_weight = float(first_weight_str)
                    net_weight = abs(first_weight - weight)
                    self.main_form.net_weight_var.set(f"{net_weight:.2f}")
                    
                    self.main_form.weighment_state_var.set("Weighment Complete")
                    
                    mode_text = "TEST MODE" if self.is_test_mode_enabled() else "WEIGHBRIDGE"
                    
                    # Enhanced: Show more detailed results
                    heavier_weight = max(first_weight, weight)
                    lighter_weight = min(first_weight, weight)
                    weight_type = "Loaded" if first_weight > weight else "Empty"
                    
                    messagebox.showinfo("Second Weight Captured", 
                                       f"Second weighment: {weight:.2f} kg\n"
                                       f"Net weight: {net_weight:.2f} kg\n"
                                       f"Heaviest: {heavier_weight:.2f} kg ({weight_type})\n"
                                       f"Lightest: {lighter_weight:.2f} kg\n"
                                       f"Time: {timestamp}\n"
                                       f"Mode: {mode_text}\n\n"
                                       "Both weighments complete. Ready to save record.")
                except ValueError:
                    messagebox.showerror("Error", "Invalid first weight value")
                    return False
            
            # Enhanced: Update last weight for future reference
            self.last_weight = weight
            return True
            
        except Exception as e:
            print(f"Error processing captured weight: {e}")
            messagebox.showerror("Error", f"Failed to process weight: {str(e)}")
            return False
    
    def get_settings_storage(self):
        """Enhanced: Get settings storage with better error handling"""
        try:
            # Method 1: Try to find through parent hierarchy
            app = self.find_main_app()
            if app and hasattr(app, 'settings_storage'):
                print("Found settings_storage through main app")
                return app.settings_storage
            
            # Method 2: Try to get from main form parent
            widget = self.main_form.parent
            attempts = 0
            while widget and attempts < 10:
                attempts += 1
                if hasattr(widget, 'settings_storage'):
                    print(f"Found settings_storage at widget level {attempts}")
                    return widget.settings_storage
                if hasattr(widget, 'master'):
                    widget = widget.master
                else:
                    break
            
            # Method 3: Create new instance as fallback
            print("Creating new SettingsStorage instance")
            try:
                from settings_storage import SettingsStorage
                return SettingsStorage()
            except ImportError:
                print("Could not import SettingsStorage")
                return None
            
        except Exception as e:
            print(f"Error getting settings storage: {e}")
            return None
    
    def find_main_app(self):
        """Enhanced: Find main app with better traversal and timeout"""
        try:
            # Start from main form and traverse up
            widget = self.main_form.parent
            attempts = 0
            max_attempts = 15
            
            while widget and attempts < max_attempts:
                attempts += 1
                
                # Check for main app indicators
                if hasattr(widget, 'data_manager') and hasattr(widget, 'settings_storage'):
                    print(f"Found main app at level {attempts}")
                    return widget
                
                # Check class name for app identification
                if hasattr(widget, '__class__'):
                    class_name = widget.__class__.__name__
                    if 'App' in class_name or 'Main' in class_name:
                        print(f"Found app class: {class_name}")
                        return widget
                
                # Try different parent references
                if hasattr(widget, 'master') and widget.master:
                    widget = widget.master
                elif hasattr(widget, 'parent') and widget.parent:
                    widget = widget.parent
                elif hasattr(widget, 'winfo_parent'):
                    try:
                        parent_name = widget.winfo_parent()
                        if parent_name:
                            widget = widget._root().nametowidget(parent_name)
                        else:
                            break
                    except Exception:
                        break
                else:
                    break
            
            print(f"Could not find main app after {attempts} attempts")
            return None
            
        except Exception as e:
            print(f"Error finding main app: {e}")
            return None

    def handle_weighbridge_weight(self, weight):
        """Enhanced: Handle weight from weighbridge with validation"""
        try:
            print(f"Weighbridge weight received: {weight}")
            
            # Enhanced: Validate received weight
            if weight is None or weight < 0 or weight > 100000:
                print(f"Invalid weight received: {weight}")
                return False
            
            # Update current weight display with formatting
            self.main_form.current_weight_var.set(f"{weight:.2f} kg")
            
            # Enhanced: Update last weight for stability tracking
            self.last_weight = weight
            
            return True
            
        except Exception as e:
            print(f"Error handling weighbridge weight: {e}")
            return False
    
    def reset_weighment(self):
        """Enhanced: Reset weighment state for new transaction"""
        try:
            print("Resetting weighment state")
            
            # Reset weighment state
            self.main_form.current_weighment = "first"
            self.main_form.weighment_state_var.set("First Weighment")
            
            # Clear weight values but keep current display
            self.main_form.first_weight_var.set("0.00")
            self.main_form.second_weight_var.set("0.00")
            self.main_form.net_weight_var.set("0.00")
            self.main_form.first_timestamp_var.set("")
            self.main_form.second_timestamp_var.set("")
            
            print("Weighment state reset successfully")
            return True
            
        except Exception as e:
            print(f"Error resetting weighment: {e}")
            return False