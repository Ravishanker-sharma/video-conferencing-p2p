
class UserProfile:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserProfile, cls).__new__(cls)
            cls._instance.name = ""
            cls._instance.initials = ""
            cls._instance.captions_text = """This is a simulated caption.
It helps to demonstrate the feature.
When you speak, words appear here.
Post-Quantum cryptography keeps it safe.
Video conferencing is the future.
Team Connect is awesome.
"""
            cls._instance.mom_text = """Meeting Minutes
Date: Today
Topic: Project Sync

Action Items:
1. Review code changes.
2. Deploy to staging.
3. Update documentation.
"""
        return cls._instance

    def set_name(self, name):
        self.name = name
        self.initials = "".join([part[0] for part in name.split()[:2]]).upper() if name else "??"

    def get_initials(self):
        return self.initials

    def update_settings(self, captions, mom):
        self.captions_text = captions
        self.mom_text = mom
