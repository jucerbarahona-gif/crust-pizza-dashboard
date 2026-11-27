"""Dashboard de Inteligencia de Negocios para San Francisco Crust Pizza.
Arranque: streamlit run app.py
"""
from __future__ import annotations
import os, json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from analytics import preparar, metricas, agrupar, contexto_para_ia, hechos_verificables, DatosInvalidos, leer_archivo_subido

st.set_page_config(page_title='Crust Pizza | Inteligencia Comercial',page_icon='🍕',layout='wide',initial_sidebar_state='expanded')

CSS = '''
<style>
[data-testid="stAppViewContainer"] {background: #F9F7F2;}
[data-testid="stSidebar"] {background: #F3EFE8;}
h1,h2,h3 {font-family: 'Helvetica Neue',Arial,sans-serif; color:#243040; letter-spacing:-.025em;}
[data-testid="stMetric"] {background:#FFFFFF; border:1px solid #E8E1D7; border-radius:10px;padding:16px 20px;box-shadow:0 2px 7px rgba(20,28,38,.035);}
[data-testid="stMetricLabel"] {font-size: .88rem;}
.stButton button[kind="primary"] {background: #B63D32; color:white;border:0;}
.stTabs [data-baseweb="tab-list"] {gap:6px;}
.stTabs [data-baseweb="tab"] {background:#F3EFE8;border-radius:6px 6px 0 0;padding:12px;}
.block-container {padding-top:2.4rem;max-width:1400px;}
.smallnote {font-size:.83rem;color:#57606A;}
</style>
'''
st.markdown(CSS,unsafe_allow_html=True)
COLOR='#B63D32'
GOLD='#C7914D'
NAVY='#263547'
PALETTE=[COLOR,NAVY,GOLD,'#6A877E','#8B6D83','#526F9C','#C9A06E','#74818E']
BASE=Path(__file__).resolve().parent

@st.cache_data(show_spinner=False)
def cargar_base():
    v=pd.read_csv(BASE/'datos'/'ventas.csv',encoding='utf-8-sig',dtype={'VentaID':str,'ClienteID':str,'ProductoID':str})
    c=pd.read_csv(BASE/'datos'/'clientes.csv',encoding='utf-8-sig',dtype={'ClienteID':str})
    p=pd.read_csv(BASE/'datos'/'productos.csv',encoding='utf-8-sig',dtype={'ProductoID':str})
    return v,c,p

@st.cache_data(show_spinner=False)
def leer_tabla_subida(contenido: bytes, nombre: str, tipo: str):
    return leer_archivo_subido(contenido, nombre, tipo)

def plot(fig,height=370):
    fig.update_layout(template='plotly_white',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
       font=dict(family='Arial',color=NAVY,size=12),margin=dict(l=10,r=15,t=35,b=20),height=height,
       hovermode='closest',legend_title_text='')
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})

def fmt_usd(v):return f'US$ {v:,.2f}'
def note():
    st.caption('Criterio: ventas, costos y utilidades se toman de cada transacción del archivo Ventas. Margen bruto = utilidad bruta / ventas netas. Ticket = ventas netas / transacciones únicas.')

st.sidebar.markdown('## 🍕 Crust Pizza')
st.sidebar.caption('Panel de dirección comercial | 2024–2025')
with st.sidebar.expander('📁 Cargar o actualizar bases de datos', expanded=True):
    st.markdown('**Sube los Excel originales de la universidad** o archivos CSV con las mismas columnas. Los datos de ejemplo ya están cargados; subir archivos es opcional.')
    nuevo_ventas = st.file_uploader('1. Ventas (Excel o CSV)', type=['xlsx','csv'], key='archivo_ventas')
    nuevo_clientes = st.file_uploader('2. Clientes (Excel o CSV)', type=['xlsx','csv'], key='archivo_clientes')
    nuevo_productos = st.file_uploader('3. Productos (Excel o CSV)', type=['xlsx','csv'], key='archivo_productos')
    st.caption('Puedes subir uno, dos o los tres archivos. Si sustituyes Ventas, los indicadores y gráficos se recalculan automáticamente. Los archivos se usan solo durante la sesión; los originales no se modifican.')
