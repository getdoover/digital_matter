

class doover_ui_element:

    def __init__(self, name, display_str, is_available=None, help_str=None, verbose_str=None, show_activity=True, form=None, graphic=None, layout=None):
        self.name = name
        self.display_str = display_str
        self.is_available = is_available
        self.help_str = help_str
        self.verbose_str = verbose_str
        self.show_activity = show_activity
        self.form = form
        self.graphic = graphic
        self.layout = layout

    def get_type(self):
        return 'uiElement'

    def get_as_dict(self):
        result = dict()
        result['type'] = self.get_type()
        result['name'] = self.name
        result['displayString'] = self.display_str
        if self.is_available is not None:
            result['isAvailable'] = self.is_available
        if self.help_str is not None:
            result['helpString'] = self.help_str
        if self.verbose_str is not None:
            result['verboseString'] = self.verbose_str
        if not self.show_activity:
            result['showActivity'] = False
        if self.form is not None:
            result['form'] = self.form
        if self.graphic is not None:
            result['graphic'] = self.graphic
        if self.layout is not None:
            result['layout'] = self.layout

        return result

    def get_name(self):
        return self.name

    def get_display_str(self):
        return self.display_str

    def get_is_available(self):
        return self.available

    def get_help_str(self):
        return self.help_str

    def get_verbose_string(self):
        return self.verbose_str

    def get_show_activity(self):
        return self.show_activity

    def set_display_str(self, display_str):
        self.display_str = display_str

    def set_is_available(self, available):
        self.available = available

    def set_help_str(self, help_string):
        self.help_str = help_string

    def set_verbose_string(self, verbose_str):
        self.verbose_str = verbose_str

    def set_show_activity(self, show_activity):
        self.show_activity = show_activity

    def set_form(self, form):
        self.form = form


class doover_ui_hidden_value:

    def __init__(self, name):
        self.name = name

    def get_type(self):
        return 'uiHiddenValue'

    def get_as_dict(self):
        result = dict()
        result['type'] = self.get_type()
        result['name'] = self.name

        return result

    def get_name(self):
        return self.name



class doover_ui_connection_info:

    ## Connection types
    #   - "constant"
    #   - "periodic"

    def __init__(
            self,
            name,
            connection_type="constant", ## "constant" or "periodic"
            connection_period=None, ## The expected time between connection events (seconds) - only applicable for "periodic"
            next_connection=None, ## Expected time of next connection (seconds after shutdown)
            offline_after=None, ## Show as offline if disconnected for more than x secs
        ):
        self.name = name
        self.connection_type = connection_type
        self.connection_period = connection_period
        self.next_connection = next_connection
        self.offline_after = offline_after

    def get_type(self):
        return 'uiConnectionInfo'

    def get_as_dict(self):
        result = dict()
        result['type'] = self.get_type()
        result['name'] = self.name
        result['connectionType'] = self.connection_type
        if self.connection_period is not None:
            result['connectionPeriod'] = self.connection_period
        if self.next_connection is not None:
            result['nextConnection'] = self.next_connection
        if self.offline_after is not None:
            result['offlineAfter'] = self.offline_after

        return result

    def get_name(self):
        return self.name


class doover_ui_warning_indicator(doover_ui_element):

    def __init__(self, name, display_str, is_available=None, help_str=None, verbose_str=None, show_activity=False, form=None, can_cancel=True):

        doover_ui_element.__init__(self, name, display_str, is_available, help_str, verbose_str, show_activity, form)

        self.can_cancel = can_cancel

    def get_type(self):
        return 'uiWarningIndicator'

    def get_as_dict(self):
        result = doover_ui_element.get_as_dict(self)
        result['canCancel'] = self.can_cancel

        return result

