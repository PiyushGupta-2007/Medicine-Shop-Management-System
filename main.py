import csv
import os
from collections import deque, defaultdict
from datetime import datetime

# Use a non-GUI backend: works in browser/remote coding environments.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDICINE_FILE = os.path.join(BASE_DIR, "medicines.csv")
CUSTOMER_FILE = os.path.join(BASE_DIR, "customers.csv")
SALES_FILE = os.path.join(BASE_DIR, "sales.csv")

customers_queue = deque()


class Medicine:
    def __init__(self, medicine_id, name, price, stock, minimum):
        self.Id = medicine_id
        self.name = name
        self.price = float(price)
        self.stock = int(stock)
        self.minimum = int(minimum)


def ensure_csv_files():
    """Create CSV files with correct headers only if missing/empty."""
    file_headers = {
        MEDICINE_FILE: [
            "medicine_id", "name", "price", "stock", "minimum_stock"
        ],
        CUSTOMER_FILE: [
            "customer_id", "customer_name", "phone", "date_time"
        ],
        SALES_FILE: [
            "bill_id", "customer_id", "customer_name", "medicine_id",
            "medicine_name", "quantity", "price", "total", "date_time"
        ],
    }
    for filename, headers in file_headers.items():
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(headers)


def read_csv_rows(filename):
    """Read a CSV safely, preserving existing records."""
    ensure_csv_files()
    with open(filename, "r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_medicines():
    medicines = {}
    for row in read_csv_rows(MEDICINE_FILE):
        try:
            medicine_id = row.get("medicine_id", "").strip()
            if not medicine_id:
                continue
            medicines[medicine_id] = Medicine(
                medicine_id,
                row.get("name", ""),
                row.get("price", "0"),
                row.get("stock", "0"),
                row.get("minimum_stock", "0"),
            )
        except (ValueError, TypeError):
            print("Warning: Skipping invalid medicine row:", row)
    return medicines


def save_medicines(medicines):
    with open(MEDICINE_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "medicine_id", "name", "price", "stock", "minimum_stock"
        ])
        for medicine in medicines.values():
            writer.writerow([
                medicine.Id, medicine.name, f"{medicine.price:.2f}",
                medicine.stock, medicine.minimum
            ])


def show_medicines():
    print("\n" + "=" * 75)
    print("MEDICINE INVENTORY")
    print("=" * 75)
    rows = read_csv_rows(MEDICINE_FILE)
    if not rows:
        print("No medicines found in medicines.csv.")
        print("Add medicine rows to medicines.csv, then try again.")
        return

    print(f'{"ID":<12}{"Medicine":<25}{"Price (Rs.)":>14}{"Stock":>10}{"Minimum":>12}')
    print("-" * 75)
    for row in rows:
        print(
            f'{row.get("medicine_id", ""):<12}'
            f'{row.get("name", ""):<25}'
            f'{row.get("price", ""):>14}'
            f'{row.get("stock", ""):>10}'
            f'{row.get("minimum_stock", ""):>12}'
        )


def search_medicine():
    medicines = load_medicines()
    name = input("Enter medicine name: ").strip().lower()
    for medicine in medicines.values():
        if medicine.name.lower() == name:
            print(
                f'\nFound: {medicine.Id} | {medicine.name} | '
                f'Rs. {medicine.price:.2f} | Stock: {medicine.stock}'
            )
            return
    print("Medicine not found.")


def low_stock():
    medicines = load_medicines()
    print("\nLOW STOCK ALERT")
    found = False
    for medicine in medicines.values():
        if medicine.stock <= medicine.minimum:
            print(
                f"{medicine.Id} - {medicine.name}: "
                f"stock={medicine.stock}, minimum={medicine.minimum}"
            )
            found = True
    if not found:
        print("All medicines have sufficient stock.")


def sort_medicines():
    data = sorted(load_medicines().values(), key=lambda medicine: medicine.price)
    print("\nMEDICINES SORTED BY PRICE")
    for medicine in data:
        print(f"{medicine.Id} - {medicine.name} - Rs. {medicine.price:.2f}")


def next_customer_id():
    highest = 100
    for row in read_csv_rows(CUSTOMER_FILE):
        try:
            number = row.get("customer_id", "").replace("CUST-", "")
            highest = max(highest, int(number))
        except (ValueError, AttributeError):
            pass
    return highest + 1


