
from collections import OrderedDict
import csv
import datetime
import sys

from peewee import *

db = SqliteDatabase('inventory.db')

class Product(Model):
    product_id = AutoField(primary_key=True)
    product_name = TextField(unique=True)
    product_quantity = IntegerField(default=0)
    product_price = IntegerField(default=0)
    date_updated = DateField(default=datetime.datetime.now)

    class Meta:
        database = db

def initialize():
    """Create the database and the table if they don't exist"""
    db.connect()
    db.create_tables([Product], safe=True)
    read_inventory()

def read_inventory():
    """Read inventory and return a list of OrderedDicts"""
    with open('inventory.csv',newline='') as csvfile:
        food_reader = csv.DictReader(csvfile,delimiter=',')
        rows = list(food_reader)
        for row in rows:
            row['product_name'] = row['product_name']
            row['product_price'] = (row['product_price']
                                    .strip('$').replace('.', ''))
            row['product_price'] = int(row['product_price'])
            row['product_quantity'] = int(row['product_quantity'])
            row['date_updated'] = datetime.datetime.strptime(
                row['date_updated'], "%m/%d/%Y").date()

            try:
                Product.create(product_name=row['product_name'],
                                product_price=row['product_price'],
                                product_quantity=row['product_quantity'],
                                date_updated=row['date_updated'],)

            except IntegrityError:
                product_record = Product.get(product_name=row['product_name'])
                if product_record.date_updated < row['date_updated']:
                    product_record.product_price = (row['product_price'])
                    product_record.product_quantity = row['product_quantity']
                    product_record.date_updated = row['date_updated']
                    product_record.save()


def menu_loop():
    """Show the menu"""

    choice = None
    while choice != 'q':
        print("Enter 'q' to quit.")
        for key, value in menu.items():
            print('{}) {}'.format(key, value.__doc__))
        choice = input('Action: ').lower().strip()
        if choice in menu:
            menu[choice]()

def add_product():
    """Add a product"""
    while True:
        try:
            name = input("Enter a product name: ")
            price = input("Enter the product price in the format of $1.50: ").strip('$').replace('.', '')
            if len(price) < 3:
                price = price + '00'
            price = int(price)
            quantity = int(input("Enter the product quantity: "))
            date_added = datetime.datetime.now().date()
        except ValueError:
            print("Please enter in the format shown in the example.")
        else:
            if name and price and quantity:
                confirm = input("Save product? [Y/n]: ").lower().strip()
                if confirm == 'y':
                    try:
                        Product.create(product_name=name,
                                        product_price=price,
                                        product_quantity=quantity,
                                        date_updated=date_added)
                    except IntegrityError:
                        existing_product = Product.select().where(Product.product_name == name)
                        existing_date = existing_product.get().date_updated
                        if existing_date <= date_added:
                            Product.update(product_name=name,
                                        product_price=price,
                                        product_quantity=quantity,
                                        date_updated=date_added).where(
                                Product.product_name == name).execute()
                            print("Existing price has been updated")
                        else:
                            break
            break

def delete_product(product):
    """Delete a product"""
    if input("Are you sure you want to delete this product? [Y/N] ").lower() == 'y':
        product.delete_instance()
        print("The product has been deleted.")

def view_product():
    """View previous entries"""
    while True:
        try:
            inv = Product.select()
            len_inv = inv.count()
            search_id = input(f"Enter Product id between 1 & {len_inv}: ")
            if search_id == 'q':
                break
            search_id = int(search_id)
            product = Product.get(Product.product_id == search_id)
            if search_id not in Product.product_id:
                raise DoesNotExist
        except DoesNotExist:
            print('This product is not in the inventory list, Try a different product id')
        except ValueError:
            print("There is no product matching that id, please try again and use digits only")
        else:
            print(f'Product id: {product.product_id}')
            print(f'Product: {product.product_name}')
            print(f'Price: ${"{:.2f}".format(product.product_price / 100)}')
            print(f'Quantity: {product.product_quantity}')
            print(f'Date updated: {product.date_updated}')
            print('\n\nPress Enter to pick another product')
            print('d) Delete product')
            print('q) Return to main menu')

            next_action = input('Action: Enter [d/q] ').lower().strip()
            if next_action == 'q':
                break
            elif next_action == 'd':
                delete_product(product)


def backup_product():
    """Make backup of the contents"""
    with open('backup.csv', 'a') as csvfile:
        fieldnames = ['product_id', 'product_name', 'product_price', 'product_quantity', 'date_updated']
        productwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)

        productwriter.writeheader()
        food_list = Product.select().order_by(Product.product_id.asc())
        for food in food_list:
            productwriter.writerow({
                'product_id': food.product_id,
                'product_name': food.product_name,
                'product_price': food.product_price,
                'product_quantity': food.product_quantity,
                'date_updated': food.date_updated,
            })
        print("Success! backup.csv was created.")

menu = OrderedDict([
    ('a', add_product),
    ('b', backup_product),
    ('v', view_product),
    ])

if __name__ == '__main__':
    initialize()
    menu_loop()
