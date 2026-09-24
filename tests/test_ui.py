def test_demo_shell_and_assets_are_available(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    for path in ("/static/app.js", "/static/styles.css", "/static/views.js", "/static/job.js"):
        assert client.get(path).status_code == 200
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
