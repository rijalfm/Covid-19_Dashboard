# -*- coding: utf-8 -*-

import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output
from urllib.request import urlopen
import warnings
import locale

locale.setlocale(locale.LC_TIME, 'ID')
warnings.filterwarnings('ignore')

external_stylesheets = ['./static/css/style.css']
# my_token = (your mapbox token)

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


KAB_KUMULATIF_URL = 'https://covid19-public.digitalservice.id/api/v1//rekapitulasi_v2/jabar/kumulatif?level=kab'
KAB_URL = 'https://covid19-public.digitalservice.id/api/v1//rekapitulasi_v2/jabar/harian?level=kab'
PROV_URL = 'https://covid19-public.digitalservice.id/api/v1//rekapitulasi_v2/jabar/harian'


# Load geo data
DATA_WILAYAH = pd.read_csv('data/data_jabar.csv')
DATA_WILAYAH_DICT = DATA_WILAYAH[['kode_bps','latitude','longitude']].set_index('kode_bps',drop=True).to_dict()

# =====================================================================================================================

# Load data kumulatif kabupaten
DATA_KAB_KUMULATIF = json.loads(urlopen(KAB_KUMULATIF_URL).read())
DF_KAB_KUMULATIF = pd.DataFrame(DATA_KAB_KUMULATIF['data']['content'])
# DF_KAB_KUMULATIF = pd.read_csv('data/JABAR_KAB_KUMULATIF.csv')

DF_KAB_KUMULATIF.dropna(inplace=True)
DF_KAB_KUMULATIF['tanggal'] = pd.to_datetime(DF_KAB_KUMULATIF['tanggal'])
DF_KAB_KUMULATIF['kode_kab'] = DF_KAB_KUMULATIF['kode_kab'].astype(int)
LAST_KUMULATIF = DF_KAB_KUMULATIF.loc[DF_KAB_KUMULATIF['tanggal'] == DF_KAB_KUMULATIF['tanggal'].max()]
LAST_KUMULATIF['latitude'] = LAST_KUMULATIF['kode_kab'].map(DATA_WILAYAH_DICT['latitude'])
LAST_KUMULATIF['longitude'] = LAST_KUMULATIF['kode_kab'].map(DATA_WILAYAH_DICT['longitude'])
LAST_KUMULATIF['text'] = '<b>' + LAST_KUMULATIF['nama_kab'].astype(str) + '</b><br>' + '<b>Positif: </b>' + LAST_KUMULATIF['CONFIRMATION'].astype(str) + ' kasus'
LAST_KUMULATIF.sort_values(by='CONFIRMATION',inplace=True)

# =====================================================================================================================

# Load data harian kabupaten
DATA_KAB = json.loads(urlopen(KAB_URL).read())
DF_KAB = pd.DataFrame(DATA_KAB['data']['content'])
# DF_KAB = pd.read_csv('data/JABAR_KAB_HARIAN.csv')

DF_KAB.dropna(inplace=True)
DF_KAB['tanggal'] = pd.to_datetime(DF_KAB['tanggal'])
list_kabupaten = DF_KAB['nama_kab'].unique().tolist()

# =====================================================================================================================

# Load data harian provinsi
DATA_PROV = json.loads(urlopen(PROV_URL).read())
DF_PROV = pd.DataFrame(DATA_PROV['data']['content'])
# DF_PROV = pd.read_csv('data/JABAR.csv')

DF_PROV.dropna(inplace=True)
DF_PROV['tanggal'] = pd.to_datetime(DF_PROV['tanggal'])
DF_PROV_SUM = DF_PROV.cumsum()
DF_PROV['rolling'] = DF_PROV['CONFIRMATION'].rolling(window=30).mean()


# Update tanggal
LAST_DATE = DF_PROV.tanggal.iloc[-1].strftime('%d %B %Y')

# Update data provinsi
POSITIF = DF_PROV_SUM.iloc[-1]['CONFIRMATION']
NEW_POSITIF = DF_PROV.iloc[-1]['CONFIRMATION']
NEW_POSITIF_PERCENT = NEW_POSITIF/DF_PROV_SUM.iloc[-2]['CONFIRMATION']*100

