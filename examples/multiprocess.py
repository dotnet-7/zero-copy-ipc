"""Example: Multi-process communication with ZeroCopyDict."""

import multiprocessing as mp
import time
import os
from zero_copy_ipc import ZeroCopyDict


def producer_process(name: str, count: int):
    """Producer process that writes data."""
    print(f"[Producer {os.getpid()}] Starting...")
    
    d = ZeroCopyDict.attach(name)
    
    for i in range(count):
        d[f"item_{i}"] = {"value": i, "timestamp": time.time()}
        print(f"[Producer {os.getpid()}] Wrote item_{i}")
        time.sleep(0.01)
    
    d["producer_done"] = True
    print(f"[Producer {os.getpid()}] Finished")
    
    d.close()


def consumer_process(name: str, consumer_id: int):
    """Consumer process that reads data."""
    print(f"[Consumer {consumer_id} {os.getpid()}] Starting...")
    
    d = ZeroCopyDict.attach(name)
    
    items_read = 0
    while True:
        if "producer_done" in d:
            break
        
        for i in range(100):
            key = f"item_{i}"
            if key in d:
                value = d[key]
                if value:
                    items_read += 1
        
        time.sleep(0.005)
    
    print(f"[Consumer {consumer_id} {os.getpid()}] Finished, read {items_read} items")
    
    d.close()


def main():
    print("Multi-Process Communication Example")
    print("=" * 50)
    
    dict_name = f"mp_example_{os.getpid()}"
    
    print("\n1. Creating shared dictionary...")
    shared_dict = ZeroCopyDict.create(
        dict_name,
        max_items=10000,
        heap_size=50 * 1024 * 1024
    )
    
    print(f"   Created: {shared_dict}")
    
    print("\n2. Starting producer and consumer processes...")
    
    producer = mp.Process(
        target=producer_process,
        args=(dict_name, 50)
    )
    
    consumers = [
        mp.Process(target=consumer_process, args=(dict_name, i))
        for i in range(2)
    ]
    
    producer.start()
    for c in consumers:
        c.start()
    
    print("\n3. Waiting for processes to complete...")
    producer.join(timeout=10)
    
    for c in consumers:
        c.join(timeout=5)
    
    print("\n4. Final statistics...")
    stats = shared_dict.stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n5. Cleaning up...")
    shared_dict.close()
    
    print("\n" + "=" * 50)
    print("Multi-process example completed!")


if __name__ == "__main__":
    main()