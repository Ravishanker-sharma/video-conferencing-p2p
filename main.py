import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from login_widget import LoginWidget
from selection_widget import ModeSelectionWidget
from ui import VideoCallWidget

class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print("MainAppWindow.__init__ start")
        self.setWindowTitle("Team Connect")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central Stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Initialize Widgets
        print("Initializing LoginWidget...")
        self.init_login()
        
        print("Initializing ModeSelectionWidget...")
        self.selection_widget = ModeSelectionWidget()
        self.selection_widget.mode_selected.connect(self.go_to_video)
        
        self.stack.addWidget(self.selection_widget) 
        print("Widgets initialized.") 

        # Global Application Styling (Dark Theme)
        # Replaced custom font with system default to avoid warnings
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
        """)

    def init_login(self):
        self.login_widget = LoginWidget()
        self.login_widget.login_successful.connect(self.go_to_selection)
        self.stack.addWidget(self.login_widget) 
        self.stack.setCurrentWidget(self.login_widget)

    def go_to_selection(self):
        self.stack.setCurrentWidget(self.selection_widget)

    def go_to_video(self, mode):
        self.video_widget = VideoCallWidget(mode=mode)
        self.video_widget.call_ended.connect(self.go_back_to_selection)
        
        self.stack.addWidget(self.video_widget) 
        self.stack.setCurrentWidget(self.video_widget)

    def go_back_to_selection(self):
        current_widget = self.stack.currentWidget()
        if isinstance(current_widget, VideoCallWidget):
            current_widget.cleanup()
            self.stack.removeWidget(current_widget)
            current_widget.deleteLater()
            
        self.stack.setCurrentWidget(self.selection_widget)

    def closeEvent(self, event):
        current = self.stack.currentWidget()
        if isinstance(current, VideoCallWidget):
            current.cleanup()
        event.accept()

def main():
    print("Starting application...")
    app = QApplication(sys.argv)
    
    print("Creating window...")
    window = MainAppWindow()
    window.show()
    
    print("Executing event loop...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
