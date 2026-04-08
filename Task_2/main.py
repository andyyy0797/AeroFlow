import json
import math
import os
import sys
from pathlib import Path
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class TrieNode:
    def __init__(self):
        self.children = {}
        self.isEnd = False
        self.records = []


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, text, record):
        node = self.root
        for char in text:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.isEnd = True
        node.records.append(record)

    def findByPrefix(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        return self.collectAllRecords(node)

    def collectAllRecords(self, node):
        result = list(node.records)
        for child in node.children.values():
            result.extend(self.collectAllRecords(child))
        return result


def getNestedValue(record, keyPath):
    value = record
    for key in keyPath.split("."):
        if isinstance(value, dict) is False or key not in value:
            return None
        value = value[key]
    return value


def jsonToTrie(jsonData, keyPath):
    trie = Trie()
    for record in jsonData:
        value = getNestedValue(record, keyPath)
        if isinstance(value, str) and value.strip():
            trie.insert(value.strip().lower(), record)
    return trie


def loadJsonData():
    filePath = Path(__file__).parent / "mockBookings.json"
    with open(filePath, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def countSort(data, key):
    if not data:
        return []

    values = [item[key] for item in data]
    maxVal = max(values)
    minVal = min(values)
    rangeVal = maxVal - minVal + 1
    count = [0] * rangeVal
    output = [None] * len(data)

    for item in data:
        count[item[key] - minVal] += 1

    for i in range(1, len(count)):
        count[i] += count[i - 1]

    for i in range(len(data) - 1, -1, -1):
        val = data[i][key]
        output[count[val - minVal] - 1] = data[i]
        count[val - minVal] -= 1

    return output


def printSorted(data, key):
    print(f"-- Sorted by '{key}' --")
    sortedData = countSort(data, key)
    for item in sortedData:
        print(item)


def prepareSortKey(data):
    if not data:
        return "id"

    firstRecord = data[0]
    if "id" in firstRecord and isinstance(firstRecord["id"], int):
        return "id"
    if "totalPrice" in firstRecord and isinstance(firstRecord["totalPrice"], int):
        return "totalPrice"

    for index, item in enumerate(data):
        item["id"] = index
    return "id"


def toPriceSortableRecords(records):
    sortable = []
    for item in records:
        priceValue = int(item.get("totalPrice", 0))
        sortable.append(
            {
                "booking_id": item.get("booking_id", ""),
                "user_email": item.get("user_email", ""),
                "totalPrice": priceValue,
            }
        )
    return sortable


def createDemoResultPanel(prefix, matchedCount, cheapestRecord, highestRecord):
    if cheapestRecord is None:
        cheapestText = "N/A"
    else:
        cheapestText = (
            f"{cheapestRecord['booking_id']} | "
            f"{cheapestRecord['user_email']} | "
            f"${cheapestRecord['totalPrice']}"
        )

    if highestRecord is None:
        highestText = "N/A"
    else:
        highestText = (
            f"{highestRecord['booking_id']} | "
            f"{highestRecord['user_email']} | "
            f"${highestRecord['totalPrice']}"
        )

    detailText = (
        f"[bold]Prefix:[/bold] '{prefix}'\n"
        f"[bold]Matched records:[/bold] {matchedCount}\n"
        f"[bold]Cheapest:[/bold] {cheapestText}\n"
        f"[bold]Highest:[/bold] {highestText}"
    )
    panelColor = "magenta" if matchedCount > 0 else "yellow"
    return Panel(detailText, border_style=panelColor, expand=True)


def createDemoTop3Table(sortedByPrice):
    table = Table(border_style="green", expand=True)
    table.add_column("Rank", justify="right", style="bold", width=4)
    table.add_column("Booking ID", style="cyan", no_wrap=True, min_width=12)
    table.add_column("Email", style="green", min_width=24)
    table.add_column("Total Price", justify="right", style="green", width=12)

    rows = sortedByPrice[:3]
    for index, item in enumerate(rows, start=1):
        table.add_row(
            str(index),
            str(item.get("booking_id", "")),
            str(item.get("user_email", "")),
            f"${int(item.get('totalPrice', 0))}",
        )

    for index in range(len(rows) + 1, 4):
        table.add_row(str(index), "-", "-", "-")

    return table


def createDemoTwoColumnTable():
    table = Table(expand=True, show_header=True, header_style="bold blue")
    table.add_column("Prefix Result", ratio=1)
    table.add_column("Top 3 Cheapest", ratio=1)
    return table


def runTrieCountSortDemo(jsonData):
    console = Console()
    emailTrie = jsonToTrie(jsonData, "user_email")
    if not jsonData:
        console.print(Panel("No records in mockBookings.json", border_style="yellow"))
        return

    firstEmail = str(jsonData[0].get("user_email", "")).lower()
    defaultPrefix = firstEmail.split("@")[0][:2] if firstEmail else "an"
    prefixes = [defaultPrefix, "ma", "zz"]
    summaryText = (
        f"[bold]Total records loaded:[/bold] {len(jsonData)}\n"
        f"[bold]Trie index key:[/bold] user_email\n"
        f"[bold]Demo prefixes:[/bold] {', '.join(prefixes)}"
    )
    console.print(Panel(summaryText, title="Trie + Count Sort Demo", border_style="blue"))

    demoTable = createDemoTwoColumnTable()
    for prefix in prefixes:
        matched = emailTrie.findByPrefix(prefix.lower())
        sortedByPrice = []
        cheapest = None
        expensive = None
        if matched:
            sortable = toPriceSortableRecords(matched)
            sortedByPrice = countSort(sortable, "totalPrice")
            cheapest = sortedByPrice[0]
            expensive = sortedByPrice[-1]

        detailPanel = createDemoResultPanel(prefix, len(matched), cheapest, expensive)
        top3Table = createDemoTop3Table(sortedByPrice)
        demoTable.add_row(detailPanel, top3Table)
    console.print(demoTable)


def clearConsole():
    os.system("cls" if os.name == "nt" else "clear")


def printLogo():
    logo = """
 █████╗ ███████╗██████╗  ██████╗ ███████╗██╗      ██████╗ ██╗    ██╗
██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔════╝██║     ██╔═══██╗██║    ██║
███████║█████╗  ██████╔╝██║   ██║█████╗  ██║     ██║   ██║██║ █╗ ██║
██╔══██║██╔══╝  ██╔══██╗██║   ██║██╔══╝  ██║     ██║   ██║██║███╗██║
██║  ██║███████╗██║  ██║╚██████╔╝██║     ███████╗╚██████╔╝╚███╔███╔╝
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝

==================== Efficient Analysis Toolbox ====================
"""
    print(logo)


def startupLoad():
    filePath = Path(__file__).parent / "mockBookings.json"
    print("1. Finding mockBookings.json")
    if filePath.exists() is False:
        raise FileNotFoundError("mockBookings.json not found.")
    print("2. mockBookings.json found.")
    print("3. Reading mockBookings.json")
    jsonData = loadJsonData()
    print(f"4. {len(jsonData)} mock bookings read.")
    print("5. Creating trie.")
    emailTrie = jsonToTrie(jsonData, "user_email")
    clearConsole()
    printLogo()
    return jsonData, emailTrie


def printMenu():
    print("1. Search Booking by Email\t\t[Trie]")
    print("2. Run Demo\t\t\t\t[Trie]\t[Count Sort]")
    print("3. Sort All Orders by Total Price\t[Count Sort]")
    print("4. Exit")
    print("")


def readNavigationKey():
    if os.name == "nt":
        import msvcrt
        first = msvcrt.getch()
        if first in (b"\x00", b"\xe0"):
            second = msvcrt.getch()
            if second == b"K":
                return "left"
            if second == b"M":
                return "right"
            return "unknown"
        if first in (b"q", b"Q", b"\r"):
            return "exit"
        return "unknown"

    import termios
    import tty
    fileDescriptor = sys.stdin.fileno()
    oldSettings = termios.tcgetattr(fileDescriptor)
    try:
        tty.setraw(fileDescriptor)
        first = sys.stdin.read(1)
        if first == "\x1b":
            second = sys.stdin.read(1)
            third = sys.stdin.read(1)
            if second == "[" and third == "D":
                return "left"
            if second == "[" and third == "C":
                return "right"
            return "unknown"
        if first in ("q", "Q", "\r"):
            return "exit"
        return "unknown"
    finally:
        termios.tcsetattr(fileDescriptor, termios.TCSADRAIN, oldSettings)


def createBookingTablePage(records, pageNumber, pageSize, prefix):
    startIndex = pageNumber * pageSize
    endIndex = min(startIndex + pageSize, len(records))
    table = Table(title=f"Search Booking by Email Prefix: '{prefix}'")
    table.add_column("Booking ID", style="cyan", no_wrap=True)
    table.add_column("Email", style="green")
    table.add_column("Destination")
    table.add_column("Departure")
    table.add_column("Class")
    table.add_column("Total Price", justify="right")
    table.add_column("Sub Pax", justify="right")
    for item in records[startIndex:endIndex]:
        destination = str(item.get("flight_info", {}).get("destination", ""))
        departureTime = str(item.get("flight_info", {}).get("departure_time", ""))
        travelClass = str(item.get("travelClass", ""))
        subPassengerCount = len(item.get("sub_passengers", []))
        table.add_row(
            str(item.get("booking_id", "")),
            str(item.get("user_email", "")),
            destination,
            departureTime,
            travelClass,
            f"${int(item.get('totalPrice', 0))}",
            str(subPassengerCount),
        )
    return table


def runPrefixSearch(emailTrie):
    console = Console()
    prefix = input("Enter email prefix: ").strip().lower()
    matched = emailTrie.findByPrefix(prefix)
    if not matched:
        print("Matched records: 0")
        return

    pageSize = 10
    totalPages = math.ceil(len(matched) / pageSize)
    currentPage = 0

    while True:
        clearConsole()
        printLogo()
        table = createBookingTablePage(matched, currentPage, pageSize, prefix)
        console.print(table)
        print(f"Page {currentPage + 1}/{totalPages} | Total matched: {len(matched)}")
        print("Use LEFT/RIGHT arrow to change page, Q or Enter to return menu.")
        key = readNavigationKey()
        if key == "right" and currentPage < totalPages - 1:
            currentPage += 1
        elif key == "left" and currentPage > 0:
            currentPage -= 1
        elif key == "exit":
            break


def createPriceRankingTable(records, title, color):
    table = Table(title=title, border_style=color)
    table.add_column("Rank", justify="right", style="bold")
    table.add_column("Booking ID", style="cyan", no_wrap=True)
    table.add_column("Email", style="green")
    table.add_column("Total Price", justify="right", style=color)
    for index, item in enumerate(records, start=1):
        table.add_row(
            str(index),
            str(item.get("booking_id", "")),
            str(item.get("user_email", "")),
            f"${int(item.get('totalPrice', 0))}",
        )
    return table


def runCountSortAll(jsonData):
    console = Console()
    sortable = toPriceSortableRecords(jsonData)
    if not sortable:
        console.print(Panel("No booking records to sort.", border_style="yellow"))
        return

    sortedByPrice = countSort(sortable, "totalPrice")
    cheapestRecords = sortedByPrice[:10]
    highestRecords = list(reversed(sortedByPrice[-10:]))
    minPrice = sortedByPrice[0]["totalPrice"]
    maxPrice = sortedByPrice[-1]["totalPrice"]
    avgPrice = sum(item["totalPrice"] for item in sortedByPrice) / len(sortedByPrice)
    summaryText = (
        f"[bold]Total Sorted:[/bold] {len(sortedByPrice)}\n"
        f"[bold]Lowest Price:[/bold] ${minPrice}\n"
        f"[bold]Highest Price:[/bold] ${maxPrice}\n"
        f"[bold]Average Price:[/bold] ${avgPrice:.2f}"
    )
    summaryPanel = Panel(summaryText, title="Sort All Orders by Total Price", border_style="blue")
    cheapestTable = createPriceRankingTable(cheapestRecords, "Top 10 Cheapest", "green")
    highestTable = createPriceRankingTable(highestRecords, "Top 10 Highest", "red")
    console.print(summaryPanel)
    console.print(Columns([cheapestTable, highestTable], expand=True))


def main():
    jsonData, emailTrie = startupLoad()
    while True:
        printMenu()
        choice = input("Select option: ").strip()
        if choice == "1":
            clearConsole()
            runPrefixSearch(emailTrie)
        elif choice == "2":
            clearConsole()
            runTrieCountSortDemo(jsonData)
        elif choice == "3":
            clearConsole()
            runCountSortAll(jsonData)
        elif choice == "4":
            print("Exiting program.")
            break
        else:
            print("Invalid option. Please try again.")
        input("Press Enter to continue...")
        clearConsole()
        printLogo()


if __name__ == "__main__":
    main()
