import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QScrollArea, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QWidget, QSizePolicy
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer


class ImageScrollApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle("Dynamic Scroll Areas with Images")
        self.setGeometry(100, 100, 800, 600)

        # Create the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create a scroll area that will contain horizontal scroll areas
        self.vertical_scroll_area = QScrollArea(self)
        self.vertical_scroll_area.setWidgetResizable(True)

        # Always show the vertical scrollbar
        self.vertical_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.scroll_content = QWidget()  # Container for the vertical scroll area
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        self.scroll_content.setLayout(self.scroll_layout)
        self.vertical_scroll_area.setWidget(self.scroll_content)

        # Add the vertical scroll area to the main layout
        self.layout.addWidget(self.vertical_scroll_area)

        # Add a button to spawn new horizontal scroll areas
        self.add_scroll_button = QPushButton("Add Horizontal Scroll Area", self)
        self.add_scroll_button.clicked.connect(self.add_horizontal_scroll_area)
        self.layout.addWidget(self.add_scroll_button)

        # Counter to keep track of dynamically created scroll areas
        self.scroll_area_counter = 0

    def add_horizontal_scroll_area(self):
        # Create a horizontal scroll area
        horizontal_scroll_area = QScrollArea(self)
        horizontal_scroll_area.setWidgetResizable(True)

        # Always show the horizontal scrollbar
        horizontal_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        horizontal_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Create a container widget and layout for the images inside the scroll area
        image_container = QWidget()
        image_layout = QHBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        image_layout.setSpacing(10)  # Remove spacing between images

        # Add the same image 5 times to the horizontal scroll area
        for _ in range(15):
            image_label = QLabel(self)
            image_label.setScaledContents(True)  # Allow scaling if needed

            # Todo: This does not work properly. There is still some vertical margain on each image which causes it
            #  to scroll vertically.
            pixmap = QPixmap('../ui/resources/test_pic.jpeg').scaled(image_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)  # Load and scale the image
            image_label.setPixmap(pixmap)



            # Set the image label in the layout
            image_layout.addWidget(image_label)

        # Set the container to the scroll area
        horizontal_scroll_area.setWidget(image_container)

        # Add the horizontal scroll area to the vertical scroll layout
        self.scroll_layout.addWidget(horizontal_scroll_area)

        # Use QTimer to ensure the layout has been applied before adjusting image size
        QTimer.singleShot(0, lambda: self.adjust_image_sizes(horizontal_scroll_area))

        # Increment counter for future references
        self.scroll_area_counter += 1

    def adjust_image_sizes(self, horizontal_scroll_area):
        # Get the height of the vertical scroll area
        total_height = self.vertical_scroll_area.viewport().height()  # Use viewport for accurate height

        # Calculate 1/3 of the total height
        minimal_image_height = total_height // 3  # Integer division for 1/3

        horizontal_scroll_area.setMinimumHeight(minimal_image_height)
        # Get the image container inside the horizontal scroll area
        image_container = horizontal_scroll_area.widget()
        layout = image_container.layout()

        # Set the minimum height for each image in the horizontal scroll area
        for i in range(layout.count()):
            image_label = layout.itemAt(i).widget()
            if isinstance(image_label, QLabel):
                image_label.setMinimumHeight(minimal_image_height)

    def resizeEvent(self, event):
        """Adjust image heights when the window is resized."""
        for i in range(self.scroll_layout.count()):
            scroll_area = self.scroll_layout.itemAt(i).widget()
            if isinstance(scroll_area, QScrollArea):
                self.adjust_image_sizes(scroll_area)

        super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageScrollApp()
    window.show()
    sys.exit(app.exec())