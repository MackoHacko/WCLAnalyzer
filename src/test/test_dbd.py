from testcontainers.compose import DockerCompose
from dbd_client import DBDClient
import os
import uuid

# needed for travis
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

DBD_PORT = 8000

GUILD_IDS = [str(uuid.uuid4()) for _ in range(2)]
REPORT_IDS = [str(uuid.uuid4()) for _ in range(3)]
LOG_IDS = [str(uuid.uuid4()) for _ in range(3)]


def get_guild_template(guild_id, reports = {}, logs = {}):
    return {
        'guildId': guild_id,
        'reports': reports,
        'logs': logs
    }


def get_report_input_templates(report_ids, data):
    report_templates = [
        {
            'id': report_id,
            'data': d
        } for report_id, d in zip(report_ids, data)
    ]
    return report_templates[0] if type(report_ids) == str else report_templates


def get_log_input_templates(log_ids, data):
    log_templates = [
        {
            "id": log_id,
            "data": d
        } for log_id, d in zip(log_ids, data)
    ]
    return log_templates[0] if type(log_ids) == str else log_templates


def parse_templates(report_template):
    if type(report_template) == list:
        return {
            rt['id']: rt['data'] for rt in report_template
        }
    return {report_template['id']: report_template['data']}


def test_should_create_guild():
    with DockerCompose(
        os.getcwd() + "/test",
        compose_file_name="docker-compose-dynamodb-test.yaml",
        pull=True
    ) as compose:
        host = compose.get_service_host("dynamodb-local-test", DBD_PORT)
        port = compose.get_service_port("dynamodb-local-test", DBD_PORT)
        assert host == "0.0.0.0" and port == "8001"

        client = DBDClient(f"http://{host}:{port}")

        client.create_guild(GUILD_IDS[0])
        guild = client.get_guild(GUILD_IDS[0])
        assert guild == get_guild_template(GUILD_IDS[0])


def test_should_add_report():
    with DockerCompose(
        os.getcwd() + "/test",
        compose_file_name="docker-compose-dynamodb-test.yaml",
        pull=True
    ) as compose:
        host = compose.get_service_host("dynamodb-local-test", DBD_PORT)
        port = compose.get_service_port("dynamodb-local-test", DBD_PORT)
        assert host == "0.0.0.0" and port == "8001"

        client = DBDClient(f"http://{host}:{port}")

        client.create_guild(GUILD_IDS[0])

        report = get_report_input_templates(
            REPORT_IDS[0],
            {"title": "Great Test Report", "meta": "Some metadata"}
        )
        client.add_report(GUILD_IDS[0], report)
        report_resp = client.get_report(GUILD_IDS[0], REPORT_IDS[0])
        assert parse_templates(report) == report_resp


def test_should_get_reports_from_correct_guild():
    with DockerCompose(
        os.getcwd() + "/test",
        compose_file_name="docker-compose-dynamodb-test.yaml",
        pull=True
    ) as compose:
        host = compose.get_service_host("dynamodb-local-test", DBD_PORT)
        port = compose.get_service_port("dynamodb-local-test", DBD_PORT)
        assert host == "0.0.0.0" and port == "8001"

        client = DBDClient(f"http://{host}:{port}")

        [client.create_guild(guild_id) for guild_id in GUILD_IDS]

        reports = get_report_input_templates(
            REPORT_IDS,
            [
                {"title": "Great Test Report 1", "meta": "Some metadata 1"},
                {"title": "Great Test Report 2", "meta": "Some metadata 2"},
                {"title": "Great Test Report 3", "meta": "Some metadata 3"}
            ]
        )
        client.add_report(GUILD_IDS[0], reports[0])
        client.add_report(GUILD_IDS[0], reports[1])
        client.add_report(GUILD_IDS[1], reports[2])

        report_resp = client.get_all_reports(GUILD_IDS[0])
        assert parse_templates(reports[:2]) == report_resp


def test_should_add_log():
    with DockerCompose(
        os.getcwd() + "/test",
        compose_file_name="docker-compose-dynamodb-test.yaml",
        pull=True
    ) as compose:
        host = compose.get_service_host("dynamodb-local-test", DBD_PORT)
        port = compose.get_service_port("dynamodb-local-test", DBD_PORT)
        assert host == "0.0.0.0" and port == "8001"

        client = DBDClient(f"http://{host}:{port}")

        client.create_guild(GUILD_IDS[0])

        log = get_log_input_templates(
            [LOG_IDS[0] + "-ragnaros-dmg"],
            [{"dmg": {"macko": 1, "lucko": 2}, "meta": "Some metadata"}]
        )[0]
        client.add_log(GUILD_IDS[0], log)
        log_resp = client.get_log(GUILD_IDS[0], LOG_IDS[0], "ragnaros", "dmg")
        assert parse_templates(log) == log_resp


def test_should_get_logs_from_correct_guild():
    with DockerCompose(
        os.getcwd() + "/test",
        compose_file_name="docker-compose-dynamodb-test.yaml",
        pull=True
    ) as compose:
        host = compose.get_service_host("dynamodb-local-test", DBD_PORT)
        port = compose.get_service_port("dynamodb-local-test", DBD_PORT)
        assert host == "0.0.0.0" and port == "8001"

        client = DBDClient(f"http://{host}:{port}")

        [client.create_guild(guild_id) for guild_id in GUILD_IDS]

        logs = get_log_input_templates(
            [
                log_id + enc for log_id, enc in zip(
                    LOG_IDS,
                    ["-ragnaros-dmg", "-huhuran-healing", "-thrall-dmg"]
                )
            ],
            [
                {"dmg": {"macko": 1, "lucko": 2}, "meta": "Some metadata"},
                {"healing": {"macko": 1, "lucko": 2}, "meta": "Some metadata"},
                {"dmg": {"macko": 1, "lucko": 2}, "meta": "Some metadata"}
            ]
        )
        client.add_log(GUILD_IDS[0], logs[0])
        client.add_log(GUILD_IDS[0], logs[1])
        client.add_log(GUILD_IDS[1], logs[2])

        log_resp = client.get_all_logs(GUILD_IDS[0])
        assert parse_templates(logs[:2]) == log_resp
