import mysql.connector 
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import make_aware

from base.models import *

# Attention, ce script supprime tout avant de migrer ! (sauf les unités)


# PERSONNALISER CES VARIABLES

user = "root"
password = "neuneu"
database = "gase"

prefix="_inde_"

# can be PRODUITS or REFERENCES
product_table = "PRODUITS"

create_unit=True #todo try to get them
migrate_categories=False
migrate_providers=False
migrate_products=False
migrate_members=False
migrate_appro_comptes=False
migrate_change_stock=False
migrate_achats=True


# FIN DE LA PERSONALISATION


mydb = mysql.connector.connect(
    host="localhost",
    user=user,
    passwd=password,
    database=database
)
mycursor = mydb.cursor()


## Unités ##

if (create_unit):
    print('Creating Unit')
    vrac_unit=Unit(name="kg/L", vrac=True, pluralize=False)
    vrac_unit.save()
    non_vrac_unit=Unit(name="unité", vrac=False, pluralize=False)
    non_vrac_unit.save()


## Catégories ##

if (migrate_categories):
    print('Migrating Categories')
    Category.objects.all().delete()
    mycursor.execute("SELECT * FROM " + prefix + "CATEGORIES")
    myresult = mycursor.fetchall()
    for x in myresult:
        # seulement les visibles
        if (x[4] == 1):
            Category(id=x[0], name=x[1]).save()


## Fournisseurs ##

if (migrate_providers):
    print('Migrating Providers')
    Provider.objects.all().delete()
    mycursor.execute("SELECT * FROM " + prefix + "FOURNISSEURS")
    myresult = mycursor.fetchall()
    for x in myresult:
        # seulement les visibles
        if (x[10] == 1):
            fax = '' if (x[7] == '') else ('Fax : ' + x[7])
            contact="\n".join([y for y in [x[2], x[3], x[4], x[5], x[6], fax]
                               if y != ''])
            Provider(id=x[0], name=x[1], contact=contact, comment=x[9]).save()


## Produits ##

if (migrate_products):
    print('Migrating Products')
    Product.objects.all().delete()
    mycursor.execute("SELECT * FROM " + prefix + product_table)
    myresult = mycursor.fetchall()
    for x in myresult:
        comment = x[9] if (x[8] == '') else ('Code fournisseur : ' + x[8] + '\n' + x[9])
        unit = vrac_unit if (x[3]) else non_vrac_unit
        alert= x[11] if (x[11] != -1) else None
        rqst="SELECT STOCK FROM  {0}STOCKS WHERE ID_REFERENCE='{1}' AND DATE = (SELECT MAX(DATE) FROM {0}STOCKS WHERE ID_REFERENCE='{1}')".format(prefix, x[0])
        mycursor.execute(rqst)
        myresult2 = mycursor.fetchall()
        Product(id=x[0], name=x[1], provider_id=x[2], category_id=x[4], unit=unit,
                price=x[5], pwyw=False, visible=x[7], stock_alert=alert, stock=Decimal(myresult2[0][0]),
                comment=comment).save()


## Adhérents ##

if (migrate_members):
    print('Migrating Members')
    Household.objects.all().delete()
    Member.objects.all().delete()
    mycursor.execute("SELECT * FROM " + prefix + "ADHERENTS")
    myresult = mycursor.fetchall()
    # ignoring x[11] "RECEIVE_ALERT_STOCK"
    for x in myresult:
        # seulement les visibles
        if (x[8] == 1):
            name = x[2] + ' ' + x[1]
            hsld=Household(id=x[0], name=name, address=x[4], comment=x[7], date=x[10])
            rqst="SELECT SOLDE FROM  {0}COMPTES WHERE ID_ADHERENT='{1}' AND DATE = (SELECT MAX(DATE) FROM {0}COMPTES WHERE ID_ADHERENT='{1}')".format(prefix, x[0])
            mycursor.execute(rqst)
            myresult2 = mycursor.fetchall()
            hsld.account=Decimal(myresult2[0][0])
            hsld.save()
            tel = ((x[5] + ' ' + x[6]) if (x[6]) else x[5]) if (x[5]) else x[6]
            Member(name=name, email=x[3], tel=tel, household=hsld, receipt=x[9],
                   stock_alert=False).save()


## Appro Comptes ##

if (migrate_appro_comptes):
    print('Migrating Appro Comptes')
    ApproCompteOp.objects.all().delete()
    mycursor.execute("SELECT * FROM " + prefix + "COMPTES WHERE OPERATION='APPROVISIONNEMENT' ORDER BY DATE ASC")
    myresult = mycursor.fetchall()
    for x in myresult:
        try:
            household=Household.objects.get(id=x[0])
        except ObjectDoesNotExist:
            household=None
        op=ApproCompteOp(household=household, amount=x[4])
        op.save()
        date= make_aware(x[2])
        ApproCompteOp.objects.filter(id=op.pk).update(date=date)


## Appro Stock + Inventaire ##

if (migrate_change_stock):
    print('Migrating Appro Stock + Inventory')
    ChangeStockOp.objects.all().delete()
    mycursor.execute("SELECT * FROM " + prefix + "STOCKS ORDER BY DATE ASC")
    myresult = mycursor.fetchall()
    for x in myresult:
        if (x[2]=='APPROVISIONNEMENT' or x[2]=='INVENTAIRE'):
            try:
                pdt=Product.objects.get(id=x[0])
            except ObjectDoesNotExist:
                pdt=None
            if (x[2]=='APPROVISIONNEMENT'):
                op = ChangeStockOp.create_appro_stock(product=pdt, quantity=Decimal(x[4]))
            if (x[2]=='INVENTAIRE'):
                op = ChangeStockOp.create_inventory(product=pdt, quantity=Decimal(-x[4]))
            op.save()
            date= make_aware(x[3])
            ChangeStockOp.objects.filter(id=op.pk).update(date=date)


## Achats ##

if (migrate_achats):
    print('Migrating Achats')
    Purchase.objects.all().delete()
    PurchaseDetailOp.objects.all().delete()
    mycursor.execute("SELECT * FROM {}ACHATS ORDER BY DATE_ACHAT ASC ".format(prefix))
    myresult = mycursor.fetchall()
    for x in myresult:
        try:
            hsld=Household.objects.get(id=x[2])
        except ObjectDoesNotExist:
            hsld=None
        p=Purchase(id=x[0], household=hsld)
        p.save()
        mycursor.execute("SELECT * FROM {0}STOCKS WHERE ID_ACHAT={1} ORDER BY DATE ASC".format(prefix, x[0]))
        myresult2 = mycursor.fetchall()
        for y in myresult2:
            try:
                pdt=Product.objects.get(id=y[0])
                price=pdt.price * Decimal(-y[4])
            except ObjectDoesNotExist:
                price=0
            pd=PurchaseDetailOp(product_id=y[0], purchase=p, quantity=Decimal(-y[4]), price=price, stock=Decimal(y[1]), label='Achat')
            pd.save()
            date= make_aware(y[3])
            PurchaseDetailOp.objects.filter(id=pd.pk).update(date=date)
        date= make_aware(x[1])
        Purchase.objects.filter(id=p.pk).update(date=date)
