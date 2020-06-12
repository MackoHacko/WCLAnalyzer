import time
import json
import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import yaml
from json.decoder import JSONDecodeError
from dash.dependencies import Input, Output, State
from dotenv import load_dotenv, find_dotenv

from client import WCLClient
from divs import reports_search_div, reports_select_div
from loggers.logger import Logger
from utils import average_logs, parse_users, remove_irrelevant_roles, get_reports_key

# Load environment variables
load_dotenv(find_dotenv())

# Gloval variables
with open(r'configs/zone_settings.yaml') as file:
    zones = yaml.load(file, Loader=yaml.FullLoader)

with open(r'configs/class_settings.yaml') as file:
    class_settings = yaml.load(file, Loader=yaml.FullLoader)

# Initialize the app
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# Initialize logger
logger = Logger().getLogger(__file__)

# Initialize WCL client
client = WCLClient()

# Get users
try:
    with open(r'configs/users.yaml') as file:
        USERS = yaml.load(file, Loader=yaml.FullLoader)
except FileNotFoundError:
    logger.error("User list not found.")
    raise

# Initialize basic auth
auth = dash_auth.BasicAuth(
    app,
    parse_users(USERS)
)


def set_app_layout(app):
    logger.info("Set app layout.")
    app.layout = html.Div(
        children=[
            html.Div([
                dcc.Store(id='memory-reports'),
                dcc.Store(id='memory-logs'),
                html.Div(
                    className='four columns div-user-controls',
                    id='leftcol',
                    children=[reports_search_div, reports_select_div]
                ),
                html.Div(
                    className='eight columns div-for-charts bg-grey',
                    id='graphdiv'
                )
            ])
        ]
    )


def set_get_reports_callback(app):
    logger.info("Set callback for get_reports.")
    return app.callback(
        [
            Output('reportsform', 'style'),
            Output('reportselect', 'style'),
            Output('reportdropdown', 'options'),
            Output('encounterdropdown', 'options'),
            Output('memory-reports', 'data'),
            Output('confirm', 'displayed')
        ],
        [
            Input('submit-val', 'n_clicks'),
            Input('back', 'n_clicks')
        ],
        [
            State('serverinput', 'value'),
            State('regionselect', 'value'),
            State('guildinput', 'value'),
            State('zoneselect', 'value'),
            State('memory-reports', 'data')
        ]
    )


def set_update_graph_callback(app):
    logger.info("Set callback for update_graph.")
    return app.callback(
        [
            Output('graphdiv', 'children'),
            Output('memory-logs', 'data'),
        ],
        [
            Input('reportdropdown', 'value'),
            Input('classdropdown', 'value'),
            Input('viewdropdown', 'value'),
            Input('encounterdropdown', 'value')
        ],
        [
            State('memory-logs', 'data')
        ]
    )


@set_get_reports_callback(app)
def get_reports(
    clicks1,
    clicks2,
    server,
    region,
    guild,
    zone,
    stored_reports
):
    report_options = []
    encounters = []
    get_reports_error = False

    if not stored_reports:
        stored_reports = {}

    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    form_style = {'display': 'block'}
    select_style = {'display': 'none'}

    if button_id == 'submit-val':

        reports_key = get_reports_key(guild, server, region)

        if reports_key not in stored_reports.keys():

            logger.info("Fetching reports..")
            try:
                t0 = time.time()
                stored_reports[reports_key] = client.get_reports(guild, server, region)
                t1 = time.time()
                logger.info('Done. API call for fetching reports took {} s.'.format(t1 - t0))
            except (JSONDecodeError, NameError, TypeError):
                logger.exception('Could not get reports')
                get_reports_error = True

                return form_style, select_style, report_options, encounters, stored_reports,\
                get_reports_error

        form_style = {'display': 'none'}
        select_style = {'display': 'block'}
        report_options = [
            report.copy() for report in stored_reports[reports_key]
            if report['zone'] == zone or not zone
        ]

        for report_option in report_options:
            report_option.pop('zone', None)
            report_option.pop('guild', None)

        if zone:
            for val in zones.values():
                if val['id'] == zone:
                    encounters = [
                        {
                            'label': encounter['name'],
                            'value': encounter['id']
                        } for encounter in val['encounters']
                    ]
                    break

    elif button_id == 'back':
        form_style = {'display': 'block'}
        select_style = {'display': 'none'}
        logger.info("Displaying report search form.")

    else:
        logger.info("Displaying report options.")

    logger.debug(f"Currently stored reports: {stored_reports}")

    return form_style, select_style, report_options, encounters, stored_reports, get_reports_error


@set_update_graph_callback(app)
def update_graph(reports, classes, view, encounter, stored_logs):

    if stored_logs:
        stored_logs = json.loads(stored_logs)
    else:
        stored_logs = {}

    trigger = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    update_triggers = {'reportdropdown', 'classdropdown', 'viewdropdown', 'encounterdropdown'}

    if all([reports, view, trigger in update_triggers]):
        current_logs = []

        logger.info("Fetching logs..")
        t0 = time.time()
        for report in reports:

            loaded_report = json.loads(report)
            report_id = loaded_report['id']
            log_key = str((report_id, encounter, view))

            if log_key in stored_logs.keys():
                logger.info(f"{view} log for encounter: {encounter} with log_id: " +
                            f"{report_id} already fetched.")
                current_logs.append(stored_logs[log_key])
                continue

            log = client.get_log(
                view = view,
                log_id = report_id,
                end = loaded_report['end'] - loaded_report['start'],
                encounter = encounter
            )

            stored_logs[log_key] = log
            current_logs.append(log)

        t1 = time.time()
        logger.info('Done. API call for fetching logs took {} s.'.format(t1 - t0))

        logger.info("Calculating average..")
        t0 = time.time()
        df = average_logs(current_logs)
        t1 = time.time()
        logger.info('Done.Calculating average for logs took {} s.'.format(t1 - t0))

        class_index = [
            True if class_ in classes else False for class_ in df['class']
        ] if classes else [True] * len(df)

        df = df[class_index].pipe(remove_irrelevant_roles)

        colors = [class_settings[class_]['color'] for class_ in df['class']]

        figure = go.Figure()
        figure.add_trace(
            go.Bar(
                x = df.index,
                y = df.Avg,
                customdata = df.Counts,
                hovertemplate = "Damage: %{y}<br>Counts: %{customdata}<extra></extra>",
                marker = dict(color=[color for color in colors]),
                error_y = dict(
                    type = 'data',
                    array = df['std'],
                    thickness = 1.5,
                    width = 3,
                )
            )
        )

        figure.update_layout(
            template = 'plotly_dark',
            paper_bgcolor = 'rgba(0, 0, 0, 0)',
            plot_bgcolor = 'rgba(0, 0, 0, 0)',
            margin = {'b': 20},
            bargap = 0.3,
            hovermode = 'x',
            autosize = True,
            title = {
                'text': f'Percentage of total {view}',
                'font': {'color': 'white'},
                'x': 0.5
            }
        )

        logger.info("Graph updated.")
        return dcc.Graph(id='test', figure=figure), json.dumps(stored_logs)
    return None, json.dumps(stored_logs)


set_app_layout(app)


if __name__ == '__main__':
    logger.info("Starting server.")
    app.run_server(debug=True)
