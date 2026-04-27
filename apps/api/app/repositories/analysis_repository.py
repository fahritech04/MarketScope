from datetime import datetime
import math
from typing import Any
import time

from supabase import Client


class AnalysisRepository:
    def __init__(self, client: Client):
        self.client = client

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, float) and math.isnan(value):
            return None
        if isinstance(value, dict):
            return {key: self._sanitize(val) for key, val in value.items()}
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        return value

    def _run(self, query_factory, retries: int = 3):
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                return query_factory().execute()
            except Exception as error:  # noqa: BLE001
                last_error = error
                message = str(error)
                transient = "Server disconnected" in message or "RemoteProtocolError" in message
                if attempt < retries and transient:
                    time.sleep(0.4 * attempt)
                    continue
                raise
        if last_error:
            raise last_error
        raise RuntimeError("Unknown database execution error.")

    def create_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload = self._sanitize(payload)
        response = self._run(lambda: self.client.table("analyses").insert(payload))
        return response.data[0]

    def list_analyses(self) -> list[dict[str, Any]]:
        response = self._run(
            lambda: self.client.table("analyses").select("*").order("created_at", desc=True)
        )
        return response.data or []

    def list_analyses_by_status(self, statuses: list[str], limit: int = 20) -> list[dict[str, Any]]:
        if not statuses:
            return []
        response = self._run(
            lambda: self.client.table("analyses")
            .select("*")
            .in_("status", statuses)
            .order("created_at", desc=False)
            .limit(limit)
        )
        return response.data or []

    def list_discovery_profiles(self, active_only: bool = True) -> list[dict[str, Any]]:
        try:
            query = self.client.table("discovery_profiles").select("*").order("created_at", desc=False)
            if active_only:
                query = query.eq("is_active", True)
            response = self._run(lambda: query)
            return response.data or []
        except Exception:
            # Tetap jalan meski tabel profile belum ada / belum termigrasi.
            return []

    def get_analysis(self, analysis_id: str) -> dict[str, Any] | None:
        response = self._run(
            lambda: self.client.table("analyses").select("*").eq("id", analysis_id).limit(1)
        )
        if not response.data:
            return None
        return response.data[0]

    def update_analysis_status(self, analysis_id: str, status: str) -> None:
        self._run(
            lambda: self.client.table("analyses")
            .update({"status": status, "updated_at": datetime.utcnow().isoformat()})
            .eq("id", analysis_id)
        )

    def create_sources(self, payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not payload:
            return []
        payload = self._sanitize(payload)
        response = self._run(lambda: self.client.table("sources").insert(payload))
        return response.data or []

    def clear_analysis_data(self, analysis_id: str) -> None:
        self._run(lambda: self.client.table("insights").delete().eq("analysis_id", analysis_id))
        self._run(lambda: self.client.table("scraped_items").delete().eq("analysis_id", analysis_id))
        self._run(lambda: self.client.table("sources").delete().eq("analysis_id", analysis_id))

    def list_sources(self, analysis_id: str) -> list[dict[str, Any]]:
        response = self._run(
            lambda: self.client.table("sources")
            .select("*")
            .eq("analysis_id", analysis_id)
            .order("created_at", desc=False)
        )
        return response.data or []

    def update_source_status(self, source_id: str, status: str) -> None:
        self._run(lambda: self.client.table("sources").update({"status": status}).eq("id", source_id))

    def create_scraped_items(self, payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not payload:
            return []
        payload = self._sanitize(payload)
        response = self._run(lambda: self.client.table("scraped_items").insert(payload))
        return response.data or []

    def list_scraped_items(self, analysis_id: str) -> list[dict[str, Any]]:
        response = self._run(
            lambda: self.client.table("scraped_items")
            .select("*")
            .eq("analysis_id", analysis_id)
            .order("created_at", desc=False)
        )
        return response.data or []

    def replace_scraped_items(self, analysis_id: str, items: list[dict[str, Any]]) -> None:
        self._run(lambda: self.client.table("scraped_items").delete().eq("analysis_id", analysis_id))
        if items:
            items = self._sanitize(items)
            self._run(lambda: self.client.table("scraped_items").insert(items))

    def upsert_insight(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload = self._sanitize(payload)
        response = self._run(lambda: self.client.table("insights").upsert(payload, on_conflict="analysis_id"))
        return response.data[0]

    def get_insight(self, analysis_id: str) -> dict[str, Any] | None:
        response = self._run(
            lambda: self.client.table("insights").select("*").eq("analysis_id", analysis_id).limit(1)
        )
        if not response.data:
            return None
        return response.data[0]

    def count_sources(self, analysis_id: str) -> int:
        sources = self.list_sources(analysis_id)
        return len(sources)

    def count_items(self, analysis_id: str) -> int:
        items = self.list_scraped_items(analysis_id)
        return len(items)
