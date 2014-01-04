# Create your forms here.

import re
from psd.register.models import Person, RegRecord, DateRecord, MatchRecord, BreakRecord
from django.contrib.auth.models import User
from psd.register.psdcheckbox import *
from django.forms import ModelForm


def augment_person_form(pform, evt, old_answers):
    #print "Old answers = %s" % (old_answers, )
    for question in evt.extra_questions.all():
        #print ( "building " + question.question_code )
        initialV = old_answers.get( question.question_code, None )
        #print ( "\tinitial = %s" % ( initialV, ) )
        #print "Match choices: "
        #for mc in question.matchchoice_set.all(): 
        #    print "%s-%s " % (mc.pk, mc, )
        if question.isYN():
        #    print "YN Q"
            field = forms.ModelMultipleChoiceField(question.matchchoice_set, widget=PSDCheckboxSelectMultiple, initial=initialV)          
        elif question.checkbox:
        #    print "Checkbox Q"
            field = forms.ModelMultipleChoiceField(question.matchchoice_set, widget=PSDCheckboxSelectMultiple, initial=initialV)
        else:
        #    print "No check Q"
            #field = forms.ModelChoiceField(question.matchchoice_set, widget=RadioSelect)
            field = forms.ModelChoiceField(question.matchchoice_set, initial=initialV)
        pform.fields["X_" + question.question_code] = field

        if question.ask_about_seek:
            initialV = old_answers.get( "seek_" + question.question_code, None )
        #    print ( "\tseek initial = %s" % ( initialV, ) )
            field2 = forms.ModelMultipleChoiceField(question.matchchoice_set, widget=PSDCheckboxSelectMultiple, initial=initialV)
            pform.fields["X_seek_" + question.question_code] = field2
        else:
            field2 = None
        # TODO: is this else statement needed???
        
    return pform


def clean_string(data):
        data = " ".join(data.split())
        if re.match( '^[\d\w\' ]+$', data ) == None:
            raise forms.ValidationError("Nicknames and names need to have only numbers, letters, and spaces in them.")
        if len(data) == 0:
            raise forms.ValidationError( "Nicknames and names need to have something, even if it is an initial." )
        return data
 
def super_clean_string(data):
        data = data.lower()
        if re.match( '^[\d\w\']+$', data ) == None:
            raise forms.ValidationError("Event names need to have only numbers and letters in them.  No spaces.  Use the long name for the event name for people.")
        if len(data) == 0:
            raise forms.ValidationError( "Event names need to have something, even if it is an initial." )
        return data
   
    
class PersonForm(ModelForm):
    gender = PSDMultipleChoiceField(choices=getPSDCheckboxOptions("Gender"), widget=PSDCheckboxSelectMultiple, label="Gender")
    seek_gender = getSeekFormField("Gender")
    seeking_primary = forms.BooleanField(required=False)
    kinky = forms.BooleanField(required=False)
    age = forms.IntegerField(widget=forms.TextInput(attrs={'size': 5}))
    seek_age_min =  forms.IntegerField(widget=forms.TextInput(attrs={'size': 5}))
    seek_age_max =  forms.IntegerField(widget=forms.TextInput(attrs={'size': 5}))
    seek_kinkiness = forms.ChoiceField(choices=getPSDCheckboxOptions("Kinkinesses"), initial='EI', required=False)

    class Meta:
        model = Person

    def clean_first_name(self):
        data = self.cleaned_data['first_name']
        return clean_string(data)
    
    def clean_last_name(self):
        data = self.cleaned_data['last_name']
        # just take last initial.
        data = clean_string(data)
        if len(data) > 0:
            data = data[0]
        return data

   
    def clean(self):
        cleaned_data = self.cleaned_data
        
        # Always return the full collection of cleaned data.
        return cleaned_data
    
    

class DateRecordForm(ModelForm):
    psdid = forms.CharField(widget=forms.TextInput(attrs={'side':8}))
    other_psdid = forms.CharField(widget=forms.TextInput(attrs={'side':8}))

    class Meta:
        model = DateRecord







class MatchRecordForm(ModelForm):
    psdid1 = forms.CharField(widget=forms.TextInput(attrs={'side':8}))
    psdid2 = forms.CharField(widget=forms.TextInput(attrs={'side':8}))
#    event = forms.CharField(max_length=15, blank=True)
#    match = forms.PositiveIntegerField(verbose_name="Likability")
#    gay_ok = forms.BooleanField(verbose_name="Gay Round Okay")
#    str_ok = forms.BooleanField(verbose_name="Straight Round Okay")

    class Meta:
        model = MatchRecord



PAYMENT_SYSTEMS = ( ('PP', 'Paypal'), ('WP', 'WePay') )

class EventForm(ModelForm):
    wepay_email = forms.EmailField(required=False)
    payment_systems = PSDMultipleChoiceField(required=False, choices=PAYMENT_SYSTEMS, widget=PSDCheckboxSelectMultiple)
    
    def clean_event(self):
        data = self.cleaned_data['event']
        data = super_clean_string(data)
        return data
    
class RegRecordForm(ModelForm):             
    location = PSDMultipleChoiceField(required=False, choices=getPSDCheckboxOptions("Location"), widget=PSDCheckboxSelectMultiple)
    nickname = forms.CharField(widget=forms.TextInput(attrs={'size': 25}))
    email = forms.EmailField() 
    referred_by = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 45}))
    comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols':40,'rows':3}))

    def clean_nickname(self):
        data = self.cleaned_data['nickname']
        data = clean_string(data)

        # Always return the cleaned data, whether you have changed it or not.
        return data
    
    
    class Meta:
        model = RegRecord
