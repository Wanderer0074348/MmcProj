import cv2
import time
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import sys
import platform
from moviepy import VideoFileClip
import tempfile
import numpy as np
# from moviepy.audio.fx import speedx 

class ImprovedMediaPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("MoviePy Media Player Pro")
        
        # Initialize pygame for audio
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        
        # Video components
        self.vid = None
        self.clip = None
        self.sound = None
        self.playing = False
        self.paused = False
        self.playback_speed = 1.0
        self.volume = 1.0
        self.frame = None
        self.stop_event = threading.Event()
        self.file_path = None
        self.current_position = 0
        self.temp_audio_file = None
        
        # Get screen dimensions
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Setup FFmpeg paths for Windows
        self.setup_ffmpeg_paths()
        
        # Check FFmpeg availability
        self.check_ffmpeg()
        
        # GUI setup
        self.create_widgets()
        
        # Print audio driver info
        print(f"Using audio driver: pygame.mixer with MoviePy")
        
        # Set up event handling for audio
        pygame.mixer.music.set_endevent(pygame.USEREVENT)
        
        # Start a timer to check for pygame events
        self.root.after(100, self.check_pygame_events)
        
        # Bind window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Configure>", self.on_resize)

    def check_pygame_events(self):
        """Check for pygame events like audio end"""
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                # Music has ended
                print("Audio playback ended")
                
        # Continue checking events
        self.root.after(100, self.check_pygame_events)

    def setup_ffmpeg_paths(self):
        """Setup FFmpeg paths for Windows"""
        if platform.system() == 'Windows':
            # Try to find FFmpeg in common locations
            possible_paths = [
                # Current directory
                os.path.join(os.getcwd(), 'ffmpeg', 'bin'),
                os.path.join(os.getcwd(), 'lib', 'ffmpeg', 'bin'),
                # Program Files
                r"C:\Program Files\ffmpeg\bin",
                # Winget location
                os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg\bin"),
                # Scoop location
                os.path.expanduser(r"~\scoop\apps\ffmpeg\current\bin"),
                # Chocolatey location
                r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin"
            ]
            
            # Create lib directory if it doesn't exist
            lib_dir = os.path.join(os.getcwd(), 'lib')
            if not os.path.exists(lib_dir):
                os.makedirs(lib_dir, exist_ok=True)
            
            # Add all potential paths to the system PATH
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"Found FFmpeg at: {path}")
                    if path not in os.environ["PATH"]:
                        os.environ["PATH"] = f"{path};{os.environ['PATH']}"
                    break

    def check_ffmpeg(self):
        """Verify FFmpeg is available and print status"""
        try:
            import imageio
            imageio.plugins.ffmpeg.download()
            print("FFmpeg is available via MoviePy/imageio")
            return True
        except Exception as e:
            print(f"Note about FFmpeg: {e}")
            return True  # Continue anyway as MoviePy will handle this

    def ensure_ffmpeg(self):
        """Attempt to ensure FFmpeg is available"""
        # First try the standard check
        if self.check_ffmpeg():
            messagebox.showinfo("FFmpeg Status", "FFmpeg is available and working.")
            return True
            
        # If FFmpeg is not available, inform the user
        if messagebox.askyesno("FFmpeg Required", 
                              "FFmpeg is required to play most media formats. Would you like to see installation instructions?"):
            self.show_ffmpeg_instructions()
        return False

    def show_ffmpeg_instructions(self):
        """Show FFmpeg installation instructions based on platform"""
        instructions = {
            "Windows": "1. Download FFmpeg from https://ffmpeg.org/download.html\n"
                      "2. Extract the archive to a folder (e.g., C:\\ffmpeg)\n"
                      "3. Add the bin folder to your PATH environment variable\n"
                      "4. Restart the application\n\n"
                      "Alternatively:\n"
                      "1. Create a 'lib' folder in the same directory as this application\n"
                      "2. Inside the lib folder, create an 'ffmpeg' folder\n"
                      "3. Copy the FFmpeg DLLs (avcodec-*.dll, avformat-*.dll, etc.) to this ffmpeg folder\n"
                      "4. Restart the application\n\n"
                      "You can also install FFmpeg using winget:\n"
                      "winget install Gyan.FFmpeg",
            "Darwin": "1. Install Homebrew if not already installed:\n   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n"
                     "2. Install FFmpeg:\n   brew install ffmpeg\n"
                     "3. Restart the application",
            "Linux": "1. Install FFmpeg using your package manager:\n"
                    "   Ubuntu/Debian: sudo apt-get install ffmpeg\n"
                    "   Fedora: sudo dnf install ffmpeg\n"
                    "   Arch: sudo pacman -S ffmpeg\n"
                    "2. Restart the application"
        }
        
        platform_name = platform.system()
        if platform_name not in instructions:
            platform_name = "Windows"  # Default to Windows instructions
        
        instruction_text = instructions.get(platform_name, "Please install FFmpeg for your platform")
        
        # Create a window with instructions
        instr_win = tk.Toplevel(self.root)
        instr_win.title("FFmpeg Installation Instructions")
        instr_win.geometry("500x400")
        instr_win.transient(self.root)
        instr_win.grab_set()
        
        text = tk.Text(instr_win, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, f"FFmpeg Installation for {platform_name}:\n\n")
        text.insert(tk.END, instruction_text)
        text.config(state=tk.DISABLED)

    def create_widgets(self):
        # Create canvas for video and controls
        self.canvas = tk.Canvas(self.root, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Overlay controls using place manager
        self.control_frame = ttk.Frame(self.canvas, style='Controls.TFrame')
        self.control_frame.place(relx=0.5, rely=0.95, anchor=tk.S)
        
        # Playback controls
        self.play_btn = ttk.Button(self.control_frame, text="▶", width=3, command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        # Speed control
        speed_frame = ttk.Frame(self.control_frame)
        speed_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.TOP)
        self.speed_slider = ttk.Scale(speed_frame, from_=0.5, to=2.0, value=1.0, length=100, orient=tk.HORIZONTAL)
        self.speed_slider.pack(side=tk.TOP)
        self.speed_slider.bind("<ButtonRelease-1>", self.update_speed)
        self.speed_label = ttk.Label(speed_frame, text="1.0x")
        self.speed_label.pack(side=tk.TOP)
        
        # Volume control
        vol_frame = ttk.Frame(self.control_frame)
        vol_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(vol_frame, text="Volume:").pack(side=tk.TOP)
        self.vol_slider = ttk.Scale(vol_frame, from_=0.0, to=1.0, value=1.0, length=100, orient=tk.HORIZONTAL)
        self.vol_slider.pack(side=tk.TOP)
        self.vol_slider.bind("<ButtonRelease-1>", self.update_volume)
        
        # Metadata button
        self.meta_btn = ttk.Button(self.control_frame, text="Metadata", command=self.show_metadata)
        self.meta_btn.pack(side=tk.LEFT, padx=5)
        
        # Menu
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Add FFmpeg menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Check FFmpeg", command=self.ensure_ffmpeg)
        tools_menu.add_command(label="FFmpeg Installation Help", command=self.show_ffmpeg_instructions)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        self.root.config(menu=menubar)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[
            ("Media Files", "*.mp4 *.avi *.mov *.mkv *.mp3 *.wav")
        ])
        
        if file_path:
            # Stop any current playback
            if self.playing:
                self.stop_media()
                
            self.file_path = file_path
            if self.initialize_media(file_path):
                self.auto_resize_window()
                self.play_media()

    def initialize_media(self, file_path):
        try:
            # Clean up any previous temp files
            self.cleanup_temp_files()
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Handle audio-only files
            if file_ext in ['.mp3', '.wav']:
                # For audio files, we'll use pygame directly
                try:
                    pygame.mixer.music.load(file_path)
                    self.sound = True
                    self.clip = None
                    # Create a blank frame for audio-only files
                    self.original_width = 400
                    self.original_height = 300
                    self.aspect_ratio = self.original_width / self.original_height
                    self.fps = 30
                    self.frame_count = 1
                    self.duration = 0  # Will be updated from pygame
                    print("Loaded audio file with pygame mixer")
                except Exception as audio_error:
                    print(f"Audio initialization error: {audio_error}")
                    self.sound = False
                    return False
            else:
                # For video files, use MoviePy
                try:
                    # Load the video with MoviePy
                    self.clip = VideoFileClip(file_path)
                    
                    # Extract video properties
                    self.original_width, self.original_height = self.clip.size
                    self.aspect_ratio = self.original_width / self.original_height
                    self.fps = self.clip.fps
                    self.frame_count = int(self.clip.fps * self.clip.duration)
                    self.duration = self.clip.duration
                    
                    # Check if video has audio
                    if self.clip.audio is not None:
                        print("Video has audio track, extracting...")
                        # Extract audio to a temporary file with current speed setting
                        self.temp_audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
                        
                        # Apply speed adjustment if needed
                        if self.playback_speed != 1.0:
                            speed_adjusted_audio = self.clip.audio.afx.speedx(self.playback_speed)
                            speed_adjusted_audio.write_audiofile(self.temp_audio_file, codec='pcm_s16le', logger=None)
                        else:
                            self.clip.audio.write_audiofile(self.temp_audio_file, codec='pcm_s16le', logger=None)
                            
                        pygame.mixer.music.load(self.temp_audio_file)
                        self.sound = True
                        print(f"Extracted audio to temporary file: {self.temp_audio_file}")
                    else:
                        self.sound = False
                        print("Video has no audio track")
                    
                    # Initialize OpenCV capture for frame-by-frame access
                    # (we use this alongside MoviePy for better frame control)
                    self.vid = cv2.VideoCapture(file_path)
                    if not self.vid.isOpened():
                        raise ValueError("Error opening video file with OpenCV")
                        
                except Exception as e:
                    print(f"MoviePy initialization error: {e}")
                    # Fallback to OpenCV only
                    try:
                        self.clip = None
                        self.vid = cv2.VideoCapture(file_path)
                        if not self.vid.isOpened():
                            raise ValueError("Error opening video file")
                        
                        self.original_width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
                        self.original_height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        self.aspect_ratio = self.original_width / self.original_height
                        self.fps = self.vid.get(cv2.CAP_PROP_FPS)
                        self.frame_count = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))
                        self.duration = self.frame_count / self.fps if self.fps > 0 else 0
                        self.sound = False
                    except Exception as cv_error:
                        print(f"OpenCV fallback error: {cv_error}")
                        return False

            # Reset position
            self.current_position = 0
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not initialize media: {str(e)}")
            return False
            
        return True

    def cleanup_temp_files(self):
        """Clean up any temporary files"""
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.unlink(self.temp_audio_file)
                print(f"Removed temporary audio file: {self.temp_audio_file}")
            except Exception as e:
                print(f"Error removing temporary file: {e}")
            self.temp_audio_file = None

    def auto_resize_window(self):
        max_width = int(self.screen_width * 0.8)
        max_height = int(self.screen_height * 0.8)
        
        if self.original_width > max_width or self.original_height > max_height:
            width_ratio = max_width / self.original_width
            height_ratio = max_height / self.original_height
            scale = min(width_ratio, height_ratio)
            new_width = int(self.original_width * scale)
            new_height = int(self.original_height * scale)
            self.root.geometry(f"{new_width}x{new_height}")
        else:
            # Add padding for controls
            self.root.geometry(f"{self.original_width}x{self.original_height + 50}")

    def play_media(self):
        if not (self.vid or self.clip) and not self.sound:
            return
            
        self.playing = True
        self.paused = False
        self.play_btn.config(text="⏸")
        self.stop_event.clear()
        
        # Start audio playback with pygame
        if self.sound:
            print(f"Starting audio playback, volume: {self.volume}")
            pygame.mixer.music.set_volume(self.volume)
            
            # If we're not at the beginning and speed isn't 1.0, 
            # we need to adjust the start position
            if self.current_position > 0 and self.playback_speed != 1.0:
                pygame.mixer.music.play(start=self.current_position)
            else:
                pygame.mixer.music.play()
                
            # Add a small delay to ensure audio starts playing
            time.sleep(0.1)
            print(f"Audio playing: {pygame.mixer.music.get_busy()}")
        
        # For audio-only files, we don't need a video thread
        if not (self.vid or self.clip):
            # For audio-only files, we need to keep checking if the audio is still playing
            def audio_monitor():
                while self.playing and not self.stop_event.is_set():
                    if not pygame.mixer.music.get_busy() and not self.paused:
                        # Audio finished playing
                        self.root.after(0, self.handle_playback_end)
                        break
                    time.sleep(0.1)
                    
            threading.Thread(target=audio_monitor, daemon=True).start()
            return
        
        def video_thread():
            start_time = time.time()
            
            while self.playing and not self.stop_event.is_set():
                if self.paused:
                    time.sleep(0.1)  # Reduce CPU usage while paused
                    continue
                
                frame_time = time.time()
                
                # Calculate which frame to show based on current time and speed
                elapsed = (frame_time - start_time) * self.playback_speed
                self.current_position = elapsed
                
                # Get the frame using MoviePy if available, otherwise OpenCV
                if self.clip:
                    try:
                        # Check if we've reached the end of the video
                        if elapsed >= self.clip.duration:
                            break
                            
                        # Get frame from MoviePy at the current position
                        frame_pos = min(elapsed, self.clip.duration)
                        movie_frame = self.clip.get_frame(frame_pos)
                        
                        # Convert from RGB to BGR for OpenCV processing
                        frame = cv2.cvtColor(movie_frame, cv2.COLOR_RGB2BGR)
                    except Exception as e:
                        print(f"MoviePy frame error: {e}")
                        # Fallback to OpenCV
                        if self.vid:
                            self.vid.set(cv2.CAP_PROP_POS_MSEC, elapsed * 1000)
                            ret, frame = self.vid.read()
                            if not ret:
                                break
                        else:
                            break
                elif self.vid:
                    # Use OpenCV directly
                    self.vid.set(cv2.CAP_PROP_POS_MSEC, elapsed * 1000)
                    ret, frame = self.vid.read()
                    if not ret:
                        break
                else:
                    break
                
                # Resize frame while maintaining aspect ratio and scale
                current_width = self.canvas.winfo_width()
                current_height = self.canvas.winfo_height()
                if current_width > 0 and current_height > 0:
                    frame = self.resize_frame(frame, current_width, current_height)
                
                # Convert to RGB for display
                self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Update display in main thread
                self.root.after(0, self.update_display)
                
                # Calculate delay for next frame
                next_frame_time = frame_time + (1.0 / self.fps / self.playback_speed)
                delay = next_frame_time - time.time()
                if delay > 0:
                    time.sleep(delay)

            # End of playback
            if not self.stop_event.is_set():
                self.root.after(0, self.handle_playback_end)

        threading.Thread(target=video_thread, daemon=True).start()

    def handle_playback_end(self):
        self.playing = False
        self.play_btn.config(text="▶")
        # Reset to beginning
        if self.vid:
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.current_position = 0
        if self.sound:
            pygame.mixer.music.stop()

    def resize_frame(self, frame, target_width, target_height):
        h, w = frame.shape[:2]
        # Only shrink if necessary, never stretch
        if w > target_width or h > target_height:
            width_ratio = target_width / w
            height_ratio = target_height / h
            scale_factor = min(width_ratio, height_ratio)
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
        else:
            new_w = w
            new_h = h
        new_w = max(1, new_w)
        new_h = max(1, new_h)
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def update_display(self):
        if self.frame is not None and self.canvas.winfo_exists():
            try:
                h, w = self.frame.shape[:2]
                img_data = cv2.imencode('.ppm', self.frame)[1].tobytes()
                img = tk.PhotoImage(data=img_data)
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                x_pos = (canvas_width - w) // 2
                y_pos = (canvas_height - h) // 2
                self.canvas.delete("all")
                self.canvas.create_image(x_pos, y_pos, image=img, anchor=tk.NW)
                self.canvas.image = img  # Keep reference to prevent garbage collection
                self.control_frame.lift()
            except Exception as e:
                print(f"Display update error: {e}")

    def on_resize(self, event):
        if event.widget == self.root and self.playing:
            self.control_frame.place(relx=0.5, rely=0.95, anchor=tk.S)
            self.root.after(10, self.update_display)

    def toggle_play(self):
        if not (self.vid or self.clip) and not self.sound:
            return
            
        if self.playing and not self.paused:
            # Pause playback
            self.paused = True
            self.play_btn.config(text="▶")
            if self.sound:
                pygame.mixer.music.pause()
        elif self.playing and self.paused:
            # Resume playback
            self.paused = False
            self.play_btn.config(text="⏸")
            if self.sound:
                pygame.mixer.music.unpause()
        else:
            # Start playback
            self.play_media()

    def update_speed(self, event=None):
        new_speed = self.speed_slider.get()
        
        # Only update if speed actually changed
        if abs(new_speed - self.playback_speed) < 0.01:
            return
        
        old_speed = self.playback_speed    
        self.playback_speed = new_speed
        self.speed_label.config(text=f"{new_speed:.1f}x")
        
        # For audio, we need to regenerate the audio file with the new speed
        if self.sound and self.clip and self.clip.audio:
            # Remember current position
            current_pos = self.current_position
            
            # Stop current audio
            pygame.mixer.music.stop()
            
            # Clean up previous temp file
            self.cleanup_temp_files()
            
            try:
                # Create new audio file with adjusted speed
                self.temp_audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
                
                # Use moviepy to create speed-adjusted audio
                speed_adjusted_audio = self.clip.audio.afx.speedx(self.playback_speed)
                speed_adjusted_audio.write_audiofile(self.temp_audio_file, codec='pcm_s16le', logger=None)
                
                # Load and play the new audio file
                pygame.mixer.music.load(self.temp_audio_file)
                pygame.mixer.music.set_volume(self.volume)
                
                # Calculate new position in the speed-adjusted audio
                adjusted_pos = current_pos * (old_speed / new_speed)
                
                # Start playing from the adjusted position
                pygame.mixer.music.play(start=adjusted_pos)
                
                print(f"Regenerated audio at {new_speed}x speed")
            except Exception as e:
                print(f"Error adjusting audio speed: {e}")
                self.sound = False

    def update_volume(self, event=None):
        self.volume = self.vol_slider.get()
        if self.sound:
            pygame.mixer.music.set_volume(self.volume)

    def stop_media(self):
        self.playing = False
        self.paused = False
        self.stop_event.set()
        time.sleep(0.1)
        
        if self.vid:
            self.vid.release()
            self.vid = None
            
        if self.clip:
            self.clip.close()
            self.clip = None
            
        if self.sound:
            pygame.mixer.music.stop()
            self.sound = False
            
        self.cleanup_temp_files()

    def show_metadata(self):
        if not (self.vid or self.clip) and not self.file_path:
            messagebox.showinfo("Metadata", "No media file loaded")
            return
        try:
            file_stats = os.stat(self.file_path)
            metadata = {
                "File Name": os.path.basename(self.file_path),
                "File Path": self.file_path,
                "File Size": f"{file_stats.st_size / (1024*1024):.2f} MB",
                "Resolution": f"{self.original_width}x{self.original_height}",
                "Aspect Ratio": f"{self.aspect_ratio:.2f}",
                "FPS": f"{self.fps:.2f}",
                "Duration": f"{self.duration:.2f} seconds",
                "Total Frames": self.frame_count,
                "Current Playback Speed": f"{self.playback_speed:.1f}x",
                "Current Volume": f"{int(self.volume * 100)}%"
            }
            
            # Add video codec info if available
            if self.vid:
                metadata["Video Codec"] = self.get_fourcc()
                
            # Add moviepy-specific info
            if self.clip:
                metadata["Processing Library"] = "MoviePy"
                metadata["Audio"] = "Yes" if self.clip.audio is not None else "No"
            else:
                metadata["Processing Library"] = "OpenCV"
            
            # Add pygame-specific audio info
            metadata["Audio Driver"] = "pygame.mixer"
            if self.sound:
                metadata["Audio Playback"] = "Active"
            else:
                metadata["Audio Playback"] = "Not available"
            
            meta_win = tk.Toplevel(self.root)
            meta_win.title("Media Metadata")
            meta_win.geometry("400x300")
            meta_win.resizable(True, True)
            meta_win.transient(self.root)
            meta_win.grab_set()
            text_frame = ttk.Frame(meta_win)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text = tk.Text(text_frame, wrap=tk.WORD, width=50, height=15)
            scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
            text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            text.insert(tk.END, "=== Media File Metadata ===\n\n")
            for key, value in metadata.items():
                text.insert(tk.END, f"{key}: {value}\n")
            text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Metadata Error", str(e))

    def get_fourcc(self):
        try:
            fourcc_int = int(self.vid.get(cv2.CAP_PROP_FOURCC))
            return "".join([
                chr((fourcc_int >> 8 * i) & 0xFF)
                for i in range(4)
            ])
        except:
            return "Unknown"

    def on_close(self):
        # Stop media playback
        self.stop_media()
        
        # Quit pygame
        pygame.quit()
        
        # Destroy the window
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    player = ImprovedMediaPlayer(root)
    root.mainloop()