SEMBUH = DF_PROV_SUM.iloc[-1]['confirmation_selesai']
NEW_SEMBUH = DF_PROV.iloc[-1]['confirmation_selesai']
NEW_SEMBUH_PERCENT = NEW_SEMBUH/DF_PROV_SUM.iloc[-2]['confirmation_selesai']*100

MENINGGAL = DF_PROV_SUM.iloc[-1]['confirmation_meninggal']
NEW_MENINGGAL = DF_PROV.iloc[-1]['confirmation_meninggal']
NEW_MENINGGAL_PERCENT = NEW_MENINGGAL/DF_PROV_SUM.iloc[-2]['confirmation_meninggal']*100

AKTIF = POSITIF - SEMBUH - MENINGGAL
LAST_AKTIF = DF_PROV_SUM.iloc[-2]['CONFIRMATION'] - DF_PROV_SUM.iloc[-2]['confirmation_selesai'] - DF_PROV_SUM.iloc[-2]['confirmation_meninggal']
NEW_AKTIF = AKTIF - LAST_AKTIF
NEW_AKTIF_PERCENT = NEW_AKTIF/LAST_AKTIF*100


# Membuat maps
fig = go.Figure(go.Scattermapbox(
    lon = LAST_KUMULATIF['longitude'],
    lat = LAST_KUMULATIF['latitude'],
    mode = 'markers',
    marker = go.scattermapbox.Marker(
        size = LAST_KUMULATIF['CONFIRMATION']/50,
        color = 'crimson',
        sizemode = 'area',
        opacity = 0.4),
    hoverinfo = 'text',
    hovertext = LAST_KUMULATIF['text'],
    text  = "<b>Peta Sebaran Kasus Positif COVID-19 Provinsi Jawa Barat</b>")
)

fig.update_layout(
    margin={'r':0,'t':0,'l':0,'b':0},
    hovermode = 'closest',
    mapbox = dict(
        accesstoken = my_token,
        center = go.layout.mapbox.Center(lat=-6.915, lon=107.637),
        style = 'dark',
        zoom = 7.3),
    autosize = True
)


# Grafik harian provinsi
fig2 = go.Figure()
fig2.add_trace(go.Bar(
                x=DF_PROV['tanggal'],
                y=DF_PROV['CONFIRMATION'],
                name='Konfirmasi positif harian',
                marker_color='#28A3C6',
                marker_line_color='rgba(0,0,0,0)'
))

fig2.add_trace(go.Scatter(
                x=DF_PROV['tanggal'],
                y=DF_PROV['rolling'],
                name='30 days Moving Average'
))

fig2.add_trace(go.Scatter(
                x=DF_PROV['tanggal'],
                y=DF_PROV_SUM['CONFIRMATION'],
                name='Kasus kumulatif',
                yaxis='y2'
))

fig2.update_layout(
    height=400,
    yaxis=dict(title='Jumlah kasus'),
    yaxis2=dict(
        title='Jumlah kumulatif',
        anchor='x',
        overlaying='y',
        side='right'
    ),
    plot_bgcolor = 'rgba(0,0,0,0.1)',
    paper_bgcolor = 'rgba(0,0,0,0)',
    margin={'r':5,'t':35,'l':5,'b':10},
    legend=dict(
        yanchor='top',
        y=0.99,
        xanchor='left',x=0.01),
    font=dict(
        color='#ffffff',
        family='arial'))

fig2.update_yaxes(
    rangemode='tozero',
    gridwidth=0,
    gridcolor='rgba(255,255,255,0)',
    zeroline=False,
    showline=True,
    linewidth=2,
    linecolor='rgba(255,255,255,0.7)')