try:
    ventas, clientes, productos = cargar_base()
    archivos_subidos = {
        'Ventas': nuevo_ventas,
        'Clientes': nuevo_clientes,
        'Productos': nuevo_productos,
    }
    if nuevo_ventas is not None:
        ventas = leer_tabla_subida(nuevo_ventas.getvalue(), nuevo_ventas.name, 'Ventas')
    if nuevo_clientes is not None:
        clientes = leer_tabla_subida(nuevo_clientes.getvalue(), nuevo_clientes.name, 'Clientes')
    if nuevo_productos is not None:
        productos = leer_tabla_subida(nuevo_productos.getvalue(), nuevo_productos.name, 'Productos')
    df, revision = preparar(ventas, clientes, productos)
except (DatosInvalidos, ValueError, KeyError, OSError, ImportError, UnicodeError) as e:
    st.error(f'La carga no pudo validarse: {e}')
    st.info('Comprueba que los archivos tienen las columnas originales de Ventas, Clientes o Productos y que sus códigos de cliente/producto coinciden.')
    st.stop()

st.sidebar.markdown('### Filtros del análisis')
fecha_ini,fecha_fin=df['Fecha'].min().date(),df['Fecha'].max().date()
intervalo=st.sidebar.date_input('Intervalo de fechas',value=(fecha_ini,fecha_fin),min_value=fecha_ini,max_value=fecha_fin,format='DD/MM/YYYY')
if isinstance(intervalo,(tuple,list)) and len(intervalo)==2:
    fi,ff=intervalo
else: fi,ff=fecha_ini,fecha_fin
ciudades=st.sidebar.multiselect('Ciudad',sorted(df['Ciudad'].dropna().unique()),default=[])
sucursales_posibles=sorted(df[df['Ciudad'].isin(ciudades)]['Sucursal'].unique()) if ciudades else sorted(df['Sucursal'].unique())
sucursales=st.sidebar.multiselect('Sucursal',sucursales_posibles,default=[])
segmentos=st.sidebar.multiselect('Segmento de clientes',sorted(df['Segmento'].dropna().unique()),default=[])
productos_elegidos=st.sidebar.multiselect('Producto',sorted(df['ProductoEtiqueta'].dropna().unique()),default=[])
mask=df['Fecha'].between(pd.Timestamp(fi),pd.Timestamp(ff))
for values,column in [(ciudades,'Ciudad'),(sucursales,'Sucursal'),(segmentos,'Segmento'),(productos_elegidos,'ProductoEtiqueta')]:
    if values: mask &= df[column].isin(values)
fil=df.loc[mask].copy()

st.markdown('## San Francisco Crust Pizza')
st.markdown('<div class="smallnote">Inteligencia comercial · tablero ejecutivo · fuentes: Ventas, Clientes y Productos</div>',unsafe_allow_html=True)
for etiqueta, archivo in archivos_subidos.items():
    if archivo is not None:
        st.info(f'Archivo temporal activo · {etiqueta}: {archivo.name}. Indicadores calculados con la selección actual.')
if fil.empty:
    st.warning('No hay ventas para la combinación de filtros. Amplía el intervalo o retira algún filtro.')
    st.stop()

m=metricas(fil)
c1,c2,c3=st.columns(3)
c1.metric('Ventas netas',fmt_usd(m['ventas']))
c2.metric('Utilidad bruta',fmt_usd(m['utilidad']))
c3.metric('Margen bruto',f'{m["margen"]:.2f} %')
c4,c5,c6=st.columns(3)
c4.metric('Ticket promedio',fmt_usd(m['ticket']))
c5.metric('Clientes con compra',f'{m["clientes"]:,}')
c6.metric('Transacciones',f'{m["transacciones"]:,}')
st.caption(f'Periodo filtrado: {fi:%d/%m/%Y} – {ff:%d/%m/%Y} · {m["unidades"]:,} unidades vendidas · {len(fil):,} filas de venta')

resumen,suc_tab,prod_tab,seg_tab,calidad_tab,ia_tab=st.tabs(['📊 Resumen','🏬 Sucursales','🍕 Productos','👥 Clientes','🧪 Calidad y actualización','✨ Asistente IA'])
with resumen:
    left,right=st.columns([1.4,1])
    with left:
        st.subheader('Evolución mensual')
        mensual=agrupar(fil,'Periodo').sort_values('Periodo')
        if len(mensual)>0:
            fig=px.line(mensual,x='Periodo',y=['Ventas','Utilidad'],markers=True,color_discrete_sequence=[COLOR,NAVY],labels={'value':'US$','variable':'Indicador','Periodo':'Mes'})
            fig.update_xaxes(tickangle=-45)
            plot(fig)
    with right:
        st.subheader('Ventas por ciudad')
        ciu=agrupar(fil,'Ciudad').sort_values('Ventas',ascending=True)
        plot(px.bar(ciu,x='Ventas',y='Ciudad',orientation='h',color_discrete_sequence=[COLOR],text='Ventas',labels={'Ventas':'Ventas netas (US$)','Ciudad':''}))
    left,right=st.columns(2)
    with left:
        st.subheader('Ventas por segmento')
        sg=agrupar(fil,'Segmento').sort_values('Ventas',ascending=False)
        plot(px.pie(sg,names='Segmento',values='Ventas',hole=.58,color_discrete_sequence=PALETTE))
    with right:
        st.subheader('Ventas por sucursal')
        su=agrupar(fil,'Sucursal').sort_values('Ventas',ascending=True)
        plot(px.bar(su,x='Ventas',y='Sucursal',orientation='h',color_discrete_sequence=[NAVY],labels={'Ventas':'US$','Sucursal':''}),height=420)
    note()
