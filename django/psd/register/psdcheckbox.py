
from django.db import models
from django.utils.encoding import force_unicode
from itertools import chain
from django.forms.widgets import CheckboxInput
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django import forms

import logging
logger = logging.getLogger('psd.register.psdcheckbox')


def get_preference_for( code_str, gen ):
    """
    Return 1 if gen is one of the preference codes in code_str
    which is a csv seperated string with possible "-X" attached.  If "gen-X" 
    found then return X
    """
    if not code_str:
        return 0
 
    gs = code_str.split( ",")
    for x in gs:
            sp = x.split("-")
            if sp[0] == gen:
                if len(sp) > 1:
                    return int(sp[1])
                else:
                    return 1
        
    return 0
        
    
    
def genSeekAndPrefs( code_str ):
    """ 
    Take coded preference string, e.g. "M-2,W,TF,Q-2" and 
    turn it into a list of the codes, followed by those codes with
    weights greater than 1.
    
    If all codes have weights greater than one, renormalize.  Nothing
    is preferred if everything is.
    """
    if not code_str:
        return [[], []]

    new_value = [ x.split("-") for x in code_str.split(",") ]
    seeks = [ x[0] for x in new_value]
    prefs = [x[0] for x in new_value if len(x) > 1]
    #print "seeks", seeks
    #print "prefs", prefs
    if len(seeks) == len(prefs):
        prefs = []
        
    return [seeks, prefs]


def genCodeForSeekAndPrefs( seeks, prefs ):
    """
    Given two lists of gender codes, generate a new list of union of all codes
    with each code followed
    by "-2" if it appears in both lists.
    """
    pref_int = set(seeks).intersection(prefs)
    seek_un = set(seeks).union( prefs )
    seeks = []
    for s in seek_un:
            if s in pref_int:
                seeks.append( s + "-2" )
            else:
                seeks.append( s )
            
    return ",".join(seeks)
    
    

class PSDMultipleChoiceField(forms.MultipleChoiceField):
    def to_python(self, value):
        return value.split(",")
    
    def clean(self, value):
        return ",".join(value)
    
    def validate(self, value):
        pass
    
    def run_validators(self, value):
        pass




class PSDMultipleChoiceWithPrefField(forms.MultipleChoiceField):
    def to_python(self, value):
        #print "to python we go?", value
        return value.split(",")
    
    def clean(self, value):
        #print "Cleaning PSD with Pref"
        seeks = value[0]
        prefs = value[1]        
        return genCodeForSeekAndPrefs( seeks, prefs )
    
    def validate(self, value):
        pass
    
    def run_validators(self, value):
        pass


    
    
    
 
    
    
class PSDCheckboxSelectMultiple(forms.CheckboxSelectMultiple):

    def render_to_list(self, name, value, attrs=None, choices=(), keep_desc=True):
        """
        Return list of HTML strings for each checkbox
        Param: value -- either a list of checkboxes to check off or a comma-seperated string of list checkboxes to check off.
        """
        #print "render_to_list(%s) value: %s\t\tattrs=%s\n\tchoices=%s" % (name, value, attrs, choices)
        
        if value is None: value = []
        if not isinstance(value, list):
            if isinstance(value,int):
                value = [value]
            else:
                value = value.split(",")

        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        #print "\tfinal_attrs = %s" % ( final_attrs, )
        output = []
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        #print "\tstr_values = %s" % ( str_values, )
        
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            if keep_desc:
                option_label = conditional_escape(force_unicode(option_label))
            else:
                option_label = ""
            #print "option_value", option_value
            #print "rendered_cb", rendered_cb
            #print "label_for", label_for
            output.append(u'<label%s>%s%s</label>' % (label_for, rendered_cb, option_label))
        
        return output

    def render(self, name, value, attrs=None, choices=() ):
        #print "render(%s) value: %s\t\tattrs=%s\n\tchoices=%s" % (name, value, attrs, choices)
        
        lst = self.render_to_list( name, value, attrs, choices )
        output = []
        for s in lst:
            output.append( "<li>" + s + "</li>" )
        
        op = u'<ul style="list-style: none;">\n' + u'\n'.join(output) + "\n</ul>"
        return mark_safe( op )
    


