from shop.app import create_app

def test_app_builds():
    assert create_app() is not None
