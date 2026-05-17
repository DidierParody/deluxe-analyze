from pyspark.sql import DataFrame

# Composite PKs for relationship entities; node entities default to "id".
_PK_BY_ENTITY: dict[str, str | list[str]] = {
    "segmentos": "name",
    "asistio_a": ["user_id", "event_id"],
    "reservo": ["user_id", "table_id"],
    "pertenece_a": ["user_id", "segment_name"],
}
_DEFAULT_PK: str = "id"


def merge_canonical(
    a: dict[str, DataFrame],
    b: dict[str, DataFrame],
) -> dict[str, DataFrame]:
    all_keys = set(a) | set(b)
    result: dict[str, DataFrame] = {}

    for key in all_keys:
        pk = _PK_BY_ENTITY.get(key, _DEFAULT_PK)
        pk_cols = pk if isinstance(pk, list) else [pk]
        if key in a and key in b:
            merged = a[key].unionByName(b[key], allowMissingColumns=True).dropDuplicates(pk_cols)
        elif key in a:
            merged = a[key]
        else:
            merged = b[key]
        result[key] = merged

    return result
