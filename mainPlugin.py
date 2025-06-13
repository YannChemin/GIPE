import os
from qgis.PyQt.QtWidgets import QAction, QMenu
from qgis.PyQt.QtGui import QIcon

from .vi_processing_dialog import VIProcessing  # VI Processing dialog class
from .about_dialog import AboutDialog # About Dialog class

class GIPEPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.menu = '&GIPE'
        self.actions = []

    def initGui(self):
        # Create the action for your dialog
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')  # Use your icon
        self.action = QAction(QIcon(icon_path), "Open VI Processing", self.iface.mainWindow())
        self.action.triggered.connect(self.show_dialog)

        # Add to GIPE menu (creates menu if not present)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.actions.append(self.action)

        # Add About to GIPE menu 
        self.about_action = QAction("About...", self.iface.mainWindow())
        self.about_action.triggered.connect(self.show_about_dialog)
        self.iface.addPluginToMenu(self.menu, self.about_action)
        self.actions.append(self.about_action)

    def unload(self):
        # Remove the action and menu
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def show_dialog(self):
        dlg = VIProcessing(self.iface.mainWindow())
        dlg.exec_()

    def show_about_dialog(self):
        dlg = AboutDialog(self.iface.mainWindow())  # Ensures dialog is modal to QGIS main window[1]
        dlg.exec_()

