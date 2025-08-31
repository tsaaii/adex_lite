"""
Weight Manager Integration - Add these methods to your existing weight_manager.py
"""

import datetime
import logging
from tkinter import messagebox

# Add this to your existing WeightManager class initialization
def init_vehicle_managers(self):
    """Initialize vehicle data and image managers"""
    from vehicle_data_manager import VehicleDataManager
    from image_selector import ImageSelector
    from ticket_closer import TicketCloser
    
    self.vehicle_mgr = VehicleDataManager("data")
    self.image_selector = ImageSelector("images")
    self.ticket_closer = TicketCloser(self.vehicle_mgr, self.image_selector)
    self.logger = logging.getLogger('WeightManager')

# Replace or enhance your existing capture_weight method
def enhanced_capture_weight(self):
    """Enhanced weight capture with quick close support"""
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

# Add this new method for quick close
def perform_quick_close(self):
    """Perform quick close using stored empty weight"""
    try:
        vehicle_no = self.main_form.vehicle_var.get()
        first_weight = float(self.main_form.first_weight_var.get())
        first_timestamp = self.main_form.first_timestamp_var.get()
        
        # Quick close
        result = self.ticket_closer.quick_close(vehicle_no, first_weight, first_timestamp)
        
        if result:
            # Update form fields
            self.main_form.second_weight_var.set(f"{result['second_weight']:.2f}")
            self.main_form.second_timestamp_var.set(result['second_timestamp'])
            self.main_form.net_weight_var.set(f"{result['net_weight']:.2f}")
            
            # Update image paths
            if result['second_front_image']:
                self.main_form.second_front_image_path = result['second_front_image']
            if result['second_back_image']:
                self.main_form.second_back_image_path = result['second_back_image']
            
            # Update state
            self.main_form.current_weighment = "complete"
            self.main_form.weighment_state_var.set("Weighment Complete")
            
            # Update image status display if method exists
            if hasattr(self.main_form, 'update_image_status_display'):
                self.main_form.update_image_status_display()
            
            messagebox.showinfo(
                "Quick Close Success",
                f"Ticket closed successfully!\n\n"
                f"Net Weight: {result['net_weight']:.2f} kg\n"
                f"Method: Quick close with stored weight"
            )
        
    except Exception as e:
        self.logger.error(f"Error in quick close: {e}")
        messagebox.showerror("Error", f"Failed to quick close: {str(e)}")

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