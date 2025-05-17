class VideoProperties:
    def __init__(self, width: int, height: int, fps: int):
        self.width = width
        self.height = height
        self.fps = fps

    def __str__(self):
        return f"VideoProperties(width={self.width}, height={self.height}, fps={self.fps})"