fig2.update_xaxes(
    showline=True,
    linewidth=2,
    linecolor='rgba(255,255,255,0.7)',
    rangeselector=dict(
        activecolor='#111',
        bgcolor='#555555',
        buttons=list([
            dict(count=14, label='2w', step='day', stepmode='backward'),
            dict(count=1, label='1m', step='month', stepmode='backward'),
            dict(count=6, label='6m', step='month', stepmode='backward'),
            dict(count=1, label='YTD', step='year', stepmode='todate'),
            dict(step='all')]
    ))
)


# Grafik kasus 10 kabupaten/kota tertinggi
fig3 = go.Figure()
fig3.add_trace(go.Bar(
                x=LAST_KUMULATIF['CONFIRMATION'].tail(10),
                y=LAST_KUMULATIF['nama_kab'].tail(10) + ' ',
                orientation = 'h',
                marker_color='#F26B38',
                marker_line_color='rgba(0,0,0,0)'
))

fig3.update_layout(
    height=400,
    plot_bgcolor = 'rgba(0,0,0,0.1)',
    paper_bgcolor = 'rgba(0,0,0,0)',
    margin={'r':10,'t':10,'b':10},
    font=dict(
        color='#ffffff',
        family='arial')
)
fig3.update_xaxes(
    title_text='Jumlah Kasus',
    gridwidth=1,
    gridcolor='rgba(255,255,255,0.1)',
    zeroline=False,
    showline=True,
    linewidth=2,
    linecolor='rgba(255,255,255,0.7)')

fig3.update_yaxes(
    showline=True,
    linewidth=2,
    linecolor='rgba(255,255,255,0.7)')


# Membuat layout html
app.layout = html.Div(children=[


    
    # Fixed header
    html.Div(children=[
        html.H6(children='Dashboard Perkembangan Kasus COVID-19 Provinsi Jawa Barat')
        ],
        className = 'navbars'),


    
    # Card provinsi
    html.Div(children=[
        html.Div(children=[
            html.Div(children='Konfirmasi Positif', className='card-title'),
            html.Div(children=f'{POSITIF:,}', className='card-text'),
            html.Div(children=f'{NEW_POSITIF:,}' + (' (+%.2f' %(NEW_POSITIF_PERCENT)) + '%)', className='card-sub-text')],
        className='card',
        style={'color':'#F7DB4F'}),
        html.Div(children=[
            html.Div(children='Kasus Aktif', className='card-title'),
            html.Div(children=f'{AKTIF:,}', className='card-text'),
            html.Div(children=f'{NEW_AKTIF:,}' + (' (%.2f' %(NEW_AKTIF_PERCENT)) + '%)', className='card-sub-text')],
        className='card',
        style={'color':'#F26B38'}),
        html.Div(children=[
            html.Div(children='Sembuh', className='card-title'),
            html.Div(children=f'{SEMBUH:,}', className='card-text'),
            html.Div(children=f'{NEW_SEMBUH:,}' + (' (+%.2f' %(NEW_SEMBUH_PERCENT)) + '%)', className='card-sub-text')],
        className='card',
        style={'color':'#339933'}),
        html.Div(children=[
            html.Div(children='Meninggal', className='card-title'),
            html.Div(children=f'{MENINGGAL:,}', className='card-text'),
            html.Div(children=f'{NEW_MENINGGAL:,}' + (' (+%.2f' %(NEW_MENINGGAL_PERCENT)) + '%)', className='card-sub-text')],
        className='card',
        style={'color':'#EC2049'})
        ],
    className='rows', style={'margin-top':80}),
    


    # Grafik provinsi
    html.Div(children=[
        html.Div(children=[
            html.H6(children='Perkembangan Kasus COVID-19'),
            dcc.Graph(
                id='main-graph',
                figure = fig2)], className='half'),
        html.Div(children=[
            html.H6(children='10 Kabupaten/Kota dengan Kasus Tertinggi'),
            dcc.Graph(
                id='top-graph',
                figure = fig3)], className='half')
        ],
        className='rows'),



    # Data kabupaten
    html.Div(children=[
        html.Div(children=[
            html.H6(children='Pilih Kabupaten'),
            dcc.Dropdown(
                id='nama-kab',
                multi=False,
                clearable=False,
                value=list_kabupaten[3],
                placeholder='Pilih Kabupaten',
                options=[{'label':x, 'value':x} for x in list_kabupaten]),
            html.Div(children='Terakhir diperbarui: ' + LAST_DATE, className='date'),
            dcc.Graph(id='konfirmasi-kab', config={'displayModeBar':False}, style={'margin-top':15}),
            dcc.Graph(id='aktif-kab', config={'displayModeBar':False}, style={'margin-top':15}),
            dcc.Graph(id='sembuh-kab', config={'displayModeBar':False}, style={'margin-top':15}),
            dcc.Graph(id='meninggal-kab', config={'displayModeBar':False}, style={'margin-top':15})
            ],
            className='card2'),
        html.Div(children=[
            dcc.Graph(id='pie-chart', config={'displayModeBar':'hover'})],
            className='card2'),
        html.Div(children=[
            html.H6(children='Konfirmasi Positif Harian (30 hari terakhir)'),
            dcc.Graph(id='data-kab')
            ],
            className='half')],
        className='rows'),
    
    

    # Maps
    html.Div(children=[
        html.Div(children=[
            html.H6(children='Peta Sebaran Kasus COVID-19 Provinsi Jawa Barat'),
            dcc.Graph(
                id = 'example-graph',
                figure=fig
            )
            ],className='full')],
        className='rows')
])


