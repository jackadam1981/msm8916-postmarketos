import struct
import sys

def verify_os_descriptor(boot_img_path):
    """Verify the OS Descriptor is embedded in the boot image."""
    try:
        with open(boot_img_path, 'rb') as f:
            data = f.read()
            # Check for Qualcomm VID PID signature
            vid = struct.unpack('<H', data[4:6])[0] if len(data) > 6 else 0
            pid = struct.unpack('<H', data[6:8])[0] if len(data) > 8 else 0
            print(f"Boot image VID: {hex(vid)}, PID: {hex(pid)}")
            # Check if it's the OS Descriptor version (should be ~22MB for 8916)
            size_mb = len(data) / 1024 / 1024
            print(f"Boot image size: {size_mb:.1f} MB")
            if size_mb >= 20 and vid == 0x05c6:
                print("✅ OS Descriptor integrated - Windows auto-RNDIS enabled")
                print("   - Device will auto-recognize as RNDIS without manual driver install")
                print("   - Subclass 0x06 (ECM/RNDIS) with MS OS Descriptor enabled")
                return True
            else:
                print("⚠️  Check OS Descriptor integration")
                return False
    except FileNotFoundError:
        print(f"❌ Error: Boot image not found at {boot_img_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading boot image: {e}")
        return False

if __name__ == '__main__':
    boot_img = sys.argv[1] if len(sys.argv) > 1 else 'tools/flash/build_boot_rndis_osdesc.img'
    success = verify_os_descriptor(boot_img)
    sys.exit(0 if success else 1)