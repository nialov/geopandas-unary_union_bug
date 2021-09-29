"""
pytest script for reproducing unary_union bug.
"""
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import LineString, MultiLineString
from shapely.affinity import translate
import pandas as pd

TRACE_DATA_PATH = Path("data/unary_error_data/err_traces.shp")

TRACE_DATA = gpd.read_file(TRACE_DATA_PATH)
assert isinstance(TRACE_DATA, gpd.GeoDataFrame)


def duplicate_and_transform_gdf(gdf: gpd.GeoDataFrame):
    """
    Duplicate and transform geometries of GeoDataFrame.
    """
    min_x, _, max_x, _ = gdf.total_bounds
    new_geoms = gdf.geometry.apply(lambda geom: translate(geom, xoff=max_x - min_x))
    copied = gdf.copy()
    new_gdf = copied.set_geometry(new_geoms)
    assert isinstance(new_gdf, gpd.GeoDataFrame)
    return new_gdf


def gdf_duplication(gdf: gpd.GeoDataFrame, how_many: int):
    gdfs = []
    gdfs.append(gdf)
    for _ in range(how_many):
        gdf = duplicate_and_transform_gdf(gdf)
        gdfs.append(gdf)
    return gdfs


@pytest.mark.parametrize(
    "trace_gdf",
    [
        pytest.param(TRACE_DATA, id="All data"),
        pytest.param(
            pd.concat(gdf_duplication(TRACE_DATA, 10), ignore_index=True), id="10x data"
        ),
    ],
)
def test_bug(trace_gdf: gpd.GeoDataFrame):
    """
    Reproduce bug with unary_union.
    """
    assert trace_gdf.crs is not None
    assert all(~trace_gdf.geometry.is_empty)
    assert all(trace_gdf.geometry.is_valid)
    assert all(isinstance(geom, LineString) for geom in trace_gdf.geometry.values)
    trace_count_original = trace_gdf.shape[0]
    unary_result = trace_gdf.unary_union
    assert isinstance(unary_result, MultiLineString)
    after_unary_length = len(list(unary_result.geoms))

    # print(f"Before: {trace_count_original}. After: {after_unary_length}.")
    assert trace_count_original < after_unary_length

    unary_result_srs = gpd.GeoSeries(list(unary_result.geoms), crs=trace_gdf.crs)

    unary_result_path = Path(
        f"results/unary_result_b{trace_count_original}_a{after_unary_length}.gpkg",
    )
    unary_result_path.parent.mkdir(parents=True, exist_ok=True)
    unary_result_srs.to_file(
        unary_result_path,
        driver="GPKG",
    )
