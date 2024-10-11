import sys

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

    thumbnail_lists = [None,]

    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle("Dynamic Scroll Areas with Images")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowState(Qt.WindowState.WindowMaximized)

        # Create the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create a scroll area that will contain horizontal scroll areas
        self.vertical_scroll_area = QScrollArea(self)
        self.vertical_scroll_area.setWidgetResizable(True)
        self.vertical_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Container for the vertical scroll area
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.vertical_scroll_area.setWidget(self.scroll_content)

        # Add the vertical scroll area to the main layout
        self.layout.addWidget(self.vertical_scroll_area)

        # Add a button to spawn new horizontal scroll areas
        self.add_scroll_button = QPushButton("Add Horizontal Scroll Area", self)

        # Todo: https://stackoverflow.com/questions/940555/pyqt-sending-parameter-to-slot-when-connecting-to-a-signal
        self.add_scroll_button.clicked.connect(
            lambda thumbnails=thumbnail_lists: self.add_horizontal_scroll_area(thumbnails)
        )
        self.layout.addWidget(self.add_scroll_button)

        # Add a button to load files
        self.load_files_button = QPushButton("Load Files", self)
        self.load_files_button.clicked.connect(self.launch_file_dialog)
        self.layout.addWidget(self.load_files_button)

        # Counter to keep track of dynamically created scroll areas
        self.scroll_area_counter = 0

        # auto populate
        self.launch_file_dialog()
        # Use QTimer to ensure the layout has been applied before adjusting image size
        QTimer.singleShot(100, lambda: self.add_horizontal_scroll_area(self.thumbnail_lists[0]))

    def launch_file_dialog(self):
        """
        Loads images from disk and add them as pixmaps to memory
        """
        #image_paths, type_filter = QFileDialog.getOpenFileNames(
        #    self,
        #    "Open Image",
        #    "/media/Images/2023/03_ErsterGeburtstag/",
        #    "Image Files (*.png *.jpg *.bmp *.CR2 *.CR3 *.DNG);;Raw Images (*.DNG)"
        #)
        image_paths = ['/media/Images/2023/03_ErsterGeburtstag/IMG_' + str(i) + '.CR3' for i in range(2660, 2671)]
        images_to_add = []

        for image_path in image_paths:

            try:
                with rawpy.imread(image_path) as raw:
                    thumb = raw.extract_thumb()
                    if thumb.format == rawpy._rawpy.ThumbFormat.JPEG:
                        # thumb.data is already in JPEG format, save as-is
                        thumb = thumb.data
                    elif thumb.format == rawpy._rawpy.ThumbFormat.BITMAP:
                        # thumb.data is an RGB numpy array, convert with imageio
                        thumb = iio.imread(thumb)
            except rawpy._rawpy.LibRawError as e:
                logger.error(f'Error loading file: {image_path}', e)

            qimg = QImage()
            qimg.loadFromData(thumb)

            images_to_add.append(qimg)

            # pre-downscale to 1080p so that subsequent scaling is faster
            #self.pixmap_list.append(
            #    QPixmap(qimg)
            #    .scaledToHeight(1080, Qt.TransformationMode.FastTransformation)
            #)
        if len(images_to_add) > 0:
            self.thumbnail_lists.insert(0, images_to_add)

    def add_horizontal_scroll_area(self, thumbnails):
        # Create a horizontal scroll area
        horizontal_scroll_area = CullingGroupArea(self)
        self.scroll_layout.addWidget(horizontal_scroll_area)

        # Add the same image x times to the horizontal scroll area
        for thumb in thumbnails:
            image_label = Thumbnail(horizontal_scroll_area)
            image_label.setScaledContents(True)  # Allow scaling if needed
            image_label.setPixmap(
                QPixmap(thumb).scaledToHeight(1080, Qt.TransformationMode.FastTransformation)
            )

            # Set the image label in the layout
            horizontal_scroll_area.add_thumbnail(image_label)

        # Use QTimer to ensure the layout has been applied before adjusting image size
        QTimer.singleShot(100, lambda: horizontal_scroll_area.adjust_thumbnail_size())

        # Increment counter for future references
        self.scroll_area_counter += 1

    def resizeEvent(self, event):
        """Adjust image heights when the window is resized."""
        for i in range(self.scroll_layout.count()):
            scroll_area = self.scroll_layout.itemAt(i).widget()
            if isinstance(scroll_area, QScrollArea):
                scroll_area.adjust_thumbnail_size()
        super().resizeEvent(event)

