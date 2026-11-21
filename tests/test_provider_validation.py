
import pytest

from app.tools.health.providers import validate_provider_id


@pytest.mark.parametrize(
    "provider_id",
    [1, 2, 4, 100],
)
def test_valid_provider_ids(provider_id):
    validate_provider_id(provider_id)


@pytest.mark.parametrize(
    "provider_id",
    [-1, 0, 1.5, True, False, "4", None],
)
def test_invalid_provider_ids(provider_id):
    with pytest.raises(ValueError):
        validate_provider_id(provider_id)
