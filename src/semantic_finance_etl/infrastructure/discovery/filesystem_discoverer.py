from __future__ import annotations

import fnmatch
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from semantic_finance_etl.config.models.source_config import SourceConfig
from semantic_finance_etl.contracts.source_discoverer import SourceDiscoverer
from semantic_finance_etl.domain.models.hook_payloads import DiscoveredAsset


class FilesystemSourceDiscoverer(SourceDiscoverer[None]):
    discoverer_name = "filesystem"

    def discover(
        self,
        source_config: SourceConfig,
        params: None = None,
    ) -> list[DiscoveredAsset]:
        root_path = Path(source_config.path)

        if not root_path.exists():
            raise FileNotFoundError(
                f"Source path does not exist for source '{source_config.source_id}': "
                f"{root_path}"
            )

        if not root_path.is_dir():
            raise ValueError(
                f"Source path must be a directory for source '{source_config.source_id}': "
                f"{root_path}"
            )

        candidate_paths = self._collect_candidate_paths(
            root_path=root_path,
            recursive=source_config.recursive,
        )

        discovered_assets: list[DiscoveredAsset] = []

        for file_path in candidate_paths:
            relative_path = str(file_path.relative_to(root_path))

            if not self._matches_include_patterns(
                file_path=file_path,
                relative_path=relative_path,
                include_patterns=source_config.include_patterns,
            ):
                continue

            if self._matches_exclude_patterns(
                file_path=file_path,
                relative_path=relative_path,
                exclude_patterns=source_config.exclude_patterns,
            ):
                continue

            stat = file_path.stat()

            discovered_assets.append(
                DiscoveredAsset(
                    path=str(file_path),
                    source_id=source_config.source_id,
                    size_bytes=stat.st_size,
                    modified_at_utc=datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ),
                    created_at_utc=datetime.fromtimestamp(
                        getattr(stat, "st_birthtime", stat.st_mtime), tz=timezone.utc
                    ),
                    content_hash=self._compute_sha256(file_path),
                    extra_metadata={
                        "relative_path": relative_path,
                        "file_name": file_path.name,
                        "suffix": file_path.suffix.lower(),
                    },
                )
            )

        return discovered_assets

    def _collect_candidate_paths(
        self,
        *,
        root_path: Path,
        recursive: bool,
    ) -> list[Path]:
        if recursive:
            paths = [path for path in root_path.rglob("*") if path.is_file()]
        else:
            paths = [path for path in root_path.iterdir() if path.is_file()]

        return sorted(paths, key=lambda path: str(path).lower())

    def _matches_include_patterns(
        self,
        *,
        file_path: Path,
        relative_path: str,
        include_patterns: list[str],
    ) -> bool:
        if not include_patterns:
            return True

        file_name = file_path.name

        return any(
            fnmatch.fnmatch(file_name, pattern)
            or fnmatch.fnmatch(relative_path, pattern)
            for pattern in include_patterns
        )

    def _matches_exclude_patterns(
        self,
        *,
        file_path: Path,
        relative_path: str,
        exclude_patterns: list[str],
    ) -> bool:
        if not exclude_patterns:
            return False

        file_name = file_path.name

        return any(
            fnmatch.fnmatch(file_name, pattern)
            or fnmatch.fnmatch(relative_path, pattern)
            for pattern in exclude_patterns
        )

    def _compute_sha256(self, file_path: Path) -> str:
        hasher = hashlib.sha256()

        with file_path.open("rb") as file:
            while chunk := file.read(1024 * 1024):
                hasher.update(chunk)

        return hasher.hexdigest()
