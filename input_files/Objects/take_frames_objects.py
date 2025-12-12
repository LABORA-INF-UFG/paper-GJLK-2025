import json

for image_ID in range(1, 1001):
    # THE LABELS FILE HAS THE RESOLUTION 640 X 360 (WIDTH X HEIGHT) WITH 230400 PIXELS
    segmentation_file = open("../Labels/{}.txt".format(image_ID), "r")
    objects_list = []
    objects_IDs = []
    for line in segmentation_file:
        for num in line.split():
            if num.isdigit() and int(num) not in objects_IDs:
                objects_IDs.append(int(num))
    segmentation_file.close()

    for object_ID in objects_IDs:
        segmentation_file = open("../Labels/{}.txt".format(image_ID), "r")
        num_occurrences = 0
        for line in segmentation_file:
            for num in line.split():
                if num.isdigit() and int(num) == object_ID:
                    num_occurrences += 1
        objects_list.append({"object_ID": object_ID, "length": num_occurrences})
        segmentation_file.close()
        
    json.dump({"objects": objects_list}, open("{}.json".format(image_ID), "w"), indent=4)
    print("{} images processed".format(image_ID))