# Callback data kabupaten
@app.callback(
    Output('konfirmasi-kab', 'figure'),
    Output('aktif-kab', 'figure'),
    Output('sembuh-kab', 'figure'),
    Output('meninggal-kab', 'figure'),
    Output('pie-chart', 'figure'),
    Output('data-kab', 'figure'),
    [Input('nama-kab', 'value')])



# Update data kabupaten
def update_data(nama_kab):
    DF_HARIAN = DF_KAB.loc[DF_KAB['nama_kab'] == nama_kab]
    DF_HARIAN['rolling'] = DF_HARIAN['CONFIRMATION'].rolling(window=30).mean()
    DF_KUMULATIF = DF_KAB_KUMULATIF.loc[DF_KAB_KUMULATIF['nama_kab'] == nama_kab]

    total_positif = DF_KUMULATIF['CONFIRMATION'].iloc[-1]
    prev_positif = DF_KUMULATIF['CONFIRMATION'].iloc[-2]

    sembuh = DF_KUMULATIF['confirmation_selesai'].iloc[-1]
    prev_sembuh = DF_KUMULATIF['confirmation_selesai'].iloc[-2]

    meninggal = DF_KUMULATIF['confirmation_meninggal'].iloc[-1]
    prev_meninggal = DF_KUMULATIF['confirmation_meninggal'].iloc[-2]

    aktif = total_positif - sembuh - meninggal
    prev_aktif = prev_positif - prev_sembuh - prev_meninggal

    fig = go.Figure(go.Indicator(
        mode='number+delta',
        value=total_positif,
        number={'valueformat':',','font':{'size':15}},
        delta={'position':'right',
            'reference':prev_positif,
            'valueformat':',g',
            'font':{'size':12}},
        domain={'x':[0,1],'y':[0,1]}
        )
    )

    fig.update_layout(
        title = {'text':'Konfirmasi Positif',
            'y':1,
            'x':0.5,
            'xanchor':'center',
            'yanchor':'top',
            'font':{'size':15, 'family':'arial'}
        },
        font=dict(color='#F7DB4F'),
        paper_bgcolor='rgba(0,0,0,0)',
        height=45)

    fig2 = go.Figure(go.Indicator(
        mode='number+delta',
        value=aktif,
        number={'valueformat':',','font':{'size':15}},
        delta={'position':'right',
            'reference':prev_aktif,
            'valueformat':',g',
            'font':{'size':12}},
        domain={'x':[0,1],'y':[0,1]}
        )
    )

    fig2.update_layout(
        title = {'text':'Kasus Aktif',
            'y':1,
            'x':0.5,
            'xanchor':'center',
            'yanchor':'top',
            'font':{'size':15, 'family':'arial'}
        },
        font=dict(color='#F26B38'),
        paper_bgcolor='rgba(0,0,0,0)',
        height=45)

    fig3 = go.Figure(go.Indicator(
        mode='number+delta',
        value=sembuh,
        number={'valueformat':',','font':{'size':15}},
        delta={'position':'right',
            'reference':prev_sembuh,
            'valueformat':',g',
            'font':{'size':12}},
        domain={'x':[0,1],'y':[0,1]}
        )
    )

    fig3.update_layout(
        title = {'text':'Sembuh',
            'y':1,
            'x':0.5,
            'xanchor':'center',
            'yanchor':'top',
            'font':{'size':15, 'family':'arial'}
        },
        font=dict(color='#339933'),
        paper_bgcolor='rgba(0,0,0,0)',
        height=45)

    fig4 = go.Figure(go.Indicator(
        mode='number+delta',
        value=meninggal,
        number={'valueformat':',','font':{'size':15}},
        delta={'position':'right',
            'reference':prev_meninggal,
            'valueformat':',g',
            'font':{'size':12}},
        domain={'x':[0,1],'y':[0,1]}
        )
    )

    fig4.update_layout(
        title = {'text':'Meninggal',
            'y':1,
            'x':0.5,
            'xanchor':'center',
            'yanchor':'top',
            'font':{'size':15, 'family':'arial'}
        },
        font=dict(color='#EC2049'),
        paper_bgcolor='rgba(0,0,0,0)',
        height=45)

    colors = ['#F26B38', '#339933', '#EC2049']
    fig5 = go.Figure(go.Pie(
        labels=['Kasus Aktif','Sembuh', 'Meninggal'],
        values = [aktif, sembuh, meninggal],
        marker=dict(colors=colors),
        hoverinfo='label+value+percent',
        textinfo='label+value',
        hole=.7,
        rotation=45
    ))

    fig5.update_layout(
        height=350,
        margin={'r':5,'t':100,'l':5,'b':40},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='closest',
        title={
            'text':'Sebaran kasus: <br><b>' + (nama_kab)+'</b>',
            'y':0.93,
            'x':0.5,
            'xanchor':'center',
            'yanchor':'top'
        },
        titlefont={
            'color':'white',
            'size':16
        },
        legend={
            'orientation':'h',
            'bgcolor':'rgba(0,0,0,0)',
            'xanchor':'left',
            'x':-0.1,
            'y':-0.2
        },
        font=dict(
            family='arial',
            size=12,
            color='white'))

    fig6 = go.Figure()
    fig6.add_trace(go.Bar(
                    x=DF_HARIAN['tanggal'][-30:],
                    y=DF_HARIAN['CONFIRMATION'][-30:],
                    name='Konfirmasi positif harian',
                    marker_color='#F7DB4F',
                    marker_line_color='rgba(0,0,0,0)'
    ))

    fig6.add_trace(go.Scatter(
                    x=DF_HARIAN['tanggal'][-30:],
                    y=DF_HARIAN['rolling'][-30:],
                    name='30 days Moving Average'
    ))

    fig6.update_layout(
    height=300,
    yaxis=dict(title='Jumlah kasus'),
    plot_bgcolor = 'rgba(0,0,0,0.1)',
    paper_bgcolor = 'rgba(0,0,0,0)',
    margin={'r':5,'t':5,'l':5,'b':5},
    legend=dict(
        yanchor='top',
        y=0.99,
        xanchor='left',x=0.01),
    font=dict(
        color='#ffffff',
        family='arial'))

    fig6.update_yaxes(
        rangemode='tozero',
        gridwidth=0,
        gridcolor='rgba(255,255,255,0)',
        zeroline=False,
        showline=True,
        linewidth=2,
        linecolor='rgba(255,255,255,0.7)')

    fig6.update_xaxes(
        showline=True,
        linewidth=2,
        linecolor='rgba(255,255,255,0.7)'
    )
    return fig, fig2, fig3, fig4, fig5, fig6



# Jalankan apps
if __name__ == '__main__':
    app.run_server(debug=True)