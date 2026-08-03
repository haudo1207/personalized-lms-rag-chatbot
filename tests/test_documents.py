SAMPLE_TEXT = (
    "Khoa chinh la thuoc tinh hoac tap thuoc tinh dung de xac dinh duy nhat "
    "moi ban ghi trong mot bang co so du lieu quan he. Khoa ngoai dung de "
    "lien ket du lieu giua cac bang va tham chieu den khoa chinh cua bang khac."
).encode("utf-8")


def _upload(client, course_id, user_id, headers, filename="notes.txt", content=SAMPLE_TEXT):
    return client.post(
        "/documents/upload",
        data={"course_id": course_id, "user_id": user_id},
        files={"file": (filename, content, "text/plain")},
        headers=headers,
    )


def test_upload_document_indexes_immediately(client, new_user, new_course, user_headers):
    resp = _upload(client, new_course["id"], new_user["id"], user_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "indexed"
    assert body["chunks"] >= 1

    listed = client.get("/documents/", headers=user_headers)
    assert listed.status_code == 200
    doc = next(d for d in listed.json() if d["id"] == body["document_id"])
    assert doc["status"] == "indexed"
    assert doc["course_id"] == new_course["id"]


def test_upload_rejects_unsupported_extension(client, new_user, new_course, user_headers):
    resp = _upload(
        client, new_course["id"], new_user["id"], user_headers, filename="notes.exe", content=b"whatever"
    )
    assert resp.status_code == 400


def test_upload_rejects_empty_document(client, new_user, new_course, user_headers):
    resp = _upload(client, new_course["id"], new_user["id"], user_headers, content=b"   ")
    assert resp.status_code == 422


def test_upload_forbidden_for_non_owned_course(client, new_user, unique_suffix, admin_headers, user_headers):
    others_course = client.post(
        "/courses/",
        json={"course_code": f"OTH{unique_suffix}", "course_name": "Not yours"},
        headers=admin_headers,
    ).json()
    resp = _upload(client, others_course["id"], new_user["id"], user_headers)
    assert resp.status_code == 403


def test_retry_index_on_already_indexed_document(client, new_user, new_course, user_headers):
    upload_resp = _upload(client, new_course["id"], new_user["id"], user_headers)
    document_id = upload_resp.json()["document_id"]

    retry_resp = client.post(f"/documents/{document_id}/index", headers=user_headers)
    assert retry_resp.status_code == 200
    assert retry_resp.json()["chunks"] >= 1


def test_retry_index_missing_document_returns_404(client, user_headers):
    resp = client.post("/documents/999999/index", headers=user_headers)
    assert resp.status_code == 404


def test_documents_endpoints_require_auth(client, new_course, new_user):
    resp = _upload(client, new_course["id"], new_user["id"], headers=None)
    assert resp.status_code == 401

    resp = client.get("/documents/")
    assert resp.status_code == 401


def test_rename_document(client, new_user, new_course, user_headers):
    document_id = _upload(client, new_course["id"], new_user["id"], user_headers).json()["document_id"]

    resp = client.patch(
        f"/documents/{document_id}", json={"file_name": "renamed.txt"}, headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["file_name"] == "renamed.txt"


def test_rename_document_forbidden_for_other_user(
    client, new_user, new_course, user_headers, second_user_headers
):
    document_id = _upload(client, new_course["id"], new_user["id"], user_headers).json()["document_id"]

    resp = client.patch(
        f"/documents/{document_id}", json={"file_name": "hijacked.txt"}, headers=second_user_headers
    )
    assert resp.status_code == 403


def test_download_document_returns_original_bytes(client, new_user, new_course, user_headers):
    document_id = _upload(client, new_course["id"], new_user["id"], user_headers).json()["document_id"]

    resp = client.get(f"/documents/{document_id}/download", headers=user_headers)
    assert resp.status_code == 200
    assert resp.content == SAMPLE_TEXT


def test_delete_document_removes_row_and_chunks(client, new_user, new_course, user_headers):
    from backend.services.vector_store import search_chunks

    document_id = _upload(client, new_course["id"], new_user["id"], user_headers).json()["document_id"]
    assert search_chunks("Khoa chinh", course_id=new_course["id"], top_k=5)

    resp = client.delete(f"/documents/{document_id}", headers=user_headers)
    assert resp.status_code == 200

    listed = client.get("/documents/", headers=user_headers)
    assert not any(d["id"] == document_id for d in listed.json())
    assert not search_chunks("Khoa chinh", course_id=new_course["id"], top_k=5)


def test_delete_document_missing_returns_404(client, user_headers):
    resp = client.delete("/documents/999999", headers=user_headers)
    assert resp.status_code == 404