#        exclude = ('people','paid','psdid')




class InitializeUserForm(forms.Form):
    """
    For adding a user account and regrecord for a person before they have 
    actually filled out any form or given any info.   Designed for pre-reg'ing
    conference lists and the like. (Made for openSF in 2012)
    """
    nickname = forms.CharField(widget=forms.TextInput(attrs={'size': 25}))
    email = forms.EmailField()
    is_group = forms.BooleanField(required=False)

        
        
class PostEmailForm(forms.Form):
    subject = forms.CharField(widget=forms.TextInput( attrs={'size':80} ))
    body = forms.CharField(widget=forms.Textarea(attrs={'cols': 80, 'rows': 40}))
    send_matches = forms.BooleanField(required=False)
    really_send = forms.BooleanField(required=False)
    


class SubgroupEmailForm(forms.Form):
    subject = forms.CharField(widget=forms.TextInput( attrs={'size':80} ))
    psdids = forms.CharField(widget=forms.Textarea(attrs={'cols': 80, 'rows': 3}))
    body = forms.CharField(widget=forms.Textarea(attrs={'cols': 80, 'rows': 40}))
    send_matches = forms.BooleanField(required=False)
    really_send = forms.BooleanField(required=False)
    





TOPICS = (
    ('general', 'General'),
    ('matching', 'Matching'),
    ('ops', 'Food/Location/Timing'),
    ('site', 'PSD website'),
    ('other', 'Other'),
        )

class FeedbackForm(forms.Form):
    topic = forms.ChoiceField(required=False, choices=TOPICS)
    message = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols':40,'rows':3}))
    email = forms.EmailField(required=False, label="Your address (optional)")
    psdid = forms.CharField(required=False, label="Your PSDID (optional)")



class NextSheetForm(forms.Form):
    psdid = forms.CharField(required=True, label="PSDID")


class PersonSearchForm(forms.Form):
    psdid = forms.CharField(required=False, label="PSDID")
    email = forms.EmailField( required=False, label="email"  )
    name = forms.CharField( required=False, label="name" )
    
    def clean(self):
        cleaned_data = super(PersonSearchForm, self).clean()
        if len(cleaned_data) >= 3:
            psdid = cleaned_data.get("psdid")
            email = cleaned_data.get("email")
            name = cleaned_data.get("name")
            
            if psdid == "" and email == "" and name == "":
                val_error = "You need to enter either a PSD ID, an email address, or a name (or part of name)"
                raise forms.ValidationError(val_error)
        return cleaned_data


class PSDIDorEmailForm(forms.Form):
    psdid = forms.CharField(required=False, label="PSDID")
    email = forms.EmailField( required=False, label="email"  )

    def clean(self):
        cleaned_data = super(PSDIDorEmailForm, self).clean()
        if len(cleaned_data) >= 2:
            val_error = 'Neither the PSD ID or the email locates a User account'
            usr = None
            psdid = cleaned_data.get("psdid")
            email = cleaned_data.get("email")
            if psdid == "" and email == "":
                val_error = "You need to enter either a PSD ID or email address"
            else:    
                if not (psdid is None):
                    try:
                        usr = User.objects.get( username=psdid )
                    except User.DoesNotExist:
                        pass
                    except Exception as ex:
                        val_error = "Weird error: %s" % (ex, )
                    
                
                if usr is None:                
                    try:
                        usr = User.objects.get( email=email )
                    except User.DoesNotExist:
                        pass
                    except Exception as ex:
                        val_error = "Weird error: %s" % (ex, )
                
            if not (usr is None):
               cleaned_data["user"] = usr
            else:
                raise forms.ValidationError(val_error)
        return cleaned_data
    
    

INCLUDE_OPTIONS = ( ("In", "Folks checked off as here" ), 
                        ("NotNo", "Everyone that has not cancelled" ),
                        ("paid", "Folks marked as paid or pending" ),
                         )


class ScheduleForm(forms.Form):
    rounds = forms.IntegerField(widget=forms.TextInput(attrs={'size': 5}), initial=12)
    trials = forms.IntegerField(widget=forms.TextInput(attrs={'size': 5}), initial=1)
    include = forms.ChoiceField( choices=INCLUDE_OPTIONS )


class PrintSchedulesForm(forms.Form):    
    include = forms.ChoiceField( choices=INCLUDE_OPTIONS )


class MakeTableTableForm(forms.Form):
    N = forms.IntegerField(widget=forms.TextInput(attrs={'size': 5}), initial=75)
    statOK = forms.CharField(required=False, label="Stationary Tables (comma separated, ranges)")
    groupOK = forms.CharField(required=False, label="Group OK Tables (comma separated, ranges)")
    
    
class MakeRecessForm(forms.Form):
    kind = forms.CharField(widget=forms.TextInput(attrs={'size':20}), initial="break") 
    breaktext = forms.CharField(required=False, widget=forms.Textarea(attrs={'size': 45, 'rows':4}), initial="5,6,7\n6,7,8\n7,8,9" ) 
    

 
class MultiBreakForm(forms.Form):
    reason = forms.CharField(widget=forms.TextInput(attrs={'size':50}), initial="hand break") 
    
class BreakForm(ModelForm):
    notes = forms.CharField(widget=forms.TextInput(attrs={'size':50}), required=False) 
    
    class Meta:
        model = BreakRecord
        
    
class CruiseForm(forms.Form):
    other_psdid = forms.CharField(required=True, label="OTHER PSDID")
        
    
