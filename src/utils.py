from datetime import datetime

import pandas as pd

from loggers.logger import Logger

# Initialize logger
logger = Logger().getLogger(__file__)

THRESHOLD_PERCENTAGE = 0.10


def create_normalized_column(df, col_name):
    df[f'norm_{col_name}'] = 100 * df[col_name] / df[col_name].sum()
    return df


def drop_rows_where_col_has_value(df, col_name, value):
    df = df[df[col_name] != value]
    return df


def average_logs(logs):
    return pd.concat(
        [
            pd.DataFrame(log["entries"])[['name', 'type', 'total']]
            .pipe(drop_rows_where_col_has_value, col_name='type', value='Pet')
            .pipe(create_normalized_column, col_name='total') for log in logs
        ]
    ).groupby(['name']).agg(
        _std=('norm_total', lambda x: x.unique().std()),  # just 'std' will use ddof = 1
        _avg=('norm_total', 'mean'),
        _counts=('name', 'size'),
        _class=('type', 'max')
    ).sort_values("_avg")


# Date parameters need to be converted to milliseconds Unix format
def convert_to_unix(date):
    return str(1000 * int(datetime.strptime(date, "%Y-%m-%d").timestamp()))


def parse_users(users):
    user_dict = {}
    logger.info(f" Adding authentication for users: {[name for name in users.keys()]}.")
    for User, user_info in users.items():
        user_dict[user_info["username"]] = user_info["password"]
    return user_dict


def remove_irrelevant_roles(df: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"Removing players with avg less than {THRESHOLD_PERCENTAGE} of max.")
    return df.query(f'_avg > _avg.max() * {THRESHOLD_PERCENTAGE}')


def get_reports_key(guild: str, server: str, region: str) -> str:
    return f'<{guild}>-<{server}>-<{region}>'
