from django.shortcuts import render

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from wsgiref.util import FileWrapper
from django.urls import reverse
import ezdxf
import math
import pandas as pd
import os

# Path to the steel table
PATH_TO_TABLE = '/Users/lorenzocesconetto/PycharmProjects/server_auto_project/AutoProject/home/static/home/tabela_aco.xlsx'


# Create your views here.
def index(request):
    if not request.user.is_authenticated:
        return render(request, 'home/index.html')
        # return render(request, 'home/index.html', {"message": None})

    context = {"user": request.user}
    return render(request, "home/main.html", context)


def login_view(request):
    try:
        username = request.POST["username"]
    except:
        return render(request, "home/index.html", {"fail_message": "Usuário ou senha inválidos."})

    try:
        password = request.POST["password"]
    except:
        return render(request, "home/index.html", {"fail_message": "Usuário ou senha inválidos."})

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "home/index.html", {"fail_message": "Usuário ou senha inválidos."})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return render(request, "home/index.html", {"success_message": "Deslogado com sucesso."})


def sapata_view(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))

    return render(request, "home/sapata.html")


def calculate_sapata_view(request):
    try:
        geometria_sapata = str(request.POST["geometria_sapata"])
    except:
        print('\n\nDeu pau: geometria_sapata\n\n')
        return None
    try:
        fck = float(request.POST["fck"])
    except:
        print('\n\nDeu pau: fck\n\n')
        return None
    try:
        y_conc = float(request.POST["y_conc"])
    except:
        print('\n\nDeu pau: y_conc\n\n')
        return None
    try:
        fyk = float(request.POST["fyk"])
    except:
        print('\n\nDeu pau: fyk\n\n')
        return None
    try:
        normal = float(request.POST["normal"])
    except:
        print('\n\nDeu pau: normal\n\n')
        return None
    try:
        a0 = float(request.POST["a0"])
    except:
        print('\n\nDeu pau: a0\n\n')
        return None
    try:
        b0 = float(request.POST["b0"])
    except:
        print('\n\nDeu pau: b0\n\n')
        return None
    try:
        tensao_lim = float(request.POST["tensao_lim"])
    except:
        print('\n\nDeu pau: tensao_lim\n\n')
        return None
    try:
        y_solo = float(request.POST["y_solo"])
    except:
        print('\n\nDeu pau: y_solo\n\n')
        return None
    try:
        espacamento = float(request.POST["espacamento"])
    except:
        print('\n\nDeu pau: espacamento\n\n')
        return None


    def teto(numero, parametro):
        numero = math.ceil(numero / parametro)
        return round(numero * parametro, 2)


    Yc = 1.4
    fcd = (fck / Yc) / 10  # kN/cm²
    Ys = 1.15
    fyd = (fyk / Ys) / 10  # kN/cm²
    d_a = 7.5
    P = 0.1 * normal

    if geometria_sapata == 'Trapezoidal':
        # Início do cálculo - Trapezoidal
        # Dimensionamento da sapata
        a1 = 1
        a2 = -((a0 / 100) - (b0 / 100))
        a3 = -(normal + P) / tensao_lim
        a = teto((-a2 + (a2 ** 2 - 4 * a1 * a3) ** 0.5) / (2 * a1), 0.05)  # m
        b = teto(a - ((a0 / 100) - (b0 / 100)), 0.05)  # m
        a = 100 * a  # cm
        b = 100 * b  # cm
        # Altura da sapata rígida junto a face do pilar
        H = teto(max([(a - a0), (b - b0)]) / 3, 0.05)  # cm
        # Altura útil da sapata
        d = H - d_a  # cm
        # Altura da sapata na extremdidade
        h0 = max([H / 3, 25])  # cm
        # Inclinação da face superior da sapata
        B = math.atan((H - h0) * 2 / (a - a0)) * 180 / math.pi
        if B <= 30:
            # Tensão máxima sob a sapata
            tensao_max = (normal + P) / (a * b / 10000)  # kN/m²
            if tensao_max <= tensao_lim:
                # Força normal centrada equivalente no pilar
                Neq = (a * b / 10000) * tensao_max - P  # kN
                # Verificação da ruptura do concreto por compressão diagonal no perímetro do pilar
                Vd = 1.4 * normal  # kN
                v = 0.6 * (1 - fck / 250)
                u0 = 2 * (a0 + b0)  # cm
                Vrd2 = 0.45 * u0 * v * fcd * d  # kN
                if Vd <= Vrd2:
                    # Força de tração na armadura longitudinal
                    Tadb = 1.4 * Neq * (a - a0) / (8 * b * d)  # kN/m
                    Tbda = 1.4 * Neq * (b - b0) / (8 * a * d)  # kN/m
                    # Armadura longitudinal inferior
                    Asa = Tadb / fyd  # cm²/m
                    Asb = Tbda / fyd  # cm²/m
                    As_min = 0.0015 * 100 * H  # cm²/m
                    # Tabela que contem os diâmetros nominais das barras de aço
                    tabela_aco = pd.read_excel(PATH_TO_TABLE)

                    def mod(x):
                        if x >= 0:
                            return x
                        else:
                            return -x

                    list_diferencas = []
                    for i in range(0, len(tabela_aco)):
                        area_teste = (math.pi * ((tabela_aco.iloc[i]['Barras'] / 10) ** 2) / 4) * (100 / espacamento)
                        list_diferencas.append([mod(area_teste - As_min), i])
                    diametro = (tabela_aco.iloc[min(list_diferencas)[1]]['Barras'])

                    list_results = [fck, fyk, Yc, Ys, fcd, fyd, y_conc, a0, b0, tensao_lim, y_solo, espacamento,
                                    a, b, H, d, h0, B, tensao_max, Vd, Vrd2, diametro]
                    list_names_variables = ['fck(MPa)', 'fyk(MPa)', 'Coeficiente de segurança do concreto',
                                            'Coef. de segurança do aço',
                                            'fcd(kN/cm²)', 'fyd(kN/cm²)', 'Peso espeífico do concreto(kN/m³)',
                                            'Dim. do pilar em a(cm)',
                                            'Dime. do pilar em b(cm)', 'Tensão limite(kN/m²)',
                                            'Peso específico do solo(kN/m³)',
                                            'Espaçamento(cm)', 'Dim. da sapata em a(cm)', 'Dim. da sapata em b(cm)',
                                            'Altura da sapata(cm)', 'Altura útil da sapata(cm)',
                                            'Altura da extremidade da sapata(cm)',
                                            'Inclinação da sapata(º)', 'Tensão máxima(kN/m²)', 'Vd(kN)', 'Vrd2(kN)',
                                            'Diâmetro(mm)']
                    d_results = {'Variáveis': list_names_variables, 'Valores': list_results}
                    df_results = pd.DataFrame(data=d_results)

                    def casas_decimais(x):
                        return round(x, 2)

                    df_results['Valores'] = df_results['Valores'].apply(casas_decimais)

                    # Início do desenho
                    # Criando o arquivo dxf e gerando o modelspace
                    dwg = ezdxf.new('R2018')
                    msp = dwg.modelspace()

                    # Criando os layers
                    dwg.layers.new(name='Sapata', dxfattribs={'linetype': 'Continuous', 'color': 7})
                    dwg.layers.new(name='Armadura', dxfattribs={'linetype': 'Continuous', 'color': 5})
                    dwg.layers.new(name='Cotas', dxfattribs={'linetype': 'Continuous', 'color': 2})

                    # Criando estilos de letras
                    dwg.styles.new('descricao_armadura', dxfattribs={'font': 'times.ttf', 'width': 8})

                    # Planta
                    # Face maior da sapata
                    p1 = (0, 0)
                    p2 = (a, 0)
                    p3 = (a, b)
                    p4 = (0, b)
                    poly_01 = [p1, p2, p3, p4, p1]
                    msp.add_lwpolyline(poly_01, dxfattribs={'layer': 'Sapata'})

                    # Face menor da sapata
                    p5 = ((a - a0) / 2, (b - b0) / 2)
                    p6 = ((a + a0) / 2, (b - b0) / 2)
                    p7 = ((a + a0) / 2, (b + b0) / 2)
                    p8 = ((a - a0) / 2, (b + b0) / 2)
                    poly_02 = [p5, p6, p7, p8, p5]
                    msp.add_lwpolyline(poly_02, dxfattribs={'layer': 'Sapata'})

                    # Ligação entre as áreas
                    msp.add_line(p1, p5, dxfattribs={'layer': 'Sapata'})
                    msp.add_line(p2, p6, dxfattribs={'layer': 'Sapata'})
                    msp.add_line(p3, p7, dxfattribs={'layer': 'Sapata'})
                    msp.add_line(p4, p8, dxfattribs={'layer': 'Sapata'})

                    # Detalhamento da armadura
                    p15 = (0.05 * a, 0.8 * b)
                    p16 = (0.95 * a, 0.8 * b)
                    p17 = (0.25 * a, 0.95 * b)
                    p18 = (0.25 * a, 0.05 * b)
                    msp.add_line(p15, p16, dxfattribs={'layer': 'Armadura'})
                    msp.add_line(p17, p18, dxfattribs={'layer': 'Armadura'})
                    txt_arm = 'Ø' + str(diametro) + ' c. ' + str(espacamento)
                    pos_txt_arm_H = (0.45 * a, 0.825 * b)
                    pos_txt_arm_V = (0.225 * a, 0.35 * b)
                    msp.add_text(txt_arm, dxfattribs={'layer': 'Cotas', 'style': 'descricao_armadura',
                                                      'height': 10}).set_pos(pos_txt_arm_H, align='MIDDLE')
                    msp.add_text(txt_arm, dxfattribs={'layer': 'Cotas', 'style': 'descricao_armadura',
                                                      'height': 10, 'rotation': 90}).set_pos(pos_txt_arm_V,
                                                                                             align='MIDDLE')

                    # Corte
                    # offsets entre a planta e o corte
                    offset_H = a + 100
                    offset_V = b * (1 / 3)

                    # corte da sapata
                    p9 = (offset_H, offset_V)
                    p10 = (a + offset_H, offset_V)
                    p11 = (a + offset_H, offset_V + h0)
                    p12 = (offset_H + (a + a0) / 2, offset_V + H)
                    p13 = (offset_H + (a - a0) / 2, offset_V + H)
                    p14 = (offset_H, offset_V + h0)
                    poly_03 = [p9, p10, p11, p12, p13, p14, p9]
                    msp.add_lwpolyline(poly_03, dxfattribs={'layer': 'Sapata'})

                    # Detalhamento da armadura
                    p19 = (offset_H + 0.05 * a, offset_V + 0.8 * h0)
                    p20 = (offset_H + 0.05 * a, offset_V + 0.2 * h0)
                    p21 = (offset_H + 0.95 * a, offset_V + 0.2 * h0)
                    p22 = (offset_H + 0.95 * a, offset_V + 0.8 * h0)
                    poly_04 = [p19, p20, p21, p22]
                    msp.add_lwpolyline(poly_04, dxfattribs={'layer': 'Armadura'})
                    pos_txt_arm_T = (offset_H + a * 0.35, offset_V + 0.4 * h0)
                    msp.add_text(txt_arm, dxfattribs={'layer': 'Cotas', 'style': 'descricao_armadura',
                                                      'height': 10}).set_pos(pos_txt_arm_T, align='MIDDLE')
                    raio = diametro / 20
                    msp.add_circle((offset_H + 0.05 * a + raio, offset_V + 0.2 * h0 + raio), raio,
                                   dxfattribs={'layer': 'Armadura'})
                    msp.add_circle((offset_H + 0.95 * a - raio, offset_V + 0.2 * h0 + raio), raio,
                                   dxfattribs={'layer': 'Armadura'})

                    print('Desenho realizado com sucesso!')
                    dwg.saveas('autoproject.dxf')

                    content = open('autoproject.dxf', 'r').read()
                    filename = 'autoproject.dxf'
                    response = HttpResponse(content, content_type='text/plain')
                    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
                    return response

                else:
                    print('\n\nVd > Vrd2 - Rever Projeto\n\n')
            else:
                print('\n\nTensão máxima > Tensão Limite - Rever Projeto\n\n')
        else:
            print('\n\nInclinação acima do permitido - Rever Projeto\n\n')



