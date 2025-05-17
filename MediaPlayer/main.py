import cv2
import time
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyglet
import sys

class ImprovedMediaPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenCV Media Player Pro")
        
        # Configure pyglet audio
        pyglet.options['audio'] = ('openal', 'directsound', 'xaudio2', 'pulse', 'silent')
        
        # Video components
        self.vid = None
        self.player = None
        self.source = None
        self.playing = False
        self.paused = False
        self.playback_speed = 1.0
        self.volume = 1.0
        self.frame = None
        self.stop_event = threading.Event()
        self.file_path = None
        self.current_position = 0
        
        # Get screen dimensions
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Check FFmpeg availability
        self.check_ffmpeg()
        
        # GUI setup
        self.create_widgets()
        
        # Print audio driver info
        print(f"Using audio driver: {pyglet.media.get_audio_driver().__class__.__name__}")
        
        # Set up pyglet clock
        pyglet.clock.schedule_interval(self.update_pyglet, 1/60.0)
        
        # Bind window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Configure>", self.on_resize)
        
        # Start pyglet event loop in a separate thread
        threading.Thread(target=self.pyglet_thread, daemon=True).start()

    def check_ffmpeg(self):
        """Verify FFmpeg is available and print status"""
        try:
            # Try to import the FFmpeg loader from pyglet
            from pyglet.media.codecs import ffmpeg
            if ffmpeg.available:
                print("FFmpeg is available")
                return True
            else:
                print("FFmpeg module found but not available")
                return False
        except ImportError:
            print("FFmpeg module not found")
            return False

    def ensure_ffmpeg(self):
        """Attempt to ensure FFmpeg is available"""
        try:
            from pyglet.media.codecs import ffmpeg
            if ffmpeg.available:
                return True
                
            # If FFmpeg is not available, inform the user
            if messagebox.askyesno("FFmpeg Required", 
                                  "FFmpeg is required to play most media formats. Would you like to see installation instructions?"):
                self.show_ffmpeg_instructions()
            return False
        except ImportError:
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
                      "4. Restart the application",
            "Darwin": "1. Install Homebrew if not already installed:\n   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n"
                     "2. Install FFmpeg:\n   brew install ffmpeg\n"
                     "3. Restart the application",
            "Linux": "1. Install FFmpeg using your package manager:\n"
                    "   Ubuntu/Debian: sudo apt-get install ffmpeg\n"
                    "   Fedora: sudo dnf install ffmpeg\n"
                    "   Arch: sudo pacman -S ffmpeg\n"
                    "2. Restart the application"
        }
        
        platform_name = sys.platform
        if platform_name.startswith("win"):
            platform_name = "Windows"
        elif platform_name.startswith("darwin"):
            platform_name = "Darwin"
        else:
            platform_name = "Linux"
            
        instruction_text = instructions.get(platform_name, "Please install FFmpeg for your platform")
        
        # Create a window with instructions
        instr_win = tk.Toplevel(self.root)
        instr_win.title("FFmpeg Installation Instructions")
        instr_win.geometry("500x300")
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
        self.root.config(menu=menubar)

    def update_pyglet(self, dt):
        """Update function called by pyglet's clock"""
        # This keeps the pyglet event loop running
        # which is necessary for audio playback
        pass

    def pyglet_thread(self):
        """Run pyglet event loop in a separate thread"""
        while True:
            # Process pyglet events
            pyglet.clock.tick()
            try:
                pyglet.app.platform_event_loop.step(0)
            except:
                pass  # Some platforms might not have this
            time.sleep(0.01)  # Small sleep to reduce CPU usage

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
            # Initialize video capture with OpenCV
            self.vid = cv2.VideoCapture(file_path)
            if not self.vid.isOpened():
                raise ValueError("Error opening video file")
            
            # Initialize audio player with pyglet
            try:
                # Try to load the media with explicit decoder hint
                self.source = None
                
                # First try with FFmpeg if available
                try:
                    self.source = pyglet.media.load(file_path, streaming=True)
                except Exception as e:
                    print(f"Primary decoder failed: {e}")
                    
                    # If that fails, try alternative loading methods
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in ['.mp4', '.avi', '.mov', '.mkv']:
                        # For video files, we can continue with just video (no audio)
                        print("Continuing with video-only playback")
                        self.source = None
                    elif file_ext in ['.mp3', '.wav']:
                        # For audio files, try alternative loading methods
                        try:
                            # Try with explicit decoder hint
                            from pyglet.media.codecs import MediaDecoder
                            decoder = MediaDecoder.get_decoders()[0]
                            self.source = decoder.decode(file_path)
                        except:
                            print("All audio loading methods failed")
                
                # Create a player and queue the source if available
                if self.source:
                    self.player = pyglet.media.Player()
                    self.player.queue(self.source)
                    
                    # Set initial playback properties
                    self.player.volume = self.volume
                    
                    # Set pitch if available (for speed control)
                    if hasattr(self.player, 'pitch'):
                        self.player.pitch = self.playback_speed
                else:
                    print("No audio will be played for this file")
                    self.player = None
                    
            except Exception as audio_error:
                print(f"Audio initialization error: {audio_error}")
                self.player = None
                self.source = None
            
            # Get video properties from OpenCV
            self.original_width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.original_height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.aspect_ratio = self.original_width / self.original_height
            self.fps = self.vid.get(cv2.CAP_PROP_FPS)
            self.frame_count = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))
            self.duration = self.frame_count / self.fps if self.fps > 0 else 0

            # Reset position
            self.current_position = 0
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not initialize media: {str(e)}")
            return False
            
        return True

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
        if not self.vid:
            return
            
        self.playing = True
        self.paused = False
        self.play_btn.config(text="⏸")
        self.stop_event.clear()
        
        # Start audio playback with pyglet
        if self.player:
            self.player.play()
            
            # Apply playback speed if pitch attribute is available
            if hasattr(self.player, 'pitch'):
                self.player.pitch = self.playback_speed
        
        def video_thread():
            while self.playing and not self.stop_event.is_set():
                if self.paused:
                    time.sleep(0.1)  # Reduce CPU usage while paused
                    continue
                    
                start_time = time.time()
                
                # Get video frame
                ret, frame = self.vid.read()
                if not ret:
                    break
                
                # Update current position
                self.current_position = self.vid.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                
                # Resize frame while maintaining aspect ratio and scale
                current_width = self.canvas.winfo_width()
                current_height = self.canvas.winfo_height()
                if current_width > 0 and current_height > 0:
                    frame = self.resize_frame(frame, current_width, current_height)
                self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Update display in main thread
                self.root.after(0, self.update_display)
                
                # Speed control
                base_delay = 1/self.fps if self.fps > 0 else 0.04
                delay = (base_delay / self.playback_speed) - (time.time() - start_time)
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
        if self.player:
            self.player.pause()
            self.player.seek(0)

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
        if not self.vid:
            return
        if self.playing and not self.paused:
            # Pause playback
            self.paused = True
            self.play_btn.config(text="▶")
            if self.player:
                self.player.pause()
        elif self.playing and self.paused:
            # Resume playback
            self.paused = False
            self.play_btn.config(text="⏸")
            if self.player:
                self.player.play()
        else:
            # Start playback
            self.play_media()

    def update_speed(self, event=None):
        new_speed = self.speed_slider.get()
        
        # Only update if speed actually changed
        if abs(new_speed - self.playback_speed) < 0.01:
            return
            
        self.playback_speed = new_speed
        self.speed_label.config(text=f"{new_speed:.1f}x")
        
        # For audio, we need to restart playback at the current position
        if self.player and self.source and self.playing:
            try:
                # Remember current state and position
                current_time = self.current_position
                was_paused = self.paused
                
                # Create a new player with the same source
                old_player = self.player
                self.player = pyglet.media.Player()
                self.player.queue(self.source)
                
                # Set volume
                self.player.volume = self.volume
                
                # Set pitch if available
                if hasattr(self.player, 'pitch'):
                    self.player.pitch = new_speed
                
                # Seek to current position
                if current_time > 0:
                    self.player.seek(current_time)
                
                # Start playing if not paused
                if not was_paused:
                    self.player.play()
                
                # Clean up old player
                old_player.pause()
                old_player.delete()
                
            except Exception as e:
                print(f"Speed change error: {e}")

    def update_volume(self, event=None):
        self.volume = self.vol_slider.get()
        if self.player:
            self.player.volume = self.volume

    def stop_media(self):
        self.playing = False
        self.paused = False
        self.stop_event.set()
        time.sleep(0.1)
        
        if self.vid:
            self.vid.release()
            self.vid = None
            
        if self.player:
            self.player.pause()
            self.player.delete()
            self.player = None
            
        self.source = None

    def show_metadata(self):
        if not self.vid or not self.file_path:
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
                "Video Codec": self.get_fourcc(),
                "Current Playback Speed": f"{self.playback_speed:.1f}x",
                "Current Volume": f"{int(self.volume * 100)}%"
            }
            
            # Add pyglet-specific audio info if available
            if self.source and hasattr(self.source, 'audio_format') and self.source.audio_format:
                audio_format = self.source.audio_format
                metadata.update({
                    "Audio Channels": audio_format.channels,
                    "Sample Rate": f"{audio_format.sample_rate} Hz",
                    "Sample Size": f"{audio_format.sample_size} bits"
                })
            
            # Add audio driver info
            metadata["Audio Driver"] = pyglet.media.get_audio_driver().__class__.__name__
            
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
        # Unschedule all pyglet events
        pyglet.clock.unschedule(self.update_pyglet)
        
        # Stop media playback
        self.stop_media()
        
        # Destroy the window
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    player = ImprovedMediaPlayer(root)
    root.mainloop()