with suc_tab:
    st.subheader('Comparación de sucursales')
    s=agrupar(fil,'Sucursal').sort_values('Utilidad',ascending=False)
    fig=px.bar(s,x='Sucursal',y='Utilidad',color='Margen %',text_auto='.2s',color_continuous_scale=['#F4D4CF',COLOR],labels={'Utilidad':'Utilidad bruta (US$)'})
    fig.update_xaxes(tickangle=-25)
    plot(fig,420)
    st.dataframe(s.style.format({'Ventas':'US$ {:,.2f}','Utilidad':'US$ {:,.2f}','Margen %':'{:.2f} %','Ticket':'US$ {:,.2f}'}),use_container_width=True,hide_index=True)
    st.info('Mayor/menor desempeño se compara aquí por utilidad bruta acumulada. Revisar también ventas, margen y transacciones antes de tomar decisiones.')
with prod_tab:
    st.subheader('Rentabilidad de productos')
    p=agrupar(fil,'ProductoEtiqueta').sort_values('Utilidad',ascending=False)
    top=p.head(10).sort_values('Utilidad',ascending=True)
    low=p.tail(10).sort_values('Utilidad',ascending=True)
    a,b=st.columns(2)
    with a:
        st.markdown('**10 con mayor utilidad acumulada**')
        plot(px.bar(top,x='Utilidad',y='ProductoEtiqueta',orientation='h',color_discrete_sequence=[NAVY],labels={'ProductoEtiqueta':'','Utilidad':'Utilidad (US$)'}),480)
    with b:
        st.markdown('**10 con menor utilidad acumulada**')
        plot(px.bar(low,x='Utilidad',y='ProductoEtiqueta',orientation='h',color_discrete_sequence=[COLOR],labels={'ProductoEtiqueta':'','Utilidad':'Utilidad (US$)'}),480)
    st.dataframe(p.style.format({'Ventas':'US$ {:,.2f}','Utilidad':'US$ {:,.2f}','Margen %':'{:.2f} %','Ticket':'US$ {:,.2f}'}),hide_index=True,use_container_width=True)
    st.caption('El volumen total de utilidad no equivale al margen porcentual. Se utilizan importes históricos, no los precios estáticos del catálogo.')
with seg_tab:
    st.subheader('Comparación por segmentos')
    sg=agrupar(fil,'Segmento').sort_values('Ventas',ascending=False)
    l,r=st.columns(2)
    with l:
        plot(px.bar(sg,x='Segmento',y='Ventas',color_discrete_sequence=[COLOR],labels={'Ventas':'Ventas netas (US$)'}))
    with r:
        plot(px.bar(sg,x='Segmento',y='Margen %',color_discrete_sequence=[GOLD],labels={'Margen %':'Margen bruto (%)'}))
    st.dataframe(sg.style.format({'Ventas':'US$ {:,.2f}','Utilidad':'US$ {:,.2f}','Margen %':'{:.2f} %','Ticket':'US$ {:,.2f}'}),hide_index=True,use_container_width=True)
    st.markdown('**Estado de clientes en la base maestra**')
    estado=clientes.groupby(['Segmento','ClienteActivo'],dropna=False).size().reset_index(name='Clientes')
    plot(px.bar(estado,x='Segmento',y='Clientes',color='ClienteActivo',barmode='group',color_discrete_sequence=[COLOR,NAVY],labels={'Clientes':'Clientes registrados'}),320)
    st.warning('El estado «ClienteActivo» y los totales acumulados de Clientes no están totalmente reconciliados con el historial de Ventas. Úsalos como señal a validar, no como prueba definitiva de abandono.')
