import pytest

pytestmark = pytest.mark.django_db


def test_spoofed_extension_rejected_via_api(authenticated_client, spoofed_resume_file):
    response = authenticated_client.post(
        "/api/v1/submissions/",
        {"submission_type": "resume", "file": spoofed_resume_file},
        format="multipart",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_oversized_file_rejected_via_api(authenticated_client, oversized_resume_file):
    response = authenticated_client.post(
        "/api/v1/submissions/",
        {"submission_type": "resume", "file": oversized_resume_file},
        format="multipart",
    )
    assert response.status_code == 400


def test_disallowed_extension_rejected_via_api(authenticated_client):
    from django.core.files.uploadedfile import SimpleUploadedFile

    executable = SimpleUploadedFile(
        "resume.exe", b"MZ\x90\x00fake-executable", content_type="application/pdf"
    )
    response = authenticated_client.post(
        "/api/v1/submissions/",
        {"submission_type": "resume", "file": executable},
        format="multipart",
    )
    assert response.status_code == 400


def test_website_with_non_url_string_rejected(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/submissions/",
        {"submission_type": "website", "source_url": "not-a-url"},
        format="json",
    )
    assert response.status_code == 400


def test_github_with_non_github_domain_rejected_via_api(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/submissions/",
        {"submission_type": "github", "source_url": "https://evil.example.com/octocat"},
        format="json",
    )
    assert response.status_code == 400
