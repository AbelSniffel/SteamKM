# UI_Handler.py
from PySide6.QtWidgets import QHBoxLayout
from Config import HORIZONTAL_SPACING

def apply_merged_edges(widgets_pairs, merge_edges):
    for left_widget, right_widget, container_layout, left_object_name, right_object_name in widgets_pairs:
        if merge_edges:
            # Set object names for merged appearance
            if left_object_name:
                left_widget.setObjectName(left_object_name)
            if right_object_name:
                right_widget.setObjectName(right_object_name)
            
            # Set spacing to 0 for connected appearance if it's a horizontal layout
            if isinstance(container_layout, QHBoxLayout):
                container_layout.setSpacing(0)
        else:
            # Set default object names
            if left_object_name:
                # If the merged name is "Title-UnifiedUI", revert to "Title"
                if left_object_name == "Title-UnifiedUI":
                    left_widget.setObjectName("Title")
                # Remove flat edge object names when not merged
                elif left_object_name in ("FlatRightEdge", "FlatLeftEdge"):
                    left_widget.setObjectName(None)
                else:
                    left_widget.setObjectName(left_object_name)
            if right_object_name:
                right_widget.setObjectName(None)
            
            # Restore default spacing
            if isinstance(container_layout, QHBoxLayout):
                container_layout.setSpacing(HORIZONTAL_SPACING)
        
        # Force style refresh for affected widgets
        for widget in [left_widget, right_widget]:
            if widget:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
