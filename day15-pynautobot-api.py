#!/usr/bin/env python3

import os
import sys
import pynautobot


def get_or_create_location_type(nb, location_type_name):
    """
    Retrieve a LocationType by name; if it doesn't exist, create one.
    """
    location_type = nb.dcim.location_types.get(name=location_type_name)
    if location_type:
        print(f"[INFO] Found existing location type: {location_type.name}")
        return location_type

    print(f"[INFO] Creating location type '{location_type_name}'...")
    try:
        location_type = nb.dcim.location_types.create(
            {
                "name": location_type_name,
                "description": f"Created by script for {location_type_name}",
                "content_types": ["dcim.device"],
            }
        )
    except pynautobot.core.query.RequestError as e:
        print(f"[ERROR] Failed to create location type '{location_type_name}': {e}")
        sys.exit(1)

    return location_type


def get_or_create_location(nb, location_name, location_type):
    """
    Retrieve a Location by name; if it doesn't exist, create one using the provided LocationType object.
    """
    location = nb.dcim.locations.get(name=location_name)
    if location:
        print(f"[INFO] Found existing location: {location.name}")
        return location

    print(f"[INFO] Creating location '{location_name}' with type '{location_type.name}'...")
    try:
        location = nb.dcim.locations.create(
            {
                "name": location_name,
                "location_type": location_type.id,
                "status": "Active",
            }
        )
    except pynautobot.core.query.RequestError as e:
        print(f"[ERROR] Failed to create location '{location_name}': {e}")
        sys.exit(1)

    return location


def get_or_create_manufacturer(nb, manufacturer_name):
    """
    Retrieve a Manufacturer by name; if it doesn't exist, create a new one.
    """
    manufacturer = nb.dcim.manufacturers.get(name=manufacturer_name)
    if manufacturer:
        print(f"[INFO] Found existing manufacturer: {manufacturer.name}")
        return manufacturer

    print(f"[INFO] Creating manufacturer '{manufacturer_name}'...")
    try:
        manufacturer = nb.dcim.manufacturers.create(
            {
                "name": manufacturer_name,
            }
        )
    except pynautobot.core.query.RequestError as e:
        print(f"[ERROR] Failed to create manufacturer '{manufacturer_name}': {e}")
        sys.exit(1)

    return manufacturer


def get_or_create_device_type(nb, device_type_model, manufacturer):
    """
    Retrieve a Device Type by model + manufacturer; if not found, create it.
    """
    try:
        device_type = nb.dcim.device_types.get(
            model=device_type_model,
            manufacturer=manufacturer.id
        )
    except pynautobot.core.query.RequestError:
        device_type = None

    if device_type:
        print(f"[INFO] Found existing device type: {device_type.model}")
        return device_type

    print(f"[INFO] Creating device type '{device_type_model}' for manufacturer '{manufacturer.name}'...")
    try:
        device_type = nb.dcim.device_types.create(
            {
                "model": device_type_model,
                "manufacturer": manufacturer.id,
            }
        )
    except pynautobot.core.query.RequestError as e:
        print(f"[ERROR] Failed to create device type '{device_type_model}': {e}")
        sys.exit(1)

    return device_type


def get_or_create_role(nb, role_name):
    """
    Retrieve a generic Role by name; if not found, create it for the `dcim.device` content type.
    """
    role = nb.extras.roles.get(name=role_name)
    if role:
        print(f"[INFO] Found existing role: {role.name}")
        return role

    print(f"[INFO] Creating role '{role_name}' for devices...")
    try:
        role = nb.extras.roles.create(
            {
                "name": role_name,
                "description": f"Device role for {role_name}",
                "content_types": ["dcim.device"],
            }
        )
    except pynautobot.core.query.RequestError as e:
        print(f"[ERROR] Failed to create role '{role_name}': {e}")
        sys.exit(1)

    return role


def create_device(nb, device_name, location, device_type, role):
    """
    Create a new device in Nautobot 2.x.
    """
    # Check if a device with this name already exists at the same location
    existing_device = nb.dcim.devices.get(name=device_name, location=location.id)
    if existing_device:
        print(f"[WARNING] Device '{device_name}' already exists at location '{location.name}'.")
        return existing_device

    print(f"[INFO] Creating new device '{device_name}'...")
    try:
        new_device = nb.dcim.devices.create(
            {
                "name": device_name,
                "device_type": device_type.id,
                "role": role.id,
                "location": location.id,
                "status": "Active",
            }
        )
    except pynautobot.core.query.RequestError as e:
        print(f"[ERROR] Failed to create device '{device_name}': {e}")
        sys.exit(1)

    return new_device


def main():
    nautobot_url = os.environ.get("NAUTOBOT_API_URL")
    nautobot_token = os.environ.get("NAUTOBOT_API_TOKEN")

    if not nautobot_url or not nautobot_token:
        print("[ERROR] Missing NAUTOBOT_API_URL or NAUTOBOT_API_TOKEN environment variable.")
        sys.exit(1)

    # Initialize pynautobot
    nb = pynautobot.api(url=nautobot_url, token=nautobot_token)

    # Example data for creation (adjust as needed)
    location_type_name = "Campus"           
    location_name = "MyCampusLocation"      
    manufacturer_name = "Cisco"
    device_type_model = "C9300-48P"
    role_name = "Access Switch"
    device_name = "myswitch001"

    # 1. Create or fetch the location type
    loc_type = get_or_create_location_type(nb, location_type_name)

    # 2. Create or fetch the location
    location = get_or_create_location(nb, location_name, loc_type)

    # 3. Create or fetch the manufacturer
    manufacturer = get_or_create_manufacturer(nb, manufacturer_name)

    # 4. Create or fetch the device type (notice we pass manufacturer=manufacturer.id)
    device_type = get_or_create_device_type(nb, device_type_model, manufacturer)

    # 5. Create or fetch the role
    role = get_or_create_role(nb, role_name)

    # 6. Create the device
    new_device = create_device(nb, device_name, location, device_type, role)

    # Print the result
    if new_device:
        print("[SUCCESS] Device created or retrieved successfully:")
        print(f"  Name:     {new_device.name}")
        print(f"  Location: {new_device.location.name}")
        print(f"  Role:     {new_device.role.name}")
        print(f"  Type:     {new_device.device_type.model}")
        print(f"  Status:   {new_device.status}")


if __name__ == "__main__":
    main()
