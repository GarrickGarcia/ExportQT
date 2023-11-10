from PyQt6.QtWidgets import QApplication, QMainWindow, QLineEdit, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QProgressBar, QCheckBox, QFileDialog, QMessageBox, QApplication
from PyQt6.QtGui import QIcon
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd
import fiona
import os
import sys
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Get the path to the data directory
        if getattr(sys, 'frozen', False):
            datadir = os.path.join(sys._MEIPASS, 'Icon')
        else:
            datadir = 'Icon'

        self.setWindowIcon(QIcon(os.path.join(datadir, 'download_icon.png')))
        self.setWindowTitle('Export Layer')
        self.resize(700, 420)
        description_label = QLabel('This tool allows you to export a layer from ArcGIS Online or Enterprise Portal to a local shapefile. Please enter your ArcGIS credentials, the URL of the service, an optional SQL query, the name for the output, and the output folder.')
        description_label.setWordWrap(True)
        self.portal_url_input = QLineEdit()
        self.portal_url_input.setPlaceholderText("Leave blank if using ArcGIS Online. Example: https://maps.myorg.org/portal/")
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("URL of specific layer. Example: https://services7.arcgis.com/xxx/arcgis/rest/services/Name/FeatureServer/0 ")
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Optional to filter the output. Example: OBJECTID = 10 or TYPE = 'Water'")
        self.last_created_checkbox = QCheckBox('Last Created Feature Only')
        self.output_name_input = QLineEdit()
        self.output_name_input.setPlaceholderText("Enter the name of the output files without the .shp extension")
        self.folder_input = QLineEdit()

        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.browse_folder)

        self.clear_button = QPushButton('Clear')
        self.clear_button.clicked.connect(self.clear_inputs)

        self.run_button = QPushButton('Run')
        self.run_button.clicked.connect(self.run_query)

        self.progress_bar = QProgressBar()
        required_label = QLabel("* designates required input")

        layout = QVBoxLayout()
        layout.addWidget(description_label)
        layout.addLayout(self.create_input_layout('Portal URL:', self.portal_url_input))
        layout.addLayout(self.create_input_layout('*Username:', self.username_input))
        layout.addLayout(self.create_input_layout('*Password:', self.password_input))
        layout.addLayout(self.create_input_layout('*Service URL:', self.url_input))
        layout.addLayout(self.create_input_layout('SQL Query:', self.query_input))
        layout.addWidget(self.last_created_checkbox)
        layout.addLayout(self.create_input_layout('*Output Name:', self.output_name_input))
        folder_layout = self.create_input_layout('*Folder:', self.folder_input)
        folder_layout.addWidget(self.browse_button)
        layout.addLayout(folder_layout)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.run_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(required_label)

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
        try:
            username = self.username_input.text()
            password = self.password_input.text()
            url = self.url_input.text()
            folder = self.folder_input.text()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_base_name = self.output_name_input.text()
            out_name = f'{output_base_name}_{timestamp}'

            # Update the progress bar
            self.progress_bar.setValue(25)

            portal_url = self.portal_url_input.text()
            gis_url = portal_url if portal_url else "https://www.arcgis.com"  # Use the portal URL if it's filled in, otherwise use the ArcGIS Online URL
            gis = GIS(gis_url, username, password)
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
                objectid_field = 'OBJECTID' if 'OBJECTID' in sedf.columns else 'objectid'
                max_objectid = sedf[objectid_field].max()
                sedf = sedf[sedf[objectid_field] == max_objectid]

            # Update the progress bar
            self.progress_bar.setValue(75)

            # Export the sedf to a shapefile
            shapefile_path = os.path.join(folder, out_name + '.shp')
            sedf.spatial.to_featureclass(location=shapefile_path)

            # Update the progress bar
            self.progress_bar.setValue(100)
        except Exception as e:
                QMessageBox.critical(self, "Error", "An error occurred while running the query.\n" + str(e))

def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()