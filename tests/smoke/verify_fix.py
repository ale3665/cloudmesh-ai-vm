import pytest
from click.testing import CliRunner
from cloudmesh.ai.command import vm

def test_reservation_duration_no_type_error():
    runner = CliRunner()
    # We don't care if it fails due to cloud config/permissions,
    # we just want to make sure it doesn't raise TypeError: get_active_provider() missing 1 required positional argument: 'ctx'
    result = runner.invoke(vm.vm_group, ["reservation", "duration", "test-res", "--node-type", "gpu", "--count", "1"])
    
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    
    if "TypeError: get_active_provider() missing 1 required positional argument: 'ctx'" in result.output:
        pytest.fail("TypeError still present!")
    else:
        print("TypeError is gone!")

if __name__ == "__main__":
    runner = CliRunner()
    result = runner.invoke(vm.vm_group, ["reservation", "duration", "test-res", "--node-type", "gpu", "--count", "1"])
    print(result.output)
