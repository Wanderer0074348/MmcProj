import sys
import vlc
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QSlider, QFileDialog, 
                            QLabel, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

class MediaPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Media Player")
        self.setGeometry(100, 100, 800, 600)
        
        # Create VLC instance and media player
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create video frame
        self.video_frame = QWidget()
        self.video_frame.setStyleSheet("background-color: black;")
        self.layout.addWidget(self.video_frame)
        
        # Set the video frame as the media player's window
        if sys.platform.startswith('linux'):  # for Linux using the X Server
            self.media_player.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32":  # for Windows
            self.media_player.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin":  # for MacOS
            self.media_player.set_nsobject(int(self.video_frame.winId()))
        
        # Create controls layout
        controls_layout = QHBoxLayout()
        
        # Create buttons
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.play_button)
        
        # Create time slider
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, 1000)
        self.time_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.time_slider)
        
        # Create volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls_layout.addWidget(self.volume_slider)
        
        # Create playback speed controls
        self.speed_label = QLabel("Speed: 1.0x")
        controls_layout.addWidget(self.speed_label)
        
        self.speed_up_button = QPushButton("+")
        self.speed_up_button.clicked.connect(self.increase_speed)
        self.speed_up_button.setMaximumWidth(30)
        controls_layout.addWidget(self.speed_up_button)
        
        self.speed_down_button = QPushButton("-")
        self.speed_down_button.clicked.connect(self.decrease_speed)
        self.speed_down_button.setMaximumWidth(30)
        controls_layout.addWidget(self.speed_down_button)
        
        # Create metadata button
        self.metadata_button = QPushButton("Metadata")
        self.metadata_button.clicked.connect(self.show_metadata)
        controls_layout.addWidget(self.metadata_button)
        
        # Add controls to main layout
        self.layout.addLayout(controls_layout)
        
        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        
        # Create actions
        open_action = file_menu.addAction("Open")
        open_action.triggered.connect(self.open_file)
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Create timer for updating the time slider
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)
        
        # Initialize variables
        self.current_file = None
        self.playback_speed = 1.0
        
        # Set initial volume
        self.media_player.audio_set_volume(50)
    
    def open_file(self):
        """Open a media file and start playback"""
        dialog = QFileDialog()
        file_path, _ = dialog.getOpenFileName(self, "Open Media File", "", 
                                             "Media Files (*.mp4 *.avi *.mov *.mkv *.mp3 *.wav)")
        
        if file_path:
            self.current_file = file_path
            self.play_media(file_path)
    
    def play_media(self, file_path):
        """Play the selected media file"""
        media = self.instance.media_new(file_path)
        self.media_player.set_media(media)
        self.media_player.play()
        self.play_button.setText("Pause")
        self.timer.start()
    
    def toggle_play(self):
        """Toggle between play and pause"""
        if self.media_player.is_playing():
            self.media_player.pause()
            self.play_button.setText("Play")
            self.timer.stop()
        else:
            if self.current_file:
                self.media_player.play()
                self.play_button.setText("Pause")
                self.timer.start()
    
    def update_ui(self):
        """Update the UI components"""
        # Update the time slider
        media_pos = int(self.media_player.get_position() * 1000)
        self.time_slider.setValue(media_pos)
        
        # Stop the player when the media has ended
        if not self.media_player.is_playing() and self.play_button.text() == "Pause":
            self.play_button.setText("Play")
            self.timer.stop()
    
    def set_position(self, position):
        """Set the position of the media player"""
        self.media_player.set_position(position / 1000.0)
    
    def set_volume(self, volume):
        """Set the volume of the media player"""
        self.media_player.audio_set_volume(volume)
    
    def increase_speed(self):
        """Increase playback speed"""
        self.playback_speed += 0.1
        self.media_player.set_rate(self.playback_speed)
        self.speed_label.setText(f"Speed: {self.playback_speed:.1f}x")
    
    def decrease_speed(self):
        """Decrease playback speed"""
        if self.playback_speed > 0.2:
            self.playback_speed -= 0.1
            self.media_player.set_rate(self.playback_speed)
            self.speed_label.setText(f"Speed: {self.playback_speed:.1f}x")
    
    def show_metadata(self):
        """Show metadata of the current media file"""
        if not self.current_file:
            QMessageBox.information(self, "Metadata", "No file loaded.")
            return
        
        metadata = self.extract_metadata(self.current_file)
        metadata_text = json.dumps(metadata, indent=4)
        
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Media Metadata")
        msg_box.setText(metadata_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
    
    def extract_metadata(self, file_path):
        """Extract metadata from the media file"""
        metadata = {}
        
        # Basic file information
        file_info = os.stat(file_path)
        metadata["file_name"] = os.path.basename(file_path)
        metadata["file_path"] = file_path
        metadata["file_size"] = f"{file_info.st_size / (1024 * 1024):.2f} MB"
        metadata["last_modified"] = str(file_info.st_mtime)
        
        # Media information from VLC
        media = self.instance.media_new(file_path)
        media.parse()
        
        metadata["duration"] = f"{media.get_duration() / 1000:.2f} seconds"
        
        # Get media tracks info
        tracks = []
        for i in range(media.tracks_get_number()):
            track = {}
            track_info = media.tracks_get()[i]
            
            if track_info.type == vlc.TrackType.audio:
                track["type"] = "audio"
                track["channels"] = track_info.audio.channels
                track["rate"] = f"{track_info.audio.rate} Hz"
            elif track_info.type == vlc.TrackType.video:
                track["type"] = "video"
                track["width"] = track_info.video.width
                track["height"] = track_info.video.height
                track["frame_rate"] = f"{track_info.video.frame_rate_num / track_info.video.frame_rate_den:.2f} fps"
            
            tracks.append(track)
        
        metadata["tracks"] = tracks
        
        return metadata

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MediaPlayer()
    player.show()
    sys.exit(app.exec_())