class PSDPrefCheckboxWidget(forms.MultiWidget):
    """
    A widget that gives two checkboxes for each option.
    """
    def __init__(self,  attrs=None, choices=()):
        #print "Constructor of PSDPrefCheckboxWidget"
        #print "\tchoices", choices
        #print "\tattrs", attrs
        choices = getPSDCheckboxOptions("Gender")
        widgets = (PSDCheckboxSelectMultiple(attrs=attrs, choices=choices),
                    PSDCheckboxSelectMultiple(attrs=attrs, choices=choices))
        super(PSDPrefCheckboxWidget, self).__init__(widgets, attrs)
    
    def compress(self,value):
        #print "compressing", value
        return value
    
    def decompress(self, value):
        #print "decompressing", value
        return genSeekAndPrefs( value )


    def render(self, name, value, attrs=None):
        # value is a list of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)
        output = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id', None)
        mx = len(self.widgets)
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, i))
            output.append(widget.render_to_list(name + '_%s' % i, widget_value, final_attrs, keep_desc=(i==mx-1)))
        return mark_safe(self.format_output(output))

    def format_output(self, rendered_widgets):
        """
        Given a list of rendered widgets (as strings), returns a Unicode string
        representing the HTML for the whole lot.

        This hook allows you to format the HTML design of the widgets, if
        needed.
        """
        output = []
        for (i, wid1) in enumerate(rendered_widgets[0]):
            output.append( "<li>" + rendered_widgets[0][i] + rendered_widgets[1][i] + "</li>" )
        
        op = u'<ul style="list-style: none;">\n' + u'\n'.join(output) + "\n</ul>"
        #print op
        return op


   
class MatchQuestion(models.Model):
    question = models.CharField(max_length=200)
    explanation = models.CharField(max_length=200, null=True)
    internal_comment = models.CharField(max_length=200, null=True)
    hard_match = models.BooleanField()
    strict_subset_match = models.BooleanField()
    checkbox = models.BooleanField()
    ask_about_seek = models.BooleanField()
    include_name = models.BooleanField()
    question_code = models.CharField(max_length=15)
#    render_string = models.CharField(max_length=100, default="Looking for <LOOK>.  Registered as <AM>")
#    render_conjunction = models.CharField(max_length=100, default="and")
#    render_seek_conjunction = models.CharField(max_length=100, default="or")

    allow_preferences = models.BooleanField()
    
    def choices(self):
        return list(MatchChoice.objects.filter(question=self.id))
    
    def num_choices(self):
        mc = MatchChoice.objects.filter(question=self.id)
        return len(mc)
    
    def isYN(self):
        """
        Can this question be represented as a Y/N checkbox?
        """
        if self.checkbox or self.num_choices() != 2:
            return False
        
        codes = set( x.choice_code for x in self.choices() )
        if "Y" in codes and "N" in codes:
            return True
        else:
            return False
 
       
    def __unicode__(self):
        return self.question


class MatchChoice(models.Model):
    question = models.ForeignKey(MatchQuestion)
    choice = models.CharField(max_length=200)
    choice_code = models.CharField( max_length=2 )
    
    def __unicode__(self):
        #return "[" + self.choice_code + "]: " + self.choice
        return self.choice


def getSeekFormField(quest):
    #print "genSeekFormField for %s" % (quest, )
    try:
        locs = MatchQuestion.objects.get( question=quest )
        if locs.allow_preferences:
            #print "returning preference checkbox"
            return PSDMultipleChoiceWithPrefField(choices=getPSDCheckboxOptions(quest), widget=PSDPrefCheckboxWidget, label=quest+" Sought")
        else:
            #print "returning no-preference checkbox"
            return PSDMultipleChoiceField(choices=getPSDCheckboxOptions(quest), widget=PSDCheckboxSelectMultiple, label=quest+" Sought")
    except MatchQuestion.DoesNotExist:
        logger.error( "Failed to load %s field in getSeekFormField()" % (quest,) ) 
    logger.warning( "Attempting to return default of no preference for seek" )
    return PSDMultipleChoiceWithPrefField(choices=getPSDCheckboxOptions(quest), widget=PSDPrefCheckboxWidget, label=quest+" Sought")

    

def getPSDCheckboxOptions( quest, no_desc=False ):
    """
    This method fetches all the possible responses to a given question as defined by 'quest'
    It looks up this info in the MatchQuestion object.  Each MatchChoice connected to it has a 
    (up to) two-letter code and a longer string for the response.   Can make defaults using the 
    psdmanage.py code in toplevel
    
    Returns: list of pairs of (code,description)
    """
    try:
        locs = MatchQuestion.objects.get( question=quest )
    except MatchQuestion.DoesNotExist:
        return ( ('UK', 'Unknown'), ('ML', 'Make "%s" match question' % (quest,) ), ('SR', 'Sorry for the ugly') )
    
    locchoice = locs.matchchoice_set.all()
    
    if no_desc:
        tups = [ (loc.choice_code, "") for loc in locchoice ]
    else:
        tups = [ (loc.choice_code, loc.choice) for loc in locchoice ]
    
    return tups
