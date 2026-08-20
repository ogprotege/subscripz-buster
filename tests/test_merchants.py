from subscripz.merchants import identify_merchant


def test_known_domain():
    assert identify_merchant("noreply@netflix.com", "Your receipt") == ("netflix", "Netflix")


def test_mailish_subdomain_adobe():
    key, name = identify_merchant("billing@email.adobe.com", "Invoice")
    assert name == "Adobe"
    assert key == "adobe"


def test_esp_uses_subject_brand():
    assert identify_merchant(
        "bounce@amazonses.com",
        "Your Netflix subscription was renewed — $15.99",
    ) == ("netflix", "Netflix")


def test_esp_without_brand_is_dropped():
    assert identify_merchant("bounce@amazonses.com", "Your receipt is ready") is None


def test_consumer_inbox_without_brand_is_dropped():
    assert identify_merchant("friend@gmail.com", "lunch tomorrow") is None


def test_notion_mail_subdomain():
    assert identify_merchant("team@mail.notion.so", "Your Notion receipt")[1] == "Notion"


def test_display_name_angle_addr():
    assert identify_merchant("Spotify <no-reply@spotify.com>", "Receipt")[1] == "Spotify"