def add_customer():
    name = input("Enter customer name: ").strip()
    if not name:
        print("Customer name cannot be empty.")
        return
    phone = input("Enter phone number: ").strip()
    customer_id = f"CUST-{next_customer_id()}"
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(CUSTOMER_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([customer_id, name, phone, date_time])

    customers_queue.append(customer_id)
    print("\nCustomer added successfully.")
    print("Customer ID:", customer_id)
    show_dashboard()


def view_queue():
    print("\nCUSTOMER QUEUE")
    if not customers_queue:
        print("Queue is empty (the queue resets when the program restarts).")
        return
    for customer_id in customers_queue:
        print(customer_id)


def find_customer(customer_id):
    for row in read_csv_rows(CUSTOMER_FILE):
        if row.get("customer_id", "").strip() == customer_id:
            return row
    return None


def next_bill_id():
    highest = 1000
    for row in read_csv_rows(SALES_FILE):
        try:
            number = row.get("bill_id", "").replace("BILL-", "")
            highest = max(highest, int(number))
        except (ValueError, AttributeError):
            pass
    return highest + 1


def generate_bill():
    medicines = load_medicines()
    if not medicines:
        print("No medicines found. Check medicines.csv first.")
        return

    customer_id = input("Enter Customer ID (e.g. CUST-101): ").strip()
    customer = find_customer(customer_id)
    if customer is None:
        print("Customer not found. Add the customer first.")
        return

    cart = []
    while True:
        medicine_id = input("Enter Medicine ID (or DONE to finish): ").strip().upper()
        if medicine_id == "DONE":
            break
        if medicine_id not in medicines:
            print("Medicine not found.")
            continue

        medicine = medicines[medicine_id]
        already_selected = sum(
            item["quantity"] for item in cart
            if item["medicine_id"] == medicine_id
        )
        remaining = medicine.stock - already_selected
        print(
            f"{medicine.name} | Price: Rs. {medicine.price:.2f} | "
            f"Available for this bill: {remaining}"
        )

        try:
            quantity = int(input("Enter quantity: "))
        except ValueError:
            print("Enter a valid whole number.")
            continue
        if quantity <= 0:
            print("Quantity must be greater than zero.")
            continue
        if quantity > remaining:
            print("Insufficient stock.")
            continue

        cart.append({
            "medicine_id": medicine.Id,
            "medicine_name": medicine.name,
            "quantity": quantity,
            "price": medicine.price,
            "total": medicine.price * quantity,
        })
        print("Added to bill.")
        if input("Add another medicine? (yes/no): ").strip().lower() != "yes":
            break

    if not cart:
        print("No items selected. Bill cancelled.")
        return

    bill_id = f"BILL-{next_bill_id()}"
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    grand_total = sum(item["total"] for item in cart)

    # Update inventory only after all cart validation is complete.
    for item in cart:
        medicines[item["medicine_id"]].stock -= item["quantity"]
    save_medicines(medicines)

    with open(SALES_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for item in cart:
            writer.writerow([
                bill_id, customer.get("customer_id", customer_id),
                customer.get("customer_name", ""),
                item["medicine_id"], item["medicine_name"], item["quantity"],
                f'{item["price"]:.2f}', f'{item["total"]:.2f}', date_time
            ])

    print("\n" + "=" * 58)
    print(" MEDICINE SHOP BILL")
    print("=" * 58)
    print("Bill ID :", bill_id)
    print("Customer ID :", customer.get("customer_id", customer_id))
    print("Customer Name :", customer.get("customer_name", ""))
    print("Phone :", customer.get("phone", ""))
    print("-" * 58)
    print(f'{"Medicine":<22}{"Qty":>5}{"Price":>13}{"Total":>13}')
    print("-" * 58)
    for item in cart:
        print(
            f'{item["medicine_name"]:<22}{item["quantity"]:>5}'
            f'{item["price"]:>13.2f}{item["total"]:>13.2f}'
        )
    print("-" * 58)
    print(f"Grand Total: Rs. {grand_total:.2f}")
    print("Date & Time:", date_time)
    print("=" * 58)
    print("Bill saved. Stock and sales CSV files updated.")
    show_dashboard()


def view_sales():
    rows = read_csv_rows(SALES_FILE)
    print("\nSALES HISTORY")
    if not rows:
        print("No sales recorded.")
        return
    for row in rows:
        print(
            f'\nBill: {row.get("bill_id", "")} | '
            f'Customer: {row.get("customer_name", "")} | '
            f'Medicine: {row.get("medicine_name", "")} | '
            f'Qty: {row.get("quantity", "")} | '
            f'Total: Rs. {row.get("total", "")} | '
            f'Date: {row.get("date_time", "")}'
        )


def show_dashboard():
    """Read current CSV contents and save a fresh dashboard PNG."""
    try:
        medicines = load_medicines()
        sales = read_csv_rows(SALES_FILE)
        customers = read_csv_rows(CUSTOMER_FILE)

        stock_names = [m.name for m in medicines.values()]
        stock_values = [m.stock for m in medicines.values()]
        minimum_values = [m.minimum for m in medicines.values()]

        revenue = defaultdict(float)
        quantity_sold = defaultdict(int)
        for row in sales:
            try:
                name = row["medicine_name"]
                revenue[name] += float(row["total"])
                quantity_sold[name] += int(row["quantity"])
            except (KeyError, ValueError, TypeError):
                continue

        customers_per_day = defaultdict(int)
        for row in customers:
            date_time = row.get("date_time", "")
            if len(date_time) >= 10:
                customers_per_day[date_time[:10]] += 1

        fig, axes = plt.subplots(2, 2, figsize=(13, 8))
        fig.suptitle("MEDICINE SHOP MANAGEMENT DASHBOARD",
                     fontsize=15, fontweight="bold")

        # 1. Stock chart
        if stock_names:
            positions = list(range(len(stock_names)))
            axes[0, 0].bar(positions, stock_values, label="Current stock")
            axes[0, 0].plot(positions, minimum_values, marker="o",
                            label="Minimum stock")
            axes[0, 0].set_xticks(positions)
            axes[0, 0].set_xticklabels(stock_names, rotation=30, ha="right")
            axes[0, 0].legend()
        else:
            axes[0, 0].text(0.5, 0.5, "No medicine data",
                            ha="center", va="center", transform=axes[0, 0].transAxes)
        axes[0, 0].set_title("Current Medicine Stock")
        axes[0, 0].set_ylabel("Units")

        # 2. Revenue chart
        revenue_names = list(revenue.keys())
        if revenue_names:
            axes[0, 1].bar(revenue_names, [revenue[n] for n in revenue_names])
            axes[0, 1].tick_params(axis="x", labelrotation=30)
        else:
            axes[0, 1].text(0.5, 0.5, "No sales data",
                            ha="center", va="center", transform=axes[0, 1].transAxes)
        axes[0, 1].set_title("Revenue by Medicine")
        axes[0, 1].set_ylabel("Revenue (Rs.)")

        # 3. Quantity sold chart
        quantity_names = list(quantity_sold.keys())
        if quantity_names:
            axes[1, 0].bar(quantity_names, [quantity_sold[n] for n in quantity_names])
            axes[1, 0].tick_params(axis="x", labelrotation=30)
        else:
            axes[1, 0].text(0.5, 0.5, "No sales data",
                            ha="center", va="center", transform=axes[1, 0].transAxes)
        axes[1, 0].set_title("Quantity Sold by Medicine")
        axes[1, 0].set_ylabel("Units sold")

        # 4. New customers per day
        dates = sorted(customers_per_day.keys())
        if dates:
            axes[1, 1].plot(dates, [customers_per_day[d] for d in dates],
                            marker="o")
            axes[1, 1].tick_params(axis="x", labelrotation=30)
        else:
            axes[1, 1].text(0.5, 0.5, "No customer data",
                            ha="center", va="center", transform=axes[1, 1].transAxes)
        axes[1, 1].set_title("Customers Added per Day")
        axes[1, 1].set_ylabel("New customers")

        low_stock_count = sum(
            1 for medicine in medicines.values()
            if medicine.stock <= medicine.minimum
        )
        total_revenue = sum(revenue.values())
        fig.text(
            0.5, 0.015,
            f"Customers: {len(customers)} | Revenue: Rs. {total_revenue:.2f} | "
            f"Low-stock medicines: {low_stock_count}",
            ha="center", fontsize=10
        )
        fig.tight_layout(rect=[0, 0.05, 1, 0.93])

        # Save in the same directory as this Python script.
        output_path = os.path.join(BASE_DIR, "medicine_dashboard.png")
        fig.savefig(output_path, dpi=160, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        if os.path.exists(output_path):
            print(f"\nDashboard image saved: {output_path}")
            print(f"Image size: {os.path.getsize(output_path)} bytes")
        else:
            print("Dashboard image was not created.")
    except Exception as error:
        print("Dashboard error:", error)


def main():
    ensure_csv_files()

    actions = {
        "1": show_medicines,
        "2": search_medicine,
        "3": low_stock,
        "4": sort_medicines,
        "5": add_customer,
        "6": view_queue,
        "7": generate_bill,
        "8": view_sales,
        "9": show_dashboard,
    }

    while True:
        print("\n" + "=" * 45)
        print(" WELCOME TO MY MEDICINE SHOP")
        print("=" * 45)
        print("1. Show Medicines")
        print("2. Search Medicine")
        print("3. Low Stock Alert")
        print("4. Sort by Price")
        print("5. Add Customer")
        print("6. View Customer Queue")
        print("7. Generate Bill")
        print("8. View Sales History")
        print("9. View Dashboard")
        print("10. Exit")

        try:
            choice = input("\nEnter choice (1-10): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nProgram stopped.")
            break

        if choice == "10":
            print("Thank you for using the Medicine Shop System!")
            break

        action = actions.get(choice)
        if action is None:
            print(f"Invalid choice {choice!r}. Please type a number from 1 to 10.")
            continue

        try:
            action()
        except Exception as error:
            print(f"\nOption {choice} failed: {type(error).__name__}: {error}")
            print("Check the CSV headers/data and try again.")

        input("\nPress Enter to return to the main menu...")


if __name__ == "__main__":
    main()