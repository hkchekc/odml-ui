import cgi

import pygtkcompat

from odml import format as ofmt

import gtk

from . import commands
from .tree_view import TreeView

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

COL_KEY = 0
COL_VALUE = 1


class AttributeView(TreeView):
    """
    A key-value ListStore based TreeView

    showing properties and allows to edit them
    based on the format-description of the obj's class
    """
    def __init__(self, execute_func=lambda x: x(), obj=None):
        self.execute = execute_func
        self._store = gtk.ListStore(str, str)
        self._store.set_sort_column_id(COL_KEY, gtk.SORT_ASCENDING)
        self._model = None
        self._fmt = None

        if obj is not None:
            self.set_model(obj)

        # List of property attributes that is displayed in the property window
        # and is not displayed again in the attribute view.
        self._property_exclude = ["unit", "type", "uncertainty", "definition"]

        super(AttributeView, self).__init__(self._store)

        self.add_column(name="Attribute", edit_func=None,
                        data=COL_KEY, col_id=COL_KEY)
        self.add_column(name="Value", edit_func=self.on_edited,
                        data=COL_VALUE, col_id=COL_VALUE)

        self._treeview.show()

    def set_model(self, obj):
        if self._model is not None:
            self._model.remove_change_handler(self.on_object_change)
        obj.add_change_handler(self.on_object_change)

        self._model = obj
        self._fmt = obj._format
        self.fill()

    def get_model(self):
        return self._model

    def fill(self):
        """
        The *fill* method resets the current attribute view store,
        walks over all attributes of the currently selected odML entity object.
        Any value is converted to string, escaped for proper viewing and
        added as a store entry.
        """
        self._store.clear()

        for curr_attr in self._fmt._args:
            val = getattr(self._model, self._fmt.map(curr_attr))
            if not isinstance(val, list):
                if val is not None:
                    val = cgi.escape(str(val))

                # Exclude property attributes that are displayed in the
                # PropertyView window.
                if isinstance(self._fmt, type(ofmt.Property)) and \
                        curr_attr in self._property_exclude:
                    continue

                self._store.append([curr_attr, val])

    def on_edited(self, widget, row, new_value, col):
        store = self._store
        store_iter = store.get_iter(row)
        curr_val = store.get_value(store_iter, COL_KEY)
        cmd = commands.ChangeValue(
            object=self._model,
            attr=self._fmt.map(curr_val),
            new_value=new_value)

        self.execute(cmd)

    def on_object_change(self, context):
        """
        This change listener is attached to the current object class
        and updates the GUI elements upon relevant change events.
        """
        if context.cur is self._model and context.post_change:
            self.fill()

    def on_button_press(self, widget, event):
        pass
