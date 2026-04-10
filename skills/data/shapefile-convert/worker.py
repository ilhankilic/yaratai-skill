"""data.shapefile-convert — Convert Shapefile to GeoJSON / KML."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {"geojson", "kml"}


class Worker(BaseWorker):
    """Convert Shapefile to GeoJSON or KML with CRS reprojection."""

    skill_id = "data.shapefile-convert"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            import geopandas as gpd
        except ImportError:
            return SkillOutput(
                success=False,
                error="geopandas is not installed. Run: pip install 'skillforge[geo]'",
            )

        try:
            file_path: str = input.data.get("file_path", "")
            output_format: str = input.data.get("output_format", "geojson").lower()
            target_crs: str = input.data.get("target_crs", "EPSG:4326")

            if not file_path:
                return SkillOutput(success=False, error="'file_path' is required.")

            if output_format not in SUPPORTED_FORMATS:
                return SkillOutput(
                    success=False,
                    error=f"Unsupported format '{output_format}'. Use: {SUPPORTED_FORMATS}",
                )

            shp_path = Path(file_path)
            if not shp_path.exists():
                return SkillOutput(success=False, error=f"File not found: {file_path}")

            gdf = gpd.read_file(shp_path)

            # Reproject if needed
            if gdf.crs and str(gdf.crs) != target_crs:
                gdf = gdf.to_crs(target_crs)

            feature_count = len(gdf)

            if output_format == "geojson":
                content = gdf.to_json(ensure_ascii=False)
            elif output_format == "kml":
                # geopandas can write KML via fiona driver
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".kml", delete=False) as tmp:
                    tmp_path = tmp.name
                gdf.to_file(tmp_path, driver="KML")
                content = Path(tmp_path).read_text(encoding="utf-8")
                Path(tmp_path).unlink(missing_ok=True)
            else:
                content = ""

            return SkillOutput(
                success=True,
                data={
                    "content": content,
                    "feature_count": feature_count,
                    "crs": target_crs,
                },
                metadata={"skill_id": self.skill_id, "format": output_format},
            )

        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

