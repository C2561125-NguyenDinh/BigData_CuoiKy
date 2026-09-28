"""Bước 2 - Bảng chiều vùng (zone dimension) và xác định vùng xử lý.

Không gán tay danh sách vùng thu phí. Vùng được phân loại bằng dữ liệu:
với các chuyến có điểm đón và điểm trả cùng một vùng (chuyến nội vùng)
trong quý I/2025, nếu phần lớn chuyến bị thu cbd_congestion_fee thì vùng đó
nằm trong Congestion Relief Zone (CRZ). Cách làm này tránh sai sót khi
ranh giới đường 60 cắt ngang một số vùng taxi.

Ngoài ra, bước này đọc shapefile taxi_zones để tính diện tích, tâm vùng,
quan hệ kề nhau và khoảng cách tới ranh giới CRZ (phục vụ phân tích lan tỏa).

Chạy:  python code/02_zone_dimension.py
"""
import io
import json
import time
import zipfile

import numpy as np
import pandas as pd
import shapefile  # pyshp
from shapely.geometry import shape
from shapely.ops import unary_union

from config import (RAW, GOLD, TAB, LOG, AIRPORT_ZONES, CRZ_FULL_SHARE,
                    CRZ_PARTIAL_SHARE, raw_file, duck)

t0 = time.time()
con = duck()
lk = pd.read_csv(RAW / "taxi_zone_lookup.csv")

share = {}
for svc in ("hvfhv", "yellow"):
    files = ",".join(f"'{raw_file(svc, m).as_posix()}'" for m in ("2025-01", "2025-02", "2025-03"))
    ts = "pickup_datetime" if svc == "hvfhv" else "tpep_pickup_datetime"
    q = f"""SELECT PULocationID AS LocationID, count(*) AS n_intra,
                   avg(CASE WHEN coalesce(cbd_congestion_fee,0) > 0 THEN 1 ELSE 0 END) AS fee_share
            FROM read_parquet([{files}])
            WHERE PULocationID = DOLocationID AND {ts} >= TIMESTAMP '2025-01-05'
            GROUP BY 1"""
    share[svc] = con.execute(q).df().rename(columns={"n_intra": f"n_intra_{svc}",
                                                      "fee_share": f"fee_share_{svc}"})

z = lk.merge(share["hvfhv"], on="LocationID", how="left").merge(share["yellow"], on="LocationID", how="left")


def classify(r):
    if r.LocationID in (264, 265) or pd.isna(r.Borough) or r.Borough in ("Unknown", "N/A"):
        return "UNKNOWN"
    if r.LocationID in AIRPORT_ZONES:
        return "AIRPORT"
    s = r.fee_share_hvfhv if not pd.isna(r.fee_share_hvfhv) else 0.0
    if s >= CRZ_FULL_SHARE:
        return "CRZ"
    if s >= CRZ_PARTIAL_SHARE:
        return "CRZ_PARTIAL"
    if r.Borough == "Manhattan":
        return "MN_NORTH"
    return "OUTER"


z["grp"] = z.apply(classify, axis=1)

# --- Hình học vùng từ shapefile (hệ tọa độ NY State Plane, đơn vị feet) ---
zf = zipfile.ZipFile(RAW / "taxi_zones.zip")
names = zf.namelist()


def member(ext):
    return [n for n in names if n.lower().endswith(ext)][0]


rdr = shapefile.Reader(shp=io.BytesIO(zf.read(member(".shp"))),
                       shx=io.BytesIO(zf.read(member(".shx"))),
                       dbf=io.BytesIO(zf.read(member(".dbf"))))
fields = [f[0] for f in rdr.fields[1:]]
geoms = {}
for sr in rdr.shapeRecords():
    rec = dict(zip(fields, sr.record))
    lid = int(rec.get("LocationID") or rec.get("OBJECTID"))
    g = shape(sr.shape.__geo_interface__).buffer(0)
    geoms[lid] = unary_union([geoms[lid], g]) if lid in geoms else g
FT2KM = 0.0003048
crz_union = unary_union([geoms[i] for i in z.loc[z.grp == "CRZ", "LocationID"] if i in geoms])

geo = []
for lid, g in geoms.items():
    c = g.centroid
    geo.append(dict(LocationID=lid, area_km2=g.area * FT2KM ** 2, cx_ft=c.x, cy_ft=c.y,
                    dist_to_crz_km=g.distance(crz_union) * FT2KM,
                    centroid_dist_crz_km=c.distance(crz_union) * FT2KM))
geo = pd.DataFrame(geo)
z = z.merge(geo, on="LocationID", how="left")

# Quan hệ kề: hai vùng chạm nhau hoặc cách nhau < 200 feet (qua đường/phố)
ids = sorted(geoms)
adj = []
for i, a in enumerate(ids):
    ga = geoms[a]
    for b in ids[i + 1:]:
        if ga.distance(geoms[b]) < 200:
            adj.append((a, b))
adj_df = pd.DataFrame(adj, columns=["a", "b"])
adj_df = pd.concat([adj_df, adj_df.rename(columns={"a": "b", "b": "a"})], ignore_index=True)
adj_df.to_csv(GOLD / "zone_adjacency.csv", index=False)
z["n_neighbors"] = z.LocationID.map(adj_df.groupby("a").size()).fillna(0).astype(int)

# Vành đai theo số bước kề tính từ CRZ (0 = trong CRZ)
ring = {int(i): 0 for i in z.loc[z.grp == "CRZ", "LocationID"]}
frontier = set(ring)
nb = adj_df.groupby("a")["b"].apply(set).to_dict()
for k in range(1, 6):
    new = set()
    for u in frontier:
        for v in nb.get(u, ()):
            if v not in ring:
                ring[v] = k
                new.add(v)
    frontier = new
z["ring"] = z.LocationID.map(ring)
z["crz_flag"] = (z.grp == "CRZ").astype(int)
z.to_parquet(GOLD / "dim_zone.parquet", index=False)
z.to_csv(TAB / "t04_dim_zone.csv", index=False)

# Lưu hình học dạng tọa độ để vẽ bản đồ (không cần geopandas)
poly = []
for lid, g in geoms.items():
    parts = g.geoms if g.geom_type == "MultiPolygon" else [g]
    for k, p in enumerate(parts):
        xs, ys = p.exterior.coords.xy
        poly += [dict(LocationID=lid, part=k, order=j, x=x, y=y)
                 for j, (x, y) in enumerate(zip(xs[::2], ys[::2]))]
pd.DataFrame(poly).to_parquet(GOLD / "zone_polygons.parquet", index=False)

cnt = z.groupby(["grp", "Borough"]).size().reset_index(name="n_zones")
cnt.to_csv(TAB / "t05_zone_groups.csv", index=False)
(LOG / "02_zone_dimension.json").write_text(json.dumps(dict(
    seconds=round(time.time() - t0, 1), n_zones=len(z),
    groups=z.grp.value_counts().to_dict(), n_adjacent_pairs=len(adj)), indent=2))
print(z.grp.value_counts())
print(z[z.grp.isin(["CRZ_PARTIAL"])][["LocationID", "Zone", "fee_share_hvfhv", "fee_share_yellow"]])
print("time", round(time.time() - t0, 1))