class doover_ui_variable(doover_ui_element):

    def __init__(self, name, display_str, var_type, curr_val, dec_precision=None, ranges=None,  verbose_str=None, show_activity=True, form=None, graphic=None, layout=None):

        doover_ui_element.__init__(self, name, display_str, verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout)

        self.var_type = var_type
        self.curr_val = curr_val
        self.dec_precision = dec_precision
        self.ranges = ranges

    def get_type(self):
        return 'uiVariable'

    def get_as_dict(self):
        result = doover_ui_element.get_as_dict(self)
        result['type'] = self.get_type()

        result['varType'] = self.get_var_type()

        curr_val = self.get_val()
        if curr_val is not None:
            result['currentValue'] = curr_val
        dec_precision = self.get_dec_precision()
        if dec_precision is not None:
            result['decPrecision'] = dec_precision
        ranges = self.get_ranges()
        if ranges is not None:
            result['ranges'] = ranges

        return result

    def get_val(self):
        if self.get_dec_precision() is not None and self.curr_val is not None:
            return round(self.curr_val, self.get_dec_precision())
        return self.curr_val

    def get_var_type(self):
        return self.var_type

    def set_val(self, val):
        self.curr_val = val

    def get_dec_precision(self):
        return self.dec_precision

    ## Ranges is a list of dicts 
    #   {
    #       "label" : None,
    #       "min" : None,
    #       "max" : None,
    #       "colour" : None,
    #       "showOnGraph" : True,
    #   }
    def get_ranges(self):
        return self.ranges


class doover_ui_interaction(doover_ui_element):
    
    def __init__(self, name, display_str, is_available=None, help_str=None, verbose_str=None, show_activity=True, form=None, graphic=None, layout=None ):

        doover_ui_element.__init__(self, name, display_str, is_available=None, help_str=None, verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout )

    def get_type(self):
        return 'uiInteraction'

    def get_as_dict(self):
        result = doover_ui_element.get_as_dict(self)
        result['type'] = self.get_type()

        return result

class doover_ui_action(doover_ui_interaction):

    def __init__(self, name, display_str, is_available=None, help_str=None, colour="blue", requires_confirm=True,  verbose_str=None, show_activity=True, form=None, graphic=None, layout=None ):
    
        doover_ui_interaction.__init__(self, name, display_str, is_available, help_str, verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout )

        ## A list of doover_ui_element's
        self.colour = colour
        self.requires_confirm = requires_confirm

    def get_type(self):
        return 'uiAction'

    def get_as_dict(self):
        result = doover_ui_interaction.get_as_dict(self)
        result['type'] = self.get_type()

        result['colour'] = self.colour
        result['requiresConfirm'] = self.requires_confirm

        return result
        

class doover_ui_state_command(doover_ui_interaction):

    def __init__(self, name, display_str, is_available=None, help_str=None, user_options=[], verbose_str=None, show_activity=True, form=None, graphic=None, layout=None ):
    
        doover_ui_interaction.__init__(self, name, display_str, is_available, help_str, verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout )

        ## A list of doover_ui_element's
        self.user_options = user_options

    def get_type(self):
        return 'uiStateCommand'

    def get_as_dict(self):
        result = doover_ui_interaction.get_as_dict(self)
        result['type'] = self.get_type()

        # user_options = []
        # for o in self.get_user_options():
        #     user_options.append( o.get_as_dict() )
        user_options = {}
        for o in self.get_user_options():
            opt_dict = o.get_as_dict()
            user_options[opt_dict['name']] = opt_dict
        result['userOptions'] = user_options

        return result

    def set_user_options(self, user_options):
        self.user_options = user_options

    def get_user_options(self):
        return self.user_options

    def add_user_option(self, option):
        if isinstance(option, list):
            for o in option:
                self.user_options.append(o)
        else:
            self.user_options.append(option)

        return self

class doover_ui_float_parameter(doover_ui_interaction):
    
    def __init__(self, name, display_str, is_available=None, help_str=None, float_min=None, float_max=None, verbose_str=None, show_activity=True, form=None, graphic=None, layout=None ):
    
        doover_ui_interaction.__init__(self, name, display_str, is_available, help_str, verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout)

        self.float_min = float_min
        self.float_max = float_max

    def get_type(self):
        return 'uiFloatParam'

    def get_as_dict(self):
        result = doover_ui_interaction.get_as_dict(self)
        result['type'] = self.get_type()

        result['min'] = self.get_min()
        result['max'] = self.get_max()

        return result

    def get_min(self):
        return self.float_min
    
    def get_max(self):
        return self.float_max

    def set_min(self, float_min):
        self.float_min = float_min

    def set_max(self, float_max):
        self.float_max = float_max
        
        
class doover_ui_text_parameter(doover_ui_interaction):
    
    def __init__(self, name, display_str, is_available=None, help_str=None, is_text_area=False, verbose_str=None, show_activity=True, form=None, graphic=None, layout=None ):
    
        doover_ui_interaction.__init__(self, name, display_str, is_available, help_str, verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout)

        self.is_text_area = is_text_area

    def get_type(self):
        return 'uiTextParam'

    def get_as_dict(self):
        result = doover_ui_interaction.get_as_dict(self)
        result['type'] = self.get_type()

        result['isTextArea'] = self.is_text_area

        return result


