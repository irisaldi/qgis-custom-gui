#!/usr/bin/env python3
"""
Collection of custom QGIS GUI.

Based on PyQGIS 3.28 and PyQt5.
"""

__author__ = 'Indraprasta Risaldi'
__copyright__ = 'Copyright (C) 2023 Indraprasta Risaldi'

__license__ = 'GNU General Public License v2.0'
__version__ = '1.0.1'
__maintainer__ = 'Indraprasta Risaldi'

from qgis.PyQt.QtCore import QDate, Qt
from qgis.PyQt.QtGui import QKeyEvent
from qgis.PyQt.QtWidgets import (QComboBox,
                                 QDialog,
                                 QDialogButtonBox,
                                 QLabel,
                                 QMessageBox,
                                 QPushButton,
                                 QVBoxLayout)

class LayerFieldFeatureWidget(QDialog):
    """
    Map QGIS project instances.

    This class combines three PyQGIS GUI classes QgsMapLayerComboBox, QgsFieldComboBox,
    and QgsCheckableComboBox. On its base call, it maps all QGIS project instances
    including all available fields and non-empty features. Filtering of layers and
    fields is made simple by passing two separated iterables listing the layer names
    and field names on first and second positional parameters, respectively. Moreover,
    filtration can also be conducted based on layer type or geometry type. Assigning
    geometry type and layer type filter together does not stack the effect.
    A filtration of features can then be applied by selecting the values of its
    attribute in the checkable box.

    Parameters
    ----------
    layer_matches : iterable(str), optional
        An iterable object that contains substrings of layer names.
        Make sure to assign those in keys/index in case dictionary is used.
    field_matches : iterable(str), optional
        An iterable object that contains strings of field names.
        Make sure to assign those in keys/index in case dictionary is used.
    title : str, optional
        This will be used as dialog title.
    layer_type : str, optional
        A substring of [QgsMapLayerType](https://qgis.org/pyqgis/3.28/core/QgsMapLayerType.html).
        Drop the "Layer" part, case insensitive. Use this for filtering layers based on its type.
    geometry_type : int, optional
        An integer identifier of [QgsWkbTypes.Type](https://qgis.org/pyqgis/3.28/core/QgsWkbTypes.html#qgis.core.QgsWkbTypes.Type)
        Use this for filtering layers based on its geometry type.

    Examples
    --------
    >>> layer_dict = {'a': None, 'b': None, 'c': None}
    >>> field_list = ['a', 'b', 'c']
    >>> dlg_name_filter = LayerFieldFeatureWidget(layer_dict, field_list, title="My Dictionary Matches")
    >>> dlg_type_filter = LayerFieldFeatureWidget(layer_type='Vector')
    >>> dlg_geom_type_filter = LayerFieldFeatureWidget(geometry_type=1)
    
    Methods
    -------
    accepted_field(self) -> [QgsField](https://qgis.org/pyqgis/3.28/core/QgsField.html#qgis.core.QgsField)
    accepted_layer(self) -> [QgsMapLayerType](https://qgis.org/pyqgis/3.28/core/QgsMapLayerType.html#qgis.core.QgsMapLayerType) 
    """
    def __init__(self, layer_matches = set(), field_matches = None, title = None, layer_type = set(), geometry_type = set()):
        super().__init__()

        # Class attributes.
        self.layer_option = "---- Please select a layer ----"
        self.layer_matches = layer_matches
        self.field_matches = field_matches
        self.title = title
        self.layer_type = layer_type
        self.geometry_type = geometry_type

        # Generating inverted model.
        self.inverted_layer_model = [inverted_layer for inverted_layer in self.generate_layer_model()]

        # Setting up dialog window.
        if self.title is not None:
            self.setWindowTitle(self.title)
        self.setFixedSize(300, 220)

        # Create combo box widget, where layer(s) will be displayed.
        self.layer_wdgt = QgsMapLayerComboBox()
        self.layer_wdgt.setAllowEmptyLayer(True, self.layer_option)
        self.layer_wdgt.setCurrentIndex(0)
        self.layer_wdgt.setShowCrs(True)
        self.layer_wdgt.setExceptedLayerList(self.inverted_layer_model)

        # Create field combo box, where the field(s) of the selected layer will be displayed.
        self.field_wdgt = QgsFieldComboBox()
        self.field_wdgt.setAllowEmptyFieldName(True)

        # Create feature list checkable combo box, where feature(s) of the selected field will be displayed.
        self.feature_wdgt = QgsCheckableComboBox()

        # Connecting signal emitted by `layer_wdgt` to the function `on_selected_layer`.
        self.layer_wdgt.layerChanged.connect(self.on_selected_layer)
        self.field_wdgt.fieldChanged.connect(self.on_selected_field)

        # Create selection buttons.
        self.selection_button = QDialogButtonBox(QDialogButtonBox.YesToAll | QDialogButtonBox.NoToAll)
        self.selection_button.setDisabled(True)

        # Create standard confirmation (or not) buttons.
        self.confirm_button = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.ok_button = self.confirm_button.buttons()[0]
        self.ok_button.setDisabled(True)

        # Connecting accept signal to a function, which store the accepted value(s) to variable(s).
        self.confirm_button.accepted.connect(self.accept)
        self.selection_button.accepted.connect(self.on_select_all)

        # Connecting reject signal to a function, which cleans all the elements in widgets.
        self.confirm_button.rejected.connect(self.reject)
        self.confirm_button.rejected.connect(self.on_reset_layer)
        self.selection_button.rejected.connect(self.on_deselect_all)

        # Create layout, which integrates all defined widgets into the dialog window.
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Layerauswahl:"))
        self.layout.addWidget(self.layer_wdgt)
        self.layout.addWidget(QLabel("Feldauswahl: [optional]"))
        self.layout.addWidget(self.field_wdgt)
        self.layout.addWidget(QLabel("Objektauswahl: [optional]"))
        self.layout.addWidget(self.feature_wdgt)
        self.layout.addWidget(self.selection_button)
        self.layout.addWidget(self.confirm_button)
        self.setLayout(self.layout)

        # Execute and show dialog window.
        self.exec()

    # Below are GUI signal processor functions.
    def keyPressEvent(self, event):
        """Respond to `Esc` and `Return` keys."""
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.reject()
                self.on_reset_layer()
            elif event.key() == Qt.Key_Return:
                self.accept()

    def on_deselect_all(self):
        """Handle `No to all` button signal."""
        self.feature_wdgt.deselectAllOptions()

    def on_select_all(self):
        """Handle `Yes to all` button signal."""
        self.feature_wdgt.selectAllOptions()

    def on_selected_field(self):
        """Handle `field_wdgt` signal."""
        self.feature_wdgt.clear()
        try:
            attribute_values = self.generate_feature_model()
            self.feature_wdgt.addItems(attribute_values)
            self.selection_button.setDisabled(False)
        except:
            self.selection_button.setDisabled(True)
            self.feature_wdgt.clear()

    def on_selected_layer(self):
        """Handle `layer_wdgt` signal."""
        if self.layer_wdgt.currentIndex() != 0:
            self.ok_button.setDisabled(False)
            self.field_wdgt.setFields(self.generate_field_model(self.layer_wdgt.currentLayer()))
            self.feature_wdgt.clear()
            if self.feature_wdgt.count() == 0:
                self.selection_button.setDisabled(True)
        else:
            self.ok_button.setDisabled(True)
            self.selection_button.setDisabled(True)
            self.field_wdgt.setFields(QgsFields())
            self.feature_wdgt.clear()

    def on_reset_layer(self):
        """Reset combo box fields."""
        self.layer_wdgt.setCurrentIndex(0)
        self.field_wdgt.setCurrentIndex(0)

    # Below are private functions responding to user entries.
    def filter_layer(self):
        """
        Generate empty layer.

        This function generates empty layer which type depends on user entry.
        """
        type = self.layer_type.lower()
        layer = {'vector': QgsVectorLayer(), 'raster': QgsRasterLayer()}
        return layer[type]

    def generate_feature_model(self):
        """Generate feature model based on applied filter."""
        layer = self.accepted_layer()
        fields = layer.fields()
        field = self.accepted_field()
        field_index = fields.indexFromName(field.name())

        if field.isDateOrTime():
            values = [value.toString(Qt.ISODate) for value in layer.uniqueValues(field_index)]
            values.sort()
            return values
        else:
            values = [value for value in layer.uniqueValues(field_index)]
            values.sort()
            return [str(sorted_value) for sorted_value in values]

    def generate_field_model(self, layer):
        """Generate field model based on applied filter."""
        temp_fields = QgsFields()
        temp_features = QgsFeature()

        if type(layer) != type(QgsRasterLayer()):
            features_list = list(layer.getFeatures())
            fields_list = layer.fields().toList()

            if self.field_matches is not None:
                for key in self.field_matches.keys():
                    for field in fields_list:
                        if key.lower() == field.name().lower():
                            for feature in features_list:
                                if field.type() == 2 or field.type() == 4:
                                    temp_fields.append(QgsField(field.name(), QVariant.Int, field.typeName(), field.length(), field.precision()))
                                    temp_features.setFields(temp_fields)
                                    temp_features.setAttribute(temp_fields.indexFromName(field.name()), feature.attribute(field.name()))
                                elif field.type() == 10:
                                    temp_fields.append(QgsField(field.name(), QVariant.String, field.typeName(), field.length(), field.precision()))
                                    temp_features.setFields(temp_fields)
                                    temp_features.setAttribute(temp_fields.indexFromName(field.name()), feature.attribute(field.name()))
                                elif field.type() == 14:
                                    temp_fields.append(QgsField(field.name(), QVariant.Date, field.typeName(), field.length(), field.precision()))
                                    temp_features.setFields(temp_fields)
                                    temp_features.setAttribute(temp_fields.indexFromName(field.name()), feature.attribute(field.name()))
                                elif field.type() == 6:
                                    temp_fields.append(QgsField(field.name(), QVariant.Double, field.typeName(), field.length(), field.precision()))
                                    temp_features.setFields(temp_fields)
                                    temp_features.setAttribute(temp_fields.indexFromName(field.name()), feature.attribute(field.name()))
            else:
                for field in fields_list:
                    for feature in features_list:
                        if field.type() == 2 or field.type() == 4:
                            temp_fields.append(QgsField(field.name(), QVariant.Int, field.typeName(), field.length(), field.precision()))
                            temp_features.setFields(temp_fields)
                            temp_features.setAttribute(temp_fields.indexFromName(field.name()), feature.attribute(field.name()))
                        elif field.type() == 10:
                            temp_fields.append(QgsField(field.name(), QVariant.String, field.typeName(), field.length(), field.precision()))
                            temp_features.setFields(temp_fields)
                            temp_features.setAttribute(temp_fields.indexFromName(field.name()), feature.attribute(field.name()))
                        elif field.type() == 14:
                            temp_fields.append(QgsField(field.name(), QVariant.Date, field.typeName(), field.length(), field.precision()))
                            temp_features.setFields(temp_fields)
                            temp_features.setAttribute(temp_fields.indexFromName(field.name()), feature.attribute(field.name()))
                        elif field.type() == 6:
                            temp_fields.append(QgsField(field.name(), QVariant.Double, field.typeName(), field.length(), field.precision()))
                            temp_features.setFields(temp_fields)
                            temp_features.setAttribute(temp_fields.indexFromName(field.name()), feature.attribute(field.name()))
            return temp_fields
        else:
            return QgsFields()

    def generate_layer_model(self):
        """Generate layer model based on applied filter."""
        layers = set(self.get_project_layers())
        type_layers = set()
        geom_type_layers = set()
        name_layers = set()

        if len(self.layer_type) != 0:
            type_layers = {layer for layer in layers if type(layer) == type(self.filter_layer())}

        if self.geometry_type != 0:
            geom_type_layers = {layer for layer in layers if type(layer) != type(QgsRasterLayer()) if layer.wkbType() == self.geometry_type}

        if len(self.layer_matches) != 0:
            for layer in layers:
                for key in self.layer_matches.keys():
                    if key.lower() in layer.name().lower():
                        name_layers.add(layer)

        if (len(self.layer_type) == len(self.layer_matches)) and (self.geometry_type == set()):
            type_layers = layers
            geom_type_layers = layers
            name_layers = layers

        allowed_layers = layers.intersection(type_layers | geom_type_layers | name_layers)
        return layers.difference(allowed_layers)

    def get_project_layers(self):
        """Map QGIS-Project instances."""
        return QgsProject.instance().mapLayers().values()

    # Public functions listed below this line.
    def accepted_layer(self):
        """Return currently selected layer."""
        return self.layer_wdgt.currentLayer()
    
    def accepted_field(self):
        """Return currently selected field."""
        fields = self.field_wdgt.fields()
        try:
            return fields.field(fields.indexFromName(self.field_wdgt.currentField()))
        except:
            return None

    def accepted_features(self):
        """Return currently selected/checked features."""
        features = self.feature_wdgt.checkedItems()
        if len(features) > 0:
            return features
        else:
            return None