class Thumbnail(QLabel):

    def __init__(self, parent):
        self.parent_object = parent
        super().__init__(parent)
        self.setStyleSheet("""
                border: 5px white;      /* 5px thick border around the image */
                border-style: outset;       /* Ensures the image size doesn't change */
        """)
        self.selected = False

    def mousePressEvent(self, event):
        # Handle mouse click to select the label
        self.parent_object.clear_selection()
        self.set_selected(True)
        #self.parent_object.select_thumbnail()
        #super().mousePressEvent(event)


    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet("""
                    border: 5px yellow;      /* 5px thick border around the image */
                    border-style: outset;       /* Ensures the image size doesn't change */
            """)
        else:
            self.setStyleSheet("""
                    border: 5px white;      /* 5px thick border around the image */
                    border-style: outset;       /* Ensures the image size doesn't change */
            """)


class CullingGroupArea(QScrollArea):
    def __init__(self, parent):
        self.parent_object = parent
        super().__init__(parent)
        self.setWidgetResizable(True)

        # Always show the horizontal scrollbar
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container_widget = QWidget()
        self.layout = QHBoxLayout(container_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.layout.setSpacing(10)  # spacing between images
        self.setWidget(container_widget)

        self.thumb_list = []
        self.selected_index = -1
        self.select_label(self.selected_index)

    def add_thumbnail(self, thumb):
        self.layout.addWidget(thumb)
        self.thumb_list.append(thumb)

    @profile
    def adjust_thumbnail_size(self):

        # set height to 1/3 of the total height
        culling_group_area_height = self.parent().parent().height() // 3  # Integer division for 1/3
        self.setFixedHeight(culling_group_area_height)

        # Get the image container inside the horizontal scroll area
        image_container = self.widget()
        layout = image_container.layout()
        image_height = self.viewport().height()

        # Set the minimum height for each image in the horizontal scroll area
        for i in range(layout.count()):
            image_label = layout.itemAt(i).widget()
            if isinstance(image_label, QLabel):
                image_label.setFixedHeight(image_height)
                image_label.setPixmap(
                    image_label.pixmap().scaledToHeight(
                        image_label.height(),
                        Qt.TransformationMode.SmoothTransformation
                    )
                )

    def split_culling_group(self):
        self.parent_object.add_horizontal_scroll_area(self.topLevelWidget().pixmap[self.selected_index+1:])
        pass

    def clear_selection(self):
        for thumb in self.thumb_list:
            thumb.set_selected(False)



    def select_label(self, index):
        if index < 0 or index >= len(self.thumb_list):
            return
        for thumb in self.thumb_list:
            thumb.deselect()
        self.thumb_list[index].select()
        self.ensureWidgetVisible(self.thumb_list[index])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Right:
            self.selected_index = (self.selected_index + 1) % len(self.thumb_list)
            self.select_label(self.selected_index)
        elif event.key() == Qt.Key.Key_Left:
            self.selected_index = (self.selected_index - 1) % len(self.thumb_list)
            self.select_label(self.selected_index)
        elif event.key() == Qt.Key.Key_S:
            self.split_culling_group()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Handle mouse click to select the label
        for i, label in enumerate(self.thumb_list):
            pos = event.position()
            # Todo: implement this nicer. Position is float but contains() expects int
            if label.geometry().contains(pos.x(), pos.y(), False):
                self.selected_index = i
                self.select_label(self.selected_index)
                break
        super().mousePressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageScrollApp()
    window.show()
    sys.exit(app.exec())