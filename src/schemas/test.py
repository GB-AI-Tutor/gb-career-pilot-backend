# Test data
from universities import UniversityResponse

data = {
    "name": "Karakoram International University",
    "city": "Gilgit",
    "sector": "Public",
    "website": "https://kiu.edu.pk",
}

uni = UniversityResponse(
    id="550e8400-e29b-41d4-a716-446655440000", created_at="2026-03-17T00:00:00", **data
)
print(uni.model_dump_json(indent=2))
