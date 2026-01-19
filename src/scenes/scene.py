class Scene:
    def __init__(self, manager):
        self.manager = manager
        self.display_surface = manager.render_surface

    def handle_events(self, events):
        pass

    def on_enter(self):
        pass

    def update(self, dt):
        pass

    def draw(self):
        pass
