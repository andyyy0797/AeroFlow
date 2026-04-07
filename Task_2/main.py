json_data = [
  {"name": "Alice", "score": 85, "id": 3},
  {"name": "Bob", "score": 92, "id": 1},
  {"name": "Charlie", "score": 78, "id": 4},
  {"name": "David", "score": 92, "id": 2},
  {"name": "Eve", "score": 85, "id": 0}
]

def count_sort(data, key):
    if not data:
      return []
    values = [item[key] for item in data]
    max_val = max(values)
    min_val = min(values)
    range_val = max_val - min_val + 1
    count = [0] * range_val
    output = [None] * len(data)

    for item in data:
      count[item[key] - min_val] += 1

    for i in range(1, len(count)):
      count[i] += count[i-1]

    for i in range(len(data) - 1, -1, -1):
      val = data[i][key]
      output[count[val - min_val] - 1] = data[i]
      count[val - min_val] -= 1
        
    return output

def print_sorted(data, key):
  print("-- Sorted by '' --")
  sorted = count_sort(data, key)
  for item in sorted:
    print(item)

print_sorted(json_data, "id")
