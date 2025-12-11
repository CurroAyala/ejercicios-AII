from main.models import Vino, DenominacionOrigen, Pais, TipoUva

path = 'data'

def poblar_vinos():
    Vino.objects.all().delete()

    file = open(f'{path}\\vinos', 'r', encoding='iso-8859-1')
    for line in file:
        rip = line.strip().split('|')
        vino = Vino(idVino=int(rip[0].strip()), nombre=rip[1], precio=float(rip[2].strip()), denominacion=DenominacionOrigen.objects.get(idDenominacion=int(rip[3].strip())))

        vino.save()

        uvas = []
        for i in range (4, len(rip)):
            uvas.append(TipoUva.objects.get(idTipoUva=int(rip[i].strip())))
        vino.tiposUva.set(uvas)

    file.close()

    return Vino.objects.count()

def poblar_denominaciones():
    DenominacionOrigen.objects.all().delete()

    file = open(f'{path}\\denominaciones', 'r', encoding='iso-8859-1')
    res = []
    for line in file:
        rip = line.strip().split('|')
        res.append(DenominacionOrigen(idDenominacion=int(rip[0].strip()), nombre=rip[1].strip(), pais=Pais.objects.get(idPais=int(rip[2].strip()))))

    DenominacionOrigen.objects.bulk_create(res) # Se utiliza bulk_create para mejorar la eficiencia al insertar muchos registros

    file.close()

    return len(res)

def poblar_paises():
    Pais.objects.all().delete()

    file = open(f'{path}\\paises', 'r', encoding='iso-8859-1')
    res = []
    for line in file:
        rip = line.strip().split('|')
        res.append(Pais(idPais=int(rip[0].strip()), nombre=rip[1].strip()))
    
    Pais.objects.bulk_create(res) # Se utiliza bulk_create para mejorar la eficiencia al insertar muchos registros

    file.close()

    return len(res)

def poblar_tipos_uva():
    TipoUva.objects.all().delete()

    file = open(f'{path}\\uvas', 'r', encoding='iso-8859-1')

    res = []
    for line in file:
        rip = line.strip().split('|')
        res.append(TipoUva(idTipoUva=int(rip[0].strip()), nombre=rip[1].strip()))
    
    TipoUva.objects.bulk_create(res) # Se utiliza bulk_create para mejorar la eficiencia al insertar muchos registros

    file.close()

    return len(res)