# video_recorder.py - Video clip recording component (UPDATED)
# Records video clips from "Capture Weight" to "Save Image" clicks
# NOW: Saves video at same resolution as captured images

import threading
import time
import os
import datetime
import cv2
import queue
import config


class VideoRecorder:
    """
    Records video clips from cameras between capture weight and save image events.
    
    UPDATED: Video frames are now saved at the same resolution as the images
    saved in images and captured_images folders, ensuring consistent size/aspect ratio.
    
    Usage:
        1. Call start_recording() when "Capture Weight" is clicked
        2. Feed frames using add_frame() from camera continuous feed
        3. Call stop_recording() when "Save Image" is clicked
        4. Video is automatically saved to captured_images/[date]/clips/[vehicle_no]/
    """
    
    def __init__(self, main_form=None):
        self.main_form = main_form
        
        # Recording state
        self.is_recording = False
        self.recording_enabled = False  # Toggle from settings (Equalizer)
        
        # Frame buffers for front and back cameras
        self.front_frames = []
        self.back_frames = []
        self.frame_lock = threading.Lock()
        
        # Recording metadata
        self.recording_start_time = None
        self.vehicle_number = None
        self.site_name = None
        self.weighment_type = None  # "first" or "second"
        
        # Video settings
        self.fps = 15  # Frames per second for saved video
        self.max_duration = 120  # Maximum recording duration in seconds (safety limit)
        self.video_codec = 'mp4v'  # MP4 codec
        
        # Target resolution for video (same as captured images)
        # This will be set dynamically based on the first frame captured
        # or can be configured to match your image save settings
        self.target_width = None
        self.target_height = None
        self.resolution_locked = False  # Lock resolution after first frame
        
        # Background save thread
        self.save_thread = None
        
        print("✅ VideoRecorder initialized (resolution-matched mode)")
    
    def set_target_resolution(self, width, height):
        """
        Set the target resolution for video recording.
        This should match the resolution of images saved in captured_images folder.
        
        Args:
            width: Target width in pixels
            height: Target height in pixels
        """
        self.target_width = width
        self.target_height = height
        print(f"📐 Video target resolution set to: {width}x{height}")
    
    def get_image_resolution_from_camera(self):
        """
        Get the resolution from the camera's current frame (full resolution).
        This matches what gets saved as images.
        """
        try:
            if self.main_form:
                # Try to get resolution from front camera
                if hasattr(self.main_form, 'front_camera') and self.main_form.front_camera:
                    cam = self.main_form.front_camera
                    if hasattr(cam, 'current_frame') and cam.current_frame is not None:
                        h, w = cam.current_frame.shape[:2]
                        return w, h
                    if hasattr(cam, 'captured_image') and cam.captured_image is not None:
                        h, w = cam.captured_image.shape[:2]
                        return w, h
                
                # Try to get resolution from back camera
                if hasattr(self.main_form, 'back_camera') and self.main_form.back_camera:
                    cam = self.main_form.back_camera
                    if hasattr(cam, 'current_frame') and cam.current_frame is not None:
                        h, w = cam.current_frame.shape[:2]
                        return w, h
                    if hasattr(cam, 'captured_image') and cam.captured_image is not None:
                        h, w = cam.captured_image.shape[:2]
                        return w, h
        except Exception as e:
            print(f"⚠️ Could not get camera resolution: {e}")
        
        return None, None
    
    def set_recording_enabled(self, enabled):
        """Enable or disable video recording from settings toggle (Equalizer)"""
        self.recording_enabled = enabled
        print(f"📹 Video recording {'enabled' if enabled else 'disabled'}")
    
    def is_enabled(self):
        """Check if video recording is enabled"""
        return self.recording_enabled
    
    def start_recording(self, vehicle_number, site_name, weighment_type="first"):
        """
        Start recording video clips from both cameras.
        Called when "Capture Weight" button is clicked.
        
        Args:
            vehicle_number: Current vehicle number
            site_name: Current site name
            weighment_type: "first" or "second" weighment
        """
        if not self.recording_enabled:
            print("📹 Video recording disabled - skipping start")
            return False
        
        if self.is_recording:
            print("⚠️ Already recording - stopping previous recording")
            self.stop_recording(save=False)
        
        try:
            # Store metadata
            self.vehicle_number = vehicle_number.replace(" ", "_").replace("/", "_")
            self.site_name = site_name.replace(" ", "_")
            self.weighment_type = weighment_type
            self.recording_start_time = datetime.datetime.now()
            
            # Try to get target resolution from camera
            w, h = self.get_image_resolution_from_camera()
            if w and h:
                self.target_width = w
                self.target_height = h
                print(f"📐 Video resolution set from camera: {w}x{h}")
            
            # Reset resolution lock for new recording
            self.resolution_locked = False
            
            # Clear frame buffers
            with self.frame_lock:
                self.front_frames = []
                self.back_frames = []
            
            # Start recording
            self.is_recording = True
            
            print(f"🎬 Video recording STARTED")
            print(f"   Vehicle: {self.vehicle_number}")
            print(f"   Site: {self.site_name}")
            print(f"   Weighment: {self.weighment_type}")
            if self.target_width and self.target_height:
                print(f"   Target Resolution: {self.target_width}x{self.target_height}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting video recording: {e}")
            self.is_recording = False
            return False
    
    def _normalize_frame_resolution(self, frame):
        """
        Normalize frame to target resolution (same as saved images).
        This ensures all video frames match the image resolution exactly.
        
        Args:
            frame: Input OpenCV frame (BGR)
            
        Returns:
            Frame resized to target resolution
        """
        if frame is None:
            return None
        
        try:
            h, w = frame.shape[:2]
            
            # If no target resolution set, use this frame's resolution as target
            if not self.resolution_locked:
                if self.target_width is None or self.target_height is None:
                    self.target_width = w
                    self.target_height = h
                    print(f"📐 Locked video resolution to first frame: {w}x{h}")
                self.resolution_locked = True
            
            # If frame already matches target, return as-is
            if w == self.target_width and h == self.target_height:
                return frame
            
            # Resize to match target resolution
            resized = cv2.resize(frame, (self.target_width, self.target_height), 
                                interpolation=cv2.INTER_LANCZOS4)
            return resized
            
        except Exception as e:
            print(f"⚠️ Frame normalization error: {e}")
            return frame
    
    def add_frame(self, frame, camera_type="front"):
        """
        Add a frame to the recording buffer.
        Called from camera continuous feed.
        
        UPDATED: Frame is normalized to match saved image resolution.
        
        Args:
            frame: OpenCV frame (BGR format) - will be resized to match image resolution
            camera_type: "front" or "back"
        """
        if not self.is_recording or not self.recording_enabled:
            return
        
        if frame is None:
            return
        
        try:
            # Check max duration safety limit
            if self.recording_start_time:
                elapsed = (datetime.datetime.now() - self.recording_start_time).total_seconds()
                if elapsed > self.max_duration:
                    print(f"⚠️ Max recording duration reached ({self.max_duration}s) - stopping")
                    self.stop_recording(save=True)
                    return
            
            # IMPORTANT: Normalize frame to match saved image resolution
            normalized_frame = self._normalize_frame_resolution(frame)
            
            if normalized_frame is None:
                return
            
            # Add frame to appropriate buffer (make a copy to avoid memory issues)
            frame_copy = normalized_frame.copy()
            
            with self.frame_lock:
                if camera_type == "front":
                    self.front_frames.append(frame_copy)
                elif camera_type == "back":
                    self.back_frames.append(frame_copy)
                    
        except Exception as e:
            print(f"❌ Error adding frame to recording: {e}")
    
    def stop_recording(self, save=True):
        """
        Stop recording and optionally save the video clips.
        Called when "Save Image" button is clicked.
        
        Args:
            save: If True, save the recorded clips to files
        """
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        with self.frame_lock:
            front_count = len(self.front_frames)
            back_count = len(self.back_frames)
        
        print(f"🎬 Video recording STOPPED")
        print(f"   Front frames: {front_count}")
        print(f"   Back frames: {back_count}")
        
        if save and (front_count > 0 or back_count > 0):
            # Save in background thread
            self.save_thread = threading.Thread(target=self._save_clips_background, daemon=True)
            self.save_thread.start()
        else:
            # Clear buffers without saving
            with self.frame_lock:
                self.front_frames = []
                self.back_frames = []
    
    def _save_clips_background(self):
        """Save video clips in background thread"""
        try:
            # Create output directory
            output_dir = self._create_output_directory()
            if not output_dir:
                print("❌ Could not create output directory")
                return
            
            # Generate timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Get frames and clear buffers
            with self.frame_lock:
                front_frames = self.front_frames.copy()
                back_frames = self.back_frames.copy()
                self.front_frames = []
                self.back_frames = []
            
            # Save front camera clip
            if front_frames:
                front_filename = f"{self.site_name}_{self.vehicle_number}_{timestamp}_{self.weighment_type}_front.mp4"
                front_path = os.path.join(output_dir, front_filename)
                self._save_video_clip(front_frames, front_path, "front")
            
            # Save back camera clip
            if back_frames:
                back_filename = f"{self.site_name}_{self.vehicle_number}_{timestamp}_{self.weighment_type}_back.mp4"
                back_path = os.path.join(output_dir, back_filename)
                self._save_video_clip(back_frames, back_path, "back")
            
            print(f"✅ Video clips saved to: {output_dir}")
            
        except Exception as e:
            print(f"❌ Error saving video clips: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_output_directory(self):
        """Create output directory for video clips"""
        try:
            # Base path: captured_images/[date]/clips/[vehicle_no]/
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Use config.DATA_FOLDER if available, otherwise use current directory
            base_path = getattr(config, 'DATA_FOLDER', '.')
            output_dir = os.path.join(base_path, "captured_images", today, "clips", self.vehicle_number)
            
            os.makedirs(output_dir, exist_ok=True)
            return output_dir
            
        except Exception as e:
            print(f"❌ Error creating output directory: {e}")
            return None
    
    def _save_video_clip(self, frames, filepath, camera_name):
        """
        Save frames as video clip.
        UPDATED: Uses consistent resolution matching saved images.
        """
        try:
            if not frames:
                print(f"⚠️ No frames to save for {camera_name}")
                return False
            
            # Get frame dimensions from first frame (all frames should now be same size)
            h, w = frames[0].shape[:2]
            
            print(f"📼 Saving {camera_name} clip: {len(frames)} frames at {w}x{h} @ {self.fps}fps")
            
            # Create video writer with MP4 codec
            fourcc = cv2.VideoWriter_fourcc(*self.video_codec)
            writer = cv2.VideoWriter(filepath, fourcc, self.fps, (w, h))
            
            if not writer.isOpened():
                print(f"❌ Could not open video writer for {filepath}")
                return False
            
            # Write frames
            for frame in frames:
                writer.write(frame)
            
            writer.release()
            
            # Verify file was created
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
                duration = len(frames) / self.fps
                print(f"✅ Saved {camera_name}: {filepath}")
                print(f"   Resolution: {w}x{h}")
                print(f"   Duration: {duration:.1f}s")
                print(f"   Size: {file_size:.2f} MB")
                return True
            else:
                print(f"❌ Video file was not created: {filepath}")
                return False
                
        except Exception as e:
            print(f"❌ Error saving {camera_name} clip: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def cancel_recording(self):
        """Cancel current recording without saving"""
        if self.is_recording:
            print("⚠️ Cancelling video recording")
            self.stop_recording(save=False)
    
    def get_recording_status(self):
        """Get current recording status"""
        with self.frame_lock:
            return {
                "is_recording": self.is_recording,
                "enabled": self.recording_enabled,
                "front_frames": len(self.front_frames),
                "back_frames": len(self.back_frames),
                "vehicle": self.vehicle_number,
                "site": self.site_name,
                "weighment_type": self.weighment_type,
                "target_resolution": f"{self.target_width}x{self.target_height}" if self.target_width else "Auto"
            }