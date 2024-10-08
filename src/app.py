import sys
import re
from profile import Profile

import imageio.v3 as iio
import logging
from line_profiler import profile

import rawpy
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QScrollArea, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QWidget, QSizePolicy, QFileDialog
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QTimer, QSize

logger = logging.getLogger(__name__)

class ImageScrollApp(QMainWindow):


    image_list = []

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

        # Add a button to load files
        self.load_files_button = QPushButton("Load Files", self)
        self.load_files_button.clicked.connect(self.file_dialog)
        self.layout.addWidget(self.load_files_button)

        # Counter to keep track of dynamically created scroll areas
        self.scroll_area_counter = 0
        self.add_horizontal_scroll_area()


    def file_dialog(self):
        image_paths, type_filter = QFileDialog.getOpenFileNames(
            self,
            "Open Image",
            "/media/Images/2023/03_ErsterGeburtstag/",
            "Image Files (*.png *.jpg *.bmp *.CR2 *.CR3 *.DNG);;Raw Images (*.DNG)"
        )
        for image_path in image_paths:

            try:
                with rawpy.imread(image_path) as raw:
                    thumb = raw.extract_thumb()
                    if thumb.format == rawpy._rawpy.ThumbFormat.JPEG:
                        # thumb.data is already in JPEG format, save as-is
                        self.image_list.append(thumb.data)
                    elif thumb.format == rawpy._rawpy.ThumbFormat.BITMAP:
                        # thumb.data is an RGB numpy array, convert with imageio
                        self.image_list.append(iio.imread(thumb))
            except rawpy._rawpy.LibRawError as e:
                print(f'Error loading file: {image_path}')
        pass

    def add_horizontal_scroll_area(self):
        # Create a horizontal scroll area
        horizontal_scroll_area = QScrollArea(self)
        horizontal_scroll_area.setWidgetResizable(True)

        # Always show the horizontal scrollbar
        horizontal_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        horizontal_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Add the horizontal scroll area to the vertical scroll layout
        self.scroll_layout.addWidget(horizontal_scroll_area)

        # Create a container widget and layout for the images inside the scroll area
        image_container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        container_layout.setSpacing(10)  # spacing between images
        image_container.setLayout(container_layout)

        # Set the container to the scroll area
        horizontal_scroll_area.setWidget(image_container)

        # Add the same image x times to the horizontal scroll area
        for img in self.image_list:
            image_label = QLabel(image_container)
            image_label.setScaledContents(True)  # Allow scaling if needed

            # Todo: This does not work properly. There is still some vertical margain on each image which causes it
            #  to scroll vertically.
            #pixmap = QPixmap('../ui/resources/test_pic.jpeg') # Load the image
            qimg = QImage()
            qimg.loadFromData(img)
            pixmap = QPixmap(qimg) # Load the image

            image_label.setPixmap(pixmap)

            # Set the image label in the layout
            container_layout.addWidget(image_label)


        # Use QTimer to ensure the layout has been applied before adjusting image size
        QTimer.singleShot(100, lambda: self.adjust_image_sizes(horizontal_scroll_area))

        # Increment counter for future references
        self.scroll_area_counter += 1

    @profile
    def adjust_image_sizes(self, horizontal_scroll_area):
        # Get the height of the vertical scroll area
        total_height = self.vertical_scroll_area.viewport().height()  # Use viewport for accurate height

        # Calculate 1/3 of the total height
        minimal_image_height = total_height // 3 # Integer division for 1/3
        print(f'minimal height: {minimal_image_height}')

        # set lower limit for scroll area height
        horizontal_scroll_area.setFixedHeight(minimal_image_height)

        # Get the image container inside the horizontal scroll area
        image_container = horizontal_scroll_area.widget()
        layout = image_container.layout()

        # Set the minimum height for each image in the horizontal scroll area
        for i in range(layout.count()):
            image_label = layout.itemAt(i).widget()
            if isinstance(image_label, QLabel):
                image_label.setFixedHeight(minimal_image_height)
                print(image_label.size())

                image_label.setPixmap(
                    image_label.pixmap().scaledToHeight(image_label.height(),
                                                Qt.TransformationMode.SmoothTransformation)
                )

    def resizeEvent(self, event):
        """Adjust image heights when the window is resized."""
        print(f'count {self.scroll_layout.count()}')
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