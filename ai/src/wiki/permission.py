from __future__ import annotations


class WikiPermissionGuard:
    def __init__(self, permission_scope, metadata_by_page=None):  # noqa: ANN001
        self.permission_scope = permission_scope
        self.metadata_by_page = metadata_by_page or {}

    def can_read_page(self, page_id: str) -> bool:
        metadata = self.metadata_by_page.get(page_id)
        if metadata is None:
            return True
        return int(getattr(metadata, "permission_level", 1)) <= int(getattr(self.permission_scope, "level", 1))

    def require_read_page(self, page_id: str) -> None:
        if not self.can_read_page(page_id):
            raise PermissionError(f"Wiki page is above current permission scope: {page_id}")

    def filter_rows(self, rows: list[dict]) -> list[dict]:
        return [
            row
            for row in rows
            if self.can_read_page(str(row.get("page_id") or row.get("id") or ""))
        ]
