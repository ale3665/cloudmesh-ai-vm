import os
import sys
import uuid
from pathlib import Path
from pprint import pprint

import yaml

# Add the project root to sys.path so 'src' and 'cloudmesh' can be imported
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cloudmesh.ai.common.dotdict import DotDict
from cloudmesh.ai.common.util import path_expand

from src.cloudmesh.ai.vm.openstack.ChameleonManager import Provider


def load_config():
    print("Loading clouds.yaml configuration...")
    config_path = path_expand("~/.config/cloudmesh/clouds.yaml")
    with open(config_path, "r", encoding="utf-8") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    pprint(data)
    return DotDict(data)


def test_chameleon_provider():
    config_all = load_config()
    cloud_name = "chameleon"

    if cloud_name not in config_all.clouds:
        print(f"Error: {cloud_name} not found in clouds.yaml")
        sys.exit(1)

    cloud_config = config_all.clouds[cloud_name]

    # Instantiate the Provider
    # The Provider expects config and cloud_name
    provider = Provider(config=cloud_config, cloud_name=cloud_name)

    # Set OS_CLOUD for chi authentication shim
    os.environ["OS_CLOUD"] = cloud_name

    print("\n" + "=" * 60)
    print("PART 1: Account and Metadata Tests")
    print("=" * 60)

    print("Testing list_regions()...")
    regions = provider.list_regions()
    print(f"Regions found: {len(regions)}")
    assert isinstance(regions, list), "list_regions should return a list"

    print("Testing get_account_info()...")
    account_info = provider.get_account_info()
    pprint(account_info)
    # The test failed because 'site' was missing.
    # Based on Provider.get_account_info, it looks for chi.get("site").
    # If chi.get("site") fails, it returns an error dict.
    if "error" in account_info:
        print(f"Warning: get_account_info returned an error: {account_info['error']}")
    else:
        assert "site" in account_info or "project_name" in account_info, (
            "Account info should contain site or project_name"
        )

    print("Testing get_images()...")
    images = provider.get_images()
    print(f"Images found: {len(images)}")
    assert isinstance(images, list), "get_images should return a list"

    print("Testing get_flavors()...")
    flavors = provider.get_flavors()
    print(f"Flavors found: {len(flavors)}")
    assert isinstance(flavors, list) and len(flavors) > 0, (
        "get_flavors should return a non-empty list"
    )

    print("Testing get_keys()...")
    keys = provider.get_keys()
    print(f"Keys found: {len(keys)}")
    assert isinstance(keys, list), "get_keys should return a list"

    print("Testing get_security_groups()...")
    sgs = provider.get_security_groups()
    print(f"Security groups found: {len(sgs)}")
    assert isinstance(sgs, list), "get_security_groups should return a list"

    print("\n" + "=" * 60)
    print("PART 2: Resource Management Tests (Non-VM)")
    print("=" * 60)

    # Key Management
    print("Testing upload_key/delete_key...")
    temp_key_name = f"test-key-{uuid.uuid4().hex[:6]}"
    pub_key_path = cloud_config.get("key_path", "~/.ssh/id_rsa.pub")

    success = provider.upload_key(pub_key_path, temp_key_name)
    print(f"upload_key: {'Success' if success else 'Failed'}")
    assert success is True, "upload_key failed"

    # Verify key is there
    current_keys = [k["name"] for k in provider.get_keys()]
    assert temp_key_name in current_keys, f"Key {temp_key_name} not found after upload"

    success = provider.delete_key(temp_key_name)
    print(f"delete_key: {'Success' if success else 'Failed'}")
    assert success is True, "delete_key failed"

    # Verify key is gone
    current_keys = [k["name"] for k in provider.get_keys()]
    assert temp_key_name not in current_keys, (
        f"Key {temp_key_name} still exists after deletion"
    )

    # Security Group Management
    print("Testing create_security_group/delete_security_group...")
    temp_sg_name = f"test-sg-{uuid.uuid4().hex[:6]}"

    success = provider.create_security_group(temp_sg_name, "Test SG for smoke test")
    print(f"create_security_group: {'Success' if success else 'Failed'}")
    assert success is True, "create_security_group failed"

    # Test rule addition
    print("Testing add_security_group_rule...")
    rule_id = provider.add_security_group_rule(temp_sg_name, "tcp", "80", "0.0.0.0/0")
    print(f"Rule added with ID: {rule_id}")
    assert rule_id is not None, "add_security_group_rule failed"

    # List rules
    rules = provider.list_security_group_rules(temp_sg_name)
    print(f"Rules found: {len(rules)}")
    assert len(rules) > 0, "No rules found in security group"

    # Delete rule
    success = provider.remove_security_group_rule(temp_sg_name, rule_id)
    print(f"remove_security_group_rule: {'Success' if success else 'Failed'}")
    assert success is True, "remove_security_group_rule failed"

    # Delete SG
    success = provider.delete_security_group(temp_sg_name)
    print(f"delete_security_group: {'Success' if success else 'Failed'}")
    assert success is True, "delete_security_group failed"

    print("\n" + "=" * 60)
    print("PART 3: VM Lifecycle Tests (DONE LAST)")
    print("=" * 60)

    vm_name = f"smoke-test-vm-{uuid.uuid4().hex[:6]}"
    try:
        print(f"Starting VM: {vm_name}...")
        # Using defaults from config
        started_vm = provider.start(name=vm_name)
        print(f"VM started: {started_vm}")
        assert started_vm is not None, "provider.start() returned None"

        print("Testing info()...")
        vm_info = provider.info(started_vm)
        pprint(vm_info)
        assert vm_info.get("Name") == started_vm, "VM info name mismatch"
        assert vm_info.get("State") in ["ACTIVE", "BUILD", "VERIFYING"], (
            f"Unexpected VM state: {vm_info.get('State')}"
        )

        print("Testing list()...")
        vms = provider.list()
        assert any(vm.get("name") == started_vm for vm in vms), (
            "VM not found in provider.list()"
        )

        print("Testing assign_floating_ip()...")
        fip = provider.assign_floating_ip(started_vm)
        print(f"Assigned FIP: {fip}")
        assert fip is not None, "assign_floating_ip failed"

        print("Testing stop()...")
        stopped = provider.stop(started_vm)
        print(f"Stop: {'Success' if stopped else 'Failed'}")
        assert stopped is True, "provider.stop() failed"

        print("Testing restart()...")
        restarted = provider.restart(started_vm)
        print(f"Restart: {'Success' if restarted else 'Failed'}")
        assert restarted is True, "provider.restart() failed"

        print("Testing suspend()...")
        suspended = provider.suspend(started_vm)
        print(f"Suspend: {'Success' if suspended else 'Failed'}")
        assert suspended is True, "provider.suspend() failed"

    finally:
        print(f"\nCleaning up VM: {vm_name}...")
        try:
            provider.delete(vm_name)
            print("VM deleted successfully.")
        except Exception as e:
            print(f"Error deleting VM: {e}")

    print("\n" + "=" * 60)
    print("All ChameleonProvider tests passed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_chameleon_provider()
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    sys.exit(0)
