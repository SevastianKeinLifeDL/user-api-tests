import os
import pytest
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def expected_asses(full_name: str) -> str:
    """Эталонное значение поля asses по ФИО."""
    parts = full_name.strip().split()
    if len(parts) < 3:
        raise ValueError(f"Ожидалось ФИО из трёх слов, получено: {full_name!r}")
    last, first, middle = parts[0], parts[1], parts[2]
    return last.upper() + first[0].upper() + middle[0].upper()


@pytest.fixture(scope="session")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()


@pytest.fixture
def created_user(api_client):
    payload = {
        "full_name": "Ткаченко Вячеслав Николаевич",
        "employee_id": "EMP-1001",
    }
    response = api_client.post("/users", json=payload, timeout=10)
    assert response.status_code == 201, response.text
    user = response.json()
    yield user
    api_client.delete(f"/users/{payload['employee_id']}", timeout=10)


def test_create_user_returns_201_and_persists(api_client):
    payload = {
        "full_name": "Ткаченко Вячеслав Николаевич",
        "employee_id": "EMP-1001",
    }
    create_resp = api_client.post("/users", json=payload, timeout=10)
    assert create_resp.status_code == 201, create_resp.text

    get_resp = api_client.get(f"/users/{payload['employee_id']}", timeout=10)
    assert get_resp.status_code == 200
    assert get_resp.json()["employee_id"] == payload["employee_id"]

    api_client.delete(f"/users/{payload['employee_id']}", timeout=10)


@pytest.mark.parametrize("full_name", [
    "Ткаченко Вячеслав Николаевич",
    "Иванов Иван Иванович",
    "Петрова Анна Сергеевна",
])
def test_create_user_computes_asses_correctly(api_client, full_name):
    employee_id = f"EMP-{abs(hash(full_name)) % 10000}"
    payload = {"full_name": full_name, "employee_id": employee_id}

    resp = api_client.post("/users", json=payload, timeout=10)
    assert resp.status_code == 201, resp.text
    created = resp.json()

    expected = expected_asses(full_name)
    assert created["asses"] == expected, (
        f"Для {full_name!r} ожидали asses={expected!r}, получили {created['asses']!r}"
    )

    api_client.delete(f"/users/{employee_id}", timeout=10)


def test_delete_user_by_employee_id(api_client, created_user):
    employee_id = created_user["employee_id"]

    delete_resp = api_client.delete(f"/users/{employee_id}", timeout=10)
    assert delete_resp.status_code in (200, 204), delete_resp.text

    get_resp = api_client.get(f"/users/{employee_id}", timeout=10)
    assert get_resp.status_code == 404, "Пользователь не должен находиться после удаления"


def test_update_user_via_put_replaces_resource(api_client, created_user):
    employee_id = created_user["employee_id"]
    new_full_name = "Сидоров Пётр Алексеевич"
    expected_new_asses = expected_asses(new_full_name)

    put_resp = api_client.put(
        f"/users/{employee_id}",
        json={"full_name": new_full_name, "employee_id": employee_id},
        timeout=10,
    )
    assert put_resp.status_code == 200, put_resp.text
    updated = put_resp.json()
    assert updated["full_name"] == new_full_name
    assert updated["asses"] == expected_new_asses
    assert updated["employee_id"] == employee_id


def test_update_user_persists_to_db(api_client, created_user):
    employee_id = created_user["employee_id"]
    new_full_name = "Новиков Дмитрий Олегович"
    expected_new_asses = expected_asses(new_full_name)

    put_resp = api_client.put(
        f"/users/{employee_id}",
        json={"full_name": new_full_name, "employee_id": employee_id},
        timeout=10,
    )
    assert put_resp.status_code == 200, put_resp.text

    get_resp = api_client.get(f"/users/{employee_id}", timeout=10)
    assert get_resp.status_code == 200
    persisted = get_resp.json()
    assert persisted["full_name"] == new_full_name
    assert persisted["asses"] == expected_new_asses, (
        "Поле asses не пересчиталось или не сохранилось в БД"
    )


def test_update_user_put_changes_full_name_and_asses(api_client, created_user):
    employee_id = created_user["employee_id"]
    old_asses = created_user["asses"]

    new_full_name = "Морозова Екатерина Викторовна"
    put_resp = api_client.put(
        f"/users/{employee_id}",
        json={"full_name": new_full_name, "employee_id": employee_id},
        timeout=10,
    )
    assert put_resp.status_code == 200, put_resp.text
    new_asses = put_resp.json()["asses"]

    assert new_asses != old_asses, "asses должен измениться при смене ФИО"
    assert new_asses == expected_asses(new_full_name)


def test_update_nonexistent_user_returns_404(api_client):
    put_resp = api_client.put(
        "/users/EMP-9999",
        json={"full_name": "Сидоров Пётр Алексеевич", "employee_id": "EMP-9999"},
        timeout=10,
    )
    assert put_resp.status_code == 404, put_resp.text