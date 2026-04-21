# from collections import OrderedDict

# import merge_karachi_universities as merged


# def test_universities_columns_match_schema_order():
#     assert [
#         "id",
#         "name",
#         "city",
#         "country",
#         "sector",
#         "website",
#         "ranking_national",
#         "qs_ranking",
#         "founded_year",
#         "has_hostel",
#         "has_scholarships",
#         "is_active",
#         "created_at",
#         "updated_at",
#     ] == merged.UNIVERSITIES_COLUMNS


# def test_build_university_row_has_complete_schema_and_normalization():
#     uni = merged.KarachiUniversity(
#         name="University Of Karachi",
#         hec_detail_url="https://example.com/hec/uni",
#         sector="Public",
#         website="https://uok.edu.pk",
#         ranking_national="3",
#         qs_ranking="=1001",
#         founded_year="1951",
#         has_hostel="true",
#         has_scholarships="false",
#     )

#     row = merged.build_university_row(
#         row_id=1,
#         uni=uni,
#         created_updated_at="2026-04-14T00:00:00+00:00",
#     )

#     assert isinstance(row, OrderedDict)
#     assert list(row.keys()) == merged.UNIVERSITIES_COLUMNS
#     assert row["id"] == 1
#     assert row["name"] == "university of karachi"
#     assert row["city"] == "Karachi"
#     assert row["country"] == "Pakistan"
#     assert row["sector"] == "Public"
#     assert row["website"] == "https://uok.edu.pk"
#     assert row["ranking_national"] == "3"
#     assert row["qs_ranking"] == "=1001"
#     assert row["founded_year"] == "1951"
#     assert row["has_hostel"] == "true"
#     assert row["has_scholarships"] == "false"
#     assert row["is_active"] == "true"