class doover_ui_datetime_parameter(doover_ui_interaction):
    ## datetime is stored as epoch seconds UTC
    
    def __init__(self, name, display_str, is_available=None, help_str=None, include_time=False, verbose_str=None, show_activity=True, form=None, graphic=None, layout=None):
    
        doover_ui_interaction.__init__(self, name, display_str, is_available, help_str, verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout)

        self.include_time = include_time

    def get_type(self):
        return 'uiDatetimeParam'

    def get_as_dict(self):
        result = doover_ui_interaction.get_as_dict(self)
        result['type'] = self.get_type()

        result['includeTime'] = self.include_time

        return result


class doover_ui_container(doover_ui_element):

    def __init__(self, name, display_str, is_available=None, help_str=None, children=[], status_icon=None, verbose_str=None, show_activity=True, form=None, graphic=None, layout=None ):
    
        doover_ui_element.__init__(self, name, display_str, is_available=None, help_str=None, verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout)

        ## A list of doover_ui_elements
        self.children = children
        self.statusIcon = status_icon

    def get_type(self):
        return 'uiContainer'

    def get_as_dict(self):
        result = doover_ui_element.get_as_dict(self)
        result['type'] = self.get_type()

        if self.statusIcon is not None:
            result['statusIcon'] = self.statusIcon

        # children = []
        # for c in self.get_children():
        #     children.append( c.get_as_dict() )
        # result['children'] = children
        children = {}
        for c in self.get_children():
            child_dict = c.get_as_dict()
            children[child_dict['name']] = child_dict
        result['children'] = children

        return result

    def get_children(self):
        return self.children

    def set_children(self, children):
        self.children = children

    def add_child(self, child):
        self.children.append( child )
        return self

    def add_children(self, children):
        for c in children:
            self.children.append( c )
        return self

    def remove_child(self, child):
        self.children.remove( child )

    def set_status_icon(self, status_icon=None):
        self.statusIcon = status_icon


class doover_ui_submodule(doover_ui_container):

    def __init__(self, name, display_str, is_available=None, help_str=None, children=[], status_string=None, collapsed=False):
        
        doover_ui_container.__init__(self, name, display_str, is_available=None, help_str=None, children=[])

        self.status_string = status_string
        self.collapsed = collapsed

    def get_type(self):
        return 'uiSubmodule'

    def get_as_dict(self):
        result = doover_ui_container.get_as_dict(self)
        result['type'] = self.get_type()

        status_string = self.get_status_string()
        if status_string is not None:
            result['statusString'] = status_string
        #result['isCollapsed'] = self.get_is_collapsed()

        return result

    def get_status_string(self):
        return self.status_string

    def get_is_collapsed(self):
        return self.collapsed

    def set_status_string(self, status_string):
        self.status_string = status_string

    def set_is_collapsed(self, collapsed):
        self.collapsed = collapsed

class doover_ui_camera(doover_ui_element):

    def __init__(self, name, display_str, uri, output_type=None, mp4_output_length=None, wake_delay=5, verbose_str=None, show_activity=True, form=None, graphic=None, layout=None):

        doover_ui_element.__init__(self, name, display_str, is_available=None, help_str=None, verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout)

        self.uri = uri
        self.output_type = output_type
        self.mp4_output_length = mp4_output_length
        self.wake_delay = wake_delay

    def get_type(self):
        return 'uiCamera'

    def get_uri(self):
        return self.uri

    def get_output_type(self):
        return self.output_type

    def get_mp4_output_length(self):
        return self.mp4_output_length


class doover_ui_alert_stream(doover_ui_element):

    def __init__(self, name, display_str):
        doover_ui_element.__init__(self, name, display_str, is_available=None, help_str=None)

    def get_type(self):
        return 'uiAlertStream'


class doover_ui_multiplot(doover_ui_element):

    def __init__(self, name, display_str, series, series_colours, series_active):

        doover_ui_element.__init__(self, name, display_str)

        self.series = series
        self.series_colours = series_colours
        self.series_active = series_active

    def get_type(self):
        return 'uiMultiPlot'

    def get_as_dict(self):
        result = doover_ui_element.get_as_dict(self)
        result['series'] = self.series
        result['colours'] = self.series_colours
        result['activeSeries'] = self.series_active
        
        return result

