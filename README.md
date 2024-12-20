# QGIS field annotations

A QGIS plugin to make map annotations and photos in the field.

![Preview of field annotations in QGIS](field_annotation_example.png "Preview of field annotations in QGIS")

## Creating annotations

### Map annotations

Map annotations can be made in three ways: with a point, line or polygon. Each annotation can have a text, and can optionally be linked to a map layer.

Annotations are stored in separate layers in a Geopackage database in the same directory as the QGIS project.

### Photo annotations

A special type of annotation is the photo annotation, where you can add an annotation with text and photo(s). Either take some new photos or import existing ones.

Photos are stored inside a new directory in the same directory as the QGIS project.