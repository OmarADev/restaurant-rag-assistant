# create_menu_pdf.py
# Utility script to regenerate the sample restaurant menu PDF used for testing.
# Run this once if restaurant_menu.pdf is missing or you want to update menu items.
# Output: restaurant_menu.pdf in the current directory.

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

pdf_path = "restaurant_menu.pdf"
c = canvas.Canvas(pdf_path, pagesize=letter)
width, height = letter

# Title
c.setFont("Helvetica-Bold", 24)
c.drawString(100, height - 50, "Pizza Restaurant Menu")

# Pizzas
c.setFont("Helvetica-Bold", 14)
c.drawString(100, height - 100, "PIZZAS")

pizzas = [
    ("Margherita", "$12.99", "Fresh mozzarella, basil, tomato sauce, olive oil"),
    ("Pepperoni", "$13.99", "Classic pepperoni with mozzarella cheese"),
    ("Vegetarian", "$14.99", "Assorted fresh vegetables with mozzarella"),
    ("Seafood", "$18.99", "Mussels, shrimp, clams with garlic sauce"),
    ("BBQ Chicken", "$15.99", "Grilled chicken, BBQ sauce, onions"),
    ("Vegan Supreme", "$16.99", "Cashew cheese, seasonal vegetables"),
    ("Sicilian", "$17.99", "Traditional Sicilian style with thick crust"),
]

c.setFont("Helvetica", 11)
y = height - 130
for name, price, description in pizzas:
    c.setFont("Helvetica-Bold", 11)
    c.drawString(120, y, f"{name} - {price}")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(140, y, description)
    y -= 25

# Sides
c.setFont("Helvetica-Bold", 14)
c.drawString(100, y - 20, "SIDES & APPETIZERS")

sides = [
    ("Garlic Bread", "$4.99"),
    ("Chicken Wings", "$7.99"),
    ("Mozzarella Sticks", "$5.99"),
    ("Salad", "$6.99"),
]

c.setFont("Helvetica", 11)
y -= 50
for name, price in sides:
    c.drawString(120, y, f"{name} - {price}")
    y -= 20

# Beverages
c.setFont("Helvetica-Bold", 14)
c.drawString(100, y - 20, "BEVERAGES")

c.setFont("Helvetica", 11)
y -= 50
c.drawString(120, y, "Soft Drinks - $2.50")
y -= 20
c.drawString(120, y, "Beer Selection - $4.00 - $6.00")
y -= 20
c.drawString(120, y, "Wine Selection - $5.00 - $15.00")

c.save()
print(f"PDF created: {pdf_path}")