with calidad_tab:
    st.subheader('Control de calidad de datos')
    items={
        'Filas de ventas procesadas':revision['registros_ventas'],
        'Transacciones únicas':revision['ventas_unicas'],
        'Clientes del catálogo':revision['clientes_catalogo'],
        'Productos del catálogo':revision['productos_catalogo'],
        'Diferencias > US$ 0,03: fórmula de venta':revision['formula_neta_diferente'],
        'Diferencias > US$ 0,03: costo':revision['formula_coste_diferente'],
        'Diferencias > US$ 0,03: utilidad':revision['formula_utilidad_diferente'],
        'Precios distintos del catálogo':revision.get('catalogo_PrecioVentaUSD_diferencias','No disponible'),
        'Costos distintos del catálogo':revision.get('catalogo_CostoUSD_diferencias','No disponible'),
        'Historial cliente ≠ registros de ventas':revision.get('historial_cliente_no_coincide','No disponible'),
        'Ciudad venta distinta de ciudad del cliente':revision.get('ciudad_compra_distinta_residencia','No disponible')
    }
    st.dataframe(pd.DataFrame([{'Control':k,'Resultado':v} for k,v in items.items()]),hide_index=True,use_container_width=True)
    st.markdown('**Regla de cálculo aplicada:** ventas netas, costos y utilidad bruta se toman de las transacciones. El catálogo describe producto y categoría; la base Clientes suministra segmentos. No se sustituyen los importes históricos por precios de catálogo.')
    st.markdown('**Actualizar sin editar el código:** usa los tres cargadores de la barra izquierda para subir Ventas, Clientes y Productos en XLSX o CSV. Ventas se puede reemplazar por sí sola; los indicadores y gráficos cambian automáticamente. Si hay columnas o relaciones incorrectas, verás un mensaje de error.')
    st.markdown('**Limitación:** la actualización es temporal por sesión, no almacena información permanentemente ni modifica el repositorio.')
    csv=(agrupar(fil,'Sucursal')).to_csv(index=False).encode('utf-8-sig')
    st.download_button('Descargar resumen de sucursales (CSV)',csv,'reporte_sucursales.csv','text/csv')
with ia_tab:
    st.subheader('Asistente de análisis comercial')
    st.markdown('El asistente recibe **únicamente métricas agregadas del periodo filtrado**; no se envían nombres ni registros individuales de clientes.')
    for h in hechos_verificables(fil):st.markdown('• '+h)
    st.divider()
    key=os.getenv('OPENAI_API_KEY','')
    if not key:
        try:key=st.secrets.get('OPENAI_API_KEY','')
        except Exception:pass
    if not key:
        st.warning('IA generativa no configurada. Los hallazgos anteriores son cálculos automáticos verificables, NO recomendaciones generadas por un modelo de IA. Para activar IA, configura OPENAI_API_KEY en Streamlit Secrets o como variable de entorno.')
    else:
        st.success('Servicio de IA configurado; el análisis se ejecuta cuando pulsas el botón.')
        pregunta=st.text_area('Consulta para el director comercial',value='Propón cinco decisiones comerciales priorizadas con evidencia numérica. Señala límites del análisis y supuestos.',height=95)
        if st.button('Generar recomendaciones con IA',type='primary'):
            try:
                from openai import OpenAI
                # Enviar solo agregados. Algunas API aplican límites de tamaño.
                context=contexto_para_ia(fil)
                sys=('Eres analista comercial. Usa EXCLUSIVAMENTE las cifras JSON adjuntas; no inventes datos. '
                     'Distingue hallazgos de hipótesis, advierte limitaciones; cada recomendación '
                     'debe citar un dato del JSON. Responde en español, con claridad y sin datos individuales.')
                result=OpenAI(api_key=key).chat.completions.create(
                    model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),
                    messages=[{'role':'system','content':sys},
                              {'role':'user','content':'Pregunta: '+pregunta+'\nDatos agregados:\n'+json.dumps(context,ensure_ascii=False,default=str)}],
                    temperature=.2,max_tokens=1100)
                st.markdown(result.choices[0].message.content or 'El modelo no devolvió texto.')
                st.caption('Estas sugerencias deben revisarse críticamente; no equivalen a decisiones ya implementadas.')
            except Exception as exc:
                st.error(f'No se pudo completar la consulta a la IA: {exc}')
    note()
st.caption('Proyecto académico · Sistema Inteligente de Apoyo a la Toma de Decisiones · San Francisco Crust Pizza')
