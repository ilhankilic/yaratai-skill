# data.shapefile-convert

Convert Shapefile (.shp) to GeoJSON or KML with optional CRS reprojection.

## Usage

```bash
skillforge run data.shapefile-convert --input input.json
```

### Input

| Field         | Type   | Required | Description                           |
|---------------|--------|----------|---------------------------------------|
| file_path     | string | ✅       | Path to the `.shp` file               |
| output_format | string | ❌       | `geojson` (default) or `kml`          |
| target_crs    | string | ❌       | Target CRS (default `EPSG:4326`)      |

### Output

| Field         | Type    | Description                     |
|---------------|---------|----------------------------------|
| content       | string  | Converted file content           |
| feature_count | integer | Number of features               |
| crs           | string  | Output CRS                       |

## Dependencies

- `geopandas`, `fiona` — install via `pip install 'skillforge[geo]'`

