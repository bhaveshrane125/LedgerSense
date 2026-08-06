from __future__ import annotations

from decimal import Decimal
from random import Random

from .models import Item, LAYOUTS, Vendor
from .utils import money


COMPANY_PREFIXES = [
    "Aarav",
    "Nila",
    "Saffron",
    "Cobalt",
    "Prism",
    "Kaveri",
    "Zenith",
    "Helio",
]
COMPANY_TYPES = [
    "Industrial Supplies",
    "Precision Components",
    "Warehouse Services",
    "Electrical Traders",
    "Machine Tools",
]
CITIES = ["Pune", "Mumbai", "Bengaluru", "Chennai", "Hyderabad", "Ahmedabad"]
ITEMS = [
    ("BLT-M8-040-ZN", "M8x40 Hex Bolt Zinc", "FASTENERS", "EA", "10.00"),
    ("NUT-M8-ZN", "M8 Zinc Hex Nut", "FASTENERS", "EA", "4.50"),
    ("BRG-6205-2RS", "Sealed Ball Bearing 6205", "BEARINGS", "EA", "185.00"),
    ("GLV-NIT-L", "Nitrile Safety Gloves Large", "SAFETY", "PAIR", "42.00"),
    ("OIL-HYD-46", "Hydraulic Oil ISO VG 46", "LUBRICANTS", "LTR", "118.00"),
    ("CBL-CU-2C", "Copper Control Cable 2 Core", "ELECTRICAL", "MTR", "72.00"),
    ("FLT-AIR-010", "Compressed Air Filter Element", "FILTERS", "EA", "650.00"),
    ("PKG-STRAP-16", "Polyester Packing Strap 16mm", "PACKING", "ROLL", "920.00"),
]


def generate_vendors(rng: Random, count: int) -> list[Vendor]:
    vendors: list[Vendor] = []
    for index in range(1, count + 1):
        prefix = rng.choice(COMPANY_PREFIXES)
        company_type = rng.choice(COMPANY_TYPES)
        city = rng.choice(CITIES)
        name = f"{prefix} {company_type} Pvt Ltd"
        vendors.append(
            Vendor(
                vendor_id=f"VEN-{index:03d}",
                legal_name=name,
                trading_name=f"{prefix} {company_type}",
                tax_id=f"99SYNTH{index:04d}Z{rng.randint(1, 9)}",
                address=f"{rng.randint(10, 999)} Test Estate, {city}, Fictional India",
                email=f"ap.{prefix.lower()}.{index}@example.test",
                payment_terms=rng.choice(["NET 15", "NET 30", "NET 45"]),
                bank_fingerprint=f"FAKE-BANK-{rng.randrange(10**7, 10**8)}",
                preferred_layout=rng.choice(LAYOUTS),
            )
        )
    return vendors


def generate_items(rng: Random, count: int) -> list[Item]:
    items: list[Item] = []
    for index in range(1, count + 1):
        sku, description, category, uom, base_price = ITEMS[(index - 1) % len(ITEMS)]
        price_factor = Decimal(str(rng.choice(["0.90", "1.00", "1.05", "1.10", "1.20"])))
        item_sku = f"{sku}-{index:03d}" if index > len(ITEMS) else sku
        items.append(
            Item(
                item_id=f"ITEM-{index:03d}",
                sku=item_sku,
                description=description,
                category=category,
                base_uom=uom,
                unit_price=money(Decimal(base_price) * price_factor),
                tax_rate=Decimal("0.18"),
                aliases=[description.upper(), description.replace("x", " X ")],
                uom_conversions={"BOX": Decimal("12")} if uom == "EA" else {},
            )
        )
    return items


def uom_conversion_table(items: list[Item]) -> dict[str, dict[str, str]]:
    return {
        item.item_id: {uom: str(quantity) for uom, quantity in item.uom_conversions.items()}
        for item in items
        if item.uom_conversions
    }
