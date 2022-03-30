import os
import json
from collections import OrderedDict
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "calibri"
plt.rcParams['font.size'] = 12


def cdate(date_time_str):
    return datetime.strptime(date_time_str.split("T")[0], '%Y-%m-%d').date()


def get_data(data_fields, product_id=None, date_min=None, date_max=None, label=None):
    """

    :param data_fields:
    :param product_id:
    :param date_min:
    :param date_max:
    :param label: [Achat, ApproStock, Inventaire]
    :return:
    """
    if label not in ['Achat', 'ApproStock', 'Inventaire', None]:
        raise Exception("Label incorrect")  # pour moi

    ds = [d for d in data_fields]

    if product_id is not None:
        ds = [d for d in ds if d["product"] == product_id]

    if date_min is not None:
        ds = [d for d in ds if date_min <= d["date"]]

    if date_max is not None:
        ds = [d for d in ds if d["date"] <= date_max]

    if label is not None:
        ds = [d for d in ds if d["label"] == label]

    return ds


def sum_data(value, data_fields, product_id=None, date_min=None, date_max=None, label=None):
    """

    :param value: [price, purchase_cost, amount]
    :param data_fields:
    :param product_id:
    :param date_min:
    :param date_max:
    :param label:
    :return:
    """
    if value not in ['price', 'purchase_cost', 'amount', None]:
        raise Exception("Valeur incorrecte")  # pour moi

    ds = get_data(data_fields=data_fields,
                  product_id=product_id,
                  date_min=date_min,
                  date_max=date_max,
                  label=label)

    values = [float(d[value]) for d in ds]

    if len(values) > 0:
        return np.sum(values)
    else:
        return 0.


directory = "C:/Users/camil/Desktop/ARanger/Epicerie/AG/2022_03/"
# MONTHS = ["Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre",
#          "Decembre"]
MONTHS = ["{0:02d}".format(i + 1) for i in range(12)]

colors = [(198 / 255, 76 / 255, 40 / 255),
          (152 / 255, 163 / 255, 62 / 255),
          (223 / 255, 168 / 255, 48 / 255),
          (88 / 255, 117 / 255, 221 / 255)]

