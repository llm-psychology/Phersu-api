import importlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    import os
    root = tmp_path_factory.mktemp("split-api")
    names={"PERSONA_DATA_DIR":root/"personas", "PSYCHANCHOR_DATA_DIR":root/"anchor",
           "CONVERSATION_DATA_DIR":root/"history", "API_DATA_DIR":root/"api",
           "UNITY_BUILD_DIR":root/"missing-unity"}
    previous={key:os.environ.get(key) for key in names}
    os.environ.update({key:str(value) for key,value in names.items()})
    from persona_api import settings
    importlib.reload(settings)
    from persona_api import app as module
    importlib.reload(module)
    sample={"基本資料":{"id":"5c771e5f3c","姓名":"示例角色","年紀":28,"性別":"女"},
            "人格屬性":{"人格特質":["外向活潑"],"社交能力":[],"能力屬性":[]},
            "生平故事":"虛構故事","語言行為":"自然","簡化行為":"喜歡交流"}
    target=root/"personas"/"5c771e5f3c_example.json"
    target.write_text(json.dumps(sample,ensure_ascii=False),encoding="utf-8")
    with TestClient(module.app) as value:
        yield value
    for key,value in previous.items():
        if value is None:
            os.environ.pop(key,None)
        else:
            os.environ[key]=value


@pytest.mark.parametrize("path", ["/", "/fire_simulation", "/fire_simulation_sse", "/schedule-control", "/llm-schedule-control", "/simulation-frontend"])
def test_packaged_static_pages(client,path):
    response=client.get(path)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_health_and_persona_list_without_model(client):
    assert client.get("/health").json() == {"status":"ok"}
    result=client.get("/humanoids")
    assert result.status_code == 200
    assert result.json()["count"] == 1


def test_panic_scale_is_0_to_100():
    from persona_api.app import get_agent_status
    assert get_agent_status(SimpleNamespace(panic_level=10)) == "正常"
    assert get_agent_status(SimpleNamespace(panic_level=80)) == "恐慌中"


def test_generation_does_not_automatically_create_interview(client, monkeypatch):
    from unittest.mock import AsyncMock
    from persona_api import app as module
    generate = AsyncMock(side_effect=["0000000001", "0000000002"])
    interview = AsyncMock(side_effect=AssertionError("Persona generation must stop at JSON"))
    monkeypatch.setattr(module, "generate_a_persona", generate)
    monkeypatch.setattr(module, "generate_persona_rag_by_id", interview)
    response = client.post("/generate?count=2")
    assert response.status_code == 200
    assert response.json()["persona_ids"] == ["0000000001", "0000000002"]
    assert interview.await_count == 0


def test_sse_keeps_events_when_next_tick_has_fewer_events(client):
    import asyncio
    from persona_api import app as module

    async def run():
        state = {"tick": 1, "status": "running", "events": ["first", "second"]}
        module.active_simulations["stream-regression"] = state
        response = await module.get_simulation_stream("stream-regression")
        stream = response.body_iterator
        try:
            assert "event: connected" in await anext(stream)
            assert '"first"' in await anext(stream)
            state.update(tick=2, events=["third"])
            update = await anext(stream)
            assert '"third"' in update
            state.update(status="paused")
            assert '"paused"' in await anext(stream)
            state.update(status="completed", finished=True, final_stats={"total_agents": 3})
            assert '"total_agents": 3' in await anext(stream)
            assert "event: simulation_ended" in await anext(stream)
        finally:
            await stream.aclose()
            module.active_simulations.pop("stream-regression", None)

    asyncio.run(run())
