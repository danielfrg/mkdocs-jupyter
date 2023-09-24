import os


class Settings:
    def __init__(self):
        this_dir = os.path.dirname(os.path.realpath(__file__))
        self.templates_dir = os.path.join(this_dir, "templates")


settings = Settings()
