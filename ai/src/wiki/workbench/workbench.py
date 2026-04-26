from __future__ import annotations

from pathlib import Path

from .services.draft_service import WikiDraftService
from .services.publish_service import WikiPublishService
from .services.release_service import WikiReleaseService
from .services.schema_service import WikiSchemaService
from .services.diagnosis_service import WikiDiagnosisService
from .services.file_relation_service import WikiFileRelationService
from .services.graph_service import WikiGraphService
from .services.truth_service import WikiTruthService
from .services.version_service import WikiVersionService


class WikiWorkbench:
    """Core-side Wiki Workbench backend facade for truth/version management."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.truth = WikiTruthService(self.project_root)
        self.draft = WikiDraftService(self.project_root)
        self.version = WikiVersionService(self.project_root)
        self.publish = WikiPublishService(self.project_root)
        self.release = WikiReleaseService(self.project_root)
        self.schema = WikiSchemaService(self.project_root)
        self.files = WikiFileRelationService(self.project_root)
        self.graph = WikiGraphService(self.project_root)
        self.diagnosis = WikiDiagnosisService(self.project_root)
