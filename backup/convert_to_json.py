import csv
import json

FILENAME = 'Item_20160416_121036'

DATA = {
	"items": [],
	"categories": []
}

def find_category(category_name):
	for category in DATA["categories"]:
		if category["name"] == category_name:
			return category

	return None

with open(FILENAME + ".csv", "r") as csvfile:
	reader = csv.reader(csvfile)
	row_number = 0
	for row in reader:
		if row_number != 0:
			item = {}
			item["name"] = row[0]
			item["note"] = row[1]
			category_name = row[2]
			category = find_category(category_name)
			if category is None:
				DATA["categories"].append(
					{
						"id": len(DATA["categories"])+1,
						"name": category_name
					}
					)

				category = find_category(category_name)

			item["category"] = category["id"]
			item["created_date"] = row[5]
			item["purchase_price"] = row[6]

			if int(row[7]) >= 0:
				item["currently_loaned"] = True

			if int(row[7]) <= 1:
				item["currently_loaned"] = False

			item["type"] = row[10]

			if row[12] == "":
				item["id"] = None
			else:
				item["id"] = int(row[12])

			images = row[19].split("\n")
			images_ary = []
			for image in images:
				images_ary.append(image.strip('*').strip(" "))
			item["images"] = images_ary
			

			DATA["items"].append(item)

			print(item)

		row_number += 1

def sort_items(item):
	if item["id"] is None:
		return 9999999
	else:
		return item["id"]

DATA["items"] = sorted(DATA["items"], key=sort_items)

json_file = open(FILENAME + ".json", "w")

json_file.write(json.dumps(DATA, indent=4))
json_file.close()

