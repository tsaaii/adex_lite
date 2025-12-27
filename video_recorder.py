# video_recorder.py - Video clip recording component
# Records video clips from "Capture Weight" to "Save Image" clicks

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
        self.recording_enabled = False  # Toggle from settings
        
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
        
        # Background save thread
        self.save_thread = None
        
        print("✅ VideoRecorder initialized")
    
    def set_recording_enabled(self, enabled):
        """Enable or disable video recording from settings toggle"""
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
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting video recording: {e}")
            self.is_recording = False
            return False
    
    def add_frame(self, frame, camera_type="front"):
        """
        Add a frame to the recording buffer.
        Called from camera continuous feed.
        
        Args:
            frame: OpenCV frame (BGR format)
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
            
            # Add frame to appropriate buffer (make a copy to avoid memory issues)
            frame_copy = frame.copy()
            
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
            save: Whether to save the recorded video clips
            
        Returns:
            tuple: (front_clip_path, back_clip_path) or (None, None) if not saved
        """
        if not self.is_recording:
            return None, None
        
        self.is_recording = False
        
        if not save:
            print("📹 Recording stopped without saving")
            with self.frame_lock:
                self.front_frames = []
                self.back_frames = []
            return None, None
        
        try:
            # Get frames atomically
            with self.frame_lock:
                front_frames = self.front_frames.copy()
                back_frames = self.back_frames.copy()
                self.front_frames = []
                self.back_frames = []
            
            print(f"📹 Recording stopped")
            print(f"   Front frames: {len(front_frames)}")
            print(f"   Back frames: {len(back_frames)}")
            
            # Calculate duration
            if self.recording_start_time:
                duration = (datetime.datetime.now() - self.recording_start_time).total_seconds()
                print(f"   Duration: {duration:.1f}s")
            
            # Save clips in background thread to avoid blocking UI
            self.save_thread = threading.Thread(
                target=self._save_clips_async,
                args=(front_frames, back_frames),
                daemon=True
            )
            self.save_thread.start()
            
            return True, True  # Indicate saving started
            
        except Exception as e:
            print(f"❌ Error stopping video recording: {e}")
            return None, None
    
    def _save_clips_async(self, front_frames, back_frames):
        """Save video clips asynchronously in background thread"""
        try:
            # Create clips folder
            clips_folder = self._create_clips_folder()
            if not clips_folder:
                print("❌ Failed to create clips folder")
                return
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            weighment_label = "1st" if self.weighment_type == "first" else "2nd"
            
            # Save front camera clip
            if front_frames and len(front_frames) > 0:
                front_filename = f"{self.site_name}_{self.vehicle_number}_{timestamp}_{weighment_label}_front.mp4"
                front_path = os.path.join(clips_folder, front_filename)
                self._save_video(front_frames, front_path)
                print(f"✅ Front clip saved: {front_filename}")
            else:
                print("⚠️ No front frames to save")
            
            # Save back camera clip
            if back_frames and len(back_frames) > 0:
                back_filename = f"{self.site_name}_{self.vehicle_number}_{timestamp}_{weighment_label}_back.mp4"
                back_path = os.path.join(clips_folder, back_filename)
                self._save_video(back_frames, back_path)
                print(f"✅ Back clip saved: {back_filename}")
            else:
                print("⚠️ No back frames to save")
            
            print(f"📁 Clips saved to: {clips_folder}")
            
        except Exception as e:
            print(f"❌ Error saving video clips: {e}")
    
    def _create_clips_folder(self):
        """
        Create the clips folder structure:
        captured_images/[date]/clips/[vehicle_number]/
        
        Returns:
            str: Path to the vehicle's clips folder
        """
        try:
            # Main captured images folder
            captured_images_folder = os.path.join(config.DATA_FOLDER, "captured_images")
            os.makedirs(captured_images_folder, exist_ok=True)
            
            # Today's date folder
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            today_folder = os.path.join(captured_images_folder, today_str)
            os.makedirs(today_folder, exist_ok=True)
            
            # Clips folder
            clips_folder = os.path.join(today_folder, "clips")
            os.makedirs(clips_folder, exist_ok=True)
            
            # Vehicle number folder
            vehicle_folder = os.path.join(clips_folder, self.vehicle_number)
            os.makedirs(vehicle_folder, exist_ok=True)
            
            return vehicle_folder
            
        except Exception as e:
            print(f"❌ Error creating clips folder: {e}")
            return None
    
    def _save_video(self, frames, output_path):
        """
        Save frames as video file.
        
        Args:
            frames: List of OpenCV frames
            output_path: Output video file path
        """
        if not frames or len(frames) == 0:
            return False
        
        try:
            # Get frame dimensions from first frame
            height, width = frames[0].shape[:2]
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*self.video_codec)
            out = cv2.VideoWriter(output_path, fourcc, self.fps, (width, height))
            
            if not out.isOpened():
                print(f"❌ Failed to open video writer for {output_path}")
                return False
            
            # Write frames
            for frame in frames:
                out.write(frame)
            
            out.release()
            
            # Verify file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"   Saved: {output_path} ({file_size / 1024:.1f} KB)")
                return True
            else:
                print(f"❌ Video file not created: {output_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error saving video: {e}")
            return False
    
    def get_recording_status(self):
        """Get current recording status for UI display"""
        if not self.recording_enabled:
            return "Video recording disabled"
        
        if self.is_recording:
            elapsed = 0
            if self.recording_start_time:
                elapsed = (datetime.datetime.now() - self.recording_start_time).total_seconds()
            
            with self.frame_lock:
                front_count = len(self.front_frames)
                back_count = len(self.back_frames)
            
            return f"🔴 Recording: {elapsed:.0f}s (F:{front_count} B:{back_count})"
        
        return "Ready to record"
    
    def cancel_recording(self):
        """Cancel current recording without saving"""
        if self.is_recording:
            print("📹 Recording cancelled")
            self.stop_recording(save=False)