with open('data.json', encoding='utf-8', errors='ignore') as f:
    print(f.readline())  # erreur ligne ?

    todays_date = date.today()

    date_min_filter = date(todays_date.year - 1, todays_date.month, 1)
    date_max_filter = todays_date + relativedelta(day=31)

    data = json.load(f, strict=False)

    data_changestock = [d for d in data if d['model'] == "base.changestockop"]
    data_purchase = [d for d in data if d['model'] == "base.purchase"]
    data_product = [d for d in data if d['model'] == "base.product"]
    data_purchasedetailop = [d for d in data if d['model'] == "base.purchasedetailop"]
    data_approcompteop = [d for d in data if d['model'] == "base.approcompteop"]
    data_foyers = [d for d in data if d['model'] == "base.household"]
    data_provider = [d for d in data if d['model'] == "base.provider"]

    data_changestock_achat = [d for d in data_changestock if d['fields']['label'] == 'Achat']

    # convert date
    for d0 in [data_changestock, data_purchase, data_approcompteop]:
        for d in d0:
            d['fields']['date'] = cdate(d['fields']['date'])
    for d in data_foyers:
        d['fields']['date'] = cdate(d['fields']['date'])
        if d['fields']['date_closed'] is not None:
            d['fields']['date_closed'] = cdate(d['fields']['date_closed'])

    # data_purchasedetailop_id_unique = np.unique([d["fields"]['purchase'] for d in data_purchasedetailop])

    data_changestock_fields = [d["fields"] for d in data_changestock]
    data_approcompteop_fields = [d["fields"] for d in data_approcompteop]

    # create dict of products
    dic_product = OrderedDict()
    for d in data_product:
        d_i = d["fields"]
        d_i["name"] = d_i["name"].capitalize()
        dic_product[d["pk"]] = d_i

    # =======================================
    # foyers
    # =======================================

    # portefeuilles et cotisation
    subscription = []
    account_pos = []
    account_neg = []
    nb_foyers = 0
    for d in data_foyers:
        if d['fields']['date_closed'] is None and d['fields']['activated']:
            nb_foyers += 1
            account = float(d["fields"]["account"])
            if account >= 0:
                account_pos.append(account)
            else:
                account_neg.append(account)

            subscription.append(float(d["fields"]["subscription"]))

    # evolution du nombre de foyers
    dates_foyer = []
    evolution_foyer = []
    for d in data_foyers:
        if d['fields']['date'] not in dates_foyer:
            dates_foyer.append(d['fields']['date'])
        if d['fields']['date_closed'] is not None:
            dates_foyer.append(d['fields']['date_closed'])

    dates_foyer.sort()
    evolution_foyer = [0] * len(dates_foyer)

    for d in data_foyers:
        date_0 = d['fields']['date']
        date_1 = d['fields']['date_closed']
        for di, date_i in enumerate(dates_foyer):
            if date_0 <= date_i:
                evolution_foyer[di] += 1
        if date_1 is not None:
            for di, date_i in enumerate(dates_foyer):
                if date_i <= date_1:
                    evolution_foyer[di] -= 1


    dates_foyer_graph = [(d - dates_foyer[0]).days for d in dates_foyer]

    fig, ax = plt.subplots(figsize=(10, 5))

    fig.subplots_adjust(left=0.08, right=0.92, bottom=0.1, top=0.95)
    ax.plot(dates_foyer_graph, evolution_foyer, color=colors[0])

    ax.text(0.5, 0.2, "Nombre de foyers : {0:d}".format(nb_foyers),
            color=colors[0], transform=ax.transAxes, ha='center')

    ax.set_ylabel("Nombre de foyers", color=colors[0])
    # ax_b.set_ylabel("Pourcentage cumulé par tranches de 5 € [%]", color=colors[1])

    x_ticks = []
    x_ticklabels = []
    for year in range(dates_foyer[0].year, dates_foyer[-1].year + 2):
        for month in [1, 4, 7, 10]:
            date_i = datetime(year, month, 1, 0).date()
            if dates_foyer[0] <= date_i <= dates_foyer[-1]:
                x_ticks.append((date_i - dates_foyer[0]).days)
                x_ticklabels.append("{0:02d}/{1:s}".format(month, str(year)[-2:]))

    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_ticklabels)

    ax.set_ylim(ymin=0)

    # plt.show()
    # plt.close()

    path_img = os.path.join(directory, "figure_foyers.png")
    print("Ecriture {0:s}".format(path_img))
    plt.savefig(path_img)

    # =======================================
    # produits
    # =======================================

    stocks_dic = OrderedDict()

    for p in dic_product.values():

        if p["activated"]:

            stocks_dic[p["name"]] = {}
            for k in ['price', 'stock']:
                stocks_dic[p["name"]][k] = float(p[k])
            stocks_dic[p["name"]]["stock_value"] = stocks_dic[p["name"]]['price'] * stocks_dic[p["name"]]['stock']

    stock_value = np.sum([p['stock_value'] for p in stocks_dic.values()])
    stock_value_sort = np.argsort([p['stock_value'] for p in stocks_dic.values()])

    fig, ax = plt.subplots(figsize=(10, 5))

    fig.subplots_adjust(left=0.35, right=0.95, bottom=0.10, top=0.95)

    bar_width = 0.7

    nb_product_plot = 10
    index = list(range(nb_product_plot)) + list(range(nb_product_plot + 1, nb_product_plot * 2 + 1))

    ids_selection = list(stock_value_sort[:nb_product_plot]) + list(stock_value_sort[-nb_product_plot:])

    index_name = [[p for p in stocks_dic][i] for i in ids_selection]

    product_plots = []
    product_plots.append([[p['stock_value'] for p in stocks_dic.values()][i] for i in ids_selection])
    product_class_1 = list(range(1, nb_product_plot + 1))[::-1]
    product_class_0 = [-i for i in list(range(1, nb_product_plot + 1))[::-1]]
    product_class = product_class_0 + product_class_1
    product_plots.append(product_class)

    l1 = ax.barh(index, product_plots[0], bar_width, color=colors[0])

    for ii, i in enumerate(index):

        if ii >= nb_product_plot:
            ax.text(product_plots[0][ii], i, "       {0:.0f} €".format(product_plots[0][ii]),
                    va='center', ha='left')
            ax.text(product_plots[0][ii], i, " {0:d}".format(product_plots[1][ii]),
                    va='center', ha='left', color=colors[1], fontweight='bold')
        else:
            ax.text(product_plots[0][ii], i, "{0:.0f} €       ".format(product_plots[0][ii]),
                    va='center', ha='right')
            ax.text(product_plots[0][ii], i, "{0:d} ".format(product_plots[1][ii]),
                    va='center', ha='right', color=colors[1], fontweight='bold')

    ax.set_xlim(xmin=-150, xmax=500)

    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    ax.set_yticks(index)
    ax.set_yticklabels(index_name)

    ax.set_xlabel("Valeur du stock [€] ")

    # plt.show()
    # plt.close()

    path_img = os.path.join(directory, "figure_stocks.png")
    print("Ecriture {0:s}".format(path_img))
    plt.savefig(path_img)

    product_nb_achats = []
    nb_products = 0
    for p, p_field in dic_product.items():
        achat_nb = len(
            get_data(data_changestock_fields, product_id=p, date_min=date_min_filter, date_max=date_max_filter,
                     label='Achat'))
        product_nb_achats.append(achat_nb)

        if p_field['visible'] and p_field['activated']:
            nb_products += 1

    product_nb_achats_sort = np.argsort(product_nb_achats)[::-1][:15][::-1]

    product_nb_achats_best = [[[d["name"] for d in dic_product.values()][i] for i in product_nb_achats_sort],
                              [product_nb_achats[i] for i in product_nb_achats_sort]]

    fig, ax = plt.subplots(figsize=(10, 5))

    fig.subplots_adjust(left=0.35, right=0.95, bottom=0.10, top=0.95)
    index = np.arange(len(product_nb_achats_best[0])) + 1
    bar_width = 0.7

    l1 = ax.barh(index, product_nb_achats_best[1], bar_width, color=colors[0])

    for ii, i in enumerate(index):
        nb_i = product_nb_achats_best[1][ii]
        ax.text(product_nb_achats_best[1][ii], i, "       [{0:d}/an, {1:.0f}/mois]".format(nb_i, nb_i / 12.),
                va='center', ha='left')

        ax.text(product_nb_achats_best[1][ii], i, " {0:d}".format(index[-ii - 1]),
                va='center', ha='left', color=colors[1], fontweight='bold')

    ax.set_xlim(xmax=200)

    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    ax.set_yticks(index)
    ax.set_yticklabels(product_nb_achats_best[0])

    ax.set_xlabel("Nombre de fois achetés [/an] ")

    # plt.show()
    # plt.close()

    path_img = os.path.join(directory, "figure_produits.png")
    print("Ecriture {0:s}".format(path_img))
    plt.savefig(path_img)

    # =======================================
    # paniers
    # =======================================

    # affichage dev
    # for p in data_changestock_achat[:10]:
    #     print(p)
    # for p in data_purchase[:10]:
    #     print(p)
    # for p in data_purchasedetailop[:10]:
    #     print(p)

    print("Calcul des paniers")
    # dictionnaire panier par jour par foyer
    dic_date_household_purchase = OrderedDict()

    for p in data_purchase:
        p_date = p['fields']['date']
        p_household = p['fields']['household']
        p_purchase_pk = p['pk']
        if p_date not in dic_date_household_purchase:
            dic_date_household_purchase[p_date] = {}
        if p_household not in dic_date_household_purchase[p_date]:
            dic_date_household_purchase[p_date][p_household] = [p_purchase_pk]
        else:
            dic_date_household_purchase[p_date][p_household].append(p_purchase_pk)

    # dictionnaire achat par jour par foyer
    dic_date_household_changestockop = OrderedDict()
    dic_date_paniers_prix = OrderedDict()
    for p0_key, p0 in dic_date_household_purchase.items():
        dic_date_household_changestockop[p0_key] = {}
        dic_date_paniers_prix[p0_key] = []
        for p1_key, p1 in p0.items():
            pks_changestockop = [d['pk'] for d in data_purchasedetailop if d['fields']['purchase'] in p1]
            dic_date_household_changestockop[p0_key][p1_key] = pks_changestockop

            panier_prix = [float(d['fields']['price']) for d in data_changestock_achat if d['pk'] in pks_changestockop]
            if len(panier_prix) != len(pks_changestockop):
                raise Exception("Erreur achat non trouve")

            dic_date_paniers_prix[p0_key].append(-sum(panier_prix))

    print("Fin du calcul des paniers")

    panier_max = 150
    paniers_prix = []
    paniers_prix_all = []
    for date_i, paniers in dic_date_paniers_prix.items():

        for p in paniers:
            if 0. < p <= panier_max:
                paniers_prix_all.append(p)

        if date_min_filter <= date_i <= date_max_filter:
            for p in paniers:
                if 0. < p <= panier_max:
                    paniers_prix.append(p)

    paniers_prix_bnds = [1, 5, ]

    hist, bin_edges = np.histogram(paniers_prix, bins=30, range=(0, panier_max))  # pas de 5 €
    hist = np.asarray(hist, dtype=float)
    hist /= float(len(paniers_prix)) / 100.  # en pourcent

    fig, ax = plt.subplots(figsize=(10, 5))

    fig.subplots_adjust(left=0.08, right=0.92, bottom=0.1, top=0.95)
    ax.bar(bin_edges[:-1] + (bin_edges[1] - bin_edges[0]) / 2, hist, width=bin_edges[1] - bin_edges[0], color=colors[0],
           alpha=1.0,
           edgecolor='k', linewidth=1)
    ax.set_xticks([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 75, 100, 125, panier_max])
    ax.set_xlim(xmin=0, xmax=panier_max)
    ax.text(0.5, 0.8, "Nombre total de paniers depuis 1 an : {0:d}".format(len(paniers_prix)),
            color=colors[0], transform=ax.transAxes, ha='center')
    ax.text(0.5, 0.75, "Prix moyen d'un panier depuis 1 an : {0:.0f} €".format(np.mean(paniers_prix)),
            color=colors[0], transform=ax.transAxes, ha='center')

    ax_b = ax.twinx()
    ax_b.plot(bin_edges[:-1] + (bin_edges[1] - bin_edges[0]) / 2, np.cumsum(hist), color=colors[1])

    ax_b.plot([bin_edges[0], bin_edges[-1]], [50, 50], color=colors[1], ls='--')
    ax_b.plot([bin_edges[0], bin_edges[-1]], [75, 75], color=colors[1], ls='--')
    ax_b.plot([bin_edges[0], bin_edges[-1]], [100, 100], color=colors[1], ls='--')

    ax.tick_params(axis='y', labelcolor=colors[0])
    ax_b.tick_params(axis='y', labelcolor=colors[1])

    ax.set_ylabel("Pourcentage par tranche de 5 € [%]", color=colors[0])
    ax_b.set_ylabel("Pourcentage cumulé par tranche de 5 € [%]", color=colors[1])

    # plt.show()
    # plt.close()

    path_img = os.path.join(directory, "figure_paniers.png")
    print("Ecriture {0:s}".format(path_img))
    plt.savefig(path_img)

    # =======================================
    # fonctionnement epicerie
    # =======================================

    dates = []
    dates_short = []
    dates_long = []
    achats = []  # adherent
    appros = []  # epicerie
    invent = []  # epicerie
    apprus = []  # adherent

    for year in [2019, 2020, 2021, 2022]:

        for month in range(1, 12 + 1):

            if year == 2019 and month <= 8:
                continue
            if year >= todays_date.year:
                if month > todays_date.month:
                    continue

            date_min = datetime(year, month, 1, 0).date()
            date_max = (datetime(year, month, 1, 23, 59) + relativedelta(day=31)).date()

            dates_i = "{0:02d}".format(len(dates_short) + 1)
            dates.append(dates_i + " : " + MONTHS[month - 1] + "/" + "{0:d}".format(year)[-2:])
            dates_short.append(dates_i)
            dates_long.append(MONTHS[month - 1] + "/" + "{0:d}".format(year))

            achats.append(sum_data('price', data_changestock_fields,
                                   product_id=None,
                                   date_min=date_min,
                                   date_max=date_max,
                                   label='Achat'))

            appros.append(sum_data('purchase_cost', data_changestock_fields,
                                   product_id=None,
                                   date_min=date_min,
                                   date_max=date_max,
                                   label='ApproStock'))

            invent.append(sum_data('purchase_cost', data_changestock_fields,
                                   product_id=None,
                                   date_min=date_min,
                                   date_max=date_max,
                                   label='Inventaire'))

            apprus.append(sum_data('amount', data_approcompteop_fields,
                                   product_id=None,
                                   date_min=date_min,
                                   date_max=date_max,
                                   label=None))

    achats = np.array(achats)
    achats *= -1

    fig, axs = plt.subplots(2, figsize=(21, 10))

    fig.subplots_adjust(left=0.1, right=0.95, bottom=0.25, top=0.95)
    index = np.arange(len(dates)) + 1
    bar_width = 0.2

    ax2 = axs[0]
    ax1 = axs[1]

    legs = ["Inventaire", "Approvisionnement", "Achats", "Comptes"]

    l1 = ax1.bar(index - 1.5 * bar_width, invent, bar_width, color=colors[0])
    l2 = ax1.bar(index - 0.5 * bar_width, appros, bar_width, color=colors[1])
    l3 = ax1.bar(index + 0.5 * bar_width, achats, bar_width, color=colors[2])
    l4 = ax1.bar(index + 1.5 * bar_width, apprus, bar_width, color=colors[3])

    invent_cum = np.cumsum(invent)
    appros_cum = np.cumsum(appros)
    achats_cum = np.cumsum(achats)
    apprus_cum = np.cumsum(apprus)

    ax2.plot(index, invent_cum, color=colors[0])
    ax2.plot(index, appros_cum, color=colors[1])
    ax2.plot(index, achats_cum, color=colors[2])
    ax2.plot(index, apprus_cum, color=colors[3])

    ax2.text(0.2, 0.9, legs[0] + " : {0:.0f} €".format(invent_cum[-1]),
             color=colors[0], transform=ax2.transAxes, ha='right')
    ax2.text(0.2, 0.8, legs[1] + " : {0:.0f} €".format(appros_cum[-1]),
             color=colors[1], transform=ax2.transAxes, ha='right')
    ax2.text(0.2, 0.7, legs[2] + " : {0:.0f} €".format(achats_cum[-1]),
             color=colors[2], transform=ax2.transAxes, ha='right')
    ax2.text(0.2, 0.6, legs[3] + " : {0:.0f} €".format(apprus_cum[-1]),
             color=colors[3], transform=ax2.transAxes, ha='right')

    ax1.legend([l1, l2, l3, l4], legs, loc='upper center', ncol=4)

    ax1.plot([index[0] - 0.5, index[-1] + 0.5], [0, 0], color='k', lw=1)
    ax2.plot([index[0] - 0.5, index[-1] + 0.5], [0, 0], color='k', lw=1)

    ax1.set_xticks(index)
    ax1.set_xticklabels(dates, rotation=90)
    # ax1.set_ylim(ymin=-100, ymax=3000)

    # ax.set_title("Année {0:d}".format(year))

    ax1.set_ylabel("Montant [€]")
    ax2.set_ylabel("Montant cumulé [€]")

    cell_text = [["{0:.0f}".format(t) for t in a] for a in [invent, appros, achats, apprus]]

    path_data = os.path.join(directory, "figure_general.csv")
    print("Ecriture {0:s}".format(path_data))
    fw = open(path_data, 'w')
    fw.write(",".join(["{0:>25}".format(t) for t in [""] + dates_long]) + "\n")
    for cell_text_ii, cell_text_i in enumerate(cell_text):
        fw.write(",".join(["{0:>25}".format(t) for t in [legs[cell_text_ii]] + cell_text_i]) + "\n")
    fw.close()

    ta = ax1.table(cellText=cell_text,
                   rowLabels=legs,
                   rowColours=colors,
                   colLabels=dates_short,
                   bbox=[0, -0.7, 1.0, 0.35])
    # ta.auto_set_font_size(False)
    # ta.set_fontsize(10)

    # plt.show()
    # plt.close()

    path_img = os.path.join(directory, "figure_general.png")
    print("Ecriture {0:s}".format(path_img))
    plt.savefig(path_img)

    # Affichage pour rapport

    print("====================")
    print("Rapport")
    print("====================")
    print("Ouvert depuis {} mois.".format(dates_short[-1]))
    print("Nombre de foyers actifs {}.".format(nb_foyers))
    print("Nombre de références {}.".format(nb_products))
    print("Nombre de fournisseurs {}.".format(len(data_provider)))
    print("Nombre de paniers depuis le début {}.".format(len(paniers_prix_all)))
    print("Nombre de paniers depuis 1 an {}.".format(len(paniers_prix)))
    print("Prix du panier moyen depuis le début {0:.1f} €.".format(np.mean(paniers_prix_all)))
    print("Prix du panier moyen depuis 1 an {0:.1f} €.".format(np.mean(paniers_prix)))
    print(
        "Valeur totale des achats faits par les adhérents depuis le début {0:.0f} €.".format(np.sum(paniers_prix_all)))
    print("Valeur totale des achats faits par les adhérents depuis 1 an {0:.0f} €.".format(np.sum(paniers_prix)))

    print("====================")
    print("Valeur du stock : {0:.0f} €".format(stock_value))
    print("Somme des portefeuilles en positif : {0:.0f} € ({1:d} portefeuilles)".format(np.sum(account_pos),
                                                                                        len(account_pos)))
    print("Somme des portefeuilles en négatif : {0:.0f} € ({1:d} portefeuilles)".format(-np.sum(account_neg),
                                                                                        len(account_neg)))
    print("Somme des cotisations : {0:.0f} € ({1:d} cotisations)".format(np.sum(subscription),
                                                                         len(subscription)))
    print("====================")
