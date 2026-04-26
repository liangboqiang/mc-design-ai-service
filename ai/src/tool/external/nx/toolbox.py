from __future__ import annotations

from pathlib import Path
from typing import Any

from .api_client import NXApiClient


class NXToolbox:
    toolbox_name = "nx"
    tags = ("external", "nx", "cad", "api")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None
        self.client = NXApiClient()

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "NXToolbox":
        return NXToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
        "nx.BatchUpdateParams": self._make_executor("BatchUpdateParams"),
        "nx.BlendShaftEndEdges": self._make_executor("BlendShaftEndEdges"),
        "nx.build_feature": self._make_executor("build_feature"),
        "nx.BuildCamLobe": self._make_executor("BuildCamLobe"),
        "nx.BuildCamLobeArray": self._make_executor("BuildCamLobeArray"),
        "nx.BuildCamshaft": self._make_executor("BuildCamshaft"),
        "nx.BuildCamshaftOneClick": self._make_executor("BuildCamshaftOneClick"),
        "nx.BuildJournalFace": self._make_executor("BuildJournalFace"),
        "nx.BuildOrUpdateEndBoss": self._make_executor("BuildOrUpdateEndBoss"),
        "nx.create_prt": self._make_executor("create_prt"),
        "nx.CreateImage": self._make_executor("CreateImage"),
        "nx.CreateNewPart": self._make_executor("CreateNewPart"),
        "nx.CreateParam": self._make_executor("CreateParam"),
        "nx.CutShaftGrooveByBlock": self._make_executor("CutShaftGrooveByBlock"),
        "nx.ExitAnimation": self._make_executor("ExitAnimation"),
        "nx.ExportSnapshot": self._make_executor("ExportSnapshot"),
        "nx.FindParams": self._make_executor("FindParams"),
        "nx.FitView": self._make_executor("FitView"),
        "nx.GetAllParamsList": self._make_executor("GetAllParamsList"),
        "nx.GetAllViewNames": self._make_executor("GetAllViewNames"),
        "nx.GetDrawingSheetNameList": self._make_executor("GetDrawingSheetNameList"),
        "nx.GetDriveParamsList": self._make_executor("GetDriveParamsList"),
        "nx.GetViewStyle": self._make_executor("GetViewStyle"),
        "nx.GetWorkPartInfo": self._make_executor("GetWorkPartInfo"),
        "nx.HighLightDim": self._make_executor("HighLightDim"),
        "nx.ImportCamProfile": self._make_executor("ImportCamProfile"),
        "nx.ListSnapshotNames": self._make_executor("ListSnapshotNames"),
        "nx.modify_parameter": self._make_executor("modify_parameter"),
        "nx.MountBossToShaft": self._make_executor("MountBossToShaft"),
        "nx.MountCamLobesToShaft": self._make_executor("MountCamLobesToShaft"),
        "nx.OpenDrawingSheet": self._make_executor("OpenDrawingSheet"),
        "nx.OpenPart": self._make_executor("OpenPart"),
        "nx.OpenTCPart": self._make_executor("OpenTCPart"),
        "nx.RotateAndScaleView": self._make_executor("RotateAndScaleView"),
        "nx.SetViewStyle": self._make_executor("SetViewStyle"),
        "nx.SmoothSwitchToView": self._make_executor("SmoothSwitchToView"),
        "nx.SwitchView": self._make_executor("SwitchView"),
        "nx.Test": self._make_executor("Test"),
        "nx.UniteLobesToShaft": self._make_executor("UniteLobesToShaft"),
        "nx.UpdateParam": self._make_executor("UpdateParam"),
        "nx.UpdateView": self._make_executor("UpdateView"),
        }

    def _make_executor(self, tool_name: str):
        def _executor(args: dict[str, Any]):
            payload = dict(args or {})
            if "user_id" not in payload and self.runtime is not None:
                payload["user_id"] = self.runtime.settings.user_id
            return self.client.call(tool_name, payload)
        _executor.__name__ = f"_exec_nx_{tool_name}"
        return _executor
