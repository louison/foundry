class AutoPlaylist:
    def __init__(self):
        self.data = None
        
    def get_tracks(self):
        raise NotImplementedError(f"get_tracks not implemented")
