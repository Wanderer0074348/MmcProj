import sys
import cv2
import os
from datetime import timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
                            QSlider, QVBoxLayout, QHBoxLayout, QFileDialog, QComboBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Setup UI
        self.setWindowTitle("PyQt5 Video Player")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        main_layout.addWidget(self.video_label)
        
        # Timestamp label
        self.timestamp_label = QLabel("00:00:00 / 00:00:00")
        self.timestamp_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.timestamp_label)
        
        # Seek slider
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setMinimum(0)
        self.seek_slider.setMaximum(100)
        self.seek_slider.valueChanged.connect(self.seek_video)
        main_layout.addWidget(self.seek_slider)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Play/Pause button
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.play_button)
        
        # Load button
        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        controls_layout.addWidget(self.load_button)
        
        # Speed selector
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "1.5x"])
        self.speed_combo.setCurrentIndex(1)  # Default to 1.0x
        self.speed_combo.currentIndexChanged.connect(self.change_speed)
        controls_layout.addWidget(self.speed_combo)
        
        main_layout.addLayout(controls_layout)
        
        # Video properties
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.duration = 0
        self.playback_speed = 1.0
        
        # Speed mapping
        self.speed_map = {0: 0.5, 1: 1.0, 2: 1.5}
        
        # Show initial state
        self.show_blank_frame()
        
    def show_blank_frame(self):
        # Display a blank frame
        blank_image = QImage(640, 480, QImage.Format_RGB888)
        blank_image.fill(Qt.black)
        self.video_label.setPixmap(QPixmap.fromImage(blank_image))
        
    def load_video(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4)")
        if filename:
            # Release previous capture if any
            if self.cap is not None:
                self.cap.release()
                
            # Open new video file
            self.cap = cv2.VideoCapture(filename)
            
            if not self.cap.isOpened():
                print("Error opening video file")
                return
                
            # Get video properties
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.duration = self.total_frames / self.fps
            
            # Update UI
            self.seek_slider.setMaximum(self.total_frames - 1)
            self.current_frame = 0
            self.playing = False
            self.play_button.setText("Play")
            
            # Stop timer if running
            if self.timer.isActive():
                self.timer.stop()
                
            # Show first frame
            self.show_frame()
            
            # Update duration in timestamp label
            duration_str = str(timedelta(seconds=int(self.duration)))
            self.timestamp_label.setText(f"00:00:00 / {duration_str}")
            
    def show_frame(self):
        if self.cap is not None and self.cap.isOpened():
            # Set position
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            
            # Read frame
            ret, frame = self.cap.read()
            
            if ret:
                # Calculate timestamp
                current_time = self.current_frame / self.fps
                timestamp = str(timedelta(seconds=int(current_time)))
                duration_str = str(timedelta(seconds=int(self.duration)))
                
                # Add timestamp overlay
                cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           1, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Convert to RGB for Qt
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                
                # Convert to QImage
                bytes_per_line = ch * w
                qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                # Display the image
                self.video_label.setPixmap(QPixmap.fromImage(qt_image))
                
                # Update timestamp label
                self.timestamp_label.setText(f"{timestamp} / {duration_str}")
                
                # Update slider position without triggering valueChanged
                self.seek_slider.blockSignals(True)
                self.seek_slider.setValue(self.current_frame)
                self.seek_slider.blockSignals(False)
                
                return True
        return False
    
    def update_frame(self):
        if self.playing and self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            success = self.show_frame()
            
            if not success:
                self.toggle_play()  # Stop playback
        else:
            self.toggle_play()  # Stop at the end
    
    def toggle_play(self):
        if self.cap is None:
            return
            
        self.playing = not self.playing
        
        if self.playing:
            self.play_button.setText("Pause")
            # Calculate interval based on fps and playback speed
            interval = int(1000 / (self.fps * self.playback_speed))
            self.timer.start(interval)
        else:
            self.play_button.setText("Play")
            self.timer.stop()
    
    def seek_video(self, position):
        if self.cap is None:
            return
            
        self.current_frame = position
        self.show_frame()
    
    def change_speed(self, index):
        self.playback_speed = self.speed_map[index]
        
        # If playing, update the timer interval
        if self.playing:
            self.timer.stop()
            interval = int(1000 / (self.fps * self.playback_speed))
            self.timer.start(interval)
    
    def closeEvent(self, event):
        # Clean up resources
        if self.cap is not None:
            self.cap.release()
        event.accept()

if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())
