"""Example: Basic usage of ZeroCopyDict."""

from zero_copy_ipc import ZeroCopyDict


def main():
    print("Zero-Copy IPC Dictionary Example")
    print("=" * 50)
    
    print("\n1. Creating shared dictionary...")
    d = ZeroCopyDict.create(
        "example_dict",
        max_items=1000,
        heap_size=10 * 1024 * 1024
    )
    
    print(f"   Created: {d}")
    
    print("\n2. Storing different types of data...")
    d["string"] = "Hello, World!"
    d["integer"] = 42
    d["float"] = 3.14159
    d["list"] = [1, 2, 3, 4, 5]
    d["dict"] = {"nested": "value", "number": 123}
    d["tuple"] = (1, 2, 3)
    
    print(f"   Stored {len(d)} items")
    
    print("\n3. Reading data...")
    print(f"   string: {d['string']}")
    print(f"   integer: {d['integer']}")
    print(f"   float: {d['float']}")
    print(f"   list: {d['list']}")
    print(f"   dict: {d['dict']}")
    print(f"   tuple: {d['tuple']}")
    
    print("\n4. Updating data...")
    d["string"] = "Updated value"
    print(f"   Updated string: {d['string']}")
    
    print("\n5. Dictionary operations...")
    print(f"   Keys: {d.keys()}")
    print(f"   Values count: {len(d.values())}")
    print(f"   Items count: {len(d.items())}")
    
    print("\n6. Statistics...")
    stats = d.stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n7. Using context manager...")
    with ZeroCopyDict.create("temp_dict", max_items=100) as temp:
        temp["temp_key"] = "temp_value"
        print(f"   Temp dict: {temp['temp_key']}")
    
    print("\n8. Cleaning up...")
    d.close()
    print("   Done!")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")


if __name__ == "__main__":
    main()