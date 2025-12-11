import csv
import json

def convert_csv_to_json(csv_file, json_file):
    result = []

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # авто-поиск колонки ID
        columns = reader.fieldnames
        id_col = None

        for col in columns:
            if "id" in col.lower():
                id_col = col
                break

        if id_col is None:
            raise ValueError(f"Не нашёл колонку ID в файле: {columns}")

        for row in reader:
            item = {
                "ID": row.get(id_col),
                "NAME": row.get("name"),
                "BRAND": row.get("brand"),
                "PRICE": row.get("price"),
                "SUBCATEGORY": row.get("subcategory"),
            }
            result.append(item)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


# пример
convert_csv_to_json("input.csv", "output.json")
