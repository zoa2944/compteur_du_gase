from django import forms

from .models import *

class HouseholdList(forms.Form):
    household = forms.ModelChoiceField(label='Sélectionnez votre compte : ',
                                       queryset=Household.objects.all())

class ProviderList(forms.Form):
    provider = forms.ModelChoiceField(label='Sélectionnez un fournisseur : ',
                                      queryset=Provider.objects.all())

class ApproCompteForm(forms.Form):
    amount = forms.DecimalField(label="Combien d'argent avez-vous virez sur le compte du GASE ?", decimal_places=2)

# utilisé pour appro stock
class ApproForm(forms.Form):
    def __init__(self, prod, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for p in prod.get_products():
            self.fields[str(p.pk)] = forms.DecimalField(label=p.name, required=False)

# utilisé pour inventaire
class ProductList(forms.Form):
    def __init__(self, pdts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for p in pdts:
            self.fields[str(p.pk)] = forms.DecimalField(label=p.name, required=False)

class ProductForm(forms.ModelForm):
    stock = forms.DecimalField(disabled=True, initial=0) # initial=0 pour création nveau pdt
    value = forms.DecimalField(disabled=True, required=False, decimal_places=2,
                               label="Valeur du stock (en €)")

    class Meta:
        model = Product
        exclude = []

class MemberForm(forms.ModelForm):
    address = forms.CharField(disabled=True, max_length=200, required=False,
                              label="Adresse")

    class Meta:
        model = Member
        exclude = []

class ProviderForm(forms.ModelForm):
    class Meta:
        model = Provider
        exclude = []