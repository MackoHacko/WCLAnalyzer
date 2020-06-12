import boto3
from botocore.exceptions import ClientError
from loggers.logger import Logger
from dotenv import load_dotenv, find_dotenv
import os
import uuid


class DBDClient():

    def __init__(
        self,
        endpoint_url = None
    ) -> None:
        if not endpoint_url:
            endpoint_url = os.getenv("DBD_HOST")
        self.__dbd_resource = boto3.resource(
            'dynamodb',
            endpoint_url = endpoint_url,
            region_name= 'eu-west-1'
        )
        self.logger = Logger().getLogger(__file__)
        self.logger.info("Initialize DBDClient.")
        self.__table = None

    def __get_log_name(self, report_id, encounter, log_type):
        return "-".join([report_id, encounter, log_type])

    def __set_table(self):
        if not self.__table:
            self.__table = self.__create_reports_table()

    def __create_reports_table(self):
        try:
            table = self.__dbd_resource.create_table(
                TableName = "Reports",
                KeySchema = [
                    {
                        'AttributeName': "guildId",
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions = [
                    {
                        'AttributeName': "guildId",
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput = {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            self.logger.info("Created table Reports.")
            self.logger.debug(table)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                self.logger.info("Table already exists, using existing table.")
                table = self.__dbd_resource.Table("Reports")
            else:
                self.logger.exception(e)
        return table

    def create_guild(self, guild_id):
        try:
            self.__set_table()
            guild = self.__table.put_item(
                TableName = "Reports",
                Item = {
                    "guildId": guild_id,
                    "reports": {},
                    "logs": {}
                },
                ConditionExpression = 'attribute_not_exists(guildId)'
            )
            self.logger.info(f"Created guild '{guild_id}'.")
            self.logger.debug(guild)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                self.logger.warning(f"Guild '{guild_id}' already exists in db. Skipping creation.")
            else:
                self.logger.exception(e)

    def add_report(self, guild_id, report):
        self.__set_table()
        try:
            report = self.__table.update_item(
                TableName = "Reports",
                Key={
                    'guildId': guild_id
                },
                UpdateExpression="set reports.#rId = if_not_exists(reports.#rId, :r)",
                ExpressionAttributeValues={
                    ':r': report["data"]
                },
                ExpressionAttributeNames={
                    '#rId': report["id"]
                },
                ConditionExpression = 'attribute_not_exists(reports.#rId)'
            )
            self.logger.info(f"Added report for guild '{guild_id}'.")
            self.logger.debug(report)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                self.logger.warning(
                    f"Report '{report['id']}' already exists in db for guild '{guild_id}'. " +
                    "Skipping creation."
                )
            else:
                self.logger.exception(e)

    def add_log(self, guild_id, log):
        self.__set_table()
        try:
            log = self.__table.update_item(
                TableName = "Reports",
                Key={
                    'guildId': guild_id
                },
                UpdateExpression="set logs.#lId = if_not_exists(logs.#lId, :l)",
                ExpressionAttributeValues={
                    ':l': log["data"]
                },
                ExpressionAttributeNames={
                    '#lId': log["id"]
                },
                ConditionExpression = 'attribute_not_exists(logs.#lId)'
            )
            self.logger.info(f"Added log for guild '{guild_id}'.")
            self.logger.debug(log)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                self.logger.warning(
                    f"Log '{log['id']}' already exists in db for guild '{guild_id}'. " +
                    "Skipping creation."
                )
            else:
                self.logger.exception(e)

    def __get_all_guild_data(self, guild_id):
        self.__set_table()
        try:
            response = self.__table.get_item(Key={'guildId': guild_id})
            self.logger.debug(response)
        except ClientError as e:
            self.logger.exception(e.response['Error']['Message'])
        else:
            try:
                return response["Item"]
            except KeyError:
                self.logger.exception("No guild with that ID in database.")

    def get_all_guild_names(self):
        return self.__table.scan(
            AttributesToGet=["guildId"]
        )["Items"]

    def get_guild(self, guild_id):
        return self.__table.get_item(
            Key={"guildId": guild_id}
        )["Item"]

    def get_all_reports(self, guild_id):
        return self.__table.get_item(
            Key={"guildId": guild_id},
            AttributesToGet=["reports"]
        )["Item"]["reports"]

    def get_report(self, guild_id, report_id):
        return self.get_all_reports(
            guild_id
        )

    def get_all_logs(self, guild_id):
        return self.__table.get_item(
            Key={"guildId": guild_id},
            AttributesToGet=["logs"]
        )["Item"]["logs"]

    def get_log(self, guild_id, report_id, encounter, log_type):
        return self.get_all_logs(
            guild_id
        )[self.__get_log_name(report_id, encounter, log_type)]


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    client = DBDClient()

    guild_ids = ["Inheritance-Razorgore-EU", "CoolGuild-Razorgore-EU"]

    [client.create_guild(guild) for guild in guild_ids]

    report_ids = [str(uuid.uuid4()) for i in range(4)]

    reports_1 = [
        {
            "id": report_ids[0],
            "data": {"title": "mc alt run", "date": "26/5-2020"}
        },
        {
            "id": report_ids[1],
            "data": {"title": "onyxia main raid", "date": "10/4-2020"}
        }
    ]

    reports_2 = [
        {
            "id": report_ids[2],
            "data": {"title": "bwl speedrun", "date": "25/6-2020"}
        },
        {
            "id": report_ids[3],
            "data": {"title": "aq beta test", "date": "30/7-2020"}
        }
    ]

    [
        client.add_report(
            guild_id = guild_ids[0],
            report = report
        ) for report in reports_1
    ]

    [
        client.add_report(
            guild_id = guild_ids[1],
            report = report
        ) for report in reports_2
    ]

    logs_1 = [
        {
            "id": report_ids[0] + "-ragnaros-dmg",
            "data": {"macko": 1, "ozzy": 9999}
        },
        {
            "id": report_ids[0] + "-ragnaros-healing",
            "data": {"lucci": 9996}
        },
        {
            "id": report_ids[0] + "-trash-dmg",
            "data": {"macko": 1, "ozzy": 123}
        },
        {
            "id": report_ids[1] + "-onyxia-dmg",
            "data": {"macko": 1, "ozzy": 123}
        }
    ]

    logs_2 = [
        {
            "id": report_ids[2] + "-broodlord-dmg",
            "data": {"macko": -500, "ozzy": 100}
        },
        {
            "id": report_ids[3] + "-huhuran-dmg",
            "data": {"macko": 10, "ozzy": 123}
        },
        {
            "id": report_ids[3] + "-huhuran-healing",
            "data": {"lucci": 321}
        }
    ]

    [
        client.add_log(
            guild_id = guild_ids[0],
            log = log
        ) for log in logs_1
    ]

    [
        client.add_log(
            guild_id = guild_ids[1],
            log = log
        ) for log in logs_2
    ]

    client.logger.info(client.get_all_reports(guild_ids[0]))
    client.logger.info(client.get_report(guild_ids[0], report_ids[0]))
    client.logger.info(client.get_all_logs(guild_ids[0]))
    client.logger.info(client.get_log(guild_ids[0], report_ids[0], "ragnaros", "dmg"))
    client.logger.info(client.get_all_reports(guild_ids[1]))
    client.logger.info(client.get_report(guild_ids[1], report_ids[2]))
    client.logger.info(client.get_all_logs(guild_ids[1]))
    client.logger.info(client.get_log(guild_ids[1], report_ids[3], "huhuran", "dmg"))
