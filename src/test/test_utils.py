import utils


def test_parse_users():
    users = {"Lucas": {"username": "Lucas", "password": "lucas123"}}
    parsed_users = utils.parse_users(users)
    assert parsed_users == {"Lucas": "lucas123"}


def test_get_reports_key():
    guild = "Inheritance"
    server = "Razorgore"
    region = "EU"
    expected = f"<{guild}>-<{server}>-<{region}>"
    assert utils.get_reports_key(guild, server, region) == expected
