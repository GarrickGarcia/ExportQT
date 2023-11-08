from PyQt6.QtWidgets import QApplication, QMainWindow, QLineEdit, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QProgressBar, QCheckBox, QFileDialog
from PyQt6.QtGui import QIcon
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd
import fiona
import os
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('download_icon.png'))
        self.setWindowTitle('Export Layer')
        self.resize(500, 350)
        description_label = QLabel('This tool allows you to export a layer from ArcGIS Online to a local shapefile. Please enter your ArcGIS Online credentials, the URL of the service, an optional SQL query, and the output folder.')
        description_label.setWordWrap(True)
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.url_input = QLineEdit()
        self.query_input = QLineEdit()
        self.last_created_checkbox = QCheckBox('Last Created Feature Only')
        self.folder_input = QLineEdit()

        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.browse_folder)

        self.clear_button = QPushButton('Clear')
        self.clear_button.clicked.connect(self.clear_inputs)

        self.run_button = QPushButton('Run')
        self.run_button.clicked.connect(self.run_query)

        self.progress_bar = QProgressBar()  # Create a QProgressBar instance

        layout = QVBoxLayout()
        layout.addWidget(description_label)
        layout.addLayout(self.create_input_layout('AGOL Username:', self.username_input))
        layout.addLayout(self.create_input_layout('Password:', self.password_input))
        layout.addLayout(self.create_input_layout('Service URL:', self.url_input))
        layout.addLayout(self.create_input_layout('SQL Query:', self.query_input))
        layout.addWidget(self.last_created_checkbox)
        folder_layout = self.create_input_layout('Folder:', self.folder_input)
        folder_layout.addWidget(self.browse_button)  # Add the browse button to the folder layout
        layout.addLayout(folder_layout)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.run_button)
        layout.addWidget(self.progress_bar)  # Add the progress bar to the layout

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def create_input_layout(self, label_text, input_widget):
        label = QLabel(label_text)
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(input_widget)
        return layout

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.folder_input.setText(folder)

    def clear_inputs(self):
        self.username_input.clear()
        self.password_input.clear()
        self.url_input.clear()
        self.query_input.clear()
        self.folder_input.clear()
        self.progress_bar.setValue(0)

    def run_query(self):
        username = self.username_input.text()
        password = self.password_input.text()
        url = self.url_input.text()
        folder = self.folder_input.text()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_name = f'output_{timestamp}'

        # Update the progress bar
        self.progress_bar.setValue(25)

        gis = GIS("https://www.arcgis.com", username, password)
        feature_layer = FeatureLayer(url)
        sedf = pd.DataFrame.spatial.from_layer(feature_layer)

        # Update the progress bar
        self.progress_bar.setValue(50)

        # Perform the query on the SeDF
        query = self.query_input.text()
        if query:
            sedf = sedf.query(query)

        # If the checkbox is checked, filter the SeDF to only include the most recently created feature
        if self.last_created_checkbox.isChecked():
            max_objectid = sedf['OBJECTID'].max()
            sedf = sedf[sedf['OBJECTID'] == max_objectid]

        # Update the progress bar
        self.progress_bar.setValue(75)

        # Export the sedf to a shapefile
        shapefile_path = os.path.join(folder, out_name + '.shp')
        sedf.spatial.to_featureclass(location=shapefile_path)

        # Update the progress bar
        self.progress_bar.setValue(100)

def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()