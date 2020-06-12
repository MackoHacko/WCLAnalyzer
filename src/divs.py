import yaml
import dash_html_components as html
import dash_core_components as dcc
from datetime import datetime as dt
from loggers.logger import Logger

# Initialize logger
logger = Logger().getLogger(__file__)

with open(r'configs/zone_settings.yaml') as file:
    zones = yaml.load(file, Loader=yaml.FullLoader)

with open(r'configs/class_settings.yaml') as file:
    classes = yaml.load(file, Loader=yaml.FullLoader)

with open(r'configs/servers.yaml') as file:
    servers = yaml.load(file, Loader=yaml.FullLoader)

serverRegion_div = html.Div(
    className='row',
    children=[
        html.Div(
            className='largeleftblock',
            children=[
                html.Datalist(
                    id='serverlist',
                    children=[html.Option(value=server) for server in servers]
                ),
                dcc.Input(
                    type='text',
                    placeholder='Server',
                    id='serverinput',
                    list='serverlist',
                    required = True
                )
            ]
        ),
        html.Div(
            className='smallrightblock',
            children=[
                dcc.Dropdown(
                    id='regionselect',
                    options=[{'label': 'EU', 'value': 'EU'}],
                    value = 'EU',
                    placeholder='Region',
                    clearable=False
                )
            ]
        )
    ]
)

guildZone_div = html.Div(
    className='row',
    children=[
        html.Div(
            className='largeleftblock',
            children=[
                dcc.Input(
                    type='text',
                    placeholder='Guild',
                    id='guildinput',
                    required = True
                )
            ]
        ),
        html.Div(
            className='smallrightblock',
            children=[
                dcc.Dropdown(
                    id='zoneselect',
                    options=[{'label': zone, 'value': zones[zone]['id']} for zone in zones],
                    placeholder='Zone'
                )
            ]
        )
    ]
)

reports_search_div = html.Div(
    id='reportsform',
    children=[
        html.Div(
            children=[
                dcc.ConfirmDialog(
                    id='confirm',
                    message = 'Invalid guild name/server/region specified.'
                ),
                html.H2('Log-Analyzer'),
                html.P('Tool for averaging more than two logs.'),
                serverRegion_div,
                guildZone_div,
                html.Br(),
                html.Button(
                    'submit',
                    id='submit-val'
                )
            ],
            style={'text-align': 'center'}
        )
    ]
)

reports_select_div = html.Div(
    id='reportselect',
    children=[
        html.Div(
            children=[
                html.H5('Result'),
                dcc.Dropdown(
                    id='reportdropdown',
                    multi=True,
                    placeholder='Logs'
                ),
                html.Br(),
                html.H3('Filters'),
                dcc.Dropdown(
                    id='classdropdown',
                    options=[{'label': class_, 'value': class_} for class_ in classes],
                    placeholder='Class',
                    multi=True
                ),
                html.Br(),
                dcc.Dropdown(
                    id='viewdropdown',
                    options=[
                        {'label': 'Healing', 'value': 'healing'},
                        {'label': 'Damage', 'value': 'damage-done'}
                    ],
                    value = 'damage-done',
                    placeholder='Type'
                ),
                html.Br(),
                dcc.Dropdown(
                    id='encounterdropdown',
                    value = '',
                    placeholder='Encounter'
                ),
                html.Br(),
                html.Button(
                    'Back',
                    id='back'
                )
            ],
            style={'text-align': 'center'}
        )
    ]
)
