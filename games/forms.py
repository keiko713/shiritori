from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.forms import BoundField
from django import forms

class BootstrapOutputMixin:

    def as_bootstrap_horizontal(self):
        """
        Returns this form rendered as HTML <div class="control-group">s 
            -- excluding the <fieldset></fieldset>.
        Also, it provides the non field alerts before fields.
        This form will be bootstrap 2.0 horizonal forms:
            http://twitter.github.com/bootstrap/base-css.html?#forms

        In template file, you can render a formset like following:
        <form class="form-horizontal" action="" method="post">
          <fieldset>
            {{ form.as_bootstrap_horizonal }}
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Submit</button>
            </div>
          </fieldset>
        </form>
        """
        output, hidden_fields = [], []
        error_row = u'<div class="alert alert-error alert-login">%s</div>'
        # self.non_field_errors returns <ul class="errorlist">
        top_errors = self.non_field_errors()

        for name, field in self.fields.items():
            bf = BoundField(self, field, name)
            if bf.is_hidden:
                # for hidden fields
                if bf.errors:
                    # for hidden fields, add errors to top_errors
                    hidden_errors = self.error_class([conditional_escape(error) for error in bf.errors])
                    top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in hidden_errors])
                hidden_fields.append(unicode(bf))
            else:
                # for control-group tag
                if bf.errors:
                    output.append(u'<div class="control-group error">')
                else:
                    output.append(u'<div class="control-group">')

                # for label
                output.append(bf.label_tag(attrs={'class': 'control-label'}))
                # for controls div tag
                output.append(u'<div class="controls">')
                # input tag, textarea tag, etc...
                output.append(unicode(bf))

                # for error
                if bf.errors:
                    output.append(u'<ul class="errorlist help-block">')
                    for error in bf.errors:
                        output.append(u'<li>%s</li>' % conditional_escape(force_unicode(error)))
                    output.append(u'</ul>')

                # for controls div tag
                output.append(u'</div><!-- /controls -->')
                # for control-group div tag
                output.append(u'</div><!-- /control-group -->')

        # insert top error messages
        if top_errors:
            output.insert(0, error_row % force_unicode(top_errors))

        # append hidden fields to the end of the output
        if hidden_fields:
            for hf in hiddenfields:
                output.append(hf)

        return mark_safe(u'\n'.join(output))


class MyUserCreationForm(UserCreationForm, BootstrapOutputMixin):
    # override the field definition from super class (UserCreationForm)
    username_attrs = {
        'class': 'span3',
        'placeholder': 'User Name',
    }
    password1_attrs = {
        'class': 'span3',
        'placeholder': 'Password',
    }
    password2_attrs = {
        'class': 'span3',
        'placeholder': 'Password confirmation',
    }
    username = forms.RegexField(label=_("User Name"), max_length=30, regex=r'^[\w.@+-]+$',
        help_text = _("Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only."),
        error_messages = {'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")},
        widget=forms.TextInput(attrs=username_attrs))
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput(attrs=password1_attrs))
    password2 = forms.CharField(label=_("Password confirmation"),
        help_text = _("Enter the same password as above, for verification."),
        widget=forms.PasswordInput(attrs=password2_attrs))


class MyAuthenticationForm(AuthenticationForm, BootstrapOutputMixin):
    # override the field definition from super class (AuthenticationForm)
    username_attrs = {
        'class': 'span3',
        'placeholder': 'User Name',
    }
    password_attrs = {
        'class': 'span3',
        'placeholder': 'Password',
    }
    username = forms.CharField(label=_("Username"), max_length=30,
        widget=forms.TextInput(attrs=username_attrs))
    password = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput(attrs=password_attrs))

    def __init__(self, request=None, *args, **kwargs):
        AuthenticationForm.__init__(self, request=None, *args, **kwargs)

