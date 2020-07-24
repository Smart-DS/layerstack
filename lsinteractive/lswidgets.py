import abc
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

import ipywidgets as widgets
import traitlets as t

ls_base_dir = Path(__file__).parent.parent


VALSTR = 'value' # used to validate proposed trait values

class LSTraitError(t.TraitError):
    pass

# ------------------------------------------------------------------------------
# Data Models
# ------------------------------------------------------------------------------

class StackEditorData(t.HasTraits):
    # class-level data
    layer_library_dirs = {}
    stack_library_dirs = {}

    # object attributes
    active_layer_library = t.Unicode(allow_none=True)
    active_stack_library = t.Unicode(allow_none=True)

    def __init__(self, layer_library_dirs=None, stack_library_dirs=None):
        # class attributes, only update if not None
        if layer_library_dirs is not None:
            logger.info("Upating StackEditorData.layer_library_dirs")
            StackEditorData.layer_library_dirs = layer_library_dirs
        if stack_library_dirs is not None:
            logger.info("Upating StackEditorData.stack_library_dirs")
            StackEditorData.stack_library_dirs = stack_library_dirs

    @t.validate('active_layer_library')
    def _valid_layer_library(self, proposal):
        if proposal[VALSTR] not in self.layer_library_dirs:
            raise LSTraitError(f"{proposal[VALSTR]} should be one of the layer "
                    f"library keys: {list(self.layer_library_dirs.keys())}")
        return proposal[VALSTR]

    @t.validate('active_stack_library')
    def _valid_stack_library(self, proposal):
        if proposal[VALSTR] not in self.stack_library_dirs:
            raise LSTraitError(f"{proposal[VALSTR]} should be one of the stack "
                    f"library keys: {list(self.stack_library_dirs.keys())}")
        return proposal[VALSTR]
            



class SingleStackEditorData(StackEditorData):
    # data
    stack = None

    # traits that locate data or allow editing
    stack_name = t.Unicode(allow_none=True)
    filename = t.Unicode(allow_none=True)
    

class SingleStackEditorWithTemplateData(SingleStackEditorData):
    # data
    template_stack = None

    # traits that locate data or allow editing
    template_stack_library = t.Unicode(allow_none=True)
    template_filename = t.Unicode(allow_none=True)


# ------------------------------------------------------------------------------
# Views
# ------------------------------------------------------------------------------


class TextEditWithLabel(widgets.HBox):
    def __init__(self, label, placeholder = None, label_width=150, 
                 text_width=700, *args, **kwargs):
        # initialize HBox
        super().__init__(*args, **kwargs)
        
        # make the Label widget
        self._label = widgets.Label(label)
        self._label.layout.width = f"{label_width}px"

        # make the Text widget
        text_kwargs = {}
        if placeholder is not None:
            text_kwargs['placeholder'] = placeholder
        self._text = widgets.Text(**text_kwargs)
        self._text.layout.width = f"{label_width}px"

        self.children = list(self.children) + [self._label, self._text]


class LibrarySelector(widgets.VBox):
    def __init__(self, data_model, *args, **kwargs):
        assert isinstance(data_model, StackEditorData), f"{data_model} is a {type(data_model)}"
        self._model = data_model

        # select which library
        self._label = widgets.Label("Select a library:")
        self._select = widgets.Select(options = self._libraries())
        self._select.observe(self._update_active_library)

        # then observe its location and contents
        self._result = widgets.Label()
        

    @abc.abstractmethod
    def _libraries(self): pass

    @abc.abstractmethod
    def _update_active_library(self): pass


class StackLibrarySelector(LibrarySelector):
    def _libraries(self):
        return list(self._model.stack_library_dirs.keys())

    def _update_active_library(self):
        self._model.active_stack_library = self._select.value


class StackCreator(widgets.VBox):
    def __init__(self, data_model, *args, **kwargs):
        super().__init__(*args, **kwargs)

        assert isinstance(data_model, SingleStackEditorWithTemplateData), f"{data_model} is a {type(data_model)}"
        self._model = data_model

        # minimum to save a stack -- A name and a file location
        self._stack_name = TextEditWithLabel(
            "Stack Name:", 
            placeholder="human readable name for new Stack")
        
        self._filename = TextEditWithLabel(
            "Filename:", 
            placeholder="name of json file where Stack is to be saved")

        self.children = list(self.children) + [self._stack_name, self._filename]

        