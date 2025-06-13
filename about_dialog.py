from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About GIPE")
        layout = QVBoxLayout()
        label = QLabel("GIPE Plugin\nVersion 1.0\n\nDeveloped by Yann\nContact: dr.yann.chemin@gmail.com")
        layout.addWidget(label)
        btn = QPushButton("Close")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)
        self.setLayout(layout)

