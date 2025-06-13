from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QCheckBox, QHBoxLayout
)
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsRasterShader,
    QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer,
    QgsProject,
    QgsRasterLayer
)
from qgis.gui import QgsMapLayerComboBox, QgsRasterBandComboBox
from qgis.core import QgsMapLayerProxyModel
import processing

class VIProcessing(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vegetation Indices Calculation")
        self.setMinimumSize(400, 200)  # Enforce minimum size

        layout = QVBoxLayout()

        # Raster layer selector
        self.layerCombo = QgsMapLayerComboBox()
        self.layerCombo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        layout.addWidget(QLabel("Select Raster Layer:"))
        layout.addWidget(self.layerCombo)

        # NIR band selector
        self.nirBandCombo = QgsRasterBandComboBox()
        layout.addWidget(QLabel("Select NIR Band:"))
        layout.addWidget(self.nirBandCombo)

        # Red band selector
        self.redBandCombo = QgsRasterBandComboBox()
        layout.addWidget(QLabel("Select Red Band:"))
        layout.addWidget(self.redBandCombo)

        # Blue band selector (for EVI)
        self.blueBandCombo = QgsRasterBandComboBox()
        layout.addWidget(QLabel("Select Blue Band (for EVI):"))
        layout.addWidget(self.blueBandCombo)

        # Index selection checkboxes
        self.ndviCheck = QCheckBox("NDVI")
        self.eviCheck = QCheckBox("EVI")
        indexLayout = QHBoxLayout()
        indexLayout.addWidget(self.ndviCheck)
        indexLayout.addWidget(self.eviCheck)
        layout.addLayout(indexLayout)
        
        # Output file selector
        self.outputButton = QPushButton("Select Output File")
        self.outputButton.clicked.connect(self.select_output_file)
        layout.addWidget(self.outputButton)
        self.output_path = None

        # Calculate button
        self.calcButton = QPushButton("Calculate")
        self.calcButton.clicked.connect(self.calculate_index)
        layout.addWidget(self.calcButton)


        # Checkbox: Close after completion
        self.close_after_cb = QCheckBox("Close dialog after completing the work")
        self.close_after_cb.setChecked(True)
        layout.addWidget(self.close_after_cb)

        # Explicit Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)

        # Update band combos when raster layer changes
        self.layerCombo.layerChanged.connect(self.updateBandCombos)

    def updateBandCombos(self, layer):
        self.nirBandCombo.setLayer(layer)
        self.redBandCombo.setLayer(layer)
        self.blueBandCombo.setLayer(layer)

    def select_output_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Select Output NDVI File", "", "GeoTIFF (*.tif)")
        if filename:
            self.output_path = filename

    def calculate_index(self):
        raster_layer = self.layerCombo.currentLayer()
        if not raster_layer:
            QMessageBox.warning(self, "No Raster Layer", "Please select a raster layer.")
            return

        nir_band = self.nirBandCombo.currentBand()
        red_band = self.redBandCombo.currentBand()
        blue_band = self.blueBandCombo.currentBand()
        if nir_band < 1 or red_band < 1:
            QMessageBox.warning(self, "Invalid Band Selection", "Please select valid bands for NIR and Red.")
            return

        if not self.output_path:
            QMessageBox.warning(self, "No Output File", "Please select an output file.")
            return

        # Determine which index to calculate
        if self.ndviCheck.isChecked() and not self.eviCheck.isChecked():
            # NDVI formula
            filename = 'ndvi'
            formula = '((A+B)==0)*-9999 + logical_and((A+B)!=0, (A+B)<10000)*((A-B)/(A+B))'
            params = {
                'INPUT_A': raster_layer.source(),
                'BAND_A': nir_band,
                'INPUT_B': raster_layer.source(),
                'BAND_B': red_band,
                'INPUT_C': None,
                'BAND_C': -1,
                'INPUT_D': None,
                'BAND_D': -1,
                'INPUT_E': None,
                'BAND_E': -1,
                'INPUT_F': None,
                'BAND_F': -1,
                'FORMULA': formula,
                'NO_DATA': 0,
                'RTYPE': 5,  # Float32
                'EXTRA': '',
                'OPTIONS': '',
                'OUTPUT': self.output_path
            }
        elif self.eviCheck.isChecked() and not self.ndviCheck.isChecked():
            # EVI formula: 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
            filename = 'evi'
            if blue_band < 1:
                QMessageBox.warning(self, "Invalid Band Selection", "Please select a valid band for Blue.")
                return
            formula = '(2.5*(A-B)/(A+6.0*B-7.5*C+1.0))*((A+6.0*B-7.5*C+1.0)!=0) + ((A+6.0*B-7.5*C+1.0)==0)*-9999'
            params = {
                'INPUT_A': raster_layer.source(),
                'BAND_A': nir_band,
                'INPUT_B': raster_layer.source(),
                'BAND_B': red_band,
                'INPUT_C': raster_layer.source(),
                'BAND_C': blue_band,
                'INPUT_D': None,
                'BAND_D': -1,
                'INPUT_E': None,
                'BAND_E': -1,
                'INPUT_F': None,
                'BAND_F': -1,
                'FORMULA': formula,
                'NO_DATA': 0,
                'RTYPE': 5,  # Float32
                'EXTRA': '',
                'OPTIONS': '',
                'OUTPUT': self.output_path
            }
        else:
            QMessageBox.warning(self, "Index Selection", "Please select exactly one index to calculate (NDVI or EVI).")
            return
        
        # Try to process, display and colour ramp it from 0 to 1
        try:
            vi_layer = QgsRasterLayer(self.output_path, filename)
            processing.run("gdal:rastercalculator", params)
            # Replace 'self.output_path' with your output file path variable
            if vi_layer.isValid():
                # Create color ramp shader
                fcn = QgsColorRampShader()
                fcn.setColorRampType(QgsColorRampShader.Interpolated)
                # Define color ramp: 0 (red), 0.5 (yellow), 1 (green)
                if filename == 'ndvi':
                    minval = 0.0
                    midval = 0.5
                    maxval = 1.0
                if filename == 'evi':
                    minval = -1.0
                    midval = 0.0
                    maxval = 1.0
                    
                lst = [
                    QgsColorRampShader.ColorRampItem(minval, QColor(203, 110, 15), 'Low'),     # Red
                    QgsColorRampShader.ColorRampItem(midval, QColor(255, 255, 0), 'Mid'),   # Yellow
                    QgsColorRampShader.ColorRampItem(maxval, QColor(26, 150, 65), 'High')     # Green
                ]
                fcn.setColorRampItemList(lst)
                shader = QgsRasterShader()
                shader.setRasterShaderFunction(fcn)
                renderer = QgsSingleBandPseudoColorRenderer(vi_layer.dataProvider(), 1, shader)
                renderer.setClassificationMin(minval)  # Force min
                renderer.setClassificationMax(maxval)  # Force max
                vi_layer.setRenderer(renderer)
                QgsProject.instance().addMapLayer(vi_layer)
            else:
                QMessageBox.warning(self, "Layer Error", "vegetation index raster could not be loaded.")

            if not self.close_after_cb.isChecked():
                QMessageBox.information(self, "Calculation Complete", "The vegetation index raster was created successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"vegetation index calculation failed:\n{e}")

        # Check if dialog should close after work
        if self.close_after_cb.isChecked():
            self.close()
# To use the dialog in QGIS Python Console:
dlg = VIProcessing()
dlg.exec_()

