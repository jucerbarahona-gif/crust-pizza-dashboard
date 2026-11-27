"""Núcleo reproducible de San Francisco Crust Pizza.
Los KPI financieros se calculan con las columnas históricas de Ventas.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

SALES_REQUIRED = {
    'VentaID','Fecha','Ciudad','Sucursal','ClienteID','ProductoID','Cantidad',
    'PrecioUnitario','CostoUnitario','DescuentoPct','VentaNeta','CostoTotal','UtilidadBruta'
}
CLIENT_REQUIRED = {'ClienteID','Segmento','ClienteActivo','NPS'}
PRODUCT_REQUIRED = {'ProductoID','Categoria','Producto','Tamaño'}
NUM_SALES = ['Cantidad','PrecioUnitario','CostoUnitario','DescuentoPct','VentaNeta','CostoTotal','UtilidadBruta']

class DatosInvalidos(ValueError):
    pass


def _required(df: pd.DataFrame, fields: set[str], title: str):
    absent = sorted(fields.difference(df.columns))
    if absent:
        raise DatosInvalidos(f'{title}: faltan columnas obligatorias: {", ".join(absent)}.')
    if df.empty:
        raise DatosInvalidos(f'{title}: el archivo está vacío.')


def parse_fecha(series: pd.Series) -> pd.Series:
    # Excel suele entregar fechas como datetime64; no deben tratarse como seriales numéricos.
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors='coerce').dt.normalize()
    numbers = pd.to_numeric(series, errors='coerce')
    if numbers.notna().mean() > 0.9:
        dates = pd.to_datetime(numbers, unit='D', origin='1899-12-30', errors='coerce')
    else:
        dates = pd.to_datetime(series, errors='coerce', dayfirst=False)
    return dates.dt.normalize()


def leer_archivo_subido(contenido: bytes, nombre: str, tipo: str) -> pd.DataFrame:
    """Abre Excel/CSV del usuario conservando identificadores como texto.

    `tipo` debe ser Ventas, Clientes o Productos. Las columnas se validan
    posteriormente en preparar(); no se interpretan nombres de campos.
    """
    from io import BytesIO
    from pathlib import Path
    ids = {
        'Ventas': {'VentaID': str, 'ClienteID': str, 'ProductoID': str},
        'Clientes': {'ClienteID': str},
        'Productos': {'ProductoID': str},
    }
    if tipo not in ids:
        raise DatosInvalidos('Tipo de base de datos desconocido.')
    suffix = Path(nombre).suffix.lower()
    try:
        if suffix == '.csv':
            return pd.read_csv(BytesIO(contenido), encoding='utf-8-sig', dtype=ids[tipo])
        if suffix == '.xlsx':
            return pd.read_excel(BytesIO(contenido), engine='openpyxl', dtype=ids[tipo])
    except (ValueError, UnicodeError, OSError, ImportError, pd.errors.ParserError) as exc:
        raise DatosInvalidos(f'No se pudo leer el archivo {nombre}: {exc}') from exc
    raise DatosInvalidos(f'{nombre}: solo se admiten archivos .xlsx y .csv.')


def preparar(ventas: pd.DataFrame, clientes: pd.DataFrame, productos: pd.DataFrame):
    v, c, p = ventas.copy(), clientes.copy(), productos.copy()
    _required(v, SALES_REQUIRED, 'Ventas')
    _required(c, CLIENT_REQUIRED, 'Clientes')
    _required(p, PRODUCT_REQUIRED, 'Productos')
    for d, cols in [(v,['VentaID','ClienteID','ProductoID','Ciudad','Sucursal']),
                    (c,['ClienteID']),(p,['ProductoID'])]:
        for col in cols:
            d[col] = d[col].astype('string').str.strip()
    if c['ClienteID'].duplicated().any() or p['ProductoID'].duplicated().any():
        raise DatosInvalidos('Clientes o Productos contienen identificadores duplicados; revisar antes de relacionar.')
    if v['VentaID'].duplicated().any():
        raise DatosInvalidos('VentaID duplicado: el identificador de transacción no es único; revisar si hay líneas de pedido.')
    v['Fecha'] = parse_fecha(v['Fecha'])
    if v['Fecha'].isna().any():
        raise DatosInvalidos(f'Hay {int(v["Fecha"].isna().sum())} fechas inválidas en Ventas.')
    for col in NUM_SALES:
        v[col] = pd.to_numeric(v[col], errors='coerce')
    if v[NUM_SALES].isna().any().any():
        bad = v[NUM_SALES].isna().sum(); bad=bad[bad>0]
        raise DatosInvalidos('Campos numéricos inválidos: '+ ', '.join(f'{k}: {int(x)}' for k,x in bad.items()))
    if ((v['DescuentoPct'] < 0) | (v['DescuentoPct'] > 100)).any():
        raise DatosInvalidos('DescuentoPct debe expresarse de 0 a 100, p. ej. 10 para 10 %.')
    if (v['Cantidad'] <= 0).any():
        raise DatosInvalidos('Existen cantidades iguales o menores a cero.')
    missing_cl = (~v['ClienteID'].isin(c['ClienteID'])).sum()
    missing_pr = (~v['ProductoID'].isin(p['ProductoID'])).sum()
    if missing_cl or missing_pr:
        raise DatosInvalidos(f'Claves sin correspondencia: {missing_cl} cliente(s), {missing_pr} producto(s).')
    ccols = ['ClienteID','Segmento','ClienteActivo','NPS']
    pcols = ['ProductoID','Categoria','Producto','Tamaño']
    datos = v.merge(c[ccols], on='ClienteID', validate='many_to_one', how='left')
    datos = datos.merge(p[pcols], on='ProductoID', validate='many_to_one', how='left')
    datos['ProductoEtiqueta'] = datos['Producto'].fillna('Sin nombre').astype(str) + ' · ' + datos['Tamaño'].fillna('—').astype(str) + ' ('+datos['ProductoID'].astype(str)+')'
    datos['Periodo'] = datos['Fecha'].dt.to_period('M').astype(str)
    datos['AñoAnalisis'] = datos['Fecha'].dt.year
    informe = {
        'registros_ventas':len(v), 'clientes_catalogo':len(c), 'productos_catalogo':len(p),
        'ventas_unicas':int(v['VentaID'].nunique()),
        'formula_neta_diferente':int(((v['PrecioUnitario']*v['Cantidad']*(1-v['DescuentoPct']/100)-v['VentaNeta']).abs()>.03).sum()),
        'formula_coste_diferente':int(((v['CostoUnitario']*v['Cantidad']-v['CostoTotal']).abs()>.03).sum()),
        'formula_utilidad_diferente':int(((v['VentaNeta']-v['CostoTotal']-v['UtilidadBruta']).abs()>.03).sum()),
    }
    for col in ['PrecioVentaUSD','CostoUSD']:
        if col in p.columns:
            check = v[['ProductoID','PrecioUnitario' if col == 'PrecioVentaUSD' else 'CostoUnitario']].merge(p[['ProductoID',col]],on='ProductoID')
            a = 'PrecioUnitario' if col=='PrecioVentaUSD' else 'CostoUnitario'
            informe[f'catalogo_{col}_diferencias']=int(((pd.to_numeric(check[a])-pd.to_numeric(check[col])).abs()>.01).sum())
    if 'Ciudad' in c.columns:
        cc = v[['ClienteID','Ciudad']].merge(c[['ClienteID','Ciudad']],on='ClienteID',suffixes=['Venta','Cliente'])
        informe['ciudad_compra_distinta_residencia']=int((cc['CiudadVenta']!=cc['CiudadCliente']).sum())
    if 'TotalCompras' in c.columns:
        count = v.groupby('ClienteID')['VentaID'].nunique().rename('ComprasEnVentas')
        b = c[['ClienteID','TotalCompras']].join(count,on='ClienteID')
        informe['historial_cliente_no_coincide']=int((pd.to_numeric(b['TotalCompras'])!=b['ComprasEnVentas'].fillna(0)).sum())
    return datos, informe


def metricas(data: pd.DataFrame) -> dict:
    sales=float(data['VentaNeta'].sum())
    profit=float(data['UtilidadBruta'].sum())
    tx=int(data['VentaID'].nunique())
    return {'ventas':sales,'utilidad':profit,'margen':profit/sales*100 if sales else 0.,
            'ticket':sales/tx if tx else 0.,'clientes':int(data['ClienteID'].nunique()),
            'transacciones':tx,'unidades':int(data['Cantidad'].sum())}


def agrupar(data: pd.DataFrame, por: str) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame(columns=[por,'Ventas','Utilidad','Unidades','Transacciones','Clientes','Margen %','Ticket'])
    g = data.groupby(por, dropna=False, observed=True).agg(
        Ventas=('VentaNeta','sum'),Utilidad=('UtilidadBruta','sum'),
        Unidades=('Cantidad','sum'), Transacciones=('VentaID','nunique'),
        Clientes=('ClienteID','nunique')).reset_index()
    g['Margen %'] = np.where(g['Ventas'].ne(0),100*g['Utilidad']/g['Ventas'],0)
    g['Ticket'] = np.where(g['Transacciones'].ne(0),g['Ventas']/g['Transacciones'],0)
    return g


def contexto_para_ia(data:pd.DataFrame) -> dict:
    """Sólo agregados, sin nombres de clientes ni datos personales."""
    m=metricas(data)
    ag=lambda key:agrupar(data,key).round(2).sort_values('Ventas',ascending=False).to_dict('records')
    return {'kpi':{k:round(v,2) for k,v in m.items()},
            'sucursales':ag('Sucursal'), 'ciudades':ag('Ciudad'),
            'segmentos':ag('Segmento'),'productos':ag('ProductoEtiqueta'),
            'años':ag('AñoAnalisis'),
            'meses':agrupar(data,'Periodo').round(2).to_dict('records')}


def hechos_verificables(data:pd.DataFrame) -> list[str]:
    if data.empty:return ['No hay registros para los filtros seleccionados.']
    m=metricas(data); b=agrupar(data,'Sucursal');pr=agrupar(data,'ProductoEtiqueta'); sg=agrupar(data,'Segmento')
    facts=[f'Ventas: US$ {m["ventas"]:,.2f}; utilidad bruta: US$ {m["utilidad"]:,.2f}; margen: {m["margen"]:.2f} %.']
    if not b.empty:
        best=b.sort_values('Utilidad',ascending=False).iloc[0]
        worst=b.sort_values('Utilidad').iloc[0]
        facts.append(f'Sucursal con mayor utilidad bruta: {best["Sucursal"]} (US$ {best["Utilidad"]:,.2f}); menor: {worst["Sucursal"]} (US$ {worst["Utilidad"]:,.2f}).')
    if not pr.empty:
        top=pr.sort_values('Utilidad',ascending=False).iloc[0]
        facts.append(f'Producto con mayor utilidad bruta acumulada: {top["ProductoEtiqueta"]} (US$ {top["Utilidad"]:,.2f}).')
    if not sg.empty:
        top=sg.sort_values('Ventas',ascending=False).iloc[0]
        facts.append(f'Segmento de mayor facturación: {top["Segmento"]} (US$ {top["Ventas"]:,.2f}).')
    y=agrupar(data,'AñoAnalisis').sort_values('AñoAnalisis')
    if len(y)>=2:
        a,b=y.iloc[-2],y.iloc[-1]
        delta=100*(b['Ventas']/a['Ventas']-1) if a['Ventas'] else 0
        facts.append(f'Variación de ventas {int(a["AñoAnalisis"])} a {int(b["AñoAnalisis"])}: {delta:+.2f} %.')
    return facts
