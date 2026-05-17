from pyspark.sql import DataFrame


_PK_BY_ENTITY = {
    "segmentos": "name",
}
_DEFAULT_PK = "id"


def merge_canonical(
    a: dict[str, DataFrame],
    b: dict[str, DataFrame],
) -> dict[str, DataFrame]:
    all_keys = set(a) | set(b)
    result: dict[str, DataFrame] = {}

    for key in all_keys:
        pk = _PK_BY_ENTITY.get(key, _DEFAULT_PK)
        if key in a and key in b:
            merged = a[key].unionByName(b[key], allowMissingColumns=True).dropDuplicates([pk])
        elif key in a:
            merged = a[key]
        else:
            merged = b[key]
        result[key] = merged

    return result
