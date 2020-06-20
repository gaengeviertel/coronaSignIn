def test_headline_exists(client):
    page = client.get("/")
    assert b"Moin! lieber Gast!" in page.data
