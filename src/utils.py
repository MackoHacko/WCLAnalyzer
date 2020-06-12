from datetime import datetime

import pandas as pd

from loggers.logger import Logger

# Initialize logger
logger = Logger().getLogger(__file__)

THRESHOLD_PERCENTAGE = 0.10


def average_logs(logs):
    done_dfs = []
    for log in logs:
        df = pd.json_normalize(log, 'entries')
        temp_df = df.loc[:, df.columns.intersection(
            ['name', 'type', 'total', 'activeTime'])]
        temp_df['total'] = 100 * temp_df['total'] / temp_df['total'].sum()
        temp_df = temp_df[temp_df['type'] != 'Pet']
        done_dfs.append(temp_df)
    temp_df = pd.concat(done_dfs)

    mean = temp_df.groupby(['name'])['total'].agg(lambda x: x.unique().mean())
    std = temp_df.groupby(['name'])['total'].agg(lambda x: x.unique().std())
    classes = temp_df.groupby(['name'])['type'].agg(lambda x: x.unique())
    count = temp_df['name'].value_counts()

    return pd.concat(
        [
            classes.rename('class'),
            mean.rename('Avg'),
            std.rename('std'),
            count.rename('Counts')
        ],
        axis = 1
    ).sort_values('Avg')


# Date parameters need to be converted to milliseconds Unix format
def convert_to_unix(date):
    return str(1000 * int(datetime.strptime(date, "%Y-%m-%d").timestamp()))


def parse_users(users):
    user_dict = {}
    logger.info(f" Adding authentication for users: {[name for name in users.keys()]}.")
    for _, user_info in users.items():
        user_dict[user_info["username"]] = user_info["password"]
    return user_dict


def remove_irrelevant_roles(df: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"Removing players with avg less than {THRESHOLD_PERCENTAGE} of max.")
    return df.query(f'Avg > Avg.max() * {THRESHOLD_PERCENTAGE}')


def get_reports_key(guild: str, server: str, region: str) -> str:
    return f'<{guild}>-<{server}>-<{region}>'
