"""Keep the Wayland/Wine game visible when background input restores it."""
def install():
    from module.config import cfg
    from module.game_and_screen.screen import Handle

    original = Handle.set_window_transparent

    def set_transparent(self, transparent=True):
        if cfg.win_input_type == 'background':
            transparent = False
        return original(self, transparent)

    Handle.set_window_transparent = set_transparent
